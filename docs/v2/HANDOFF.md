# Handoff: where the 2.0 build stands

Written 2026-11-24 for whoever continues the work, in any coding agent. Last updated 2026-11-24 by the Fable 5.2 session that reviewed tasks 1.1, 1.2, 1.6, 1.4 and 1.5 and built task 1.3. Update this file when the state changes; it is the first thing to read.

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
| The guide | `packs/core/cg/SKILL.md` | task 1.3: reads `~/.cg/launcher.json`, runs `cg.py status`, follows the playbook status names; starts nothing when the human did not type `/cg` |
| Playbooks | `packs/core/cg/playbooks/setup.md`, `quick.md` | task 1.3; each opens with what the agent owns and ends with a `Reply:` contract |
| Pointer block and templates | `packs/core/cg/templates/` (`pointer-block.md`, `verification.md`, `work-report.md`) | task 1.3; the block is nine lines, written into `AGENTS.md` only, and this repository's `AGENTS.md` holds it |
| Codex adapter | `packs/core/cg/agents/openai.yaml` | task 1.3; optional (ADR 0004); not yet run in Codex |
| Tests | `tests/core/`, `tests/hub/` | 86 tests, and one that runs only on Windows; run `python3 -m pytest -q` (or `uvx pytest -q`) |

The version 1 tree is gone from `v2`: the generated host trees, `.github`, `adapters/`, `bin/`, `scripts/`, the Pester tests, the installers and release machinery, `research_evidence/` and `c-research/`. All of it is unchanged on branch `v1`, and later ports read from there (`git show v1:<path>` or `git archive v1 <path>`). Kept: `.cg-docs/`, `docs/` (its version 1 pages are for task 7.5), `spike/`.

## Next tasks, in order

1. **0.2 (#212)** Done. Version 1 is frozen on branch `v1`, cut from the tip of `dev` (which holds everything in `main` plus one unreleased help feature) with a notice in its README. `main` and the `v1.3.0` release are untouched and keep serving current installs. No tag was added, because the version 1 updater lists every tag that starts with `v`. Decided by the maintainer on 2026-11-24: the unreleased help feature is not released to version 1 users; pull requests #181 and #191 were old and are closed (their branches remain); `dev` is kept, for version 2 development and nothing of version 1.
   **How `dev` is used:** until 2.0 is released, work happens on `v2` and `dev` is left where it is. Moving `dev` earlier would start the version 1 workflows on it. At release `v2` merges into `main`, `dev` is brought up to `main`, and from then on changes go `dev` to `main` as before. One name per branch, so no `dev-v2`.
2. **1.1 (#217)** Built. Hub layout, manifests, pack index, version sync; version 1 removed.
3. **1.2 (#218)** Built. `cg.py` `doctor`, `status`, `new`, `packs`.
4. **1.6 (#222)** Built. Linter, validator, budgets, glossary check, one workflow. The docs drift check is task 7.5 (#257).
5. **1.4 (#220)** Built. `install.py` and `docs/install-block.md`. Its "Done when" is met except a real OneDrive folder on a World Bank Windows machine.
6. **1.5 (#221)** Built. `lang-r`.
7. **1.3 (#219)** Built by Fable 5.2. The guide, the `setup` and `quick` playbooks, the pointer block. What was done and not done is in the issue. No host has run it yet; that is the gate.
8. **Review by Fable 5.2** of tasks 1.1, 1.2, 1.6, 1.4 and 1.5: done. Each issue has a review comment with findings, most severe first, each with proof. No finding blocked task 1.3. The findings to fix are listed under "Findings from the review" below.
9. **Next, for Opus 5.5:** review task 1.3 (#219), and fix the review findings marked "before the gate".
10. The gate **1.7 (#223)**, with the maintainer at the keyboard. It can be run now: `install.py --packs core,lang-r --dry-run` against the maintainer's real home folder on 2026-11-24 listed nine installs and no refusal. See "Before the gate" below.

No task in this set failed its "Done when" twice. CI failed once each in tasks 1.6 and 1.4, both on Windows and both in tests, and was fixed in the next commit.

Windows: the command-line host run is merged (#258) and recorded in ADR 0001. It matched macOS except that `python3` does not exist (the agents used `python`) and a directory junction worked as the link; `install.py` and `cg.py` were changed for both. Still waiting on the maintainer: a run with the project inside OneDrive (run B of `spike/host-matrix/WINDOWS.md`), the editor panels on Windows, and `install.py --packs core,lang-r` from a clone in a OneDrive folder whose name has spaces.

For every later playbook: no file of the core pack names `python3` (a test holds this). Start `cg.py` with the interpreter recorded in `~/.cg/launcher.json`, by absolute path, as section 1 of the guide says (ADR 0001, design change 8).

### Before the gate

- Remove the host test skills first (`cg-spike-auto`, `cg-spike-hello`): they sit in both user skill folders, and `cg.py doctor` reports any folder named `cg-*` as a failure (#218, finding 4).
- The toy project will be a new repository. Make one commit before the first `/cg`, or expect `git: not a repository` in status (#218, finding 3).
- Run `install.py` with the machine's own Python, not one from a project's virtual environment (#218, finding 1).
- In Codex, check the policy file: an ordinary request in plain words must not load `cg`, and `$cg` must still run (ADR 0001, "Still open").
- In one host, ask for a plain piece of R code without `/cg` and note whether `r-shared` is loaded (#221, finding 1).

### Findings from the review

Each is in its issue with proof. None was fixed; the code is Opus 5.5's.

| Issue | Finding | Priority | When |
|---|---|---|---|
| #220 | A first install that fails part-way cannot be run again, and leaves a half-copied folder where hosts read | P1 | before the gate |
| #220 | `--update` deletes a real folder that replaced its link in `~/.claude/skills` | P1 | before the gate |
| #218 | The launcher records a virtual environment's Python, which later disappears | P1 | before the gate |
| #218 | `status` from a subfolder reports a new project | P2 | before the pilot |
| #218 | A repository with no commit is "not a repository" | P2 | before the gate, or commit first |
| #218 | doctor fails on any `cg-*` folder; `install.py` leaves the same folder alone | P2 | before the gate, or remove the test skills first |
| #218 | The add command is not runnable as printed in PowerShell (inferred) | P2 | before the Windows run |
| #220 | A Claude Code plugin copy is seen only for a pack's lead skill | P2 | before the pilot |
| #222 | The linter passes three frontmatter shapes a strict parser rejects or cuts, and mishandles folded descriptions | P2 | before packs from other teams |
| #221 | `r-shared` holds the rule for which R skills to load, and its description does not say so | P2 | wording for Fable 5.2; check at the gate |
| #221 | Two references to version 1's `/cg-fixbug` remain in `r-testing` | P2 | any time |
| #217 | `2.0.0.9000` sorts after `2.0.0`, so the release stops every project set up during the build | P2 | maintainer's decision, before the pilot |
| all five | P3 findings | P3 | with the next edit of each file |

## Working rules agreed with the maintainer

- **Commit often**, small commits, conventional messages, on `v2`. Unfinished work is fine. Push `v2` as you go. Ask before touching `main`, tags or other branches.
- **Run checks yourself.** Hand the maintainer only what needs their decision or cannot be done from the session.
- **Everything here is public.** Write governance text as general rules. Keep any organization's internal policy detail, tool approvals and audit findings out of files and commit messages.
- **Shared language is strict.** Run `python3 tools/check_glossary.py` (and the other checks in `CONTRIBUTING.md`) before each commit and read its exit code directly; a pipe once hid a failure.
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

- `packs/core/cg/templates/artifact.md`: the template `cg.py new` fills for every type except a work report; task 2.1.
- `packs/core/cg/playbooks/quick.md`: the risk table in step 2 stands in for `cg.py tier` (task 2.1), and step 5 for `cg.py evidence` (task 2.4). Until then the agent answers the table and fills the work report itself.
- In `cg.py`: `PHASE_PLAYBOOK` (no config means `setup`, config means `quick`; task 2.14), `ARTIFACT_FOLDERS`, `OPEN_STATUSES` and `WAITING_STATUSES` (task 2.1).

Decisions taken in task 1.3 that a reviewer should check (each is also in #219):

- The guide keeps `disable-model-invocation: true`, and its description says it is only for a human who types `/cg`. Where a host ignores the flag, section 2 of the guide makes a model-started guide report the state and stop.
- Setup writes three more keys into `.cg-docs/config.json` than `cg.py status` reads: `classification-levels`, `approved-tools` and `contacts`, which P12 asks setup to record. It writes the verification profile P4 asks for as `.cg-docs/verification.md`. Nothing reads these four yet.
- Setup reads each installed pack's lead skill for the settings it takes, so core names no pack's setting. It finds the lead skill's folder with `cg.py packs --json`.
- A quick work report starts as `status: in-progress` and ends as `completed`. Both are in the lists `cg.py` already has.
- Evidence digests in quick work come from `git hash-object`, which every supported machine has.
- In an R package, setup adds `.cg-docs`, `AGENTS.md` and `CLAUDE.md` to `.Rbuildignore`.
- The glossary gained one term, pointer block.
- Quick work is closed to anything that can move a number someone will read: that is line 1 of its risk table and a hard stop.

Decisions taken in tasks 1.1 to 1.6 that a reviewer should check:

- `.cg-docs/config.json` keys read by `cg.py status`: `packs`, `requires-core` and `settings`. Setup (1.3) writes this file.
- Per-machine state is in `~/.cg/`: `launcher.json` (written by `cg.py doctor`) and `installed.json` (written by `install.py`).
- Install profiles: `economist` = core, lang-r, lang-stata, research, writing-wb; `developer` = core, lang-r, lang-python.
- The marketplace is named `compound` and its plugins are named after the packs.

Open points found while building (each is in its issue, and none was changed):

- Decided 2026-11-24: `install.py` is the one supported install route in every host; the marketplace files stay valid and unadvertised (ADR 0003, "Changes"). Tested: a marketplace install names the guide `/core:cg` and `cg.py packs` then sees only core.
- Decided 2026-11-24: a project's pack settings go in `.cg-docs/config.json` under `settings`, keyed by pack (ADR 0003, rule 7); `cg.py status` prints them. For `lang-r`: `"settings": {"lang-r": {"r-syntax": "tidyverse"}}`; absent means `data.table-collapse`, the default the maintainer chose. Setup (task 1.3) proposes the value from the project's R code and the human confirms it.
- Decided by the maintainer on 2026-11-24: the glossary stays strict. `suite` and `manually` remain unconditional, and pack content is reworded to pass, as in the `lang-r` port (#221).
- Decided 2026-11-24: hub tooling (`tools/`, `install.py`) is capped at 2,000 lines in `SCOPE.md`, checked in CI (#222).
- `LICENSE` (MIT) added on 2026-11-24, holder as in `GPID-WB/global-poverty-map`.
- The documentation pages in `docs/` other than `adr/`, `v2/` and `install-block.md` still describe version 1 (task 7.5).

- The plan's body predates the glossary and uses some avoided words. The amendments and the glossary govern.
- Issue texts say "Spec verifier"; it is now the `contract` verifier. Issue texts say ten principles; there are twelve.
- The `v2` history was rewritten once on 2026-11-24 to remove internal wording. Commit hashes quoted before that date may no longer exist.
