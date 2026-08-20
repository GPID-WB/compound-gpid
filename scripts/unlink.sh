#!/usr/bin/env bash
# scripts/unlink.sh
# Removes Compound GPID-managed install units from the current project.

set -euo pipefail

FORCE=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --yes|-y|--force|-Force) FORCE=1; shift ;;
        *) printf 'WARNING: Unrecognized argument %s -- ignoring\n' "$1" >&2; shift ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(pwd)"
MANIFEST_PATH="$PROJECT_ROOT/.compound-gpid/managed-files.json"
GITIGNORE_PATH="$PROJECT_ROOT/.gitignore"
COPILOT_INSTRUCTIONS_MARKER="<!-- compound-gpid:managed -->"

print_cyan()   { printf '\033[0;36m%s\033[0m\n' "$1"; }
print_green()  { printf '\033[0;32m%s\033[0m\n' "$1"; }
print_yellow() { printf '\033[0;33m%s\033[0m\n' "$1"; }
print_gray()   { printf '\033[0;90m  %s\033[0m\n' "$1"; }
print_warn()   { printf '\033[0;33mWARNING: %s\033[0m\n' "$1" >&2; }
print_error()  { printf '\033[0;31mERROR: %s\033[0m\n' "$1" >&2; }

resolve_python() {
    local candidate version
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        case "$version" in Python\ [0-9]*) printf '%s\n' "$candidate"; return 0 ;; esac
    done
    return 1
}

PYTHON_CMD="$(resolve_python || true)"
if [ -z "$PYTHON_CMD" ]; then
    print_error "Python is required but not found (checked: python3, python, py)."
    exit 1
fi

all_unit_targets() {
    printf '%s\n' \
        '.github/prompts|directory' '.github/skills|directory' '.github/agents|directory' '.github/instructions|directory' '.github/shared|directory' '.github/copilot-instructions.md|file' \
        '.claude/commands|directory' '.claude/skills|directory' '.claude/agents|directory' '.claude/instructions|directory' '.claude/shared|directory' '.claude/CLAUDE.md|file' \
        '.agents/commands|directory' '.agents/skills|directory' '.agents/subagents|directory' '.agents/instructions|directory' '.agents/shared|directory' '.agents/AGENTS.md|file' \
        '.opencode/commands|directory' '.opencode/skills|directory' '.opencode/agents|directory' '.opencode/instructions|directory' '.opencode/shared|directory' '.opencode/AGENTS.md|file' '.opencode/opencode.json|file' \
        '.kilo/commands|directory' '.kilo/skills|directory' '.kilo/agents|directory' '.kilo/instructions|directory' '.kilo/shared|directory' '.kilo/AGENTS.md|file' '.kilo/kilo.json|file'
}

remove_copy_directory_unit() {
    local target_rel="$1" target_path="$PROJECT_ROOT/$1"
    "$PYTHON_CMD" - "$target_path" "$target_rel" <<'PYEOF'
import hashlib
import json
import os
import sys

target, target_rel = sys.argv[1:3]
marker = os.path.join(target, ".compound-gpid-managed-copy.json")
if not os.path.isfile(marker):
    sys.exit(1)
try:
    with open(marker, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, ValueError):
    sys.exit(1)
if data.get("schemaVersion") != 1 or not isinstance(data.get("files"), dict):
    sys.exit(1)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

removed_any = False
target_real = os.path.realpath(target)
for rel, recorded in data["files"].items():
    if rel.startswith("/") or rel.startswith("..") or rel == ".." or rel == "." or "\\" in rel or ":" in rel:
        continue
    file_path = os.path.join(target, rel)
    # The marker is a plain editable file, so never delete anything that does
    # not resolve strictly inside the managed directory (guards keys such as
    # docs/../../victim.txt).
    real = os.path.realpath(file_path)
    if real != target_real and not real.startswith(target_real + os.sep):
        print("WARN %s/%s has an unsafe managed-copy path; leaving it in place" % (target_rel, rel))
        continue
    if os.path.isfile(real) and sha256(real) == recorded:
        os.unlink(real)
        print("  %s/%s - managed copy removed" % (target_rel, rel))
        removed_any = True
    elif os.path.exists(real):
        print("WARN %s/%s was modified by the user; leaving it in place" % (target_rel, rel))

try:
    os.unlink(marker)
    print("  %s - managed-copy marker removed" % target_rel)
    removed_any = True
except OSError:
    pass

# Prune empty subdirectories bottom-up, never following or removing symlinks.
for root, dirs, _files in os.walk(target, topdown=False):
    for d in dirs:
        candidate = os.path.join(root, d)
        if os.path.islink(candidate):
            continue
        try:
            os.rmdir(candidate)
        except OSError:
            pass

sys.exit(0 if removed_any else 1)
PYEOF
}

remove_directory_unit() {
    local target_rel="$1" target_path link_target
    target_path="$PROJECT_ROOT/$target_rel"
    if [ ! -e "$target_path" ] && [ ! -L "$target_path" ]; then return 1; fi
    if [ -L "$target_path" ]; then
        link_target="$(readlink "$target_path")"
        if [[ "$link_target" == *compound-gpid* ]]; then
            rm -f "$target_path"
            print_gray "$target_rel - symlink removed"
            return 0
        fi
        print_yellow "  $target_rel - non-Compound symlink, skipping"
        return 1
    fi
    if [ -d "$target_path" ]; then
        # Real directory: remove only if it is a managed copy-directory
        # (marker present); otherwise treat as user-owned and skip.
        if remove_copy_directory_unit "$target_rel"; then return 0; fi
    fi
    print_yellow "  $target_rel - user-owned path, skipping"
    return 1
}

remove_file_unit() {
    local target_rel="$1" target_path
    target_path="$PROJECT_ROOT/$target_rel"
    if [ "$target_rel" = ".github/copilot-instructions.md" ]; then
        if [ -f "$target_path" ] && grep -qF "$COPILOT_INSTRUCTIONS_MARKER" "$target_path" 2>/dev/null; then
            rm -f "$target_path"
            print_gray "$target_rel - removed"
            return 0
        fi
        return 1
    fi
    "$PYTHON_CMD" - "$MANIFEST_PATH" "$target_rel" "$target_path" <<'PYEOF'
import hashlib
import json
import os
import sys

manifest_path, target_rel, target_path = sys.argv[1:]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if not os.path.exists(manifest_path):
    sys.exit(1)
with open(manifest_path, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
files = manifest.setdefault("files", {})
record = files.get(target_rel)
if not record:
    sys.exit(1)
if not os.path.exists(target_path):
    files.pop(target_rel, None)
    status = "MISSING"
elif sha256(target_path) == record.get("checksum"):
    os.unlink(target_path)
    files.pop(target_rel, None)
    status = "REMOVED"
else:
    files.pop(target_rel, None)
    status = "USER_MODIFIED"
if files:
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
else:
    os.unlink(manifest_path)
print(status)
PYEOF
}

remove_gitignore_block() {
    [ -f "$GITIGNORE_PATH" ] || return 0
    "$PYTHON_CMD" - "$GITIGNORE_PATH" <<'PYEOF'
import os
import re
import sys
import tempfile

path = sys.argv[1]
with open(path, "r", encoding="utf-8", errors="replace") as handle:
    content = handle.read()
    pattern = r"(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.claude/|\.agents/|\.opencode/|\.kilo/|\.compound-gpid/)[^\r\n]*\r?\n)*"
updated = re.sub(pattern, "", content).rstrip("\n")
if updated == content.rstrip("\n"):
    sys.exit(0)
if not updated.strip():
    os.unlink(path)
    print("  .gitignore - removed (empty after CG cleanup)")
    sys.exit(0)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(updated + "\n")
    os.replace(tmp, path)
finally:
    if os.path.exists(tmp):
        os.unlink(tmp)
print("  .gitignore - CG entries removed")
PYEOF
}

remove_empty_root() {
    local root="$1" path="$PROJECT_ROOT/$1"
    if [ -d "$path" ] && [ -z "$(ls -A "$path" 2>/dev/null)" ]; then
        rmdir "$path"
        print_gray "$root/ - empty, removed"
    fi
}

# NOTE: The Kilo markdown_source permission in the global kilo.jsonc is keyed on
# the Compound GPID *installation* path, not the project. Multiple projects may
# share one installation, so removing the permission on unlink would break Kilo
# command loading for any other still-linked project. The permission is therefore
# intentionally left in place on unlink; a stale allow entry is harmless.

printf '\n'
print_cyan "Compound GPID - Unlink"
print_cyan "======================"
printf '\n'
printf 'This will remove only Compound GPID-managed install units from this project.\n'
if [ "$FORCE" -eq 0 ]; then
    printf 'Proceed? [y/N] '
    read -r answer </dev/tty
    case "$answer" in [Yy]*) ;; *) print_yellow "Aborted."; exit 0 ;; esac
fi

REMOVED_ANY=false

for root in .github .claude .agents .opencode .kilo; do
    path="$PROJECT_ROOT/$root"
    if [ -L "$path" ]; then
        link_target="$(readlink "$path")"
        if [[ "$link_target" == *compound-gpid* ]]; then
            rm -f "$path"
            print_gray "$root/ - legacy whole-root symlink removed"
            REMOVED_ANY=true
        fi
    fi
done

while IFS='|' read -r target_rel unit_type; do
    if [ "$unit_type" = "directory" ]; then
        if remove_directory_unit "$target_rel"; then REMOVED_ANY=true; fi
    else
        status="$(remove_file_unit "$target_rel" || true)"
        case "$status" in
            REMOVED) print_gray "$target_rel - managed file removed"; REMOVED_ANY=true ;;
            USER_MODIFIED) print_warn "$target_rel was modified by the user; leaving it in place and dropping CG ownership." ;;
        esac
    fi
done < <(all_unit_targets)

for root in .github .claude .agents .opencode .kilo .compound-gpid; do remove_empty_root "$root"; done
remove_gitignore_block

# Remove only checksum-owned manifest projection files; user-modified projected
# files and user roots are preserved (managed by scripts/cg_project_projection.py).
if [ -f "$PROJECT_ROOT/.compound-gpid/projection-ownership.json" ]; then
    set +e
    PROJECTION_OUTPUT="$("$PYTHON_CMD" "$COMPOUND_GPID_DIR/scripts/cg_project_projection.py" --project-root "$PROJECT_ROOT" --unlink 2>&1)"
    PROJECTION_STATUS=$?
    set -e
    if [ "$PROJECTION_STATUS" -ne 0 ]; then
        print_warn "Could not remove manifest projection files."
    else
        print_gray "Removed checksum-owned manifest projection files."
    fi
fi

printf '\n'
if [ "$REMOVED_ANY" = true ]; then
    print_green "Unlinked."
else
    print_yellow "Nothing to unlink - no Compound GPID-managed units found."
fi
printf 'To re-link at any time, run: cg-link\n\n'
