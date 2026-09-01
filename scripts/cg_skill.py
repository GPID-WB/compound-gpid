#!/usr/bin/env python3
"""Private descriptor-driven dispatcher for Compound GPID skill management."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import stat
import sys
import types
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence, Tuple

import secure_fs
from skill_management import contracts
from skill_management.context import ContextDiscoveryError, discover_context
from skill_management.planning import OperationOutcome, result_envelope


OPERATIONS_ROOT = PurePosixPath(".github/shared/skill-management/operations")
CONTRACTS_ROOT = PurePosixPath(".github/shared/skill-management/contracts")
OPERATION_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
_REPARSE_POINT_FLAG = 0x400
RUNTIME_ROOT = Path(__file__).resolve().parents[1]


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


def _is_regular_file(path: Path) -> bool:
    try:
        metadata = os.lstat(str(path))
    except OSError:
        return False
    return not (
        stat.S_ISLNK(metadata.st_mode)
        or bool(getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG)
    ) and stat.S_ISREG(metadata.st_mode)


def _root_relative_file(root: Path, relative: str, *, max_bytes: int = 4 * 1024 * 1024) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError(f"Descriptor path is unsafe: {relative!r}")
    path = root.joinpath(*pure.parts)
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ValueError(f"Descriptor path escapes source_root: {relative!r}") from error
    try:
        secure_fs.secure_read_bytes(root, pure, max_bytes=max_bytes)
    except (OSError, ValueError) as error:
        raise ValueError(
            f"Descriptor path is missing or not a confined regular file: {relative}"
        ) from error
    return path


def _load_contract_relative(root: Path, relative: PurePosixPath) -> dict:
    content = secure_fs.secure_read_bytes(
        root,
        relative,
        max_bytes=contracts.MAX_CONTRACT_BYTES,
    )
    return contracts.load_contract_bytes(content, source=relative.as_posix())


def _load_descriptor(source_root: Path, operation: str) -> Tuple[dict, dict]:
    descriptor_relative = OPERATIONS_ROOT / f"{operation}.json"
    try:
        descriptor = _load_contract_relative(source_root, descriptor_relative)
    except FileNotFoundError:
        raise FileNotFoundError(operation) from None
    descriptor_schema = _load_contract_relative(
        source_root,
        CONTRACTS_ROOT / "operation-descriptor-v1.schema.json",
    )
    findings = contracts.validate_instance(descriptor, descriptor_schema)
    if findings:
        details = "; ".join(f"{item.path}: {item.code}" for item in findings)
        raise ValueError(f"Operation descriptor is invalid: {details}")
    if descriptor.get("operation") != operation:
        raise ValueError("Operation descriptor identity does not match its filename")
    expected_handler = f"skill_management.operations.{operation.replace('-', '_')}:handle"
    if descriptor.get("handler") != expected_handler:
        raise ValueError(
            "Operation descriptor handler must match its operation identity"
        )

    for field in ("workflow", "documentation"):
        _root_relative_file(source_root, descriptor[field])
    for test_path in descriptor["tests"]:
        _root_relative_file(source_root, test_path)
    contract_relative = PurePosixPath(descriptor["contract"])
    if contract_relative.name != f"{operation}-v1.schema.json":
        raise ValueError("Operation descriptor contract filename must match operation")
    operation_contract_path = _root_relative_file(
        source_root,
        descriptor["contract"],
        max_bytes=contracts.MAX_CONTRACT_BYTES,
    )
    operation_contract = _load_contract_relative(
        source_root,
        PurePosixPath(descriptor["contract"]),
    )
    schema_findings = contracts.validate_schema_definition(operation_contract)
    if schema_findings:
        details = "; ".join(
            f"{item.path}: {item.code}" for item in schema_findings
        )
        raise ValueError(f"Operation contract is invalid: {details}")
    contract_id = operation_contract.get("$id")
    if not isinstance(contract_id, str) or not contract_id.startswith(
        f"cg-skill-{operation}-"
    ):
        raise ValueError("Operation contract $id must match operation identity")
    definitions = operation_contract.get("$defs")
    if not isinstance(definitions, dict) or not all(
        isinstance(definitions.get(name), dict)
        for name in ("arguments", "resultData")
    ):
        raise ValueError(
            "Operation contract must define $defs.arguments and $defs.resultData"
        )
    return descriptor, operation_contract


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
    return rooted


def _load_handler(source_root: Path, operation: str):
    """Load one handler from validated, captured source bytes."""
    module_name = f"skill_management.operations.{operation.replace('-', '_')}"
    relative = PurePosixPath(
        f"scripts/skill_management/operations/{operation.replace('-', '_')}.py"
    )
    content = secure_fs.secure_read_bytes(
        source_root,
        relative,
        reject_hardlinks=True,
        max_bytes=1024 * 1024,
    )
    source_name = relative.as_posix()
    code = compile(content, source_name, "exec", dont_inherit=True)
    module = types.ModuleType(module_name)
    module.__file__ = str(source_root.joinpath(*relative.parts))
    module.__package__ = "skill_management.operations"
    module.__spec__ = None
    exec(code, module.__dict__)  # pylint: disable=exec-used
    handler = getattr(module, "handle", None)
    if not callable(handler):
        raise TypeError("Operation module must define callable handle")
    return handler


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
        discovered = discover_context(
            Path(arguments.project_root),
            Path(arguments.source_root) if arguments.source_root else None,
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
        handler = _load_handler(discovered.source_root, operation)
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
