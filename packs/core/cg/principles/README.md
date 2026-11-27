# The principles

Status (task 0.5): all twelve were accepted by the maintainer on 2026-11-24 as the working version. Accepted means in force now. It does not mean final: see [How a principle changes](#how-a-principle-changes). Each file's `status` field is the record.

Everything made with Compound GPID is held to these principles, and so is the plugin itself. A principle here is not advice. Each one says what the working agent does, what evidence that leaves, and how a verifier checks it.

## Index

Read the full file for any principle you apply. Cite a principle in a reply only if you read its file in this session.

| ID | Principle | Applies when | Verifier |
|---|---|---|---|
| P1 | [Specify before generating](P01-specify-before-generating.md) | before anything consequential is produced, and when judging whether the output matches | `contract` |
| P2 | [The human decides and can explain it](P02-human-decides.md) | a choice changes behavior, scope, risk or method; at sign-off | `ownership` |
| P3 | [Deterministic by default](P03-deterministic-by-default.md) | any output or check that code could produce | `determinism` |
| P4 | [Prove it works](P04-prove-it-works.md) | after each slice and before declaring done | `verification` |
| P5 | [Adversarial by default](P05-adversarial-by-default.md) | at each transition between phases, and when fixes keep failing | `adversary` |
| P6 | [Smallest change, simplest design](P06-smallest-change.md) | sizing a plan or a diff, or tempted to add | `simplicity` |
| P7 | [Honest claims](P07-honest-claims.md) | any statement about what was done, found or measured | `claims` |
| P8 | [The reasoning is the artifact](P08-reasoning-is-the-artifact.md) | a decision or a limitation that someone absent would need | `record` |
| P9 | [Lessons become structure](P09-lessons-become-structure.md) | capturing what was learned | `lesson` |
| P10 | [Correct in the domain](P10-correct-in-the-domain.md) | the work touches data, estimates, or published results | domain lenses |
| P11 | [Shared language](P11-shared-language.md) | a word carries meaning both sides must hold the same way | `language` |
| P12 | [Governed data](P12-governed-data.md) | the work reads, produces or describes a dataset or information about a person | `governance` |

## Who this is for

Economists, researchers and data scientists, and the people who build their packages, pipelines and dashboards. The work is analytical: estimates, datasets, reports, R and Python packages, Shiny dashboards. Rigor and robustness of the calculation come first. The examples in these files are analytical for that reason, and a principle borrowed from application development is kept only where it holds for analytical work.

Words such as output, artifact, worked example, verification and validation have one meaning each, set in the plugin glossary, [`GLOSSARY.md`](../GLOSSARY.md).

## The five parts of every principle file

1. **Statement and why.**
2. **In production.** What the working agent does. It is split by stage of the loop, in loop order: Setup, Brainstorm, Plan, Work, Review, Sign-off, Compound, and Every stage. A stage heading appears only when the principle asks something at that stage. When one stage holds two kinds of obligation, the heading names both, as in "Work: verification" and "Work: validation". Each bullet under a heading is one obligation. Playbooks and `worker.md` take their obligations from here.
3. **Evidence it leaves.** A file or record a reviewer can open. A principle that left nothing behind was not applied.
4. **Verifier.** Instructions for a reviewer that checks this one principle.
5. **Deterministic checks.** What code checks. These are stronger than any reviewer and run first.

## How a verifier works

A verifier is started in a fresh context. It receives the work under review (the diff, the outputs, the artifacts), the approved contract, and its principle file. It never receives the author's explanation of the work.

It returns one **verdict block**: the principle, a verdict of PASS, FLAG, INCONCLUSIVE or NOT APPLICABLE, its findings, and a note on what it could not inspect. `verifier.md`, beside the guide, gives the block and the rules every verifier follows. `cg.py verifiers` writes the kickoff of each verifier from fixed text and from paths, and `cg.py conformance` records each verdict in the conformance record.

Rules for every verifier:

- A finding needs proof that code can open: a file and a line, or the record of a run. A finding without it is recorded under `unverified`, never as a flag.
- "No findings" is a valid result. Do not invent one.
- INCONCLUSIVE means the verifier could not check. It is not a pass, and the human sees it as an open item.
- A verifier reports. It does not fix, and it does not start another verifier.
- When the host has no subagent tool, the same instructions run in the main thread, and the conformance record says `self-review`.

## Evidence grades

Used in findings and in every claim an agent makes (P7).

| Grade | Meaning |
|---|---|
| E1 | Asserted. Worth nothing alone. |
| E2 | Pointed at: a real `file:line`, or the package's own documentation or source. |
| E3 | Reasoned: the failure was walked step by step and does not reach. |
| E4 | Ran it: a script, test or command on the real code or data, with its output. |
| E5 | Reproduced in the real pipeline or the published output. |

## When verifiers run

The `stages` field of each principle file is the source. `cg.py verifiers --stage <stage>` reads it and prints the dispatch list, so the order below is computed and never recalled from memory.

| Stage | Verifiers |
|---|---|
| plan, before approval | `contract`, `determinism`, `simplicity`, `governance`, domain lenses |
| end of each slice | deterministic checks only |
| review | `verification`, `determinism`, `adversary`, `simplicity`, `contract`, `claims`, `language`, `governance`, domain lenses |
| sign-off | `ownership`, `record` |
| compound | `lesson` |

Quick work runs the deterministic checks and one combined pass of `determinism`, `verification` and `simplicity`.

## What these files cannot do

Verifiers are model reviewers. They lower the chance of an unowned, unverified or irreproducible result; they do not remove it. The human at sign-off is the last check, and no file in this folder can do that part for them.

## How a principle changes

These files are expected to improve with use. Nobody should work around a principle that is wrong, unclear or too costly to follow: say so, and the file gets fixed.

- **Clearer wording, same meaning:** an ordinary commit.
- **A change of meaning** (what the working agent must do, what evidence is left, what the verifier flags): the maintainer decides. The commit says what was observed in real use and what changed. The verifier section and its planted-violation test change in the same commit, so the text and the check cannot drift apart.
- **Adding, merging or removing a principle:** the maintainer decides, with a decision record in `docs/adr/`.
- **Planned reviews:** at each milestone gate and after the pilot, the maintainer and the build session read the findings that were accepted with a written reason, the INCONCLUSIVE verdicts and the `dogfood` issues, and revise the principles those point at.

## Priorities

P0 blocks everything: exposed restricted data, personal data or credentials, silent data corruption, an incorrect statistical result. P1 blocks merge. P2 should be fixed. P3 is advisory.
