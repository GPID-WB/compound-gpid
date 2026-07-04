#!/usr/bin/env bash
# scripts/unlink.sh
# Removes the Compound GPID symlinks from the current project's .github/.
# Does NOT delete any files in the global compound-gpid installation.
#
# Handles both the legacy whole-directory symlink (old cg-link behaviour)
# and the current per-subdirectory symlink approach.
#
# Requirements:
#   - python3 (used to safely remove the Compound GPID block from .gitignore)
#
# Run this from your project root:
#   cg-unlink

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
# --yes / -y  Skip all interactive confirmation prompts.
#             Used by CI (cg-unlink in E2E smoke tests) and any automation
#             that cannot supply keyboard input.
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) FORCE=1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
PROJECT_ROOT="$(pwd)"
TARGET_GITHUB_DIR="$PROJECT_ROOT/.github"
GITIGNORE_PATH="$PROJECT_ROOT/.gitignore"

# Subdirectories managed by Compound GPID
MANAGED_DIRS=("prompts" "skills" "agents" "instructions" "shared")

# Generated platform trees managed by Compound GPID
PLATFORM_TREES=(".claude" ".agents" ".opencode")

# Management marker used in copilot-instructions.md
COPILOT_INSTRUCTIONS_MARKER="<!-- compound-gpid:managed -->"
COPILOT_INSTRUCTIONS_DEST="$TARGET_GITHUB_DIR/copilot-instructions.md"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
print_cyan()   { printf '\033[0;36m%s\033[0m\n' "$1"; }
print_green()  { printf '\033[0;32m%s\033[0m\n' "$1"; }
print_yellow() { printf '\033[0;33m%s\033[0m\n' "$1"; }
print_gray()   { printf '\033[0;90m  %s\033[0m\n' "$1"; }
print_warn()   { printf '\033[0;33mWARNING: %s\033[0m\n' "$1" >&2; }
print_error()  { printf '\033[0;31mERROR: %s\033[0m\n' "$1" >&2; }

# ---------------------------------------------------------------------------
# Verify python3 is available
# ---------------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    print_error "python3 is required but not found."
    printf 'Install Xcode Command Line Tools: xcode-select --install\n' >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Check if .github exists
# ---------------------------------------------------------------------------
if [[ ! -e "$TARGET_GITHUB_DIR" && ! -L "$TARGET_GITHUB_DIR" ]]; then
    print_yellow ".github/ does not exist in this project. Nothing to unlink."
    exit 0
fi

# ---------------------------------------------------------------------------
# Handle legacy: .github/ itself is a whole-directory symlink
# ---------------------------------------------------------------------------
if [[ -L "$TARGET_GITHUB_DIR" ]]; then
    LINK_TARGET="$(readlink "$TARGET_GITHUB_DIR")"
    if [[ "$LINK_TARGET" != *"compound-gpid"* ]]; then
        print_warn ".github/ is a symlink but does not point to compound-gpid: $LINK_TARGET"
        print_warn "Only symlinks created by cg-link are managed by cg-unlink."
        exit 1
    fi

    printf '\n'
    print_cyan "Found legacy whole-directory symlink. Removing..."
    if [[ "$FORCE" -eq 0 ]]; then
        printf 'Remove the .github symlink from this project? [y/N] '
        read -r answer </dev/tty
        if [[ ! "$answer" =~ ^[Yy]$ ]]; then
            print_yellow "Aborted."
            exit 0
        fi
    fi
    rm -f "$TARGET_GITHUB_DIR"
    print_green "Legacy symlink removed."
    printf '\n'
    print_green "Unlinked."
    printf 'Run cg-link to re-link using the current per-subdirectory approach.\n'
    exit 0
fi

# ---------------------------------------------------------------------------
# Per-subdirectory unlink
# ---------------------------------------------------------------------------
printf '\n'
print_cyan "Compound GPID - Unlink"
print_cyan "======================"
printf '\n'
printf 'This will remove Compound GPID symlinks from .github/ in this project.\n'
printf 'The global Compound GPID installation is NOT affected.\n'
if [[ "$FORCE" -eq 0 ]]; then
    printf 'Proceed? [y/N] '
    read -r answer </dev/tty
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        print_yellow "Aborted."
        exit 0
    fi
fi

REMOVED_ANY=false

# Remove per-subdirectory symlinks
for dir in "${MANAGED_DIRS[@]}"; do
    SYMLINK_PATH="$TARGET_GITHUB_DIR/$dir"

    if [[ ! -e "$SYMLINK_PATH" && ! -L "$SYMLINK_PATH" ]]; then
        print_gray "$dir/ - not found, skipping"
        continue
    fi

    if [[ -L "$SYMLINK_PATH" ]]; then
        # readlink without -f is BSD-safe (macOS ships BSD readlink)
        LINK_TARGET="$(readlink "$SYMLINK_PATH")"
        if [[ "$LINK_TARGET" == *"compound-gpid"* ]]; then
            rm -f "$SYMLINK_PATH"
            print_gray "$dir/ - symlink removed"
            REMOVED_ANY=true
        else
            print_yellow "  $dir/ - symlink not from compound-gpid (target: $LINK_TARGET), skipping"
        fi
    else
        print_yellow "  $dir/ - real directory (not a symlink), skipping"
    fi
done

# Remove generated platform tree symlinks
for tree_dir in "${PLATFORM_TREES[@]}"; do
    TREE_PATH="$PROJECT_ROOT/$tree_dir"

    if [[ ! -e "$TREE_PATH" && ! -L "$TREE_PATH" ]]; then
        continue
    fi

    if [[ -L "$TREE_PATH" ]]; then
        LINK_TARGET="$(readlink "$TREE_PATH")"
        if [[ "$LINK_TARGET" == *"compound-gpid"* ]]; then
            rm -f "$TREE_PATH"
            print_gray "$tree_dir/ - symlink removed"
            REMOVED_ANY=true
        else
            print_yellow "  $tree_dir/ - symlink not from compound-gpid, skipping"
        fi
    fi
done

# Remove copilot-instructions.md only if it carries the management marker
if [[ -f "$COPILOT_INSTRUCTIONS_DEST" ]]; then
    if grep -qF "$COPILOT_INSTRUCTIONS_MARKER" "$COPILOT_INSTRUCTIONS_DEST" 2>/dev/null; then
        rm -f "$COPILOT_INSTRUCTIONS_DEST"
        print_gray "copilot-instructions.md - removed (was CG-managed)"
        REMOVED_ANY=true
    else
        print_yellow "  copilot-instructions.md - user-managed (no marker), leaving in place"
    fi
else
    print_gray "copilot-instructions.md - not found, skipping"
fi

# If .github/ is now empty, remove the directory
if [[ -d "$TARGET_GITHUB_DIR" ]]; then
    if [[ -z "$(ls -A "$TARGET_GITHUB_DIR" 2>/dev/null)" ]]; then
        rmdir "$TARGET_GITHUB_DIR"
        print_gray ".github/ - empty after unlinking, directory removed"
    fi
fi

# ---------------------------------------------------------------------------
# Remove CG-specific .gitignore entries
# ---------------------------------------------------------------------------
if [[ -f "$GITIGNORE_PATH" ]]; then
    python3 - "$GITIGNORE_PATH" <<'PYEOF'
import sys, re, tempfile, os

path = sys.argv[1]
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

if not re.search(r'(?m)^# Compound GPID managed items', content):
    sys.exit(0)

# Remove the CG block
cleaned = re.sub(
    r'(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.cg-docs/)[^\r\n]*\r?\n)*',
    '',
    content
).rstrip('\n')

out = cleaned + '\n' if cleaned else ''
tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path))
try:
    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
        f.write(out)
    os.replace(tmp_path, path)
except:
    try: os.unlink(tmp_path)
    except: pass
    raise

if cleaned:
    print('  Removed Compound GPID entries from .gitignore')
else:
    print('  Cleared .gitignore (was empty after CG block removal)')
PYEOF
fi

# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------
printf '\n'
if [[ "$REMOVED_ANY" == "true" ]]; then
    print_green "Unlinked."
    printf '\n'
    printf '\033[0;33mIMPORTANT: Restart VS Code / Positron.\033[0m\n'
    printf '  Copilot needs to re-index the workspace to reflect the unlinked state.\n'
else
    printf 'No Compound GPID symlinks were found in this project.\n'
fi
printf '\n'
