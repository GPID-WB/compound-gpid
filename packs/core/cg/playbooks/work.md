---
name: work
derived-from: "addyosmani/agent-skills@e997ac5:skills/incremental-implementation/SKILL.md; addyosmani/agent-skills@e997ac5:skills/test-driven-development/SKILL.md; addyosmani/agent-skills@e997ac5:skills/constraint-driven-development/SKILL.md; addyosmani/agent-skills@e997ac5:commands/build.toml; mattpocock/skills@d653911:skills/engineering/implement/SKILL.md; mattpocock/skills@d653911:skills/engineering/implement-spec/SKILL.md; mattpocock/skills@d653911:skills/engineering/tdd/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/feature.md; cursor/plugins@ca782ed:pstack/skills/principle-sequence-verifiable-units/SKILL.md; cursor/plugins@ca782ed:pstack/skills/show-me-your-work/SKILL.md; v1:.agents/commands/cg-work.md"
---

# Work

**You own the work on an approved plan, one slice at a time: start the slice, see its checks fail, make the change, prove it, and have code record it.** The plan holds the contract, and you change no word of it. The human approved it once, and that approval carries you from slice to slice without asking again. It never covers an action that cannot be undone, a change to the plan, or what the plan's Ask first list names. Each of those stops the work, as section 5 says.

## 1. Start or resume

Read the plan in full: the contract, the boundaries, the data register and the slices. It is the plan the human named, or the one status shows as `approved` or `in-progress`. When status lists it under `waiting-on-human`, or when no plan is approved, do no work: say that `/cg plan` gets the human's yes first, and end your turn.

The work report is the record of this work. Take the first line that fits.

- **Status shows an open work report for this plan.** Continue in that file. Have code say where the work stands:

  `"<python>" "<cg>" evidence --report "<the work report>" --project "<project root>"`

  It lists each record and, for each slice, the verdict of each of its checks. The next slice is the first one with a check that is not `verified`. Take where the work stands from this list, never from the conversation or from a summary of it. When status names the work report under `waiting-on-human`, a stop is not answered yet: go to section 5.
- **There is none.** Create it, and write the goal of the plan under "Asked":

  `"<python>" "<cg>" new work-report "<short title>" --plan "<the plan>" --project "<project root>"`

  If it prints `refused`, nothing was written, and the reason says why: the plan is not approved as it now reads, or the work on it has a work report already.

Then tell the human in two lines which slices are left, and that you stop only where section 5 says.

## 2. Start a slice

Take the next slice in the plan's order, and no other. Finish it, with its checks verified, before the one after it starts (P4). Say which slice it is, what it delivers and which files it may touch. Then have code record the start of the slice and compute what is risky in it. Answer the six facts for this slice alone, as step 2 of `playbooks/quick.md` defines them:

`"<python>" "<cg>" tier --fact number=<yes or no> --fact personal=<yes or no> --fact irreversible=<yes or no> --fact interface=<yes or no> --fact choice=<yes or no> --fact no-check=<yes or no> --slice "<slice ID>" --reads "<data file>" --agent "<this coding agent>" --report "<the work report>" --project "<project root>"`

Code takes the files from the slice. Give `--reads` once for each data file you will open, or that code you run will read. When there is none, give `--reads none` and leave out `--agent`. Then read the line `stop`.

- **`stop: none`.** Go on to step 3 without waiting. Whatever else the `reasons` line holds, the human approved with the plan.
- **`stop:` with a reason.** Go to section 5, rule 1, before anything else.

A dataset that the `data` line calls `not cleared` stays closed, in the way the plan says: you never open it, and a check reports an exit code or a count and never a row (P12). When the human decides that you read it, step 2 of `playbooks/quick.md` says how that reply is recorded before the file is opened.

## 3. Change

- Before the first slice, read the lead skill of each pack on the `packs-expected` line of status and load what it names, as step 3 of `playbooks/quick.md` says.
- **See the slice's checks fail first.** Run each check the slice ends in, as step 4 writes it, before the change. A check that fails now and passes after the change proves the change. A check that passes before the change proves nothing for this slice, unless it is a baseline or a pin, whose job is to stay the same. When it is neither, the plan is wrong: section 5, rule 3.
- Before you change code that already produces an output, capture the baseline the plan names.
- Make the change this slice describes, in the files it lists, and nothing else (P6). What you see beside it goes on the "Noticed but not touching" list of the work report.
- When the slice is a worked example, show each step and its outcome. When it is the tool, show that the tool gives the outcome of the worked example before it runs on the other units (P3). Nothing that reaches a reader is typed in.
- Check a function or an argument you are not sure of in the documentation of the package version the project uses, and name the page (P7).
- Fail loudly: missing data, a null weight or an unmatched merge raises an error, never a silent fallback (P10).

## 4. Prove

Run each check the slice ends in through code. It runs the command the approved plan declares for that check, as the plan writes it, and records that it ran: the command, the exit code, a digest of what it printed, and the commit.

`"<python>" "<cg>" evidence "<check ID>" --report "<the work report>" --project "<project root>"`

- Code gives the verdict from the exit code: 0 is `verified`, anything else is `not verified`. Read what the check printed against the plan's "Fails when". When a check ends with 0 and its outcome means failure, run the line again with `--verdict not-verified` added, or with `--verdict inconclusive` when the check could not tell. Inconclusive is not a pass.
- Never get a check to pass by making it easier: no change to its command, to an expected value or to a tolerance, no test removed or skipped, no warning or error silenced. When a check fails, fix the first place in the code where things went wrong.
- A command of your own goes through `evidence --run`, as step 4 of quick work writes it. Code labels it ad hoc, and it never stands for a check of the plan.
- For a number, compare it with what the plan names as independent of the code, at the tolerance the plan set, and write what it was compared with under "Evidence" in the work report (P4).

Then have code look at the slice as a whole:

`"<python>" "<cg>" guard --report "<the work report>" --project "<project root>"`

A line that starts with `FAIL` names a test that was removed or skipped, a checker that was silenced, a file that changed and that the slice does not list, or a check of the slice with no verified evidence on the files as they now are. Fix the change, and never the finding. The slice is done when the line prints `guard: clean`. Write its files into the "Changed" table of the work report, and start the next slice at step 2 without asking.

## 5. Stop rules

Each rule below stops the work, whatever the plan says and however far the work is. A stop is a question in your reply, and then you end your turn. The coding agent's own approval settings are not the human's yes: where they are off, this section is all that stands between you and the action.

1. **An action that cannot be undone. This is a hard stop, each time.** It holds when the plan names the action, and when the human asked for it a moment ago. The actions: deleting or overwriting data, or a file that no commit holds; a push or a merge into a shared branch, a tag or a release; publishing a dataset, a report, a package or a dashboard; sending a message, an email or a comment to anyone; changing credentials or access rights; changing a database or a store outside the project. Before the action, declare it: run the `tier` line of step 2 with `irreversible=yes`. Write under "Risk" in the work report what exactly will be done, to what, and why it cannot be undone. Show that to the human as the file reads. Say that a plain yes lets this one action go ahead and is recorded under their name, and that you will take anything else as a change or a question. Then end your turn. When they answer, record the reply before you act. Show the line, then run it:

   `"<python>" "<cg>" approve "<the work report>" --reply "<the human's reply, word for word>" --project "<project root>"`

   If it prints `refused`, nothing was recorded and the action does not happen: the reason says what to ask next. Until a yes is recorded, code runs no check for this work. The yes covers that one action, and the next one stops again.
2. **A check that will not pass.** After two attempts to fix the code, stop. Say what you tried, what the check printed, and where you think the fault is.
3. **The plan has to change.** The slice needs a file it does not list, a check or its tolerance is wrong, a requirement cannot be met as written, or the work needs a decision the plan does not hold. Say what and why, and end your turn. The human decides, and `/cg plan` writes the amendment they approve. Code runs no check of a plan that was changed without it.
4. **Ask first.** Whatever the plan's Ask first list names, each time it comes up.
5. **A finding of `guard` that the plan asks for,** such as a test that goes with the code it tested. Show it, and let the human decide. Write their answer under "Not checked".

## 6. Close

When every slice is done, read the Verifier section of P3, P4 and P6 in `principles/`, and judge the whole change against each. Fill the "Self-review" table of the work report. This is a self-review, and the record says so.

<!-- PLACEHOLDER: written in task 2.5. The self-review above stands in for the dispatch of the `determinism`, `verification` and `simplicity` verifiers, each in a fresh context, on the change, the evidence and the approved contract. -->

Fill every other section of the work report. Set `status: completed` only when every check of the plan is `verified`: code fails a work report that says so without the evidence. Then have code check the record:

`"<python>" "<cg>" validate "<the work report>" --project "<project root>"`

A line that starts with `FAIL` names what is missing. Fix it and run the line again. The plan stays `in-progress`: the work is proven, and nobody has reviewed it or signed it off yet.

Commit only when the human asks, or when the plan's Always list says that each slice is committed. Run `guard` before the commit, which leaves it nothing to compare. The change, the work report and its records under `.cg-docs/evidence/` and `.cg-docs/approvals/` go in one commit (P8). A push is rule 1.

**A slice in a fresh context.** When the coding agent can start another agent, you may give it one slice. The first line of its kickoff is the one the guide gives, which sends it to `worker.md`. After it, give pointers and none of your reasoning: the plan, the slice, the files it lists and the checks it ends in. That agent makes the change and reports. You run `tier` before it starts, and `evidence` and `guard` after it reports. The record is yours, and so is every stop.

**Reply:** the plan and the work report, each with its status; each slice that is done, with its checks and their verdicts as `evidence` lists them; what `guard` printed for the last slice; each stop, with what you asked and what you are waiting for; each finding the human decided on; the self-review verdict for P3, P4 and P6; what you did not check; the "Noticed but not touching" list; and the slices that are left. Label each claim measured, inferred or guess.

<!-- PLACEHOLDER: written in task 2.9. The review playbook takes the proven work next. Until then the work ends with the plan `in-progress`. -->
