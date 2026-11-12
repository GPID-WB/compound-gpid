#!/bin/bash
# One old-tag upgrade, in a disposable hosted profile. No real Kilo launch.
# Usage: bash scripts/ci/upgrade-matrix.sh OLD_TAG FRESH_ROOT [migration|update|old-updater]
set -euo pipefail
old_tag=$1 root=$2
mode=${3:-migration}
legacy_note='compound-gpid.local.md has no settings block; using default settings. Your file was not changed. Run /cg-setup to add settings.'
[[ $mode == migration || $mode == update || $mode == old-updater ]] || { echo 'Unknown mode.' >&2; exit 1; }
[[ $mode != update || $old_tag == v1.2.0.9024 ]] || { echo 'Update mode requires genuine 9024.' >&2; exit 1; }
[[ $mode != old-updater || $old_tag == v1.1.11 || $old_tag == v1.2.0.9021 ]] || { echo 'Unsupported old-updater tag.' >&2; exit 1; }
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
snapshot_diffs=''
second_changed=false third_changed=false
old_outcome='not run'
finish() {
    code=$?
    trap - EXIT
    if [[ $code -ne 0 && -z $reason ]]; then reason="Exit $code at $stage; see the matching command log."; fi
    printf '| macos-latest | %s | %s | %s | %s |\n' "$old_tag" "$result" "$stage" "$reason" | tee "$root/result.md"
    if [[ $mode == old-updater ]]; then
        printf '\nOLD updater outcome: %s\n\nNEW migration and cg-link: %s (%s).\n' "$old_outcome" "$result" "$stage" >> "$root/result.md"
    fi
    if [[ -n $snapshot_diffs ]]; then
        printf '\n### Snapshot differences\n```text\n%s\n```\n' "$snapshot_diffs" >> "$root/result.md"
    fi
    [[ -z ${GITHUB_STEP_SUMMARY:-} ]] || cat "$root/result.md" >> "$GITHUB_STEP_SUMMARY"
    exit "$code"
}
trap finish EXIT
# checkout fetches all published tags; choose an unused numeric successor.
tags=$(git -C "$source" tag --list 'v*' --sort=-v:refname)
candidate_tag=$(printf '%s\n' "$tags" | LC_ALL=C awk -F . '
    /^v[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$/ && !found {
        printf "%s.%s.%s.%.0f\n", $1, $2, $3, (NF == 4 ? $4+1 : 9001)
        found=1
    }
    END { if (!found) exit 1 }
')
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
    (cd "$1" && find . -name .git -prune -o -type f -exec bash -c '
        for path; do
            hash=$(shasum -a 256 < "$path") || exit
            printf "%s|file|%s\n" "${path#./}" "${hash%% *}"
        done' _ {} + -o -type l -exec bash -c '
        for path; do
            target=$(readlink "$path") || exit
            printf "%s|link|%s\n" "${path#./}" "$target"
        done' _ {} + -o -type d -exec bash -c '
        for path; do printf "%s|directory\n" "${path#./}"; done' _ {} +) | LC_ALL=C sort
}
assert_snapshot() {
    local changes
    # Compare normalized records by path, including when either snapshot is empty.
    changes=$(LC_ALL=C awk -F '|' '
        FILENAME == ARGV[1] { before[$1] = $0; next }
        { after[$1] = $0 }
        END {
            for (path in before) {
                if (!(path in after)) print "removed: " path
                else if (before[path] != after[path]) print "changed: " path
            }
            for (path in after) if (!(path in before)) print "added: " path
        }' "$1" "$2" | LC_ALL=C sort) || return 2
    if [[ -n $changes || ${4:-} == report ]]; then
        local details=${changes:-unchanged}
        snapshot_diffs+="Snapshot comparison at $stage: $3"$'\n'"$details"$'\n'
        printf 'Snapshot comparison at %s: %s\n%s\n' "$stage" "$3" "$details" | tee -a "$root/snapshot-diff.log" || return 2
    fi
    [[ -z $changes ]] || { [[ ${4:-} == report ]] || reason="Snapshot mismatch: $3"; return 1; }
}
assert_repeat_snapshot() {
    local code=0 valid=true file generations staging line
    # Report physical UUID churn too, but require identical logical generation bytes.
    assert_snapshot "$1" "$2" "$3 (all physical changes)" report || code=$?
    [[ $code -le 1 ]] || return "$code"
    [[ ${4:-} == kilo-project ]] || return "$code" # Copy-only fixtures have no generation.
    for file in before after; do
        local input=$1
        [[ $file != after ]] || input=$2
        generations=$(awk -F '|' '$1 ~ /^\.compound-gpid\/generations\/[^\/]+$/ && $2 == "directory" { n++ } END { print n+0 }' "$input") || return 2
        LC_ALL=C awk -F '|' -v generations="$generations" '
            $1 ~ /^\.compound-gpid\/(active\/[^\/]+\.json|projection-ownership\.json|projection-transaction\.json)$/ && $2 == "file" { next }
            { if (generations == 1) sub(/^\.compound-gpid\/generations\/[^\/|]+/, ".compound-gpid/generations/<current>"); print }
        ' "$input" > "$root/repeat.$file" || return 2
    done
    code=0
    assert_snapshot "$root/repeat.before" "$root/repeat.after" "$3 (stable logical contents)" report || code=$?
    [[ $code -le 1 ]] || return "$code"
    [[ $code == 0 ]] || valid=false
    generations=$(awk -F '|' '$1 ~ /^\.compound-gpid\/generations\/[^\/]+$/ && $2 == "directory" { n++ } END { print n+0 }' "$2") || return 2
    staging=$(awk -F '|' '$1 ~ /^\.compound-gpid\/staging\/.+/ && $2 == "directory" { n++ } END { print n+0 }' "$2") || return 2
    line="$3 state: generation directories=$generations (required 1); staging directories=$staging (required 0)"
    snapshot_diffs+="$line"$'\n'
    printf '%s\n' "$line" | tee -a "$root/snapshot-diff.log" || return 2
    [[ $valid == true && $generations == 1 && $staging == 0 ]]
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
if [[ $mode != migration ]]; then
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
    [[ $mode == migration ]] || continue
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
# Preserve every historical tag; the successor cannot collide with one.
git -C "$candidate" fetch origin 'refs/tags/*:refs/tags/*'
git -C "$candidate" checkout --detach "$head"
git -C "$candidate" tag -a "$candidate_tag" -m 'LOCAL ONLY upgrade fixture' "$head"
git -C "$candidate" branch --force main "$head"
# Redirect official-tag verification to the unpublished local fixture remote.
git config --global "url.file://$candidate.insteadOf" https://github.com/GPID-WB/compound-gpid.git
if [[ $mode == old-updater ]]; then
    stage='OLD cg-update latest against candidate main'
    git -C "$install" remote set-url origin https://github.com/GPID-WB/compound-gpid.git
    git -C "$install" branch --force main "$old_head"
    git -C "$install" config branch.main.remote origin
    git -C "$install" config branch.main.merge refs/heads/main
    cd "$HOME/kilo-project"
    snapshot "$PWD" > "$root/project.before"
    old_code=0
    "$install/bin/cg-update" latest > "$root/old-updater.log" 2>&1 || old_code=$?
    observed_head=$(git -C "$install" rev-parse HEAD)
    observed_pin=$(cat "$install/.cg-version")
    snapshot "$install" > "$root/old.observed"
    snapshot "$PWD" > "$root/project.after"
    install_unchanged=true project_unchanged=true
    assert_snapshot "$root/old.before" "$root/old.observed" 'OLD updater installation changes' report || install_unchanged=false
    assert_snapshot "$root/project.before" "$root/project.after" 'OLD updater project changes' report || project_unchanged=false
    old_outcome='broken state'
    wrappers_present=true
    for wrapper in cg-link cg-update cg-unlink; do
        [[ -x "$install/bin/$wrapper" ]] || wrappers_present=false
    done
    if [[ $old_code == 0 && $observed_head == "$head" && $observed_pin == latest &&
          $wrappers_present == true && -z $(git -C "$install" status --porcelain) ]]; then
        old_outcome=success
    elif [[ $old_code != 0 && $install_unchanged == true && $project_unchanged == true && -s "$root/old-updater.log" ]]; then
        old_outcome='safe stop with a message'
    fi
    old_outcome+="; exit=$old_code; HEAD=$observed_head; pin=$observed_pin; see old-updater.log"
    # Preserve the actual post-updater state, not the initial tag.
    old_head=$observed_head
    cp "$root/old.observed" "$root/old.before"
fi
if [[ $mode == update ]]; then
    stage='installed 9024 updater'
    git -C "$install" remote set-url origin https://github.com/GPID-WB/compound-gpid.git
    [[ -z $(git -C "$install" status --porcelain) ]]
    # Old updater rejects stale consumer manifests; NEW cg-link refreshes them
    # after the installation update from neutral fixture HOME.
    cd "$HOME"
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
        assert_snapshot "$root/$name.before" "$root/$name.after" "$name changed"
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
assert_snapshot "$root/old.before" "$root/old.after" 'Old installation bytes were not preserved in backup.'
for wrapper in cg-link cg-update cg-unlink; do
    [[ -x "$install/bin/$wrapper" ]]
    cmp "$install/bin/$wrapper" "$candidate/bin/$wrapper"
done
resolved=$(/bin/bash -ic 'command -v cg-update' 2>/dev/null || true)
[[ $resolved == "$install/bin/cg-update" ]] || grep -F 'WARNING: NEW installation kept.' "$root/migration.log"
snapshot "$candidate" > "$root/candidate.before"
snapshot "${backups[0]}" > "$root/backup.before"
snapshot "$install" > "$root/install.before"
if [[ $mode == old-updater ]]; then
    stage='NEW cg-link after OLD updater and migration'
    cd "$HOME/kilo-project"
    run recovered-link "$install/bin/cg-link" --platforms kilo --yes
    cmp .kilo/commands/cg-review.md "$candidate/.kilo/commands/cg-review.md"
    grep -qxF 'small Git project' fixture.txt
    for name in candidate backup install outside source; do
        case $name in backup) path=${backups[0]} ;; outside) path=$root/outside ;; *) path=${!name} ;; esac
        snapshot "$path" > "$root/$name.after"
        assert_snapshot "$root/$name.before" "$root/$name.after" "$name changed"
    done
    result=pass
    exit 0
fi
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
    assert_snapshot "$root/project.before" "$root/project.after" 'Read-only check changed project.'
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
    if [[ ${names[i]} != kilo-project ]]; then
        cmp .github/copilot-instructions.md.pre-9024.bak "$root/copilot.before"
        [[ -f .github/copilot-instructions.md && -r .github/copilot-instructions.md ]]
        grep -F '<!-- compound-gpid:managed -->' .github/copilot-instructions.md
        ! grep -F 'upgrade Copilot user edit' .github/copilot-instructions.md
    fi
    stage="candidate repeat (${names[i]})"
    snapshot "$project" > "$root/project.before"
    run "repeat-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    snapshot "$project" > "$root/project.second"
    diff_code=0
    assert_repeat_snapshot "$root/project.before" "$root/project.second" 'Link 1->2' "${names[i]}" || diff_code=$?
    [[ $diff_code -le 1 ]] || exit "$diff_code"
    [[ $diff_code == 0 ]] || second_changed=true
    stage="candidate third link (${names[i]})"
    run "third-${names[i]}" bash "$install/scripts/link.sh" --platforms "${platforms[i]}" --yes
    snapshot "$project" > "$root/project.third"
    diff_code=0
    assert_repeat_snapshot "$root/project.second" "$root/project.third" 'Link 2->3' "${names[i]}" || diff_code=$?
    [[ $diff_code -le 1 ]] || exit "$diff_code"
    [[ $diff_code == 0 ]] || third_changed=true
    if [[ ${names[i]} == kilo-project ]]; then
        [[ $(grep -F -o "$legacy_note" "$root/repeat-${names[i]}.log" | wc -l | tr -d ' ') == 1 ]]
        [[ $(grep -F -o "$legacy_note" "$root/third-${names[i]}.log" | wc -l | tr -d ' ') == 1 ]]
        cmp compound-gpid.local.md "$root/legacy-config.before"
    fi
done
stage='outside-write checks'
for name in candidate backup install outside source; do
    case $name in backup) path=${backups[0]} ;; outside) path=$root/outside ;; *) path=${!name} ;; esac
    snapshot "$path" > "$root/$name.after"
    assert_snapshot "$root/$name.before" "$root/$name.after" "$name changed"
done
stage='repeat snapshot assertions'
if [[ $second_changed == true ]]; then reason='Second link violated repeat content/state constraints.'; exit 1; fi
if [[ $third_changed == true ]]; then reason='Third link violated repeat content/state constraints.'; exit 1; fi
result=pass
