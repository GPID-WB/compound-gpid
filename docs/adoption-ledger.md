# Adoption ledger

What Compound GPID 2.0 takes from each source, where it lands, and how far along it is. This file is the working record; section 5 of the approved plan was its first version.

**Rule.** Read the source file in full, at the pinned commit, before writing the file derived from it. Then put the source in that file's `derived-from` field (ADR 0002).

Verdicts: **Adapt**, we write our own version for analytical work. **Pattern**, we reuse the idea, not the content. **Later**, a possible pack. **Skip**, not taken.

Status: **cited** means at least one principle file already names this source in `derived-from`. **open** means nothing derived from it exists yet. Change a row to **done** when its target file exists and cites it.

## addyosmani/agent-skills

Pinned at 0.6.18, `e997ac5`. MIT licence.

| Source | Verdict | Lands in | What changes for us | Status |
|---|---|---|---|---|
| `using-agent-skills` (router, six behaviors, failure modes) | Adapt | `cg/SKILL.md`, `worker.md`, P2, P6, P7 | state comes from a script; the guide does not fire by itself | cited |
| `interview-me` | Adapt | `grilling.md`, `brainstorm` | a first reading stated with what is still missing, in place of a confidence number nobody can check (P7); restate with out-of-scope; the stop when the next three answers can be predicted; the list of replies that are not a yes, held in `cg.py` | done |
| `idea-refine` | Adapt | `brainstorm` | the widen-then-narrow step replaces `/cg-ideate`; its questions are for analytical work (the simplest version, what the project already has, the rawest input, an independent source) | done |
| `spec-driven-development` | Adapt | `plan`, P1, `grilling.md` | the assumptions block is in `grilling.md`; the plan's contract keeps the Always / Ask first / Never lists and puts what is deferred under Out of scope; a change to an approved plan is an amendment in the same file, with a dated line, and the record of the earlier approval keeps the earlier text, in place of a delta file; the hard stop is held by code, which records only a plain yes; success criteria become checks with a command and an outcome that means failure; the capability map and the parts on code style and project structure are not taken | done |
| `planning-and-task-breakdown` | Adapt | `plan` | a slice goes from an input to an output someone can read, for one unit, in place of one feature through every layer; the first slice is the worked example; baselines and pins come first, and the slice most likely to fail early; each slice ends in a check, which takes the place of checkpoints; five files at most; slices are a table in the plan and not a task list of their own; `cg.py new plan` makes no plan beside an unfinished one unless the human said it is other work | done |
| `incremental-implementation` | Adapt | `work` | one slice, evidence, commit | open |
| `constraint-driven-development` | Adapt | charter constraints as a floor, `cg.py guard` | diff may not delete or skip tests or add suppressions | open |
| `context-engineering` | Adapt | `status`, pointer block | restartable boundaries; never infer approval from chat | cited |
| `source-driven-development` | Adapt | rule in `worker.md` and language packs | check package docs for R, Stata, Python and cite them | cited |
| `doubt-driven-development` | Adapt | Adversary verifier, P5 | the work and the contract only; three rounds; "doubt theater" flag | cited |
| `test-driven-development` | Adapt | `work`, language packs | failing check first; prove-it for bugs | open |
| `debugging-and-error-recovery` | Adapt | `bugfix` | merged with mattpocock `diagnosing-bugs` | open |
| `code-review-and-quality` | Adapt | `review`, general lenses | severity mapped to P0 to P3; "zero findings is valid" | open |
| `code-simplification` | Adapt | Simplicity verifier, P6 |  | open |
| `security-and-hardening` | Adapt | data-protection lens | personal data, credentials and microdata, instead of web application risks | open |
| `performance-optimization` | Adapt | performance lens | measure first, with Explain the Number | open |
| `documentation-and-adrs` | Adapt | decision records, stale detection in `cg.py index` |  | cited |
| `git-workflow-and-versioning` | Adapt | `ship` | merged with v1 `cg-skill-git-workflow` | open |
| `/build auto` rules | Adapt | `work` | one approval, fixed stop list for irreversible actions | open |
| five personas and their composition rule | Pattern | lenses | a verifier never starts another verifier | open |
| `definition-of-done` reference | Adapt | project Definition of Done, used by P4 |  | open |
| skill linter, path allowlist, routing evals, pressure cases, rejection ledger, skill anatomy | Pattern | `tools/`, `evals/`, `SCOPE.md` | our own code | open |
| frontend, API design, browser testing, accessibility, observability, CI/CD, deprecation, shipping; the 10 commands; the hooks | Skip |  | application development; see `.out-of-scope/application-development-skills.md` | n/a |

## mattpocock/skills

Pinned at 1.3.2, `d653911`. MIT licence.

| Source | Verdict | Lands in | What changes for us | Status |
|---|---|---|---|---|
| `grilling`, `grill-me`, `grill-with-docs` | Adapt | `grilling.md`, P2 | used by brainstorm now, by plan and triage later; rounds of three decisions at most; each answer is written into the intent in the turn it comes | done |
| `domain-modeling` (glossary, ADR format) | Adapt | the two glossaries (P11), decision records (P8) | project terms such as welfare aggregate, PPP vintage | cited |
| `to-spec` | Adapt | `plan` | the plan is written from the decided intent, with no second interview; the human agrees the checks at the hard stop, each shown with what it catches and what no check would catch; no user stories; file paths are kept, per slice, because the work is held to them | done |
| `to-tickets` | Adapt | `plan` slices, issues pack | the first slice is the thinnest whole path; slices are ordered rows, each resting only on the rows above it; one mechanical change across many files is cut as add, move in batches, remove; publishing to a tracker waits for the issues pack | done for `plan`; open for the issues pack |
| `implement`, `implement-spec` | Adapt | `work` | fresh context per slice for deep work | open |
| `wayfinder` | Adapt | deep size, roadmap pack | decision map for multi-session work | open |
| `tdd` | Adapt | `work`, P4 | no check at a point the human has not confirmed | cited |
| `diagnosing-bugs` | Adapt | `bugfix` | feedback loop first, ranked hypotheses shown to the user, regression test before the fix | open |
| `code-review` | Adapt | `review` | standards and spec reviewed separately, never merged | open |
| `prototype` | Adapt | `brainstorm` | a choice that running something can settle is named as an experiment; the brainstorm does not run it, quick work does, so the data rules and the tier hold | done |
| `research` | Adapt | `grilling.md` | fact-finding in a fresh context, each fact with its source | done |
| `to-questionnaire` | Adapt | `grilling.md` | when the knowledge sits with a colleague, such as the survey team: the questions are written for that person and the decision stays open | done |
| `setup-matt-pocock-skills` | Adapt | `setup` | explore, propose, confirm, write a pointer block | done |
| `ask-matt`, phase boundaries | Adapt | help and `status` | continue, clear, hand off, or delegate | open |
| `handoff` | Adapt | `status` | pause note computed from files | open |
| `retro` | Adapt | `compound`, P9 | mechanical lesson becomes a check | cited |
| `teach`, `wait-what` | Adapt | `understand` | plain-language re-pitch using glossary terms | cited |
| `pr` | Adapt | `ship` | PR body contract | open |
| `triage` and its agent brief | Adapt | issues pack; out-of-scope records in core |  | open |
| `writing-for-agents` | Adapt | our writing rules and linter rules; maintainer pack | completion criteria, leading words, positive phrasing, pruning | cited |
| `SCOPE.md`, `.out-of-scope/`, buckets, changesets | Pattern | governance |  | open |
| `codebase-design`, `improve-codebase-architecture` | Later | software pack |  | open |
| `wizard`, in-progress and misc skills | Skip |  |  | n/a |

## cursor/plugins, `pstack/`

Pinned at 0.15.48, `ca782ed`. MIT licence.

| Source | Verdict | Lands in | What changes for us | Status |
|---|---|---|---|---|
| `poteto-mode` (router, principles index, reply rules) | Adapt | `cg/SKILL.md`, principles index | approval gates added; no model-specific setup | done |
| the 24 `principle-*` skills | Adapt | P3, P4, P6, P9 and others | merged into twelve principles; each has a verifier | cited |
| `worker.md` | Adapt | `worker.md` | first line of every kickoff to another agent | open |
| playbooks: bug fix, feature, refactoring, investigation, prototype, multi-phase plan, opening a PR, session pickup, pause safely | Adapt | `bugfix`, `work`, `understand`, `brainstorm`, `plan`, `ship`, `status` | ownership statement and `Reply:` contract kept; from `multi-phase-plan`, the plan is the output and no slice starts in the same turn | cited |
| `figure-it-out` | Adapt | `custom` playbook | falsifiable done condition; verdicts verified, not verified, inconclusive | cited |
| `show-me-your-work` | Adapt | `cg.py decide`, `cg.py evidence` | append-only trail written by script, audited at the end | open |
| `ketchup`, `recall`, `in-your-own-words`, `bro` | Adapt | `status`, restate step | list of decisions waiting on the human; `in-your-own-words` is the restate step of `grilling.md` | cited |
| `how`, `why`, `teach` | Adapt | `understand` | part of sign-off, not optional | open |
| `interrogate` | Adapt | Adversary verifier | findings reproduced; dropped findings listed | cited |
| `blast-radius` | Adapt | scope lens, P7 | its ladder of certainty becomes our evidence grades E1 to E5 | cited |
| `benchmark-checklist`, Explain the Number | Adapt | analysis track, Verification verifier | applied to any reported statistic | cited |
| `create-verification-skill`, `maintain-verification-skill` | Adapt | the verification profile written by `setup` (P4) | how to run and check this project; source of check IDs | cited |
| `reflect`, `correct` | Adapt | `compound`, Lesson verifier | rule-to-check table; prove the check fails on the past mistake | cited |
| `architect`, Foundational Thinking | Adapt | `plan` | the shape of the data is named before any step: the unit of observation, the key and the columns, and for an estimate the weights and the population; what every later slice needs goes first; sketching two shapes is left to the brainstorm's widening | done |
| `sharpen`, `reframe` | Adapt | `brainstorm` | the field's term with a source that was opened, when the human describes it in everyday words; the widening questions; an experiment in place of an opinion | done |
| `unslop`, `technical-writing` | Pattern | writing pack | numbered rules other skills cite | open |
| `comment-sicko` | Pattern | principle verifiers | one verifier per principle | open |
| `poteto-help` | Adapt | help | routes without starting work | open |
| harness adapter doc | Pattern | `hosts.md`, only if the spike shows naming gaps | one adapter file (ADR 0004), nothing generated | open |
| arena, swarm, babysit, shipping, autopilot, worktree cleanup, formal verification, statechart, bot UI, TypeScript, model setup, `automate-me` | Skip |  | Cursor-specific, costly, or out of scope | n/a |

## Not from the three sources

- Validation as a separate duty from verification (P4), the seven questions for a number rewritten for statistics, and predict-then-check: ours.
- One verifier per principle with a conformance record and planted-violation tests: ours, extending pstack's single-rule reviewer.
- P10 Correct in the domain and P12 Governed data: ours.
- The compound step and the loop itself: Every's Compound Engineering, credited in `docs/why-compound-gpid.md`.
