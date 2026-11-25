# Handoff: where the 2.0 build stands

Written 2026-11-24 for whoever continues the work, in any coding agent. Last updated 2026-11-25 by the Fable 5.2 session that reviewed the wording written for the gate (task 1.7, #223). Update this file when the state changes; it is the first thing to read.

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
| Version sync | `tools/sync_version.py` | each `pack.json` is its pack's version source; core's version is the hub's (`1.99.0.9000`, the work in progress before 2.0.0); the root `plugin.json` `repository` is the hub URL's source; `docs/install-block.md` is the one other place it appears |
| `cg.py` | `packs/core/cg/scripts/cg.py` | task 1.2: `doctor`, `status`, `new`, `packs`; and `setup`, which writes what the human confirmed in the setup playbook (#219, finding 2) and records data rules (`--data path=level`, later runs without `--packs`). `status` names the next playbook only with `--guide`, which only the guide passes (#223); it prints a `data` line. Standard library, Python 3.9 or later |
| Checks and CI | `tools/lint_skills.py`, `tools/validate_pack.py`, `tools/check_budgets.py`, `.github/workflows/v2.yml` | task 1.6; CI runs the checks, and pytest on Linux, macOS and Windows with Python 3.9 and 3.13 |
| Installer | `install.py`, `docs/install-block.md` | task 1.4; installs into `~/.agents/skills` with links from `~/.claude/skills`; owns only what `~/.cg/installed.json` lists |
| `lang-r` pack | `packs/lang-r/` | task 1.5: the eight v1 R skills, renamed `r-*`; lead skill `r-shared` |
| The guide | `packs/core/cg/SKILL.md` | task 1.3: reads `~/.cg/launcher.json`, runs `cg.py status`, follows the playbook status names; starts nothing when the human did not type `/cg` |
| Playbooks | `packs/core/cg/playbooks/setup.md`, `quick.md` | task 1.3; each opens with what the agent owns and ends with a `Reply:` contract |
| Pointer block and templates | `packs/core/cg/templates/` (`pointer-block.md`, `verification.md`, `work-report.md`) | task 1.3; the block is nine lines, written into `AGENTS.md` only, and this repository's `AGENTS.md` holds it |
| Codex adapter | `packs/core/cg/agents/openai.yaml` | task 1.3; optional (ADR 0004); not yet run in Codex |
| Tests | `tests/core/`, `tests/hub/`, `tests/spike/` | 127 tests, and one that runs only on Windows; run `python3 -m pytest -q` (or `uvx pytest -q`) |
| Gate kit | `spike/gate/` | the toy R package, `make_toy.py` (one copy per agent, and the value to give it), `compare_status.py` (status across the copies, work reports, `--collect` for the evidence), and `README.md`, the steps and the table for #223. `run_cli_gate.py` reruns steps B to D in Claude Code, Codex and Kilo from the command line with approval prompts off, and judges each step from files and status. It has two known gaps, noted on #223 for Opus 5.5 (item 14 below). Two one-off probes for the path it misses are in `.cg-docs/gate-m1/panel-shape/`, with a `README.md` |

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
9. **Review by Opus 5.5** of task 1.3 (#219): done. Eight findings in the issue, none blocking the gate. Finding 1 was in Opus's code and is fixed; the others are in the table below.
10. **Fixes by Opus 5.5**: every finding in Opus's code from the reviews is fixed except two left on purpose (see the table), each with a test that fails on the code before it. Each issue has a comment saying what was fixed.
11. **The gate 1.7 (#223): no-go on 2026-11-25, then fixed.** The maintainer ran it in five agents (the four hosts and Posit Assistant in Positron). Evidence and per-agent notes: `.cg-docs/gate-m1/` (`notes.md`). Five failures, posted on #223: a bare `/cg` did not start the guide in Kilo and Posit Assistant (the skill's text arrives as the human's message, without `/cg`); Claude Code and Copilot skipped the hard stop on an estimate (risk lines 1 and 2 read differently); the quick lane ran without `/cg` in Claude Code and Copilot (they followed status's playbook line from the pointer block); P04 named `cg.py guard`, not built yet, so Posit Assistant could not complete work; answers about data were never recorded. The maintainer decided that Opus 5.5 writes all the fixes, the wording included, this once, and that Fable 5.2 reviews the wording afterwards. The maintainer also noted that most people run agents with auto-approval, so no stop may rely on a host's approval prompt.
12. **Fixes and the rerun, 2026-11-25.** Commits `4a53f225` (code) and `d708ded0`, `0d92119c`, `fa65adcd`, `2ac6c749` (wording), each with a test that failed first. `run_cli_gate.py` reran B to D on fresh copies: Codex 9 of 9 and Claude Code 8 of 9 on the final text (`.cg-docs/gate-m1/rerun-5/`), Kilo 9 of 9 (`rerun-6k/`, after the toy package got `Author` and `Maintainer` fields and the script looked for `headcount()` in any R file). Claude Code was recorded as mentioning `/cg` at the end of a plain reply and not at the start; item 13 shows that this was the script and not the agent. Earlier rounds, kept as evidence: `rerun/` to `rerun-4/` (one Codex round failed on a script error, `exec resume` takes no `--sandbox`).
13. **Review of the gate wording by Fable 5.2, 2026-11-25: done.** Commits `0c7324c1` to `d93dfef6`. A comment on #223 gives each item as kept or changed, with the reason; #219 and #221 have their own.
    - *Kept as Opus 5.5 wrote it:* the guide's Tools and Approval rules, the rule that a failed check is fixed in the code and not in the check, the file list from `--dry-run`, the pointer block's sentence on `/cg`, the closing sentence of the guide's section 2.
    - *Changed:* the guide's section 2 (who started the guide is decided from the human's message alone) and its Installs rule; quick risk lines 1, 2 and 7, the data question asked at the hard stop, and what `completed` needs; setup's data questions and write step; the condition for the pointer block's sentence, and a PowerShell note; P12's "Who to ask"; the description of `r-shared` (#221, finding 1). This also closes #219 findings 3, 4 and 5, and the wording half of finding 8.
    - *Two things the first rerun did not measure as recorded.* Claude Code does open a plain reply with the sentence on `/cg` (its session files show it): `run_cli_gate.py` reads only the last message of a Claude Code turn, so that check fails wrongly. And Kilo's command line sends the literal `/cg`, so failure 1, where the guide's text arrives as the human's message, was never rerun. Sent in that shape from the command line, a bare `/cg` started setup in 2 of 4 runs on the text of `e624bca5` and in 10 of 10 on the final text (`.cg-docs/gate-m1/panel-shape/`).
    - *Rerun on the final text* (`.cg-docs/gate-m1/rerun-8/`): Codex 9 of 9, Kilo 9 of 9, Claude Code 8 of 9 by the script and 9 of 9 with its session file read for the ninth check. `rerun-7/` is the same rerun on the first round of changes.
    - *Not fixed:* in the panel's shape with a request after `/cg`, Kilo still opens its reply with the pointer block's sentence and then runs the guide. Claude Code loaded no `r-*` skill in any of its 15 rerun sessions, ten of which were asked to write R code; Since the new description Kilo loaded `r-shared` and both dialect skills in three of six steps that write R code, against none of eight before (#221).
14. **Next.**
    - *For Opus 5.5, code, listed on #223:* `run_cli_gate.py` reads the whole reply of a Claude Code turn; it gains a step that sends the guide's text as the human's message (the probes in `panel-shape/` show how); its transcripts are no longer named `claude.md`, which Claude Code loads as project instructions on a file system that ignores case; `cg.py status` checks the shape of `approved-tools` and `classification-levels` and prints them (#219, finding 8).
    - *For the maintainer:* a bare `/cg` once in Kilo's panel and once in Posit Assistant, on core at `d93dfef6` or later; Copilot was not retested. Three decisions are open, in the comment on #223: whether quick work tells the agent to read the lead skill of each pack the project expects (it changes rule 1 of ADR 0003); whether `cg.py setup` keeps `--contact`, which no playbook asks for any more; and data rules by folder for a project with many data files (task 2.1).
    - *Then milestone 2,* built by Fable 5.2 and reviewed by Opus 5.5.

No task in this set failed its "Done when" twice. CI failed once each in tasks 1.6 and 1.4, both on Windows and both in tests, and was fixed in the next commit.

Windows: the command-line host run is merged (#258) and recorded in ADR 0001. It matched macOS except that `python3` does not exist (the agents used `python`) and a directory junction worked as the link; `install.py` and `cg.py` were changed for both. Still waiting on the maintainer: a run with the project inside OneDrive (run B of `spike/host-matrix/WINDOWS.md`), the editor panels on Windows, and `install.py --packs core,lang-r` from a clone in a OneDrive folder whose name has spaces.

For every later playbook: no file of the core pack names `python3` (a test holds this). Start `cg.py` with the interpreter recorded in `~/.cg/launcher.json`, by absolute path, as section 1 of the guide says (ADR 0001, design change 8).

### Before the gate

- Make the toy project outside this hub checkout and outside any folder that holds `.cg-docs/`. Status now looks upward for the nearest `.cg-docs/` (#218, finding 2), so a project inside this checkout would be taken for the hub.
- The host test skills (`cg-spike-*`) are no longer in the user skill folders on the maintainer's Mac (checked 2026-11-24). If they come back, doctor only warns about them now (#218, finding 4).
- A new repository with no commit is fine now (#218, finding 3), and so is running `install.py` from a virtual environment: the launcher records the base Python (#218, finding 1).
- Version 1 is still on the maintainer's Mac (`~/.compound-gpid`, the PATH block in `~/.zshrc`, an entry in Kilo's settings). `install.py` reports it with the steps to remove it. It does not affect the gate.
- In Codex, check the policy file: an ordinary request in plain words must not load `cg`, and `$cg` must still run (ADR 0001, "Still open").
- In one host, ask for a plain piece of R code without `/cg` and note whether `r-shared` is loaded (#221, finding 1).

### Findings from the review

Each is in its issue with proof, and each fix is in a comment on that issue.

| Issue | Finding | Priority | State |
|---|---|---|---|
| #220 | A first install that fails part-way cannot be run again | P1 | fixed, `63325842` |
| #220 | `--update` deletes a real folder that replaced its link | P1 | fixed, `63325842` |
| #218 | The launcher records a virtual environment's Python | P1 | fixed, `a48e6307` |
| #219 | doctor writes the launcher from the hub checkout, so the guide runs the hub's `cg.py` | P2 | fixed, `a48e6307` |
| #218 | `status` from a subfolder, no-commit repository, `cg-*` folders, PowerShell, config shape, `new` titles, missing folder, usage text | P2, P3 | fixed, `a48e6307`, `e8b5d180`, `d23ab1e4` |
| #220 | plugin copies beyond the lead skill, unknown `--remove`, doctor's exit code, tests reading `PATH` | P2, P3 | fixed, `e5885558` |
| #222 | YAML shapes, folded descriptions, `../` paths in text, a pack needing a newer core, one glossary path list | P2, P3 | fixed, `910fa986` |
| #222 | the `python3` and playbook rules are tests, not lint rules | P3 | left as tests on purpose |
| #217 | `sync_version.py` from another folder; root `plugin.json` claim | P3 | fixed, `910fa986` |
| #217 | `requires-core` has no source | P3 | in part: the validator fails a value newer than core; the rest waits on the version decision |
| #221 | Two `/cg-fixbug` notes, "hand-computed" | P2, P3 | fixed, `bc4c9529` |
| #217 | `2.0.0.9000` sorts after `2.0.0` | P2 | fixed: the maintainer chose `1.99.0.9000`; a test holds every pack before 2.0.0 |
| #221 | `r-shared`'s description does not say it decides which R skills load | P2 | description rewritten, `25dc5642`: Kilo then loads it and the dialect skills in three of six steps that write R code, none of eight before; Claude Code still loads no R skill (a decision for the maintainer, item 14) |
| #221 | The team's name in two descriptions | P3 | task 7.3 |
| #219 | Setup's writes are made by the model, not by code (P3) | P2 | fixed: `cg.py setup` (`3e40f5bf`), and the setup playbook calls it (`d708ded0`, gate) |
| #219 | Line 1 of the quick risk table and the build comment disagree on figure labels | P2 | measured at the gate (two hosts answered no); lines 1 and 2 rewritten (`d708ded0`), then reviewed: line 1 says what is a yes and what is a no (`99b1746c`) |
| #219 | No step for `status` failing; no PowerShell note in the pointer block; config keys defined only in a playbook | P3 | fixed in the wording, `0c7324c1`, `3b594f56`, `94f3a48a`; for the config keys, a shape check in `cg.py status` is left for Opus 5.5 |
| #219 | Model-started guide may raise an approval prompt; Codex sandbox and the launcher write | P3 | checked at the gate: no problem seen; the Codex policy file works |

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
