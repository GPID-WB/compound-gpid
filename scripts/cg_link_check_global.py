"""Information-only, no-follow inspection of global Compound GPID Kilo entries."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

import secure_fs


def global_kilo_information(source: Path) -> list[str]:
    """Report related permission/plugin entries without ownership or write claims.

    Args:
        source: Local Compound GPID source, including custom installation paths.
    Returns:
        Information lines only. Missing, unsafe or invalid config never blocks.
    Example:
        ``global_kilo_information(Path("source").absolute())``.
    """
    location = "~/.config/kilo/kilo.jsonc"
    home = Path(os.environ.get("HOME") or Path.home())
    try:
        raw = secure_fs.secure_read_bytes(
            home, ".config/kilo/kilo.jsonc", reject_hardlinks=True,
            max_bytes=1024 * 1024,
        ).decode("utf-8-sig")
        # Keep quoted strings intact when removing JSONC comments/trailing commas.
        strings = r'"(?:\\.|[^"\\])*"'
        raw = re.sub(strings + r'|//[^\r\n]*|/\*[\s\S]*?\*/',
                     lambda m: m[0] if m[0].startswith('"') else " ", raw)
        raw = re.sub(strings + r'|,\s*(?=[}\]])',
                     lambda m: m[0] if m[0].startswith('"') else " ", raw)
        config = json.loads(raw)
        if not isinstance(config, dict):
            raise ValueError("root is not an object")
    except FileNotFoundError:
        return [f"{location}: absent; no settings changed"]
    except (OSError, ValueError, UnicodeError) as error:
        return [f"{location}: not assessed ({error}); preserved; never a blocker"]

    source_name = source.as_posix().casefold()

    def related(value: str) -> bool:
        normalized = value.replace("\\", "/").casefold()
        return source_name in normalized or any(name in normalized for name in (
            "compound-gpid", "cg-native-evidence", "cg-evidence-",
        ))

    rows = [f"{location}: user settings; no ownership or automatic cleanup"]

    def permissions(value: dict, prefix: str = "permission") -> None:
        for key, setting in sorted(value.items()):
            label = prefix + "[" + json.dumps(key) + "]"
            if related(key) or key == "*" or (key == "markdown_source" and not isinstance(setting, dict)):
                rows.append(label + " = " + json.dumps(setting, sort_keys=True))
            elif isinstance(setting, dict):
                permissions(setting, label)

    permission = config.get("permission", {})
    if isinstance(permission, dict):
        permissions(permission)
    else:
        rows.append("permission: not an object; preserved")
    plugins = config.get("plugin", [])
    if isinstance(plugins, list):
        for entry in plugins:
            if isinstance(entry, str) and related(entry):
                rows.append("plugin entry = " + json.dumps(entry))
    else:
        rows.append("plugin: not an array; preserved")
    if len(rows) == 1:
        rows.append("No related Compound GPID permission/plugin entries found")
    return rows
