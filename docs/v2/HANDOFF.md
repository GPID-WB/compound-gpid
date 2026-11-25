# Handoff: where the 2.0 build stands

Written 2026-11-24 for whoever continues the work, in any coding agent. Last updated 2026-11-24 by the Opus 5.5 session that built tasks 1.1, 1.2, 1.6, 1.4 and 1.5. Update this file when the state changes; it is the first thing to read.

## Read in this order

1. This file.
2. The plan: `.cg-docs/plans/2026-11-24-compound-gpid-v2.md`. Its "Amendments after approval" section overrides the body where they differ.
3. `packs/core/cg/GLOSSARY.md`. Every new text uses these words.
4. `packs/core/cg/principles/README.md`, then the principle files you need.
5. The decision records in `docs/adr/` (0001 hosts, 0002 sources, 0003 packs, 0004 no base host) and `SCOPE.md`.

Issues: tracking issue #256 in `GPID-WB/compound-gpid`; tasks #211 to #255 and #257, label `v2`. Branch: `v2`.

## What exists

| Thing | Where | State |
|---|---|---|
| Approved plan with amendments | `.cg-docs/plans/` | current |
| Twelve principles | `packs/core/cg/principles/` | all accepted on 2026-11-24 as the working version; they are meant to be revised (see "How a principle changes" in the index) |
| Plugin glossary and its check | `packs/core/cg/GLOSSARY.md`, `tools/check_glossary.py` | in use |
| Host record | `docs/adr/0001-host-matrix.md` | all four hosts tested on macOS (Copilot and Kilo's panel in the editor); Copilot honors the flag and loads `AGENTS.md`, `CLAUDE.md` and `copilot-instructions.md` together; the `@AGENTS.md` import works; Codex and Kilo ignore `disable-model-invocation`; Claude Code reads only `~/.claude/skills`, Codex only `~/.agents/skills`, Kilo both; Windows open |
| Host test kit | `spike/host-matrix/` | the maintainer runs `run_cli_checks.py` (macOS and Windows); raw results are git-ignored, `--report` writes a copy that can be committed; `WINDOWS.md` is a handoff for an agent on Windows |
| Sources, notices, ledger | `docs/adr/0002-sources.md`, `THIRD_PARTY_NOTICES`, `docs/adoption-ledger.md` | current |
| Pack contract | `docs/adr/0003-packs.md` | accepted on 2026-11-24 as the working contract; free to change before 2.0 by amending the record; the layout held in tasks 1.1 and 1.5, with two open points under "Known loose ends" |
| Scope policy and budgets | `SCOPE.md`, `.out-of-scope/` | in force; checked in CI by `tools/check_budgets.py` and `tools/lint_skills.py` |
| Triage of v1 issues | `docs/v2/v1-issue-triage.md` | done as a table; no issue touched |
| Evidence workbench | repository `GPID-WB/research-evidence` | moved with history, tests pass; removed from this repository in task 1.1 |
| Issue script | `tools/admin/create_v2_issues.py` | rerun to add tasks or refresh the tracking issue |
| Hub layout and manifests | `packs/`, `.claude-plugin/marketplace.json` (the pack index), `plugin.json`, `packs/*/.claude-plugin/plugin.json` | task 1.1; `claude plugin validate --strict` passes; a marketplace install has not been tried in any host |
| Version sync | `tools/sync_version.py` | each `pack.json` is its pack's version source; core's version is the hub's (`2.0.0.9000`); the root `plugin.json` `repository` is the hub URL's source; `docs/install-block.md` is the one other place it appears |
| `cg.py` | `packs/core/cg/scripts/cg.py` | task 1.2: `doctor`, `status`, `new`, `packs`; standard library, Python 3.9 or later |
| Checks and CI | `tools/lint_skills.py`, `tools/validate_pack.py`, `tools/check_budgets.py`, `.github/workflows/v2.yml` | task 1.6; CI runs the checks, and pytest on Linux, macOS and Windows with Python 3.9 and 3.13 |
| Installer | `install.py`, `docs/install-block.md` | task 1.4; installs into `~/.agents/skills` with links from `~/.claude/skills`; owns only what `~/.cg/installed.json` lists |
| `lang-r` pack | `packs/lang-r/` | task 1.5: the eight v1 R skills, renamed `r-*`; lead skill `r-shared` |
| Tests | `tests/core/`, `tests/hub/` | 76 tests; run `python3 -m pytest -q` (or `uvx pytest -q`) |

The version 1 tree is gone from `v2`: the generated host trees, `.github`, `adapters/`, `bin/`, `scripts/`, the Pester tests, the installers and release machinery, `research_evidence/` and `c-research/`. All of it is unchanged on branch `v1`, and later ports read from there (`git show v1:<path>` or `git archive v1 <path>`). Kept: `.cg-docs/`, `docs/` (its version 1 pages are for task 7.5), `spike/`.

## Next tasks, in order

1. **0.2 (#212)** Done. Version 1 is frozen on branch `v1`, cut from the tip of `dev` (which holds everything in `main` plus one unreleased help feature) with a notice in its README. `main` and the `v1.3.0` release are untouched and keep serving current installs. No tag was added, because the version 1 updater lists every tag that starts with `v`. Decided by the maintainer on 2026-11-24: the unreleased help feature is not released to version 1 users; pull requests #181 and #191 were old and are closed (their branches remain); `dev` is kept, for version 2 development and nothing of version 1.
   **How `dev` is used:** until 2.0 is released, work happens on `v2` and `dev` is left where it is. Moving `dev` earlier would start the version 1 workflows on it. At release `v2` merges into `main`, `dev` is brought up to `main`, and from then on changes go `dev` to `main` as before. One name per branch, so no `dev-v2`.
2. **1.1 (#217)** Built. Hub layout, manifests, pack index, version sync; version 1 removed.
3. **1.2 (#218)** Built. `cg.py` `doctor`, `status`, `new`, `packs`.
4. **1.6 (#222)** Built. Linter, validator, budgets, glossary check, one workflow. The docs drift check is task 7.5 (#257).
5. **1.4 (#220)** Built. `install.py` and `docs/install-block.md`. Its "Done when" is met except a real OneDrive folder on a World Bank Windows machine.
6. **1.5 (#221)** Built. `lang-r`.
7. **Next: 1.3 (#219)**, for Fable 5.2. The guide, the `setup` and `quick` playbooks, the pointer block. It replaces the placeholders listed below.
8. **Review by Fable 5.2** of tasks 1.1, 1.2, 1.6, 1.4 and 1.5. Each issue has a comment saying what was done, what was not, and what was decided along the way. Each "Observed" point there waits on a decision.
9. The gate **1.7 (#223)**, with the maintainer at the keyboard.

No task in this set failed its "Done when" twice. CI failed once each in tasks 1.6 and 1.4, both on Windows and both in tests, and was fixed in the next commit.

Windows: the command-line host run is merged (#258) and recorded in ADR 0001. It matched macOS except that `python3` does not exist (the agents used `python`) and a directory junction worked as the link; `install.py` and `cg.py` were changed for both. Still waiting on the maintainer: a run with the project inside OneDrive (run B of `spike/host-matrix/WINDOWS.md`), the editor panels on Windows, and `install.py --packs core,lang-r` from a clone in a OneDrive folder whose name has spaces.

For task 1.3: no playbook may call `python3`. Start `cg.py` with the interpreter recorded in `~/.cg/launcher.json` (ADR 0001, design change 8).

## Working rules agreed with the maintainer

- **Commit often**, small commits, conventional messages, on `v2`. Unfinished work is fine. Push `v2` as you go. Ask before touching `main`, tags or other branches.
- **Run checks yourself.** Hand the maintainer only what needs their decision or cannot be done from the session.
- **Everything here is public.** Write governance text as general rules. Keep any organization's internal policy detail, tool approvals and audit findings out of files and commit messages.
- **Shared language is strict.** Run `python3 tools/check_glossary.py packs docs/adr docs/v2 docs/adoption-ledger.md SCOPE.md .out-of-scope spike README.md CONTRIBUTING.md AGENTS.md docs/install-block.md` (and the other checks in `CONTRIBUTING.md`) before each commit and read its exit code directly; a pipe once hid a failure.
- **Read a source file in full before adapting it**, then cite it in `derived-from` and update the ledger row.
- **Analysts first.** Examples are analytical; rigor of the calculation comes before anything else.
- **No host is the base.** Anything one host needs is an optional adapter.
- **Do not switch branches in this checkout.** The repository sits in a OneDrive folder. On 2026-11-24 a switch to `v1` and back made the sync client delete 14 tracked files and leave four duplicate folders ending in " 2". Nothing was lost, because everything was pushed. To work on another branch, use `git worktree add` in a folder outside OneDrive, or push a commit to the other branch without checking it out. After any odd result, run `git status` before continuing.
- **A build session may be refused permission to start another coding agent.** Do not work around it; use the host script, which the maintainer runs.

## Which model builds which task

A judgement to test at the first gate. Text that decides how an agent behaves (principles, the guide, playbooks, verifiers, lenses, the pointer block, the glossary) is written by Fable 5.2. Work that has tests to hold it (layout, tooling, the installer, CI, pack ports) is built by Opus 5.5. Whichever builds, the other reviews. Each issue carries a "Suggested model" line; this table is the same split for milestone 1.

| Task | Built by | Reviewed by |
|---|---|---|
| 1.1 hub layout (#217) | Opus 5.5 | Fable 5.2 |
| 1.2 `cg.py` (#218) | Opus 5.5 | Fable 5.2 |
| 1.6 CI (#222) | Opus 5.5 | Fable 5.2 |
| 1.4 `install.py` (#220) | Opus 5.5 | Fable 5.2 |
| 1.5 `lang-r` pack (#221) | Opus 5.5 | Fable 5.2 |
| 1.3 guide, playbooks, pointer block (#219) | Fable 5.2 | Opus 5.5 |
| 1.7 gate (#223) | the maintainer, with either | |
| All of milestone 2 | Fable 5.2 | Opus 5.5 |

Rules for a build session:

- **Build only the tasks assigned to the model you are.** When the next task belongs to the other model, stop, update this file, and say so.
- **Do not write the other model's text to get unblocked.** If a tooling task needs a file whose wording decides behavior (a `SKILL.md` body, a playbook, a lens), add the smallest placeholder that lets the tests run, mark it `PLACEHOLDER: written in task <n>`, and list it under "Known loose ends".
- **Principles, the glossary and the pack contract can change, but a tooling session does not change their meaning alone.** If a build task shows one of them is wrong, write what was observed in the issue and stop on that point. For the pack contract before 2.0, the fix may go in the same pull request once the maintainer agrees (ADR 0003, "How this contract changes").
- **A task that fails its own "Done when" check twice** moves to the other model. Say so in the issue.
- **Removing the version 1 tree (task 1.1) deletes thousands of files inside a OneDrive folder.** Delete in a few commits, push each, and run `git status` after each one before continuing.

## Known loose ends

Placeholders (each file says `PLACEHOLDER: written in task <n>`):

- `packs/core/cg/SKILL.md`: the guide; task 1.3. It has `disable-model-invocation: true` and says it does nothing.
- `AGENTS.md`: the pointer block for this repository; task 1.3.
- `packs/core/cg/templates/artifact.md`: the template `cg.py new` fills; task 2.1.
- In `cg.py`: `PHASE_PLAYBOOK` (no config means `setup`, config means `quick`; task 2.14), `ARTIFACT_FOLDERS`, `OPEN_STATUSES` and `WAITING_STATUSES` (task 2.1). The playbooks it names (`playbooks/setup.md`, `playbooks/quick.md`) do not exist yet.

Decisions taken in tasks 1.1 to 1.6 that a reviewer should check:

- `.cg-docs/config.json` keys read by `cg.py status`: `packs` and `requires-core`. Setup (1.3) writes this file.
- Per-machine state is in `~/.cg/`: `launcher.json` (written by `cg.py doctor`) and `installed.json` (written by `install.py`).
- Install profiles: `economist` = core, lang-r, lang-stata, research, writing-wb; `developer` = core, lang-r, lang-python.
- The marketplace is named `compound` and its plugins are named after the packs.

Open points found while building (each is in its issue, and none was changed):

- Claude Code names a plugin's skills `<plugin>:<skill>`, so a marketplace install gives the guide the name `/core:cg`; `install.py` gives `/cg` (#217).
- ADR 0003 looks for packs beside the `cg` skill. A Claude Code marketplace install keeps each plugin in its own folder, so `cg.py packs` would see only core there (#217).
- `r-syntax`, the R dialect setting, has no place in a v2 project; v1 kept it in `compound-gpid.local.md` (#221).
- Decided by the maintainer on 2026-11-24: the glossary stays strict. `suite` and `manually` remain unconditional, and pack content is reworded to pass, as in the `lang-r` port (#221).
- Hub tooling (`tools/`, `install.py`) has no cap in `SCOPE.md`; the budget check reports it (#222). Proposed: 2,000 lines.
- `LICENSE` (MIT) added on 2026-11-24, holder as in `GPID-WB/global-poverty-map`.
- The documentation pages in `docs/` other than `adr/`, `v2/` and `install-block.md` still describe version 1 (task 7.5).

- The plan's body predates the glossary and uses some avoided words. The amendments and the glossary govern.
- Issue texts say "Spec verifier"; it is now the `contract` verifier. Issue texts say ten principles; there are twelve.
- The `v2` history was rewritten once on 2026-11-24 to remove internal wording. Commit hashes quoted before that date may no longer exist.
