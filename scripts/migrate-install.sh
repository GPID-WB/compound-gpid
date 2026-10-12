#!/bin/bash
# Replace an installation from a separate clean clone at an exact numeric tag.
# bash /new-clone/scripts/migrate-install.sh [--install-path /old-install]
# bash /new-clone/scripts/migrate-install.sh --install-path /old-install --rollback /old-install.backup-VERSION-TIMESTAMP
set -euo pipefail
official='https://github.com/GPID-WB/compound-gpid.git'
install_path= rollback= target= backup= created=0 moved=0
fail() { printf '%s\n' "$*" >&2; exit 1; }

# Resolve the parent physically, but never follow the selected directory itself.
normal_path() {
    local path=$1 parent
    while [[ "$path" != / && "$path" == */ ]]; do path=${path%/}; done
    [[ ! -L "$path" ]] || fail "Symlink targets are not supported: $path"
    parent=$(cd -- "$(dirname -- "$path")" && pwd -P) || fail "Target parent is missing: $path"
    printf '%s/%s\n' "${parent%/}" "$(basename -- "$path")"
}
assert_clone() {
    local path=$1
    [[ ! -L "$path" && ! -L "$path/.git" && -d "$path/.git" ]] ||
        fail "Not a standalone Git clone root (.git files/worktrees refused): $path"
    [[ "$(git -C "$path" rev-parse --show-toplevel)" == "$path" ]] || fail "Not a Git clone root: $path"
    [[ ! -e "$path/.git/worktrees" ]] || fail "Clone has registered worktrees; manual action required: $path"
    [[ -f "$path/scripts/install.sh" && -f "$path/bin/cg-update" ]] || fail "Compound GPID installer/wrapper is missing: $path"
}
assert_separate() {
    [[ "$1" != "$source" && "$1" != "$source/"* && "$source" != "$1/"* ]] || fail "NEW clone and target overlap: $1"
}
get_backups() {
    local item
    backups=()
    for item in "$1".backup-*; do
        if [[ -d "$item" || -L "$item" ]]; then backups+=("$item"); fi
    done
}
rollback_command() {
    printf '  bash %q --install-path %q --rollback %q\n' "$script" "$target" "$1"
}
restore_on_exit() {
    local code=$?
    trap - EXIT
    [[ "$moved" == 1 ]] || return "$code"
    set +e
    if [[ "$created" == 1 && -d "$target" && ! -L "$target" ]]; then rm -rf -- "$target"; fi
    if [[ ! -e "$target" && ! -L "$target" ]] && mv -- "$backup" "$target"; then
        printf "Migration failed. Old folder restored to '%s'. Review installer PATH/profile writes manually.\n" "$target" >&2
    else
        printf "Automatic restore failed. Keep backup '%s'; inspect both folders before rollback.\n" "$backup" >&2
        rollback_command "$backup" >&2
    fi
    exit "$code"
}
trap restore_on_exit EXIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-path|--rollback)
            [[ $# -ge 2 && -n "$2" ]] || fail "Missing path for $1"
            if [[ "$1" == --install-path ]]; then install_path=$2; else rollback=$2; fi
            shift 2 ;;
        *) fail "Unknown option: $1" ;;
    esac
done
command -v git >/dev/null 2>&1 || fail 'Install Git first.'
[[ -z "$rollback" || -n "$install_path" ]] || fail '--rollback requires --install-path with the exact original target.'
source=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
script="$source/scripts/migrate-install.sh"
assert_clone "$source"
new_head=$(git -C "$source" rev-parse HEAD)
new_tag=$(git -C "$source" describe --tags --exact-match HEAD) || fail 'Run from a clean fresh clone at an exact release tag.'
source_status=$(git -C "$source" status --porcelain --untracked-files=all)
[[ "$new_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$ &&
    -z "$source_status" ]] || fail 'Run from a clean fresh clone at an exact release tag.'
stamp=$(date '+%Y%m%d-%H%M%S')

if [[ -n "$rollback" ]]; then
    target=$(normal_path "$install_path")
    backup=$(normal_path "$rollback")
    suffix=${backup#"$target.backup-"}
    [[ "$backup" == "$target.backup-"* && "$suffix" =~ ^[A-Za-z0-9._-]+-[0-9]{8}-[0-9]{6}$ ]] ||
        fail 'Use the exact target and sibling .backup- path printed by migration.'
    assert_separate "$target"
    assert_separate "$backup"
    assert_clone "$backup"
    aside="$target.rollback-$stamp"
    [[ ! -e "$aside" && ! -L "$aside" ]] || fail "Already exists: $aside"
    if [[ -e "$target" ]]; then mv -- "$target" "$aside"; fi
    if ! mv -- "$backup" "$target"; then
        if [[ -e "$aside" && ! -e "$target" ]]; then mv -- "$aside" "$target"; fi
        fail "Rollback failed. Inspect: $target and $backup"
    fi
    printf 'Restored backup to: %s\n' "$target"
    [[ ! -e "$aside" ]] || printf 'Current installation preserved at: %s\n' "$aside"
    printf 'Review PATH/profile and project copies manually. Open a new terminal; no old code was run.\n' >&2
    exit 0
fi

found=()
add_candidate() {
    local path item
    [[ -d "$(dirname -- "$1")" ]] || return 0
    path=$(normal_path "$1")
    get_backups "$path"
    [[ -e "$path" || ${#backups[@]} -gt 0 ]] || return 0
    for item in "${found[@]:-}"; do [[ "$item" != "$path" ]] || return 0; done
    found+=("$path")
}
add_bin() {
    local bin=${1%/} root
    [[ "$bin" == */bin ]] || return 0
    root=${bin%/bin}
    get_backups "$root"
    if [[ -f "$bin/cg-update" || -f "$bin/cg-link" || ${#backups[@]} -gt 0 ]]; then add_candidate "$root"; fi
}
if [[ -n "$install_path" ]]; then
    target=$(normal_path "$install_path")
else
    add_candidate "$HOME/.compound-gpid"
    for name in cg-update cg-link; do
        resolved=$(command -v "$name" || true)
        [[ -n "$resolved" ]] || continue
        [[ "$resolved" == */bin/"$name" ]] || fail "Unknown PATH wrapper; use --install-path: $resolved"
        add_candidate "${resolved%/bin/*}"
    done
    # Raw PATH entries still find an interrupted target whose wrappers are gone.
    remaining="${PATH:-}:"
    while [[ "$remaining" == *:* ]]; do
        entry=${remaining%%:*}; remaining=${remaining#*:}
        [[ -z "$entry" ]] || add_bin "$entry"
    done
    # Read only known PATH syntax inside owned blocks. Never source or eval rc text.
    path_pattern='^[[:space:]]*export[[:space:]]+PATH=(.*)/bin:'
    for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
        [[ -f "$rc" ]] || continue
        in_block=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            case "$line" in
                '# --- Compound GPID ---') in_block=1; continue ;;
                '# --- End Compound GPID ---') in_block=0; continue ;;
            esac
            [[ "$in_block" == 1 ]] || continue
            if [[ "$line" =~ $path_pattern ]]; then
                root=${BASH_REMATCH[1]}
                root=${root#\"}; root=${root#\'}
                case "$root" in
                    '$HOME/'*) root="$HOME/${root#\$HOME/}" ;;
                    '${HOME}/'*) root="$HOME/${root#\$\{HOME\}/}" ;;
                    '~/'*) root="$HOME/${root#\~/}" ;;
                esac
                [[ "$root" == /* && "$root" != *'$'* && "$root" != *'`'* ]] ||
                    fail "Unknown Compound GPID PATH block in $rc; use --install-path."
                add_candidate "$root"
            elif [[ "$line" == *PATH=* ]]; then
                fail "Unknown Compound GPID PATH block in $rc; use --install-path."
            fi
        done < "$rc"
    done
    [[ ${#found[@]} -gt 0 ]] || fail 'No installation found. Run the normal NEW scripts/install.sh instead.'
    if [[ ${#found[@]} -gt 1 ]]; then
        printf 'Multiple installations found. Use --install-path:\n' >&2
        printf '  %s\n' "${found[@]}" >&2
        exit 1
    fi
    target=${found[0]}
fi
assert_separate "$target"
get_backups "$target"
if [[ ${#backups[@]} -gt 0 ]]; then
    printf 'Stop lifecycle activity. Inspect the target and backups; choose one backup to restore.\n'
    for item in "${backups[@]}"; do rollback_command "$item"; done
    printf 'To resume: roll back first, then run this exact command:\n'
    printf '  bash %q --install-path %q\n' "$script" "$target"
    fail "Existing backup found: ${backups[*]}. Nothing was changed."
fi
assert_clone "$target"
shell=${SHELL:-/bin/bash}
case "${shell##*/}" in bash|zsh) ;; *) fail "Unsupported login shell: $shell. Use bash or zsh and review PATH manually." ;; esac
[[ -x "$shell" ]] || fail "User shell is not executable: $shell"
old_head=$(git -C "$target" rev-parse HEAD)
old_version=$(git -C "$target" describe --tags --always --dirty)
printf 'Old HEAD: %s\nOld describe: %s\nOld .cg-version: ' "$old_head" "$old_version"
if [[ -f "$target/.cg-version" ]]; then cat -- "$target/.cg-version"; else printf '(absent)'; fi
printf '\n'
safe_version=$(printf '%s' "$old_version" | LC_ALL=C tr -c 'A-Za-z0-9._-' '_' | sed 's/[bB][aA][cC][kK][uU][pP]/old/g')
backup="$target.backup-$safe_version-$stamp"
[[ ! -e "$backup" && ! -L "$backup" ]] || fail "Already exists: $backup"
printf 'Backup: %s\n' "$backup"
printf 'Stop other install/update/link activity. Installer PATH/profile writes are not snapshotted.\n' >&2
mv -- "$target" "$backup"
moved=1
mkdir -- "$target"
created=1
# --no-local avoids hardlinks/alternates and leaves the running clone untouched.
git -C "$source" clone --no-local --branch "$new_tag" -- "$source" "$target"
git -C "$target" remote set-url origin "$official"
git -C "$target" fetch --tags origin "refs/tags/$new_tag"
[[ "$(git -C "$target" rev-parse 'FETCH_HEAD^{commit}')" == "$new_head" &&
    "$(git -C "$target" rev-parse HEAD)" == "$new_head" ]] || fail 'Official tag does not match the running NEW clone.'
printf '%s' "$new_tag" > "$target/.cg-version"
bash "$target/scripts/install.sh" || fail 'NEW installer failed.'
new_status=$(git -C "$target" status --porcelain --untracked-files=all)
[[ "$(git -C "$target" rev-parse HEAD)" == "$new_head" &&
    "$(git -C "$target" describe --tags --exact-match HEAD)" == "$new_tag" &&
    "$(cat -- "$target/.cg-version")" == "$new_tag" &&
    -z "$new_status" ]] || fail 'NEW checkout/tag/pin/clean-status verification failed.'
for name in cg-link cg-unlink cg-update; do
    [[ -f "$target/bin/$name" && -x "$target/bin/$name" ]] || fail "Missing or non-executable NEW wrapper: $name"
done
moved=0
# PATH/profile problems do not undo a verified installation.
login_resolved=$("$shell" -lic 'command -v cg-update' || true)
interactive_resolved=$("$shell" -ic 'command -v cg-update' || true)
if [[ "$login_resolved" != "$target/bin/cg-update" && "$interactive_resolved" != "$target/bin/cg-update" ]]; then
    printf 'WARNING: NEW installation kept. Fresh shells do not resolve cg-update to the target.\n' >&2
    for resolved in "$login_resolved" "$interactive_resolved"; do
        [[ -z "$resolved" ]] || printf 'Shadowing cg-update: %s. Remove its bin directory from PATH in your shell profile.\n' "$resolved" >&2
    done
    if [[ "${shell##*/}" == bash ]]; then
        printf 'Add this exact line to ~/.bash_profile to load ~/.bashrc:\n  [ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"\n' >&2
    else
        printf 'Add this exact line to ~/.zprofile to load ~/.zshrc:\n  [ -f "$HOME/.zshrc" ] && . "$HOME/.zshrc"\n' >&2
    fi
    printf 'If PATH still omits the NEW bin directory, add this exact line to your shell rc file:\n  export PATH=%q:"$PATH"\n' "$target/bin" >&2
fi
printf 'Migrated: %s -> %s (pinned)\nBackup preserved: %s\n' "$old_version" "$new_tag" "$backup"
printf 'Open a new terminal. Run cg-link once per project. Unresolved project conflicts: manual action required; preserve files.\n'
printf 'Returning to latest is a separate user action. No project reconciliation was run.\nRollback (stop other lifecycle activity first):\n'
rollback_command "$backup"
