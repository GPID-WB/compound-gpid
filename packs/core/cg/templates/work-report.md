---
type: work-report
schema: 2
title: "{title}"
date: {date}
status: in-progress
size: quick
---

# {heading}

## Asked

<the request in the human's words, then your restatement of it>

## Risk

<the lines `cg.py tier` printed, your reason for each no, and the human's reply when the tier was elevated>

## Changed

| File | What changed and why |
|---|---|
| <a file the change created, changed or deleted> | <what changed in it, and why> |

## Checks

| Check | Command | Exit code | Verdict |
|---|---|---|---|
| <what it shows> | <the command as run> | <the exit code> | <verified, not verified or inconclusive> |

## Evidence

- Commit the checks ran on: <`git rev-parse --short HEAD`, with "+changes" when the change is not committed>
- Digest of each output file the change produced or moved: <the path and its digest from `git hash-object`, before and after where there was a baseline>
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
