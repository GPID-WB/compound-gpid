#!/usr/bin/env python3
"""Private descriptor-driven dispatcher for Compound GPID skill management."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple

import secure_fs


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
_MAX_TRUSTED_MODULE_BYTES = 4 * 1024 * 1024
_TRUST_ANCHOR_MODULES = frozenset({"secure_fs"})
_SECURE_FS_MODULE = secure_fs
_TRUSTED_MODULES = {}  # type: Dict[str, Tuple[object, Path, str]]


class _CapturedModule:
    """One repository-local module bound to captured source bytes."""

    def __init__(
        self,
        name: str,
        relative: PurePosixPath,
        content: bytes,
        is_package: bool,
    ) -> None:
        self.name = name
        self.relative = relative
        self.content = content
        self.is_package = is_package
        self.digest = hashlib.sha256(content).hexdigest()
        self.defined_names = set()  # type: set[str]


class _CapturedSourceGraph(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Capture and import one complete repository-local dependency closure."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve(strict=True)
        self.modules = {}  # type: Dict[str, _CapturedModule]
        self.package_names = set()  # type: set[str]

    def prepare(self, module_name: str) -> None:
        """Capture and validate all local imports reachable from one module."""
        if not self._capture_if_local(module_name):
            raise ImportError(f"Trusted module is not installed: {module_name}.")
        self._verify_preloaded_modules()

    def prepare_many(self, module_names: Sequence[str]) -> None:
        """Capture and validate the union of multiple local import closures."""
        for module_name in module_names:
            if not self._capture_if_local(module_name):
                raise ImportError(f"Trusted module is not installed: {module_name}.")
        self._verify_preloaded_modules()

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[object] = None,
    ):
        """Return captured specs and block uncaptured internal package imports."""
        del path, target
        captured = self.modules.get(fullname)
        if captured is not None:
            return importlib.util.spec_from_loader(
                fullname,
                self,
                origin=str(self.root.joinpath(*captured.relative.parts)),
                is_package=captured.is_package,
            )
        if fullname == "skill_management" or fullname.startswith(
            "skill_management."
        ):
            raise ImportError(
                f"Internal module was not in the captured dependency closure: {fullname}."
            )
        if any(fullname.startswith(f"{name}.") for name in self.package_names):
            raise ImportError(
                f"Internal package import was not captured: {fullname}."
            )
        return None

    def create_module(self, spec: object) -> None:
        """Use Python's standard module allocation for captured modules."""
        del spec
        return None

    def exec_module(self, module: object) -> None:
        """Execute only the source bytes captured during graph preparation."""
        module_name = vars(module).get("__name__")
        if not isinstance(module_name, str) or module_name not in self.modules:
            raise ImportError("Captured loader received an unknown module.")
        captured = self.modules[module_name]
        source_path = self.root.joinpath(*captured.relative.parts)
        namespace = vars(module)
        namespace["__file__"] = str(source_path)
        if captured.is_package:
            namespace["__path__"] = [str(source_path.parent)]
        code = compile(
            captured.content,
            captured.relative.as_posix(),
            "exec",
            dont_inherit=True,
        )
        exec(code, namespace)  # pylint: disable=exec-used
        _TRUSTED_MODULES[module_name] = (
            module,
            self.root,
            captured.digest,
        )

    @contextmanager
    def active(self) -> Iterator[None]:
        """Install this graph for one bounded import or handler execution."""
        self._verify_preloaded_modules()
        if sys.modules.get("secure_fs") is not _SECURE_FS_MODULE:
            raise ImportError("The secure filesystem trust anchor was replaced.")
        sys.meta_path.insert(0, self)
        try:
            yield
        finally:
            if self in sys.meta_path:
                sys.meta_path.remove(self)

    def _capture_if_local(self, module_name: str) -> bool:
        if not module_name or module_name in _TRUST_ANCHOR_MODULES:
            return False
        if module_name in self.modules:
            return True
        source = self._read_module_source(module_name)
        if source is None:
            return False
        relative, content, is_package = source
        captured = _CapturedModule(module_name, relative, content, is_package)
        self.modules[module_name] = captured
        if is_package:
            self.package_names.add(module_name)

        parent = module_name.rpartition(".")[0]
        if parent and not self._capture_if_local(parent):
            raise ImportError(f"Internal package is incomplete: {parent}.")

        tree = compile(
            content,
            relative.as_posix(),
            "exec",
            ast.PyCF_ONLY_AST,
            dont_inherit=True,
        )
        captured.defined_names = self._module_defined_names(tree)
        self._reject_dynamic_imports(captured, tree)
        self._capture_imports(captured, tree)
        return True

    def _read_module_source(
        self, module_name: str
    ) -> Optional[Tuple[PurePosixPath, bytes, bool]]:
        parts = module_name.split(".")
        package_relative = PurePosixPath("scripts", *parts, "__init__.py")
        module_relative = PurePosixPath(
            "scripts", *parts[:-1], f"{parts[-1]}.py"
        )
        for relative, is_package in (
            (package_relative, True),
            (module_relative, False),
        ):
            try:
                content = secure_fs.secure_read_bytes(
                    self.root,
                    relative,
                    reject_hardlinks=True,
                    max_bytes=_MAX_TRUSTED_MODULE_BYTES,
                )
            except FileNotFoundError:
                continue
            return relative, content, is_package
        return None

    def _capture_imports(self, captured: _CapturedModule, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = self._capture_if_local(alias.name)
                    if alias.name.startswith("skill_management") and not local:
                        raise ImportError(
                            f"Internal import is not installed: {alias.name}."
                        )
                continue
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level:
                package = (
                    captured.name
                    if captured.is_package
                    else captured.name.rpartition(".")[0]
                )
                requested = "." * node.level + (node.module or "")
                try:
                    base = importlib.util.resolve_name(requested, package)
                except (ImportError, ValueError) as error:
                    raise ImportError(
                        f"Invalid relative import in {captured.name}."
                    ) from error
            else:
                base = node.module or ""
            if not base:
                continue
            base_is_local = self._capture_if_local(base)
            if (node.level or base.startswith("skill_management")) and not base_is_local:
                raise ImportError(f"Internal import is not installed: {base}.")
            if not base_is_local or not self.modules[base].is_package:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                candidate = f"{base}.{alias.name}"
                if self._capture_if_local(candidate):
                    continue
                if alias.name not in self.modules[base].defined_names:
                    raise ImportError(
                        f"Internal package member is not installed: {candidate}."
                    )

    @staticmethod
    def _module_defined_names(tree: ast.AST) -> set[str]:
        names = set()  # type: set[str]
        body = getattr(tree, "body", ())
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                for target in targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.asname or alias.name.partition(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        names.add(alias.asname or alias.name)
        return names

    @staticmethod
    def _reject_dynamic_imports(captured: _CapturedModule, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if isinstance(function, ast.Name) and function.id == "__import__":
                raise ImportError(
                    f"Dynamic internal import is forbidden in {captured.name}."
                )
            if isinstance(function, ast.Attribute) and function.attr == "import_module":
                raise ImportError(
                    f"Dynamic internal import is forbidden in {captured.name}."
                )

    def _verify_preloaded_modules(self) -> None:
        for name, captured in self.modules.items():
            existing = sys.modules.get(name)
            if existing is None:
                continue
            trusted = _TRUSTED_MODULES.get(name)
            if trusted is None or trusted[0] is not existing:
                raise ImportError(f"Untrusted preloaded internal module: {name}.")
            if trusted[1] != self.root or trusted[2] != captured.digest:
                raise ImportError(f"Preloaded internal module has wrong root: {name}.")


class _BoundTrustedHandler:
    """Keep the captured graph active for deferred handler imports."""

    def __init__(self, graph: _CapturedSourceGraph, handler: object) -> None:
        self.graph = graph
        self.handler = handler

    def __call__(self, **kwargs: object) -> object:
        with self.graph.active():
            return self.handler(**kwargs)  # type: ignore[operator]


contracts = None
ContextDiscoveryError = None
discover_context = None
OperationOutcome = None
result_envelope = None
_BOOTSTRAP_ERROR = None  # type: Optional[BaseException]
try:
    _bootstrap_graph = _CapturedSourceGraph(RUNTIME_ROOT)
    _bootstrap_graph.prepare_many(
        (
            "skill_management.contracts",
            "skill_management.context",
            "skill_management.planning",
        )
    )
    with _bootstrap_graph.active():
        contracts = importlib.import_module("skill_management.contracts")
        context_module = importlib.import_module("skill_management.context")
        planning_module = importlib.import_module("skill_management.planning")
    ContextDiscoveryError = context_module.ContextDiscoveryError
    discover_context = context_module.discover_context
    OperationOutcome = planning_module.OperationOutcome
    result_envelope = planning_module.result_envelope
except BaseException as error:  # Fail closed; main emits a stable redacted envelope.
    _BOOTSTRAP_ERROR = error


if contracts is not None:
    CONTRACTS_ROOT = contracts.CONTRACTS_ROOT
    OPERATION_PATTERN = contracts.OPERATION_PATTERN
else:
    CONTRACTS_ROOT = PurePosixPath(".github/shared/skill-management/contracts")
    OPERATION_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


class UsageError(ValueError):
    """Raised instead of allowing argparse to terminate the process."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="python scripts/cg_skill.py",
        description="Private Compound GPID skill-management dispatcher.",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--source-root", default=None)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("operation")
    parser.add_argument("operation_arguments", nargs=argparse.REMAINDER)
    return parser


def _finding(
    code: str,
    message: str,
    remediation: str,
    *,
    path: str = "",
) -> contracts.ContractFinding:
    return contracts.ContractFinding(path, code, "error", message, remediation)


def _error_result(
    operation: str,
    exit_code: int,
    finding: contracts.ContractFinding,
    *,
    role: str = "consumer",
    phase: str = "read",
) -> dict:
    safe_operation = operation if OPERATION_PATTERN.fullmatch(operation) else "unknown"
    return result_envelope(
        safe_operation,
        phase,
        role,
        OperationOutcome(findings=(finding,), exit_code=exit_code),
    )


def _load_contract_relative(root: Path, relative: PurePosixPath) -> dict:
    return contracts.load_contract(root, relative)


def _load_descriptor(source_root: Path, operation: str) -> Tuple[dict, dict]:
    try:
        record = contracts.load_operation_descriptor(source_root, operation)
    except FileNotFoundError:
        raise FileNotFoundError(operation) from None
    except contracts.DescriptorValidationError as error:
        raise ValueError(str(error)) from error
    return dict(record.descriptor), dict(record.contract)


def _validate_request(source_root: Path, request: Mapping[str, Any]) -> None:
    request_schema = _load_contract_relative(
        source_root,
        CONTRACTS_ROOT / "request-v1.schema.json",
    )
    findings = contracts.validate_instance(request, request_schema)
    if findings:
        details = "; ".join(f"{item.path}: {item.code}" for item in findings)
        raise ValueError(f"Common request is invalid: {details}")


def _validate_result(source_root: Path, result: Mapping[str, Any]) -> None:
    result_schema = _load_contract_relative(
        source_root,
        CONTRACTS_ROOT / "result-v1.schema.json",
    )
    findings = contracts.validate_instance(result, result_schema)
    if findings:
        details = "; ".join(f"{item.path}: {item.code}" for item in findings)
        raise ValueError(f"Handler result is invalid: {details}")


def _select_phase(
    descriptor: Mapping[str, Any], arguments: Sequence[str]
) -> Tuple[str, Optional[str], list[str]]:
    remaining = []  # type: list[str]
    digest = None  # type: Optional[str]
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if item == "--apply":
            if digest is not None or index + 1 >= len(arguments):
                raise UsageError("--apply requires exactly one plan digest")
            digest = arguments[index + 1]
            index += 2
            continue
        if item.startswith("--apply="):
            if digest is not None:
                raise UsageError("--apply may be specified only once")
            digest = item.partition("=")[2]
            index += 1
            continue
        remaining.append(item)
        index += 1
    phases = tuple(descriptor["phases"])
    if digest is not None:
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise UsageError("--apply requires a lowercase 64-character digest")
        if "apply" not in phases:
            raise UsageError("This operation does not support apply phase")
        return "apply", digest, remaining
    if "read" in phases:
        return "read", None, remaining
    if "plan" in phases:
        return "plan", None, remaining
    raise UsageError("Operation descriptor has no selectable read or plan phase")


def _coerce_argument(value: str, schema: Mapping[str, Any]) -> Any:
    type_name = schema.get("type")
    if type_name == "integer":
        try:
            return int(value)
        except ValueError as error:
            raise UsageError(f"Expected integer argument, received {value!r}") from error
    if type_name == "number":
        try:
            number = float(value)
        except ValueError as error:
            raise UsageError(f"Expected numeric argument, received {value!r}") from error
        if not math.isfinite(number):
            raise UsageError("Numeric arguments must be finite")
        return number
    if type_name == "boolean":
        normalized = value.casefold()
        if normalized not in ("true", "false"):
            raise UsageError(f"Expected true or false, received {value!r}")
        return normalized == "true"
    return value


def _parse_operation_arguments(
    arguments: Sequence[str], schema: Mapping[str, Any]
) -> dict:
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError("Operation argument schema properties must be an object")
    parsed = {}
    positionals = []
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if not item.startswith("--") or item == "--":
            positionals.append(item)
            index += 1
            continue
        option, separator, inline = item[2:].partition("=")
        name = option.replace("-", "_")
        property_schema = properties.get(name)
        if not isinstance(property_schema, dict):
            parsed[name] = inline if separator else True
            index += 1
            continue
        if property_schema.get("type") == "boolean" and not separator:
            value = True
            index += 1
        else:
            if separator:
                raw = inline
                index += 1
            else:
                if index + 1 >= len(arguments):
                    raise UsageError(f"--{option} requires a value")
                raw = arguments[index + 1]
                index += 2
            value = _coerce_argument(raw, property_schema)
        if name in parsed:
            raise UsageError(f"--{option} may be specified only once")
        parsed[name] = value
    if positionals:
        if "positionals" not in properties:
            parsed["positionals"] = positionals
        else:
            parsed["positionals"] = positionals
    return parsed


def _root_operation_schema(schema: Mapping[str, Any], identifier: str) -> dict:
    rooted = dict(schema)
    rooted["$schema"] = contracts.SCHEMA_DIALECT
    rooted["$id"] = identifier
    if isinstance(schema.get("$defs"), dict):
        rooted["$defs"] = dict(schema["$defs"])
    return rooted


def _load_handler(
    source_root: Path,
    operation: str,
    handler_spec: Optional[str] = None,
):
    """Load one handler from a complete captured internal source closure."""
    if handler_spec is None:
        operation_module = operation.replace("-", "_")
    else:
        operation_module = contracts.operation_handler_module(operation, handler_spec)
    module_name = f"skill_management.operations.{operation_module}"
    graph = _CapturedSourceGraph(source_root)
    graph.prepare(module_name)
    with graph.active():
        module = importlib.import_module(module_name)
    handler = vars(module).get("handle")
    if not callable(handler):
        raise TypeError("Operation module must define callable handle")
    return _BoundTrustedHandler(graph, handler)


def _dispatch(
    arguments: argparse.Namespace,
    invocation_path: Optional[Path],
    runtime_root: Path,
) -> dict:
    operation = arguments.operation
    if not OPERATION_PATTERN.fullmatch(operation):
        return _error_result(
            operation,
            contracts.EXIT_USAGE,
            _finding(
                "operation.invalid",
                "Operation names must be lowercase identifiers, not paths.",
                "Use a registered operation name without path separators.",
                path="/operation",
            ),
        )

    try:
        source_root = (
            Path(arguments.source_root)
            if arguments.source_root is not None
            else runtime_root
        )
        discovered = discover_context(
            Path(arguments.project_root),
            source_root,
            invocation_path=invocation_path,
            trusted_source_root=runtime_root,
        )
    except ContextDiscoveryError as error:
        return _error_result(
            operation,
            contracts.EXIT_CONTRACT,
            _finding(
                "context.invalid",
                str(error),
                "Use existing real project and source root directories.",
                path="/root",
            ),
        )
    if discovered.source_root != runtime_root:
        return _error_result(
            operation,
            contracts.EXIT_CONTRACT,
            _finding(
                "context.untrusted-source",
                "source_root does not match the running dispatcher checkout.",
                "Run the dispatcher from the selected canonical source checkout.",
                path="/sourceRoot",
            ),
            role=discovered.role,
        )

    try:
        descriptor, operation_contract = _load_descriptor(
            discovered.source_root, operation
        )
    except FileNotFoundError:
        return _error_result(
            operation,
            contracts.EXIT_USAGE,
            _finding(
                "operation.unknown",
                f"Operation {operation!r} is not registered.",
                "Use an operation with a complete active descriptor.",
                path="/operation",
            ),
            role=discovered.role,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return _error_result(
            operation,
            contracts.EXIT_CONTRACT,
            _finding(
                "descriptor.invalid",
                str(error),
                "Repair the descriptor and every path that it declares.",
                path=f"/{operation}",
            ),
            role=discovered.role,
        )

    try:
        phase, plan_digest, remaining_arguments = _select_phase(
            descriptor,
            arguments.operation_arguments,
        )
    except UsageError as error:
        return _error_result(
            operation,
            contracts.EXIT_USAGE,
            _finding(
                "arguments.apply",
                str(error),
                "Use --apply followed by one valid plan digest.",
                path="/arguments",
            ),
            role=discovered.role,
        )
    if any(
        item == "--role" or item.startswith("--role=")
        for item in remaining_arguments
    ):
        return _error_result(
            operation,
            contracts.EXIT_ROLE_CONTEXT,
            _finding(
                "role.override",
                "A command-line role value cannot grant authority.",
                "Remove --role; role is derived from validated checkout context.",
                path="/arguments",
            ),
            role=discovered.role,
            phase=phase,
        )

    allowed_roles = set(descriptor["roles"])
    authorized = discovered.role in allowed_roles or (
        discovered.role == "maintainer" and "consumer" in allowed_roles
    )
    if not authorized:
        detail = "; ".join(discovered.write_context_errors)
        return _error_result(
            operation,
            contracts.EXIT_ROLE_CONTEXT,
            _finding(
                "role.context-invalid",
                detail or "The resolved role is not allowed for this operation.",
                "Run maintainer operations from one approved canonical feature-branch checkout.",
                path="/role",
            ),
            role=discovered.role,
            phase=phase,
        )

    argument_schema = _root_operation_schema(
        operation_contract["$defs"]["arguments"],
        f"cg-skill-{operation}-arguments-v1",
    )
    result_data_schema = _root_operation_schema(
        operation_contract["$defs"]["resultData"],
        f"cg-skill-{operation}-result-data-v1",
    )
    try:
        operation_arguments = _parse_operation_arguments(
            remaining_arguments,
            argument_schema,
        )
    except UsageError as error:
        return _error_result(
            operation,
            contracts.EXIT_USAGE,
            _finding(
                "arguments.invalid",
                str(error),
                "Use the operation's documented typed arguments.",
                path="/arguments",
            ),
            role=discovered.role,
            phase=phase,
        )
    argument_findings = contracts.validate_instance(
        operation_arguments, argument_schema
    )
    if argument_findings:
        return result_envelope(
            operation,
            phase,
            discovered.role,
            OperationOutcome(
                findings=argument_findings,
                exit_code=contracts.EXIT_USAGE,
            ),
        )

    request = {
        "schema": "cg-skill-request-v1",
        "operation": operation,
        "phase": phase,
        "root": ".",
        "sourceRoot": ".",
        "arguments": operation_arguments,
    }
    if plan_digest is not None:
        request["planDigest"] = plan_digest
    try:
        _validate_request(discovered.source_root, request)
        handler = _load_handler(
            discovered.source_root,
            operation,
            str(descriptor["handler"]),
        )
        outcome = handler(context=discovered, request=request)
        if not isinstance(outcome, OperationOutcome):
            raise TypeError("Operation handler must return OperationOutcome")
        data_findings = contracts.validate_instance(
            dict(outcome.data),
            result_data_schema,
        )
        if data_findings:
            raise ValueError(
                "Operation result data is invalid: "
                + "; ".join(
                    f"{item.path}: {item.code}" for item in data_findings
                )
            )
        result = result_envelope(operation, phase, discovered.role, outcome)
        _validate_result(discovered.source_root, result)
        contracts.canonical_json_bytes(result)
        return result
    except Exception:
        return _error_result(
            operation,
            contracts.EXIT_INTERNAL,
            _finding(
                "internal.dispatch",
                "The selected operation could not complete safely.",
                "Inspect the validated operation module and rerun the command.",
                path="/handler",
            ),
            role=discovered.role,
            phase=phase,
        )


def _render_human(result: Mapping[str, Any]) -> str:
    status = "OK" if result["ok"] else "ERROR"
    lines = [
        f"{status}: {result['operation']} ({result['role']}, {result['phase']})"
    ]
    for finding in result["findings"]:
        location = f" {finding['path']}" if finding["path"] else ""
        lines.append(
            f"{finding['severity'].upper()} [{finding['code']}]{location}: "
            f"{finding['message']}"
        )
        lines.append(f"Remediation: {finding['remediation']}")
    if result.get("planDigest") is not None:
        lines.append(f"Plan digest: {result['planDigest']}")
    if result.get("manifestHealth") is not None:
        lines.append(f"Manifest health: {result['manifestHealth']}")
    if result.get("actions"):
        lines.append(
            "Actions: "
            + contracts.canonical_json_bytes(result["actions"]).decode("utf-8")
        )
    if result.get("data"):
        lines.append(
            "Data: "
            + contracts.canonical_json_bytes(result["data"]).decode("utf-8")
        )
    return "\n".join(lines) + "\n"


def _emit(result: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        sys.stdout.buffer.write(contracts.canonical_json_bytes(result) + b"\n")
        return
    stream = sys.stdout if result["ok"] else sys.stderr
    stream.write(_render_human(result))


def _bootstrap_failure_result() -> dict:
    """Return the stable fail-closed result used before trusted imports exist."""
    return {
        "schema": "cg-skill-result-v1",
        "ok": False,
        "exitCode": 1,
        "operation": "unknown",
        "phase": "read",
        "role": "consumer",
        "changed": False,
        "actions": [],
        "findings": [
            {
                "code": "internal.dispatch",
                "severity": "error",
                "path": "/handler",
                "message": "The trusted dispatcher runtime could not be loaded safely.",
                "remediation": (
                    "Inspect the trusted dispatcher installation and rerun the command."
                ),
            }
        ],
        "data": {},
    }


def _emit_bootstrap_failure(result: Mapping[str, Any], output_format: str) -> None:
    """Render a bootstrap failure without importing internal serialization code."""
    if output_format == "json":
        rendered = json.dumps(
            result,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        sys.stdout.write(rendered + "\n")
        return
    finding = result["findings"][0]
    sys.stderr.write(
        "ERROR: unknown (consumer, read)\n"
        f"ERROR [{finding['code']}] {finding['path']}: {finding['message']}\n"
        f"Remediation: {finding['remediation']}\n"
    )


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    invocation_path: Optional[Path] = None,
    runtime_root: Optional[Path] = None,
) -> int:
    """Parse common arguments, dispatch one operation, and return its exit code."""
    raw_arguments = list(argv if argv is not None else sys.argv[1:])
    output_format = "human"
    for index, value in enumerate(raw_arguments):
        if value == "--format" and index + 1 < len(raw_arguments):
            output_format = raw_arguments[index + 1]
            break
        if value.startswith("--format="):
            output_format = value.partition("=")[2]
            break
    if _BOOTSTRAP_ERROR is not None:
        result = _bootstrap_failure_result()
        _emit_bootstrap_failure(result, output_format)
        return 1
    try:
        arguments = _parser().parse_args(raw_arguments)
    except UsageError as error:
        result = _error_result(
            "unknown",
            contracts.EXIT_USAGE,
            _finding(
                "usage.invalid",
                str(error),
                "Use python scripts/cg_skill.py [common options] <operation> [arguments].",
            ),
        )
        _emit(result, output_format)
        return contracts.EXIT_USAGE
    trusted_runtime = Path(runtime_root) if runtime_root is not None else RUNTIME_ROOT
    trusted_runtime = trusted_runtime.resolve(strict=True)
    try:
        if runtime_root is None or trusted_runtime == RUNTIME_ROOT:
            with _bootstrap_graph.active():
                result = _dispatch(arguments, invocation_path, trusted_runtime)
                contracts.canonical_json_bytes(result)
        else:
            # The injectable root is an in-process test seam. Production CLI
            # dispatch always uses the captured runtime graph above.
            result = _dispatch(arguments, invocation_path, trusted_runtime)
            contracts.canonical_json_bytes(result)
    except Exception:
        result = _error_result(
            "unknown",
            contracts.EXIT_INTERNAL,
            _finding(
                "internal.dispatch",
                "The command could not complete safely.",
                "Inspect the trusted dispatcher installation and rerun the command.",
            ),
        )
    try:
        _emit(result, arguments.format)
    except Exception:
        fallback = _error_result(
            "unknown",
            contracts.EXIT_INTERNAL,
            _finding(
                "internal.output",
                "The command result could not be rendered safely.",
                "Use a valid output format and JSON-compatible operation result.",
            ),
        )
        _emit(fallback, "human")
        return contracts.EXIT_INTERNAL
    return int(result["exitCode"])


if __name__ == "__main__":
    sys.exit(main())
