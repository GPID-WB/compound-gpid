"""Print the facts the host matrix needs. Reads only; writes nothing."""
import os
import platform
import shutil
import sys
from pathlib import Path

here = Path(__file__).resolve()
print("probe: ok")
print("python:", sys.version.split()[0], "at", sys.executable)
print("platform:", platform.system(), platform.release())
print("script:", here)
print("skill folder:", here.parent.parent)
print("install root:", here.parent.parent.parent)
print("cwd:", Path.cwd())
print("path has spaces:", " " in str(here))
print("under OneDrive:", "onedrive" in str(here).lower())
for tool in ("git", "gh", "node", "npx", "uv"):
    print(f"{tool}:", shutil.which(tool) or "not found")
siblings = sorted(p.name for p in here.parent.parent.parent.iterdir() if p.is_dir())
print("sibling skills:", len(siblings), "including", [s for s in siblings if s.startswith("cg-spike")])
print("env hints:", {k: v for k, v in os.environ.items() if k in ("CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "TERM_PROGRAM")})
