#!/usr/bin/env bash
# scripts/install.sh
# One-time setup for Compound GPID on macOS.
# Run this after cloning the repo:
#   bash ~/.compound-gpid/scripts/install.sh
#
# What this does:
#   1. Verifies Git is available.
#   1b. Verifies Python is available (required for cg-index and cg-token-audit).
#   2. Tests that symlinks can be created on this machine.
#   3. Creates bash wrappers in bin/ and adds bin/ to PATH via shell profile
#      so cg-link, cg-unlink, cg-update are available from any terminal.
#   4. Initializes .cg-version with "latest" (if not already set).
#
# Options:
#   --uninstall   Remove PATH registration while preserving package wrappers.
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

resolve_python() {
    local candidate version
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        case "$version" in
            Python\ [0-9]*) ;;
            *) continue ;;
        esac
        "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue
        printf '%s\n' "$candidate"; return 0
    done
    return 1
}

PYTHON_CMD="$(resolve_python || true)"

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

    # Package-owned wrappers are source files required for later reinstall.
    BIN_DIR="$COMPOUND_GPID_DIR/bin"
    wrapper_count=0
    for wrapper in "$BIN_DIR"/cg-*; do
        [[ -e "$wrapper" ]] || continue
        wrapper_count=$((wrapper_count + 1))
    done
    print_gray "Preserved $wrapper_count package-owned cg-* wrappers in $BIN_DIR"

    # Remove PATH block from shell profile
    if [[ -f "$PROFILE_FILE" ]]; then
        if [[ -z "$PYTHON_CMD" ]]; then
            print_error "Python is required to update $PROFILE_FILE (checked: python3, python, py)."
            exit 1
        fi
        # Use Python to safely remove the block (avoids sed multiline issues)
        "$PYTHON_CMD" - "$PROFILE_FILE" "$CG_PROFILE_START" "$CG_PROFILE_END" <<'PYEOF'
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
except OSError:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
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
# Step 1b: Verify Python is available
# ---------------------------------------------------------------------------
print_gray "Checking for Python..."
if [[ -z "$PYTHON_CMD" ]]; then
    print_error "Python is required but not found (checked: python3, python, py)."
    printf '\n'
    printf 'Install Xcode Command Line Tools:\n' >&2
    printf '  xcode-select --install\n' >&2
    printf 'Or install Python from https://www.python.org/downloads/\n' >&2
    exit 1
fi
print_gray "Found: $($PYTHON_CMD --version 2>&1)"

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

# cg-index calls Python directly (not a .sh script), so it's generated
# separately rather than inside the loop above.
WRAPPER="$BIN_DIR/cg-index"
cat > "$WRAPPER" <<'EOF'
#!/bin/bash
# bin/cg-index — Compound GPID knowledge indexer (macOS)
# This file is committed to the repo; install.sh regenerates it on install/upgrade.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
resolve_python() {
    local candidate version
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        case "$version" in Python\ [0-9]*) ;; *) continue ;; esac
        "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue
        printf '%s\n' "$candidate"; return 0
    done
    return 1
}
PYTHON_CMD="$(resolve_python || true)"
if [[ -z "$PYTHON_CMD" ]]; then
    printf 'ERROR: Python is not available (checked: python3, python, py).\n' >&2
    exit 1
fi
exec "$PYTHON_CMD" "$SCRIPT_DIR/../scripts/cg_index.py" "$@"
EOF
chmod +x "$WRAPPER"
print_gray "Created: $WRAPPER"

# cg-brain-init also calls Python directly (same pattern as cg-index).
WRAPPER="$BIN_DIR/cg-brain-init"
cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
# bin/cg-brain-init — Team brain initialisation command (macOS/Linux)
# This file is committed to the repo; install.sh regenerates it on install/upgrade.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
resolve_python() {
    local candidate version
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        case "$version" in Python\ [0-9]*) ;; *) continue ;; esac
        "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue
        printf '%s\n' "$candidate"; return 0
    done
    return 1
}
PYTHON_CMD="$(resolve_python || true)"
if [[ -z "$PYTHON_CMD" ]]; then
    printf 'ERROR: Python is not available (checked: python3, python, py).\n' >&2
    exit 1
fi
exec "$PYTHON_CMD" "$SCRIPT_DIR/../scripts/team_brain/init.py" "$@"
EOF
chmod +x "$WRAPPER"
print_gray "Created: $WRAPPER"

# cg-render-artifact is committed as the installer source of truth.
CG_RENDER_ARTIFACT_SRC="$COMPOUND_GPID_DIR/bin/cg-render-artifact"
CG_RENDER_ARTIFACT_DST="$BIN_DIR/cg-render-artifact"
if [[ "$CG_RENDER_ARTIFACT_SRC" != "$CG_RENDER_ARTIFACT_DST" ]]; then
    cp "$COMPOUND_GPID_DIR/bin/cg-render-artifact" "$BIN_DIR/cg-render-artifact"
else
    print_gray "Already present: $CG_RENDER_ARTIFACT_DST"
fi
chmod +x "$BIN_DIR/cg-render-artifact"
print_gray "Registered: $BIN_DIR/cg-render-artifact"

# cg-token-audit calls the context/model-governance audit directly.
WRAPPER="$BIN_DIR/cg-token-audit"
cat > "$WRAPPER" <<'EOF'
#!/bin/bash
# bin/cg-token-audit -- Compound GPID token/context audit (macOS/Linux)
# This file is committed to the repo; install.sh regenerates it on install/upgrade.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
resolve_python() {
    local candidate version
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        case "$version" in Python\ [0-9]*) ;; *) continue ;; esac
        "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue
        printf '%s\n' "$candidate"; return 0
    done
    return 1
}
PYTHON_CMD="$(resolve_python || true)"
if [[ -z "$PYTHON_CMD" ]]; then
    printf 'ERROR: Python is not available (checked: python3, python, py).\n' >&2
    exit 1
fi
exec "$PYTHON_CMD" "$SCRIPT_DIR/../scripts/cg_audit_context.py" "$@"
EOF
chmod +x "$WRAPPER"
print_gray "Created: $WRAPPER"

for spec in \
    "diff-summary|diff|summarize current git diff and store full patch artifact" \
    "log-summary|log|summarize recent branch commits" \
    "problems-summary|problems|summarize VS Code or diagnostics problem output" \
    "test-summary|test|summarize existing test runner output without running tests" \
    "tree-summary|tree|summarize project tree structure"; do
    IFS='|' read -r name kind description <<< "$spec"
    WRAPPER="$BIN_DIR/cg-$name"
    cat > "$WRAPPER" <<EOF
#!/bin/bash
# bin/cg-$name -- $description.
# This file is committed to the repo; install.sh regenerates it on install/upgrade.
set -euo pipefail
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
resolve_python() { for candidate in python3 python py; do command -v "\$candidate" >/dev/null 2>&1 || continue; version="\$("\$candidate" --version 2>&1 || true)"; case "\$version" in Python\ [0-9]*) ;; *) continue ;; esac; "\$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue; printf '%s\n' "\$candidate"; return 0; done; return 1; }
PYTHON_CMD="\$(resolve_python || true)"
if [[ -z "\$PYTHON_CMD" ]]; then printf 'ERROR: Python is not available (checked: python3, python, py).\n' >&2; exit 1; fi
exec "\$PYTHON_CMD" "\$SCRIPT_DIR/../scripts/cg_summary.py" $kind "\$@"
EOF
    chmod +x "$WRAPPER"
    print_gray "Created: $WRAPPER"
done

# ---------------------------------------------------------------------------
# Step 4: Add bin/ to PATH via shell profile (idempotent)
# ---------------------------------------------------------------------------
print_gray "Registering cg-* commands via PATH ($PROFILE_FILE)..."

# Idempotent: remove any existing CG block before rewriting.
# Uses Python to safely handle multiline removal.
if [[ -f "$PROFILE_FILE" ]] && grep -qF "$CG_PROFILE_START" "$PROFILE_FILE" 2>/dev/null; then
    "$PYTHON_CMD" - "$PROFILE_FILE" "$CG_PROFILE_START" "$CG_PROFILE_END" <<'PYEOF'
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
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
PYEOF
    print_gray "Removed stale Compound GPID block from $PROFILE_FILE"
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
printf '  cg-render-artifact   -- Render or validate one workflow artifact\n'
printf '  cg-token-audit       -- Analyze token/context usage  (run from project root)\n'
printf '\n'
printf 'To uninstall: bash "%s/scripts/install.sh" --uninstall\n' "$COMPOUND_GPID_DIR"
printf '\n'
printf 'Quick start:\n'
printf '  1. Restart your terminal\n'
printf '  2. cd /path/to/your/project\n'
printf '  3. cg-link\n'
printf '\n'
