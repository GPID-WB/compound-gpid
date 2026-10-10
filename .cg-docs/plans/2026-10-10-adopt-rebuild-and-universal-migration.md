---
artifact-schema-version: 1
date: "2026-10-10"
title: "Adopt Rebuild and Universal Migration"
status: active
scope: Deep
deviation-policy: strict
---

## Objective
Make roadmap step 3 safe for users on any published version: 9024 migration tool, small upgrade matrix, guide and required small ports; announcement; reviewed dev adoption; reviewed main adoption; official release decision. Current approval covers recording decisions and implementing ONLY Phase 1 Step 1, isolated tests, commits and normal push. Later steps need separate execution approval.

## Context
Baseline: `chore/rebuild-from-9017`, 9023 = `e8cd488066524d9d4f92dae81d06d2ff3d364394`; published prerelease, Windows/macOS host-mode tests green. Roadmap: `2026-10-08-rebuild-roadmap.md:22-54`; saved `rebuild.roadmap`, `rebuild.status`, `migration.universal`. Real-project pilot completion remains an adoption entry criterion, not a result inferred from CI.
Live read-only refs on 2026-10-10: dev `f4f4eceaa95c565b7c9c7224d9d276997584dd79`; main `89b2730495b783bf02c7716c4a1c653e015f2721`; archive `51bb64b48189de2715489963549f8c2c1a274a97`. Main contains dev plus nine commits. GitHub Latest is still `v1.2.0.9003`, marked non-prerelease; this is independent of updater `latest`.

## Installation Footprint (Part A)
Families describe persistent install/update/link protocols, not each added command. This 26-family table is REFERENCE, not the initial CI matrix. Ranges include intermediate tags; side tags are assigned explicitly. Later rows inherit the shared footprint unless stated otherwise. Evidence is immutable `rev:path:line`; no historical code was run.
Shared locations: scripts derive the clone root from their location, including custom paths (`v0.0.5:install.ps1:21-23`). Documented defaults include `C:\WBG\.compound-gpid`, `%USERPROFILE%\.compound-gpid`, and POSIX `~/.compound-gpid` (`v0.9.0.9000:docs/installation.md:18-19,103-106`). Windows registers clone `bin` in HKCU `Environment\PATH`, later sets `COMPOUND_GPID_INSTALLED`, and cleans recognized profile functions. POSIX modifies marked `.zshrc`/`.bashrc` blocks, not automatically `.zprofile` (`v1.2.0.9006:install.ps1:349-381`; `v1.2.0.9006:scripts/install.sh:59-82,370-425`).
Shared update modes: `.cg-version` stores `latest` or a tag; explicit selection wins. Latest pulls the attached branch, normally main, switching detached installs to main; it is NOT GitHub Latest. Old latest discards tracked edits; pins fetch/checkout a tag. The original updater process then refreshes current-project instructions/copies and may migrate knowledge folders, not its newly checked-out updater (`v0.0.5:scripts/update.ps1:148-259,270-359`; `v1.0.3:scripts/update.ps1:384-518`). Normal updates do not rerun installer/link/npm; the repair side tag below is an exception. Latest target generation starts at 1.0.2; old pins do not generate; rebuild pins validate with `--all --dry-run` (`v1.2.0.9006:scripts/update.ps1:340-385`; `v1.2.0.9022:scripts/update.ps1:405-425`).

| Family / Tags | Fixture Tag | Install / Update Difference | Project And External Footprint | Evidence |
|---|---|---|---|---|
| F01: v0.0.5-v0.0.8 | v0.0.5 | Clone-relative CMD generation; HKCU PATH append; three-number pins, latest as above | Four Copilot junctions; marked instructions copy; no ownership receipt, projection, mirror or plugin | `v0.0.5:install.ps1:107-170`; `v0.0.5:scripts/link.ps1:36-41`; `v0.0.5:scripts/update.ps1:76-95` |
| F02: v0.1.0-v0.6.6, including v0.1.0.9000 | v0.3.0 | Repair/dev-pin support in .1; PATH prepend and persistent install marker in .3 | Same links/copy; .2 removes old knowledge ignore block | `v0.1.0.9000:scripts/update.ps1:57-62,85-119,173-177`; `v0.3.0:install.ps1:123-137`; `v0.2.0:scripts/link.ps1:234-248` |
| F03: v0.7.0-v0.9.0 stable | v0.7.0 | Same Windows registration and updater | Instructions now generated from template; no POSIX installer yet | `v0.7.0:scripts/link.ps1:164-185`; `v0.7.0:scripts/helpers.ps1:51-125` |
| F04: v0.9.0.9000, v0.9.1-v0.9.2 | v0.9.0.9000 | First POSIX installer: writes wrappers/chmod and rc PATH; same latest/pin model | POSIX symlinks replace Windows junctions; instructions copy; no new receipt | `v0.9.0.9000:scripts/install.sh:182-249`; `v0.9.0.9000:bin/cg-link:6` |
| F05: v0.10.0-v0.17.1, except v0.10.2.9001 | v0.17.1 | More generated wrappers; Windows self-copy repaired by .17.1 | Fifth shared link; optional manually copied root adapters, not managed native linking | `v0.10.2:scripts/link.sh:33`; `v0.17.1:install.ps1:175-185`; `v0.17.0:adapters/manifest.json:5-18` |
| F06: v0.10.2.9001 side branch | v0.10.2.9001 | POSIX removes old functions/exports; repair update reruns installer | Legacy links; no native ownership/projection | `v0.10.2.9001:scripts/install.sh:323-390`; `v0.10.2.9001:scripts/update.sh:131-132` |
| F07: v0.18.0-v1.0.1 | v0.18.0 | Four adapters by default; .18.1 installer/.18.2 updater widen Windows profile cleanup | Copilot/Claude/Codex/OpenCode unit links; managed root/config copies; consumer `managed-files.json` | `v0.18.0:scripts/link.ps1:27,58-59`; `v0.18.0:.github/shared/target-mapping.json:70-154`; `v0.18.2:scripts/update.ps1:49-63` |
| F08: v1.0.2 | v1.0.2 | Latest generation optional/warning-only; link can continue after update failure | Adds source-tree `.compound-gpid-generated.json`, distinct from consumer receipts | `v1.0.2:scripts/cg_generate_targets.py:56,899-916,1037-1067`; `v1.0.2:scripts/update.ps1:304-328`; `v1.0.2:scripts/link.ps1:285-294` |
| F09: v1.0.3, v1.1.0.9000 side tag | v1.0.3 | Latest generation mandatory; link blocks on update failure unless skip variable | Native instructions/shared closure completed; research side tag shares lifecycle files | `v1.0.3:.github/shared/target-mapping.json:75-76,119-120,156-157`; `v1.0.3:scripts/update.ps1:308-326`; `v1.0.3:scripts/link.ps1:286-300` |
| F10: v1.0.4-v1.1.3 stable | v1.0.4 | Same update protocol; later render/publish wrappers | Retires native model JSON only when receipt hash matches; modified bytes remain | `v1.0.4:.github/shared/target-mapping.json:61-67,95-101,129-142`; `v1.0.4:scripts/link.ps1:163-214,272-300` |
| F11: v1.1.4-v1.1.5 | v1.1.4 | Adds Kilo selection; installers still generate wrappers | Kilo category links, copied AGENTS.md, copy-or-snippet kilo.json; no global Kilo writer yet | `v1.1.4:scripts/link.ps1:58`; `v1.1.4:.github/shared/target-mapping.json:170-182` |
| F12: v1.1.6-v1.1.8 | v1.1.6 | Same registration/update | Kilo links; POSIX adds global `~/.config/kilo/kilo.jsonc` markdown permission; unlink retains it | `v1.1.6:scripts/link.sh:438-496,563-571`; `v1.1.6:scripts/unlink.sh:165-169` |
| F13: v1.1.9-v1.1.10 | v1.1.9 | Same registration/update | Kilo POSIX recursive copies without per-file ownership; Windows still junctions despite copy strategy | `v1.1.9:.github/shared/target-mapping.json:171-175`; `v1.1.9:scripts/link.sh:220-257`; `v1.1.9:scripts/link.ps1:123-158` |
| F14: v1.1.11 | v1.1.11 | Same registration/update | Windows Kilo copies gain `.compound-gpid-managed-copy.json`; POSIX remains recursive overwrite | `v1.1.11:scripts/link.ps1:29,278-283,316-409,479-492`; `v1.1.9:scripts/link.sh:239-253` |
| F15: v1.2.0.9000-v1.2.0.9001 | v1.2.0.9000 | Module generation, optional suite filter; normal updater still `--all` | Windows regresses to Kilo junctions; POSIX copies/global grant; no consumer projection | `v1.2.0.9000:scripts/cg_generate_targets.py:523-549,1543-1545`; `v1.2.0.9000:scripts/link.ps1:123-158` |
| F16: v1.2.0.9002-v1.2.0.9005 | v1.2.0.9002 | Same generated-wrapper/numeric update protocol | Restores Windows checksum Kilo copies; lifecycle/map unchanged through 9005 | `v1.2.0.9002:scripts/link.ps1:29,33-38,307-326,505-515` |
| F17: v1.2.0.9006 | v1.2.0.9006 | Windows rewrites three dispatch wrappers; POSIX rewrites tracked wrappers/modes; no pin rollback | Manifest projection, legacy links and checksum Kilo copies; exact host allowlist; global Kilo grant on Windows too | `v1.2.0.9006:install.ps1:237-242`; `v1.2.0.9006:scripts/link.ps1:764-861`; `v1.2.0.9006:scripts/helpers.ps1:774-856` |
| F18: v1.2.0.9007-v1.2.0.9009 | v1.2.0.9007 | Same mutable-wrapper updater, allowlist and no rollback | Adds checksum-owned adapter-specific skills mirrors under `.compound-gpid/kilo-compat-skills` | `v1.2.0.9007:scripts/link.ps1:664-710`; `v1.2.0.9007:scripts/link.sh:889-965`; `v1.2.0.9007:.kilo/kilo.json:11-15` |
| F19: v1.2.0.9010-v1.2.0.9011 | v1.2.0.9010 | Same installer/updater/allowlist | Source-resolved projection before Kilo checks; managed projection-root/state ignores | `v1.2.0.9010:scripts/link.ps1:904-913,923-985,998-1027` |
| F20: v1.2.0.9012-v1.2.0.9013 | v1.2.0.9012 | Adds cg-skill; retires discovery wrappers; same updater/allowlist | Copilot skills become local projection; other Copilot categories remain linked | `v1.2.0.9012:install.ps1:234-242,339-355`; `v1.2.0.9012:.github/shared/target-mapping.json:9-38,69-202` |
| F21: v1.2.0.9014-v1.2.0.9016 | v1.2.0.9014 | Adds legacy research-output migration in update/link; exact allowlist retained | Hybrid projection/copies/mirrors; research migration also native-only | `v1.2.0.9014:scripts/update.ps1:540-558,641-660`; `v1.2.0.9014:scripts/update.sh:602-614,677-690` |
| F22: v1.2.0.9017 | v1.2.0.9017 | Same old updater, no rollback; minimum Kilo 7.4.20 replaces exact allowlist | Hybrid projection/legacy links/copies/mirrors; no native plugin | `v1.2.0.9017:scripts/cg_kilo_preflight.py:24-26,405-409,675-684`; `v1.2.0.9017:scripts/link.ps1:923-1027` |
| F23: v1.2.0.9018-v1.2.0.9019, old line | v1.2.0.9018 | SemVer prerelease/build readers and show-dev; old reset/no rollback; minimum host | Same project install protocol; async controller in clone, not native-evidence plugin | `v1.2.0.9018:scripts/update.ps1:92-146,249-252,337-449`; `v1.2.0.9018:scripts/cg_kilo_preflight.py:26,678-684` |
| F24: v1.2.0.9020-v1.2.0.9021, old line | v1.2.0.9020 | Help/release/autopilot wrappers; same old updater/minimum host | Manifest Kilo includes native-evidence loader + four modules; legacy units do not deliver plugin directory | `v1.2.0.9020:install.ps1:248-252,291-406`; `v1.2.0.9020:scripts/cg_generate_targets.py:89-95,1505-1511`; `v1.2.0.9020:.github/shared/target-mapping.json:244-256` |
| F25: v1.2.0.9022, rebuild | v1.2.0.9022 | POSIX validates shipped wrappers without rewrite/chmod; Windows writes remain; latest refuses dirty tracked/staged state; numeric pins gain rollback | 9017 hybrid footprint; minimum host; narrowly retires proven native-plugin bytes | `v1.2.0.9022:scripts/install.sh:203-218`; `v1.2.0.9022:scripts/update.ps1:281-284,369-425,759-796`; `v1.2.0.9022:scripts/cg_retire_native_evidence.py:23-36,193-201` |
| F26: v1.2.0.9023, rebuild | v1.2.0.9023 | Recoverable numeric updater; NO lifecycle host/version dependency | Same local footprint/retirement and global grant; optional launcher containment, advisory version only | `e8cd4880:scripts/link.ps1:999-1022`; `e8cd4880:scripts/update.ps1:476-497`; `e8cd4880:scripts/cg_kilo_preflight.py:665-681` |

Short notes: F05 includes v0.10.2.9000 and v0.12.0.9000/.9001/.9002; index, brain-init, token-audit and summary wrapper additions do not change its ownership protocol (`v0.12.0.9002:scripts/install.sh:213-223`; `v0.16.0:scripts/install.sh:228-238`). Unprefixed pre-v0.0.5 tags exist but are outside the stated supported tag range; discovery still reports unknown installs without executing them.
Project inventory: copied root/config receipt `.compound-gpid/managed-files.json`; directory-copy receipt `.compound-gpid-managed-copy.json`; projection `active-manifest.json`, `projection-ownership.json`, `projection-transaction.json`, `staging/`, `generations/`, `active/`, `retired/`; mirrors; managed ignores; marked Copilot instructions (`v1.2.0.9006:scripts/link.ps1:26-29`; `v1.2.0.9006:scripts/cg_project_projection.py:68-75`). No evidence that installers deploy consumer `.vscode/settings.json` or `.claude/settings.json`: old `.vscode/settings.json` is checkout configuration (`v1.2.0.9020:.vscode/settings.json:13-19`). Inspect user settings but never claim ownership from their filename.

## Migration Design (Part B)
Ship only `scripts/migrate-install.ps1` and `scripts/migrate-install.sh` in 9024. Run their absolute paths from a fresh official 9024 clone outside the selected old install. Require trusted Git and normal new-install prerequisites, never Kilo. Never run/source/import old Compound GPID scripts, wrappers, installer, updater or linker; use normal Git commands.
Discovery is read-only: resolve PATH cg-update/cg-link plus defaults, including custom paths/spaces. Multiple distinct installs require `-InstallPath`/`--install-path`; never choose the first silently. Refuse links/junctions, `.git` files/worktrees, non-clone roots and source/target overlap before moving anything. Unknown metadata is reported, not authority to replace a directory.
Verify a clean standalone NEW clone at an exact release tag, without Kilo. Record only old HEAD, `git describe --tags --always --dirty` and literal `.cg-version`; never run old-clone status, reset/stash/clean or execute old code. Move the entire folder to `<target>.backup-<safe old version>-<timestamp>` in the same parent. Preserve every local change.
NO lock, phase-note or registration-snapshot framework. Pause lifecycle activity. Existing target backup on rerun means stop with recovery instructions. Create the NEW checkout AT the target; leave the running clone in place. Windows clones locally with `--no-local`, sets origin to the official URL and fetches tags: no second network checkout, no shared objects, no move of the running script folder. Verify the tag SHA against origin before installation.
Write the new tag to `.cg-version` BEFORE the NEW installer (9023 defaults to latest: `e8cd4880:install.ps1:421-427`). Run only that absolute installer in a child process. Verify exact tag/HEAD/pin, clean status, wrappers and fresh-process cg-update resolution after reading HKCU PATH again. If checkout/install/verification fails, remove only this run's partial NEW target and restore the old folder. Report external installer writes as not automatically restored.
Print old/new versions, backup, next steps and rollback commands. `-InstallPath <target> -Rollback <backup>` moves the current target aside without deletion and restores the sibling backup to that explicit original path. Project conflicts do not block installation; affected projects require manual action, with no deletion. Same-path links change immediately; copies stay old. Run cg-link once per project separately. Keep the new pin; returning to latest is a separate user action.

## Project Reconciliation
9023 already removes exact old whole-root links without following/deleting targets, skips foreign roots, deletes checksum-matching stale copies, rejects selected modified/unowned projection collisions, and retires only five proven local native-plugin files (`e8cd4880:scripts/link.ps1:480-503`; `e8cd4880:scripts/cg_kilo_copy.py:170-208`; `e8cd4880:scripts/cg_project_projection.py:1046-1084`; `e8cd4880:scripts/cg_retire_native_evidence.py:23-36,160-225`). This covers owned F07+ copies, F17+ projection, F18+ mirrors and proven F24 plugin bytes, not every old file.
Gaps: F01-F06 marker-only copies have no checksum authority; F13+ POSIX unrecorded copies can overwrite; F11-F16/general native per-unit links lack a complete projection transition; F14+ copy receipts are not bridged to projection; stale modified ownership is dropped; incompatible journals can be overwritten; marker-based instructions and force-confirmed foreign links can replace user changes (`e8cd4880:scripts/link.sh:379-435`; `e8cd4880:scripts/link.ps1:543-553,619-634`; `e8cd4880:scripts/tests/test_rebuild_residue.py:203-288`).
Approved simplified Step-3 scope ONLY: (a) read-only `cg-link --check` with strict rejection of unknown options, and (b) remove marker/gitignore-only permission to replace differing bytes. All other old footprints are reported and preserved with manual guidance. No receipt bridge, per-unit link migration, journal/global-config repair, project snapshot framework or broader plugin retirement.
There is NO existing read-only cg-link option; unknown flags are ignored and may mutate (`e8cd4880:scripts/link.ps1:40-59,836-853`; `e8cd4880:scripts/link.sh:8-23,800-809`). Add explicit NEW `cg-link --check` with strict unknown-flag rejection before update/state creation. Reuse pure manifest resolver and plan/verify functions with an IN-MEMORY desired manifest for missing/stale projects, not the existing CLI that requires an active manifest. Disable bytecode; no update, recovery, retirement, copying, mirrors, global/ignore writes. List path, owner, current state, intended action and reason; nonzero for blocking conflicts.
Global `.config/kilo/kilo.jsonc` permission/plugin arrays and user settings are report-only without key-specific ownership. Existing writer risks remain reported, not new repair work in 9024. Preserve user `.gitignore` lines outside owned blocks. Manual relocation/edits, with backup, are required when ownership cannot be proved.

## Removed Content (Part C)
The adoption equality target is the APPROVED rebuild candidate including 9024 and selected small ports, not the literal e8cd4880 tree. No wholesale cherry-pick of old release merges.
| Old Content / Commit References | Disposition / Required Port |
|---|---|
| 9018 `9afd40ef`, 9019 `06804d24`: async controller, producer/snapshot contracts, Pages/ruleset repairs | Exclude controller-bound machinery; archive history. Reader improvements require a later separate decision. |
| 9020 `789193d7`: help `97289306`/`c12afce0`, docs browser `dffdc90a`, exclusion consumers `2be89445` | Defer simplified help without evidence binding to step 4; browser/registry improvements separately, not adoption blockers. |
| 9020 autopilot/plugin `f67717c1`/`5baf970a`, receipts/snapshots `5ee7a00e`, Routine publisher `6fa0acbb` | Exclude; keep current Reserve-only four-part publication. No restored runtime host/SDK qualification. |
| 9021 `fa6c33f3`: Routine-dev policy/help evidence rebinding | Exclude old branch/type policy and evidence binding; preserve tag. |
| Recovery `51bb64b4`/`9cd209c7` cleanup; `32abcc1e`/`52524b4b`/`28cc77ce` filesystem/process framework | Narrow config-ignore/retirement intent already present; only proven reconciliation fixes above. No custom supervisor or broad recovery framework. |
| Main-only `14e87863`, retained by PR190 merge `89b27304`: doc-rebuild draft-PR safeguard and charter/archive rule | PORT adapted workflow/tests before candidate freeze; do not restore direct bot pushes to main. Charter body/archive change needs approval. |
| Same `14e87863`: `presentation/vendor/reveal.js/LICENSE`, `LICENSE.marked.txt` | PORT exact vendor notices: rebuild retains vendored assets but lacks both licenses. |
| Main-only Pages sealing `1d06fc42`/`84cadb92`/`219a08b2`/`72fd2cb7` | Supersede explicitly, including Finalize/preview bindings/tests; regenerate indexes from selected tree. |

Latest users: F01-F07 can reset/pull then refresh current-project marked files; F08 adds optional generation; F09-F26 require generation in latest mode. F17-F21 can fail before checkout/link on the exact Kilo allowlist; F22-F25 retain a minimum-host gate; old POSIX tracked-wrapper dirt can interfere. F25-F26 refuse dirty latest rather than discard it. Attached custom branches continue their branch, not necessarily main. Pins remain old unless explicitly changed, and old cg-link still invokes its updater. Same-path linked projects change when main is pulled; copied artifacts can stay mixed. NO family should use its installed updater for this migration.
9024 MUST be published and announced before main moves. Require five working days of notice plus one Windows and one Mac user pilot. New main installer/link/update entry points should print fresh-clone migration guidance when reached by an old updater; this cannot protect an old process that resets files or fails BEFORE checkout. Publication/announcement, not that banner, is the safety gate.
Close draft PR191 as superseded only after the replacement dev PR is accepted, with approval; do not delete its head `chore/ignore-local-kilo-config`. Preserve remote archive `51bb64b4`, local frozen recovery `ef9d08c5ca3257dc4572e5a32d75eb711d7ad24c`, and verified saved bundle; archive is NOT the full recovery tip. Review conflicting PR181 separately and prevent an old Routine-policy merge. Keep historical tags/releases immutable.

## Requirements
| ID | Requirement | Source |
|---|---|---|
| R1 | Fresh-tag, version-independent same-path migration; preserve original clone/local changes | User Part B; kilo.independence |
| R2 | Explicit custom/multiple-install selection, safe registrations, restart and rollback | User Part B; migration critique |
| R3 | NEW read-only check and ownership-safe project reconciliation | User Part B; residue tests |
| R4 | About six representative tags per OS initially; expand after user survey only | Approved decision 2 |
| R5 | One-page guide, announcement outline, main guidance and pilot evidence | User Parts B/C |
| R6 | Separate approval for every PR creation, merge, release, announcement and closure | User scope; rebuild roadmap |
| R7 | Exact reviewed tree on dev then main; preserve history/checks/archive and necessary ports | User Part C; main-only review |
| R8 | Explicit official-release/Latest and stale-memory decisions, no implicit restoration | User Parts C/D |

## Phase 1: Build And Publish 9024
### 1. Implement Windows Migration
Current approved code session: `scripts/migrate-install.ps1`, under about 260 lines, plus isolated fixtures. Implement discovery, metadata, same-path replacement/recovery, verification and rollback only; no real installation.
- **Requirements**: R1, R2
- **Tests**: Single/custom/multiple installs, dirty backup, link/worktree refusal, install failure recovery, interrupted-rerun refusal and rollback; fake profiles/local bare remote, no real HKCU.
- **Step-1 resolution (2026-10-10)**: Changes a-e implemented in 245 lines; local gates passed, no fixture correction needed. Commits/normal push/every CI job will be recorded in `backups/9024-step1-finish/handoff.txt` outside the worktree; Step 2 is next only after Step 1 passes.
- **Clarified constraint**: "Never run old installed code" means: never run, source, or import the old Compound GPID clone's scripts, wrappers, installer, updater, or linker. It does NOT require defending against the user's own Git configuration, such as filters or hooks configured by the user. Use normal Git commands.
- **Changes a-e**: No old-clone status; normal Git without config defenses; UTF-8 native output with caller encoding restored; raw HKCU/process PATH and default sibling-backup discovery with exact resume/rollback commands; explicit rollback InstallPath and ASCII-safe version names without `backup` text.
- **Tests**: Existing assertions retained; new Unicode/HKCU interruption/explicit rollback/safe-name fixtures included. Focused Windows pytest: 25 passed/25 skipped/72 deselected. Prepare preflight vs `872c4644`: 2834 passed/153 skipped/2 deselected, three module checks passed. Full simple Pester at `E:\t\q16`: 3054 passed/0 failed/2 skipped; full/unfiltered, no files skipped.
### 2. Implement POSIX Migration
One bounded session, same contract; selected rc block ownership, spaces, dirty tracked wrappers and shell resolution. No generic migration service.
- **Requirements**: R1, R2
- **Tests**: macOS migration faults/rollback/custom-path tests; existing `test_install_sh.py` fixtures.
### 3. Fix NEW Link Reconciliation And Check
Separate bounded session: ONLY read-only check/strict option parser and removal of marker/gitignore-only overwrite permission. Other footprints are reported/preserved with manual guidance.
- **Requirements**: R3
- **Tests**: Extend `test_rebuild_residue.py`, copy/projection/retirement tests; no-write snapshots for missing/stale manifests and all conflict states.
### 4. Add Upgrade Matrix, Guide And Required Small Ports
Separate bounded sessions for matrix/guide, then doc-PR safeguard/license ports. Review source tag assignments, preservation assertions, guide and candidate tree before freeze.
- **Requirements**: R4, R5, R7
- **Tests**: Matrix below; artifact validator; focused workflow/port tests; CI-matched preflight and canonical full short-root Pester gate.
### 5. Review And Publish 9024
Approve creation of a small implementation PR into the rebuild branch, approve its merge separately after checks, then approve Reserve-only 9024 publication after FULL `tests.yml` dispatch on reviewed rebuild SHA. Do not mark a prerelease Latest.
- **Requirements**: R4, R5, R6
- **Tests**: All migration cells correctly classified; FULL CI current SHA; published tag/release/payload read-back and guide links.

## Phase 2: Announcement
### 6. Announce Before Adoption
Obtain approval of exact text/channel/audience, then publish; run one Windows and one macOS user pilot in separately approved sessions, one project at a time. Observe agreed notice window; no watchers or automatic user updates.
- **Requirements**: R5, R6
- **Tests**: Announcement/guide download commands reviewed; both pilot backups, wrapper resolution, check/apply/preserved-file outcomes confirmed.

## Phase 3: Dev Adoption
### 7. Supersede Reviewed Legacy Histories
Approve removal/port table, freeze reviewed rebuild/dev/main SHAs and prepare one branch with both `-s ours` ancestry merges. Approve dev PR creation, human review and all five checks; approve merge commit separately. Close PR191 as superseded after dev PR acceptance; keep branches.
- **Requirements**: R6, R7
- **Tests**: Tree equality, both ancestor tests, all required contexts on current PR head; no force/bypass/squash/rebase.

## Phase 4: Main Adoption
### 8. Promote Dev To Main
After notice/pilots/dev equality, approve dev-to-main PR creation; review main-only removals again; require all five fresh checks and resolved threads; approve merge commit separately. Stop on tip drift and re-review before another normal commit/PR.
- **Requirements**: R5, R6, R7
- **Tests**: Main ancestry and final tree equal approved rebuild; guidance preserved; archive/recovery refs unchanged.

## Phase 5: Official Release Decision
### 9. Decide Stable Version And Latest
After stable real use on adopted main, decide official v2.0.0 readiness (research/skill changes already included), publisher path and exact tag/payload. Separate publication approval, then explicit approval to mark that NON-prerelease GitHub Latest; verify releases/latest no longer resolves 9003. Review memory keys below; do not update them without approval.
- **Requirements**: R6, R8
- **Tests**: Stable release gates/payload/tag/release read-back; Latest API check; no implicit prerelease reclassification.

## Adoption Commands (Not Executed)
PowerShell examples; substitute approved SHA/PR/head values. Stop on any failure. Run in an approved execution session, never in this planning session. `-s ours` retains the WHOLE candidate tree; `-X ours` does not. Both GitHub PRs MUST use merge commits, not squash/rebase, so recorded ancestry survives. No ruleset change is needed.
```powershell
git fetch origin dev main
$rebuild = '<APPROVED_REBUILD_40_HEX_SHA>'
$dev = 'f4f4eceaa95c565b7c9c7224d9d276997584dd79'
$main = '89b2730495b783bf02c7716c4a1c653e015f2721'
if ((git rev-parse origin/dev) -ne $dev -or (git rev-parse origin/main) -ne $main) { throw 'Stop: review changed tips' }
git switch --create chore/adopt-rebuild $rebuild
git merge --strategy=ours --no-ff $dev -m "chore(adoption): supersede old dev tree"
git diff --exit-code $rebuild HEAD
git merge --strategy=ours --no-ff $main -m "chore(adoption): supersede reviewed main-only content"
git diff --exit-code $rebuild HEAD
git merge-base --is-ancestor $dev HEAD
git merge-base --is-ancestor $main HEAD
python -B scripts/cg_pr_preflight.py --phase committed --format text --default-branch main --run-native-target --base $dev
# Run canonical full Pester in the established short-root test environment.
git push --set-upstream origin HEAD:refs/heads/chore/adopt-rebuild
# Separate approval to create this PR, then to merge after review/five checks.
gh pr create --base dev --head chore/adopt-rebuild --title "chore(adoption): adopt the reviewed rebuild" --body "Reviewed removals and main-only ports; both histories recorded; merge commit only."
$devPr = '<APPROVED_DEV_PR_NUMBER>'
$adoptionHead = '<APPROVED_ADOPTION_HEAD_SHA>'
gh pr merge $devPr --merge --match-head-commit $adoptionHead
git fetch origin dev main
if ((git rev-parse origin/main) -ne $main) { throw 'Stop: main changed' }
git diff --exit-code $rebuild origin/dev
git merge-base --is-ancestor $main origin/dev
# Separate approval to create the main PR, then to merge after five new checks.
gh pr create --base main --head dev --title "chore(adoption): promote the reviewed rebuild to main" --body "Reviewed exact rebuild tree and recorded main ancestry; merge commit only."
$mainPr = '<APPROVED_MAIN_PR_NUMBER>'
$devHead = '<APPROVED_DEV_HEAD_SHA>'
gh pr merge $mainPr --merge --match-head-commit $devHead
git fetch origin main
git diff --exit-code $rebuild origin/main
```

## Testing Strategy
Initial matrix: `v1.0.4`, `v1.1.11`, `v1.2.0.9003`, `v1.2.0.9016`, `v1.2.0.9021`, `v1.2.0.9023` x Windows/macOS = about 12 cells. Expand only after user survey. Keep Part A as reference; disclose unsupported footprints rather than claim false passes.
Use disposable hosted accounts/VMs and isolated profiles/projects for later upgrade cells; pin old tag BEFORE old link with process-only `CG_SKIP_UPDATE=1`. Only that later isolated matrix may run historical installer/link code. Migration NEVER executes old code. Inject user sentinels, migrate from fresh NEW clone, then NEW check/link. Pinned/latest inputs both finish pinned to 9024; NEVER production PATH or real Kilo/plugin/SDK qualification.
Assert exact new HEAD/pin, clean wrappers, fresh-shell resolution, preserved tracked/untracked bytes and unrelated files. Windows fixtures cover selection/refusal, install failure restoration, interruption with existing backup, and rollback preserving current clone aside. Later check tests prove no writes; unresolved footprints/conflicts remain with manual guidance.
Bound: plain pytest, existing preflight and proven simple Pester runner only; one fixture at a time. No watchers, monitors, custom helpers, CI log parsers or evidence frameworks. Preserve FULL CI before publication. Step 1: preflight against current remote SHA, full Pester at `E:\t\q16`, tested/committed hash equality, normal push and every push-run job recorded. One bounded test-fixture fix iteration only; stop on product failures.
Five required checks, unchanged: `Pester on macos-14`, `Pester on windows-2022`, `Native target Python gate on macos-14`, `Native target Python gate on windows-2022`, `PR title follows Conventional Commits`. Rulesets 21338685 (dev), 16657602 (main); both require up-to-date PRs. FULL CI 37957517000 was green on 9023 but is NOT fresh PR-title/merge evidence.
Plan gate: `python -B scripts/render_artifact.py --root . --validate-only <Plan>`; existing CI-matched prepare/committed preflight with current remote push-before SHA (`872c4644d51dd70adce25cbcb67d5c3e4a2cf325` at session start). Docs-only selection must run zero native commands; this is not a full test pass.

## Documentation Checklist
- One-page upgrade guide: all-version warning; prerequisites; fresh official clone/tag verification; absolute new-script examples per OS; default/custom/multiple installs; backup/new pin/PATH checks; NEW check then link one project; preserved conflicts/private/global settings; explicit later unpin; rollback. Do not start with old cg-update or cg-link.
- Short announcement: who is affected (all tags, latest and pins); why old updater is unsafe; 9024/guide links and exact fresh-clone route; notice/main date; removed features; unchanged Kilo independence; preservation/rollback and pilot outcomes. Approval before sending, not a draft presented as sent.
- Rollback: stop lifecycle activity; use the NEW script's explicit rollback option to move current clone aside and backup back to its EXACT path, keeping both. No registration/project snapshots or automatic external restoration. Review installer/profile changes manually; open a new terminal. Same-path links return to old content. No old installer/update/link, blanket unlink or Git reset.

## Risks & Mitigations
- Clone swap changes every direct link immediately; use maintenance window, backups and one-project reconciliation. Unknown install identities/worktrees stay report-only. A successful install is not host/project readiness.
- Existing global/profile writers can change user values; disclose their writes and manual review. No snapshot framework in migration. Read-only checks run in memory without import caches.
- Ours merge records intentional exclusions, not feature integration; freeze SHAs, review every removal and required port, compare whole trees after BOTH merges and promotions. Tip drift stops adoption.
- Windows-only historical Mac cells and fake hosts limit evidence; disclose unsupported/fixture status and require separate current Windows/macOS user pilots. Notice cannot guarantee every dormant latest user reads it.

## Approved decisions
1. 9024 = migration tool, small upgrade matrix, guide and required small ports. cg-help moves to a later release.
2. About six tags per OS initially: v1.0.4, v1.1.11, v1.2.0.9003, v1.2.0.9016, v1.2.0.9021, v1.2.0.9023. Expand only after survey; retain the 26-family reference.
3. Auto-detect PATH cg-update/cg-link and defaults; multiple installs require InstallPath. Refuse links/junctions, worktrees and source/target overlap.
4. Simple steps only: NO lock, phase-note or registration-snapshot framework. Existing backup on rerun means stop with instructions.
5. Installation proceeds despite project conflicts; unresolved projects get `manual action required`. Nothing is deleted.
6. Pin to the new tag; returning to latest is a separate user action.
7. Five working days of notice before main moves, plus one Windows and one Mac user pilot.
8. Port both vendor licenses and doc-rebuild draft-PR safeguard from 14e87863 before freeze. Charter text needs separate review.
9. Adoption uses `-s ours` merges and merge-commit PRs only; no force-push.
10. Close PR191 as superseded after dev PR acceptance; keep branches.
11. v2.0.0 and GitHub Latest later; verify stable publishing first.
12. Correct outdated saved decisions only after the relevant steps are done.

## Decisions needed
1. Charter body/archive port: recommend separate review before text changes; license/workflow approval does not approve charter text.
2. PR181 disposition: recommend separate review/closure if obsolete; preserve branch/history.
3. Unknown old version: recommend allow only verified standalone clone with install.ps1/cg wrappers; print unknown metadata, never execute old code.
4. External installer writes after failure/rollback: recommend manual review with warning; folder restoration does not undo HKCU/profile writes. No snapshot framework.
5. Publication, announcement and adoption PR operations: recommend separate execution approval at their steps; none is authorized by this Step-1 session.

## Saved Decisions For Review
- `release.controller_reuse`, `release.controller_cutover_strategy`, `release.controller_cutover`, `release.controller_status`, controller architecture/bridge/sandbox records: obsolete as adoption prerequisites; retain only historical context. No third publisher or controller restoration.
- `pr_target_dev_only` PR191-main exception: replace with the approved dev-then-main adoption sequence; not general permission for unrelated main PRs. `main_promotion_scope` saying all old dev content is ready must not imply wholesale restoration.
- `release.9022_reclone_migration`, `release.9022_consumer_cleanup_scope`: fresh-clone principle remains; replace version-limited manual procedure with 9024 universal tool and precise ownership-safe/manual boundaries.
- `release.routine_four_part_path`, `release.legacy_operations`, `release.publication_order` Finalize/build implications: reconcile with 9023 Reserve-only four-part path. `release.branch_origins` restrictions need separate review against newer branch/type-separation corrections, not silent revival.
- `rebuild.roadmap` step-4 9024 allocation and `rebuild.status`: update after approved milestones, not now. Keep `kilo.independence`, immutable tags, research/skill v2 scope and no-force constraints.

## Out of Scope
Only Plan recording and Phase 1 Step 1 Windows migration/tests/commits/normal push are approved now. No POSIX implementation, real installation, real cg-link/cg-update, real Kilo launch, PR, merge, dev/main change, tag/release, ruleset edit, force push or memory edit. Later execution needs separate approval. No autopilot/plugin/controller, receipts, sealing, supervisor, watcher, monitor, helper/evidence framework or wholesale history port.

## Completion Contract
### Outcome
Full implementation ends with verified universal migration/guide, small Windows/macOS matrix/pilots, reviewed rebuild tree on dev then main, preserved histories/user files and official-release decision. Current Step-1 handoff supplies decisions, Windows behavior, test/CI results and Step 2 as exact next action, not claims of later work.
### Verification Surface
| ID | Evidence Required | Command/Artifact | Required |
|---|---|---|---|
| V1 | Valid Plan and current-SHA CI-matched preflight | Artifact validator and prepare/committed preflight | yes |
| V2 | 9024 migration/preservation/fault coverage and honest legacy cells | Existing CI upgrade matrix, focused tests, Windows/macOS pilots | yes |
| V3 | Reviewed exact tree, ancestry and five checks on each PR | `git diff --exit-code`, `git merge-base --is-ancestor`, PR checks | yes |
| V4 | Separate human approvals and publication/announcement/Latest decisions | Approved session handoffs and tag/release/Latest read-back | yes |
### Constraints
| ID | Constraint | Check |
|---|---|---|
| C1 | Never run old installed code in migration; no Kilo dependency | Fresh absolute scripts, inert Git, isolated old-code CI only |
| C2 | Never delete/replace unowned or modified content; retain old clone | Ownership/hash/identity assertions and rollback tests |
| C3 | No force, bypass, history loss, implicit retired-feature restoration | Reviewed ancestry/tree/checks/removed table |
| C4 | Windows Step 1 only now; later approval gates; bounded sessions | Commit path/hash audit, unchanged dev/main, explicit approvals |
### Boundaries
Only the two OS scripts, minimal existing ownership/parser fixes, bounded CI/guide and explicitly selected small ports belong to 9024. Global conflicts/manual repairs and official stable publisher readiness are not hidden automatic migrations.
### Iteration Policy
One bounded session per deliverable; one focused verification/fix pass, then stop and report if still failing or scope expands. No polling/retry services. Use CI-matched preflight before each push and FULL CI before publication.
### Blocked-Stop Conditions
Stop for ambiguous identity/PATH, source-target overlap, unsafe write/unknown ownership, foreign journal, failed preservation/rollback/no-write assertion, failed tests/checks, unreviewed remote drift, missing required notices/ports/pilots, or absent consequential approval. Preserve state and record the next decision; never bypass a gate.
