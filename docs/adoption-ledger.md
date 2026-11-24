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
| `interview-me` | Adapt | grilling primitive | hypothesis with confidence, restate with out-of-scope, list of replies that are not a yes | cited |
| `idea-refine` | Adapt | `brainstorm` | widen-then-narrow step replaces `/cg-ideate` | open |
| `spec-driven-development` | Adapt | `plan`, P1 | assumptions block; Always / Ask first / Never boundaries; deferred scope; amendments instead of rewrites; a hard stop | cited |
| `planning-and-task-breakdown` | Adapt | `plan` | vertical slices, checkpoints, never overwrite an unfinished plan | open |
| `incremental-implementation` | Adapt | `work` | one slice, evidence, commit | open |
| `constraint-driven-development` | Adapt | charter constraints as a floor, `cg.py guard` | diff may not delete or skip tests or add suppressions | open |
| `context-engineering` | Adapt | `status`, pointer block | restartable boundaries; never infer approval from chat | open |
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
| `grilling`, `grill-me`, `grill-with-docs` | Adapt | grilling primitive, P2 | used by brainstorm, plan and triage | cited |
| `domain-modeling` (glossary, ADR format) | Adapt | the two glossaries (P11), decision records (P8) | project terms such as welfare aggregate, PPP vintage | cited |
| `to-spec` | Adapt | `plan` | synthesize, do not re-interview; agree the checks | open |
| `to-tickets` | Adapt | `plan` slices, issues pack | tracer bullets, blocking edges, tracker as verbs | open |
| `implement`, `implement-spec` | Adapt | `work` | fresh context per slice for deep work | open |
| `wayfinder` | Adapt | deep size, roadmap pack | decision map for multi-session work | open |
| `tdd` | Adapt | `work`, P4 | no check at a point the human has not confirmed | cited |
| `diagnosing-bugs` | Adapt | `bugfix` | feedback loop first, ranked hypotheses shown to the user, regression test before the fix | open |
| `code-review` | Adapt | `review` | standards and spec reviewed separately, never merged | open |
| `prototype` | Adapt | `brainstorm` | settle a fork by running something, on a throwaway branch | open |
| `research` | Adapt | grilling | fact-finding in a fresh context, with citations | open |
| `to-questionnaire` | Adapt | `brainstorm` | when the knowledge sits with a colleague, such as the survey team | open |
| `setup-matt-pocock-skills` | Adapt | `setup` | explore, propose, confirm, write a pointer block | cited |
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
| `poteto-mode` (router, principles index, reply rules) | Adapt | `cg/SKILL.md`, principles index | approval gates added; no model-specific setup | cited |
| the 24 `principle-*` skills | Adapt | P3, P4, P6, P9 and others | merged into twelve principles; each has a verifier | cited |
| `worker.md` | Adapt | `worker.md` | first line of every kickoff to another agent | open |
| playbooks: bug fix, feature, refactoring, investigation, prototype, multi-phase plan, opening a PR, session pickup, pause safely | Adapt | `bugfix`, `work`, `understand`, `brainstorm`, `plan`, `ship`, `status` | ownership statement and `Reply:` contract kept | open |
| `figure-it-out` | Adapt | `custom` playbook | falsifiable done condition; verdicts verified, not verified, inconclusive | cited |
| `show-me-your-work` | Adapt | `cg.py decide`, `cg.py evidence` | append-only trail written by script, audited at the end | open |
| `ketchup`, `recall`, `in-your-own-words`, `bro` | Adapt | `status`, restate step | list of decisions waiting on the human | open |
| `how`, `why`, `teach` | Adapt | `understand` | part of sign-off, not optional | open |
| `interrogate` | Adapt | Adversary verifier | findings reproduced; dropped findings listed | cited |
| `blast-radius` | Adapt | scope lens, P7 | its ladder of certainty becomes our evidence grades E1 to E5 | cited |
| `benchmark-checklist`, Explain the Number | Adapt | analysis track, Verification verifier | applied to any reported statistic | cited |
| `create-verification-skill`, `maintain-verification-skill` | Adapt | the verification profile written by `setup` (P4) | how to run and check this project; source of check IDs | cited |
| `reflect`, `correct` | Adapt | `compound`, Lesson verifier | rule-to-check table; prove the check fails on the past mistake | cited |
| `architect`, Foundational Thinking | Adapt | `plan` for build work | name the data shape and keys first | open |
| `sharpen`, `reframe` | Adapt | `brainstorm` | expert vocabulary with verified links when the user is outside their field | open |
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
