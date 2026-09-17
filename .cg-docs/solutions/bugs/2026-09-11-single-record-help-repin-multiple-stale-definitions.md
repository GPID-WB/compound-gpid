---
date: 2026-09-11
title: "Single-record help repin blocked by multiple stale definitions"
category: "bugs"
type: "bug"
language: "Python"
tags: [cg-help, catalog, definition-digest, repin, stale-metadata, fixture-gap]
root-cause: "Named maintenance required unrelated definition pins to be current at both entry and prospective validation."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "fixture-gap"
---

# Single-record help repin blocked by multiple stale definitions

## Symptom

Preview and explicit reviewed repin of `shell:cg-brain-init` failed when both its
definition and the unrelated `shell:cg-diff-summary` definition were stale. The
maintenance command returned a source-validation error for the unrelated stale
pin. It could not complete a valid single-record operation.

This is the separate `D3-multi-stale-single-repin-scope` maintenance repair found
during Step 6 of Phase 3 in the
[cg-help plan](../../plans/2026-09-08-evidence-backed-cg-help-command.md).
It is not a defect in the rule that ordinary catalog generation must reject
stale evidence. Severity is P2: the error blocked valid maintenance; this repair
does not establish data corruption or a security failure.

## Expected Behavior Source

The expected behavior source is `user-requirement`, recorded for
`D3-multi-stale-single-repin-scope`: preview or explicitly repin one reviewed,
named record when multiple definitions are stale. Leave every other pin and
metadata field unchanged. Preview must not write. Repin must change only the
selected digest, after full source-set, structural, and security validation.

For the reproduction input, preview of `shell:cg-brain-init` must succeed without
a write. Its reviewed repin must succeed and leave the `shell:cg-diff-summary`
pin stale and unchanged. Ordinary generation and freshness checks must still
fail until every stale record has been reviewed and repinned separately.
These expectations come from the requirement, not from the buggy return value.

## Root Cause

Both maintenance validation boundaries imposed an incorrect freshness scope in
[scripts/help/catalog.py](../../../scripts/help/catalog.py):

1. Entry validation allowed the selected pin to be stale but required unrelated
   pins to be current. An unrelated stale record stopped both preview and repin.
2. Prospective validation of the proposed repin again required every pin to be
   current. Fixing entry validation alone would still prevent the write.

Structural validity and digest freshness had been coupled too tightly for
maintenance. The operation needed the complete source graph to remain valid,
but did not have approval to refresh all stale pins in that graph.

## Reproduction Test

The parameterized test is
`test_multi_stale_shell_definitions_allow_one_record_maintenance` in
[scripts/tests/test_help_catalog.py](../../../scripts/tests/test_help_catalog.py),
with cases `[preview]` and `[repin]`.

The `committed_catalog_source_graph` fixture supplies a complete isolated source
graph and validates it strictly before each injected change. The test changes
only the two named wrapper definitions, verifies the exact stale-record set,
and invokes the actual current-code maintenance CLI. It checks the operation
result, unrelated pins, sidecar bytes, generated catalog bytes, and continued
rejection by ordinary generation. The CLI repin uses `--reviewed`.

Historical red evidence is recorded in the
[work report](../../work-reports/2026-09-09-evidence-backed-cg-help-command.md),
section `Maintenance Repair Evidence Reconciliation`. Reproduction session
`ses_f6eb11f1fffetGPMExL2P9KcR2` established two passing baseline tests and two
new failing reproduction cases before source edits. Both new failures occurred
at the actual maintenance calls because of the unrelated
`shell:cg-diff-summary` stale digest, not during fixture setup. The user then
explicitly confirmed failing behavior and approved the two-boundary diagnosis.

## Test Gap

`fixture-gap`: existing tests covered a single changed definition and rejection
of bulk repin, but did not provide a valid complete graph with multiple stale
definitions for a named maintenance operation. The two baseline tests passed
on complete, strictly current isolated fixtures. They did not assert the buggy
multi-stale behavior. The repair added the triggering data shape and boundary
cases instead of removing strict validation or replacing valid assertions.

## Fix

Named maintenance now supplies `maintenance_definition_id` to
`validate_source_metadata`. This permits stale pins during maintenance entry,
without bypassing validation of any source or record. Ordinary callers do not
supply a maintenance ID, so all their pins must remain current.

Entry validation in `_definition_record` now uses:

```python
source = validate_source_metadata(
    root, maintenance_definition_id=command_id
)
```

For both slash and shell records, stale-pin tolerance excludes the selected
record when `require_current_definition` is true. The proposed repin therefore
must pass this second boundary with its selected pin current:

```python
prospective = validate_source_metadata(
    root,
    maintenance_definition_id=command_id,
    require_current_definition=True,
    source_overrides={metadata_path: updated},
)
```

The implementation retains full schema, inventory, source-set, ownership,
reference, and security checks. It also retains the source-snapshot comparison,
metadata-byte conflict check, unique digest replacement, and atomic replacement
of the selected metadata file. Unrelated stale pins are not refreshed.

Thirty added boundary, invalid-evidence, and conflict cases cover slash-only,
mixed slash/shell, shared-installer changes, no-op repeat repins, unknown IDs,
malformed pins, unsafe or missing sources, inventory/reference/workflow errors,
selected prospective freshness, and source/metadata conflicts. Preview and
failure paths preserve bytes. Ordinary `--write`, `--check`, and `--stdout`
continue to reject stale evidence.

Only the explicitly approved operation-specific response assertion was
corrected: preview reports the stored pin as `currentDefinitionDigest`; a changed
repin reports the old pin as `previousDefinitionDigest` and the new pin as
`currentDefinitionDigest`. No response semantics changed. This narrow correction
does not replace the `fixture-gap` classification for the reported bug.

The six-point red-green proof was independently validated by read-only session
`ses_f6db586faffexGRJ7uQ8xSYemP`. The parent supplied that result and the user's
explicit `confirmed fixed` answer in request `amr_092563eda001yZs71AM5hjSoRe`
before this document was written. The following test results are cited prior
execution evidence, not tests run by this documentation stage:

1. Red phase: both reproduction cases were confirmed failing before the fix.
2. Failure matched the symptom: unrelated stale evidence blocked the selected
   maintenance call, rather than fixture construction.
3. Implementation changes followed the established failing tests and approved
   diagnosis.
4. Green phase: both original reproduction cases passed after the fix and the
   approved metadata prerequisite; 63 other tests were deselected in that run.
5. Existing relevant tests: the unfiltered three-file Python suite passed all
   224 tests, with zero failures, errors, skips, or deselections. Focused
   maintenance passed 34 tests with 31 deselected; metadata/inventory passed
   11 tests with 54 deselected. These counts are separate runs, not additive.
6. Test repair: the missing fixture shape and boundary cases were added, and
   only the approved new-versus-previous response assertion was corrected.
   All other valid assertions were retained.

The work report section
`Metadata Bootstrap Verification And Handoff: 2026-09-11T20:59:16Z` records the
exact commands and exit-0 results from execution leaf
`ses_f6dce1037ffeZxOmYUV64rfAJO`. The unfiltered relevant command was:

```powershell
py -3.12 -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_help_query.py scripts/tests/test_cg_help.py -q --tb=short -p no:cacheprovider
```

The earlier 110-pass, 12-failure, 102-setup-error run was blocked by stale
production metadata and was not full repair proof. Under separate explicit
approval, five descriptive metadata records were corrected, all 15 existing
records were individually reviewed and repinned, and the new `shell:cg-help`
record was reviewed and pinned through the supported tool. Each operation
preserved unrelated pins and complete source sets.

The new record alone used an explicitly approved, one-time temporary zero
digest to satisfy the existing schema before supported preview and reviewed
repin. No placeholder remained when catalog generation ran. This exception
does not authorize automatic initialization, fabricated final pins, bulk repin,
or bypass of source validation in future maintenance.

Strict catalog generation and its freshness check passed before the cited
post-metadata tests; the check passed again afterward with the recorded bytes
unchanged. This document closes only the confirmed maintenance bug. Phase 3
remains active and incomplete at Step 6, with completed phases `[1, 2]`.
Combined V3, focused Pester checks, and the unfiltered phase gate remain open.
Python 3.8, native POSIX filesystem execution, native IDE diagnostics, and host
certification are not established. No later phase, merge, publication, or budget
reset is authorized by this document. Later `cg-work` execution owns repair
closure in the plan, report, active-state, and ledger; none was changed here.

## Lessons Learned

- For a `fixture-gap`, start from a complete strictly valid fixture, then add the
  exact triggering shape. A setup failure is not proof of the reported bug.
- Test named maintenance with several stale records, including shared sources.
  Assert that the selected operation succeeds and unrelated pins stay fixed.
- Separate maintenance freshness policy from structural and security validity.
  Test both entry and prospective validation; do not disable the latter.
- Keep ordinary generation strict. A successful single-record repin does not
  make the remaining stale evidence safe to publish.
- Preserve byte-level no-write and conflict checks, not only parsed values.
  Add invalid-evidence cases while unrelated pins are stale.
- Distinguish preview from repin response fields. Correct only an approved
  assertion error; do not change response semantics to fit the test.
- Require individual source review and explicit repin approval. Do not turn a
  one-time bootstrap exception into general pin-management authority.
- Keep focused repair proof separate from full phase and host validation.

## Related

None.
