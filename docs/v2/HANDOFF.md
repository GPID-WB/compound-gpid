# Handoff: where the 2.0 build stands

Written 2026-11-24 for whoever continues the work, in any coding agent. Last updated 2026-11-25 by the Fable 5.2 session that built task 2.1 (#224), the first task of milestone 2, then wrote in the maintainer's decision on who answers for the data, and set this repository up for `/cg` on 2026-11-26; then by the Opus 5.5 session that reviewed task 2.1 on 2026-11-26 (item 18), by the Fable 5.2 session that built task 2.2 (#225) the same day (item 20), by a second Fable 5.2 session that probed it and wrote in the maintainer's decision on replies (item 21), by the Opus 5.5 session that reviewed task 2.2 the same day (item 22), by the Fable 5.2 session that built the maintainer's second decision on replies and fixed W1 to W13 (item 23), and by the Fable 5.2 agent that built task 2.3 (#226) the same day (item 26). Update this file when the state changes; it is the first thing to read.

## Read in this order

1. This file.
2. The plan: `.cg-docs/plans/2026-11-24-compound-gpid-v2.md`. Its "Amendments after approval" section overrides the body where they differ.
3. `packs/core/cg/GLOSSARY.md`. Every new text uses these words.
4. `packs/core/cg/principles/README.md`, then the principle files you need.
5. The decision records in `docs/adr/` (0001 hosts, 0002 sources, 0003 packs, 0004 no base host, 0005 artifacts, approvals and the tier) and `SCOPE.md`.

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
| `cg.py` | `packs/core/cg/scripts/cg.py` | task 1.2: `doctor`, `status`, `new`, `packs`; and `setup`, which writes what the human confirmed in the setup playbook (#219, finding 2) and records data rules (`--data path=level`, later runs without `--packs`). `status` names the next playbook only with `--guide`, which only the guide passes (#223); it prints a `data` line. Task 2.1 added `validate`, `approve` and `tier` (next row). Task 2.2 added no command: `approve` takes an intent, and `status --guide --playbook NAME` opens the playbook the human asked for. Task 2.3 added none either: `new plan` takes `--intent` and `--other-work`, `validate` checks a plan's checks, slices and data register, and `approve` holds a plan to its intent and to an amendment. Standard library, Python 3.9 or later; 1,663 of its 2,500 lines |
| Artifact schema, approvals, tier | `docs/adr/0005-artifacts.md`; the table `ARTIFACTS` in `cg.py`; `packs/core/cg/templates/` (one template per artifact type) | task 2.1, reviewed by Opus 5.5 on 2026-11-26 (six fixes in code, nine wording findings open, item 18); the ADR still waits for the maintainer's acceptance: schema 2 with `schema: 2` as its marker, version 1 artifacts read as they are, `cg.py validate` (`--strict` for a project's CI), `cg.py approve` (one file per approval under `.cg-docs/approvals/`), `cg.py tier` (six declared facts, and the data rules and the file count from code), and `cg.py approve --reads`, which records the human's decision that a coding agent reads data it is not cleared for. Task 2.3 amended the ADR: a plan is built on a decided intent, the record of an approval keeps the text, the artifact names its record under `approval`, and an approved plan changes by a dated line under `## Amendments` |
| Checks and CI | `tools/lint_skills.py`, `tools/validate_pack.py`, `tools/check_budgets.py`, `.github/workflows/v2.yml` | task 1.6; CI runs the checks, and pytest on Linux, macOS and Windows with Python 3.9 and 3.13 |
| Installer | `install.py`, `docs/install-block.md` | task 1.4; installs into `~/.agents/skills` with links from `~/.claude/skills`; owns only what `~/.cg/installed.json` lists |
| `lang-r` pack | `packs/lang-r/` | task 1.5: the eight v1 R skills, renamed `r-*`; lead skill `r-shared` |
| The guide | `packs/core/cg/SKILL.md` | task 1.3: reads `~/.cg/launcher.json`, runs `cg.py status`, follows the playbook status names; starts nothing when the human did not type `/cg` |
| Playbooks | `packs/core/cg/playbooks/setup.md`, `quick.md`, `brainstorm.md`, `plan.md` | tasks 1.3, 2.2 and 2.3; each opens with what the agent owns and ends with a `Reply:` contract. `plan.md` is at 117 of its 120 lines |
| Grilling | `packs/core/cg/grilling.md` | task 2.2: how a fact is looked up, how a decision is put to the human, the restatement, the assumptions block, and the replies that are not a yes. It is no playbook: the brainstorm playbook has it read in full, and the guide points every playbook at it. 76 lines; a test holds it to a playbook's 120 |
| Pointer block and templates | `packs/core/cg/templates/` (`pointer-block.md`, `verification.md`, `work-report.md`) | task 1.3; the block is nine lines, written into `AGENTS.md` only, and this repository's `AGENTS.md` holds it |
| Codex adapter | `packs/core/cg/agents/openai.yaml` | task 1.3; optional (ADR 0004); not yet run in Codex |
| Tests | `tests/core/`, `tests/hub/`, `tests/spike/` | 204 tests, and one that runs only on Windows; run `python3 -m pytest -q` (or `uvx pytest -q`) |
| Gate kit | `spike/gate/` | the toy R package, `make_toy.py` (one copy per agent, and the value to give it), `compare_status.py` (status across the copies, work reports, `--collect` for the evidence), and `README.md`, the steps and the table for #223. `run_cli_gate.py` reruns steps B to D in Claude Code, Codex and Kilo from the command line with approval prompts off, and judges each step from files and status. Since task 2.2 it also runs step G, a brainstorm, and `--steps` picks the steps. Since task 2.3 it runs step H, a plan on the intent of step G, to its hard stop. It has two known gaps, noted on #223 for Opus 5.5 (item 14 below). Two one-off probes for the path it misses are in `.cg-docs/gate-m1/panel-shape/`, with a `README.md` |

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
14. **Fable's code items and the maintainer's three decisions: done, 2026-11-25.** Opus 5.5 did the four code items of Fable's review (`967ddf30`, `34f73cd7`, `81dcd279`): status checks and prints the data rules, `run_cli_gate.py` reads every Claude Code message and has a `kilo-panel` agent that sends the panel's shape, and transcripts are `<agent>-transcript.md`. Rerun with them, `rerun-9/`: Claude Code and `kilo-panel` 9 of 9. The maintainer decided: quick work has the agent read the lead skill of each expected pack before it writes code (step 3; rule 1 of ADR 0003 amended, `cde18ff4`); `cg.py setup` no longer takes `--contact`; data rules by folder wait for `cg.py tier` (task 2.1). The maintainer checked a bare `/cg` once in Posit Assistant and once in Kilo's panel: both proposed a setup.
15. **The gate 1.7 (#223): go, decided by the maintainer on 2026-11-25.** Milestone 1 is done. Copilot was not retested after the fixes (it has no command line); check it during the pilot. To retest without a human after a change to the guide or the playbooks: `python3 spike/gate/run_cli_gate.py --kilo-model openai/gpt-6-luna` (Claude Code, Codex, Kilo, and Kilo with the panel's shape).
16. **2.1 (#224)** Built by Fable 5.2 on 2026-11-25. Artifact schema, version 1 reader, `validate`, `approve`, `tier`. Its three "Done when" lines hold, each with a test (`tests/core/test_artifacts.py`). See "Ready for review" below. Gate rerun on this wording (`.cg-docs/gate-m1/rerun-10/`): Claude Code, Codex, Kilo and `kilo-panel` each 9 of 9. All four ran `cg.py tier` and stopped on `tier: elevated`, and each work report passes `cg.py validate --strict`. Codex and Kilo also answered yes to `interface` for a new exported function, and Claude Code answered no; the tier was the same, because `number` was a yes in all four.
17. **The maintainer's decision on data, 2026-11-25, built the same day by Fable 5.2.** P12's check line changes, not the code. And the human answers for the data: when they declare a file Public, or decide that a coding agent reads a file it is not cleared for, the work goes on, as long as they were warned and the decision is on record. Commits `7cd3671d` (the tests, failing) and `14404f3e`: `cg.py approve --reads` records the decision, `tier` names it on every run and no longer raises the tier for that file, `status` lists it under `data-decisions`, P12 says who answers for the data, and the quick playbook has the agent warn the human and record the decision before the file is opened. ADR 0005 is amended under "Tier". Gate rerun on this wording (`.cg-docs/gate-m1/rerun-11/`): Claude Code, Codex, Kilo and `kilo-panel` each 9 of 9, and each work report passes `cg.py validate --strict`. No agent recorded a decision on data unasked. The rerun shows that the old steps still pass; it does not try the new path, because the toy's one data file is declared Public. No agent has been run yet on a file that is not cleared.
18. **Review of 2.1 by Opus 5.5, 2026-11-26: done.** Fifteen findings in a comment on #224, each with proof. Six were in code and are fixed: `c477d6c0` (the tests, failing first) and `2ed91434`; CI green. Three were P1: a rule or a decision for the project root (`.`) covered files outside the project, `~/.ssh` included; a folder given to `--reads` was judged by its own rule, so a stricter file inside it was read at a low tier; and `approve` recorded "No." as a yes, for a plan and for data. The other three: a schema 2 file with a byte order mark, an unclosed frontmatter or another encoding was read as version 1 and never checked; a plan put back to the text an amendment replaced passed (only the newest approval counts now); a level that changed only in case voided a decision. Gate not rerun: no guide or playbook text changed.
19. **The wording findings of the review, fixed by Fable 5.2 on 2026-11-26.** Commits `080c9168` (three tests, failing first) and `d84e713a`. Finding 7: every cell a template leaves to fill now asks for its content, and `unfilled()` counts one request left anywhere in a line, so a completed work report needs a changed file and a verdict for P3, P4 and P6. Findings 8 to 11, in step 2 of `quick.md`: the warning names the organization's rules; a decision on data is not a yes to the contract; `--reads` takes the place the human named and nothing wider; and each cause of `refused` has its own next step (a reply that declines is the answer and is not asked again; a reply that agrees in words that open with a no, which `SAYS_NO` refuses, gets one question for a plain yes). Findings 12 and 13: P12 names the place of a decision, and its check line is as wide as the code. Findings 14 and 15: the known limits below and ADR 0005. Gate rerun on this wording and these templates (`.cg-docs/gate-m1/rerun-12/`): Claude Code, Codex, Kilo and `kilo-panel` each 9 of 9. Each work report passes `cg.py validate --strict`, lists the files it changed and holds a verdict for P3, P4 and P6. As in rerun 11, no agent met a file that is not cleared, so the path of a decision on data is covered by tests only.
20. **2.2 (#225)** Built by Fable 5.2 on 2026-11-26. Grilling, the restatement, the assumptions block and the brainstorm playbook. Its three "Done when" lines hold, each with a test (`tests/core/test_brainstorm.py`). See "Ready for review" below. Gate rerun on this wording (`.cg-docs/gate-m1/rerun-13/`), with the new step G: Claude Code, Codex, Kilo and `kilo-panel` each 13 of 13. In step G each agent wrote an intent and changed no code, refused "Sounds good." as a yes (Claude Code passed it to `approve`, which refused it; Kilo asked what was unclear without running it, twice; Codex asked too, and its transcript holds messages only, so whether it ran `approve` is not known), and ended with a `decided` intent whose record holds the reply the script sent. Read in the transcripts and not judged by the script: every agent put its questions with a recommended answer, and two wrote the term they settled into the project's `GLOSSARY.md`. Codex recommended the average shortfall among the poor only, which Claude Code's own facts name as the common mistake with this measure, and the script's human took it: the playbook puts the decision to the human, and it does not make the recommendation right. Kilo showed a summary of the intent at the hard stop, not the file's text. The script takes every recommended answer, so a correction and a decision handed back were tried by the tests only. The gate ran on the text of `25dddab1`; the commit after it changed two messages of `cg.py` and no guide, playbook or template.
21. **A second look at 2.2 by another Fable 5.2 session, and the maintainer's decision on replies, 2026-11-26.** Probes on `439996a6` found five breaks, each now with a test that failed first (`46cc5bb6`) and a fix (`8d01c67e`). (1) Only the word `open` counted as no answer: an intent was decided with "pending", "TBD", "?" or `open` in backticks in the human's cell. (2) An intent was decided with nothing written under Goal, Out of scope, A wrong result or Assumptions. (3) `approve` refused a list and recorded the rest: "I'd rather not", "Maybe", a question, and the playbook's own placeholder `<the human's reply, word for word>` were each recorded as a yes. (4) "Yes, and also add the poverty gap" was recorded. (5) A source of "unknown" and a recommended answer of "-" passed. **The maintainer decided for (3): code records a reply only when it holds a plain yes word, with ok, sí and de acuerdo among them.** The rule is in ADR 0005 under "Approvals". The empty-section check holds for every artifact type, a work report included. This was a review by the model that built the task, so it does not stand in for the review by Opus 5.5. Gate rerun on this wording (`.cg-docs/gate-m1/rerun-14/`): Claude Code, Codex, Kilo and `kilo-panel` each 13 of 13, and every artifact in the four copies passes `cg.py validate --strict`. The rerun also showed that Kilo's transcripts of reruns 13 and 14 held the line of `approve` that names who said yes, with the organization's email domain left in: `sanitize()` replaced the user name before it looked for addresses. Fixed with a test that failed first (`sanitize` in `spike/host-matrix/run_cli_checks.py` removes addresses first, and the name git gives), and the four lines are removed from the evidence. The earlier version of the two rerun-13 files is still in the history at `498eeeca`.
22. **Review of 2.2 by Opus 5.5, 2026-11-26: done.** A comment on #225 gives each finding with its proof. Seven were in code and are fixed: `c3a39de4` adds the tests, failing first, and `7a6fafda` the fixes; CI green. Three were P1. (1) A yes word was enough: `the_yes` recorded all 43 replies probed, among them "Is this ok?", "OK, wait.", "Yes if you drop D2", "Yes, drop D2.", "I haven't approved this" and "Sí, aunque cambia D2". It now refuses a question that holds a yes, a not yet anywhere beside a yes (`NOT_YET`), more conditions (`HAS_CONDITION`, with "if" and the Spanish ones), a change asked for with no marker word (`CORRECTION`), and more negations. (2) An open decision, or a fact with no source, under a subheading of Decisions or Facts was decided: `table_rows` now reads every table under the heading. (3) `grilling.md`'s assumptions block, pasted with its requests left in, passed. The four others: placeholders behind a list mark or off the list, and "none" as a source (P2); filler under a heading, an HTML comment included (P2); a name JSON-escaped or decomposed left in a transcript (P3; none is in the committed evidence); and a brainstorm asked for before setup was set aside in silence (P3). Still let through by judgement: a no after the yes ("Yes to D1, no to D2"), "I agree with nothing here", and a decision handed back with a yes ("OK, your call"), which `grilling.md:75` calls a yes. For the maintainer: word lists keep missing cases, and the rule that would not miss is to record a reply only when every word is a plain yes word or filler. That changes the decision of 2026-11-26, so it was not built. Gate not rerun: no guide, playbook, `grilling.md` or template text changed. `cg.py validate --strict` still passes on the four copies of rerun 14. The installed core in `~/compound-gpid` is behind `v2` until its next `install.py --update`.
    **Left for Fable 5.2 before task 2.3: thirteen wording findings, W1 to W13 in the comment.** The P2 ones: W1, `grilling.md:75` should not call a handed-back decision a yes; W2, row 3 of the replies table, `quick.md:51` and ADR 0005 "Approvals" are behind the code since `7a6fafda`; W3, the brainstorm has no way to end when a decision waits on an experiment or on someone else; W4, a subagent in a fresh context is not told that data stays closed. The P3 ones: W5 to W8 and W11 in `grilling.md` and `brainstorm.md`; W9, how to quote a `--reply` that holds `"`, `$` or a backtick; W10, "Approaches considered" is asked for but not required by code; W12 and W13, two rows of the guide's table.
23. **The maintainer's second decision on replies, and W1 to W13, 2026-11-26.** After the review the maintainer decided: `cg.py approve` records a reply only when it is a plain yes and nothing else. Commits `dace81dd` (the tests, failing first) and `1da1fc2f`. A reply is recorded when it holds a word of `YES` and every other word in it is of `FILLER`, with no question mark; the lists `NEGATION`, `NOT_YET`, `HAS_CONDITION` and `CORRECTION` from the review are gone, because the rule now names what a yes is. "Yes, that is what I want." is refused and asked once more, so each hard stop that code records tells the human that a plain yes confirms (step 6 of the brainstorm, the data stop of quick work). The gate's last reply in step G is "Yes." now. The thirteen wording findings are fixed in the same commit: W1 and W2 by the new table of replies in `grilling.md`; W3, a brainstorm may end with a `draft` intent when a decision waits; W4 to W9 and W11 as the review suggested; W10, "Approaches considered" is a required section of an intent; W12 and W13, two rows of the guide's table. ADR 0005 "Approvals" tells how the rule got here. Gate rerun on this wording (`.cg-docs/gate-m1/rerun-15/`): Claude Code, Codex and Kilo each 13 of 13, and each intent was decided on the reply "Yes.". `kilo-panel` passed 11 of 13: in step C it got the yes, found that the change needed `NAMESPACE` and the help file beside the two files it had declared, and stopped again to ask, as step 3 of quick work tells it to. The script sent one yes only, so two checks failed with no fault in the agent. The script now says yes again, three times at most, while no code has changed (`1d23e193`, with a test that failed first). Rerun of step C for that agent (`rerun-15b/`): 7 of 7. In that rerun the agent declared all four files at once, so the second yes is covered by the test only.
24. **From here the Fable 5.2 session that holds this conversation starts each agent itself** (the maintainer's instruction of 2026-11-26): a Fable 5.2 agent builds a task, an Opus 5.5 agent reviews it, one writer in the checkout at a time. It stops only for a decision that is the maintainer's or for something that cannot be undone. The stop after each task is lifted.
25. **Task 2.3** (#226, `plan`, hard stop 1, plan-stage verifiers) was given to Fable 5.2. The issue names 2.5 (the verifier engine) as a dependency and the plan puts 2.3 first: the playbook and the hard stop are built now, and the dispatch of the plan-stage verifiers is a marked placeholder for task 2.5.
26. **2.3 (#226)** Built by Fable 5.2 on 2026-11-26. The plan playbook, hard stop 1, and what code holds of a plan. Its three "Done when" lines hold, each with a test that failed first (`tests/core/test_plan.py`). Commits: `03d31f25` (the tests, failing), `c36ef973` (the code and the text), `8c5a3de7` and `a3ba0aa4` (the gate's step H, test first), `a0ef4e12` (ADR 0005 and the ledger), and `90ff76ee` (what an amended plan prints at `validate`). See "Ready for review: task 2.3" below, and "Decisions for the maintainer from task 2.3" under "Known loose ends". The gate was not run by the build agent: the session that started it reruns it with step H, after `install.py --update` in the home clone. What a human types changed: `/cg plan`.
27. **Next:** the gate rerun with step H, then the review of 2.3 by Opus 5.5, then task 2.4 (#227, `work`: `evidence`, `guard`, stop rules, `worker.md`), built by Fable 5.2.

### Ready for review: task 2.3 (#226), for Opus 5.5

Read `packs/core/cg/playbooks/plan.md` first, then ADR 0005, where the paragraphs marked task 2.3 give each choice with the alternatives set aside. The commits are in item 26. Each source the ledger names for `plan` was read in full at its pinned commit before the text was written (`spec-driven-development`, `planning-and-task-breakdown`, `to-spec`, `to-tickets`, pstack's `multi-phase-plan`, `architect`, `principle-foundational-thinking` and `principle-sequence-verifiable-units`, and version 1's `cg-plan`), and the ledger rows say what changed for analytical work.

How the three "Done when" lines are held:

| Done when | In the text | In code, with its test |
|---|---|---|
| Every check in the plan can fail | step 3 of the playbook, the five things each check is held to, and "what no check would catch" below the table; step 4, every check belongs to a slice | `contract_problems`: a check's command and its failing outcome are no placeholder, the outcome does not say that the check cannot fail (`CANNOT_FAIL`), each slice ends in a check that exists, and a slice ends in every check (`test_every_check_in_a_plan_can_fail`) |
| The turn ends at approval; approval is written to the artifact | step 7, a hard stop that shows the plan as the file reads and asks for a plain yes; step 8, no slice starts in the same turn | a plan is `approved` only through `approve`, which records a plain yes and nothing else, writes `approval: <the record>` into the plan, and keeps the approved text in the record (`test_a_plan_is_approved_only_by_the_humans_recorded_yes_which_is_written_into_it`). Code cannot see a turn end: the gate's step H judges that from the files, with a unit test of its own (`tests/spike/test_gate.py`) |
| An unfinished plan is never overwritten | step 1: a draft is continued in its file, an approved plan is frozen and changes by an amendment, other work gets a plan of its own only after the human said so | `new` never writes over a file and makes no plan beside an unfinished one without `--other-work` (`test_an_unfinished_plan_is_never_overwritten`); an approved plan is approved again only with a new dated line under `## Amendments`, and each record keeps the text it approved (`test_an_approved_plan_changes_only_by_an_amendment_and_what_was_approved_stays_readable`) |

Two more things code holds, which ADR 0005 had left open: a plan is built on a decided intent (`test_a_plan_is_built_on_a_decided_intent`), and its data register agrees with the recorded classifications (`test_the_data_register_is_held_to_the_recorded_classifications`).

Things to try to break:

- **A check that cannot fail and passes.** `contract_problems`, `nothing` and `CANNOT_FAIL` in `cg.py`. Code refuses a placeholder and a cell that says the check cannot fail. It does not judge the command, or an outcome that is a matter of opinion: "the output looks wrong" passes. Look for a cell that says "this cannot fail" in words the list misses, and for a legitimate outcome it refuses ("NA is returned" must pass).
- **Slices.** A slice with no check, a check no slice ends in, a slice by code with no tool, a second table under a subheading. A range such as `C1-C3` names only its two ends.
- **The intent under a plan.** `decided_intent` and `plan_inputs`. Check that no path makes a plan on a draft intent, on a `decided` typed into the file, or on an intent changed since its yes; and that an approved plan is not failed later because its intent or a data rule moved.
- **The data register.** `plan_inputs`: a dataset with no recorded rule, a level that differs, a folder rule, an absolute path, the row "none". A plan that reads data and says "none" passes: that is for the `governance` verifier.
- **Amendments.** `amendments` in `cg.py` counts lines such as `- 2026-11-26: ...` under `## Amendments`. Check that an approved plan cannot be changed and approved again without one more line, that a status set back to `draft` does not get round it, and what a deleted record does.
- **The frontmatter that `approve` rewrites.** It sets `status` and `approval` and nothing else, in a file with a byte order mark or other line ends too.
- **`new plan`.** The refusal beside an unfinished plan counts schema 2 plans that are not closed, with any status code does not know. `--other-work` is the agent's to pass, after the human's yes.
- **The wording** of `plan.md`, sentence by sentence, and the changed lines elsewhere: the new row of the guide's table, two sentences of `quick.md` (a slice of an approved plan in step 1, `/cg plan` in the `size` line), the Reply of `brainstorm.md`, the check lines of P1, P3 and P12, the glossary term amendment, and two lines of the plan template.
- **The gate's step H.** The script answers a complete draft with a yes that goes on before it says "Yes.". Check that it cannot pass an agent that records the first reply or that rewords it into a yes.

Known limits, none fixed here:

- The plan-stage verifiers are not dispatched. Step 6 of the playbook has a self-review of P1, P3, P6, P12 and P10 in their place, marked `PLACEHOLDER: written in task 2.5`.
- Whether a command can fail, whether an outcome is a matter of opinion, whether a slice is thin, and whether the register lists every dataset the work reads are by judgement. "Five files at most" is in the playbook only.
- Nothing holds the work to an approved plan yet (task 2.4). Until then the plan's Reply sends the human to `/cg` with the first slice, and step 1 of quick work tells the agent to read the plan. Quick work then stops again at an elevated tier.
- The lines `tier` prints at plan stage are shown at the hard stop and are not written into the plan.
- A version 1 intent cannot carry a plan: it has no recorded yes, so `new plan` refuses it. The work it describes starts with a new brainstorm, which may read it.
- The guide opens the plan playbook when the human types `/cg plan` or asks for a plan. A bare `/cg` with a decided intent and no plan still opens quick work; routing by state is task 2.14.
- The plan playbook opens no data file and runs none of the project's code, so a check is judged to fail today by reading, not by running it.
- Step H of the gate needs the intent of step G, so G always runs before it. The script sends one correction and takes every recommended answer.
- Task 2.3 was not built with `/cg`, for the reason given for tasks 2.1 and 2.2: it touches more than five files, and the plan playbook did not exist until this task wrote it. Task 2.4 can be the first one planned with `/cg brainstorm` and `/cg plan`.

### Ready for review: task 2.2 (#225), for Opus 5.5

Reviewed on 2026-11-26: see item 22. What follows is kept as the brief the review worked from.

Read `packs/core/cg/grilling.md` and `packs/core/cg/playbooks/brainstorm.md` first, then ADR 0005, where the paragraphs marked task 2.2 give each choice. The commits: `c8c7077a` (the tests, failing), `1ccb41c6` (the code and the text), `25dddab1` (the gate's step G) and `439996a6` (the ADR, the ledger, two messages). Each source was read in full at its pinned commit before the text was written, and the ledger rows say what changed for analytical work.

How the three "Done when" lines are held:

| Done when | In the text | In code, with its test |
|---|---|---|
| Facts are looked up by the agent; decisions are put to the human with a recommended answer | `grilling.md`, "Facts and decisions" and "How a decision is put"; step 2 and 3 of the playbook | `intent_problems`: `approve` refuses an intent in which a fact has no source or a decision has no recommended answer (`test_an_intent_with_something_still_open_is_not_confirmed`) |
| The session ends only when nothing is silently assumed and the human confirms | the Assumptions block; steps 5 and 6 of the playbook, a hard stop | an intent becomes `decided` only through `approve`, which needs every decision answered and the Assumptions section filled; a status typed into the file fails `validate` and shows under `waiting-on-human` (`test_an_intent_is_decided_only_by_the_humans_recorded_yes` and the two after it) |
| A list of replies that do not count as a yes | `grilling.md`, "Replies that are not a yes" | `YES`, `FILLER`, `NOT_A_YES` and `SAYS_NO` in `cg.py`: a reply is recorded only when it is a plain yes and nothing else (item 23); a test holds `grilling.md`, P2 and the setup playbook to the list (`test_replies_that_are_not_a_yes_are_refused_with_what_to_ask_next`, `test_grilling_names_every_reply_that_code_refuses_and_so_do_p2_and_setup`) |

Things to try to break:

- **The replies.** `the_yes` in `cg.py`. Since item 23 a reply is recorded only when it holds a word of `YES` and nothing else but words of `FILLER`, with no question mark. This holds for a plan and for `--reads` too. `SAYS_NO` and `NOT_A_YES` only choose what the refusal says. What is left to break: a word of `FILLER` that turns a yes round, and a reply that is not the human's own words.
- **A cell that stands for "not yet".** `blank` and `NOT_FILLED` in `cg.py`: `open`, pending, TBD, a question mark and the like are no answer, no source and no recommended answer, with or without marks of emphasis. A human's answer that starts with such a word is refused until the agent puts it in quotes. Look for a placeholder the list misses.
- **A section with nothing under it.** `empty_sections` in `cg.py`, for every artifact type: a warning in the first status, an error after it and at `approve`. A table with only its two header lines counts as nothing. Look for a section that is empty in substance and passes, such as one line of filler.
- **A draft is allowed to be incomplete.** In a `draft` intent an open decision is a warning, and an error once the status is `decided` or `approve` is asked. Check that no path makes an intent `decided` with something open.
- **The routing.** `status --guide --playbook NAME`: the guide passes the playbook the human asked for, and code opens it only in a project that is set up. The row in the guide's table decides when that is, by judgement: the word `brainstorm` after `/cg`, or a request to think something through with no change asked for. Check that a request for a change still goes to quick work (step C of the gate does), and that a plain question is not taken for a brainstorm.
- **The wording** of `grilling.md` and of the playbook, sentence by sentence. Two choices to question: rounds hold three decisions at most (the sources say one, or the whole frontier), and a first reading is stated with what is missing in place of a confidence number, which P7 would not let pass.
- **The changed lines elsewhere:** the guide's Approval and Asking rules, the sentence on `choice` in step 2 of `quick.md`, the check lines of P1 and P2, and three glossary terms (intent, grilling, assumption).

Known limits, none fixed here:

- Whether a fact was looked up or made up, and whether an answer in the Decisions table is the human's, code cannot tell. The human sees the whole intent at the hard stop, and their yes is recorded against that text.
- The brainstorm opens no data file and runs no code. A fact only the data can show stays an assumption, or becomes an experiment that quick work runs.
- Nothing links a decided intent to the work that follows. The plan playbook (2.3) does that.
- The human reaches the playbook with `/cg brainstorm`, or with a request the guide reads as one. A bare `/cg` with a draft intent open still opens quick work, which lists the intent under `waiting-on-human`; routing by state is task 2.14.
- `grilling.md` has no line budget in `SCOPE.md` or the linter. A test holds it to 120 lines.
- Task 2.2 was not built with `/cg`, for the reason given for task 2.1 below: more than five files, and no plan playbook yet.

### Ready for review: task 2.1 (#224), for Opus 5.5

Read `docs/adr/0005-artifacts.md` first: it gives each choice with the alternatives set aside. Then the commits `9ee64743` (the tests, failing), `b7b6bd7c` (the code and the templates) and `74e9148d` (the playbook wording), and for the decision on data `7cd3671d` (the tests, failing) and `14404f3e`. Things to try to break:

- **The version 1 reader.** `read_frontmatter` and `read_artifact` in `cg.py`. A file with no `schema` key is never failed. `cg.py validate --project .` in this repository reads its 668 version 1 artifacts with no problem; before this task, status did not see the 235 solutions, which version 1 keeps in a folder per category.
- **The approval digest.** It covers the plan's body and leaves out line ends and trailing spaces. Check that nothing an agent can do to a plan after approval goes unseen, and that nothing a sync does voids an approval.
- **The tier.** `clearance` decides whether this coding agent may read a file. Names and levels are compared without regard to case. Only the word `Public` counts as public: the first entry of `classification-levels` does not, in case an organization's list starts higher.
- **The decision on data.** `approve_reads`, `data_decisions` and `decision_for` in `cg.py`. A decision holds for one coding agent, one file or folder, and the level the file had. Check that no decision covers more than the human said, that a change of level asks for a new one, and that a reply that is not a clear yes writes nothing. The wording to check is the new paragraph of step 2 in `playbooks/quick.md` and the changed lines of P12.
- **The wording** of step 2 and step 5 of `playbooks/quick.md`, the data lines of `playbooks/setup.md`, and the five new templates. The facts table kept the wording the gate passed, with a name for each fact in place of a line number.

Known limits, none fixed here:

- An artifact written without `schema: 2` is read as version 1, so `validate` checks nothing in it. `cg.py new` writes the key; an agent that writes a file itself can leave it out.
- `approve` cannot know that the human said what `--reply` holds. It refuses the three replies P2 names, and since the review any reply that starts with a no (`SAYS_NO`); the rest is for the `ownership` verifier.
- The six facts are still the agent's answers. Code only makes sure that each is given and that one yes is enough. The data and size facts are computed, but from what the agent passes: the files in `--touches` and `--reads`, and the name in `--agent`. Nothing checks which coding agent is running, so the same file is cleared or not by the name given.
- Task 2.1 was not built with `/cg`, though its issue asks for that from task 1.7 on. The session was started with a plain prompt, this repository had no `.cg-docs/config.json`, and the one playbook for work, quick, stops at more than five files. Until the plan playbook exists (task 2.3), a task of this size has no playbook to run in. The repository is set up since 2026-11-26 (see the decisions under "Known loose ends"), so a change of five files or fewer can now go through `/cg`.
- A decision on data rests on the reply the agent passes to `--reply`, as a plan's approval does. Nothing stops an agent from recording a decision for a folder when the human named one file; the reply is stored word for word so that a reader can see it.

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
| #224 | Root rule or decision covers files outside the project; a folder read hides a stricter file; "No." recorded as a yes | P1 | fixed, `2ed91434` |
| #224 | Schema 2 file with a byte order mark, an unclosed frontmatter or another encoding read as version 1; a replaced plan text passes; level case voids a decision | P2, P3 | fixed, `2ed91434` |
| #224 | A completed work report passes with empty table cells (finding 7) | P2 | fixed, `d84e713a` |
| #224 | `quick.md` step 2: the warning lacks "their organization's rules bind them"; whether a decision on data is a yes to the contract; the place recorded; what `refused` means (findings 8 to 11) | P2, P3 | fixed, `d84e713a` |
| #224 | P12 leaves out the place and narrows the check line; the handoff says the data facts are not the agent's; ADR 0005 is behind the fixes on two lines (findings 12 to 15) | P3 | fixed, `d84e713a` and ADR 0005 |
| #225 | A yes word was enough; an open decision under a subheading was decided; grilling.md's block with its requests passed (findings 1 to 3) | P1 | fixed, `7a6fafda` |
| #225 | Placeholders behind a mark or off the list, "none" as a source, filler under a heading; a name in another spelling in a transcript; a brainstorm before setup set aside in silence (findings 4 to 7) | P2, P3 | fixed, `7a6fafda` |
| #225 | Wording W1 to W13: a handed-back decision called a yes, the reply lists behind the code, no end for a decision that waits, a subagent not told data stays closed, and nine P3 | P2, P3 | fixed, `1da1fc2f` |

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

- `packs/core/cg/playbooks/quick.md`: step 5 stands in for `cg.py evidence` (task 2.4). Until then the agent fills the work report itself, and `cg.py validate` checks that no part of it is left unfilled.
- `packs/core/cg/playbooks/plan.md`: step 6 has a self-review in place of the dispatch of the plan-stage verifiers (task 2.5), and step 8 sends the human to quick work for the first slice until the work playbook exists (task 2.4).
- In `cg.py`: `PHASE_PLAYBOOK` (no config means `setup`, config means `quick`; task 2.14). Since task 2.2 the guide can also pass `--playbook brainstorm`.

Decisions for the maintainer from task 2.3 (each was built on the conservative path, and none is hard to undo):

- **A plan needs a decided intent.** `cg.py new plan` refuses without one, and so does `approve`. A human with a clear request therefore meets two hard stops, one for the intent and one for the plan. The alternative is a plan with no intent that carries its own statement of a wrong result and its own assumptions. Taken because P1 asks for that statement before a plan, and the plan template holds none.
- **The record of an approval now keeps the text that was approved.** It makes "the original stays readable" (P1) true without git. Records grow by the size of the plan, and they are committed with it.
- **An amendment is a dated line in the same plan**, with the text changed in place. A plan cannot be put back exactly to an earlier text. The alternative is a file per amendment.
- **Only a recorded classification counts in a plan's data register.** A plan whose register names a dataset with no rule in `.cg-docs/config.json` is not approved, also for an output the work will produce.
- **`cg.py` is at 1,663 of 2,500 lines** with about ten commands still to come (`evidence`, `guard`, `verifiers`, `conformance`, `repro` and others). At the rate of tasks 2.1 to 2.3 the budget will not hold. `SCOPE.md` asks for a decision record and an equal deletion to raise it.
- **ADR 0005 still waits for acceptance**, now with the amendments of tasks 2.2 and 2.3.

Decisions from task 2.1, taken by the maintainer on 2026-11-25:

- P12's check line changed to say what `cg.py tier` does, and the human answers for the data (item 17 above, ADR 0005 under "Tier").
- This repository is set up for `/cg`, with the maintainer's yes of 2026-11-26: `core` is the one expected pack, and the two data files found (`.cg-docs/token/workflow-costs.csv` and the gate's toy survey) are recorded as Public, the maintainer's classification. `.cg-docs/config.json` holds no approved tool and no level names, so nothing about an organization's rules is in this public repository. `.cg-docs/verification.md` is a draft: Run and Doctor are "not found", and the outputs map names the checks of `CONTRIBUTING.md` and the gate rerun. Status says `phase: ready`. It also counts 31 open version 1 artifacts and names a version 1 plan as `active`; the first `/cg` here will meet them.

Decisions taken in task 1.3 that a reviewer should check (each is also in #219):

- The guide keeps `disable-model-invocation: true`, and its description says it is only for a human who types `/cg`. Where a host ignores the flag, section 2 of the guide makes a model-started guide report the state and stop.
- Setup writes three more keys into `.cg-docs/config.json` than `cg.py status` reads: `classification-levels`, `approved-tools` and `contacts`, which P12 asks setup to record. It writes the verification profile P4 asks for as `.cg-docs/verification.md`. Nothing reads these four yet.
- Setup reads each installed pack's lead skill for the settings it takes, so core names no pack's setting. It finds the lead skill's folder with `cg.py packs --json`.
- A quick work report starts as `status: in-progress` and ends as `completed`. Both are in the lists `cg.py` already has.
- Evidence digests in quick work come from `git hash-object`, which every supported machine has.
- In an R package, setup adds `.cg-docs`, `AGENTS.md` and `CLAUDE.md` to `.Rbuildignore`.
- The glossary gained one term, pointer block. Task 2.2 added three: intent, grilling and assumption. Task 2.3 added one: amendment.
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
