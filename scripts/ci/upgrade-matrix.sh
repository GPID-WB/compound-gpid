#!/bin/bash
# One old-tag upgrade, in a disposable hosted profile. No real Kilo launch.
# Usage: bash scripts/ci/upgrade-matrix.sh OLD_TAG FRESH_ROOT
set -euo pipefail
old_tag=$1 root=$2
source=$(cd "$(dirname "$0")/../.." && pwd -P)
[[ ${GITHUB_ACTIONS:-} == true ]] || { echo 'Requires a disposable hosted account.' >&2; exit 1; }
[[ ! -e "$root" && -d "$(dirname "$root")" ]] || { echo 'Root must be fresh with an existing parent.' >&2; exit 1; }
mkdir "$root"
root=$(cd "$root" && pwd -P)
export HOME="$root/home" USERPROFILE="$root/home"
export APPDATA="$HOME/AppData/Roaming" LOCALAPPDATA="$HOME/AppData/Local" XDG_CONFIG_HOME="$HOME/.config"
export TMPDIR="$HOME/temp" TEMP="$HOME/temp" TMP="$HOME/temp" ZDOTDIR="$HOME" SHELL=/bin/bash
export GIT_CONFIG_GLOBAL="$HOME/gitconfig" GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 GIT_ALLOW_PROTOCOL=file
export CG_SKIP_UPDATE=1 PYTHONDONTWRITEBYTECODE=1
install="$HOME/.compound-gpid" candidate="$HOME/candidate"
stage='fixture setup' result=fail reason=''
finish() {
    code=$?
    trap - EXIT
    if [[ $code -ne 0 ]]; then reason="Exit $code at $stage; see the matching command log."; fi
    printf '| macos-latest | %s | %s | %s | %s |\n' "$old_tag" "$result" "$stage" "$reason" | tee "$root/result.md"
    [[ -z ${GITHUB_STEP_SUMMARY:-} ]] || cat "$root/result.md" >> "$GITHUB_STEP_SUMMARY"
    exit "$code"
}
trap finish EXIT
run() {
    local name=$1 code=0
    shift
    "$@" > "$root/$name.log" 2>&1 || code=$?
    if [[ $code -ne 0 ]]; then
        cat "$root/$name.log"
        # Do not turn arbitrary old-command/harness errors into successful skips.
        return "$code"
    fi
}
snapshot() {
    # BSD find defaults to no symlink traversal; exclude Git's mutable index/cache.
    (cd "$1" && find . -name .git -prune -o -type f -exec shasum -a 256 {} \; -o \
        -type l -exec ls -ld {} \; -o -type d -print) | LC_ALL=C sort
}
mkdir -p "$APPDATA" "$LOCALAPPDATA" "$XDG_CONFIG_HOME" "$TMPDIR" "$root/outside"
printf 'outside fixture\n' > "$root/outside/sentinel.txt"
snapshot "$root/outside" > "$root/outside.before"
snapshot "$source" > "$root/source.before"
git config --global user.name 'Upgrade fixture'
git config --global user.email upgrade@example.invalid
git config --global commit.gpgsign false
git config --global maintenance.auto false
git clone --no-local --branch "$old_tag" -c core.autocrlf=false "$source" "$install"
old_head=$(git -C "$install" rev-parse HEAD)
printf '%s' "$old_tag" > "$install/.cg-version"
stage='old installer'
run old-installer bash "$install/scripts/install.sh"
names=(project) platforms=(copilot,claude-code)
edited=(.claude/CLAUDE.md) unedited=(.github/prompts/cg-review.prompt.md)
user=(.claude/user-upgrade-sentinel.md)
if [[ $old_tag != v1.0.4 ]]; then
    # Separate Kilo consumer: old coexistence gates require a host otherwise.
    names+=(kilo-project) platforms+=(kilo)
    edited+=(.kilo/commands/cg-plan.md) unedited+=(.kilo/commands/cg-review.md)
    user+=(.kilo/commands/user-upgrade-sentinel.md)
fi
for ((i=0; i<${#names[@]}; i++)); do
    project="$HOME/${names[i]}"
    git init "$project"
    printf 'small Git project\n' > "$project/fixture.txt"
    git -C "$project" add fixture.txt
    git -C "$project" commit -m fixture
    cd "$project"
    stage="old link (${names[i]})"
    run "old-link-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    [[ ! -L "$(dirname "${edited[i]}")" && ! -L "${edited[i]}" ]]
    printf '\n<!-- upgrade user edit -->\n' >> "${edited[i]}"
    printf 'user-added bytes\n' > "${user[i]}"
    cp "${user[i]}" "$root/${names[i]}-user.before"
    cp "${edited[i]}" "$root/${names[i]}-edited.before"
    if [[ -f .github/copilot-instructions.md ]]; then
        printf '\n<!-- upgrade Copilot user edit -->\n' >> .github/copilot-instructions.md
        cp .github/copilot-instructions.md "$root/copilot.before"
    fi
done
snapshot "$install" > "$root/old.before"
stage='candidate clone and local-only tag'
head=$(git -C "$source" rev-parse HEAD)
# The local fixture tag must not collide with an inherited published tag.
git clone --no-local --no-tags -c core.autocrlf=false "$source" "$candidate"
git -C "$candidate" checkout --detach "$head"
git -C "$candidate" tag -a v1.2.0.9024 -m 'LOCAL ONLY upgrade fixture' "$head"
# Redirect official-tag verification to the unpublished local fixture remote.
git config --global "url.file://$candidate.insteadOf" https://github.com/GPID-WB/compound-gpid.git
stage='candidate migration'
run migration bash "$candidate/scripts/migrate-install.sh" --install-path "$install"
[[ $(git -C "$install" rev-parse HEAD) == "$head" ]]
[[ $(cat "$install/.cg-version") == v1.2.0.9024 ]]
backups=("$install".backup-*)
[[ ${#backups[@]} == 1 && -d ${backups[0]} ]]
[[ $(git -C "${backups[0]}" rev-parse HEAD) == "$old_head" ]]
snapshot "${backups[0]}" > "$root/old.after"
cmp "$root/old.before" "$root/old.after"
for wrapper in cg-link cg-update cg-unlink; do
    [[ -x "$install/bin/$wrapper" ]]
    cmp "$install/bin/$wrapper" "$candidate/bin/$wrapper"
done
resolved=$(/bin/bash -ic 'command -v cg-update' 2>/dev/null || true)
[[ $resolved == "$install/bin/cg-update" ]] || grep -F 'WARNING: NEW installation kept.' "$root/migration.log"
snapshot "$candidate" > "$root/candidate.before"
snapshot "${backups[0]}" > "$root/backup.before"
snapshot "$install" > "$root/install.before"
for ((i=0; i<${#names[@]}; i++)); do
    project="$HOME/${names[i]}"
    cd "$project"
    stage="candidate check (${names[i]})"
    snapshot "$project" > "$root/project.before"
    check_code=0
    bash "$install/scripts/link.sh" --check --platforms "${platforms[i]}" > "$root/check-${names[i]}.log" 2>&1 || check_code=$?
    [[ $check_code == 1 ]]
    grep -F 'Manual action required:' "$root/check-${names[i]}.log"
    grep -F "${edited[i]}" "$root/check-${names[i]}.log"
    snapshot "$project" > "$root/project.after"
    cmp "$root/project.before" "$root/project.after"
    stage="candidate link (${names[i]})"
    run "link-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    cmp "${edited[i]}" "$root/${names[i]}-edited.before"
    cmp "${unedited[i]}" "$candidate/${unedited[i]}"
    grep -E 'Manual action required: [1-9]' "$root/link-${names[i]}.log"
    grep -F "${edited[i]}" "$root/link-${names[i]}.log"
    cmp "${user[i]}" "$root/${names[i]}-user.before"
    if [[ ${names[i]} == kilo-project ]]; then
        grep -F 'user-upgrade-sentinel.md: user file kept' "$root/link-${names[i]}.log"
    else
        cmp .github/copilot-instructions.md.pre-9024.bak "$root/copilot.before"
        [[ -f .github/copilot-instructions.md && -r .github/copilot-instructions.md ]]
        grep -F '<!-- compound-gpid:managed -->' .github/copilot-instructions.md
        ! grep -F 'upgrade Copilot user edit' .github/copilot-instructions.md
    fi
    stage="candidate repeat (${names[i]})"
    snapshot "$project" > "$root/project.before"
    run "repeat-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    snapshot "$project" > "$root/project.after"
    cmp "$root/project.before" "$root/project.after"
done
stage='outside-write checks'
for name in candidate backup install outside source; do
    case $name in backup) path=${backups[0]} ;; outside) path=$root/outside ;; *) path=${!name} ;; esac
    snapshot "$path" > "$root/$name.after"
    cmp "$root/$name.before" "$root/$name.after"
done
result=pass
