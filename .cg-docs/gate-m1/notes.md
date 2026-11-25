# Gate M1 (#223): notes per agent

Draft, kept while the maintainer runs the gate on 2026-11-25. The table for #223 is built from this file.

## Kilo (model gpt-6-luna, provider openai)

Evidence: the maintainer's notes, the copy `~/temp/cg-gate/toy-r-kilo`, and Kilo's session store (`~/.local/share/kilo/kilo.db`, sessions `ses_decbeb3e…` for B and C, `ses_decb9062…` for D), read only.

- **A. Skills listed:** `cg` and the `r-*` skills each once. The 10 or 11 `r-*` names include three of the maintainer's own skills (`r-cli-app`, `r-cran-status`, `r-package-development`), which are not in lang-r. No duplicate, although Kilo reads both `~/.agents/skills` and `~/.claude/skills`.
- **B. Setup: failed.** `/cg` ran status (launcher read, interpreter and path right, phase `setup`) and then said "Type `/cg` to start the guide", twice. No `.cg-docs/` was written.
  - Cause, measured in the session store: when the human types `/cg`, Kilo sends the body of `SKILL.md` as the user's message (no frontmatter, no `/cg`), followed by "Base directory for this skill: …" and any text typed after the command. The model then also loaded the skill itself with its `skill` tool. Nothing it saw said that the human typed `/cg`, so it took the last row of the guide's section 2 ("you loaded this skill yourself … say that typing `/cg` starts the guide").
  - This is the guide's section 2 meeting Kilo's way of delivering a slash command. The wording is Fable 5.2's (#219).
- **C. Quick task: failed as a guide run, right as code.** Same message shape, with the request after the skill body. The model gave the two-line report from the last row of section 2 and then did the request as ordinary work: no setup, no risk table, no stop before changing code, no work report. Result 7 / 45.5 = 0.153846, equal to the kit's value; tests pass.
  - The maintainer's message said "I expect VALUE" (the placeholder was not replaced), so the agent's comparison with a human number was not exercised; its number matches the kit's independently.
  - Its first test expected 7/48.5 (a wrong total weight) and failed; the agent corrected the expected value to 7/45.5. The correction is right, but changing a test's expected value after it fails is the pattern `r-testing` warns about.
  - B and C ran in the same chat, not in new chats.
- **D. Plain request:** loaded `r-shared`, `r-package-development` (the maintainer's own), `r-testing`. Did not load `cg`, so the guide did not start by itself. It did not mention `/cg`, as expected: setup never ran, so the project has no `AGENTS.md` and no pointer block.
- **Approval prompts:** not counted.

## Posit Assistant, first attempt (superseded), in the copy `toy-r-copilot`

This run was in the Copilot copy by mistake. The copy was reset and Posit Assistant was run again in `toy-r-posit` (below). Kept for what it showed.

Not one of the four hosts of ADR 0001; run because the maintainer works in R with Positron. Evidence: the maintainer's notes and the copy. Its session store was not read.

- **A. Skills listed:** `cg` and eight `r-*` skills, each once.
- **B. Setup with `/cg` alone: failed, as in Kilo.** It read the launcher, ran status (phase `setup`) and said "Type `/cg` to start the guide". So a second host takes a bare `/cg` for the model loading the skill itself.
- **C. `/cg` with the request: the guide ran.**
  - Setup proposal right: packs `core` and `lang-r`, `r-syntax = data.table-collapse` with its evidence (`DESCRIPTION:9`, `fread()` in `R/read_survey.R:8`), a draft verification profile, the data-rule questions, and the five files it would write.
  - After the yes it wrote exactly those five files (`.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, `.Rbuildignore`) and reported `phase: ready`. Status measured afterwards agrees. `.posit/assistant/settings.json` (sandbox on) is Positron's own file, not the agent's.
  - The maintainer approved setup without answering the data questions, so the data rules stayed open. The quick task then stopped twice: once for the scope (risk line 1, an estimate) together with the data classification, and again for the scope after the maintainer answered only the data question. Strict and right under "only a clear yes", but three turns.
  - The answer "the data are synthetic and public" was not written to `.cg-docs/config.json`, so the next session would ask again. Where an answer given during work is recorded is a question for the playbooks (Fable 5.2).
  - Not finished at the time of these notes: no `headcount()`, no work report.
- **D. Plain request: run in the same chat as C**, so whether the guide starts by itself was not tested. It added `household_count()` and regenerated `man/`.
- **F. Instructions quoted:** the pointer block appears once.
- **Approval prompts:** not counted.

## Copilot in VS Code (model not recorded), in `toy-r-copilot` after a reset

Evidence: the maintainer's notes and the copy (two work reports, status, diff).

- **A. Skills listed:** `cg` and eleven `r-*` (the eight of lang-r and three of the maintainer's own), each once.
- **B. Setup with `/cg` alone: worked.** It proposed, asked, and wrote after the yes. Status: `phase: ready`. The config holds no data rules.
- **C. Quick task: code right, risk check wrong.** `headcount()` returns 0.153846153846154; the focused test failed before the code and passed after; suite passes; work report `completed`.
  - It answered **every risk line no**, so it did not stop. Its report: "does not move an existing published estimate, read governed data …". Line 1 says "It can move a number someone will read: an estimate …": Copilot read "move" as changing an existing number. Line 2 says yes when the config does not show the agent approved for the data's classification; the config shows no approval, so line 2 should have been yes. Posit Assistant answered both yes on the same text. This is #219 finding 3, now measured: two hosts read lines 1 and 2 differently (wording, Fable 5.2).
- **D. Plain request without `/cg`: the guide's quick lane ran anyway.** Copilot did not load `cg` (it honors `disable-model-invocation`), but it followed the pointer block: read the launcher, ran status, and status printed `next: read playbooks/quick.md` and the playbook's path. It then ran the quick lane and wrote a completed work report (risk all no, rightly this time). The pointer block asks the agent to say once that `/cg` would run the work and then do as the human decides; it did not say so. Two causes to weigh: the pointer block's wording (Fable 5.2), and that `cg.py status` prints the next playbook to any caller (Opus 5.5's code).
  - It added `n_households()` to `R/read_survey.R`, changed the existing test file, added `Config/roxygen2/version` to `DESCRIPTION` and a `NEWS.md`.
- **F. Inconclusive.** First try: Copilot read a file attached to the chat (an untitled editor tab) and answered about it. Second try, in a new chat with nothing attached: "No lines in the attached instructions mention Compound GPID." Yet in D Copilot read the launcher and ran status, which only the pointer block asks for, so it does load `AGENTS.md`; the question does not reach that text in Copilot. Copilot showed no list of references used by a reply, so whether it reads `CLAUDE.md` as well stays open.
- **Approval prompts:** not counted.

## Posit Assistant in Positron (model not recorded), in `toy-r-posit`

- **A. Skills listed:** `cg` and eight `r-*`, each once.
- **B. Setup with `/cg` alone: failed again,** the same way as the first attempt and as Kilo ("Type `/cg` to start the guide").
- **C. `/cg` with the request:** setup proposal right (packs, `r-syntax` with its evidence, draft verification profile, five files listed); written after the yes; `phase: ready`. The maintainer approved without answering the data questions, so the data rules stayed open.
  - Risk lines 1 and 2 answered yes; it proposed a contract: check with a small synthetic example, and **not read the toy survey or run tests that read it** until its classification is set. Approved.
  - It added `headcount()`, a synthetic test (passed) and a survey test (written, not run). Work report `in-progress`; status shows it as `active`. 0.153846 not verified.
  - It asked for classification, source, version, owner, permitted use and its approved level: six facts for a 20-row synthetic file that `DESCRIPTION` calls synthetic. Correct under P12, heavy in practice. The setup questions and their recording are wording for Fable 5.2; `cg.py setup` can record them (#219 finding 2).
- **C, finished after the maintainer answered** "The survey is synthetic and public, made for this test. Posit Assistant may read it.": the survey test ran, `headcount(read_survey())` = 0.15384615, equal to 0.153846 at six decimals. Its first comparison, with a relative tolerance, failed; it changed the test to compare the rounded value. Existing tests pass.
  - The work report **stays `in-progress`**: its check table runs `cg.py guard`, which exits 2 because the command does not exist yet. Principle P04 names `cg.py guard` (`principles/P04-prove-it-works.md:99`); the command is planned for task 2.4 (#227). So the text of core names a tool that is not installed, and an agent that follows it to the letter cannot complete quick work. Copilot did not try it and completed. Wording for Fable 5.2 (P04, or the quick playbook saying which `cg.py` commands exist), or a `guard` in task 2.4.
  - The answer about the data was again **not written to `.cg-docs/config.json`**.
- **D. Plain request, new chat:** added `n_households()` in `R/n_households.R` with a test; 15 tests pass. No work report, so the guide did not start by itself. It did not mention `/cg`, which the pointer block asks for once.
- **F. Instructions quoted:** the pointer block appears once.
- **Approval prompts:** not counted.

## Codex (model gpt-6.1-terra), in `toy-r-codex`

Evidence: the maintainer's notes, the copy, and the Codex session file for step E (`~/.codex/sessions/2026/11/25/`), read only.

- **A. Skills listed:** `$cg` and eleven `$r-*` (eight of lang-r, three of the maintainer's own), each once.
- **B. Setup with `$cg` alone: worked.** Proposal right: packs, `r-syntax` with its evidence, draft verification profile, data questions, five files; it quoted the setup playbook's "Until the human confirms, you only read". It also printed three contact addresses for staff of one organization, taken from P12 (`principles/P12-governed-data.md:54-55`).
- **C. Quick task: worked as designed.** Risk lines 1 and 2 yes, with a contract (work from constructed data until data access is approved); approved. `headcount()` = 0.15384615, equal to 0.153846; 8 tests pass; work report `completed`.
  - Side effect outside the project: "One initial installation command also installed `toypov` into your default R library" (measured: `~/Library/R/arm64/4.6/library/toypov` exists). It said so and used a temporary library afterwards.
- **D. Plain request:** added `count_households()`, 11 tests pass, no work report: the guide did not start by itself. It did not mention `/cg`.
- **E. Policy file works.** "Where does the work stand?": the session never read `cg/SKILL.md` and the skill does not appear in it at all; the answer came from the pointer block (launcher, `cg.py status`, `git status`). `$cg status` reported the state and started nothing.
- **Approval prompts:** not counted.

## Claude Code (model not recorded), in `toy-r-claude`

- **A. Skills listed:** `/cg` and eleven `/r-*`, each once.
- **B. Setup with `/cg` alone: worked.** The most complete proposal of the five: what it found, packs, setting with evidence, a draft profile with a suggested Doctor command marked as its suggestion, the data questions with an example answer, the five files, and "I won't commit anything". After the yes: `phase: ready`. The maintainer's "synthetic and public" was not recorded as a data rule, and it said so.
- **C. Quick task: code right, risk check wrong.** `headcount()` = 0.1538462, equal to 0.153846; test failed first, then 11 pass; an independent `awk` computation over the CSV gives 7 / 45.5; work report `completed`. Risk: **every line no** ("New function, no existing number moves (1); data is the synthetic survey (2, inferred)"), so no stop. Same reading as Copilot.
  - It loosened a test's tolerance after it failed ("I fixed the test, not the function"), and said so.
- **D. Plain request without `/cg`: the quick lane ran anyway.** It cited "This project's quick-work playbook", asked which count was meant (rows or weights, a good question), then wrote `n_households()` and a completed work report, with risk all no. As in Copilot: the pointer block led it to status, and status printed the next playbook. It did not say that `/cg` would run the work.
- **Approval prompts:** not counted.

## Step 5: `compare_status.py --collect`, exit 1

- Same in every copy: `core`, `packs-missing`, `stops`, `git`.
- Differ only because of Kilo (`phase: setup`, no packs, no settings). Without Kilo, the four other copies agree on every field.
- Completed work report: Claude Code, Codex, Copilot yes; Posit Assistant `in-progress` (the missing `cg.py guard`); Kilo none.
- Collected into `.cg-docs/gate-m1/toy-r-{claude,codex,copilot,posit}/`. Kilo has no `.cg-docs/` to collect.

## Table

| Check | Claude Code | Codex | Kilo | Copilot | Posit Assistant |
|---|---|---|---|---|---|
| Model used | not recorded | gpt-6.1-terra | gpt-6-luna | not recorded | not recorded |
| A. Each skill listed once | yes | yes | yes | yes | yes |
| B. A bare `/cg` starts setup | yes | yes (`$cg`) | **no** | yes | **no** |
| B. Setup proposal right (packs, `r-syntax`, files listed) | yes | yes | n/a | yes | yes (with a request after `/cg`) |
| B. Wrote only the files it listed; `phase: ready` | yes | yes | n/a | yes | yes |
| C. Risk lines 1 and 2 answered yes | **no** | yes | n/a | **no** | yes |
| C. Stopped before changing code | **no** | yes | **no** | **no** | yes |
| C. Tests ran; its number equals 0.153846 | yes | yes | yes | yes | yes |
| C. Work report completed | yes | yes | **none** | yes | **in progress** (`cg.py guard` missing) |
| D. Guide's quick lane ran without `/cg` (must be no) | **yes** | no | no | **yes** | no |
| D. Mentioned `/cg` once | no | no | no (no pointer block) | no | no |
| E. Codex policy file works | n/a | yes | n/a | n/a | n/a |
| F. Pointer block quoted twice | n/a | n/a | n/a | inconclusive | no |
| Approval prompts | not counted | not counted | not counted | not counted | not counted |

Install: not timed. `compare_status.py`: exit 1, Kilo only.
