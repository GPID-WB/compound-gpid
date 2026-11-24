# The ten principles

Status: draft for maintainer review (task 0.5). Nothing is built on these files until they are accepted.

Everything made with Compound GPID is held to these principles, and so is the plugin itself. A principle here is not advice. Each one says what the working agent does, what evidence that leaves, and how a verifier checks it.

## Index

Read the full file for any principle you apply. Cite a principle in a reply only if you read its file in this session.

| ID | Principle | Applies when | Verifier |
|---|---|---|---|
| P1 | [Specify before generating](P01-specify-before-generating.md) | before anything consequential is produced, and when judging whether the result matches | `spec` |
| P2 | [The human decides and can explain it](P02-human-decides.md) | a choice changes behavior, scope, risk or method; at sign-off | `ownership` |
| P3 | [Deterministic by default](P03-deterministic-by-default.md) | any output or check that code could produce | `determinism` |
| P4 | [Prove it works](P04-prove-it-works.md) | after each slice and before declaring done | `verification` |
| P5 | [Adversarial by default](P05-adversarial-by-default.md) | at each transition between phases, and when fixes keep failing | `adversary` |
| P6 | [Smallest change, simplest design](P06-smallest-change.md) | sizing a plan or a diff, or tempted to add | `simplicity` |
| P7 | [Honest claims](P07-honest-claims.md) | any statement about what was done, found or measured | `claims` |
| P8 | [The reasoning is the artifact](P08-reasoning-is-the-artifact.md) | a decision, a term or a limitation that someone absent would need | `record` |
| P9 | [Lessons become structure](P09-lessons-become-structure.md) | capturing what was learned | `lesson` |
| P10 | [Correct in the domain](P10-correct-in-the-domain.md) | the work touches data, estimates, or published results | domain lenses |

## Who this is for

Economists, researchers and data scientists, and the people who build their packages, pipelines and dashboards. The work is analytical: estimates, datasets, reports, R and Python packages, Shiny dashboards. Rigor and robustness of the calculation come first. The examples in these files are analytical for that reason, and a principle borrowed from application development is kept only where it holds for analytical work.

Words such as output, artifact, worked example, verification and validation have one meaning each, set in [`GLOSSARY.md`](../../../GLOSSARY.md).

## The five parts of every principle file

1. **Statement and why.**
2. **In production.** What the working agent does. It is split by stage of the loop, in loop order: Setup, Brainstorm, Plan, Work, Review, Sign-off, Compound, and Every stage. A stage heading appears only when the principle asks something at that stage. When one stage holds two kinds of obligation, the heading names both, as in "Work: verification" and "Work: validation". Each bullet under a heading is one obligation. Playbooks and `worker.md` take their obligations from here.
3. **Evidence it leaves.** A file or record a reviewer can open. A principle that left nothing behind was not applied.
4. **Verifier.** Instructions for a reviewer that checks this one principle.
5. **Deterministic checks.** What code checks. These are stronger than any reviewer and run first.

## How a verifier works

A verifier is started in a fresh context. It receives the work under review (the diff, the outputs, the artifacts), the approved contract, and its principle file. It never receives the author's explanation of the work.

It returns one **verdict block**:

```
principle: P3
verdict: PASS | FLAG | INCONCLUSIVE | NOT APPLICABLE
review-mode: independent | self-review
findings:
  - what: <one sentence>
    where: <file:line or artifact section>
    proof: <command run and its output, or the quoted line>
    grade: E2 | E3 | E4 | E5
    priority: P0 | P1 | P2 | P3
    fix: <proposed change>
not-checked: <what the verifier could not inspect, and why>
```

Rules for every verifier:

- A finding needs proof. A finding without proof is reported under `unverified`, never as a flag.
- "No findings" is a valid result. Do not invent one.
- INCONCLUSIVE means the verifier could not check. It is not a pass, and the human sees it as an open item.
- A verifier reports. It does not fix, and it does not start another verifier.
- When the host has no subagent tool, the same instructions run in the main thread and `review-mode` is `self-review`.

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

The `stages` field of each principle file is the source. `cg.py verifiers --stage <stage>` (task 2.5) reads it and prints the dispatch list, so the order below is computed and never recalled from memory.

| Stage | Verifiers |
|---|---|
| plan, before approval | `spec`, `determinism`, `simplicity`, domain lenses |
| end of each slice | deterministic checks only |
| review | `verification`, `determinism`, `adversary`, `simplicity`, `spec`, `claims`, domain lenses |
| sign-off | `ownership`, `record` |
| compound | `lesson` |

Quick work runs the deterministic checks and one combined pass of `determinism`, `verification` and `simplicity`.

## What these files cannot do

Verifiers are model reviewers. They lower the chance of an unowned, unverified or irreproducible result; they do not remove it. The human at sign-off is the last check, and no file in this folder can do that part for them.

## Priorities

P0 blocks everything: security, exposed personal data or credentials, silent data corruption, an incorrect statistical result. P1 blocks merge. P2 should be fixed. P3 is advisory.
