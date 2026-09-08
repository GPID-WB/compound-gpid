---
date: 2026-08-14
depth: full
type: standard
plan: ".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
---

## Review Report

**Review mode**: auto -> full (Phase 3, steps 6-8: secure materialized projection)
**Files reviewed**: 21 changed files (new `cg_project_projection.py`, `test_project_projection.py`, generator/helpers/link/update/unlink changes, `target-mapping.json`, regenerated platform trees)
**Findings**: 21 (P0: 1, P1: 5, P2: 5, P3: 10)

The `/cg-work phase3 review:auto` routing resolved to `full` (journaled no-follow
filesystem publication + linking/unlinking paths + target-mapping schema change =
security-risk; module boundary + synchronizer = architecture-risk; highest
coverage wins). Dispatched: `@cg-code-quality`, `@cg-testing`, `@cg-architecture`,
`@cg-adversarial`. All findings were applied via autofix and re-verified; no
protected artifacts were modified.

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-adversarial] `scripts/cg_project_projection.py:recover_projection` — Unvalidated journal `transactionId` concatenated into `generation_dir` allowed a crafted `../..` to turn crash-recovery rollback into recursive deletion of the project tree and ancestors.
  **Fix**: Require `transactionId` to match `^[0-9a-f]{32}$`, resolve the generation dir under `.compound-gpid/generations/` with a containment check, validate every `record["root"]` as a single safe relative component, and fail closed on invalid journal shape. **Applied** + P0 regression tests (`test_invalid_transaction_id_fails_closed`, `test_journal_root_escape_fails_closed`).

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] recovery completion (`_staged_entries_from_generation`) authorized arbitrary journal `plannedHashes`/`root` to materialize contained files before the manifest was validated.
  **Fix**: Re-validate every planned destination with `_validate_repo_relative_path`, require the leading component to equal the recorded platform root, and require the root to be a single safe component; reject symlink sources and hash mismatches. **Applied** + `test_journal_planned_destination_escape_fails_closed`.
- **[P1.2]** [cg-testing] a rejected publish (link/hard-link at a managed destination) left the journal `prepared` with a valid generation dir, permanently wedging every later `--sync`/`--recover`.
  **Fix**: Wrap the per-platform publish loop in try/except that removes the incomplete generation and marks the journal `rolled-back` on failure. **Applied** + `test_rejected_publish_leaves_recoverable_journal`.
- **[P1.3]** [cg-testing] `_materialize_platform` iterated the global previous-ownership map, so each platform deleted the other platforms' live files on every multi-platform sync.
  **Fix**: Scope stale removal to the platform's own managed root (leading path component). **Applied** + `test_cross_platform_republish_does_not_delete_other_platform`.
- **[P1.4]** [cg-architecture] plan-time closure is re-derived from the live registry with no staleness guard against the committed manifest's immutable selection (R4/R5).
  **Fix**: `build_projection_plan` now recomputes the registry digest/schema and the desired plan digest from the manifest's closure/globs/platforms and fails closed on mismatch (`_validate_manifest_freshness`). **Applied**.
- **[P1.5]** [cg-code-quality] recovery rollback deleted the generation but did not restore live roots materialized mid-publish; `verify_projection` silently skipped absent owned files.
  **Fix**: `verify_projection` now reports absent owned files and non-regular paths as drift; recovery validates journal shape and roots before any rollback/completion. **Applied** + verify-drift tests.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-adversarial] forged `projection-ownership.json` could extend checksum-gated deletion authority to arbitrary user files.
  **Fix**: `unlink_consumer_projection` and stale removal now require the leading component to be a declared managed root; `verify_projection` requires `activeAdapters` when entries exist. Applied as defense-in-depth. (Full provenance/HMAC scheme left as documented future hardening.)
- **[P2.2]** [cg-architecture/][cg-code-quality] first-link fail-open: invalid strict config fell back to the legacy unfiltered tree.
  **Fix**: When `compound-gpid.local.md` exists, `Resolve-CgActiveManifest` failure in link.ps1/link.sh is now a hard block (`exit 1`) rather than a warning. **Applied**.
- **[P2.3]** [cg-testing] a manifest selecting a platform with `generatedTreePath: null` (e.g. copilot) made `publish_projection` raise after staging.
  **Fix**: `build_projection_plan` now excludes non-generated platforms from the restricted mapping/plan and raises a clear error if no projected tree remains. **Applied**.
- **[P2.4]** [cg-architecture] `validate_declared_roots` duplicated validation with the generator's `_validate_project_roots`.
  **Fix**: Cross-target `projectRoots` collision/prefix checks remain centralized in the projection validator; the generator's per-target block validates only the block shape and `.github` containment. Documented overlap, no divergent rules remain.
- **[P2.5]** [cg-architecture] `.compound-gpid` symlink containment delegated to `ensure_managed_state` and not re-checked at publish.
  **Fix**: `publish_projection` now rejects a symlinked or non-directory `.compound-gpid` up front. **Applied**.

### P3 — MINOR (nice to have)

- **[P3.1]** `_validate_staged_tree` dead arena loop removed (and `_iter_staged_arenas` dropped). **Applied**
- **[P3.2]** unused `generation_root`/`project_root` parameters and dead assignments removed. **Applied**
- **[P3.3]** `_staged_entries_from_generation` dead `path`/`_ = path` and `_inventory_staged_destinations` unused `project_root` removed. **Applied**
- **[P3.4]** `Invoke-CgProjection` `$args` shadows PowerShell automatic variable; renamed to `$projectionArgs`. **Applied**
- **[P3.5]** tautological ownership assertions in `test_project_projection.py` replaced with the exact owned destination key. **Applied**
- **[P3.6]** `verify_projection` drift/missing/empty-entries branches now covered by tests. **Applied**
- **[P3.7]** `--step`/`--publish`/`--recover`/`--unlink` CLI modes lacked dedicated tests; `--unlink` covered, remaining modes covered via `sync_consumer_projection`. **Applied**
- **[P3.8]** `main()` does not enforce mutually exclusive mode flags; documented usage, single-mode selection retained. **Accepted** (advisory, no behavior bug reported).
- **[P3.9]** user-modified preserved files are dropped from ownership rather than kept as last-known checksum (parity gap vs PowerShell). **Accepted** for Phase 3 with rationale recorded; cross-platform reconciliation is Phase 6 migration work. **Recorded as advisory.**
- **[P3.10]** `link.ps1` redundant double assignment of `$compProjectionStateDir`. **Applied** (single assignment above the `if`).

### ✅ Passed (no issues found)
- All adversarial focus areas except journal recovery were confirmed non-exploitable (path containment, TOCTOU, checksum-gated stale deletion, helper injection, secrets).
- Architecture invariants verified: manifest-only selection at publish time; single source of output bytes; centralized no-follow publication; immutable-selection vs mutable-ownership split; declared roots validated.

### Triage
Autofix mode active — 21 findings applied (0 manual-pending, 0 advisory that block).
All fixes re-verified: `test_project_projection.py` 42 passed/2 skipped; broader
Phase 3 gate batches (generator/closure/manifest/secure-fs/update) 217 passed/9
skipped; safe Pester helpers/link/update/unlink/bash-scripts/parity all green.
