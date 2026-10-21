#!/usr/bin/env bash
# scripts/link.sh
# Links the current project to Compound GPID using per-install-unit symlinks and
# managed copied files. Existing platform roots are preserved.

set -euo pipefail

FORCE=0
PLATFORMS=""
CHECK=0
HELP=0
usage() {
    printf '%s\n' 'Usage: cg-link [--check] [--platforms <copilot,claude-code,codex,opencode,kilo|all>] [--yes] [--help]'
    printf '%s\n' '--check reports the current project without update or writes. Exit: 0 nonblocking, 1 manual action or block, 2 usage.'
}
usage_error() { printf 'ERROR: %s\n' "$1" >&2; usage >&2; exit 2; }
while [ "$#" -gt 0 ]; do
    case "$1" in
        --yes|-y|--force|-Force) FORCE=1; shift ;;
        --check) CHECK=1; shift ;;
        --help|-h) HELP=1; shift ;;
        --platform=*|--platforms=*|-Platforms=*)
            PLATFORMS="${1#*=}"
            [ -n "$PLATFORMS" ] || usage_error 'Missing platform value'
            shift ;;
        --platform|--platforms|-Platforms)
            shift
            if [ "$#" -eq 0 ] || [[ "$1" == -* ]] || [ -z "$1" ]; then usage_error 'Missing value after --platforms'; fi
            PLATFORMS="$1"
            shift
            ;;
        *) usage_error "Unrecognized argument '$1'" ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(pwd)"
TARGET_MAPPING_PATH="$COMPOUND_GPID_DIR/.github/shared/target-mapping.json"
MANIFEST_PATH="$PROJECT_ROOT/.compound-gpid/managed-files.json"
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
    local -a probe_args=()
    [ "$CHECK" -eq 0 ] || probe_args=(-B)
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate ${probe_args[@]+"${probe_args[@]}"} --version 2>&1 || true)"
        case "$version" in
            Python\ [0-9]*) ;;
            *) continue ;;
        esac
        "$candidate" ${probe_args[@]+"${probe_args[@]}"} -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 || continue
        printf '%s\n' "$candidate"; return 0
    done
    return 1
}

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

replace_symlink_safely() {
    local link_path="$1" expected_target="$2" parent leaf temporary
    parent="$(dirname "$link_path")"
    leaf="$(basename "$link_path")"
    temporary="$parent/.$leaf.cg-link-$$-${RANDOM:-0}"
    rm -f "$temporary"
    if ! ln -s "$expected_target" "$temporary"; then
        return 1
    fi
    if ! same_realpath "$temporary" "$expected_target"; then
        rm -f "$temporary"
        return 1
    fi
    if ! "$PYTHON_CMD" - "$temporary" "$link_path" <<'PYEOF'
import os
import sys
os.replace(sys.argv[1], sys.argv[2])
PYEOF
    then
        rm -f "$temporary"
        return 1
    fi
    same_realpath "$link_path" "$expected_target"
}

normalize_platforms() {
    local input selected item platform exists unknown
    input="$1"
    selected=""
    [ -z "$input" ] && input="all"
    IFS=',' read -ra parts <<< "$input"
    for item in "${parts[@]}"; do
        platform="$(printf '%s' "$item" | tr '[:upper:]' '[:lower:]' | xargs)"
        [ -z "$platform" ] && continue
        if [ "$platform" = "all" ]; then
            for platform in copilot claude-code codex opencode kilo; do
                case ",$selected," in *",$platform,"*) ;; *) selected="${selected:+$selected,}$platform" ;; esac
            done
            continue
        fi
        case "$platform" in
            copilot|claude-code|codex|opencode|kilo)
                case ",$selected," in *",$platform,"*) ;; *) selected="${selected:+$selected,}$platform" ;; esac
                ;;
            *) usage_error "Unknown platform '$platform'" ;;
        esac
    done
    if [ -z "$selected" ]; then
        usage_error 'No valid platforms selected. Supported: copilot, claude-code, codex, opencode, kilo'
    fi
    printf '%s\n' "$selected"
}

platform_generated_tree() {
    # Returns the generatedTreePath (e.g. ".kilo") for a native platform, or an
    # empty string for copilot / unknown platforms.
    case "$1" in
        claude-code) printf '%s\n' ".claude" ;;
        codex)       printf '%s\n' ".agents" ;;
        opencode)    printf '%s\n' ".opencode" ;;
        kilo)        printf '%s\n' ".kilo" ;;
        *)           printf '%s\n' "" ;;
    esac
}

PLATFORMS="$(normalize_platforms "$PLATFORMS")"
[ "$HELP" -eq 0 ] || { usage; exit 0; }
PYTHON_CMD="$(resolve_python || true)"
if [ -z "$PYTHON_CMD" ]; then
    print_error 'Python 3.8+ is required (checked: python3, python, py).'
    exit 1
fi
if [ "$CHECK" -eq 1 ]; then
    check_args=(--root "$PROJECT_ROOT" --source-root "$COMPOUND_GPID_DIR" --platforms "$PLATFORMS")
    [ "$FORCE" -eq 0 ] || check_args+=(--force)
    exec "$PYTHON_CMD" -B "$SCRIPT_DIR/cg_link_check.py" "${check_args[@]}"
fi

add_units_for_platform() {
    case "$1" in
        copilot)
            printf '%s\n' \
                'copilot|directory|.github/prompts|.github/prompts|link-directory|' \
                'copilot|directory|.github/agents|.github/agents|link-directory|' \
                'copilot|directory|.github/instructions|.github/instructions|link-directory|' \
                'copilot|directory|.github/shared|.github/shared|link-directory|' \
                'copilot|file|.github/copilot-instructions.template.md|.github/copilot-instructions.md|generated-copy|'
            ;;
        claude-code)
            printf '%s\n' \
                'claude-code|directory|.claude/commands|.claude/commands|link-directory|' \
                'claude-code|directory|.claude/skills|.claude/skills|link-directory|' \
                'claude-code|directory|.claude/agents|.claude/agents|link-directory|' \
                'claude-code|directory|.claude/instructions|.claude/instructions|link-directory|' \
                'claude-code|directory|.claude/shared|.claude/shared|link-directory|' \
                'claude-code|file|.claude/CLAUDE.md|.claude/CLAUDE.md|managed-copy|' \
            ;;
        codex)
            printf '%s\n' \
                'codex|directory|.agents/commands|.agents/commands|link-directory|' \
                'codex|directory|.agents/skills|.agents/skills|link-directory|' \
                'codex|directory|.agents/subagents|.agents/subagents|link-directory|' \
                'codex|directory|.agents/instructions|.agents/instructions|link-directory|' \
                'codex|directory|.agents/shared|.agents/shared|link-directory|' \
                'codex|file|.agents/AGENTS.md|.agents/AGENTS.md|managed-copy|' \
            ;;
        opencode)
            printf '%s\n' \
                'opencode|directory|.opencode/commands|.opencode/commands|link-directory|' \
                'opencode|directory|.opencode/skills|.opencode/skills|link-directory|' \
                'opencode|directory|.opencode/agents|.opencode/agents|link-directory|' \
                'opencode|directory|.opencode/instructions|.opencode/instructions|link-directory|' \
                'opencode|directory|.opencode/shared|.opencode/shared|link-directory|' \
                'opencode|file|.opencode/AGENTS.md|.opencode/AGENTS.md|managed-copy|' \
                'opencode|file|.opencode/opencode.json|.opencode/opencode.json|config-copy-or-snippet|Add instructions .opencode/AGENTS.md and skills.paths .opencode/skills to your existing opencode.json.' \
                ;;
        kilo)
            printf '%s\n' \
                'kilo|directory|.kilo/commands|.kilo/commands|copy-directory|' \
                'kilo|directory|.kilo/skills|.kilo/skills|copy-directory|' \
                'kilo|directory|.kilo/agents|.kilo/agents|copy-directory|' \
                'kilo|directory|.kilo/instructions|.kilo/instructions|copy-directory|' \
                'kilo|directory|.kilo/shared|.kilo/shared|copy-directory|' \
                'kilo|file|.kilo/AGENTS.md|.kilo/AGENTS.md|managed-copy|' \
                'kilo|file|.kilo/kilo.json|.kilo/kilo.json|config-copy-or-snippet|Add instructions .kilo/AGENTS.md and skills.paths .kilo/skills to your existing kilo.json.' \
                ;;
    esac
}

all_install_units() {
    local platform
    for platform in copilot claude-code codex opencode kilo; do
        add_units_for_platform "$platform"
    done
}

ensure_root_directory() {
    local root_name="$1" root_path existing_target
    root_path="$PROJECT_ROOT/$root_name"
    if [ -L "$root_path" ]; then
        existing_target="$(readlink "$root_path")"
        if same_realpath "$root_path" "$COMPOUND_GPID_DIR/$root_name"; then
            print_yellow "  $root_name/ - migrating legacy whole-root symlink"
            rm -f "$root_path"
            mkdir -p "$root_path"
            return 0
        fi
        print_warn "$root_name/ is a non-Compound symlink; manual action required; skipping units under it."
        return 1
    fi
    if [ -e "$root_path" ] && [ ! -d "$root_path" ]; then
        print_warn "$root_name exists as a file; skipping units under it."
        return 1
    fi
    if [ ! -d "$root_path" ]; then
        mkdir -p "$root_path"
        print_gray "$root_name/ - created"
    fi
    return 0
}

install_directory_unit() {
    local source_rel="$1" target_rel="$2" strategy="$3" source_path target_path existing_target parent compat_platform mirror_path
    source_path="$COMPOUND_GPID_DIR/$source_rel"
    target_path="$PROJECT_ROOT/$target_rel"
    if [ -L "$target_path" ]; then
        existing_target="$(readlink "$target_path")"
        compat_platform="$(compat_platform_for_target "$target_rel" || true)"
        mirror_path=""
        [ -n "$compat_platform" ] && mirror_path="$PROJECT_ROOT/$KILO_COMPAT_MIRROR_ROOT_REL/$compat_platform"
        if [ -n "$mirror_path" ] && same_realpath "$target_path" "$mirror_path"; then
            print_gray "$target_rel - already linked through Kilo compatibility mirror"
            return 0
        elif same_realpath "$target_path" "$source_path"; then
            if [ "$strategy" = "copy-directory" ]; then
                print_yellow "  $target_rel - migrating legacy symlink to copy-directory"
                rm -f "$target_path"
            else
                print_gray "$target_rel - already linked"
                return 0
            fi
        else
            print_warn "$target_rel is a symlink pointing to: $existing_target; manual action required; preserving it."
            return 1
        fi
    elif [ -d "$target_path" ]; then
        if [ "$strategy" = "copy-directory" ]; then
            print_gray "$target_rel - already a real directory (will update)"
        else
            print_warn "$target_rel is a real directory; skipping this unit."
            return 1
        fi
    elif [ -e "$target_path" ]; then
        print_warn "$target_rel exists as a file; skipping this unit."
        return 1
    fi
    parent="$(dirname "$target_path")"
    if [ "$strategy" = "copy-directory" ]; then
        copy_args+=(--directory "$source_rel" "$target_rel")
        print_gray "$target_rel - copy queued"
    else
        mkdir -p "$parent"
        ln -s "$source_path" "$target_path"
        print_gray "$target_rel - linked"
    fi
    return 0
}

valid_copy_receipt() {
    "$PYTHON_CMD" -B - "$SCRIPT_DIR" "$PROJECT_ROOT" "$1" "$2" "${3:-$2}" <<'PYEOF'
from pathlib import Path
import sys

sys.path.insert(0, sys.argv[1])
from cg_link_check_paths import link_component, mirror_receipt

root = Path(sys.argv[2])
try:
    safe_parent = not link_component(root, Path(sys.argv[5]).parent.as_posix())
    valid = safe_parent and mirror_receipt(root, sys.argv[4], sys.argv[3]) is not None
except (OSError, ValueError) as error:
    sys.stderr.write(f"WARNING: {sys.argv[4]} receipt unreadable: {error}\n")
    sys.exit(1)
if not valid:
    reason = "linked parent" if not safe_parent else "missing, invalid or unreadable receipt"
    sys.stderr.write(f"WARNING: {sys.argv[4]}: {reason}\n")
sys.exit(0 if valid else 1)
PYEOF
}

protect_kilo_compatibility_skill_links() {
    valid_copy_receipt '.kilo/skills' '.kilo/skills' || return 0
    local record platform source_rel target_rel source_path target_path mirror_rel mirror_path link_target
    for record in \
        'claude-code|.claude/skills|.claude/skills' \
        'codex|.agents/skills|.agents/skills' \
        'opencode|.opencode/skills|.opencode/skills'; do
        IFS='|' read -r platform source_rel target_rel <<< "$record"
        source_path="$COMPOUND_GPID_DIR/$source_rel"
        target_path="$PROJECT_ROOT/$target_rel"
        mirror_rel="$KILO_COMPAT_MIRROR_ROOT_REL/$platform"
        mirror_path="$PROJECT_ROOT/$mirror_rel"
        [ -L "$target_path" ] || continue
        link_target="$(readlink "$target_path")"
        if ! same_realpath "$target_path" "$source_path" && ! same_realpath "$target_path" "$mirror_path"; then
            continue
        fi

        if ! valid_copy_receipt "$source_rel" "$mirror_rel" "$target_rel"; then
            print_warn "$target_rel compatibility mirror has no valid receipt or crosses a symlink; manual action required; preserving the link."
            continue
        fi
        if same_realpath "$target_path" "$source_path"; then
            if ! replace_symlink_safely "$target_path" "$mirror_path"; then
                print_error "$target_rel compatibility link replacement failed"
                return 1
            fi
            print_gray "$target_rel - localized for Kilo compatibility discovery"
        else
            print_gray "$target_rel - Kilo compatibility mirror updated"
        fi
        printf '%s\n%s\n' "$target_rel" "$mirror_rel" >> "$entries_file"
    done
}

install_file_unit() {
    copy_args+=(--file "$1" "$2" "$3")
    if [ -n "${4:-}" ]; then
        copy_args+=(--manual-snippet "$2" "$4")
    fi
}

update_gitignore_block() {
    local entries_file="$1" gitignore_path="$PROJECT_ROOT/.gitignore" marker pattern
    marker="# Compound GPID managed items (junctions + copied file - do not commit)"
    "$PYTHON_CMD" - "$gitignore_path" "$entries_file" "$marker" <<'PYEOF'
import os
import re
import sys
import tempfile

path, entries_file, marker = sys.argv[1:]
with open(entries_file, "r", encoding="utf-8") as handle:
    entries = sorted({line.strip() for line in handle if line.strip()})
if not entries:
    sys.exit(0)
content = ""
if os.path.exists(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        content = handle.read()
if content and not content.endswith("\n"):
    content += "\n"
pattern = r"(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.claude/|\.agents/|\.opencode/|\.kilo/|\.compound-gpid/)[^\r\n]*\r?\n)*"
cleaned = re.sub(pattern, "", content).rstrip("\n")
cleaned = re.sub(r"(?m)^# Compound GPID knowledge base[^\r\n]*\r?\n\.cg-docs/\r?\n?", "", cleaned)
cleaned = re.sub(r"(?m)^\.cg-docs/\r?\n?", "", cleaned).rstrip("\n")
block = marker + "\n" + "\n".join(entries) + "\n"
out = cleaned + ("\n\n" if cleaned else "") + block
directory = os.path.dirname(path) or "."
fd, tmp = tempfile.mkstemp(dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(out)
    os.replace(tmp, path)
finally:
    if os.path.exists(tmp):
        os.unlink(tmp)
PYEOF
    print_gray "Updated CG entries in .gitignore"
}

collect_existing_managed_entries() {
    local platform unit_type source_rel target_rel strategy snippet target_path existing_target compat_platform mirror_path
    all_install_units | while IFS='|' read -r platform unit_type source_rel target_rel strategy snippet; do
        [ -z "$platform" ] && continue
        target_path="$PROJECT_ROOT/$target_rel"
        if [ "$unit_type" = "directory" ]; then
            if [ -L "$target_path" ]; then
                existing_target="$(readlink "$target_path")"
                compat_platform="$(compat_platform_for_target "$target_rel" || true)"
                mirror_path=""
                [ -n "$compat_platform" ] && mirror_path="$PROJECT_ROOT/$KILO_COMPAT_MIRROR_ROOT_REL/$compat_platform"
                if same_realpath "$target_path" "$COMPOUND_GPID_DIR/$source_rel" ||
                   { [ -n "$mirror_path" ] && same_realpath "$target_path" "$mirror_path"; }; then
                    printf '%s\n' "$target_rel"
                fi
            elif [ -f "$target_path/.compound-gpid-managed-copy.json" ] &&
                 grep -qF "\"source\": \"$source_rel\"" "$target_path/.compound-gpid-managed-copy.json"; then
                printf '%s\n' "$target_rel"
            fi
        elif [ "$target_rel" = ".github/copilot-instructions.md" ]; then
            if [ -f "$target_path" ] && grep -qF "$COPILOT_INSTRUCTIONS_MARKER" "$target_path" 2>/dev/null; then
                printf '%s\n' "$target_rel"
            fi
        fi
    done

    if [ -f "$MANIFEST_PATH" ]; then
        "$PYTHON_CMD" - "$MANIFEST_PATH" "$PROJECT_ROOT" <<'PYEOF'
import json
import os
import sys

manifest_path, project_root = sys.argv[1:]
try:
    with open(manifest_path, "r", encoding="utf-8-sig") as handle:
        manifest = json.load(handle)
    files = manifest.get("files", {}) if isinstance(manifest, dict) else {}
    if not isinstance(files, dict):
        files = {}
except (OSError, ValueError) as error:
    sys.stderr.write(f"WARNING: managed-files.json ignored (no receipt): {error}\n")
    files = {}
for target_rel in sorted(files):
    if os.path.exists(os.path.join(project_root, target_rel)):
        print(target_rel)
if files:
    print(".compound-gpid/managed-files.json")
PYEOF
    fi
}

cleanup_legacy_model_mapping_files() {
    if [ ! -f "$MANIFEST_PATH" ]; then return 0; fi
    "$PYTHON_CMD" - "$MANIFEST_PATH" "$PROJECT_ROOT" <<'PYEOF'
import hashlib
import json
import os
import sys

manifest_path, project_root = sys.argv[1:]
legacy_targets = (
    ".claude/model-mapping.claude.json",
    ".agents/model-mapping.codex.json",
    ".opencode/model-mapping.opencode.json",
    ".kilo/model-mapping.kilo.json",
)

try:
    with open(manifest_path, "r", encoding="utf-8-sig") as handle:
        manifest = json.load(handle)
    if (not isinstance(manifest, dict) or
            manifest.get("schemaVersion") != "compound-gpid-managed-files-v1" or
            not isinstance(manifest.get("files"), dict)):
        raise ValueError("invalid receipt schema")
except (OSError, ValueError) as error:
    sys.stderr.write(f"WARNING: managed-files.json ignored (no receipt): {error}\n")
    sys.exit(0)
files = manifest["files"]
changed = False

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

for target_rel in legacy_targets:
    record = files.get(target_rel)
    if not record:
        continue
    target_path = os.path.join(project_root, target_rel)
    if os.path.isfile(target_path) and not os.path.islink(target_path):
        if sha256(target_path) == record.get("checksum"):
            os.unlink(target_path)
            print(f"REMOVED\t{target_rel}")
        else:
            print(f"PRESERVED\t{target_rel}\tuser-modified")
    files.pop(target_rel, None)
    changed = True

if changed:
    if files:
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
    else:
        os.unlink(manifest_path)
PYEOF
}

run_kilo_preflight() {
    local output status
    local -a preflight_args=("$COMPOUND_GPID_DIR/scripts/cg_kilo_preflight.py" --root "$PROJECT_ROOT" --json --local-only)
    set +e
    output="$($PYTHON_CMD "${preflight_args[@]}")"
    status=$?
    set -e
    if [ "$status" -ne 0 ]; then
        print_error "Linking is blocked by local generated Kilo file validation."
        printf '%s\n' "$output" >&2
        exit "$status"
    fi
    local result_status
    result_status="$(printf '%s\n' "$output" | "$PYTHON_CMD" -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
    print_gray "Kilo preflight (local): $result_status"
}

if [ ! -d "$COMPOUND_GPID_DIR" ]; then print_error "Compound GPID installation directory not found at: $COMPOUND_GPID_DIR"; exit 1; fi
if [ ! -f "$TARGET_MAPPING_PATH" ]; then print_error "Target mapping not found at: $TARGET_MAPPING_PATH"; exit 1; fi

update_kilo_global_permission() {
    local action="$1"
    local kilo_config_dir="$HOME/.config/kilo"
    local kilo_config_path="$kilo_config_dir/kilo.jsonc"
    local commands_source="${COMPOUND_GPID_DIR//\\//}/.kilo/commands"
    local permission_key="${commands_source}/*"

    mkdir -p "$kilo_config_dir"

    "$PYTHON_CMD" - "$kilo_config_path" "$permission_key" "$action" <<'PYEOF'
import json
import os
import sys

config_path, permission_key, action = sys.argv[1], sys.argv[2], sys.argv[3]

config = {}
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as handle:
        raw = handle.read()
    if raw.strip():
        try:
            config = json.loads(raw)
        except json.JSONDecodeError:
            print("ABORTED")
            print("WARNING: Could not parse kilo.jsonc; leaving it unchanged.", file=sys.stderr)
            sys.exit(0)
        if not isinstance(config, dict):
            print("ABORTED")
            print("WARNING: kilo.jsonc root is not a JSON object; leaving it unchanged.", file=sys.stderr)
            sys.exit(0)

config.setdefault("permission", {})
if not isinstance(config["permission"], dict):
    config["permission"] = {}
config["permission"].setdefault("markdown_source", {})
if not isinstance(config["permission"]["markdown_source"], dict):
    config["permission"]["markdown_source"] = {}

if action == "remove":
    if permission_key in config["permission"]["markdown_source"]:
        del config["permission"]["markdown_source"][permission_key]
        if not config["permission"]["markdown_source"]:
            del config["permission"]["markdown_source"]
        if not config["permission"]:
            del config["permission"]
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")
        print("REMOVED")
    else:
        print("NOT_FOUND")
elif action == "add":
    if config["permission"]["markdown_source"].get(permission_key) == "allow":
        print("ALREADY_PRESENT")
    else:
        config["permission"]["markdown_source"][permission_key] = "allow"
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")
        print("ADDED")
PYEOF
}

printf '\n'
if [ "${CG_SKIP_UPDATE:-}" = "1" ]; then
    print_gray "Skipping Compound GPID update (CG_SKIP_UPDATE=1)."
else
    print_cyan "Updating Compound GPID..."
    if ! CG_INTERNAL_CALL=1 "$COMPOUND_GPID_DIR/scripts/update.sh"; then
        print_error "Could not update and validate Compound GPID; linking is blocked. Existing installed content was left unchanged."
        exit 1
    fi
fi

VERSION_FILE="$COMPOUND_GPID_DIR/.cg-version"
ACTIVE_VERSION="latest"
[ -f "$VERSION_FILE" ] && ACTIVE_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
[ -z "$ACTIVE_VERSION" ] && ACTIVE_VERSION="latest"

printf '\n'
print_cyan "Compound GPID - Link"
print_cyan "===================="
print_gray "Version: $([ "$ACTIVE_VERSION" = latest ] && printf 'tracking main (latest)' || printf '%s (pinned)' "$ACTIVE_VERSION")"
print_gray "Platforms: $PLATFORMS"
printf '\n'

units_file="$(mktemp "${TMPDIR:-/tmp}/cg-link-units-XXXXXX")"
entries_file="$(mktemp "${TMPDIR:-/tmp}/cg-link-entries-XXXXXX")"
trap 'rm -f "$units_file" "$entries_file"' EXIT
IFS=',' read -ra selected_parts <<< "$PLATFORMS"
for platform in "${selected_parts[@]}"; do add_units_for_platform "$platform" >> "$units_file"; done

missing=""
while IFS='|' read -r platform unit_type source_rel target_rel strategy snippet; do
    [ -z "$platform" ] && continue
    if [ ! -e "$COMPOUND_GPID_DIR/$source_rel" ]; then missing="${missing}${platform}: ${source_rel}\n"; fi
done < "$units_file"
if [ -n "$missing" ]; then
    print_error "Selected Compound GPID source units are missing:"
    printf '%b' "$missing" >&2
    exit 1
fi

MANIFEST_DRIVEN="false"
[ -f "$PROJECT_ROOT/compound-gpid.local.md" ] && MANIFEST_DRIVEN="true"
# target-mapping projectedCategories delegates Copilot skills to the Python
# projection worker. Every non-skill Copilot install unit keeps its old topology.
COPILOT_PROJECTED_CATEGORIES="skills"

# Resolve strict manifest inputs before any consumer cleanup or installation.
# Registry/catalog data comes from the Compound GPID source; project selection
# and managed output remain rooted in the consumer project.
if [ "$MANIFEST_DRIVEN" = "true" ]; then
    set +e
    MANIFEST_OUTPUT="$("$PYTHON_CMD" "$COMPOUND_GPID_DIR/scripts/cg_project_manifest.py" --root "$PROJECT_ROOT" --source-root "$COMPOUND_GPID_DIR" --platforms "$PLATFORMS" --ensure-state 2>&1)"
    MANIFEST_STATUS=$?
    set -e
    if [ "$MANIFEST_STATUS" -ne 0 ]; then
        print_error "Linking is blocked by active manifest resolution failure."
        printf '%s\n' "$MANIFEST_OUTPUT" >&2
        exit 1
    fi
    while IFS= read -r line; do
        case "$line" in
            'compound-gpid.local.md has no settings block;'*) printf '%s\n' "$line" ;;
        esac
    done <<< "$MANIFEST_OUTPUT"
    print_gray "Active manifest: resolved for $PLATFORMS"
fi

# Retire proven plugin residue after selection validation, before ownership refresh.
if ! "$PYTHON_CMD" "$COMPOUND_GPID_DIR/scripts/cg_retire_native_evidence.py" --root "$PROJECT_ROOT"; then
    print_error "Linking is blocked by preserved native-evidence residue; review the diagnostics above."
    exit 1
fi

cleanup_legacy_model_mapping_files

copy_args=()
while IFS='|' read -r platform unit_type source_rel target_rel strategy snippet; do
    [ -z "$platform" ] && continue
    root_name="${target_rel%%/*}"
    if ! ensure_root_directory "$root_name"; then
        copy_args+=(--manual-path "$root_name")
        continue
    fi
    # Manifest-driven consumers materialize native generated-tree roots as real
    # project-local directories through the projection synchronizer. Their
    # legacy link-directory/copy-directory install units are skipped so the
    # no-follow synchronizer never sees a junction/copy destination.
    GENERATED_PROJECTED="false"
    if [ -n "$(platform_generated_tree "$platform")" ]; then GENERATED_PROJECTED="true"; fi
    if [ "$MANIFEST_DRIVEN" = "true" ] && [ "$GENERATED_PROJECTED" = "true" ] && [ "$unit_type" = "directory" ]; then
        print_gray "$target_rel - projected by manifest (legacy install skipped)"
        continue
    fi
    if [ "$MANIFEST_DRIVEN" = "true" ] && [ "$target_rel" = ".github/skills" ] &&
       [ "$COPILOT_PROJECTED_CATEGORIES" = "skills" ]; then
        print_gray "$target_rel - Copilot skills projected by manifest"
        continue
    fi
    if [ "$unit_type" = "directory" ]; then
        if install_directory_unit "$source_rel" "$target_rel" "$strategy"; then
            printf '%s\n' "$target_rel" >> "$entries_file"
        else
            copy_args+=(--manual-path "$target_rel")
        fi
    else
        install_file_unit "$source_rel" "$target_rel" "$strategy" "$snippet"
    fi
done < "$units_file"

# Run even with no queued units: existing compatibility links can need mirrors.
if COPY_OUTPUT="$("$PYTHON_CMD" -B "$SCRIPT_DIR/cg_kilo_copy.py" --source-root "$COMPOUND_GPID_DIR" --project-root "$PROJECT_ROOT" --sync-projection ${copy_args[@]+"${copy_args[@]}"} 2>&1)"; then
    printf '%s\n' "$COPY_OUTPUT"
else
    printf '%s\n' "$COPY_OUTPUT" >&2
    print_error 'Shared copy or manifest projection synchronization failed; review the diagnostics above.'
    exit 1
fi

# The batch publishes manifest-driven roots before local Kilo preflight.
# Keep their runtime output in the managed ignore block without syncing again.
if [ -d "$PROJECT_ROOT/.compound-gpid" ] && [ -f "$PROJECT_ROOT/.compound-gpid/active-manifest.json" ]; then
    print_gray "Project projection: synced and verified"

    # Generated projection roots are reproducible runtime output. Keep them in
    # the managed gitignore block while leaving active-manifest.json reviewable.
    for platform in "${selected_parts[@]}"; do
        projection_root="$(platform_generated_tree "$platform")"
        [ -n "$projection_root" ] && printf '%s\n' "$projection_root" >> "$entries_file"
    done
    printf '%s\n' \
        '.compound-gpid/active/' \
        '.compound-gpid/generations/' \
        '.compound-gpid/projection-ownership.json' \
        '.compound-gpid/projection-transaction.json' \
        '.compound-gpid/staging/' \
        '.compound-gpid/quarantine/' \
        '.compound-gpid/retired/' \
        '.compound-gpid/*.tmp' \
        '.compound-gpid/*.bak' >> "$entries_file"
fi

protect_kilo_compatibility_skill_links

if [[ ",$PLATFORMS," == *,kilo,* ||
      -f "$PROJECT_ROOT/.kilo/skills/.compound-gpid-managed-copy.json" ]]; then
    if printf '%s\n' "$COPY_OUTPUT" | grep -Eq '^Kilo validation deferred: [1-9][0-9]*$'; then
        print_warn 'Kilo validation deferred: kept Kilo files need manual action; use cg-link --check after resolving them.'
    else
        run_kilo_preflight
    fi
fi
if [[ -d "$PROJECT_ROOT/.kilo/skills" &&
      ( -d "$PROJECT_ROOT/.agents/skills" || -d "$PROJECT_ROOT/.claude/skills" ) ]]; then
    print_yellow "Note: Kilo and compatibility skills coexist. Use cg-kilo for an optional contained launch."
fi

collect_existing_managed_entries >> "$entries_file"
update_gitignore_block "$entries_file"

case ",$PLATFORMS," in
    *,kilo,*)
        result="$(update_kilo_global_permission "add")"
        case "$result" in
            ADDED)           print_gray "Updated kilo.jsonc markdown_source permission" ;;
            ALREADY_PRESENT) print_gray "kilo.jsonc markdown_source permission already present" ;;
            ABORTED)         print_warn "kilo.jsonc could not be parsed or is not a JSON object; left unchanged." ;;
        esac
        ;;
esac

printf '\n'
print_gray "Platform availability checks:"
IFS=',' read -ra check_platforms <<< "$PLATFORMS"
for platform in "${check_platforms[@]}"; do
    case "$platform" in
        copilot) check_rel=".github/prompts/cg-setup.prompt.md" ;;
        claude-code) check_rel=".claude/commands/cg-plan.md" ;;
        codex) check_rel=".agents/commands/cg-plan.md" ;;
        opencode) check_rel=".opencode/commands/cg-plan.md" ;;
        kilo) check_rel=".kilo/commands/cg-plan.md" ;;
        *) check_rel="" ;;
    esac
    if [ -n "$check_rel" ] && [ -e "$PROJECT_ROOT/$check_rel" ]; then
        print_gray "$platform - available"
    else
        print_warn "$platform - not fully available; review skipped units above."
    fi
done

printf '\n'
print_green "Linked!"
printf '\nCompound GPID assets are now available for: %s.\n' "$PLATFORMS"
printf 'Use --platforms copilot for Copilot-only or --platforms kilo for Kilo-only assets.\n\n'
print_yellow "IMPORTANT: Restart your AI coding tool so commands, skills, agents, and config reload."
printf '\n'
