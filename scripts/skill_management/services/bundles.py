"""Source-neutral atomic skill-bundle inventory and Markdown reference APIs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import urllib.parse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import secure_fs
from brain.utils import parse_frontmatter

from skill_management import paths as path_policy


MAX_BUNDLE_FILES = 5000
MAX_BUNDLE_DEPTH = 32
MAX_BUNDLE_FILE_BYTES = 4 * 1024 * 1024
MAX_BUNDLE_TOTAL_BYTES = 64 * 1024 * 1024
_REPARSE_POINT_FLAG = 0x400
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
_FRONTMATTER_CLOSE = re.compile(r"(?m)^---[ \t]*\r?$")
_FRONTMATTER_KEY = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9_-]*):")
_QUOTED_DESCRIPTION = re.compile(r'(?m)^description:[ \t]*"')
SCAFFOLD_TEMPLATE_ROOT = PurePosixPath(
    ".github/skills/cg-skill-management/templates"
)
MARKDOWN_LINK_PATTERN = re.compile(
    r"!?\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+[^)]*)?\)"
)
MARKDOWN_REFERENCE_PATTERN = re.compile(
    r"^\s*\[[^\]]+\]:\s*<?([^\s>]+)>?", re.MULTILINE
)


class BundleValidationError(ValueError):
    """Raised when a skill bundle cannot be inventoried safely."""


@dataclass(frozen=True)
class BundleFile:
    """One regular source file in an atomic skill bundle."""

    source_path: str
    bundle_path: str
    content: bytes
    sha256: str
    executable: bool


@dataclass(frozen=True)
class BundleIssue:
    """One deterministic bundle validation issue."""

    code: str
    path: str
    message: str
    remediation: str


@dataclass(frozen=True)
class BundleInventory:
    """Complete source-neutral inventory for one atomic skill bundle."""

    identifier: str
    source_path: str
    origin: str
    frontmatter: Mapping[str, Any]
    files: Tuple[BundleFile, ...]
    digest: str


def bundle_inventory_from_files(
    identifier: str,
    source_path: str,
    origin: str,
    files: Mapping[str, bytes],
) -> BundleInventory:
    """Build one validated atomic inventory from exact in-memory files.

    Args:
        identifier: Immutable bundle identifier.
        source_path: Future repository-relative bundle root.
        origin: Stable bundle origin.
        files: Bundle-relative paths mapped to exact bytes.

    Returns:
        A deterministic validated inventory without filesystem writes.

    Raises:
        BundleValidationError: If paths, frontmatter, or limits are invalid.

    Example:
        ``bundle_inventory_from_files("demo", source_path, "plugin-canonical", files)``
    """
    errors = path_policy.validate_repo_relative_path("bundle source path", source_path)
    if errors or PurePosixPath(source_path).name != identifier:
        raise BundleValidationError(
            "Bundle source path must be portable and end with its identifier."
        )
    paths = validate_bundle_paths(files)
    if len(paths) > MAX_BUNDLE_FILES:
        raise BundleValidationError(
            f"Skill bundle exceeds maximum file count {MAX_BUNDLE_FILES}."
        )
    if "SKILL.md" not in files:
        raise BundleValidationError("Skill bundle is missing regular SKILL.md.")
    total = 0
    bundle_files = []
    for bundle_path in paths:
        content = files[bundle_path]
        if not isinstance(content, bytes):
            raise BundleValidationError(
                f"In-memory bundle resource must be exact bytes: {bundle_path}"
            )
        if len(content) > MAX_BUNDLE_FILE_BYTES:
            raise BundleValidationError(
                f"Skill bundle file exceeds maximum bytes: {bundle_path}"
            )
        total += len(content)
        if total > MAX_BUNDLE_TOTAL_BYTES:
            raise BundleValidationError(
                f"Skill bundle exceeds maximum total bytes {MAX_BUNDLE_TOTAL_BYTES}."
            )
        source_file = f"{source_path}/{bundle_path}"
        bundle_files.append(
            BundleFile(
                source_file,
                bundle_path,
                content,
                hashlib.sha256(content).hexdigest(),
                False,
            )
        )
    frontmatter = parse_skill_frontmatter(files["SKILL.md"], identifier)
    digest_input = b"".join(
        item.bundle_path.encode("utf-8")
        + b"\0"
        + item.sha256.encode("ascii")
        + b"\n"
        for item in bundle_files
    )
    return BundleInventory(
        identifier,
        source_path,
        origin,
        frontmatter,
        tuple(bundle_files),
        hashlib.sha256(digest_input).hexdigest(),
    )


def _scaffold_names(values: Sequence[str], root: str) -> Tuple[str, ...]:
    result = []
    for value in values:
        name = value.strip()
        if not name:
            continue
        if "/" in name or "\\" in name:
            raise BundleValidationError(
                f"Scaffold {root} names must be one portable filename."
            )
        if root != "resources" and not PurePosixPath(name).suffix:
            name += ".md"
        relative = f"{root}/{name}"
        errors = path_policy.validate_repo_relative_path("scaffold resource", relative)
        if errors:
            raise BundleValidationError("Unsafe scaffold path: " + "; ".join(errors))
        result.append(relative)
    if len(set(result)) != len(result):
        raise BundleValidationError(
            f"Scaffold {root} paths collide after normalization."
        )
    return validate_bundle_paths(result)


def _load_scaffold_template(source_root: Path, name: str) -> str:
    relative = SCAFFOLD_TEMPLATE_ROOT / name
    try:
        content = secure_fs.secure_read_bytes(
            Path(source_root).resolve(strict=True),
            relative,
            reject_hardlinks=True,
            max_bytes=MAX_BUNDLE_FILE_BYTES,
        )
        return content.decode("utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        raise BundleValidationError(
            f"Cannot load canonical scaffold template safely: {relative}"
        ) from error


def scaffold_permanent_bundle(
    source_root: Path,
    identifier: str,
    description: str,
    owner: str,
    capability: str,
    *,
    references: Sequence[str] = (),
    workflows: Sequence[str] = (),
    examples: Sequence[str] = (),
    resources: Sequence[str] = (),
    resource_classes: Optional[Mapping[str, str]] = None,
) -> BundleInventory:
    """Build a focused permanent skill scaffold entirely in memory.

    Args:
        source_root: Canonical source containing reviewed scaffold templates.
        identifier: Immutable lowercase skill identifier.
        description: Non-empty ASCII frontmatter description.
        owner: Explicit owner module identifier.
        capability: Explicit capability identifier.
        references: Requested reference filenames.
        workflows: Requested workflow filenames.
        examples: Requested example filenames.
        resources: Requested non-data resource filenames.
        resource_classes: Approved class by exact opaque resource path.

    Returns:
        Validated future canonical bundle inventory.

    Raises:
        BundleValidationError: If metadata or requested paths are invalid.

    Example:
        ``scaffold_permanent_bundle(root, "demo", "Demo.", "cap-demo", "demo")``
    """
    if _IDENTIFIER_PATTERN.fullmatch(identifier) is None:
        raise BundleValidationError("Permanent skill identifier is invalid.")
    for label, value in (
        ("description", description),
        ("owner", owner),
        ("capability", capability),
    ):
        if not isinstance(value, str) or not value.strip():
            raise BundleValidationError(f"Permanent skill {label} is required.")
        try:
            value.encode("ascii")
        except UnicodeEncodeError as error:
            raise BundleValidationError(
                f"Permanent skill {label} must contain ASCII characters only."
            ) from error
    if "\r" in description or "\n" in description:
        raise BundleValidationError("Permanent skill description must be one line.")

    paths = {
        "reference": _scaffold_names(references, "references"),
        "workflow": _scaffold_names(workflows, "workflows"),
        "example": _scaffold_names(examples, "examples"),
        "resource": _scaffold_names(resources, "resources"),
    }
    classes = dict(resource_classes or {})
    resource_paths = set(paths["resource"])
    if any(path not in resource_paths for path in classes):
        raise BundleValidationError(
            "Resource classes may name only requested resource paths."
        )
    title = " ".join(part.capitalize() for part in identifier.split("-"))
    class_line = ""
    if classes:
        entries = [f"{path}={classes[path]}" for path in sorted(classes)]
        class_line = (
            "resource-classes: "
            + json.dumps(entries, ensure_ascii=True)
            + "\n"
        )
    skill_template = _load_scaffold_template(source_root, "skill.md.txt")
    skill_text = (
        skill_template.replace("{{NAME}}", identifier)
        .replace("{{DESCRIPTION}}", json.dumps(description, ensure_ascii=True))
        .replace("{{OWNER}}", owner)
        .replace("{{CAPABILITY}}", capability)
        .replace("{{RESOURCE_CLASSES}}", class_line)
        .replace("{{TITLE}}", title)
    )
    files = {"SKILL.md": skill_text.encode("utf-8")}
    for kind, requested in paths.items():
        for relative in requested:
            if kind != "resource":
                template_name = f"{kind}.md"
            elif PurePosixPath(relative).suffix.casefold() == ".svg":
                template_name = "resource.svg"
            elif PurePosixPath(relative).suffix.casefold() == ".json":
                template_name = "resource.json"
            else:
                template_name = "resource.txt"
            template = _load_scaffold_template(source_root, template_name)
            text = template.replace("{{TITLE}}", title).replace(
                "{{RESOURCE}}", PurePosixPath(relative).name
            )
            files[relative] = text.encode("utf-8")
    return bundle_inventory_from_files(
        identifier,
        f".github/skills/{identifier}",
        "plugin-canonical",
        files,
    )


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def validate_bundle_paths(paths: Iterable[str]) -> Tuple[str, ...]:
    """Validate and sort one portable bundle-relative path inventory.

    Args:
        paths: Bundle-relative POSIX paths.

    Returns:
        Sorted validated paths.

    Raises:
        BundleValidationError: If a path is unsafe or collides portably.

    Example:
        ``validate_bundle_paths(("SKILL.md", "references/guide.md"))``
    """
    ordered = sorted(paths)
    seen = {}
    for value in ordered:
        errors = path_policy.validate_repo_relative_path("bundle path", value)
        if errors:
            raise BundleValidationError("Unsafe bundle path: " + "; ".join(errors))
        key = path_policy.portable_path_key(value)
        prior = seen.get(key)
        if prior is not None and prior != value:
            raise BundleValidationError(
                f"Skill bundle portable path collision: {prior} and {value}"
            )
        seen[key] = value
    return tuple(ordered)


def parse_skill_frontmatter(content: bytes, expected_id: str) -> Dict[str, Any]:
    """Parse and strictly validate canonical ``SKILL.md`` frontmatter.

    Args:
        content: Exact source bytes.
        expected_id: Immutable skill identifier from the bundle directory.

    Returns:
        Parsed frontmatter mapping.

    Raises:
        BundleValidationError: If encoding, delimiters, name, or description fail.

    Example:
        ``parse_skill_frontmatter(skill_bytes, "cg-skill-example")``
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BundleValidationError("SKILL.md is not valid UTF-8.") from error
    if text.startswith("\ufeff"):
        raise BundleValidationError("SKILL.md frontmatter must not contain a BOM.")
    opening = re.match(r"^---[ \t]*(?:\r?\n)", text)
    if opening is None:
        raise BundleValidationError("SKILL.md must start with YAML frontmatter.")
    closing = _FRONTMATTER_CLOSE.search(text, opening.end())
    if closing is None:
        raise BundleValidationError("SKILL.md frontmatter has no closing delimiter.")
    block = text[opening.end():closing.start()]
    try:
        block.encode("ascii")
    except UnicodeEncodeError as error:
        raise BundleValidationError(
            "SKILL.md frontmatter must contain ASCII characters only."
        ) from error
    keys = _FRONTMATTER_KEY.findall(block)
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise BundleValidationError(
            "SKILL.md frontmatter contains duplicate keys: " + ", ".join(duplicates)
        )
    parsed = parse_frontmatter(text)
    if parsed.get("name") != expected_id or _IDENTIFIER_PATTERN.fullmatch(expected_id) is None:
        raise BundleValidationError(
            "SKILL.md name must match its lowercase immutable bundle identifier."
        )
    description = parsed.get("description")
    if (
        not isinstance(description, str)
        or not description.strip()
        or _QUOTED_DESCRIPTION.search(block) is None
    ):
        raise BundleValidationError(
            "SKILL.md description must be one non-empty double-quoted string."
        )
    return dict(parsed)


def list_canonical_bundle_paths(source_root: Path) -> Tuple[str, ...]:
    """List canonical skill bundle roots without using external locations.

    Args:
        source_root: Canonical Compound GPID source root.

    Returns:
        Sorted repository-relative bundle directory paths.

    Raises:
        BundleValidationError: If the canonical skills root or an entry is unsafe.

    Example:
        ``list_canonical_bundle_paths(Path("."))``
    """
    root = Path(source_root).resolve()
    skills_root = root / ".github/skills"
    try:
        metadata = os.lstat(str(skills_root))
    except OSError as error:
        raise BundleValidationError("Canonical .github/skills root is missing.") from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise BundleValidationError("Canonical .github/skills root is not a real directory.")
    result = []

    def has_managed_entry(directory: Path) -> bool:
        with os.scandir(str(directory)) as children:
            ordered_children = sorted(children, key=lambda item: item.name)
        for child in ordered_children:
            child_metadata = child.stat(follow_symlinks=False)
            if _is_link_or_reparse(child_metadata):
                return True
            if stat.S_ISDIR(child_metadata.st_mode):
                if has_managed_entry(Path(child.path)):
                    return True
            else:
                return True
        return False

    with os.scandir(str(skills_root)) as entries:
        for entry in sorted(entries, key=lambda item: item.name):
            entry_metadata = entry.stat(follow_symlinks=False)
            relative = f".github/skills/{entry.name}"
            if _is_link_or_reparse(entry_metadata):
                raise BundleValidationError(
                    f"Canonical skill bundle is a link or reparse point: {relative}"
                )
            if not stat.S_ISDIR(entry_metadata.st_mode):
                raise BundleValidationError(
                    f"Canonical skill entry is not a directory: {relative}"
                )
            if not has_managed_entry(Path(entry.path)):
                continue
            errors = path_policy.validate_repo_relative_path("skill bundle", relative)
            if errors:
                raise BundleValidationError("Unsafe canonical skill path: " + "; ".join(errors))
            result.append(relative)
    return tuple(result)


def read_skill_frontmatter(source_root: Path, source_path: str) -> Dict[str, Any]:
    """Read only one canonical ``SKILL.md`` metadata block safely.

    Args:
        source_root: Root that contains the bundle.
        source_path: Portable root-relative bundle directory.

    Returns:
        Strictly parsed skill frontmatter.

    Raises:
        BundleValidationError: If the source path or frontmatter is invalid.

    Example:
        ``metadata = read_skill_frontmatter(root, ".github/skills/example")``
    """
    errors = path_policy.validate_repo_relative_path("bundle source path", source_path)
    if errors:
        raise BundleValidationError("Unsafe bundle source path: " + "; ".join(errors))
    root = Path(source_root).resolve()
    relative_root = PurePosixPath(source_path)
    _validate_bundle_root(root, relative_root)
    skill_path = relative_root / "SKILL.md"
    try:
        content = secure_fs.secure_read_bytes(
            root,
            skill_path,
            reject_hardlinks=True,
            max_bytes=MAX_BUNDLE_FILE_BYTES,
        )
    except (OSError, ValueError) as error:
        raise BundleValidationError(
            f"Cannot read bundle SKILL.md safely: {skill_path}: {error}"
        ) from error
    return parse_skill_frontmatter(content, relative_root.name)


def _validate_bundle_root(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = os.lstat(str(current))
        except OSError as error:
            raise BundleValidationError(f"Skill bundle path is missing: {relative}") from error
        if _is_link_or_reparse(metadata):
            raise BundleValidationError(
                f"Skill bundle path contains a link or reparse point: {relative}"
            )
        if not stat.S_ISDIR(metadata.st_mode):
            raise BundleValidationError(f"Skill bundle path is not a directory: {relative}")
    return current


def inventory_bundle(
    source_root: Path,
    source_path: str,
    *,
    origin: str,
    executable_paths: Optional[Sequence[str]] = None,
    validate_frontmatter: bool = True,
) -> BundleInventory:
    """Inventory one complete atomic bundle without following links.

    Args:
        source_root: Root that contains the source bundle.
        source_path: Portable root-relative bundle directory.
        origin: Stable source origin such as ``plugin-canonical``.
        executable_paths: Optional Git-index executable paths.
        validate_frontmatter: Whether to enforce canonical skill metadata.

    Returns:
        Complete deterministic bundle inventory.

    Raises:
        BundleValidationError: If confinement, paths, files, or frontmatter fail.

    Example:
        ``inventory_bundle(root, ".github/skills/example", origin="plugin-canonical")``
    """
    errors = path_policy.validate_repo_relative_path("bundle source path", source_path)
    if errors:
        raise BundleValidationError("Unsafe bundle source path: " + "; ".join(errors))
    root = Path(source_root).resolve()
    relative_root = PurePosixPath(source_path)
    bundle_root = _validate_bundle_root(root, relative_root)
    git_executables = set(executable_paths) if executable_paths is not None else None
    pending = [(bundle_root, 0)]
    files = []
    total_bytes = 0
    while pending:
        directory, depth = pending.pop()
        if depth > MAX_BUNDLE_DEPTH:
            raise BundleValidationError(
                f"Skill bundle exceeds maximum depth {MAX_BUNDLE_DEPTH}."
            )
        with os.scandir(str(directory)) as entries:
            ordered_entries = sorted(entries, key=lambda item: item.name, reverse=True)
        for entry in ordered_entries:
            entry_path = Path(entry.path)
            bundle_path = entry_path.relative_to(bundle_root).as_posix()
            source_relative = entry_path.relative_to(root).as_posix()
            metadata = entry.stat(follow_symlinks=False)
            if _is_link_or_reparse(metadata):
                raise BundleValidationError(
                    f"Skill bundle contains a symlink or reparse point: {bundle_path}"
                )
            if stat.S_ISDIR(metadata.st_mode):
                if entry.name == "__pycache__":
                    continue
                pending.append((entry_path, depth + 1))
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise BundleValidationError(
                    f"Skill bundle contains a non-regular entry: {bundle_path}"
                )
            if bundle_path.casefold().endswith((".pyc", ".pyo")):
                raise BundleValidationError(
                    f"Skill bundle contains Python cache artifact: {bundle_path}"
                )
            if len(files) >= MAX_BUNDLE_FILES:
                raise BundleValidationError(
                    f"Skill bundle exceeds maximum file count {MAX_BUNDLE_FILES}."
                )
            try:
                content = secure_fs.secure_read_bytes(
                    root,
                    PurePosixPath(source_relative),
                    reject_hardlinks=True,
                    max_bytes=MAX_BUNDLE_FILE_BYTES,
                )
            except (OSError, ValueError) as error:
                raise BundleValidationError(
                    f"Cannot read bundle file safely: {source_relative}: {error}"
                ) from error
            total_bytes += len(content)
            if total_bytes > MAX_BUNDLE_TOTAL_BYTES:
                raise BundleValidationError(
                    f"Skill bundle exceeds maximum total bytes {MAX_BUNDLE_TOTAL_BYTES}."
                )
            executable = (
                source_relative in git_executables
                if git_executables is not None
                else bool(metadata.st_mode & 0o111)
            )
            files.append(
                BundleFile(
                    source_relative,
                    bundle_path,
                    content,
                    hashlib.sha256(content).hexdigest(),
                    executable,
                )
            )
    validated_paths = validate_bundle_paths(item.bundle_path for item in files)
    by_path = {item.bundle_path: item for item in files}
    if "SKILL.md" not in by_path:
        raise BundleValidationError("Skill bundle is missing regular SKILL.md.")
    identifier = relative_root.name
    frontmatter = (
        parse_skill_frontmatter(by_path["SKILL.md"].content, identifier)
        if validate_frontmatter
        else {}
    )
    ordered_files = tuple(by_path[path] for path in validated_paths)
    digest_input = b"".join(
        item.bundle_path.encode("utf-8") + b"\0" + item.sha256.encode("ascii") + b"\n"
        for item in ordered_files
    )
    return BundleInventory(
        identifier,
        relative_root.as_posix(),
        origin,
        frontmatter,
        ordered_files,
        hashlib.sha256(digest_input).hexdigest(),
    )


def normalized_content(file: BundleFile) -> bytes:
    """Return generator-compatible bytes for one inventoried bundle file.

    Args:
        file: Inventoried bundle file.

    Returns:
        Exact non-Markdown bytes or LF-normalized UTF-8 Markdown bytes.

    Raises:
        BundleValidationError: If a Markdown resource is not UTF-8.

    Example:
        ``content = normalized_content(bundle.files[0])``
    """
    if not file.bundle_path.casefold().endswith((".md", ".markdown")):
        return file.content
    try:
        text = file.content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BundleValidationError(
            f"Markdown file is not valid UTF-8: {file.source_path}"
        ) from error
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def strip_fenced_code(text: str) -> str:
    """Remove closed or unterminated Markdown fenced code blocks.

    Args:
        text: Markdown source text.

    Returns:
        Text outside fenced code blocks with source line endings retained.

    Example:
        ``strip_fenced_code("before\n```\ncode\n```\nafter")``
    """
    output = []
    fence_character = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
        if fence_character is None:
            if match:
                fence_character = match.group(1)[0]
                fence_length = len(match.group(1))
            else:
                output.append(line)
        elif (
            match
            and match.group(1)[0] == fence_character
            and len(match.group(1)) >= fence_length
        ):
            fence_character = None
            fence_length = 0
    return "".join(output)


def markdown_references(file: BundleFile) -> Tuple[str, ...]:
    """Extract local and external Markdown reference targets from one file.

    Args:
        file: Inventoried Markdown file.

    Returns:
        Reference targets in source order.

    Raises:
        BundleValidationError: If Markdown is not UTF-8.

    Example:
        ``markdown_references(skill_file)``
    """
    if not file.bundle_path.casefold().endswith((".md", ".markdown")):
        return ()
    try:
        text = strip_fenced_code(file.content.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise BundleValidationError(
            f"Markdown file is not valid UTF-8: {file.source_path}"
        ) from error
    matches = []
    for match in MARKDOWN_LINK_PATTERN.finditer(text):
        matches.append((match.start(), match.group(1)))
    for match in MARKDOWN_REFERENCE_PATTERN.finditer(text):
        matches.append((match.start(), match.group(1)))
    return tuple(value for _, value in sorted(matches))


def validate_markdown_references(inventory: BundleInventory) -> Tuple[BundleIssue, ...]:
    """Validate every local Markdown reference against one bundle inventory.

    Args:
        inventory: Complete atomic bundle inventory.

    Returns:
        Deterministically sorted reference issues.

    Example:
        ``issues = validate_markdown_references(inventory)``
    """
    included = {item.bundle_path for item in inventory.files}
    issues = []
    for file in inventory.files:
        for raw_reference in markdown_references(file):
            reference = urllib.parse.unquote(raw_reference)
            reference = reference.split("#", 1)[0].split("?", 1)[0]
            if not reference or reference.startswith("#"):
                continue
            parsed = urllib.parse.urlsplit(reference)
            if parsed.scheme or parsed.netloc:
                continue
            if reference.startswith(("/", "\\")) or re.match(
                r"^[A-Za-z]:", reference
            ):
                issues.append(
                    BundleIssue(
                        "bundle.reference-escape",
                        file.source_path,
                        f"Markdown reference escapes skill bundle: {raw_reference}",
                        "Use a relative link to a regular file inside this skill bundle.",
                    )
                )
                continue
            parts = []
            escaped = False
            target = PurePosixPath(file.bundle_path).parent.joinpath(
                PurePosixPath(reference.replace("\\", "/"))
            )
            for part in target.parts:
                if part in ("", "."):
                    continue
                if part == "..":
                    if not parts:
                        escaped = True
                        break
                    parts.pop()
                else:
                    parts.append(part)
            resolved = PurePosixPath(*parts).as_posix()
            if escaped:
                code = "bundle.reference-escape"
                message = f"Markdown reference escapes skill bundle: {raw_reference}"
            elif resolved not in included:
                code = "bundle.reference-missing"
                message = f"Markdown reference is missing from skill bundle: {raw_reference}"
            else:
                continue
            issues.append(
                BundleIssue(
                    code,
                    file.source_path,
                    message,
                    "Point the link to a regular file included in this skill bundle.",
                )
            )
    return tuple(sorted(issues, key=lambda item: (item.path, item.code, item.message)))
