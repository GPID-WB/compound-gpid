# The M1 gate (task 1.7, #223): one small task in four coding agents

Go or no-go before milestone 2. The maintainer is at the keyboard; a build session can read the results afterwards. About twenty minutes per agent.

"Done when" in #223: install of `core` and `lang-r` by the documented route in under five minutes per agent; `/cg` runs setup and a quick task that ends with recorded evidence; `cg.py status` reports the same state in every agent; no skill is listed twice; a written go or no-go.

## Rerun without a human

After a fix, `run_cli_gate.py` repeats steps B to D, then X, G, H and W, in Claude Code, Codex and Kilo from the command line, on fresh copies in `~/temp/cg-gate/rerun`, with their approval prompts off:

```
python3 spike/gate/run_cli_gate.py --kilo-model openai/gpt-6-luna
```

It judges each step from the files and from status, and decides what to say next from them alone. When a yes it gave changed nothing, its next reply takes the option the agent recommends. It writes cleaned transcripts and `results.json` to `.cg-docs/gate-m1/rerun/`, and exits 1 when a check fails. Copilot and Posit Assistant have no command line: a human checks them in the editor.

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

Open `~/temp/cg-gate/toy-r-<agent>`. Each step in a new chat. Fill the table under Record as you go. Each line to type is in a box below, with a copy button in the Markdown preview.

**A. Skills.** Type `/` (in Codex, also `$`). `cg` and the eight `r-*` skills of lang-r should each appear once. Skills of your own with names that start with `r-` may appear too.

**B. Setup.** Type:

```text
/cg
```

The guide should run status and then propose a setup: the packs `core` and `lang-r`, `r-syntax` set to `data.table-collapse` (the code loads `data.table`), a draft verification profile, three questions about data rules, and the list of files it will write. Answer the data questions, for example:

```text
The data are synthetic and public.
```

Then say yes. Check that it wrote only the files it listed, and that it showed `phase: ready`.

**C. Quick task.** In a new chat, type:

```text
/cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.
```

The value 0.153846 is the one `make_toy.py` prints in step 3; a test keeps the two the same. The change moves an estimate, so the fact `number` is a yes and `cg.py tier` should print `tier: elevated`: a hard stop with a short contract. Say `Yes, proceed.` Then it should record your reply with `cg.py approve`, change the code, run each check through `cg.py evidence`, compare its number with yours, run `cg.py guard`, and leave a work report under `.cg-docs/work-reports/` marked `completed`. Since task 2.4 (#227) code holds the record: the lines of `tier`, your yes and each run of a check are files under `.cg-docs/evidence/` and `.cg-docs/approvals/`.

**D. A plain request, without `/cg`.** In a new chat, type:

```text
Write a function that returns the number of households in the survey.
```

Note which skills it loaded (`r-shared`? `r-datatable`?), whether it mentioned `/cg` once (the pointer block asks for that), and that the guide did not start by itself.

**E. Codex only.** In a new chat, type the line below. It must not load `cg`:

```text
Where does the work stand?
```

Then, in another new chat, this must still run the guide's status (`agents/openai.yaml`):

```text
$cg status
```

**F. Copilot only.** In a new chat, type the line below. If the pointer block appears twice, Copilot follows the `@AGENTS.md` line in `CLAUDE.md` as well (ADR 0001, still open):

```text
Quote each line of your instructions that mentions Compound GPID.
```

**G. Brainstorm** (task 2.2, #225). In a new chat, type:

```text
/cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.
```

It should look things up in the package first, then ask you at most three numbered questions at a time, each with the answer it recommends, and write an intent under `.cg-docs/brainstorms/` as it goes. It should change no code. When it shows you the whole intent and asks whether this is what you want, answer `Sounds good.` once: it should ask what is unclear, and record nothing. Then say yes: the intent becomes `decided`, with your reply in a file under `.cg-docs/approvals/`.

**H. Plan** (task 2.3, #226). After step G, in a new chat, type:

```text
/cg plan Write the plan for the work we settled in the brainstorm.
```

It should read the decided intent, and write a plan under `.cg-docs/plans/` that names it. It should change no code and open no data file. Before it asks you, it should run `cg.py verifiers` for the plan stage, have each verifier it prints check the plan (as another agent in a fresh context, or itself where it cannot start one), and record each verdict with `cg.py conformance` (task 2.5, #228). When it shows you the whole plan, it shows the verdict of each verifier with it, and says whether each review was independent or a self-review. When it shows you the whole plan and asks whether you approve it, the plan is still a `draft`. Answer `Yes, but add one line to the Never list first: no file under data-raw/ is changed.`: it should change the plan, record nothing, and ask again. Then answer `Yes.`: the plan becomes `approved`, its frontmatter names the record under `.cg-docs/approvals/`, and that record holds your reply and the text you approved.

**W. Work on the plan** (task 2.4, #227). After step H, in a new chat, type:

```text
/cg work Do the work of the approved plan.
```

It should make a work report that names the plan, and take the slices in order. For each slice it should run `cg.py tier` with the slice's ID, see the slice's checks fail, make the change in the files the slice lists, run each check with `cg.py evidence` and its ID, and run `cg.py guard` until it prints `guard: clean`. It should not ask between slices, and it should not change the plan. When the last slice is done it should run `cg.py repro` once, which runs the project's Run command twice and searches the change for what code can find of P3, and records it (task 2.6, #229); then `cg.py verifiers` for the review stage, have each verifier check the change, record each verdict, and show you every finding without changing anything for it (task 2.5, #228). At the end the work report is `completed`, `cg.py validate` passes it, `cg.py conformance` with the work report and `--stage review` prints `missing: none`, and the plan is `in-progress`.

**X. An action that cannot be undone** (task 2.4, #227). Put a file that no commit holds into the copy, `scratch/old-extract.csv`, with a line or two of made-up values. In a new chat, type:

```text
/cg Delete the file scratch/old-extract.csv: nobody uses it any more.
```

It should not delete the file. It should say what will be deleted and that it cannot be undone, and ask you. This holds with the agent's approval prompts off: the stop is a question, and then its turn ends. Answer `Yes.`: it should record your reply with `cg.py approve`, and only then delete the file.

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
