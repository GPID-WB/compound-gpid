---
date: 2026-08-13
depth: light
parent-review: .cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md
type: verification
plan: .cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md
findings:
  P0.1: open
  P1.1: fixed
  P1.2: skipped
  P1.3: skipped
  P1.4: fixed
  P1.5: skipped
  P1.6: skipped
  P1.7: skipped
  P1.13: skipped
  P1.14: fixed
  P2.1: skipped
  P2.2: skipped
  P2.3: fixed
  P2.4: fixed
  P2.5: skipped
  P2.6: fixed
  P2.7: skipped
  P2.8: skipped
  P3.1: fixed
---

## Verification Review

**Review mode**: verify (light)
**Parent review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md`
**Files reviewed**: current uncommitted Phase 1 implementation and test changes
**Findings**: 19 (P0: 1, P1: 9, P2: 8, P3: 1)

### Suppression Context

Fixed-scope P2/P3 findings from the parent review were not re-raised unless
cross-file behavior made them relevant. P0/P1 findings were never suppressible.

### P0 -- BLOCKING

- **[P0.1]** `scripts/link.ps1`, `scripts/link.sh`, `scripts/update.ps1`, `scripts/update.sh` -- project publication remains incremental and non-rollbackable.
  **Why**: A later copy, marker, preflight, or permission failure can leave mixed project/global state.
  **Fix**: Implement the planned staged, journaled per-root publication boundary.

### P1 -- CRITICAL

- **[P1.1]** `scripts/cg_kilo_preflight.py:397-416` -- host output is buffered by `capture_output=True` before the byte limit is applied.
  **Fix**: Stream bounded `Popen` output and reject over-limit output.
- **[P1.2]** `scripts/link.ps1` copy-directory implementation and `scripts/cg_kilo_copy.py` -- Windows and POSIX synchronizers still diverge.
  **Fix**: Route both platforms through one identical secure synchronizer or prove equivalent behavior with executable cross-platform tests.
- **[P1.3]** `scripts/cg_kilo_copy.py:168-211` -- the copy worker mutates files incrementally.
  **Fix**: Stage and validate a complete generation before activation.
- **[P1.4]** `scripts/cg_kilo_preflight.py:23-24,342-386,586-603`; `scripts/tests/fixtures/kilo_coexistence_host.json` -- host certification lacks immutable executable provenance.
  **Fix**: Add versioned compatibility policy records with executable hashes and refresh evidence.
- **[P1.5]** `roadmap.json` -- direct roadmap edits remain mixed into the worktree and cannot be attributed to this operation.
  **Fix**: Preserve existing user changes and reconcile through `@cg-roadmap`.
- **[P1.6]** `scripts/link.ps1`, `scripts/link.sh`, `scripts/update.ps1`, `scripts/update.sh` -- early host-only and later full preflights repeat version/inventory subprocesses.
  **Fix**: Reuse operation-scoped host evidence while retaining a final race-safe verification.
- **[P1.7]** `scripts/tests/test_kilo_coexistence.py:166-200` -- Codex preservation is not executable evidence.
  **Fix**: Add a Codex-side sentinel inventory assertion or mark the evidence unavailable and blocking.
- **[P1.13]** `scripts/update.ps1`, `scripts/update.sh` -- standalone update does not synchronize project-local Kilo directories.
  **Fix**: Integrate the shared Kilo synchronizer into update flows before final validation.
- **[P1.14]** `scripts/update.sh:162-169` -- the early POSIX preflight masks the worker’s typed exit code with a hard-coded `3`.
  **Fix**: Capture and relay the worker’s actual status.

### P2 -- IMPORTANT

- **[P2.1]** `scripts/cg_kilo_preflight.py` -- projection validation, host discovery, policy, inventory parsing, and launch remain tightly coupled.
  **Fix**: Split responsibilities during manifest/projection work.
- **[P2.2]** `scripts/cg_kilo_preflight.py` -- projection files are rescanned and rehashed repeatedly.
  **Fix**: Reuse one bounded per-operation evidence inventory.
- **[P2.3]** `scripts/cg_kilo_preflight.py` -- executable selection and some filesystem ordering are not fully deterministic.
  **Fix**: Sort candidates and inventory records by normalized and raw paths.
- **[P2.4]** `scripts/cg_kilo_copy.py:180,197` -- preservation warnings are unbounded.
  **Fix**: Emit bounded examples with aggregate counts.
- **[P2.5]** `scripts/cg_kilo_preflight.py` -- compatibility policy is embedded in code.
  **Fix**: Move supported versions, roots, and layouts into a reviewed artifact.
- **[P2.6]** `docs/installation.md`, `docs/reference.md`, `docs/troubleshooting.md` -- command inventories omit `cg-kilo` in several locations.
  **Fix**: Add the certified launcher to all command inventories and recovery instructions.
- **[P2.7]** `scripts/link.ps1`, `scripts/link.sh` -- Kilo linking still mutates global `markdown_source` permissions despite project-local copies.
  **Fix**: Condition this legacy side effect on an actual symlink requirement or retire it after verified evidence.
- **[P2.8]** `.cg-docs/work-reports/2026-08-13-manifest-driven-skill-loading.md`, `tests/last-run.json` -- verification evidence is not durable/current enough for independent reproduction.
  **Fix**: Store immutable command, timestamp, host, commit, and result references.

### P3 -- MINOR

- **[P3.1]** `scripts/cg_kilo_preflight.py:92-102` -- `asdict()` copies the complete inventory before JSON conversion.
  **Fix**: Construct the bounded JSON representation directly if inventory size becomes material.

### Passed Checks

- Python verification surface: `12 passed, 1 skipped`; embedded-host integration passed.
- Shell syntax and `git diff --check` passed.
- Safe Pester gates after fixes: install `90/90`, update `138 passed/2 skipped`, bash guard `1/1`, link `79/79`.
- Fixed-scope findings were not re-raised.

## Conclusion

The fixed scopes converged, but the review cycle remains open because P0/P1
publication, parity, provenance, update, and evidence findings remain. These
must be triaged before the full plan can claim completion.
