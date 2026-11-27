---
name: quick
derived-from: "cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/feature.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/bug-fix.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md; addyosmani/agent-skills@e997ac5:skills/context-engineering/SKILL.md; v1:.github/prompts/cg-light-work.prompt.md"
---

# Quick work

**You own this piece of work from the request to the evidence: restate, check the risk, change, prove, record.** Quick work has no hard stop unless step 2 finds a reason for one. It always leaves evidence.

Work on an approved plan is not quick work: `playbooks/work.md` takes a plan slice by slice.

## 1. Restate

Say in one or two sentences what the human asked for and the smallest change that meets it (P6). Name what you will leave alone. If the request can be read two ways, ask which is meant. Do not pick one.

If status shows an open work report under `active`, read it first. When the request is that work, continue in that file. When it is other work, name what is open in one line, leave it as it is, and go on with the request. Open work of another request does not hold this one back: not an open work report, and not a draft or a stop of other work that status lists under `waiting-on-human`. When the human says that open work is not to be finished, close it as step 5 says. If the human gave no request and nothing is open, ask what they want done and end your turn.

When the request is a slice of an approved plan, or work that an approved plan describes, this playbook does not do it: run the status line again with `--playbook work` added, and follow the playbook it names.

For new work, create the work report before anything is checked or changed. It is the record of this work, and code writes into it from here on:

`"<python>" "<cg>" new work-report "<short title>" --project "<project root>"`

Write the request and your restatement under "Asked".

## 2. Check the risk

Look at the files the change will touch, and open no data file to do it: until the `data` line of `tier` below calls a file `cleared`, or names the human's decision that you read it, you look at its name and at the code that reads it, never at its contents. That holds for a file you are asked to delete or to move, too. Then answer each fact below with yes or no. Find the answers in the files and in the status output, and ask the human only for what they alone know. Answer from what the change does, not from how small it looks: each no needs a reason you can write in the record.

| Fact | It is a yes when the change |
|---|---|
| `number` | computes a number someone will read, or can change one. New code that computes an estimate or a count is a yes, even when no number existed before. So is a change to a weight, a sample, a filter, a merge, a method or a unit of measure, or to the values in a table, a figure or a published dataset. A change to a label, a title, a colour or a layout that leaves every value and its unit of measure as it was is a no. |
| `personal` | touches personal data, credentials or access rights. |
| `irreversible` | deletes or overwrites data, or does something that cannot be undone: a push to a shared branch, a release, a publication, a message sent. |
| `interface` | adds or upgrades a dependency, or alters a function, a file format or a column that other code or other people rely on. |
| `choice` | needs a choice between real alternatives that the human has not made. |
| `no-check` | cannot be checked: you can name no check that would fail if the change were wrong. |

Code computes the tier from your answers. It also counts the files, and it decides from the data rules in `.cg-docs/config.json` whether this coding agent may read each data file. Run:

`"<python>" "<cg>" tier --fact number=<yes or no> --fact personal=<yes or no> --fact irreversible=<yes or no> --fact interface=<yes or no> --fact choice=<yes or no> --fact no-check=<yes or no> --touches "<file>" --reads "<data file>" --agent "<this coding agent>" --report "<the work report>" --project "<project root>"`

Code writes what the line prints into a record of the work report, so copy none of it. Give `--touches` once for each file the change will create, change or delete, also a file that a tool writes as part of the change, such as a generated help page. Give `--reads` once for each data file you will open, or that code you run will read. When there is none, give `--reads none` and leave out `--agent`. Name this coding agent as setup recorded it. Only a recorded rule clears a data file: "synthetic" or "public" written in a README, a comment or a file name is a description, not a classification.

**`tier: low`.** Go on to step 3 without waiting.

**`tier: elevated`.** This is a hard stop. Tell the human each reason on the `reasons` line. Then give a short contract: the goal, what is out of scope, and the checks you will run with the outcome that would mean failure. Write it under "Risk" in the work report first, and show it as the file reads. When a reason is `irreversible`, it names what will be done that cannot be undone, and to which file or place. When a reason is `data`, ask in the same reply for what would clear the file, with an example answer the human can copy: its classification, and the highest level their organization lets this coding agent read. Say how you will work without seeing the data if they cannot answer yet (P12). The human answers for the data, so say too that they may decide you read the file as it stands, that reading it sends its contents to the company that runs the model, that their organization's rules still bind them, and that code records the decision under their name when they reply with a plain yes. With a `data` reason, the data is the one thing you ask for in this reply: the yes to the contract is asked for once the data is settled. With no `data` reason, say for the contract that a plain yes confirms it and is recorded under their name, and that you will take anything else as a change or a question. End your turn. When a reason is `size`, say that the work needs a plan, which `/cg plan` writes once `/cg brainstorm` has settled what is wanted, and offer the first slice that is small enough to do now. When a reason is `choice`, put the choice to the human in the same reply, with the answer you recommend and its trade-off. If one question cannot settle it, say that `/cg brainstorm` works it through before anything changes.

**A stop with a `data` reason keeps this order.** First the data: the human's classification of the file, or their decision that you read it, each recorded as the paragraphs below say; or the file is left out of the work. Then `tier` again. Then, when `tier` is still elevated, the contract and the question for its yes, in a reply of its own. A yes to the contract opens no data file: code refuses it while the `stop` line names one.

**When the human says yes to the contract,** record the reply before you change anything. Show the line, then run it:

`"<python>" "<cg>" approve "<the work report>" --reply "<the human's reply, word for word>" --project "<project root>"`

If it prints `refused`, nothing was recorded and nothing changes. The reason says what kind of reply it was and what to ask next. When the human said no and asks for no change, that is their answer: do not ask again, and close the work as step 5 says. A stop holds for the facts and the files you gave `tier`: when you run `tier` again and it is still elevated, the stop is a new one.

**When the human answers a data question,** here or later in the work, record the answer before you go on, so that no later session asks again. Show the line, then run it:

`"<python>" "<cg>" setup --data "<file or folder>=<level>" --approved-tool "<this coding agent>=<level>" --project "<project root>"`

Record only what the human stated, in their words for the level, such as `Public`. A rule for a folder covers every file under it. Leave out `--approved-tool` when they did not say what this coding agent may read. "Synthetic" or "test data" is a description, not a level: ask which level it is. Then run `tier` again and read its `data` line. An answer about the data is not a yes to the contract.

**When the human decides that you read a file that is not cleared,** record their reply before you open the file. Give `--reads` the place the human named and nothing wider: the file when they named a file, a folder only when they named the folder. Show the line, then run it:

`"<python>" "<cg>" approve --reads "<file or folder>" --agent "<this coding agent>" --reply "<the human's reply, word for word>" --project "<project root>"`

If it prints `refused`, nothing was recorded and the file stays closed. Read the reason it gives. When the human declined, that is their answer: work without the data, and do not ask again. When the reply says more than a plain yes, deal with what it adds or asks, then ask for a plain yes. When it holds no yes, ask one question: what is unclear. When git has no user name, show the human the line the command printed.

Once the decision is recorded, run `tier` again. Its `data` line names the decision, and the file no longer raises the tier. The decision lets you read the file. It is not a yes to the contract: when `tier` is still elevated, show the contract and ask for its yes before you change anything. Rows and values still stay out of the work report, the evidence and every commit.

## 3. Change

- Before you write code, read the lead skill of each pack on the `packs-expected` line of status. `"<python>" "<cg>" packs --json` gives each lead skill's folder as `path`. Follow what it says about which of its pack's skills to load for this work, and load them.
- Before you change code that already produces an output, capture the baseline: the current value or digest of each output the change may move (P4).
- Make the change, and only that change. Unrelated things you see go on a "Noticed but not touching" list (P6).
- When one operation applies to many units, do one worked example, write the tool, show that the tool gives the outcome of the worked example, and only then run it on the rest (P3). Nothing that reaches a reader is typed in.
- Check a function name or an argument you are not sure of in the package's documentation before you use it (P7).
- Fail loudly: missing data, a null weight or an unmatched merge raises an error, never a silent fallback (P10).
- If the change grows beyond what you restated, or a fact in step 2 turns to yes, stop and return to step 2.

## 4. Prove

- Run each check through code, which records that it ran: its command, its exit code, a digest of what it printed, and the commit. Put the command in single quotes when it holds double quotes. Code keeps the text of the command in the record, which is committed: write no value and no name from a dataset into it. What the check needs of them goes into a file that the command reads. Show the line, then run it:

  `"<python>" "<cg>" evidence --run "<the check's command>" --report "<the work report>" --project "<project root>"`

- Where you can, see each check fail before the change and pass after it. Check the real output, not a step on the way to it.
- For a number that changed, compare it with something independent of the code: a reference value, a published figure, or what the human said they expected before the check ran (P4). Compare at the precision the value was given in: 12.4 is right to one decimal and says nothing about the second. Set that tolerance before the first run.
- When a check fails, fix the code, not the check. Change an expected value or a tolerance only when a source independent of the code shows it was wrong, and name that source in the record and in the reply (P4).
- Each check gets one verdict: verified, not verified or inconclusive. Inconclusive is not a pass. Code gives it from the exit code: 0 is verified, anything else is not. When a check ends with 0 and what it printed shows the failure, run the line again with `--verdict not-verified` added, or with `--verdict inconclusive` when the check could not tell.
- Then have code look at the change as a whole:

  `"<python>" "<cg>" guard --report "<the work report>" --project "<project root>"`

  A line that starts with `FAIL` names a test that was removed or skipped, a checker that was silenced, a file you changed and did not give to `tier`, or that no check is verified on the files as they now are. Fix the change, and never the finding. For a file you did not give to `tier`, return to step 2. When a finding is what the human asked for, such as a test that goes with the code it tested, show it to them and let them decide.
- Read the Verifier section of P3, P4 and P6 in `principles/`, and judge your own change against each. This is a self-review, and the record says so.

## 5. Record

Fill every section of the work report. Code holds the commands, the exit codes, the verdicts and the digests, and the report holds what code cannot record. Neither ever holds data.

Set `status: completed` when every check you named for this change, in step 2 or in the contract, ran through `evidence` and is verified. With no verified check, the work is not completed, and code fails a report that says it is. Otherwise leave `status: in-progress` and say so in the reply, so that status keeps showing the work as open.

**Work that will not be finished.** When the human says that the work is not to be finished, or says no at the hard stop and asks for no change, set `status: dropped` in the work report. Write under "Not checked" which files were changed and left as they are, what was not done, and that the human ended the work, in their words. Leave the rest of the file as it is. Code then counts the work as closed and asks it for no evidence, and status no longer shows it as open or as waiting. Never set it on your own: work that nobody ended stays `in-progress`.

Then have code check the record:

`"<python>" "<cg>" validate "<the work report>" --project "<project root>"`

A line that starts with `FAIL` names what is wrong in the work report. Fix it there and run the line again.

What the project or the install does not have yet is not a failed check: a Doctor or Run command that the verification profile marks "not found", a `cg.py` command that `--help` does not list, a formatter that is not installed. Write each under "Not checked" and say it in the reply. It does not keep the work open. A check you named is the exception: when what it needs is missing, its verdict is inconclusive and the work stays open.

A failure that was there before your change, in something the change did not touch, is not yours either. Show that it was there: run the same check on the unchanged code, or quote the baseline. Put it under "Noticed but not touching". It does not keep the work open. A check you wrote for this change fails on the old code by design, so this rule never covers it.

Commit only when the human asks. Then the work report goes in the same commit as the change (P8).

**Reply:** what was asked, what changed and in which files, each check with its command and verdict, what `guard` printed, any check you changed after it failed with the source that showed it wrong, the self-review verdict for P3, P4 and P6, the path of the work report, what you did not check, and the "Noticed but not touching" list. Label each claim measured, inferred or guess.
