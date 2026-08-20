#!/usr/bin/env bash
# scripts/link.sh
# Links the current project to Compound GPID using per-install-unit symlinks and
# managed copied files. Existing platform roots are preserved.

set -euo pipefail

FORCE=0
PLATFORMS=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --yes|-y|--force|-Force) FORCE=1; shift ;;
        --platforms=*) PLATFORMS="${1#--platforms=}"; shift ;;
        -Platforms=*) PLATFORMS="${1#-Platforms=}"; shift ;;
        --platforms|-Platforms)
            shift
            if [ "$#" -eq 0 ]; then printf 'ERROR: Missing value after --platforms\n' >&2; exit 1; fi
            PLATFORMS="$1"
            shift
            ;;
        *) printf 'WARNING: Unrecognized argument %s -- ignoring\n' "$1" >&2; shift ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(pwd)"
TARGET_MAPPING_PATH="$COMPOUND_GPID_DIR/.github/shared/target-mapping.json"
MANIFEST_PATH="$PROJECT_ROOT/.compound-gpid/managed-files.json"
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
if [ -z "$PYTHON_CMD" ]; then
    print_error "Python is required but not found (checked: python3, python, py)."
    printf 'Install Xcode Command Line Tools or Python from https://www.python.org/downloads/\n' >&2
    exit 1
fi

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
                case ",$selected," in *",$platform,"*) ;; *) selected="${selected:+$selected},$platform" ;; esac
                ;;
            *) print_warn "Unknown platform '$platform' -- skipping" ;;
        esac
    done
    if [ -z "$selected" ]; then
        print_error "No valid platforms selected. Supported platforms: copilot, claude-code, codex, opencode, kilo"
        exit 1
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

generate_copilot_instructions() {
    local template_path="$1" project_root="$2" marker="$3"
    "$PYTHON_CMD" - "$template_path" "$project_root" "$marker" <<'PYEOF'
import os
import re
import sys

template_path, project_root, marker = sys.argv[1], sys.argv[2], sys.argv[3]

def extract_fm_value(path, key):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        match = re.match(r"^---[ \t]*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return ""
        value_match = re.search(r"(?m)^\s*" + re.escape(key) + r":\s*[\"']?([^\"'\r\n]+)[\"']?\s*$", match.group(1))
        return value_match.group(1).strip() if value_match else ""
    except OSError:
        return ""

project_name = extract_fm_value(os.path.join(project_root, "compound-gpid.md"), "project-name") or "<project-name>"
local_path = os.path.join(project_root, "compound-gpid.local.md")
language = extract_fm_value(local_path, "language") or "<not configured>"
project_type = extract_fm_value(local_path, "project-type") or "<not configured>"
review_depth = extract_fm_value(local_path, "review-depth") or "<not configured>"
r_syntax = extract_fm_value(local_path, "r-syntax")
languages = f"{language} (R dialect: {r_syntax})" if r_syntax and re.search(r"\bR\b", language, re.I) else language
for value in (project_name, project_type, languages, review_depth):
    if "{{" in value:
        print("ERROR: Config value contains a placeholder token.", file=sys.stderr)
        sys.exit(1)
with open(template_path, "r", encoding="utf-8") as handle:
    template = handle.read()
if not template.strip():
    print(f"ERROR: Template file is empty: {template_path}", file=sys.stderr)
    sys.exit(1)
output = template.replace("{{project-name}}", project_name).replace("{{project-type}}", project_type).replace("{{languages}}", languages).replace("{{review-depth}}", review_depth)
sep = "\r\n" if "\r\n" in output else "\n"
sys.stdout.write(marker + sep + output)
PYEOF
}

add_units_for_platform() {
    case "$1" in
        copilot)
            printf '%s\n' \
                'copilot|directory|.github/prompts|.github/prompts|link-directory|' \
                'copilot|directory|.github/skills|.github/skills|link-directory|' \
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
        if [[ "$existing_target" == *compound-gpid* ]]; then
            print_yellow "  $root_name/ - migrating legacy whole-root symlink"
            rm -f "$root_path"
            mkdir -p "$root_path"
            return 0
        fi
        print_warn "$root_name/ is a non-Compound symlink; skipping units under it."
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
    local source_rel="$1" target_rel="$2" strategy="$3" source_path target_path existing_target parent
    source_path="$COMPOUND_GPID_DIR/$source_rel"
    target_path="$PROJECT_ROOT/$target_rel"
    if [ -L "$target_path" ]; then
        existing_target="$(readlink "$target_path")"
        if [[ "$existing_target" == *compound-gpid* ]]; then
            if [ "$strategy" = "copy-directory" ]; then
                print_yellow "  $target_rel - migrating legacy symlink to copy-directory"
                rm -f "$target_path"
            else
                print_gray "$target_rel - already linked"
                return 0
            fi
        else
            print_warn "$target_rel is a symlink pointing to: $existing_target"
            if [ "$FORCE" -eq 0 ]; then
                printf '  Relink %s to Compound GPID instead? [y/N] ' "$target_rel"
                read -r answer </dev/tty
                case "$answer" in [Yy]*) ;; *) print_yellow "  $target_rel - skipped"; return 1 ;; esac
            fi
            rm -f "$target_path"
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
    mkdir -p "$parent"
    if [ "$strategy" = "copy-directory" ]; then
        "$PYTHON_CMD" "$COMPOUND_GPID_DIR/scripts/cg_kilo_copy.py" \
            --source "$source_path" --target "$target_path" --source-relative "$source_rel"
        print_gray "$target_rel - copied"
    else
        ln -s "$source_path" "$target_path"
        print_gray "$target_rel - linked"
    fi
    return 0
}

install_file_unit() {
    local source_rel="$1" target_rel="$2" strategy="$3" snippet="$4" source_path target_path parent generated existing
    source_path="$COMPOUND_GPID_DIR/$source_rel"
    target_path="$PROJECT_ROOT/$target_rel"
    if [ "$strategy" = "generated-copy" ]; then
        existing=""
        [ -f "$target_path" ] && existing="$(< "$target_path")"
        if [ -n "$existing" ] && ! grep -qF "$COPILOT_INSTRUCTIONS_MARKER" "$target_path" 2>/dev/null; then
            print_yellow "  $target_rel - user-managed (marker absent), skipping"
            return 1
        fi
        generated="$(generate_copilot_instructions "$source_path" "$PROJECT_ROOT" "$COPILOT_INSTRUCTIONS_MARKER")"
        parent="$(dirname "$target_path")"
        mkdir -p "$parent"
        if [ "$generated" != "$existing" ]; then printf '%s' "$generated" > "$target_path.tmp" && mv "$target_path.tmp" "$target_path"; fi
        print_gray "$target_rel - generated"
        return 0
    fi

    "$PYTHON_CMD" - "$MANIFEST_PATH" "$source_rel" "$target_rel" "$source_path" "$target_path" "$snippet" <<'PYEOF'
import hashlib
import json
import os
import shutil
import sys

manifest_path, source_rel, target_rel, source_path, target_path, snippet = sys.argv[1:]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

manifest = {"schemaVersion": "compound-gpid-managed-files-v1", "files": {}}
if os.path.exists(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as handle:
        try:
            manifest.update(json.load(handle))
        except json.JSONDecodeError:
            pass
manifest.setdefault("files", {})
record = manifest["files"].get(target_rel)
can_write = not os.path.exists(target_path)
if not can_write and record and sha256(target_path) == record.get("checksum"):
    can_write = True
if not can_write:
    print(f"SKIP\t{snippet}")
    sys.exit(0)
os.makedirs(os.path.dirname(target_path), exist_ok=True)
shutil.copy2(source_path, target_path)
manifest["files"][target_rel] = {"source": source_rel, "checksum": sha256(target_path)}
os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2)
    handle.write("\n")
print("COPIED")
PYEOF
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
    local platform unit_type source_rel target_rel strategy snippet target_path existing_target
    all_install_units | while IFS='|' read -r platform unit_type source_rel target_rel strategy snippet; do
        [ -z "$platform" ] && continue
        target_path="$PROJECT_ROOT/$target_rel"
        if [ "$unit_type" = "directory" ]; then
            if [ -L "$target_path" ]; then
                existing_target="$(readlink "$target_path")"
                [[ "$existing_target" == *compound-gpid* ]] && printf '%s\n' "$target_rel"
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
with open(manifest_path, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
files = manifest.get("files", {})
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

with open(manifest_path, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
files = manifest.setdefault("files", {})
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
    local mode="$1"
    local output status
    local -a preflight_args=("$COMPOUND_GPID_DIR/scripts/cg_kilo_preflight.py" --root "$PROJECT_ROOT" --json)
    if [ "$mode" = "host" ]; then
        preflight_args+=(--require-coexistence --host-only)
    elif [ "$mode" = "coexistence" ]; then
        preflight_args+=(--require-coexistence)
    else
        preflight_args+=(--local-only)
    fi
    set +e
    output="$($PYTHON_CMD "${preflight_args[@]}")"
    status=$?
    set -e
    if [ "$status" -ne 0 ]; then
        print_error "Linking is blocked by Kilo coexistence preflight."
        printf '%s\n' "$output" >&2
        exit "$status"
    fi
    local result_status
    result_status="$(printf '%s\n' "$output" | "$PYTHON_CMD" -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
    print_gray "Kilo preflight ($mode): $result_status"
    if [ "$mode" = "coexistence" ]; then
        print_yellow "Certified launch required: cg-kilo (direct Kilo launches unsupported with compatibility roots)."
    fi
}

if [[ ",$PLATFORMS," == *,kilo,* ]] &&
   [[ ",$PLATFORMS," == *,codex,* || ",$PLATFORMS," == *,claude-code,* ||
      -d "$PROJECT_ROOT/.agents/skills" || -d "$PROJECT_ROOT/.claude/skills" ]]; then
    run_kilo_preflight host
fi

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

cleanup_legacy_model_mapping_files

MANIFEST_DRIVEN="false"
[ -f "$PROJECT_ROOT/compound-gpid.local.md" ] && MANIFEST_DRIVEN="true"

while IFS='|' read -r platform unit_type source_rel target_rel strategy snippet; do
    [ -z "$platform" ] && continue
    root_name="${target_rel%%/*}"
    ensure_root_directory "$root_name" || continue
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
    if [ "$unit_type" = "directory" ]; then
        if install_directory_unit "$source_rel" "$target_rel" "$strategy"; then printf '%s\n' "$target_rel" >> "$entries_file"; fi
    else
        output="$(install_file_unit "$source_rel" "$target_rel" "$strategy" "$snippet")"
        case "$output" in
            COPIED*) print_gray "$target_rel - copied"; printf '%s\n' "$target_rel" >> "$entries_file"; [ -f "$MANIFEST_PATH" ] && printf '%s\n' ".compound-gpid/managed-files.json" >> "$entries_file" ;;
            SKIP*) print_warn "$target_rel exists and is not manifest-managed; skipping."; [ -n "${output#SKIP$'\t'}" ] && print_yellow "  Manual config snippet: ${output#SKIP$'\t'}" ;;
            *) [ -n "$output" ] && printf '%s\n' "$output" ;;
        esac
    fi
done < "$units_file"

if [[ ",$PLATFORMS," == *,kilo,* ]] &&
   [[ ",$PLATFORMS," == *,codex,* || ",$PLATFORMS," == *,claude-code,* ]]; then
    run_kilo_preflight coexistence
elif [[ -d "$PROJECT_ROOT/.kilo/skills" &&
        ( -d "$PROJECT_ROOT/.agents/skills" || -d "$PROJECT_ROOT/.claude/skills" ) ]]; then
    run_kilo_preflight coexistence
elif [[ ",$PLATFORMS," == *,kilo,* ]]; then
    run_kilo_preflight local
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
# Persist the selected platform set in the committed active manifest so no
# separate resolution command is needed during later cg-update runs. A
# manifest-driven consumer with invalid strict config fails closed: linking
# must not silently fall through to the legacy unfiltered tree.
if [ -f "$PROJECT_ROOT/compound-gpid.local.md" ]; then
    set +e
    MANIFEST_OUTPUT="$("$PYTHON_CMD" "$COMPOUND_GPID_DIR/scripts/cg_project_manifest.py" --root "$PROJECT_ROOT" --platforms "$PLATFORMS" --ensure-state 2>&1)"
    MANIFEST_STATUS=$?
    set -e
    if [ "$MANIFEST_STATUS" -ne 0 ]; then
        print_error "Linking is blocked by active manifest resolution failure."
        printf '%s\n' "$MANIFEST_OUTPUT" >&2
        exit 1
    fi
    print_gray "Active manifest: resolved for $PLATFORMS"
fi

# For a manifest-driven consumer project, verify the committed active manifest
# and recover/publish the project-local projection through the journaled
# synchronizer. Fresh junction/copy links without a .compound-gpid state stay
# on the legacy path; a projection error blocks the link success banner.
if [ -d "$PROJECT_ROOT/.compound-gpid" ] && [ -f "$PROJECT_ROOT/.compound-gpid/active-manifest.json" ]; then
    set +e
    PROJECTION_OUTPUT="$("$PYTHON_CMD" "$COMPOUND_GPID_DIR/scripts/cg_project_projection.py" --project-root "$PROJECT_ROOT" --source-root "$COMPOUND_GPID_DIR" --sync 2>&1)"
    PROJECTION_STATUS=$?
    set -e
    if [ "$PROJECTION_STATUS" -ne 0 ]; then
        print_error "Linking is blocked by manifest projection failure."
        printf '%s\n' "$PROJECTION_OUTPUT" >&2
        exit 1
    fi
    print_gray "Project projection: synced and verified"
fi

print_green "Linked!"
printf '\nCompound GPID assets are now available for: %s.\n' "$PLATFORMS"
printf 'Use --platforms copilot for Copilot-only or --platforms kilo for Kilo-only assets.\n\n'
print_yellow "IMPORTANT: Restart your AI coding tool so commands, skills, agents, and config reload."
printf '\n'
