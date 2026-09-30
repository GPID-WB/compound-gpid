---
date: 2026-09-11
depth: light
type: verification
parent-review: .cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-review.md
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P1.5: fixed
---

# Phase 2 Final Verification Review

## Result

P1.5 is independently verified fixed. No new actionable finding or cross-file
regression was found in the requested scope. All seven prior confirmations are
preserved. The parent retains the Phase 2 completion decision.

- Newly verified IDs: 1 (P1.5).
- Prior confirmations preserved: 7. Total confirmed fixed: 8.
- Remaining findings: 0 (P0: 0, P1: 0, P2: 0, P3: 0).
- New findings: 0 (P0: 0, P1: 0, P2: 0, P3: 0).
- Specs completed: 2/2, cg-code-quality then cg-testing, emulated sequentially
  in this verification session, not two independent reviewer sessions.
- Incomplete scopes/outputs: 0 within the requested verification scope.

## Authority And Scope

Read the exact execution report
`.cg-docs/work-reports/2026-09-11-generic-asynchronous-release-controller.md`,
lines 926-996, including the Final Verification Handoff at 974-992. Read the
Phase 2 parent review and its P1.5 repair section, and the prior independent
report
`.cg-docs/reviews/2026-09-11-generic-asynchronous-release-controller-phase2-verify-review.md`.
That prior report remains the evidence source for the seven original independent
confirmations; this pass does not repeat the full Phase 2 review.

Primary scope: policy.py, metadata.py, manifest.py, and test_manifest.py under
`packages/cg-release/`. Cross-file checks covered the strict model constraints,
public proposal construction, safe_ref callers, existing-manifest rejection,
metadata reapplication, and prior repair regression tests. The Python skill,
anti-pattern reference, local Python instructions, and both requested agent
specs were applied. Open-brain tools were unavailable; no project-memory or
Brain update was made.

## Sequential Spec Results

### 1. cg-code-quality

No findings. P1.5 is fixed by checks at both boundaries, without relaxing the
supported manifest schema:

- `packages/cg-release/src/cg_release/policy.py:137-144` checks artifact names
  and paths separately. Path uniqueness uses casefold, matching the reader at
  `manifest.py:44-45`.
- `policy.py:51-75` rejects complete refs longer than 255 characters.
  `preview.py:102` applies it to prefix plus resolved version, not just either
  part. This matches `models.py:12` and `manifest.py:16-17`. Policy branches and
  adopted tags already use the same Name constraint; inspected source and
  GitHub branch callers still reject invalid refs before their remote read.
- `metadata.py:253-256` validates the exact serialized manifest bytes before
  adding the manifest or returning the edit tuple. The edits collected earlier
  are local data, not published partial output. Direct producer callers cannot
  bypass this final reader check.
- `metadata.py:182-183` retains validation of existing manifest bytes.
  `manifest.py:26-61` retains strict schema, path, projection, and tag checks,
  with a typed E_MANIFEST diagnostic for existing or generated invalid input.

The proposal digest is still calculated only after a complete valid edit set
exists (`preview.py:156-190`). No new write or submission path was introduced.
Ruff passed. No cosmetic refactoring was requested for previously fixed blocks.

### 2. cg-testing

No findings. Inspected and freshly executed all 13 P1.5 parameterized cases in
`packages/cg-release/tests/test_manifest.py` as part of the full package run:

| Evidence | Confirmed behavior |
|---|---|
| Lines 18-36 | Exact and case-aliased duplicate artifact paths fail policy validation and the first public proposal with E_POLICY. |
| Lines 39-50 | Complete 256/260-character tags fail the public proposal with E_REF. This includes the original 260-character trigger. |
| Lines 53-83 | Complete 254/255-character tags with two distinct outputs succeed. The returned manifest passes the reader; all returned edit bytes replace the in-memory source blobs; the identical proposal arguments produce identical path/content pairs. The second manifest also passes the reader. |
| Lines 86-115 | Direct producer calls reject duplicate/case-aliased outputs, an overlong tag, bad source SHA, empty line/request identity, and an unsafe output path with E_MANIFEST. |

These tests exercise real policy, proposal, producer, and reader functions,
without mocks between those boundaries. The accepted cases compare all edit
bytes, not only the manifest. Their input digests are not expected to stay equal
after reapplication; the content-idempotence assertion is the correct contract.
Existing malformed-manifest and numeric-preservation tests remain in place and
passed. The full suite also passed its CLI, timing, bounded-process,
source-acquisition, and installed-wheel checks.

## Prior Confirmations

The prior verification's evidence and limitations remain unchanged. The fresh
full package run is additional regression evidence, not a claim that every
original static review was repeated.

| ID | Preserved confirmation |
|---|---|
| P0.1 | Exact JSON token edits preserve unrelated numeric lexemes and bytes; typed invalid-input behavior remains tested. |
| P1.1 | Verified standard role/permission envelopes control maintainer override eligibility. |
| P1.2 | Strict existing-manifest validation remains active; P1.5 now closes the separate generated-output mismatch. |
| P1.3 | Exact graphql endpoint and separate query argument retain the documented public/Enterprise routing contract. No live Enterprise claim. |
| P1.4 | Notes use the baseline selected for the resolved version, including stable patch versus future RC history. |
| P2.1 | Actual confirmation timing and shared-deadline accounting remain tested with injected clocks. No measured submission-speed claim. |
| P2.2 | Bounded direct-child stdout/stderr collection and advertised blob-size rejection remain tested. No general descendant-tree guarantee. |

## Test Evidence

| Check | Result |
|---|---|
| Fresh locked Python 3.12 package pytest | 256 passed in 8.43 seconds, including the 13 P1.5 cases and build/install tests |
| Fresh native preflight pytest | 52 passed in 0.44 seconds |
| Fresh Ruff over package source/tests and benchmark | Passed |
| Fresh git diff --check | Passed for tracked diffs; not a whitespace check of untracked package bodies |
| Supplied full Pester gate, checked in tests/last-run.json | ranAt=2026-09-11T20:07:43Z; gitSha=b94f585; passed=true; totalCount=2906; passedCount=2904; failedCount=0; skippedCount=2; failures=[]; filteredFiles=null |

Fresh commands:

```text
uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider
uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release/src packages/cg-release/tests scripts/benchmark_release.py --output-format concise --no-cache
git diff --check
```

Pester was not rerun in this session. Preserve the known TestDrive cleanup
missing-path/nonempty-directory caveat; successful temporary-folder cleanup is
not claimed. No live GitHub/Enterprise call, remote CI matrix, release
publication, or cross-platform supervision check was performed.

## Change Boundary

Only this review report was manually written. No implementation, prior review,
execution report, completion metadata, protected artifact, or Phase 1 artifact
was edited. No commit, push, remote mutation, Phase 3 work, or later pipeline
command was performed. Existing unrelated worktree changes were left intact.
This report does not advance phase status or reset any repair/recovery budget.
