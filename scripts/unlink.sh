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
KILO_COMPAT_MIRROR_ROOT_REL=".compound-gpid/kilo-compat-skills"

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

same_realpath() {
    "$PYTHON_CMD" - "$1" "$2" <<'PYEOF'
import os
import sys
sys.exit(0 if os.path.realpath(sys.argv[1]) == os.path.realpath(sys.argv[2]) else 1)
PYEOF
}

compat_platform_for_target() {
    case "$1" in
        .claude/skills) printf 'claude-code\n' ;;
        .agents/skills) printf 'codex\n' ;;
        .opencode/skills) printf 'opencode\n' ;;
        *) return 1 ;;
    esac
}

all_unit_targets() {
    printf '%s\n' \
        '.github/prompts|directory|.github/prompts|copilot' '.github/skills|directory|.github/skills|copilot' '.github/agents|directory|.github/agents|copilot' '.github/instructions|directory|.github/instructions|copilot' '.github/shared|directory|.github/shared|copilot' '.github/copilot-instructions.md|file||copilot' \
        '.claude/commands|directory|.claude/commands|claude-code' '.claude/skills|directory|.claude/skills|claude-code' '.claude/agents|directory|.claude/agents|claude-code' '.claude/instructions|directory|.claude/instructions|claude-code' '.claude/shared|directory|.claude/shared|claude-code' '.claude/CLAUDE.md|file||claude-code' \
        '.agents/commands|directory|.agents/commands|codex' '.agents/skills|directory|.agents/skills|codex' '.agents/subagents|directory|.agents/subagents|codex' '.agents/instructions|directory|.agents/instructions|codex' '.agents/shared|directory|.agents/shared|codex' '.agents/AGENTS.md|file||codex' \
        '.opencode/commands|directory|.opencode/commands|opencode' '.opencode/skills|directory|.opencode/skills|opencode' '.opencode/agents|directory|.opencode/agents|opencode' '.opencode/instructions|directory|.opencode/instructions|opencode' '.opencode/shared|directory|.opencode/shared|opencode' '.opencode/AGENTS.md|file||opencode' '.opencode/opencode.json|file||opencode' \
        '.kilo/commands|directory|.kilo/commands|kilo' '.kilo/skills|directory|.kilo/skills|kilo' '.kilo/agents|directory|.kilo/agents|kilo' '.kilo/instructions|directory|.kilo/instructions|kilo' '.kilo/shared|directory|.kilo/shared|kilo' '.kilo/AGENTS.md|file||kilo' '.kilo/kilo.json|file||kilo'
}

remove_copy_directory_unit() {
    local target_rel="$1" target_path="$PROJECT_ROOT/$1"
    "$PYTHON_CMD" - "$target_path" "$target_rel" "$PROJECT_ROOT" <<'PYEOF'
import hashlib
import json
import os
import sys

target, target_rel, project = sys.argv[1:4]
project = os.path.abspath(project)
target = os.path.abspath(target)
if os.path.commonpath((project, target)) != project or target == project:
    sys.exit(1)
cursor = project
for part in os.path.relpath(target, project).split(os.sep):
    cursor = os.path.join(cursor, part)
    if os.path.lexists(cursor) and os.path.islink(cursor):
        sys.exit(1)
marker = os.path.join(target, ".compound-gpid-managed-copy.json")
if not os.path.isfile(marker) or os.path.islink(marker):
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
    cursor = target
    unsafe = False
    for part in rel.split("/"):
        cursor = os.path.join(cursor, part)
        if os.path.lexists(cursor) and os.path.islink(cursor):
            unsafe = True
            break
    if unsafe:
        print("WARN %s/%s crosses a symlink; leaving it in place" % (target_rel, rel))
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
    local target_rel="$1" source_rel="$2" platform="$3" target_path link_target mirror_platform mirror_path owned
    target_path="$PROJECT_ROOT/$target_rel"
    if [ ! -e "$target_path" ] && [ ! -L "$target_path" ]; then return 1; fi
    if [ -L "$target_path" ]; then
        link_target="$(readlink "$target_path")"
        owned=0
        if same_realpath "$target_path" "$COMPOUND_GPID_DIR/$source_rel"; then owned=1; fi
        mirror_platform="$(compat_platform_for_target "$target_rel" || true)"
        mirror_path=""
        [ -n "$mirror_platform" ] && mirror_path="$PROJECT_ROOT/$KILO_COMPAT_MIRROR_ROOT_REL/$mirror_platform"
        if [ -n "$mirror_path" ] && same_realpath "$target_path" "$mirror_path"; then owned=1; fi
        if [ "$owned" -eq 1 ]; then
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
        if remove_copy_directory_unit "$target_rel"; then
            [ -z "$(ls -A "$target_path" 2>/dev/null)" ] && rmdir "$target_path"
            return 0
        fi
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
    if [ -d "$path" ] && [ ! -L "$path" ] && [ -z "$(ls -A "$path" 2>/dev/null)" ]; then
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
        if same_realpath "$path" "$COMPOUND_GPID_DIR/$root"; then
            rm -f "$path"
            print_gray "$root/ - legacy whole-root symlink removed"
            REMOVED_ANY=true
        fi
    fi
done

while IFS='|' read -r target_rel unit_type source_rel platform; do
    if [ "$unit_type" = "directory" ]; then
        if remove_directory_unit "$target_rel" "$source_rel" "$platform"; then REMOVED_ANY=true; fi
    else
        status="$(remove_file_unit "$target_rel" || true)"
        case "$status" in
            REMOVED) print_gray "$target_rel - managed file removed"; REMOVED_ANY=true ;;
            USER_MODIFIED) print_warn "$target_rel was modified by the user; leaving it in place and dropping CG ownership." ;;
        esac
    fi
done < <(all_unit_targets)

MIRROR_REMOVED=false
for platform in claude-code codex opencode; do
    mirror_rel="$KILO_COMPAT_MIRROR_ROOT_REL/$platform"
    mirror_path="$PROJECT_ROOT/$mirror_rel"
    if remove_copy_directory_unit "$mirror_rel"; then
        REMOVED_ANY=true
        MIRROR_REMOVED=true
        if [ -d "$mirror_path" ] && [ ! -L "$mirror_path" ] && [ -z "$(ls -A "$mirror_path" 2>/dev/null)" ]; then rmdir "$mirror_path"; fi
    fi
done
mirror_root="$PROJECT_ROOT/$KILO_COMPAT_MIRROR_ROOT_REL"
if [ "$MIRROR_REMOVED" = true ] && [ -d "$mirror_root" ] && [ ! -L "$mirror_root" ] && [ -z "$(ls -A "$mirror_root" 2>/dev/null)" ]; then rmdir "$mirror_root"; fi

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
