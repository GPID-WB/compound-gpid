"""Strict executable-only parser for installer declaration sections.

This module reads installer sections as inert text and extracts only the
command inventory the installer actually executes. It never executes prompt,
wrapper, or documentation content.
"""
from __future__ import annotations

import re
from typing import List, Sequence

from help.base import HelpValidationError

MAX_INSTALLER_BYTES = 1024 * 1024
POSIX_INSTALL_START = "# Step 3: Create bin/ wrappers"
POSIX_INSTALL_END = "# Step 4: Add bin/ to PATH via shell profile"
WINDOWS_INSTALL_START = "# Step 3: Register cg-* commands via .cmd wrappers on PATH"
WINDOWS_INSTALL_END = "# Add bin/ to user PATH"

_POSIX_FALSE_GUARDS = re.compile(
    r"^(?:if false\b|if \[ false \]|if :)\s*;?\s*(?:then)?\s*$"
)
_POSIX_IF = re.compile(r"^if\b")
_POSIX_FI = re.compile(r"^fi\b")
_POSIX_HERE_DOC = re.compile(r"<<\s*-?\s*['\"]?([A-Za-z0-9_]+)['\"]?\s*$")


def _bounded_installer_section(
    content: bytes,
    source: str,
    start_marker: str,
    end_marker: str,
) -> List[str]:
    """Return one exact bounded installer declaration section as LF lines."""
    if len(content) > MAX_INSTALLER_BYTES:
        raise HelpValidationError("{} exceeds the installer byte limit".format(source))
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise HelpValidationError("{} must be UTF-8".format(source)) from error
    if "\r" in text:
        raise HelpValidationError(
            "{} must use LF line endings in installer sections".format(source)
        )
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise HelpValidationError(
            "{} installer inventory markers must occur exactly once".format(source)
        )
    section = text.split(start_marker, 1)[1].split(end_marker, 1)[0]
    return section.split("\n")


def _block_lines(lines: Sequence[str], start: int, closing: str) -> List[str]:
    for index in range(start + 1, len(lines)):
        if lines[index] == closing:
            return list(lines[start + 1:index])
    raise HelpValidationError("installer declaration block is not closed")


def _executable_lines(lines: Sequence[str]) -> List[str]:
    """Return only lines the shell or PowerShell interpreter would execute.

    Full-line comments, here-document bodies, and never-true ``if false``
    guard bodies cannot satisfy declaration or chmod evidence.
    """
    executable: List[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].lstrip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        here_doc = _POSIX_HERE_DOC.search(lines[index])
        if here_doc is not None:
            executable.append(stripped)
            marker = here_doc.group(1)
            index += 1
            while index < len(lines) and lines[index] != marker:
                index += 1
            index += 1
            continue
        if _POSIX_FALSE_GUARDS.match(stripped) is not None:
            depth = 1
            index += 1
            while index < len(lines) and depth:
                current = lines[index].lstrip()
                if _POSIX_IF.match(current) is not None:
                    depth += 1
                elif _POSIX_FI.match(current) is not None:
                    depth -= 1
                index += 1
            continue
        if stripped == "if ($false) {":
            depth = 1
            index += 1
            while index < len(lines) and depth:
                depth += lines[index].count("{") - lines[index].count("}")
                index += 1
            continue
        executable.append(stripped)
        index += 1
    return executable


def parse_posix_installer_inventory(content: bytes) -> set:
    """Parse only executable command declarations in the POSIX install section."""
    lines = _executable_lines(
        _bounded_installer_section(
            content,
            "scripts/install.sh",
            POSIX_INSTALL_START,
            POSIX_INSTALL_END,
        )
    )
    commands = set()

    for index, line in enumerate(lines):
        loop = re.fullmatch(r"for cmd in ([a-z0-9 -]+); do", line)
        if loop is None:
            continue
        body = [item.strip() for item in _block_lines(lines, index, "done")]
        if (
            'WRAPPER="$BIN_DIR/cg-$cmd"' in body
            and any(item.startswith('cat > "$WRAPPER" <<') for item in body)
            and 'chmod +x "$WRAPPER"' in body
        ):
            commands.update("cg-" + name for name in loop.group(1).split())

    wrapper_indices = [
        index for index, line in enumerate(lines) if line.startswith("WRAPPER=")
    ]
    for position, index in enumerate(wrapper_indices):
        match = re.fullmatch(r'WRAPPER="\$BIN_DIR/(cg-[a-z0-9-]+)"', lines[index])
        if match is None:
            continue
        end = (
            wrapper_indices[position + 1]
            if position + 1 < len(wrapper_indices)
            else len(lines)
        )
        body = [item.strip() for item in lines[index + 1:end]]
        if (
            any(item.startswith('cat > "$WRAPPER" <<') for item in body)
            and 'chmod +x "$WRAPPER"' in body
        ):
            commands.add(match.group(1))

    for line in lines:
        match = re.fullmatch(
            r'(?P<variable>[A-Z][A-Z0-9_]*_DST)="\$BIN_DIR/(?P<name>cg-[a-z0-9-]+)"',
            line,
        )
        if match is None:
            continue
        variable_chmod = 'chmod +x "${}"'.format(match.group("variable"))
        literal_chmod = 'chmod +x "$BIN_DIR/{}"'.format(match.group("name"))
        if variable_chmod in lines or literal_chmod in lines:
            commands.add(match.group("name"))

    for index, line in enumerate(lines):
        if line != "for spec in \\":
            continue
        specs = []
        body_start = None
        for header_index in range(index + 1, len(lines)):
            declaration = lines[header_index].strip()
            terminal = declaration.endswith("; do")
            suffix = "; do" if terminal else "\\"
            if not declaration.endswith(suffix):
                raise HelpValidationError("POSIX installer summary declaration is malformed")
            quoted = declaration[: -len(suffix)].strip()
            match = re.fullmatch(r'"([a-z0-9-]+)\|[^"|]+\|[^"|]+"', quoted)
            if match is None:
                raise HelpValidationError("POSIX installer summary declaration is malformed")
            specs.append(match.group(1))
            if terminal:
                body_start = header_index
                break
        if body_start is None:
            raise HelpValidationError("POSIX installer summary declaration is not closed")
        body = [item.strip() for item in _block_lines(lines, body_start, "done")]
        if (
            'WRAPPER="$BIN_DIR/cg-$name"' in body
            and any(item.startswith('cat > "$WRAPPER" <<') for item in body)
            and 'chmod +x "$WRAPPER"' in body
        ):
            commands.update("cg-" + name for name in specs)
    return commands


def parse_windows_installer_inventory(content: bytes) -> set:
    """Parse only executable command declarations in the Windows install section."""
    lines = _executable_lines(
        _bounded_installer_section(
            content,
            "install.ps1",
            WINDOWS_INSTALL_START,
            WINDOWS_INSTALL_END,
        )
    )
    commands = set()
    for index, line in enumerate(lines):
        scripts = re.fullmatch(r'\$scripts\s*=\s*@\((?P<items>.*)\)', line)
        if scripts is None:
            continue
        names = re.findall(r'"([a-z0-9-]+)"', scripts.group("items"))
        normalized = re.sub(r'"[a-z0-9-]+"|[\s,]', "", scripts.group("items"))
        if not names or normalized:
            raise HelpValidationError("Windows installer script declaration is malformed")
        loop_index = next(
            (
                candidate
                for candidate in range(index + 1, len(lines))
                if lines[candidate] == "foreach ($script in $scripts) {"
            ),
            None,
        )
        if loop_index is None:
            continue
        body = [item.strip() for item in _block_lines(lines, loop_index, "}")]
        if (
            '$cmdPath = Join-Path $binDir "cg-$script.cmd"' in body
            and any(item.startswith("Set-Content -Path $cmdPath ") for item in body)
        ):
            commands.update("cg-" + name for name in names)

    destination_indices = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(
            r'\$[A-Za-z][A-Za-z0-9]*CmdDst\s*=\s*Join-Path \$binDir "cg-[a-z0-9-]+\.cmd"',
            line,
        )
    ]
    for position, index in enumerate(destination_indices):
        match = re.fullmatch(
            r'\$(?P<variable>[A-Za-z][A-Za-z0-9]*CmdDst)\s*=\s*Join-Path \$binDir "(?P<name>cg-[a-z0-9-]+)\.cmd"',
            lines[index],
        )
        assert match is not None
        end = (
            destination_indices[position + 1]
            if position + 1 < len(destination_indices)
            else len(lines)
        )
        body = "\n".join(lines[index + 1:end])
        source_variable = match.group("variable")[:-3] + "Src"
        if (
            re.search(
                r"^if \(Test-Path \${}\) \{{".format(source_variable),
                body,
                flags=re.MULTILINE,
            )
            and re.search(
                r"^\s*Copy-Item -Path \${} -Destination \${} -Force$".format(
                    source_variable, match.group("variable")
                ),
                body,
                flags=re.MULTILINE,
            )
        ):
            commands.add(match.group("name"))
    return commands


def require_exact_installer_inventory(
    expected: set, observed: set, label: str
) -> None:
    """Require one installer declaration set to match metadata exactly."""
    if expected != observed:
        raise HelpValidationError(
            "{} inventory mismatch: missing={!r}, extra={!r}".format(
                label,
                sorted(expected - observed),
                sorted(observed - expected),
            )
        )