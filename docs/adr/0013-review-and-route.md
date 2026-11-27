# ADR 0013: The review: findings kept by priority, the contract apart from the standards, and the human's decisions through `cg.py route`

Date: 2026-11-27. Status: proposed in task 2.9 (#232) as the working version. It waits for the maintainer's acceptance. Before 2.0 it changes by amending this record.

## Context

The issue asks for one review step in place of version 1's `/cg-review`, `/cg-fix-triage` and `/cg-verify-pr`, with general lenses ported from version 1's 17 review agents and a command `cg.py route`. It is done when findings keep P0 to P3, standards findings and spec findings are reported separately, and the human triages, with zero findings a valid result. "Spec" is the contract in our words (the glossary). The sources were read in full: the three version 1 commands and its routing contract, its 17 agents in `.agents/skills/`, addyosmani's `code-review-and-quality` and `security-and-hardening`, and mattpocock's `code-review` (two axes, standards and spec, never merged or ranked).

Four things were given. The engine (ADR 0008) dispatches the verifiers of a stage from the principle files and records each verdict as one line of the conformance record, with its findings; the close of the work playbook ran the review stage since task 2.5, and the work ended with the plan `in-progress` and a placeholder for this task. Nothing followed from a FLAG in code. `cg.py approve` records a reply only when it is a plain yes, under the name git gives, one file each under `.cg-docs/approvals/`. And the gate reruns 21 to 23 show agents recording findings without the priority the verdict block gives them.

## Decision

### The review playbook takes the review stage from the work

- **`playbooks/review.md` dispatches the verifiers of the review stage**, with the paragraph and the line that stood in section 6 of `work.md`, and then shows the findings, puts them to the human at a hard stop and records each decision. The work playbook keeps code's checks of the close (`repro`, `scope`, `claims`), completes the work report on its evidence, runs `validate`, and then runs the status line with `--playbook review` and follows what it names, as quick work hands a slice of a plan to the work playbook. So status chooses the playbook, and the review runs in the turn that closed the work. Considered and set aside: `repro`, `scope` and `claims` in the review too, which moves sentences that six gates passed and that the gate's step W checks; and a review only when the human types `/cg review`, which leaves the verdicts of a closed work missing until then.
- **A bare `/cg` does not open the review by state.** The guide has a row for `/cg review`, and status lists a work report whose findings wait under `waiting-on-human`, which the guide shows first. Routing by state is task 2.14.

### One record of findings

- **The conformance record is the one record of findings.** A decision of the human holds the ID, a digest of the finding (its verifier, its pointer and its sentence), its priority, its pointer and the state of the change its verdict was on, and never its sentence. Considered and set aside: the review artifact of task 2.1, a table of findings written into `.cg-docs/reviews/`, which is a second copy of every finding that can drift from the record, with a "Proof" column that asks for what a command printed (against rule 4 of `verifier.md`). The type stays in the schema for version 1's reviews; nothing writes a new one.

### Findings keep P0 to P3

- **`conformance` reads the priority of each finding from its sentence and keeps it.** The verdict block of `verifier.md` ends each finding with `(P1; fix: ...)`. Code takes the last `(P0` to `(P3` in the finding, keeps it as `priority` beside the finding, an unverified one too (which is now a pair of sentence and priority), and refuses a finding with none: the agent gives each finding whole, as the guide now says, and starts a verifier that gave none once more. A sentence is still cut at 300 characters, and the priority is read before the cut. A `(P12` is no priority, so a principle in brackets is not read as one. Considered and set aside: `--priority` beside each `--finding`, which pairs two lists in the shell; and a priority read only when listed, which a cut at 300 characters loses.

### The contract apart from the standards

- **A principle file says `axis: contract` when its findings are on the contract.** P1's says so; every other principle's findings are on the standards the work is held to. `route` lists the two parts apart, each in order of priority and in the order of dispatch within one priority, and numbers the findings F1, F2 and so on across them, the contract's first. A finding of one part is never ranked against the other: the contract's P1 comes before the standards' P0. A lens of a pack that serves P1 is in the contract's part. Considered and set aside: P1 named in code, which ADR 0011 set aside for P5's rules too; and the project's documented coding standards as the standards axis, as in the source: a rule of style a linter checks is the linter's (P3), and the principles are what everything made with Compound GPID is held to.

### What `cg.py route` decides, and from what

- **`route <work report>` decides which findings of the review wait on the human, where each decided one goes, and whether the review is done.** From: the newest verdict of each verifier that `dispatch()` names at the review stage, the decision records of the work report under `.cg-docs/approvals/` (`<work report>.route.<n>.json`, the newest decision on a finding counts), and the plan the work report names. A finding waits until the human decides on it. A decision to fix holds until a verdict on another state of the change holds the same finding: the fix did not take, and it waits again. Each decided finding goes on: fix, back to the work, which on a plan is an amendment that adds a slice for it (`/cg plan`, then `/cg work` in the same work report) and in quick work is quick work in the same work report; accept, kept for sign-off with the human's reason; drop, closed. Exit code 1 while a verifier gave no verdict or a finding waits. With no finding the listing says `findings: none`, nothing waits, and exit code 0: zero findings is a valid result.
- **`route <work report> --reply "<the human's words>"` records the human's decisions.** It refuses while a verifier gave no verdict, and says there is nothing to decide when no verifier found anything. A reply is a plain answer (`the_answer`) when each of its parts names findings by ID, or `all` of those that wait, and one decision, fix, accept with a reason in the human's words, or drop, and nothing else but words of courtesy; parts end at `;`, a new line, or a comma before the next part. A question, an opening no, a decision with nothing it names, a reason left out, one finding given two decisions, or anything more refuses the whole reply, as `the_yes` refuses a yes that says more. "Yes." decides nothing: code does not know what the agent recommended. The record keeps the reply word for word, the name and email from git, the time, and the decisions. A decision to fix sets a completed work report back to `in-progress`, as `approve` sets a plan's status.
- **What `route` does not decide.** Which verifiers run (`verifiers` does, from the principle files and the lenses' `when`, where version 1's routing contract chose agents by a risk class of the change), and which playbook comes next (status does). Considered and set aside: `route` as version 1's routing of reviewers, which would be a second dispatch beside `verifiers`; decisions typed into a table and approved with a plain yes, as an intent's are, which puts the agent's words in the table the human approves; and a decision through `approve`, which takes a plain yes and nothing else.

### The general lenses

The plan (section 7) sends version 1's 17 general agents to core's lenses and principle verifiers. Each agent's part that a principle holds went to that principle's lens. The three verifiers of the review stage with no lens get one, in the shape of the others, 60 lines at most: `lenses/domain-lenses.md`, the general data lens of P10 (version 1's `cg-data-quality`, and its testing agent's happy path); `lenses/language.md`, P11 (`cg-code-quality`'s names and `cg-documentation`); `lenses/governance.md`, P12 (`cg-version-control`'s credentials and data files, and `security-and-hardening` for analytical work). Version 1's reproducibility, adversarial, testing and plan-critic agents were already in the lenses of tasks 2.6 to 2.8. Its architecture agent stays out, since P6 rules out the restructuring it asks for in a change; its performance agent waits for a decision, since no principle holds speed; and its learnings, fix-problems, project, release, roadmap and wiki agents are no review and go to their tasks and packs. The ledger has a row for each. No code was added for these three: no rule finds a weight, a word or a credential yet, and each lens says so.

### The checks of a pull request

`/cg-verify-pr` read the checks of a pull request, fixed what failed, committed and pushed. The review keeps its observe-only part: when the branch has an open pull request, the agent reads its checks with `gh pr checks` and names a failing one to the human. No fix, commit or push: a push is stop rule 1 of the work playbook, and a fix is the human's decision. `cg.py` makes no network call for it.

## Consequences

- `cg.py` went from 2,990 to 3,171 of its 4,000 lines: about 125 for `route`, `review_of` and `the_answer`, about 10 for the priority in `conformance`, and the rest for the line of status and the parser.
- Every finding a verifier gives now carries its priority into the record, and the agent passes each finding whole.
- The close of the work ends in a hard stop when a verifier found anything.
- Gate step R measures the review from the guide (`spike/gate/run_cli_gate.py`).

## Open

- Whether code refuses a decision to accept a P0, which blocks everything; it does not, and the playbook has the agent say what it blocks.
- What a recommended decision is worth: `route` cannot take a yes to the agent's recommendations, because they are only in the conversation.
- A finding whose verifier words it again on the same state is a new finding with no decision, since a decision names a finding by its sentence.
- The review artifact type and its template stay unused by the playbook.
- No rule of code for a credential, a data file or rows of one in the change, which P12's check line names, and none for a weight or a word.
