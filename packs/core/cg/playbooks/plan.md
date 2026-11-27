---
name: plan
derived-from: "addyosmani/agent-skills@e997ac5:skills/spec-driven-development/SKILL.md; addyosmani/agent-skills@e997ac5:skills/planning-and-task-breakdown/SKILL.md; mattpocock/skills@d653911:skills/engineering/to-spec/SKILL.md; mattpocock/skills@d653911:skills/engineering/to-tickets/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/multi-phase-plan.md; cursor/plugins@ca782ed:pstack/skills/architect/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-foundational-thinking/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-sequence-verifiable-units/SKILL.md; v1:.agents/commands/cg-plan.md"
---

# Plan

**You own the plan, and none of the work in it: read the intent, write the contract, cut the slices, have the plan checked, and put it to the human.** The plan is what the human approves and what the work is later held to. This playbook changes no file outside `.cg-docs/` except the project's `GLOSSARY.md`, opens no data file, and runs none of the project's code. It ends in a hard stop: the human's yes to the plan as the file reads.

Read `grilling.md` in full before your first question. It is beside the guide's `SKILL.md`. It says how a fact is looked up, how a decision is put to the human, and which replies are not a yes.

## 1. Start or resume

A plan is built on a decided intent: the record of what the human wants, what is out of scope and what a wrong result looks like. Status names under `ready-to-plan` each decided intent that no plan is built on yet. Read each of them, each other intent under `.cg-docs/brainstorms/` whose status is `decided`, and each plan under `.cg-docs/plans/` with `schema: 2` that is not finished. Then take the first line below that fits.

- **A plan for this work is a `draft`.** Continue in that file from where it stands. Never start a second plan for the same work, and never write a new text over an unfinished plan.
- **A plan for this work is `approved` or `in-progress`.** It is frozen: progress goes into the work report, never into the plan. When the human asks for no change to it, say where it stands and end your turn. A change they ask for is an amendment. Change only what has to change, and add a line under a heading `## Amendments` at the end of the plan: `- <today's date, as YYYY-MM-DD>: <what changes, and why>`. Keep the earlier lines. Make the change through the steps it touches, 3 to 5, then go to step 6. The human approves the amended plan, and the record of each earlier approval keeps the text they approved then.
- **No decided intent covers what the human asks for.** Write no plan from the conversation. Say that `/cg brainstorm` followed by the request settles first what is wanted, name what you see as still open, and end your turn.
- **Otherwise** create the plan on the intent:

  `"<python>" "<cg>" new plan "<short title>" --intent "<the decided intent>" --project "<project root>"`

If it prints `refused`, nothing was written, and the reason says why. When it names a plan that is not finished, read that plan. The same work goes on in that file. For other work, ask the human whether the new plan stands beside the unfinished one, or whether that one is finished first or dropped, and end your turn. Add `--other-work` to the line only after they said that it stands beside it. When they drop the old plan, set its status to `dropped` and leave its text. If the line prints `exists, not overwritten`, a plan of that title was made today: continue in that file, or choose another title.

The plan is the record of the planning. A later session continues from the file, never from the conversation.

## 2. Read before you write

Do not interview the human again. The intent holds their answers: read it in full, with its facts, its decisions and its assumptions, and plan the approach they chose. Then look up what the plan needs and the intent does not hold (P2): the code and the outputs the work will touch, the commands this project is run and checked with in `.cg-docs/verification.md`, the project's `GLOSSARY.md`, and earlier plans and decision records on the same subject. Write the plan in the project's own terms (P11).

Before any step, name the shape of the data (P6, P10): for each dataset, the unit of observation, the key and the columns that matter; for each estimate, the unit of observation, the weights and the population it covers. Take them from the code that reads the data, from the codebook or from the documentation. They go into the plan below the table of the data register, as sentences and never as a table: code reads every table there as datasets.

Writing a plan shows what the intent left open. Handle it by what it changes:

- **The goal, the scope or the approach.** That is a change to the intent, and a decided intent changes only with a new yes. Say that `/cg brainstorm` reopens it, and end your turn.
- **A choice inside the plan that only the human can make,** such as the value they expect from a check, a tolerance, which output proves the work, what needs their yes each time, or the classification of a dataset. Give it a row in the Open questions table of the plan: its ID, the part of the plan it is about, the question, and the answer you recommend with its trade-off. For what the human alone knows, such as a classification, the recommended cell says what the plan does until their answer comes. Put the open rows to the human in rounds, as `grilling.md` says, and end your turn. Until they answer, each place in the plan where the answer goes names the question's ID in brackets, such as `(Q1)`. Code names an unanswered row and such a mark as open, so the plan cannot go to approval with either. Then write their answer into the row, in their words, and what follows from it into each place that named the question. When they have no value to give, ask which check stands in its place.
- **Anything smaller.** Take the simplest reasonable default, and write it in the plan, where the human sees it at the hard stop.

The Open questions table holds the second kind and nothing else. After a brainstorm most plans ask nothing, and the table then has one row that says "none" in each cell.

## 3. Write the contract

The contract is the part of the plan the human approves and the work is held to (P1). Fill each part of the file that `new` made.

- **Goal.** What will be true when the work is done, in terms someone can measure. "Harmonize the welfare variable" becomes "every survey has one welfare column, in 2021 PPP dollars per person per day, with no missing value for a sampled household".
- **Out of scope.** What this work will not do, from the intent, and what is deferred: an idea that is good and that the goal does not need goes here in one line, with the reason, so that it is kept and not built (P6).
- **Requirements.** One thing the work must do in each row. A requirement that needs "and" is two.
- **Checks.** Every requirement has at least one check, and every check can fail (P4). Hold each check to these six:
  1. Its Command cell holds one command, written in full as it will be run, with its arguments, in one pair of backticks: code runs what stands between them, from the project root, and refuses a cell that holds no such text or more than one. Each cell repeats its command, and never says "the C1 command" or "as C1, with one more test". A file name or a note beside the command is plain words, outside backticks. Take the command from the verification profile when the profile has one. It runs on this machine from the project as it stands: the command itself loads the code it tests, needs no program or package the machine lacks, and writes no file into the project outside its slice, such as the folder of `R CMD check`, which `--output` sends elsewhere.
  2. "Fails when" names an outcome someone can observe: an exit code, a value, a count, a difference from a baseline. An outcome that is a matter of opinion is no check.
  3. It looks at the real output and not at a proxy: the number in the final table, the function as its caller calls it. "It runs" and "the file exists" prove nothing.
  4. It would fail if the requirement were not met. A check that already passes on the project as it is today, as far as reading the code shows, cannot fail for this work: replace it. Three kinds of check are the exception, because their job is to show that something stayed the same: a baseline, a pin, and a regression check, such as the project's whole test run. Such a check may pass before the change, and it must still pass after it. A requirement that asks for something new still needs a check that fails today.
  5. For a number, it compares the number with something independent of the code: a reference value, a published figure, or the value the human expects. The tolerance is set now and written in the row.
  6. Its exit code is its verdict: code reads 0 as a pass and anything else as a failure. The exit code of a pipe or of `;` is the last command's, so a command that ends in `| tail -1`, `; grep` or `|| true` passes whatever the check before it did. End the command with the part that judges.

  At least one check must fail on the wrong result the intent names. Below the table, write what no check would catch, or that you know of nothing (P5, P7).
- **Boundaries.** Three lists, written for this work and not copied from another plan. Always: what you do in every slice without asking, such as running the slice's checks, or stopping on a missing weight. Ask first: what needs the human's yes each time, such as a new dependency, a file outside the slice's list, or a change to a check or to its tolerance. Never: what this work does not do, such as printing rows of a dataset, changing a check so that it passes, or publishing.

## 4. Cut the slices

A slice is a small piece of the plan that ends in a check and can be reviewed in one sitting.

- **Cut along the path, not across it.** A slice goes from an input to an output someone can read, for a narrow case: one indicator, one survey year, one table. "All the cleaning, then all the estimates, then all the tables" shows nothing until the last slice.
- **The first slice is the thinnest whole path:** one unit, from the rawest input to the real output, with its check. When one operation applies to many units, that first slice is the worked example, the next one is the tool that gives the same outcome, and only then come the other units (P3).
- **What every later slice needs comes first:** the baseline of an output that may move, the pin of a behavior that must stay, the check that fails until the work is done. Put the slice most likely to fail early.
- **Keep each slice small:** a handful of files, five at most, and one thing delivered. A slice that needs "and" to describe is two. One mechanical change across many files, such as a renamed column, is cut in three: add the new form beside the old one, move the callers in batches, then remove the old form.
- **Order them.** Each slice rests only on the slices above it, and leaves the project working.

Give each row its ID, what it delivers as its reader will see it, the files it may touch, the checks it ends in, and how it is done: by code or by judgement. A slice done by code names the tool: a script, a function, a pipeline target, a check. By judgement is for a step that needs a person or a model to weigh something. A step that would be repeated for each unit is done by code (P3). Every check belongs to a slice.

## 5. Fill the data register

List every dataset the work reads or produces, one row each (P12). When there is none, one row says "none" in each cell.

- **Classification** is the level recorded for the dataset, or for a folder above it: the `data` line of status. Code holds the register to those rules. A level you only type into the plan does not count, and neither does "synthetic" or "public" in a README or a file name. When no level is recorded, for an input or for an output the work will produce, that is an open question of step 2: ask the human for it, with an example answer they can copy, and end your turn. An output made from restricted data keeps that data's level until the data owner says otherwise. Record what the human states before you go on. Show the line, then run it:

  `"<python>" "<cg>" setup --data "<file or folder>=<level>" --approved-tool "<this coding agent>=<level>" --project "<project root>"`

  Leave out `--approved-tool` when they did not say what this coding agent may read.
- **Source, version, owner and permitted use** are facts. Look them up, and ask the human only for what they alone know.

Then have code say which datasets this coding agent may read, and what makes the work risky. Answer the six facts for the work as a whole, as step 2 of `playbooks/quick.md` defines them. Give `--touches` once for each file in the slices, and `--reads` once for each dataset the work reads, or `--reads none` without `--agent` when it reads none:

`"<python>" "<cg>" tier --fact number=<yes or no> --fact personal=<yes or no> --fact irreversible=<yes or no> --fact interface=<yes or no> --fact choice=<yes or no> --fact no-check=<yes or no> --touches "<file>" --reads "<data file>" --agent "<this coding agent>" --project "<project root>"`

A yes to `choice` or to `no-check` means that the plan is not ready: go back to step 2 or to step 3. A dataset that the `data` line calls `not cleared` stays closed. Plan the work so that you never open it: you write and check the code against its codebook or a public sample, a check reports an exit code or a count and never a row, and the Never list names the file. Say so at the hard stop.

The human answers for the data, so they may decide that you read the file all the same. Before they decide, warn them that reading it sends its contents to the company that runs the model, that their organization's rules still bind them, and that code records the decision under their name when they reply with a plain yes. Record that reply before the file is opened, for the place they named and nothing wider. Show the line, then run it:

`"<python>" "<cg>" approve --reads "<file or folder>" --agent "<this coding agent>" --reply "<the human's reply, word for word>" --project "<project root>"`

A decision on data is not a yes to the plan. Change the plan to what they decided, and ask for the plan again.

## 6. Have the plan checked

`"<python>" "<cg>" validate "<the plan>" --project "<project root>"`

A line that starts with `FAIL` or `warn` names what is not ready: a requirement with no check, a check with no outcome that means failure or that no slice runs, a dataset with no recorded level, a question the human has not answered or whose ID still stands where its answer goes, a part of the template that is still unfilled. Fix it in the plan, or settle it with the human, and run the line again. Go on only when it prints `problems: 0` and `warnings: 0`. An amendment is the one exception: its line that no approval is recorded for the plan as it now reads stays until step 7, and nothing else may be left.

Then have the plan checked by the verifiers of the principles a plan is held to. The line below says which verifiers run, and prints the kickoff of each. Run each one and record its verdict as the guide says under "Verifiers". Then run the line printed after `then`: it lists the verdict of each verifier with its findings and the kind of review that gave it, and names under `missing` each verifier that gave none. When the verifiers give findings, fix in the plan each one you can fix, run the `validate` line again, and run the verifiers a second time, all of them, on the plan as it now reads. For each finding you leave as it is, say at the hard stop why. After that second round change nothing more for a finding: it stays in the record with its pointer, and the human decides on it at the hard stop. Go on only when the listing prints `missing: none`.

`"<python>" "<cg>" verifiers "<the plan>" --stage plan --project "<project root>"`

## 7. Approve

This is a hard stop. Show the human the plan as the file reads, and not a summary of it: the contract, with what each check catches and what no check would catch; the slices in order; the data register, with each dataset that stays closed and how the work goes on without it; the Open questions, each with the answer they gave; the `reasons` line of `tier`; and the verdict of each verifier with each of its findings, as the listing of step 6 gives them, whether each review was independent or a self-review, and each verdict the listing marks as given on an earlier text. For an amendment, show first what changed against the text they approved before, which the record the plan names under `approval` holds as `text`. Ask whether they approve the plan. Say that a plain yes approves it and is recorded under their name, and that you will take anything else as a change or a question. Then end your turn.

When they answer, record the reply before anything else. Show the line, then run it:

`"<python>" "<cg>" approve "<the plan>" --reply "<the human's reply, word for word>" --project "<project root>"`

It sets the plan to `approved` and writes the path of the record into the plan. If it prints `refused`, nothing was recorded and the plan is not approved. Read the reason: it names the kind of reply, or the part of the plan that is not ready, and says what to do. A correction is not a yes: change the plan, run step 6 again with one round of every verifier and no fix for its findings, show the part that changed, and ask again. Never set the status yourself. A status typed into the file is not an approval, and code tells the two apart.

## 8. Hand over

Planning ends with the approved plan, not with a change. Do not start a slice in the same turn. Commit only when the human asks: the plan, its intent and their records under `.cg-docs/approvals/` then go into one commit, with `.cg-docs/config.json` when step 5 changed it (P8).

**Reply:** the path of the plan and its status, the goal in one sentence, each requirement with its checks, the slices in order, each dataset that stays closed, each open question with its answer or that it waits, what is deferred, what no check would catch, the verdict of each verifier with the kind of review that gave it and each finding with its pointer, what you did not look up, and what the human can do next: `/cg work`, which takes the plan slice by slice. When the turn ends before the plan is approved, say which step you are at and what you are waiting for. Label each claim measured, inferred or guess.
