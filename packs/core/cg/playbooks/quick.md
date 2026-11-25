---
name: quick
derived-from: "cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/feature.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/bug-fix.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md; addyosmani/agent-skills@e997ac5:skills/context-engineering/SKILL.md; v1:.github/prompts/cg-light-work.prompt.md"
---

# Quick work

**You own this piece of work from the request to the evidence: restate, check the risk, change, prove, record.** Quick work has no hard stop unless step 2 finds a reason for one. It always leaves evidence.

Until the plan and review playbooks are installed, this is the one playbook for work in a project that is set up.

## 1. Restate

Say in one or two sentences what the human asked for and the smallest change that meets it (P6). Name what you will leave alone. If the request can be read two ways, ask which is meant. Do not pick one.

If the human gave no request, ask what they want done and end your turn.

## 2. Check the risk

Look at the files the change will touch. Then answer each line with yes or no. Find the answers in the files, and ask the human only for what they alone know.

| # | Fact about the change |
|---|---|
| 1 | It can move a number someone will read: an estimate, a weight, a sample, a merge, a method, a unit, a table, a figure or a published dataset. |
| 2 | It reads data, and `.cg-docs/config.json` does not show that this coding agent is approved for that data's classification. |
| 3 | It touches personal data, credentials or access rights. |
| 4 | It deletes or overwrites data, or does something that cannot be undone: a push to a shared branch, a release, a publication, a message sent. |
| 5 | It adds or upgrades a dependency, or alters a function, a file format or a column that other code or other people rely on. |
| 6 | It needs more than about five files, or a choice between real alternatives that the human has not made. |
| 7 | You cannot name a check that would fail if the change were wrong. |

**Every answer is no.** Go on to step 3 without waiting.

**Any answer is yes.** This is a hard stop. Tell the human which lines are yes and why. Then give a short contract: the goal, what is out of scope, the checks you will run with the outcome that would mean failure, and for line 2 how you will work without seeing the data (P12). End your turn, and go on only after a clear yes. When line 6 is yes because the work is large, say that it needs a plan, and offer the first slice that is small enough to do now.

## 3. Change

- Before you change code that already produces an output, capture the baseline: the current value or digest of each output the change may move (P4).
- Make the change, and only that change. Unrelated things you see go on a "Noticed but not touching" list (P6).
- When one operation applies to many units, do one worked example, write the tool, show that the tool gives the outcome of the worked example, and only then run it on the rest (P3). Nothing that reaches a reader is typed in.
- Check a function name or an argument you are not sure of in the package's documentation before you use it (P7).
- Fail loudly: missing data, a null weight or an unmatched merge raises an error, never a silent fallback (P10).
- If the change grows beyond what you restated, or a line in step 2 turns to yes, stop and return to step 2.

## 4. Prove

- Run the checks yourself. Where you can, see each check fail before the change and pass after it. Check the real output, not a step on the way to it.
- For a number that changed, compare it with something independent of the code: a reference value, a published figure, or what the human said they expected before the check ran (P4).
- Give each check one verdict: verified, not verified or inconclusive. Inconclusive is not a pass.
- Read the Verifier section of P3, P4 and P6 in `principles/`, and judge your own change against each. This is a self-review, and the record says so.

## 5. Record

Create the work report:

`"<python>" "<cg>" new work-report "<short title>" --project "<project root>"`

Fill every section of the file it creates. Evidence holds commands, exit codes, digests and counts. It never holds data.

Set `status: completed` when every check is verified. Otherwise leave `status: draft`, so that status keeps showing the work as open.

Commit only when the human asks. Then the work report goes in the same commit as the change (P8).

**Reply:** what was asked, what changed and in which files, each check with its command and verdict, the self-review verdict for P3, P4 and P6, the path of the work report, what you did not check, and the "Noticed but not touching" list. Label each claim measured, inferred or guess.

<!-- PLACEHOLDER: written in tasks 2.1 and 2.4. The table in step 2 moves into `cg.py tier`, and step 5 into `cg.py evidence`. -->
