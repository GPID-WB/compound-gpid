# Handoff: where the 2.0 build stands

Written 2026-11-24 for whoever continues the work, in any coding agent. Update this file when the state changes; it is the first thing to read.

## Read in this order

1. This file.
2. The plan: `.cg-docs/plans/2026-11-24-compound-gpid-v2.md`. Its "Amendments after approval" section overrides the body where they differ.
3. `skills/cg/GLOSSARY.md`. Every new text uses these words.
4. `skills/cg/principles/README.md`, then the principle files you need.
5. The decision records in `docs/adr/` (0001 hosts, 0002 sources, 0003 packs, 0004 no base host) and `SCOPE.md`.

Issues: tracking issue #256 in `GPID-WB/compound-gpid`; tasks #211 to #255 and #257, label `v2`. Branch: `v2`.

## What exists

| Thing | Where | State |
|---|---|---|
| Approved plan with amendments | `.cg-docs/plans/` | current |
| Twelve principles | `skills/cg/principles/` | P3, P4, P11 accepted; nine are drafts awaiting the maintainer |
| Plugin glossary and its check | `skills/cg/GLOSSARY.md`, `tools/check_glossary.py` | in use |
| Host record | `docs/adr/0001-host-matrix.md` | Claude Code and Codex tested on macOS; Kilo, Copilot, Windows open |
| Host test kit | `spike/host-matrix/` | the maintainer runs `run_cli_checks.sh`; results are git-ignored |
| Sources, notices, ledger | `docs/adr/0002-sources.md`, `THIRD_PARTY_NOTICES`, `docs/adoption-ledger.md` | current |
| Pack contract | `docs/adr/0003-packs.md` | proposed; layout to be tested in tasks 1.1 and 1.5 |
| Scope policy and budgets | `SCOPE.md`, `.out-of-scope/` | written; the budget check itself is task 1.6 |
| Triage of v1 issues | `docs/v2/v1-issue-triage.md` | done as a table; no issue touched |
| Evidence workbench | repository `GPID-WB/research-evidence` | moved with history, tests pass; still also in this repository until task 1.1 |
| Issue script | `tools/admin/create_v2_issues.py` | rerun to add tasks or refresh the tracking issue |

Nothing of version 1 has been removed from `v2` yet. The version 1 tree is still there beside the new files.

## Next tasks, in order

1. **0.2 (#212)** Done. Version 1 is frozen on branch `v1`, cut from the tip of `dev` (which holds everything in `main` plus one unreleased help feature) with a notice in its README. `main` and the `v1.3.0` release are untouched and keep serving current installs. No tag was added, because the version 1 updater lists every tag that starts with `v`. Decided by the maintainer on 2026-11-24: the unreleased help feature is not released to version 1 users; pull requests #181 and #191 are old and are to be ignored; `dev` is kept, for version 2 development and nothing of version 1.
   **How `dev` is used:** until 2.0 is released, work happens on `v2` and `dev` is left where it is. Moving `dev` earlier would start the version 1 workflows on it. At release `v2` merges into `main`, `dev` is brought up to `main`, and from then on changes go `dev` to `main` as before. One name per branch, so no `dev-v2`.
2. **1.1 (#217)** Hub layout: move `skills/cg/` to `packs/core/cg/`, add manifests and the pack index, remove the version 1 packaging from `v2`, remove `research_evidence/`.
3. **1.2 (#218)** `cg.py`: `doctor`, `status`, `new`, `packs`, with tests.
4. **1.6 (#222)** CI: skill linter, pack validator, budget check, glossary check, docs drift check.
5. **1.3 (#219)** The guide, the `setup` and `quick` playbooks, the pointer block.
6. **1.4 (#220)**, **1.5 (#221)**, then the gate **1.7 (#223)**.

Waiting on the maintainer: review of the nine draft principles (#215) and of the pack contract (#216); the Kilo rerun and the Copilot checklist (#211); a Windows machine.

## Working rules agreed with the maintainer

- **Commit often**, small commits, conventional messages, on `v2`. Unfinished work is fine. Push `v2` as you go. Ask before touching `main`, tags or other branches.
- **Run checks yourself.** Hand the maintainer only what needs their decision or cannot be done from the session.
- **Everything here is public.** Write governance text as general rules. Keep any organization's internal policy detail, tool approvals and audit findings out of files and commit messages.
- **Shared language is strict.** Run `python3 tools/check_glossary.py skills docs/adr docs/v2 docs/adoption-ledger.md SCOPE.md .out-of-scope spike` before each commit and read its exit code directly; a pipe once hid a failure.
- **Read a source file in full before adapting it**, then cite it in `derived-from` and update the ledger row.
- **Analysts first.** Examples are analytical; rigor of the calculation comes before anything else.
- **No host is the base.** Anything one host needs is an optional adapter.
- **Do not switch branches in this checkout.** The repository sits in a OneDrive folder. On 2026-11-24 a switch to `v1` and back made the sync client delete 14 tracked files and leave four duplicate folders ending in " 2". Nothing was lost, because everything was pushed. To work on another branch, use `git worktree add` in a folder outside OneDrive, or push a commit to the other branch without checking it out. After any odd result, run `git status` before continuing.
- **A build session may be refused permission to start another coding agent.** Do not work around it; use the host script, which the maintainer runs.

## Which model

A judgement to test at the first gate: the most capable model for principles, playbooks, verifiers and the pack contract, where wording decides behavior; a cheaper strong model for layout, tooling, CI and pack ports, which have tests. Whichever builds, the other reviews.

## Known loose ends

- The plan's body predates the glossary and uses some avoided words. The amendments and the glossary govern.
- Issue texts say "Spec verifier"; it is now the `contract` verifier. Issue texts say ten principles; there are twelve.
- `scripts/secure_fs.py` exists in both this repository and `research-evidence`.
- The `v2` history was rewritten once on 2026-11-24 to remove internal wording. Commit hashes quoted before that date may no longer exist.
