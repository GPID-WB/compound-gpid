---
date: 2026-07-31
title: "Review artifacts must use machine-readable finding maps and stable validation evidence"
category: "testing-patterns"
language: "PowerShell/Markdown"
tags: [review-artifacts, fix-triage, frontmatter, findings-map, validation-evidence, last-run-json, provenance, prompt-tests, cross-file-contract]
root-cause: "Review-producing prompts and phase work reports treated human-readable prose and mutable runner artifacts as if they were stable machine contracts, so /cg-fix-triage compatibility and evidence provenance drifted until a later review re-read the whole surface."
severity: "P1"
---

# Review Artifacts Must Use Machine-Readable Finding Maps and Stable Validation Evidence

## Problem

A full `/cg-review` pass over the Compound Research branch exposed two coupled contract defects in saved artifacts:

- `/cr-review` still instructed the agent to write legacy review frontmatter with `status: open` and `findings: N`, then hand users off to `/cg-fix-triage` as if the report were machine-selectable by finding ID.
- CR phase work reports cited `tests/last-run.json` as durable proof for earlier validation events, even though `tests/last-run.json` is intentionally mutable and overwritten by later test runs.

The branch looked locally healthy because the prose still read sensibly and the latest runner artifact was green. But the workflow contracts were wrong in two important ways:

1. `/cg-fix-triage` consumes a `findings:` status map keyed by finding ID, not a free-form status/count pair.
2. Historical work reports need immutable or run-stamped evidence references, not pointers to a session-local file whose contents change over time.

These defects surfaced as fixed findings `P1.1` and `P1.2` in [.cg-docs/reviews/2026-07-30-cr-scoping-normative-gates-review-2.md](.cg-docs/reviews/2026-07-30-cr-scoping-normative-gates-review-2.md).

## Root Cause

This was a cross-file contract drift problem across prompts, review artifacts, and documentation.

The repository already had the right ideas in separate places:

- `/cg-fix-triage` expects `findings: { P1.1: open|fixed|skipped }`
- review frontmatter is supposed to be the durable machine-readable status ledger
- `tests/last-run.json` exists to decouple test output from agent context, not to serve as an immutable historical record

But the producer and consumer surfaces evolved independently:

1. `/cr-review` kept an older report schema even after `/cg-fix-triage` standardized on per-finding status maps.
2. CR work reports copied the latest green runner artifact path into evidence tables instead of citing the specific validation run that happened at the time.
3. Because each file still looked plausible in isolation, only a branch-wide review that re-read prompts, reports, and tests together exposed the mismatch.

## Solution

Treat saved review reports and work reports as machine contracts, not just narrative documents.

### 1. Align review-producing prompts with the fix-triage schema

`/cr-review` was updated to emit a `findings:` map instead of the legacy `status/findings:N` shape:

```yaml
---
date: YYYY-MM-DD
title: "<description>"
scope: "<files reviewed>"
findings:
  P1.1: open
  P2.1: open
---
```

The prompt now explicitly says to parse all `P[0-3]\.\d+[a-z]?` IDs from the report body and initialize each to `open`, with valid statuses restricted to `open`, `fixed`, and `skipped`.

It also switched its handoff example from bracketed prose IDs to the actual `/cg-fix-triage` command shape:

```text
/cg-fix-triage P0.1
/cg-fix-triage P1
```

### 2. Replace mutable runner-artifact citations with run-scoped evidence text

CR work reports were revised so evidence tables cite the validation run event rather than pretending `tests/last-run.json` is a stable proof object.

Bad pattern:

```markdown
| V10 | passed | . tests/Run-Tests.ps1 -> tests/last-run.json | Full suite recorded 0 failures ... |
```

Safer pattern:

```markdown
| V10 | passed | . tests/Run-Tests.ps1 | Full suite recorded 0 failures on 2026-07-31; this report cites the validation run rather than the mutable `tests/last-run.json` artifact |
```

The key rule is that `tests/last-run.json` can summarize the most recent run, but it must not be cited as immutable historical evidence for an older phase-specific claim unless it is snapshotted or otherwise frozen.

### 3. Co-author prompt assertions in the same fix session

The prompt/schema fix was guarded immediately in Pester:

```powershell
It "Step 5 writes a findings status map for /cg-fix-triage compatibility" {
    ($content -match 'findings:\s*\r?\n\s+P1\.1:\s+open') | Should -Be $true
    ($content -match 'Valid\s+statuses\s+are\s+`open`,\s+`fixed`,\s+and\s+`skipped`') | Should -Be $true
    ($content -notmatch 'status:\s+open\s*\r?\nfindings:\s+N') | Should -Be $true
}
```

That ensured the review producer contract changed at the same time as the prose.

## Prevention

1. When a saved review file is meant to feed `/cg-fix-triage`, its frontmatter must be a `findings:` status map keyed by finding ID. Never use human-readable count/status summaries as the only machine-readable state.
2. Treat review frontmatter as authoritative machine state and review body prose as historical narrative unless the body is intentionally rewritten.
3. Do not cite `tests/last-run.json` as immutable historical evidence in committed reports. Cite the run event, a committed summary artifact, or a timestamped snapshot instead.
4. When fixing prompt-contract text in `.prompt.md`, add the matching Pester assertion in the same session. Prompt schema drift is otherwise invisible until a later verify or review pass.
5. After any shared-state artifact fix, run both the narrow owning suite and the full canonical suite. File-local green tests are necessary but not sufficient for cross-file contract repairs.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md`
- `.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md`
- `.cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md`
- `.cg-docs/solutions/testing-patterns/2026-07-30-review-routing-contract-changes-must-update-all-entry-points-and-coverage-layers.md`
- `.cg-docs/reviews/2026-07-30-cr-scoping-normative-gates-review-2.md`
- `.github/prompts/cr-review.prompt.md`
- `tests/cr-prompts.Tests.ps1`
- `.cg-docs/work-reports/2026-07-30-cr-evidence-provenance-spine.md`
- `.cg-docs/work-reports/2026-07-30-cr-scoping-normative-gates.md`