#!/usr/bin/env bash
# scripts/install.sh
# One-time setup for Compound GPID on macOS.
# Run this after cloning the repo:
#   bash ~/.compound-gpid/scripts/install.sh
#
# What this does:
#   1. Verifies Git is available.
#   1b. Verifies python3 is available (required for cg-index knowledge indexing).
#   2. Tests that symlinks can be created on this machine.
#   3. Creates bash wrappers in bin/ and adds bin/ to PATH via shell profile
#      so cg-link, cg-unlink, cg-update are available from any terminal.
#   4. Initializes .cg-version with "latest" (if not already set).
#
# Options:
#   --uninstall   Remove bin/ wrappers and PATH block from shell profile.
#
# This script is idempotent - running it again updates the wrappers
# and PATH entry without creating duplicates. An existing .cg-version
# preference is preserved on upgrade.

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve the install directory (always the parent of scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"

# ---------------------------------------------------------------------------
# Helper: print coloured output (no deps required)
# ---------------------------------------------------------------------------
print_cyan()    { printf '\033[0;36m%s\033[0m\n' "$1"; }
print_green()   { printf '\033[0;32m%s\033[0m\n' "$1"; }
print_yellow()  { printf '\033[0;33m%s\033[0m\n' "$1"; }
print_gray()    { printf '\033[0;90m  %s\033[0m\n' "$1"; }
print_error()   { printf '\033[0;31mERROR: %s\033[0m\n' "$1" >&2; }

# ---------------------------------------------------------------------------
# Determine shell profile file
# ---------------------------------------------------------------------------
# Target ~/.zshrc for zsh (covers VS Code integrated terminal and most macOS
# terminal emulators — Terminal.app opens interactive login shells which source
# both .zprofile and .zshrc).
# For bash, target ~/.bashrc.
# Users with login-shell-only setups should add the block to ~/.zprofile instead.
detect_profile() {
    local shell_name
    shell_name="$(basename "${SHELL:-/bin/zsh}")"
    if [[ "$shell_name" == "zsh" ]]; then
        echo "$HOME/.zshrc"
    elif [[ "$shell_name" == "bash" ]]; then
        echo "$HOME/.bashrc"
    else
        print_yellow "Warning: unrecognized shell '$shell_name'. Defaulting to ~/.bashrc." >&2
        print_yellow "  You may need to manually add the PATH block to your shell profile." >&2
        echo "$HOME/.bashrc"
    fi
}

PROFILE_FILE="$(detect_profile)"

# CG block markers used in shell profile
CG_PROFILE_START="# --- Compound GPID ---"
CG_PROFILE_END="# --- End Compound GPID ---"

# ---------------------------------------------------------------------------
# --uninstall mode
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--uninstall" ]]; then
    printf '\n'
    print_cyan "Compound GPID - Uninstall"
    print_cyan "========================="
    printf '\n'

    # Remove bin/ wrappers
    BIN_DIR="$COMPOUND_GPID_DIR/bin"
    for cmd in cg-link cg-unlink cg-update; do
        if [[ -f "$BIN_DIR/$cmd" ]]; then
            rm -f "$BIN_DIR/$cmd"
            print_gray "Removed: $BIN_DIR/$cmd"
        fi
    done

    # Remove PATH block from shell profile
    if [[ -f "$PROFILE_FILE" ]]; then
        # Use python3 to safely remove the block (avoids sed multiline issues)
        python3 - "$PROFILE_FILE" "$CG_PROFILE_START" "$CG_PROFILE_END" <<'PYEOF'
import sys, re, tempfile, os
path, start_marker, end_marker = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, 'r') as f:
    content = f.read()
pattern = re.escape(start_marker) + r'.*?' + re.escape(end_marker) + r'\n?'
updated = re.sub(pattern, '', content, flags=re.DOTALL).rstrip('\n')
out = updated + '\n' if updated else ''
tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path))
try:
    with os.fdopen(tmp_fd, 'w') as f:
        f.write(out)
    os.replace(tmp_path, path)
except:
    try: os.unlink(tmp_path)
    except: pass
    raise
PYEOF
        print_gray "Removed Compound GPID block from $PROFILE_FILE"
    fi

    printf '\n'
    print_green "Uninstalled."
    printf '\n'
    exit 0
fi

# ---------------------------------------------------------------------------
# Normal install
# ---------------------------------------------------------------------------
printf '\n'
print_cyan "Compound GPID - Install"
print_cyan "========================"
printf '\n'

# ---------------------------------------------------------------------------
# Step 1: Verify git is available
# ---------------------------------------------------------------------------
print_gray "Checking for Git..."
if ! command -v git &>/dev/null; then
    print_error "Git is not available on this system."
    printf '\n'
    printf 'Install Git from: https://git-scm.com/download/mac\n' >&2
    printf 'Or via Xcode command line tools: xcode-select --install\n' >&2
    printf 'Then re-run this script.\n' >&2
    exit 1
fi
GIT_VERSION="$(git --version)"
print_gray "Found: $GIT_VERSION"

# ---------------------------------------------------------------------------
# Step 1b: Verify python3 is available
# ---------------------------------------------------------------------------
print_gray "Checking for python3..."
if ! command -v python3 &>/dev/null; then
    print_error "python3 is required but not found."
    printf '\n'
    printf 'Install Xcode Command Line Tools:\n' >&2
    printf '  xcode-select --install\n' >&2
    printf 'Or install Python from https://www.python.org/downloads/\n' >&2
    exit 1
fi
print_gray "Found: $(python3 --version 2>&1)"

# ---------------------------------------------------------------------------
# Step 2: Test symlink capability
# ---------------------------------------------------------------------------
print_gray "Testing symlink capability..."
TEMP_TARGET="$(mktemp -d "${TMPDIR:-/tmp}/cg-gpid-symlink-target-XXXXXX")"
TEMP_LINK="${TMPDIR:-/tmp}/cg-gpid-symlink-test-$$"

SYMLINK_OK=false
if ln -s "$TEMP_TARGET" "$TEMP_LINK" 2>/dev/null; then
    SYMLINK_OK=true
    rm -f "$TEMP_LINK"
fi
rm -rf "$TEMP_TARGET"

if [[ "$SYMLINK_OK" != "true" ]]; then
    print_error "Symlink creation failed on this machine."
    printf '\n' >&2
    printf 'Compound GPID uses symlinks to link managed subdirectories\n' >&2
    printf '(prompts/, skills/, agents/, instructions/) inside your\n' >&2
    printf "project's .github/ to the shared installation.\n" >&2
    printf '\n' >&2
    printf 'This usually indicates a filesystem restriction. Check that\n' >&2
    printf 'the install path is on a local APFS/HFS+ volume.\n' >&2
    exit 1
fi
print_gray "Symlinks supported."

# ---------------------------------------------------------------------------
# Step 3: Create bin/ wrappers
# ---------------------------------------------------------------------------
print_gray "Creating cg-* commands in bin/..."
BIN_DIR="$COMPOUND_GPID_DIR/bin"
mkdir -p "$BIN_DIR"

for cmd in link unlink update; do
    WRAPPER="$BIN_DIR/cg-$cmd"
    cat > "$WRAPPER" <<EOF
#!/bin/bash
# cg-$cmd — Compound GPID wrapper (generated by install.sh)
set -euo pipefail
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
exec "\$SCRIPT_DIR/../scripts/$cmd.sh" "\$@"
EOF
    chmod +x "$WRAPPER"
    print_gray "Created: $WRAPPER"
done

# cg-index calls python3 directly (not a .sh script), so it's generated
# separately rather than inside the loop above.
WRAPPER="$BIN_DIR/cg-index"
cat > "$WRAPPER" <<'EOF'
#!/bin/bash
# bin/cg-index — Compound GPID knowledge indexer (macOS)
# This file is committed to the repo; install.sh regenerates it on install/upgrade.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/../scripts/cg_index.py" "$@"
EOF
chmod +x "$WRAPPER"
print_gray "Created: $WRAPPER"

# ---------------------------------------------------------------------------
# Step 4: Add bin/ to PATH via shell profile (idempotent)
# ---------------------------------------------------------------------------
print_gray "Registering cg-* commands via PATH ($PROFILE_FILE)..."

# Idempotent: remove any existing CG block before rewriting.
# Uses python3 (zero-dependency on macOS) to safely handle multiline removal.
if [[ -f "$PROFILE_FILE" ]] && grep -qF "$CG_PROFILE_START" "$PROFILE_FILE" 2>/dev/null; then
    python3 - "$PROFILE_FILE" "$CG_PROFILE_START" "$CG_PROFILE_END" <<'PYEOF'
import sys, re, tempfile, os
path, start_marker, end_marker = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, 'r') as f:
    content = f.read()
pattern = re.escape(start_marker) + r'.*?' + re.escape(end_marker) + r'\n?'
updated = re.sub(pattern, '', content, flags=re.DOTALL).rstrip('\n')
if updated or content:
    out = updated + '\n' if updated else ''
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path))
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            f.write(out)
        os.replace(tmp_path, path)
    except:
        try: os.unlink(tmp_path)
        except: pass
        raise
PYEOF
    print_gray "Removed stale Compound GPID block from $PROFILE_FILE"
fi

# Step 4a: Remove stale function-based install artifacts (migration from pre-bin/ installs).
# Older compound-gpid versions added cg-*() shell functions and COMPOUND_GPID_DIR exports
# directly to the profile. These shadow the new bin/ wrappers and must be removed.
if [[ -f "$PROFILE_FILE" ]]; then
    python3 - "$PROFILE_FILE" <<'PYEOF'
import sys, re, tempfile, os

path = sys.argv[1]
with open(path, 'r') as f:
    lines = f.readlines()

stale = [
    re.compile(r'^cg-\w+\s*\(\)'),          # cg-cmd() { ... } function definitions
    re.compile(r'^export COMPOUND_GPID_DIR='), # old COMPOUND_GPID_DIR variable export
    re.compile(r'^# Compound GPID\s*$'),      # old unfenced section header
]

cleaned = [line for line in lines if not any(p.match(line) for p in stale)]

# Collapse consecutive blank lines left behind by removals
final = []
prev_blank = False
for line in cleaned:
    is_blank = line.strip() == ''
    if is_blank and prev_blank:
        continue
    final.append(line)
    prev_blank = is_blank

if final != lines:
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path))
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            f.writelines(final)
        os.replace(tmp_path, path)
    except:
        try: os.unlink(tmp_path)
        except: pass
        raise
    removed = sum(1 for a, b in zip(lines, final + [''] * len(lines)) if a != b)
    print(f"  Removed stale cg-* function definitions from {path}", file=sys.stderr)
PYEOF
fi

# Check if bin/ is already on PATH via an existing bare export line
# (e.g., manually added). If so, skip adding the block.
ALREADY_ON_PATH=false
if [[ -f "$PROFILE_FILE" ]] && grep -qF "$BIN_DIR" "$PROFILE_FILE" 2>/dev/null; then
    ALREADY_ON_PATH=true
fi

if [[ "$ALREADY_ON_PATH" == "true" ]]; then
    print_gray "Already on PATH (found in $PROFILE_FILE)"
else
    # Build a portable PATH entry: prefer $HOME-relative path to survive repo moves
    if [[ "$BIN_DIR" == "$HOME/"* ]]; then
        PATH_ENTRY="\$HOME/${BIN_DIR#$HOME/}"
    else
        PATH_ENTRY="$BIN_DIR"
    fi
    # Append the CG block to the profile
    {
        printf '\n%s\n' "$CG_PROFILE_START"
        printf 'export PATH="%s:$PATH"\n' "$PATH_ENTRY"
        printf '%s\n' "$CG_PROFILE_END"
    } >> "$PROFILE_FILE"
    print_gray "Added to PATH: $BIN_DIR"
fi

# ---------------------------------------------------------------------------
# Step 5: Initialize .cg-version
# ---------------------------------------------------------------------------
print_gray "Initializing version preference..."
VERSION_FILE="$COMPOUND_GPID_DIR/.cg-version"
if [[ ! -f "$VERSION_FILE" ]]; then
    printf 'latest' > "${VERSION_FILE}.tmp" && mv "${VERSION_FILE}.tmp" "$VERSION_FILE"
    print_gray "Created .cg-version: latest"
else
    EXISTING_VER="$(< "$VERSION_FILE")"
    print_gray "Existing .cg-version preserved: $EXISTING_VER"
fi

# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------
printf '\n'
print_green "Compound GPID installed successfully!"
printf '\n'
printf '  Location : %s\n' "$COMPOUND_GPID_DIR"
printf '  Commands : %s\n' "$BIN_DIR"
printf '  Profile  : %s\n' "$PROFILE_FILE"
printf '\n'
printf '\033[0;33mIMPORTANT: Restart your terminal and VS Code / Positron:\033[0m\n'
printf '  The PATH change only takes effect in new processes.\n'
printf '  Copilot will not pick up changes until VS Code / Positron is restarted.\n'
printf '\n'
printf 'Available commands (after restarting):\n'
printf '  cg-link    -- Link current project to Compound GPID  (run from project root)\n'
printf '  cg-unlink  -- Unlink current project                 (run from project root)\n'
printf '  cg-update  -- Pull latest updates                    (run from anywhere)\n'
printf '  cg-update <version>  -- Pin to a specific release (e.g. cg-update v0.2.0)\n'
printf '  cg-update latest     -- Unpin and return to tracking main\n'
printf '  cg-update --list     -- Browse available releases\n'
printf '\n'
printf 'To uninstall: bash "%s/scripts/install.sh" --uninstall\n' "$COMPOUND_GPID_DIR"
printf '\n'
printf 'Quick start:\n'
printf '  1. Restart your terminal\n'
printf '  2. cd /path/to/your/project\n'
printf '  3. cg-link\n'
printf '\n'
