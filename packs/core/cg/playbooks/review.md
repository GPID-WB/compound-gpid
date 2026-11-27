---
name: review
derived-from: "addyosmani/agent-skills@e997ac5:skills/code-review-and-quality/SKILL.md; mattpocock/skills@d653911:skills/engineering/code-review/SKILL.md; v1:.agents/commands/cg-review.md; v1:.agents/commands/cg-fix-triage.md; v1:.agents/commands/cg-verify-pr.md; v1:.agents/shared/review-routing.contract.md"
---

# Review

**You own the review of proven work: have it checked by the verifiers of the review stage, show the human every finding, those against the contract apart from those against the standards, and record what they decide on each one.** You change no file of the project in this playbook, and you fix no finding. Each finding stays in the conformance record with its pointer and its priority, P0 to P3, and the human decides what follows from it. No finding is a valid result: never invent one, and never soften one.

## 1. Start

The work under review is a work report: the one the human named, or the one the work playbook has just closed. Code's checks of the close ran on it first: `repro`, `scope`, `claims` and `validate`, as section 6 of `playbooks/work.md` says. When they did not, or a slice of the plan is still to do, say that `/cg work` closes the work first, and end your turn.

Have code say where the review stands:

`"<python>" "<cg>" route "<the work report>" --project "<project root>"`

- **A line under `missing`** names a verifier that gave no verdict: go to step 2.
- **`waiting` is not `none`:** findings wait on the human. Go to step 3.
- **Otherwise** nothing waits on the human. Give the Reply.

## 2. Have the change checked

Have the whole change checked by the verifiers of the principles the work is held to. The line below says which verifiers run, and prints the kickoff of each. Run each one and record its verdict as the guide says under "Verifiers": each finding whole, with its priority and its fix, as the verifier wrote it. Then run the line printed after `then`, which lists the verdict of each verifier, and go on only when it prints `missing: none`. A verdict that the listing marks as given on an earlier text was given before the change last moved: start that verifier again, once, and record its new verdict. A mark that is still there goes to the human with the findings. Change nothing for a finding in this step: the human decides on each one at step 4.

`"<python>" "<cg>" verifiers "<the work report>" --stage review --project "<project root>"`

Then run the `route` line of step 1 again.

## 3. The findings

`route` lists every finding in two parts. The findings against the contract are what the verifier of P1 found against what the human approved. The findings against the standards are what the verifiers of every other principle found. Each part is in order of priority, P0 first, and each finding has its ID, F1, F2 and so on, its verifier, its pointer, or "no proof" when code could not open one, and what is wrong. Show both parts as `route` prints them. Never merge them, rank one against the other, or leave a finding out: work can meet every standard and build the wrong thing, or hold to the contract and break a standard. P0 blocks everything and P1 blocks a merge (`principles/README.md`). Name each verdict that is INCONCLUSIVE, with its note, and each that the listing marks as given on an earlier state: what it did not check is not checked.

With no finding, say so in one line: no verifier found anything in the work, which is a valid result. Nothing waits on the human. Give the Reply.

When the branch of the work has an open pull request, and `gh` is installed and signed in, read its checks with `gh pr checks`. A check that fails there and passes here goes to the human beside the findings: name the check and the machine it ran on, open no log that can hold a row of data, and change, commit and push nothing for it (`playbooks/work.md`, section 5, rule 1).

## 4. The human decides: a hard stop

This is a hard stop. Show the findings as step 3 says, and for each one the decision you recommend, with its trade-off:

- **fix:** the work goes back to change it;
- **accept:** it stays as it is, for a reason the human gives in their words, and sign-off reads that reason;
- **drop:** it is no fault, as the human reads it.

Recommend fix for a P0 or a P1 unless the finding is wrong, and say what it blocks when you recommend another decision. Ask the human to decide on each finding that waits, in a reply of this form: `F1 fix; F2 accept: <the reason>; F3 drop`, or `all fix`. Say that code records their reply under their name and takes only that plain answer, so that a yes or anything else comes back to them as a question. Then end your turn. The coding agent's own approval settings are not the human's decision.

## 5. Record

When the human answers, record their reply before anything else. Show the line, then run it:

`"<python>" "<cg>" route "<the work report>" --reply "<the human's reply, word for word>" --project "<project root>"`

Run it only when the reply answers the question you asked. Give `--reply` the human's words as they wrote them, punctuation included, in single quotes, as `grilling.md` says, and never reword a reply into a plain answer. If it prints `refused`, nothing was recorded: read the reason, and ask the human again in the form of step 4. A reply that decides some findings records those, and the others still wait: ask again for them alone.

## 6. What follows

Each decision goes where `route` says after `next`:

- **fix:** code sets the work report to `in-progress` again. On a plan, the fix is an amendment that adds a slice for each finding to fix: `/cg plan` writes it from the findings that `route` lists as fix, the human approves it, and `/cg work` does that slice in this work report, whose close runs this review again. In quick work, quick work does it in the same work report.
- **accept:** the finding stays in the record with the human's reason, for sign-off.
- **drop:** closed, with no change.

When the review runs again after a fix, each decision still holds for the finding it named, and a finding to fix that a verifier finds again on the changed work waits on the human again. Change no file for a decision in this playbook, and start no slice. Commit only when the human asks: the records under `.cg-docs/conformance/` and `.cg-docs/approvals/` then go in one commit (P8). A push is section 5, rule 1, of `playbooks/work.md`.

**Reply:** the work report and its status; whether every verifier gave its verdict, each with the kind of review that gave it; the findings against the contract, then those against the standards, each part by priority, each finding with its ID, its pointer and its decision, or that none was found; the checks of the pull request, when you read them; where each decision sends its finding; what you did not check; and what the human can do next. Label each claim measured, inferred or guess.
