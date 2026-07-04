#!/usr/bin/env bash
# scripts/link.sh
# Links the current project to the global Compound GPID installation by creating
# per-subdirectory symlinks inside .github/ for the managed Compound GPID
# directories (prompts/, skills/, agents/, instructions/) and generating
# copilot-instructions.md with a management marker.
#
# Run this from your project root:
#   cg-link
#
# Key behaviours:
#   - Creates .github/ as a real directory if it does not exist.
#   - Adds symlinks only for CG-managed subdirectories, leaving all existing
#     .github/ content (workflows, templates, CODEOWNERS, etc.) untouched.
#   - Generates copilot-instructions.md with a <!-- compound-gpid:managed --> marker.
#     Remove the marker to take ownership of the file and prevent cg-update
#     from overwriting it.
#   - Runs cg-update first to ensure the global clone is up to date.
#   - Gitignores only the CG-managed items, not the entire .github/ folder.

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
FORCE=0
PLATFORMS=""
for arg in "$@"; do
    case "$arg" in
        --yes|-y) FORCE=1 ;;
        --platforms=*) PLATFORMS="${arg#--platforms=}" ;;
        --platforms) shift; PLATFORMS="$1" ;;
    esac
done

# Default: copilot only (preserves existing behavior)
if [[ -z "$PLATFORMS" ]]; then
    PLATFORMS="copilot"
fi

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_GITHUB="$COMPOUND_GPID_DIR/.github"
PROJECT_ROOT="$(pwd)"
TARGET_GITHUB_DIR="$PROJECT_ROOT/.github"

# Subdirectories managed by Compound GPID (each gets its own symlink)
MANAGED_DIRS=("prompts" "skills" "agents" "instructions" "shared")

# Management marker and destination for copilot-instructions.md
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
# generate_copilot_instructions <template_path> <project_root> <marker>
# Reads the template, parses frontmatter from compound-gpid.md and
# compound-gpid.local.md, substitutes placeholders, and writes the result
# (with management marker prepended) to stdout.
# Must be defined before the main body calls it in Step 4.
# ---------------------------------------------------------------------------
generate_copilot_instructions() {
    local template_path="$1"
    local project_root="$2"
    local marker="$3"

    python3 - "$template_path" "$project_root" "$marker" <<'PYEOF'
import sys, re, os

template_path, project_root, marker = sys.argv[1], sys.argv[2], sys.argv[3]

charter_path = os.path.join(project_root, 'compound-gpid.md')
local_path   = os.path.join(project_root, 'compound-gpid.local.md')

def extract_fm_value(path, key):
    """Extract a YAML frontmatter value by key. Returns '' if not found."""
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

# Read project-name from charter
project_name = extract_fm_value(charter_path, 'project-name') or '<project-name>'

# Read per-user config from compound-gpid.local.md
language     = extract_fm_value(local_path, 'language')     or '<not configured>'
project_type = extract_fm_value(local_path, 'project-type') or '<not configured>'
review_depth = extract_fm_value(local_path, 'review-depth') or '<not configured>'
r_syntax     = extract_fm_value(local_path, 'r-syntax')

# Build languages string — append R dialect when configured
languages = language
if r_syntax and re.search(r'\bR\b', language, re.IGNORECASE):
    languages = f'{language} (R dialect: {r_syntax})'

# Guard: reject config values that contain placeholder tokens
for val in (project_name, project_type, languages, review_depth):
    if '{{' in val:
        print('ERROR: A config value contains a placeholder token which would corrupt the output.'
              ' Check compound-gpid.md and compound-gpid.local.md.', file=sys.stderr)
        sys.exit(1)

# Read template
with open(template_path, 'r', encoding='utf-8') as f:
    template = f.read()

if not template.strip():
    print(f'ERROR: Template file is empty: {template_path}. Run cg-update --fix.', file=sys.stderr)
    sys.exit(1)

# Substitute placeholders (literal, not regex — mirrors PS .Replace() behaviour)
output = template
output = output.replace('{{project-name}}', project_name)
output = output.replace('{{project-type}}', project_type)
output = output.replace('{{languages}}',    languages)
output = output.replace('{{review-depth}}', review_depth)

# Prepend the management marker, matching the template's line-ending style
sep = '\r\n' if '\r\n' in output else '\n'
sys.stdout.write(marker + sep + output)
PYEOF
}

# ---------------------------------------------------------------------------
# Validate the global install exists
# ---------------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    print_error "python3 is required but not found."
    printf 'Install Xcode Command Line Tools: xcode-select --install\n' >&2
    exit 1
fi

if [[ ! -d "$COMPOUND_GPID_DIR" ]]; then
    print_error "Compound GPID installation directory not found at: $COMPOUND_GPID_DIR"
    printf '\nSee docs/installation.md for setup instructions.\n' >&2
    exit 1
fi

if [[ ! -d "$SOURCE_GITHUB" ]]; then
    print_error "Expected .github/ not found inside $COMPOUND_GPID_DIR. The installation may be corrupted."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 1: Update the global clone before linking
# ---------------------------------------------------------------------------
# Ensures the user always links against the latest version.
# CG_INTERNAL_CALL suppresses the copilot-instructions.md refresh in update.sh
# because link.sh handles that refresh itself in Step 4 to avoid doing it twice.
printf '\n'
print_cyan "Updating Compound GPID..."

if ! CG_INTERNAL_CALL=1 "$COMPOUND_GPID_DIR/scripts/update.sh"; then
    print_warn "Could not update Compound GPID (offline?). Continuing with current version."
fi

# Show which version is active after the update
VERSION_FILE="$COMPOUND_GPID_DIR/.cg-version"
if [[ -f "$VERSION_FILE" ]]; then
    ACTIVE_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
else
    ACTIVE_VERSION="latest"
fi
[[ -z "$ACTIVE_VERSION" ]] && ACTIVE_VERSION="latest"

if [[ "$ACTIVE_VERSION" == "latest" ]]; then
    print_gray "Version: tracking main (latest)"
else
    print_gray "Version: $ACTIVE_VERSION (pinned)"
fi

printf '\n'
print_cyan "Compound GPID - Link"
print_cyan "===================="
printf '\n'

# ---------------------------------------------------------------------------
# Step 2: Handle .github/ directory in this project
# ---------------------------------------------------------------------------
if [[ -L "$TARGET_GITHUB_DIR" ]]; then
    # Legacy: .github/ itself is a whole-directory symlink (old cg-link behaviour).
    LINK_TARGET="$(readlink "$TARGET_GITHUB_DIR")"
    if [[ "$LINK_TARGET" == *"compound-gpid"* ]]; then
        printf '.github/ is a legacy Compound GPID symlink - migrating to per-subdirectory symlinks...\n'
        rm -f "$TARGET_GITHUB_DIR"
        mkdir -p "$TARGET_GITHUB_DIR"
        print_gray "Migrated: .github/ is now a real directory."
    fi
elif [[ ! -d "$TARGET_GITHUB_DIR" ]]; then
    mkdir -p "$TARGET_GITHUB_DIR"
    print_gray "Created .github/ directory."
fi
# If .github/ already exists as a real directory, leave it untouched.

# ---------------------------------------------------------------------------
# Step 3: Create per-subdirectory symlinks
# ---------------------------------------------------------------------------
print_gray "Linking managed directories..."

for dir in "${MANAGED_DIRS[@]}"; do
    SYMLINK_PATH="$TARGET_GITHUB_DIR/$dir"
    SYMLINK_TARGET="$SOURCE_GITHUB/$dir"

    # Verify the source exists
    if [[ ! -d "$SYMLINK_TARGET" ]]; then
        print_warn "Source not found, skipping: $SYMLINK_TARGET"
        continue
    fi

    if [[ -L "$SYMLINK_PATH" ]]; then
        # Already a symlink — check if it points to this compound-gpid install
        EXISTING_TARGET="$(readlink "$SYMLINK_PATH")"
        if [[ "$EXISTING_TARGET" == *"compound-gpid"* ]]; then
            print_gray "$dir/ - already linked"
            continue
        else
            print_warn "$dir/ is a symlink pointing to: $EXISTING_TARGET"
            if [[ "$FORCE" -eq 0 ]]; then
                printf '  Relink %s/ to Compound GPID instead? [y/N] ' "$dir"
                read -r answer </dev/tty
                if [[ ! "$answer" =~ ^[Yy]$ ]]; then
                    print_gray "Skipping $dir/"
                    continue
                fi
            fi
            rm -f "$SYMLINK_PATH"
        fi
    elif [[ -d "$SYMLINK_PATH" ]]; then
        # Real directory exists — cannot create symlink without risking data loss
        print_error "A real directory .github/$dir/ already exists in this project."
        printf 'Compound GPID cannot create a symlink here without risking data loss.\n\n' >&2
        printf 'To resolve: rename or remove .github/%s/ manually, then re-run cg-link.\n' "$dir" >&2
        exit 1
    fi

    if ln -s "$SYMLINK_TARGET" "$SYMLINK_PATH"; then
        print_gray "$dir/ - linked"
    else
        print_error "Failed to create symlink for $dir/"
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Step 3b: Link generated platform trees (if --platforms includes non-copilot)
# ---------------------------------------------------------------------------
# Map platform IDs to their generated tree directories in the global clone.
declare -A PLATFORM_TREES=(
    ["claude-code"]=".claude"
    ["codex"]=".agents"
    ["opencode"]=".opencode"
)

if [[ "$PLATFORMS" != "copilot" ]]; then
    print_gray "Linking platform trees (platforms: $PLATFORMS)..."

    IFS=',' read -ra PLATFORM_LIST <<< "$PLATFORMS"
    for platform in "${PLATFORM_LIST[@]}"; do
        platform=$(echo "$platform" | xargs) # trim whitespace
        tree_dir="${PLATFORM_TREES[$platform]:-}"

        if [[ -z "$tree_dir" ]]; then
            print_warn "Unknown platform '$platform' — skipping"
            continue
        fi

        source_tree="$COMPOUND_GPID_DIR/$tree_dir"
        target_tree="$PROJECT_ROOT/$tree_dir"

        if [[ ! -d "$source_tree" ]]; then
            print_warn "Source tree not found for $platform: $source_tree — skipping"
            continue
        fi

        # Handle existing target directory
        if [[ -L "$target_tree" ]]; then
            EXISTING_TARGET="$(readlink "$target_tree")"
            if [[ "$EXISTING_TARGET" == *"compound-gpid"* ]]; then
                print_gray "$tree_dir/ - already linked"
                continue
            else
                print_warn "$tree_dir/ is a symlink pointing to: $EXISTING_TARGET"
                if [[ "$FORCE" -eq 0 ]]; then
                    printf '  Relink %s/ to Compound GPID instead? [y/N] ' "$tree_dir"
                    read -r answer </dev/tty
                    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
                        print_gray "Skipping $tree_dir/"
                        continue
                    fi
                fi
                rm -f "$target_tree"
            fi
        elif [[ -d "$target_tree" ]]; then
            print_error "A real directory $tree_dir/ already exists in this project."
            printf 'Compound GPID cannot create a symlink here without risking data loss.\n\n' >&2
            printf 'To resolve: rename or remove %s/ manually, then re-run cg-link.\n' "$tree_dir" >&2
            exit 1
        fi

        if ln -s "$source_tree" "$target_tree"; then
            print_gray "$tree_dir/ - linked ($platform)"
        else
            print_error "Failed to create symlink for $tree_dir/"
            exit 1
        fi
    done
fi

# ---------------------------------------------------------------------------
# Step 4: Generate copilot-instructions.md from template
# ---------------------------------------------------------------------------
print_gray "Linking copilot-instructions.md..."

EXISTING_CONTENT=""
if [[ -f "$COPILOT_INSTRUCTIONS_DEST" ]]; then
    EXISTING_CONTENT="$(< "$COPILOT_INSTRUCTIONS_DEST")"
fi

USER_MANAGED=false
if [[ -n "$EXISTING_CONTENT" ]] && ! grep -qF "$COPILOT_INSTRUCTIONS_MARKER" "$COPILOT_INSTRUCTIONS_DEST" 2>/dev/null; then
    USER_MANAGED=true
fi

if [[ "$USER_MANAGED" == "true" ]]; then
    print_yellow "  copilot-instructions.md - user-managed (marker absent), skipping"
    print_gray "To restore CG management, delete the file and re-run cg-link."
else
    TEMPLATE_PATH="$COMPOUND_GPID_DIR/.github/copilot-instructions.template.md"
    if [[ ! -f "$TEMPLATE_PATH" ]]; then
        print_error "Template not found at: $TEMPLATE_PATH. Run cg-update --fix to repair."
        exit 1
    fi

    GENERATED="$(generate_copilot_instructions "$TEMPLATE_PATH" "$PROJECT_ROOT" "$COPILOT_INSTRUCTIONS_MARKER")"
    if [[ "$GENERATED" != "$EXISTING_CONTENT" ]]; then
        printf '%s' "$GENERATED" > "${COPILOT_INSTRUCTIONS_DEST}.tmp" && mv "${COPILOT_INSTRUCTIONS_DEST}.tmp" "$COPILOT_INSTRUCTIONS_DEST"
        print_gray "copilot-instructions.md - generated"
    else
        print_gray "copilot-instructions.md - up to date"
    fi
fi

# ---------------------------------------------------------------------------
# Step 5: Update .gitignore with CG-specific entries only
# ---------------------------------------------------------------------------
# Gitignore only the CG-managed items so the user's own .github/ content
# (workflows, templates, CODEOWNERS, etc.) remains tracked by git.
# Strategy: idempotent remove-then-rewrite of the CG block.
GITIGNORE_PATH="$PROJECT_ROOT/.gitignore"
CG_GITIGNORE_MARKER="# Compound GPID managed items (junctions + copied file - do not commit)"

# Build the CG gitignore block
CG_GITIGNORE_BLOCK="$CG_GITIGNORE_MARKER"
for dir in "${MANAGED_DIRS[@]}"; do
    CG_GITIGNORE_BLOCK="$CG_GITIGNORE_BLOCK
.github/$dir/"
done
CG_GITIGNORE_BLOCK="$CG_GITIGNORE_BLOCK
.github/copilot-instructions.md"

if [[ -f "$GITIGNORE_PATH" ]]; then
    # Remove any existing CG block before rewriting (handles version upgrades cleanly)
    python3 - "$GITIGNORE_PATH" "$CG_GITIGNORE_BLOCK" <<'PYEOF'
import sys, re, tempfile, os

path      = sys.argv[1]
new_block = sys.argv[2]

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Ensure trailing newline for consistent processing
if content and not content.endswith('\n'):
    content += '\n'

# Remove any existing CG block
cleaned = re.sub(
    r'(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.cg-docs/)[^\r\n]*\r?\n)*',
    '',
    content
).rstrip('\n')

separator = '\n\n' if cleaned else ''
out = cleaned + separator + new_block + '\n'
tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path))
try:
    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
        f.write(out)
    os.replace(tmp_path, path)
except:
    try: os.unlink(tmp_path)
    except: pass
    raise
PYEOF
    print_gray "Updated CG entries in .gitignore"
else
    printf '%s\n' "$CG_GITIGNORE_BLOCK" > "$GITIGNORE_PATH"
    print_gray "Created .gitignore with CG entries"
fi

# Remove stale .cg-docs/ gitignore entry from older setups
if [[ -f "$GITIGNORE_PATH" ]]; then
    python3 - "$GITIGNORE_PATH" <<'PYEOF'
import sys, re, tempfile, os
path = sys.argv[1]
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
if re.search(r'(?i)# Compound GPID knowledge base', content):
    cleaned = re.sub(r'(?m)^# Compound GPID knowledge base[^\r\n]*\r?\n\.cg-docs/\r?\n?', '', content).rstrip('\n')
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
    print("  Removed stale .cg-docs/ entry from .gitignore")
PYEOF
fi

# ---------------------------------------------------------------------------
# Step 6: Verify managed directories are accessible via a known file
# ---------------------------------------------------------------------------
# Check a specific file through the prompts symlink, not just directory
# existence. A directory check passes even when the symlink target is on
# cloud storage with inaccessible contents (matches link.ps1 Step 6 behaviour).
VERIFY_CHECK="$TARGET_GITHUB_DIR/prompts/cg-setup.prompt.md"
if [[ ! -f "$VERIFY_CHECK" ]]; then
    print_warn "Verification failed - prompts not visible at expected path: $VERIFY_CHECK"
else
    print_gray "Symlinks verified."
fi

# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------
printf '\n'
print_green "Linked!"
printf '\n'
printf 'Compound GPID prompts are now available in this project.\n'
printf '  Next step: run /cg-setup in Copilot Chat to configure.\n'
printf '\n'
printf '\033[0;33mIMPORTANT:\033[0m\n'
printf '  The following directories are managed by Compound GPID.\n'
printf '  Do not edit files inside them - changes will be lost on cg-update.\n'
printf '  Managed: .github/prompts/  .github/skills/  .github/agents/  .github/instructions/\n'
printf '\n'
printf '\033[0;33mIMPORTANT: Restart VS Code / Positron now.\033[0m\n'
printf '  Copilot must re-index the workspace to see the linked prompts and agents.\n'
printf '  Without a restart, /cg-setup and other prompts will not be available.\n'
printf '\n'
printf 'Run in VS Code / Positron Copilot Chat:\n'
printf '  \033[0;36m/cg-setup\033[0m\n'
printf '\n'
printf 'Optional: set up cross-project knowledge sharing (team brain manager only):\n'
printf '  \033[0;90mcg-brain-init --repo <owner/name> --manager <github-username>\033[0m\n'
printf '\n'

exit 0
