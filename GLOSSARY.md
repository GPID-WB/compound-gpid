# Compound GPID glossary

The shared words of Compound GPID 2.0. Principles, playbooks, verifiers and documentation use these terms with these meanings. When two words exist for one idea, one is chosen and the others are listed under _Avoid_.

Format adapted from mattpocock/skills (`skills/engineering/domain-modeling/GLOSSARY-FORMAT.md`).

## Who it is for

**Analyst**:
The person the plugin serves: an economist, researcher or data scientist whose work is an estimate, a dataset, a report, a package or a dashboard. Rigor of the calculation comes before anything else.
_Avoid_: developer (when it means an application developer), end user

**Human**:
The person in the conversation who owns the work and signs it off.
_Avoid_: user (in principle and playbook text), operator

## The work

**Output**:
What the project's code produces: a dataset, an estimate, a table, a figure, a rendered report, a package function's return value, a dashboard.
_Avoid_: result (when the thing is a file), deliverable

**Real output**:
The output in the form its reader will receive it: the number in the final table, the published dataset, the running dashboard.
_Avoid_: real artifact

**Artifact**:
A document the loop writes under `.cg-docs/`: intent, plan, work report, review, decision record, solution.
_Avoid_: output (for these documents), doc

**Unit**:
One of many like things the same operation applies to: a country, a survey year, a file, a table, a model specification.

**Worked example**:
One unit that the agent takes through directly, step by step, before any script exists, showing each step and its result. It exists to learn what the script must do and to give a known result to test the script against. The agent does it, never the human, and the delivered output never comes from it.
_Avoid_: by hand, manually

**Tool**:
A script, pipeline target, function or generator that performs a step and can be run again by anyone.
_Avoid_: lever, automation

**By code**:
A step whose output a tool produces.

**By judgement**:
A step that needs a person or a model to weigh something: an interpretation, a choice of method, a trade-off.

**Slice**:
A small piece of the plan that ends in a check and can be reviewed in one sitting.
_Avoid_: task (for this meaning), ticket

**Contract**:
The part of the plan the human approves: goal, out of scope, checks, boundaries.
_Avoid_: spec, requirements

## Checking

**Verification**:
Showing that the work does what the contract says, by running checks on the real output. It answers: did we build what we said we would?

**Validation**:
Showing that the result is right for the question, by comparing it with something independent of our code: a reference value, a published figure, the same computation in a second software, a prediction the human made beforehand. It answers: is the answer correct?
_Avoid_: using "validation" for input checks or for approval

**Input assertion**:
A check on data as it enters the code: a key is unique, a weight is present, a value is in range.
_Avoid_: validation, guard

**Check**:
A command with a stated pass condition that can fail.
_Avoid_: test (when it is not a unit test)

**Proxy**:
Something easier to observe than the real output that is taken as proof: "it runs", "the file exists", the agent's own report.

**Baseline**:
The value of an output captured before a change, so a check can read "old against new".

**Pin**:
A check that records current behavior before a restructuring, so the restructuring can be shown to change nothing.
_Avoid_: snapshot (unless it is one)

**Reference value**:
A number known to be right from a source independent of our code.

**Cross-check**:
The same computation done independently, usually in a second software, and compared.

**Verdict**:
The outcome of checking one thing: verified, not verified, or inconclusive. Inconclusive is not a pass.

**Evidence**:
The record that a check ran: command, exit code, a digest of the output, the commit. It never contains data.

**Verifier**:
A reviewer agent that checks one principle and returns a verdict block.
_Avoid_: reviewer agent, critic

**Lens**:
The instruction file a verifier reads. Packs add lenses for their field.
_Avoid_: persona, agent file

**Independent review**:
A review by an agent in a fresh context that did not see the author's reasoning.

**Self-review**:
The same checks run in the author's own context. Recorded as such; weaker than independent review.

## The loop

**Guide**:
The `/cg` skill: it reads the state of the work and opens the right playbook.
_Avoid_: orchestrator, router

**Playbook**:
The steps for one kind of work: brainstorm, plan, work, review, compound, bugfix and others.
_Avoid_: command, prompt, workflow

**Track**:
The kind of work: analysis, build, bug, writing, understand.

**Tier**:
The risk level of a piece of work, computed by code from declared facts.

**Hard stop**:
A point where the agent ends its turn and waits for the human: plan approval, and sign-off.
_Avoid_: gate (for these two)

**Sign-off**:
The human's statement that they can explain the work, given after reading the defend-it brief and the conformance record.

**Defend-it brief**:
What the agent presents at sign-off: what changed, why, how it was verified and validated, what could still be wrong, what was not checked.

**Conformance record**:
The file holding one verdict per principle for a piece of work.

## Packaging

**Hub**:
The repository that holds the pack index, the installer and the core pack.

**Pack**:
A folder of skills with a `pack.json`, installed on its own.
_Avoid_: module, suite, plugin (for a pack)

**Core**:
The pack everyone installs: the guide, the playbooks, the principles and the tooling.
_Avoid_: kernel

## Flagged ambiguities

- "Artifact" in pstack means what we call the real output. Here an artifact is always a `.cg-docs/` document.
- "Validation" in pstack means input checks at a system boundary. Here that is an input assertion, and validation means checking the result against independent truth.
- "Test" in the source repos usually means a unit test. Most checks in analytical work are not unit tests, so "check" is the general word.
