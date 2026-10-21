#!/bin/bash
# One old-tag upgrade, in a disposable hosted profile. No real Kilo launch.
# Usage: bash scripts/ci/upgrade-matrix.sh OLD_TAG FRESH_ROOT [migration|update]
set -euo pipefail
old_tag=$1 root=$2
mode=${3:-migration}
candidate_tag=v1.2.0.9025
legacy_note='compound-gpid.local.md has no settings block; using default settings. Your file was not changed. Run /cg-setup to add settings.'
[[ $mode == migration || $mode == update ]] || { echo 'Unknown mode.' >&2; exit 1; }
[[ $mode != update || $old_tag == v1.2.0.9024 ]] || { echo 'Update mode requires genuine 9024.' >&2; exit 1; }
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
git clone --no-local --no-tags --branch "$old_tag" -c core.autocrlf=false "$source" "$install"
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
    edited+=('') unedited+=(.kilo/commands/cg-review.md)
    user+=(.kilo/commands/user-upgrade-sentinel.md)
fi
if [[ $mode == update ]]; then
    names=(kilo-project) platforms=(kilo)
fi
for ((i=0; i<${#names[@]}; i++)); do
    project="$HOME/${names[i]}"
    git init "$project"
    printf 'small Git project\n' > "$project/fixture.txt"
    if [[ $mode == update ]]; then
        printf '%s\n' '---' 'language: both' 'suites: [cg]' '---' '# Valid fixture settings' > "$project/compound-gpid.local.md"
        cp "$project/compound-gpid.local.md" "$root/valid-config.before"
    fi
    git -C "$project" add fixture.txt
    git -C "$project" commit -m fixture
    cd "$project"
    stage="old link (${names[i]})"
    run "old-link-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    [[ $mode != update ]] || continue
    if [[ -n ${edited[i]} ]]; then
        [[ ! -L "$(dirname "${edited[i]}")" && ! -L "${edited[i]}" ]]
        printf '\n<!-- upgrade user edit -->\n' >> "${edited[i]}"
        cp "${edited[i]}" "$root/${names[i]}-edited.before"
    fi
    printf 'user-added bytes\n' > "${user[i]}"
    cp "${user[i]}" "$root/${names[i]}-user.before"
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
# Preserve historical release proofs, excluding only the local fixture tag.
git -C "$candidate" fetch origin 'refs/tags/*:refs/tags/*' "^refs/tags/$candidate_tag"
git -C "$candidate" checkout --detach "$head"
git -C "$candidate" tag -a "$candidate_tag" -m 'LOCAL ONLY upgrade fixture' "$head"
# Redirect official-tag verification to the unpublished local fixture remote.
git config --global "url.file://$candidate.insteadOf" https://github.com/GPID-WB/compound-gpid.git
if [[ $mode == update ]]; then
    stage='installed 9024 updater'
    git -C "$install" remote set-url origin https://github.com/GPID-WB/compound-gpid.git
    [[ -z $(git -C "$install" status --porcelain) ]]
    cd "$HOME/kilo-project"
    run installed-update "$install/bin/cg-update" "$candidate_tag"
    [[ $(git -C "$install" rev-parse HEAD) == "$head" ]]
    [[ $(cat "$install/.cg-version") == "$candidate_tag" ]]
    [[ -z $(git -C "$install" status --porcelain) ]]
    snapshot "$candidate" > "$root/candidate.before"
    snapshot "$install" > "$root/install.before"
    for name in kilo-project legacy-project; do
        project="$HOME/$name"
        if [[ $name == legacy-project ]]; then
            git init "$project"
            printf '# Old project notes\r\nUse R and keep these free-form notes.' > "$project/compound-gpid.local.md"
            cp "$project/compound-gpid.local.md" "$root/legacy-config.before"
        fi
        cd "$project"
        stage="updated link ($name)"
        run "updated-link-$name" "$install/bin/cg-link" --platforms kilo --yes
        [[ -f .kilo/commands/cg-review.md ]]
        if [[ $name == legacy-project ]]; then
            [[ $(grep -F -o "$legacy_note" "$root/updated-link-$name.log" | wc -l | tr -d ' ') == 1 ]]
            cmp compound-gpid.local.md "$root/legacy-config.before"
        else
            cmp compound-gpid.local.md "$root/valid-config.before"
        fi
    done
    stage='outside-write checks'
    for name in candidate install outside source; do
        case $name in outside) path=$root/outside ;; *) path=${!name} ;; esac
        snapshot "$path" > "$root/$name.after"
        cmp "$root/$name.before" "$root/$name.after"
    done
    [[ -z $(git -C "$install" status --porcelain) ]]
    result=pass
    exit 0
fi
stage='candidate migration'
run migration bash "$candidate/scripts/migrate-install.sh" --install-path "$install"
[[ $(git -C "$install" rev-parse HEAD) == "$head" ]]
[[ $(cat "$install/.cg-version") == "$candidate_tag" ]]
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
    if [[ ${names[i]} == kilo-project ]]; then
        printf '# Old project notes\r\nUse R and keep these free-form notes.' > "$project/compound-gpid.local.md"
        cp "$project/compound-gpid.local.md" "$root/legacy-config.before"
    fi
    cd "$project"
    stage="candidate check (${names[i]})"
    snapshot "$project" > "$root/project.before"
    check_code=0
    bash "$install/scripts/link.sh" --check --platforms "${platforms[i]}" > "$root/check-${names[i]}.log" 2>&1 || check_code=$?
    [[ $check_code == 0 || $check_code == 1 ]]
    grep -F 'Manual action required:' "$root/check-${names[i]}.log"
    if [[ -n ${edited[i]} ]]; then
        [[ $check_code == 1 ]]
        grep -F "${edited[i]}" "$root/check-${names[i]}.log"
    else
        [[ $(grep -F -o "$legacy_note" "$root/check-${names[i]}.log" | wc -l | tr -d ' ') == 1 ]]
    fi
    snapshot "$project" > "$root/project.after"
    cmp "$root/project.before" "$root/project.after"
    stage="candidate link (${names[i]})"
    run "link-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    if [[ ${names[i]} == kilo-project ]]; then
        [[ $(grep -F -o "$legacy_note" "$root/link-${names[i]}.log" | wc -l | tr -d ' ') == 1 ]]
        cmp compound-gpid.local.md "$root/legacy-config.before"
    fi
    if [[ -n ${edited[i]} ]]; then cmp "${edited[i]}" "$root/${names[i]}-edited.before"; fi
    cmp "${unedited[i]}" "$candidate/${unedited[i]}"
    if [[ -n ${edited[i]} ]]; then
        grep -E 'Manual action required: [1-9]' "$root/link-${names[i]}.log"
        grep -F "${edited[i]}" "$root/link-${names[i]}.log"
    fi
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
    if [[ ${names[i]} == kilo-project ]]; then
        [[ $(grep -F -o "$legacy_note" "$root/repeat-${names[i]}.log" | wc -l | tr -d ' ') == 1 ]]
        cmp compound-gpid.local.md "$root/legacy-config.before"
    fi
done
stage='outside-write checks'
for name in candidate backup install outside source; do
    case $name in backup) path=${backups[0]} ;; outside) path=$root/outside ;; *) path=${!name} ;; esac
    snapshot "$path" > "$root/$name.after"
    cmp "$root/$name.before" "$root/$name.after"
done
result=pass
