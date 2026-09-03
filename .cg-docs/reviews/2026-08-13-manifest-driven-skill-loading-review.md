---
date: 2026-08-13
depth: full
type: standard
plan: .cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md
findings:
  P0.1: open
  P1.1: open
  P1.2: open
  P1.3: open
  P1.4: open
  P1.5: open
  P1.6: open
  P1.7: open
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
  P2.5: open
  P2.6: open
  P2.7: open
  P2.8: open
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P3.1: open
---

## Review Report

**Review mode**: full (auto-routed security/architecture/install changes)
**Files reviewed**: Phase 1 implementation, tests, installers, and docs
**Findings**: 26 (P0: 1, P1: 12, P2: 12, P3: 1)

### P0 -- BLOCKING

- **[P0.1]** `scripts/link.ps1`, `scripts/link.sh`, `scripts/update.ps1`, `scripts/update.sh` -- publication still mutates project/global state before the complete preflight and lacks a durable rollback boundary.
  **Why**: A later projection or content failure can leave a mixed or partially updated runtime. This is explicitly required by Phase 3's staged/journaled synchronizer and is not solved by the Phase 1 host-only check.
  **Fix**: Implement the Phase 3 secure projection worker with staged validation, durable per-root activation, journaled recovery, and checksum-owned publication before claiming success.

### P1 -- CRITICAL

- **[P1.1]** `scripts/cg_kilo_preflight.py` -- bounded host output still uses `capture_output=True`, so noisy host output is buffered before truncation.
  **Why**: A hostile or broken host can consume memory before the byte limit is applied.
  **Fix**: Use bounded `Popen` streaming reads and reject output beyond the limit.
- **[P1.2]** `scripts/cg_kilo_copy.py` vs. `scripts/link.ps1` -- Windows and POSIX copy implementations are not yet one identical synchronizer.
  **Why**: POSIX now uses the secure worker, while the existing PowerShell path retains separate copy logic and semantics.
  **Fix**: Complete the Phase 3 cross-platform worker integration and remove divergent copy behavior.
- **[P1.3]** `scripts/cg_kilo_copy.py` -- synchronization mutates files incrementally rather than staging and activating a complete generation.
  **Why**: A later failure can leave a mixed projection.
  **Fix**: Complete the Phase 3 staged/journaled publication boundary.
- **[P1.4]** `scripts/cg_kilo_preflight.py` -- host compatibility policy is an exact 7.4.20/7.4.21 allowlist without immutable executable provenance.
  **Why**: A version string alone does not identify the binary used for certification.
  **Fix**: Maintain a versioned compatibility policy/evidence table with executable digests and explicit host refresh evidence.
- **[P1.5]** `roadmap.json` -- current worktree contains pre-existing direct roadmap edits that conflict with the plan's `@cg-roadmap` reconciliation requirement.
  **Why**: Roadmap state cannot be attributed to this operation or reconciled safely by direct JSON inspection.
  **Fix**: Preserve the existing user changes and route the required vendoring contract reconciliation through `@cg-roadmap` in Phase 5.
- **[P1.6]** `scripts/cg_kilo_preflight.py` -- full host inventory is still queried repeatedly across preflight and post-copy gates.
  **Why**: Combined link/update can perform redundant version/inventory subprocesses.
  **Fix**: Cache host evidence within one operation and avoid duplicate probes while retaining final race-safe verification.
- **[P1.7]** `scripts/tests/test_kilo_coexistence.py` -- executable negative coverage now includes Claude/mixed roots, but supported-host evidence does not yet include a Codex-side discovery assertion.
  **Why**: Kilo containment and Codex preservation are separate requirements.
  **Fix**: Add a supported Codex sentinel inventory assertion or record the host-side evidence as unavailable rather than passing it.

### P2 -- IMPORTANT

- **[P2.1]** `scripts/cg_kilo_preflight.py` -- preflight remains a large combined module for projection validation, host discovery, policy, inventory, and launch.
  **Fix**: Split focused responsibilities during the manifest/projection phases.
- **[P2.2]** `scripts/cg_kilo_preflight.py` -- local marker and inventory scans repeat file reads/hashes.
  **Fix**: Reuse one bounded digest/frontmatter inventory per operation.
- **[P2.3]** `scripts/cg_kilo_preflight.py` -- extension candidate ordering and normalized-path tie-breaking should be fully deterministic.
  **Fix**: Sort candidates and inventory records by normalized and raw path.
- **[P2.4]** `scripts/cg_kilo_copy.py` -- preserved-file warnings are unbounded.
  **Fix**: Emit bounded examples and aggregate counts.
- **[P2.5]** `scripts/cg_kilo_preflight.py` -- exact Kilo versions and extension layout should move to a versioned compatibility artifact.
  **Fix**: Move policy data out of the worker while retaining fail-closed defaults.
- **[P2.6]** `docs/installation.md`, `docs/reference.md` -- `cg-kilo` is not yet present in every command inventory/troubleshooting list.
  **Fix**: Complete command-reference documentation in the documentation phase.
- **[P2.7]** `scripts/link.ps1`, `scripts/link.sh` -- legacy global `markdown_source` permission remains an unconditional side effect for Kilo.
  **Fix**: Retire or condition it on actual symlinked command roots after project-local evidence is complete.
- **[P2.8]** `.cg-docs/work-reports/2026-08-13-manifest-driven-skill-loading.md` -- mutable `tests/last-run.json` is not a durable per-command evidence artifact.
  **Fix**: Record immutable command/timestamp/host evidence references in the execution report or dedicated evidence fixture.
- **[P2.9]** `scripts/cg_kilo_preflight.py` -- documentation and validation scope must remain aligned as command/instruction schema checks evolve.
  **Fix**: Keep the docs scoped to managed skill, agent, and `cg-*` command frontmatter until broader checks are implemented.

### P3 -- MINOR

- **[P3.1]** `scripts/cg_kilo_preflight.py` -- `asdict()` copies the inventory before JSON conversion.
  **Fix**: Construct the bounded JSON shape directly if inventory size grows.

### Resolved During Review

- **[P1.8]** Python fallback parity -- `scripts/helpers.ps1`, `scripts/link.sh`, and `scripts/update.sh` now enforce Python 3.8+ before selecting a candidate.
- **[P1.9]** Duplicate POSIX preflight execution -- `scripts/link.sh` and `scripts/update.sh` parse the captured JSON result instead of rerunning the host probe.
- **[P1.10]** Windows launcher exit propagation -- `bin/cg-kilo.cmd` selects a candidate outside probe blocks and relays the child exit code.
- **[P1.11]** Managed-marker safety -- `scripts/cg_kilo_preflight.py` and the secure copy worker reject unsafe marker schema/source/path/checksum states.
- **[P1.12]** Negative containment coverage -- the Kilo tests include ineffective containment plus Claude-only and mixed Codex/Claude cases.
- **[P2.9]** Documentation scope -- installation docs now limit local-content claims to managed skills, agents, and `cg-*` commands.
- **[P2.10]** POSIX recursive-copy hazard -- `scripts/link.sh` delegates Kilo copy-directory synchronization to `cg_kilo_copy.py` and `secure_fs` rather than `cp -R`.
- **[P2.11]** Missing certified launcher source -- both installers fail closed with repair guidance when `cg-kilo` is absent.
- **[P2.12]** Early host gate -- combined Kilo compatibility roots are host-preflighted before link/update mutation; the full staged publication boundary remains open as P0.1/P1.3.

### Passed

- `scripts/tests/test_kilo_coexistence.py`: containment, caller-environment, unsupported-content, Claude/mixed-root, and typed failure coverage passed.
- `scripts/tests/test_kilo_copy.py`: checksum ownership, stale deletion, user preservation, and source-link rejection passed.
- Safe Pester gates: `install` 90/90, `update` 138 passed/2 skipped, `bash-scripts` 1/1, `link` 79/79.
- Real embedded Kilo 7.4.20/7.4.21 host preflight passed with local inventory retained and external compatibility inventory excluded.
- No protected `.github/` source deletion/replacement was recommended or performed.

## Triage Guidance

P0.1 and P1.1--P1.3 remain blockers for the later full projection outcome and
must be resolved before Phase 3 release evidence. P1.4--P1.7 and P2 findings
remain tracked for the relevant later phase; only findings explicitly marked
`fixed` above were addressed during this Phase 1 run.
