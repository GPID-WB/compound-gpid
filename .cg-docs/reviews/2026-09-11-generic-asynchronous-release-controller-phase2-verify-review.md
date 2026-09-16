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
  P1.5: open
---

# Phase 2 Verification Review

## Result

All seven original repair mechanisms are independently confirmed in their
reported scope. One new P1 cross-file defect remains open. Phase 2 acceptance
must remain blocked until that defect is repaired and verified.

- Original IDs confirmed: 7. Original IDs still open: 0.
- New findings: 1 (P0: 0, P1: 1, P2: 0, P3: 0).
- Total remaining findings: 1 (P0: 0, P1: 1, P2: 0, P3: 0).
- Coverage: 2/2 specs, cg-code-quality then cg-testing, emulated sequentially
  in this dedicated verification session. Not two independent reviewer sessions.
- Incomplete outputs/scopes: 0 within the requested verification scope.
- No implementation edits, prior-review edits, completion metadata changes,
  commits, remote mutations, or Phase 3 work were performed.

## New Finding

### P1.5: Generated Manifests Can Fail Their Own New Validator

**Agents:** cg-code-quality; confirmed by cg-testing and independent probes.

**Evidence:** `packages/cg-release/src/cg_release/metadata.py:182-183,242-254`,
`packages/cg-release/src/cg_release/manifest.py:16-17,39-45`,
`packages/cg-release/src/cg_release/policy.py:96,134-139`, and
`packages/cg-release/src/cg_release/models.py:12,141`.

**Issue:** The new manifest parser validates existing bytes, but the producer
does not validate its generated manifest against that same schema. Policy and
proposal validation accept inputs that the manifest reader rejects. The first
call returns a successful, hashed edit set; reapplying that exact set fails with
`E_MANIFEST`. This violates the Phase 2 validated-edit-set and reapplication
contracts in the plan at lines 413-423 and 597-604.

Two separate triggers were executed using the standard offline snapshot and
the public `create_proposal` boundary:

1. Add a second build artifact with a distinct name but the same path,
   `dist/package.whl`, and set `max_artifacts` to 2. Policy checks unique artifact
   names, not unique paths. The proposal succeeds and emits duplicate manifest
   outputs. The new reader rejects them at `manifest.py:44-45`.
2. Set `tag_prefix` to 64 ASCII `v` characters and request the valid SemVer
   `1.0.0-` followed by 190 ASCII `a` characters. The prefix and version each
   satisfy their current limits, and the combined 260-character tag passes
   `safe_ref`. Proposal creation succeeds. The new manifest reader rejects the
   tag because `Manifest.tag` uses `Name`, which has a 255-character limit.

For both probes, all returned edit bytes were placed in a replacement in-memory
snapshot and the identical proposal arguments were reused. The second call
returned `E_MANIFEST`. No checkout file was written. A first direct-validator
probe also reproduced duplicate-output rejection; its uncaught domain exception
was a diagnostic probe result, not a claim of an uncaught CLI product error.

**Fix:** Validate the generated manifest before returning any edit set. Align
the producer and reader constraints: reject duplicate/case-aliased output paths
in trusted policy, and enforce or consistently support the combined tag length.
Keep strict existing-manifest validation. Add public proposal and full-edit-set
reapplication regressions for both triggers, including the accepted boundary.
Every returned manifest must be accepted by the supported manifest reader.

This is a new producer/reader contract failure exposed by the repair, not a
repetition of the original P1.2 malformed-existing-input defect. No invalid
manifest was published; Phase 2 submission remains disabled.

## Original Finding Verification

Paths in this table are relative to `packages/cg-release/`.

| ID | Result and implementation evidence | Executed regression evidence |
|---|---|---|
| P0.1 | Confirmed. `src/cg_release/json_edit.py:25-40,76-85` validates the complete document without float conversion, then replaces only the selected string token. `metadata.py:99-100` uses this path. Unrelated bytes and numeric lexemes remain intact; invalid JSON raises a typed metadata error. | `tests/test_phase2_repairs.py:20-66`: underflow, overflow, long decimal, signed zero, nested values, escaped pointer segments, array indices, and CLI success/error events. Existing duplicate/type/missing-field and multi-field tests also pass. |
| P1.1 | Confirmed. `src/cg_release/source.py:133-155,204-209` binds the permission response to the authenticated numeric actor ID and verifies standard `role_name` against the legacy permission mapping. `policy.py:229-249` retains maintainer/admin override checks. Unknown/custom/missing/contradictory roles fail closed. | `tests/test_phase2_repairs.py:110-162`: actual maintain/write and admin/admin envelopes succeed through acquisition and proposal; write, triage, read, custom, contradictory, and missing roles fail. Numeric actor binding was checked in source; this report does not claim a new actor-mismatch test. |
| P1.2 | Original defect confirmed fixed. `src/cg_release/metadata.py:182-183` invokes strict `manifest.py:26-61` validation before replacement. Absence remains permitted; invalid existing schemas/shapes are rejected. The separate generated-output mismatch is P1.5 above. | `tests/test_phase2_repairs.py:69-107`: malformed/duplicate/unknown schema and fields, wrong types, unsafe paths, and supported prior manifest. `tests/test_metadata.py:173-199` proves ordinary complete-set byte-idempotence. |
| P1.3 | Confirmed at the documented gh argv boundary. `src/cg_release/github.py:126-145,248` passes exact endpoint `graphql`, separate `--raw-field query=...`, explicit GET, and the selected hostname. | `tests/test_phase2_repairs.py:165-205` checks public/Enterprise routing keys and argv. `tests/test_github_reads.py:115-152` retains 101-ref cursor pagination and repository/object identities. No live Enterprise result is claimed. |
| P1.4 | Confirmed. `src/cg_release/source.py:182-195` selects one line and resolves the version before choosing the adopted notes commit. `versions.py:143-169` shares the baseline rule; core bumps select stable history, while explicit promotion and RC continuation use relevant history. | `tests/test_phase2_repairs.py:208-247` checks stable 1.4.2 plus future 1.5.0-rc.1: patch uses the stable commit; promotion and continuation use the RC commit. `notes.py:28-46` still rejects diverged comparisons; its baseline guard was not weakened. |
| P2.1 | Confirmed. `src/cg_release/cli.py:117-171,176-185` uses one injected clock/deadline, records actual interactive input through TimingRecorder, and extends the deadline only by that measured interval. Recheck expiry remains enforced; no submission timing is invented. | `tests/test_cli.py:81-160`: accept, decline, EOF, interrupt, 500-second synthetic human wait, lower policy timeout, expiry before confirmation, and combined acquisition/recheck expiry. Normal plan/yes/noninteractive behavior remains tested. |
| P2.2 | Confirmed for bounded direct-child capture. `src/cg_release/process.py:15-90` concurrently bounds both byte buffers, kills on overflow, and reaps the child. `source_blobs.py:105-111` rejects excessive advertised blob size before retrieval. | `tests/test_bounded_capture.py:13-85`: real stdout/stderr producers exceed 512-byte limits while still running, return E_RESPONSE_SIZE, and are reaped; dual streams/nonzero status, timeout, and pre-download rejection pass. General descendant-tree supervision is not claimed. |

## Sequential Spec Results

### 1. cg-code-quality

Completed the source repair review with the Python skill, anti-pattern reference,
and local Python instructions. Reported P1.5 for the producer/reader schema
contract. No additional actionable issues found in this verification scope.
Ruff passed. Cosmetic refactoring suggestions inside explicitly fixed blocks
were suppressed under verification rules; P0/P1 and cross-file issues were not.

### 2. cg-testing

Completed test review after the source review. Independently reproduced P1.5
through the public proposal and reapplication boundaries. The passing suite
does not cover these two manifest-output edge cases. No additional findings.

The changed process spies retain their intended behavior checks:
`test_contracts.py:230-288` checks separated argv, cwd, capture limit, unsafe
arguments, and typed/redacted timeout/tool/OS failures; actual Popen assertions
for `shell=False`, pipes, unbuffered capture, and cwd remain in
`test_bounded_capture.py:20-25`. Status/resume tests prohibit Popen at
`test_contracts.py:174-190`. No weaker mock of a removed subprocess.run boundary
is used for the repaired production wrapper.

Cross-file checks included metadata projections and alias rules, preview digest
rechecks, strict model loading, notes transport, source read-only acquisition,
timing records, and installed-wheel behavior. Existing dirty-worktree and
state-journal prerequisite tests passed. Signing fingerprints and environment
names remain requirements, not proof of signing capability or actual approval.
`preview-not-submitted` remains a preview identity, not a durable receipt.

## Test Evidence

| Check | Result |
|---|---|
| Fresh independent locked Python 3.12 package pytest | 243 passed in 8.36 seconds, including wheel/sdist build, isolated install, and real bounded producers |
| Fresh native preflight pytest | 52 passed in 0.46 seconds |
| Fresh Ruff over package source/tests and benchmark | Passed |
| Fresh `git diff --check` | Passed for tracked diffs; not a check of untracked package bodies |
| Independent generated-manifest probes | Both first proposals succeeded; both exact reapplications failed with E_MANIFEST |
| Latest supplied full Pester, checked in `tests/last-run.json` | passed=true; totalCount=2906; passedCount=2904; failedCount=0; skippedCount=2; failures=[]; filteredFiles=null; ranAt=2026-09-11T19:51:46Z; gitSha=b94f585 |

Fresh commands:

```text
uv run --project packages/cg-release --python 3.12 --locked pytest packages/cg-release/tests -q --tb=short -p no:cacheprovider
python -m pytest scripts/tests/test_cg_pr_preflight.py -q --tb=short -p no:cacheprovider
uv run --project packages/cg-release --python 3.12 --locked ruff check packages/cg-release/src packages/cg-release/tests scripts/benchmark_release.py --output-format concise --no-cache
git diff --check
```

Pester was not rerun in this verification session. The known TestDrive cleanup
missing-path/nonempty-directory caveat is retained; successful temporary-folder
cleanup is not claimed. Passing Pester and Python tests do not refute P1.5.
No live target GitHub/Enterprise request, release publication, remote CI matrix,
or cross-platform process-supervision test was performed. Synthetic clock tests
do not measure submission speed.

## Scope And Knowledge

Authority was the exact execution report at
`.cg-docs/work-reports/2026-09-11-generic-asynchronous-release-controller.md`,
lines 769-806 and 817-924, especially its verification handoff at 908-919;
the parent review including its Authorized Repair section; and plan Steps 3-4.
Local review verification, routing, context-loading, and report rules were read.
Protected artifacts, Phase 1 reports, and unrelated dirty-worktree changes were
left unchanged. Generated views, caches, distributions, and environments were
not review evidence.

Open-brain tools were unavailable. A bounded local `cg-index query` succeeded
with a 600-token budget and 594 index warnings. Its relevant lesson was to keep
non-404 provider errors distinct from absence, from
`.cg-docs/solutions/build-errors/2026-03-19-invoke-restmethod-bare-catch-swallows-non-404-errors.md`.
The existing HTTP classification tests retain that behavior. No Brain or saved
project-memory artifact was changed.

Only this new verification report was written. The parent must make the Phase 2
evidence/completion decision; this report does not advance the plan or reset any
repair/recovery budget.
