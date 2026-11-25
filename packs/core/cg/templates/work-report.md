---
type: work-report
title: "{title}"
date: {date}
status: draft
size: quick
---

# {heading}

## Asked

<the request in the human's words, then your restatement of it>

## Risk

<each line of the risk table that was yes, and the human's approval; or "every line was no">

## Changed

| File | What changed and why |
|---|---|

## Checks

| Check | Command | Exit code | Verdict |
|---|---|---|---|
| <what it shows> | <the command as run> | <code> | <verified, not verified or inconclusive> |

## Evidence

- Commit the checks ran on: <`git rev-parse --short HEAD`, with "+changes" when the change is not committed>
- Digest of each output file the change produced or moved: <path and `git hash-object <path>`, before and after where there was a baseline>
- Validation, for a number: <what it was compared with, and the two values; or "no number changed">

## Self-review

| Principle | Verdict | Finding, with file and line |
|---|---|---|
| P3 Deterministic by default | <PASS, FLAG or NOT APPLICABLE> | |
| P4 Prove it works | | |
| P6 Smallest change | | |

review-mode: self-review

## Not checked

<what you did not check, and why>

## Noticed but not touching

<unrelated things you saw and left alone, or "nothing">
