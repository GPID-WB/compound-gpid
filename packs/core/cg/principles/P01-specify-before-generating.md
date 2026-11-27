---
id: P1
name: Specify before generating
applies-when: "before anything consequential is produced, and when judging whether a result matches what was asked"
stages: "plan, review"
verifier: contract
status: accepted
derived-from: "docs/philosophy.md (principle 1); addyosmani/agent-skills@e997ac5:skills/spec-driven-development/SKILL.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md; mattpocock/skills@d653911:skills/productivity/grilling/SKILL.md"
---

# P1 Specify before generating

Before the agent produces anything consequential, the human has stated what they want, what a correct result looks like, what an incorrect result looks like, and how the two will be told apart.

**Why.** The specification is for the person who must judge the result, not for the agent. Without a standard for correctness there is nothing real to review.

## In production

### Brainstorm

- Restate the goal in plain words.
- State what is out of scope.
- State what a wrong result would look like.

### Plan

- Write the contract: goal, out of scope, the named checks, and the boundaries (always do, ask first, never do).
- Give every requirement a check. Every check names its command and the outcome that would mean failure.
- Turn vague aims into measurable ones. "Harmonize the welfare variable" becomes "every survey has one welfare column, in 2021 PPP dollars per person per day, with no missing values for sampled households".

### Work

- Build what the contract names. An idea that arrives mid-work goes on the deferred list.

### Every stage

- A change to the contract is an amendment the human approves. The original stays readable.

## Evidence it leaves

- The intent, with goal, out of scope and wrong-result statement.
- The plan's contract section and its approval record.
- The deferred list and any amendments.

## Verifier: `contract`

**At plan stage, inspect** the plan. **At review stage, inspect** the diff and outputs against the approved contract.

Flag when:

- the plan has no statement of what a wrong result looks like;
- a requirement has no check, or a check serves no requirement;
- a check cannot fail, or its pass condition is a matter of opinion;
- something was built that the contract does not name;
- something the contract names was not built, or was changed with no amendment.

**Prove a flag** by quoting the contract line and pointing at the `file:line` of the diff, or by showing that a search for the required element returns nothing.

**Leave alone:** wording preferences, and detail the human explicitly chose to leave open.

## Deterministic checks

- `cg.py validate`: the intent has its goal, its out of scope and its wrong-result statement.
- `cg.py validate`: the plan has every contract section. Each check has an ID, a command and an outcome that means failure, and a slice ends in it. Nothing in the plan is still marked as open, and `cg.py approve` refuses a plan while a row of its Open questions has no recommended answer or no answer from the human.
- `cg.py new plan` makes a plan only on a decided intent, and `cg.py approve` refuses a plan whose intent is not decided as it now reads.
- `cg.py approve` record exists and its hash matches the current plan. The record keeps the text that was approved, and a changed plan is approved again only with a new dated line under `## Amendments`, beside the earlier lines.
