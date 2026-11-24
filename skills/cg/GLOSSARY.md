# Compound GPID

The words Compound GPID itself uses: in its principles, playbooks, verifiers and documentation, and in what the agent says to the human. This file ships with the core pack, so the agent and the human share these words in every project.

A project's own subject words (welfare aggregate, PPP vintage, survey wave) do not belong here. They go in that project's `GLOSSARY.md`, in the same format.

How to read an entry: the term, what it is, then the words not to use for it. An avoided word with a condition in brackets is avoided only in that sense. `tools/check_glossary.py` fails the build on an unconditional avoided word and lists the conditional ones for a reviewer.

Format adapted from mattpocock/skills (`skills/engineering/domain-modeling/GLOSSARY-FORMAT.md`).

## People

**Analyst**:
The person the plugin serves: an economist, researcher or data scientist whose work is an estimate, a dataset, a report, a package or a dashboard.
_Avoid_: end user, developer (when it means an application developer)

**Human**:
The person in the conversation who owns the work and signs it off.
_Avoid_: operator, user (in principle and playbook text)

## The work

**Output**:
What the project's code produces: a dataset, an estimate, a table, a figure, a rendered report, a function's return value, a dashboard.
_Avoid_: deliverable, result (when the thing is a file)

**Real output**:
The output in the form its reader receives: the number in the final table, the published dataset, the running dashboard.
_Avoid_: real artifact

**Artifact**:
A document the loop writes under `.cg-docs/`: intent, plan, work report, review, decision record, solution.
_Avoid_: output (for these documents)

**Unit**:
One of many like things the same operation applies to: a country, a survey year, a file, a table, a model specification.

**Worked example**:
One unit that the agent takes through directly, step by step, before any tool exists, showing each step and its outcome. It teaches what the tool must do and gives a known outcome to test the tool against. The agent does it, never the human, and no delivered output comes from it.
_Avoid_: by hand, manually

**Tool**:
A script, pipeline target, function or generator that performs a step and that anyone can run again.
_Avoid_: lever

**By code**:
Said of a step whose output a tool produces.

**By judgement**:
Said of a step that needs a person or a model to weigh something: an interpretation, a choice of method, a trade-off.

**Slice**:
A small piece of the plan that ends in a check and can be reviewed in one sitting.
_Avoid_: ticket, task (for a piece of the plan)

**Contract**:
The part of the plan the human approves: goal, out of scope, requirements, checks, boundaries.
_Avoid_: spec (for the approved document)

**Requirement**:
One thing the contract says the work must do.

## Checking

**Verification**:
Showing that the work does what the contract says, by running checks on the real output. It answers: did we build what we said we would?

**Validation**:
Showing that the output is right for the question, by comparing it with something independent of our code: a reference value, a published figure, a cross-check, an expectation the human stated beforehand. It answers: is the answer correct?

**Input assertion**:
A check on data as it enters the code: a key is unique, a weight is present, a value is in range.
_Avoid_: validator, guard (for an input check)

**Check**:
A command with a stated pass condition that can fail.
_Avoid_: test (when it is not a unit test)

**Proxy**:
Something easier to observe than the real output that is taken as proof: "it runs", "the file exists", the agent's own report.

**Baseline**:
The value of an output captured before a change, so a check can compare old against new.

**Pin**:
A check that records current behavior before code is restructured, so the restructuring can be shown to change nothing.

**Reference value**:
A number known to be right from a source independent of our code.

**Cross-check**:
The same computation done independently, usually in a second software, and compared.

**Verdict**:
The outcome of checking one thing: verified, not verified, or inconclusive. Inconclusive is not a pass.

**Evidence**:
The record that a check ran: command, exit code, a digest of the output, the commit. It never contains data.

**Principle**:
One of the rules everything made with Compound GPID is held to. Each has a file, a verifier and deterministic checks.

**Verifier**:
An agent that checks one principle in a fresh context and returns a verdict block.
_Avoid_: reviewer agent, critic

**Lens**:
The instruction file a verifier reads. Packs add lenses for their field.
_Avoid_: persona

**Independent review**:
A review by an agent in a fresh context that did not see the author's reasoning.

**Self-review**:
The same checks run in the author's own context. Recorded as such; weaker than independent review.

## The loop

**Guide**:
The `/cg` skill: it reads the state of the work and opens the right playbook.
_Avoid_: orchestrator

**Playbook**:
The steps for one kind of work: brainstorm, plan, work, review, compound, bugfix and others.
_Avoid_: command (for a playbook), prompt (for a playbook), workflow (for a playbook)

**Track**:
The kind of work: analysis, build, bug, writing, understand.

**Tier**:
The risk level of a piece of work, computed by code from declared facts.

**Hard stop**:
A point where the agent ends its turn and waits for the human: plan approval, and sign-off.

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
_Avoid_: suite, module (for a pack), plugin (for a pack)

**Core**:
The pack everyone installs: the guide, the playbooks, the principles and the tooling.
_Avoid_: kernel

## Relationships

- A plan holds one **contract**. A contract lists **requirements** and **checks**.
- A plan is cut into **slices**. Each slice ends in a check.
- A check that ran leaves **evidence** and gets a **verdict**.
- **Verification** and **validation** together are what "prove it works" means.
- A **verifier** reads one **lens**, checks one **principle**, and returns a verdict block.
- The **conformance record** holds one verdict per principle. **Sign-off** needs all of them.
- A **pack** holds skills and lenses. The **hub** lists packs.
- The **guide** opens **playbooks**. A playbook applies **principles**.

## Flagged ambiguities

- "Artifact" in pstack means what we call the real output. Here an artifact is always a `.cg-docs/` document.
- "Validation" in pstack means an input check at a system boundary. Here that is an input assertion, and validation means checking the output against an independent source.
- "Test" in the source repos usually means a unit test. Most checks in analytical work are not unit tests, so "check" is the general word.
- "By hand" in pstack means the agent doing one unit directly. Read alone it suggests the human does it. Resolved: worked example.
- "Spec" was used for both the approved document and the act of specifying. Resolved: the document is the contract; "specify" stays as a verb.
