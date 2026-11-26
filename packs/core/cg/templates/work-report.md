---
type: work-report
schema: 2
title: "{title}"
date: {date}
status: in-progress
size: {size}
plan: {plan}
---

# {heading}

## Asked

<the request in the human's words, then your restatement of it>

## Risk

<your reason for each fact you answered no. At a hard stop, written before you ask: the short contract, or the action that cannot be undone, as the human is asked to say yes to it>

## Changed

| File | What changed and why |
|---|---|
| <a file the change created, changed or deleted> | <what changed in it, and why> |

## Checks

| Check | What a failure of it would show, and what it does not look at |
|---|---|
| <its ID in the plan, or its command> | <what it catches, and what it would miss> |

## Evidence

Code records each run of a check: its command, its exit code, its verdict, a digest of what it printed and the commit. `cg.py evidence` with this file as `--report` lists the records. They hold digests and counts and never data, and this file holds no data either.

- Digest of each output file the change produced or moved: <the path and its digest from `git hash-object`, before and after where there was a baseline; or "no output moved">
- Validation, for a number: <what it was compared with, and the two values; or "no number changed">

## Self-review

| Principle | Verdict | Finding, with file and line |
|---|---|---|
| P3 Deterministic by default | <PASS, FLAG or NOT APPLICABLE> | <the finding with file and line, or "none"> |
| P4 Prove it works | <PASS, FLAG or NOT APPLICABLE> | <the finding with file and line, or "none"> |
| P6 Smallest change | <PASS, FLAG or NOT APPLICABLE> | <the finding with file and line, or "none"> |

review-mode: self-review

## Not checked

<what you did not check, and why>

## Noticed but not touching

<unrelated things you saw and left alone, or "nothing">
