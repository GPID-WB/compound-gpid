# The M1 gate (task 1.7, #223): one small task in four coding agents

Go or no-go before milestone 2. The maintainer is at the keyboard; a build session can read the results afterwards. About twenty minutes per agent.

"Done when" in #223: install of `core` and `lang-r` by the documented route in under five minutes per agent; `/cg` runs setup and a quick task that ends with recorded evidence; `cg.py status` reports the same state in every agent; no skill is listed twice; a written go or no-go.

## What stays and what is thrown away

- **Stays (a real install):** the hub clone in `~/compound-gpid`, the skills `cg` and `r-*` in `~/.agents/skills` with their links in `~/.claude/skills`, and `~/.cg/` (the install record and the launcher). This is the install the pilot uses. To take it all away: `python3 ~/compound-gpid/install.py --uninstall`, then delete `~/compound-gpid`.
- **Thrown away:** the four toy copies in `~/temp/cg-gate`. Delete that folder once the evidence is collected (step 8).

## Before

1. **Get the hub by the documented route** (`docs/install-block.md`), outside any synced folder. Start a timer.

   ```
   git clone --branch v2 https://github.com/GPID-WB/compound-gpid ~/compound-gpid
   ```

   If `~/compound-gpid` exists already, run `git -C ~/compound-gpid pull` instead.
2. **Install, and stop the timer.**

   ```
   python3 ~/compound-gpid/install.py --packs core,lang-r          # Windows: py -3 ...
   ```

   Note the minutes and whether `cg.py doctor`, at the end, printed any `FAIL`. Notes about version 1 do not affect the gate.
3. **Make one copy of the toy project per agent:**

   ```
   python3 ~/compound-gpid/spike/gate/make_toy.py
   ```

   It makes `~/temp/cg-gate/toy-r-claude`, `-codex`, `-kilo` and `-copilot`, each a git repository with one commit, and prints **the value to give the agent** in step C. The toy is a tiny R package that reads a synthetic survey (`inst/extdata/survey.csv`, 20 made-up households). Its data are public.
4. Quit and reopen each coding agent so it sees the new skills.

## In each agent, in its own copy

Open `~/temp/cg-gate/toy-r-<agent>`. Each step in a new chat. Fill the table under Record as you go.

- **A. Skills.** Type `/` (in Codex, also `$`). `cg` and the eight `r-*` skills should each appear once.
- **B. Setup.** Type `/cg`. The guide should run status and then propose a setup: the packs `core` and `lang-r`, `r-syntax` set to `data.table-collapse` (the code loads `data.table`), a draft verification profile, three questions about data rules, and the list of files it will write. Answer the data questions (for example: "the data are synthetic and public"), then say yes. Check that it wrote only the files it listed, and that it showed `phase: ready`.
- **C. Quick task.** Type, with the value from step 3:

  > /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect VALUE.

  The change moves an estimate, so line 1 of the quick lane's risk table should be yes: a hard stop with a short contract. Say yes. Then it should change the code, run the tests, compare its number with yours, and leave a work report under `.cg-docs/work-reports/` marked `completed`.
- **D. A plain request, without `/cg`:** "Write a function that returns the number of households in the survey." Note which skills it loaded (`r-shared`? `r-datatable`?), whether it mentioned `/cg` once (the pointer block asks for that), and that the guide did not start by itself.
- **E. Codex only:** "Where does the work stand?" must not load `cg`, and `$cg status` must still run (`agents/openai.yaml`).
- **F. Copilot only:** ask "Quote each line of your instructions that mentions Compound GPID." If the pointer block appears twice, Copilot follows the `@AGENTS.md` line in `CLAUDE.md` as well (ADR 0001, still open).

Count the approval prompts in each agent, with its default settings.

## After

5. **Compare the four copies and collect the evidence.** Run this once, after all four agents are done, in a terminal outside the agents, from the root of the checkout where the gate's evidence will be committed (the one you build in), then read the exit code on its own line:

   ```
   python3 spike/gate/compare_status.py --collect
   echo $?
   ```

   It runs status on all four copies with the installed `cg.py`, says which fields differ (they should not), checks that each copy has a completed work report, and copies each copy's `.cg-docs/` into `.cg-docs/gate-m1/` of that checkout. Exit code 0: the copies agree.
6. Fill the table below and post it on #223 with the go or no-go and why.
7. Commit `.cg-docs/gate-m1/`.
8. Delete `~/temp/cg-gate`.

## Record

Copy this table into #223 (step 6), fill it, and end with the go or no-go and why.

| Check | Claude Code | Codex | Kilo | Copilot |
|---|---|---|---|---|
| Model used | | | | |
| A. Each skill listed once | | | | |
| B. Setup proposal right (packs, `r-syntax`, files listed) | | | | |
| B. Wrote only the files it listed; `phase: ready` | | | | |
| C. Risk lines answered yes | | | | |
| C. Stopped before changing code | | | | |
| C. Tests ran; its number equals yours | | | | |
| C. Work report completed | | | | |
| D. Skills loaded for a plain R request | | | | |
| D. Guide started by itself (must be no) | | | | |
| E. Codex policy file works | n/a | | n/a | n/a |
| F. Pointer block quoted twice | n/a | n/a | n/a | |
| Approval prompts | | | | |

Install time: ___ minutes. `compare_status.py`: ___ (exit code).
