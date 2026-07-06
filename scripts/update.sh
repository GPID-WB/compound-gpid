#!/usr/bin/env bash
# scripts/update.sh
# Updates the global Compound GPID installation.
# Because all projects use per-subdirectory symlinks to the same shared
# .github/ subdirectories, this single command propagates changes to every
# linked project's prompts/, skills/, agents/, and instructions/ immediately.
#
# For copilot-instructions.md (a copied file, not a symlink), this script also
# refreshes the copy in the current working directory if the management marker
# is present. Remove the marker to opt out of auto-refresh.
#
# Run from anywhere:
#   cg-update               -- use current version preference (default: latest)
#   cg-update v0.2.0        -- pin to a specific release
#   cg-update latest        -- unpin and track main
#   cg-update --list        -- browse available releases
#   cg-update --fix         -- repair a broken installation
#
# Environment:
#   CG_INTERNAL_CALL=1      -- set by cg-link to suppress copilot-instructions
#                              refresh (cg-link handles it in its own Step 4)

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
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
        case "$version" in
            Python\ [0-9]*) printf '%s\n' "$candidate"; return 0 ;;
        esac
    done
    return 1
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COPILOT_INSTRUCTIONS_MARKER="<!-- compound-gpid:managed -->"
VERSION_FILE="$COMPOUND_GPID_DIR/.cg-version"

# Regex that matches 3-component release tags only (e.g. v0.2.0)
# Dev tags (4-component, e.g. v0.2.0.9000) are excluded from user-visible output.
RELEASE_TAG_PATTERN='^v[0-9]+\.[0-9]+\.[0-9]+$'

# Accepts all valid version inputs: release tags, dev tags, and 'latest'.
# git tag names are case-sensitive: V0.2.0 is not the same as v0.2.0.
VERSION_ACCEPT_PATTERN='^(latest|v[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?)$'

# ---------------------------------------------------------------------------
# generate_copilot_instructions <template_path> <project_root> <marker>
# Defined before the main body to allow the end-of-script refresh to call it.
# ---------------------------------------------------------------------------
generate_copilot_instructions() {
    local template_path="$1"
    local project_root="$2"
    local marker="$3"

    "$PYTHON_CMD" - "$template_path" "$project_root" "$marker" <<'PYEOF'
import sys, re, os

template_path, project_root, marker = sys.argv[1], sys.argv[2], sys.argv[3]

charter_path = os.path.join(project_root, 'compound-gpid.md')
local_path   = os.path.join(project_root, 'compound-gpid.local.md')

def extract_fm_value(path, key):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.match(r'^---[ \t]*\n(.*?)\n---', content, re.DOTALL)
        if not m:
            return ''
        fm = m.group(1)
        pattern = r'(?m)^\s*' + re.escape(key) + r':\s*["\']?([^"\'\\r\\n]+)["\']?\s*$'
        vm = re.search(pattern, fm)
        return vm.group(1).strip() if vm else ''
    except Exception:
        return ''

project_name = extract_fm_value(charter_path, 'project-name') or '<project-name>'
language     = extract_fm_value(local_path, 'language')     or '<not configured>'
project_type = extract_fm_value(local_path, 'project-type') or '<not configured>'
review_depth = extract_fm_value(local_path, 'review-depth') or '<not configured>'
r_syntax     = extract_fm_value(local_path, 'r-syntax')

languages = language
if r_syntax and re.search(r'\bR\b', language, re.IGNORECASE):
    languages = f'{language} (R dialect: {r_syntax})'

for val in (project_name, project_type, languages, review_depth):
    if '{{' in val:
        print('ERROR: A config value contains a placeholder token which would corrupt the output.', file=sys.stderr)
        sys.exit(1)

with open(template_path, 'r', encoding='utf-8') as f:
    template = f.read()

if not template.strip():
    print(f'ERROR: Template file is empty: {template_path}. Run cg-update --fix.', file=sys.stderr)
    sys.exit(1)

output = template
output = output.replace('{{project-name}}', project_name)
output = output.replace('{{project-type}}', project_type)
output = output.replace('{{languages}}',    languages)
output = output.replace('{{review-depth}}', review_depth)

sep = '\r\n' if '\r\n' in output else '\n'
sys.stdout.write(marker + sep + output)
PYEOF
}

# ---------------------------------------------------------------------------
# Validate install exists
# ---------------------------------------------------------------------------
if [[ ! -d "$COMPOUND_GPID_DIR" ]]; then
    print_error "Compound GPID installation directory not found at: $COMPOUND_GPID_DIR"
    printf '\nSee docs/installation.md for setup instructions.\n' >&2
    exit 1
fi

# Verify git is available
if ! command -v git &>/dev/null; then
    print_error "git is not available. Install Git from https://git-scm.com/download/mac"
    printf 'Or via Xcode command line tools: xcode-select --install\n' >&2
    exit 1
fi

# Verify Python is available
PYTHON_CMD="$(resolve_python || true)"
if [[ -z "$PYTHON_CMD" ]]; then
    print_error "Python is required but not found (checked: python3, python, py)."
    printf 'Install Xcode Command Line Tools or Python from https://www.python.org/downloads/\n' >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
VERSION_ARG=""
DO_LIST=false
DO_FIX=false

for arg in "$@"; do
    case "$arg" in
        --list)   DO_LIST=true ;;
        --fix)    DO_FIX=true  ;;
        --*)      print_error "Unknown option: $arg"; printf 'Usage: cg-update [version|latest|--list|--fix]\n' >&2; exit 1 ;;
        *)        VERSION_ARG="$arg" ;;
    esac
done

# Trim whitespace from version argument
VERSION_ARG="${VERSION_ARG#"${VERSION_ARG%%[![:space:]]*}"}"
VERSION_ARG="${VERSION_ARG%"${VERSION_ARG##*[![:space:]]}"}"

# Guard against invalid version input
if [[ -n "$VERSION_ARG" ]] && ! [[ "$VERSION_ARG" =~ $VERSION_ACCEPT_PATTERN ]]; then
    print_error "Invalid version: '$VERSION_ARG'. Expected a tag like 'v0.2.0', 'latest', or use --list to browse."
    exit 1
fi

# ---------------------------------------------------------------------------
# --fix: repair a broken installation
# ---------------------------------------------------------------------------
if [[ "$DO_FIX" == "true" ]]; then
    printf '\n'
    print_cyan "Repairing compound-gpid installation..."
    print_gray "Install dir: $COMPOUND_GPID_DIR"
    printf '\n'

    (
        cd "$COMPOUND_GPID_DIR"
        print_gray "Cleaning untracked files..."
        git clean -fd
        print_gray "Discarding local changes..."
        git checkout .
        print_gray "Pulling latest..."
        if ! git pull --ff-only; then
            print_error "git pull --ff-only failed"
            exit 1
        fi
    )

    printf '\n'
    print_green "Repair complete."
    print_gray "Run cg-update again to verify."
    printf '\n'
    exit 0
fi

# ---------------------------------------------------------------------------
# Resolve version mode
# ---------------------------------------------------------------------------
if [[ -n "$VERSION_ARG" ]]; then
    VERSION_MODE="$VERSION_ARG"
elif [[ -f "$VERSION_FILE" ]]; then
    # Read first non-empty line and trim
    VERSION_MODE="$(grep -v '^[[:space:]]*$' "$VERSION_FILE" | head -1 | tr -d '[:space:]')"
    [[ -z "$VERSION_MODE" ]] && VERSION_MODE="latest"
else
    VERSION_MODE="latest"
fi

# Validate .cg-version content format (catches manual edits with garbage values)
if [[ -z "$VERSION_ARG" ]] && ! [[ "$VERSION_MODE" =~ $VERSION_ACCEPT_PATTERN ]]; then
    print_error "Malformed .cg-version: '$VERSION_MODE'. Expected a tag like 'v0.2.0' or 'latest'. Edit or delete $VERSION_FILE."
    exit 1
fi

LATEST_TAG=""

# ---------------------------------------------------------------------------
# --list: show available releases and exit
# ---------------------------------------------------------------------------
if [[ "$DO_LIST" == "true" ]]; then
    printf '\n'
    print_cyan "Fetching available releases..."
    (cd "$COMPOUND_GPID_DIR" && git fetch --tags 2>/dev/null) || \
        print_warn "git fetch --tags failed -- showing cached tag data. Check your network connection."

    ALL_TAGS="$(cd "$COMPOUND_GPID_DIR" && git tag --list 'v*' --sort=-version:refname 2>/dev/null || true)"
    RELEASE_TAGS="$(printf '%s\n' "$ALL_TAGS" | grep -E "$RELEASE_TAG_PATTERN" || true)"

    # Determine current label
    CURRENT_PIN="$VERSION_MODE"
    if [[ "$CURRENT_PIN" == "latest" ]]; then
        MODE_LABEL="main (latest)"
    elif [[ "$CURRENT_PIN" =~ ^v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        MODE_LABEL="$CURRENT_PIN (dev -- not listed above)"
    else
        MODE_LABEL="$CURRENT_PIN (pinned)"
    fi

    # When in latest mode, find which release tag HEAD points to
    INSTALLED_TAG=""
    if [[ "$CURRENT_PIN" == "latest" ]]; then
        INSTALLED_TAG="$(cd "$COMPOUND_GPID_DIR" && \
            git tag --points-at HEAD 2>/dev/null | grep -E "$RELEASE_TAG_PATTERN" | head -1 || true)"
    fi

    printf '\n'
    print_cyan "Available releases:"
    if [[ -n "$RELEASE_TAGS" ]]; then
        while IFS= read -r tag; do
            [[ -z "$tag" ]] && continue
            MARKER=""
            if [[ "$tag" == "$CURRENT_PIN" || "$tag" == "$INSTALLED_TAG" ]]; then
                MARKER="  <-- current"
            fi
            printf '  %s%s\n' "$tag" "$MARKER"
        done <<< "$RELEASE_TAGS"
    else
        print_gray "No releases found."
        print_gray "See: https://github.com/GPID-WB/compound-gpid/releases"
    fi

    printf '\n'
    print_gray "Current: $MODE_LABEL"
    printf '\n'
    printf '  cg-update <version>  -- pin to a specific release\n'
    printf '  cg-update latest     -- unpin and track main\n'
    printf '\n'
    exit 0
fi

# ---------------------------------------------------------------------------
# Show active mode
# ---------------------------------------------------------------------------
if [[ "$VERSION_MODE" == "latest" ]]; then
    print_gray "Mode: tracking main (latest)"
else
    print_gray "Mode: pinned ($VERSION_MODE)"
fi

# ---------------------------------------------------------------------------
# Latest mode: track main HEAD
# ---------------------------------------------------------------------------
if [[ "$VERSION_MODE" == "latest" ]]; then

    # Persist "latest" when the user explicitly unpins with 'cg-update latest'
    if [[ "$VERSION_ARG" == "latest" ]]; then
        printf 'latest' > "${VERSION_FILE}.tmp" && mv "${VERSION_FILE}.tmp" "$VERSION_FILE"
    fi

    (
        cd "$COMPOUND_GPID_DIR"

        # If previously on a detached HEAD (pinned tag), switch back to main first
        HEAD_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
        if [[ "$HEAD_BRANCH" == "HEAD" ]]; then
            print_gray "Switching from pinned version back to main..."
            if ! git checkout main 2>/dev/null; then
                print_error "git checkout main failed"
                exit 1
            fi
        fi

        # Capture commit hash before update
        BEFORE="$(git rev-parse --short HEAD 2>/dev/null)"

        print_cyan "Checking for updates..."

        # Reset any accidental local changes before pulling.
        # Warn first if there are uncommitted changes so developers don't lose work silently.
        if ! git diff --quiet 2>/dev/null; then
            print_warn "Local changes in compound-gpid installation will be reset before pulling."
        fi
        git checkout . 2>/dev/null || true

        if ! git pull --ff-only; then
            print_error "git pull failed"
            printf 'To repair: run cg-update --fix\n' >&2
            exit 1
        fi

        AFTER="$(git rev-parse --short HEAD 2>/dev/null)"

        if [[ -n "$BEFORE" && "$BEFORE" != "$AFTER" ]]; then
            printf '\n'
            print_green "Updated: $BEFORE -> $AFTER"
            printf '\n'
            print_cyan "Changes:"
            git log --oneline "$BEFORE..$AFTER"
            printf '\n'
            print_gray "Managed subdirectories (prompts/, skills/, agents/, instructions/) are"
            print_gray "updated in all linked projects immediately via symlinks."
        else
            print_green "Already up to date."
        fi

        # --- Regenerate platform trees after pull (source repo only) ---
        # If this is the compound-gpid source repo, regenerate .claude/, .agents/,
        # and .opencode/ from the updated .github/ canonical assets so linked
        # consumer projects see fresh platform trees via their symlinks/junctions.
        TARGET_MAPPING="$COMPOUND_GPID_DIR/.github/shared/target-mapping.json"
        GENERATOR_SCRIPT="$COMPOUND_GPID_DIR/scripts/cg_generate_targets.py"
        if [[ -f "$TARGET_MAPPING" ]] && [[ -f "$GENERATOR_SCRIPT" ]]; then
            printf '\n'
            print_gray "Regenerating platform trees..."
            if "$PYTHON_CMD" "$GENERATOR_SCRIPT" --root "$COMPOUND_GPID_DIR" --all 2>&1 | sed 's/^/  /'; then
                print_gray "Platform trees regenerated."
            else
                print_warn "Platform tree generation failed — existing trees remain linked."
            fi
        fi
    )

# ---------------------------------------------------------------------------
# Pinned mode: checkout a specific tag (detached HEAD)
# ---------------------------------------------------------------------------
else
    print_cyan "Checking out $VERSION_MODE..."

    (
        cd "$COMPOUND_GPID_DIR"

        # Fetch tags first — fault-tolerant
        git fetch --tags 2>/dev/null || \
            print_warn "git fetch --tags failed -- continuing with cached tag data"

        ALL_TAGS="$(git tag --list 'v*' --sort=-version:refname 2>/dev/null || true)"
        RELEASE_TAGS_FILTERED="$(printf '%s\n' "$ALL_TAGS" | grep -E "$RELEASE_TAG_PATTERN" || true)"
        LATEST_TAG_LOCAL="$(printf '%s\n' "$RELEASE_TAGS_FILTERED" | head -1)"

        # Validate the tag exists
        if ! printf '%s\n' "$ALL_TAGS" | grep -qxF "$VERSION_MODE"; then
            HINT=""
            if [[ -n "$RELEASE_TAGS_FILTERED" ]]; then
                HINT="$(printf '\nAvailable releases:\n'; printf '%s\n' "$RELEASE_TAGS_FILTERED" | head -5 | sed 's/^/  /')"
            fi
            print_error "Release '$VERSION_MODE' not found.$HINT"
            printf '\nRun: cg-update --list   to see all available releases.\n' >&2
            exit 1
        fi

        # Checkout the tag (detached HEAD is expected for pinned mode)
        if ! git checkout "$VERSION_MODE" 2>/dev/null; then
            print_error "git checkout $VERSION_MODE failed"
            exit 1
        fi

        # Persist the version preference only after successful checkout
        printf '%s' "$VERSION_MODE" > "${VERSION_FILE}.tmp" && mv "${VERSION_FILE}.tmp" "$VERSION_FILE"

        printf '\n'
        print_green "Pinned to $VERSION_MODE."
        printf '\n'
        print_gray "Managed subdirectories (prompts/, skills/, agents/, instructions/) are"
        print_gray "updated in all linked projects immediately via symlinks."
        printf '\n'
        print_gray "Run: cg-update latest   to return to tracking main."

        # Hint if there is a newer release
        if [[ -n "$LATEST_TAG_LOCAL" && "$LATEST_TAG_LOCAL" != "$VERSION_MODE" ]]; then
            printf '\n'
            print_yellow "Note: $LATEST_TAG_LOCAL is available. Run: cg-update $LATEST_TAG_LOCAL"
        fi
    )
fi

# ---------------------------------------------------------------------------
# Refresh manifest-managed copied platform files in the current project
# ---------------------------------------------------------------------------
CWD_MANIFEST_PATH="$(pwd)/.compound-gpid/managed-files.json"
if [[ "${CG_INTERNAL_CALL:-}" != "1" ]] && [[ -f "$CWD_MANIFEST_PATH" ]]; then
    "$PYTHON_CMD" - "$CWD_MANIFEST_PATH" "$COMPOUND_GPID_DIR" <<'PYEOF'
import hashlib
import json
import os
import shutil
import sys

manifest_path, compound_dir = sys.argv[1:]
project_root = os.getcwd()

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def contained_path(root, relative, label):
    if not relative or os.path.isabs(relative):
        raise ValueError(f"{label} path must be relative: {relative}")
    root_abs = os.path.abspath(root)
    full = os.path.abspath(os.path.join(root_abs, relative))
    if os.path.commonpath([root_abs, full]) != root_abs:
        raise ValueError(f"{label} path escapes its root: {relative}")
    return full

with open(manifest_path, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
files = manifest.setdefault("files", {})
changed = False
for target_rel in list(files.keys()):
    record = files[target_rel]
    try:
        target_path = contained_path(project_root, target_rel, "Managed target")
        source_path = contained_path(compound_dir, record.get("source", ""), "Managed source")
    except ValueError as exc:
        print(f"WARNING: Invalid managed file manifest entry, skipping refresh: {target_rel} ({exc})")
        continue
    if not os.path.exists(source_path):
        print(f"WARNING: Managed source missing, leaving current project file unchanged: {record.get('source', '')}")
        continue
    if os.path.islink(source_path):
        print(f"WARNING: Managed source is a symlink, skipping refresh: {record.get('source', '')}")
        continue
    if not os.path.exists(target_path):
        print(f"WARNING: Managed file missing in current project, dropping manifest entry: {target_rel}")
        files.pop(target_rel, None)
        changed = True
        continue
    if os.path.islink(target_path):
        print(f"WARNING: Managed target is a symlink, skipping refresh: {target_rel}")
        continue
    if sha256(target_path) != record.get("checksum"):
        print(f"WARNING: Managed file modified by user, skipping refresh: {target_rel}")
        continue
    shutil.copy2(source_path, target_path)
    files[target_rel] = {"source": record.get("source", ""), "checksum": sha256(target_path)}
    changed = True
    print(f"  Refreshed managed platform file: {target_rel}")
if changed:
    if files:
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
    else:
        os.unlink(manifest_path)
PYEOF
fi

# ---------------------------------------------------------------------------
# Refresh copilot-instructions.md in the current project (if linked)
# ---------------------------------------------------------------------------
# Skip when called internally by cg-link (it handles the refresh itself).
CWD_GITHUB="$(pwd)/.github"
CWD_COPILOT_DEST="$CWD_GITHUB/copilot-instructions.md"

# Refresh copilot-instructions.md — skipped when called internally by cg-link
# (cg-link handles the refresh itself to avoid doing it twice).
if [[ "${CG_INTERNAL_CALL:-}" != "1" ]] && \
   [[ -d "$CWD_GITHUB" ]] && [[ -f "$CWD_COPILOT_DEST" ]]; then

    if grep -qF "$COPILOT_INSTRUCTIONS_MARKER" "$CWD_COPILOT_DEST" 2>/dev/null; then
        TEMPLATE_PATH="$COMPOUND_GPID_DIR/.github/copilot-instructions.template.md"
        if [[ -f "$TEMPLATE_PATH" ]]; then
            EXISTING_CONTENT="$(< "$CWD_COPILOT_DEST")"
            GENERATED="$(generate_copilot_instructions "$TEMPLATE_PATH" "$(pwd)" "$COPILOT_INSTRUCTIONS_MARKER")"
            if [[ "$GENERATED" != "$EXISTING_CONTENT" ]]; then
                printf '%s' "$GENERATED" > "${CWD_COPILOT_DEST}.tmp" && mv "${CWD_COPILOT_DEST}.tmp" "$CWD_COPILOT_DEST"
                print_gray "Refreshed copilot-instructions.md in current project."
            else
                print_gray "copilot-instructions.md up to date."
            fi
        fi
    fi
fi

printf '\n'

# ---------------------------------------------------------------------------
# Structural migration: docs/ -> .cg-docs/
# ---------------------------------------------------------------------------
# Applies when run from a linked project (CWD_GITHUB exists).
# Runs unconditionally — NOT gated by CG_INTERNAL_CALL — so that a
# cg-link on a project with old layout triggers migration immediately.
if [[ -d "$CWD_GITHUB" ]]; then
    CWD_ROOT="$(pwd)"
    CG_DOCS_DIR="$CWD_ROOT/.cg-docs"
    DIRS_TO_MIGRATE=("brainstorms" "plans" "solutions")
    MIGRATED_ANY=false

    for dir in "${DIRS_TO_MIGRATE[@]}"; do
        OLD_PATH="$CWD_ROOT/docs/$dir"
        NEW_PATH="$CG_DOCS_DIR/$dir"

        if [[ -d "$OLD_PATH" ]]; then
            mkdir -p "$CG_DOCS_DIR"
            if [[ ! -d "$NEW_PATH" ]]; then
                mv "$OLD_PATH" "$NEW_PATH"
                print_gray "Migrated: docs/$dir/ -> .cg-docs/$dir/"
                MIGRATED_ANY=true
            else
                # Target exists — merge file by file, skip conflicts
                CONFLICTS=0
                while IFS= read -r -d '' file; do
                    REL="${file#"$OLD_PATH/"}"
                    DEST="$NEW_PATH/$REL"
                    DEST_DIR="$(dirname "$DEST")"
                    mkdir -p "$DEST_DIR"
                    if [[ ! -f "$DEST" ]]; then
                        mv "$file" "$DEST"
                    else
                        CONFLICTS=$((CONFLICTS + 1))
                        print_warn "Skipped (already exists): $REL"
                    fi
                done < <(find "$OLD_PATH" -type f -print0)
                # Remove old dir if now empty
                find "$OLD_PATH" -type d -empty -delete 2>/dev/null || true
                MIGRATED_ANY=true
                if [[ "$CONFLICTS" -gt 0 ]]; then
                    print_gray "Merged: docs/$dir/ -> .cg-docs/$dir/ ($CONFLICTS files skipped - already exist)"
                else
                    print_gray "Migrated: docs/$dir/ -> .cg-docs/$dir/"
                fi
            fi
        fi
    done

    # Clean up empty docs/ directory if all CG subdirs moved and nothing else remains
    OLD_DOCS_DIR="$CWD_ROOT/docs"
    if [[ -d "$OLD_DOCS_DIR" ]] && [[ "$MIGRATED_ANY" == "true" ]]; then
        if [[ -z "$(ls -A "$OLD_DOCS_DIR" 2>/dev/null)" ]]; then
            rmdir "$OLD_DOCS_DIR"
            print_gray "Removed empty docs/ directory."
        fi
    fi
fi
