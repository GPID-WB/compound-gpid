---
date: 2026-08-13
title: "Final Local Evidence Workbench Review"
depth: full
type: standard
plan: .cg-docs/plans/2026-08-12-cr-local-evidence-workbench-revised.md
scope: "HEAD commit 84afe99, 37 changed files"
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P0.4: fixed
  P0.5: fixed
  P0.6: fixed
  P0.7: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P3.1: skipped
---

# Final Local Evidence Workbench Review

## Review Routing

- Unrecognized invocation arguments `deep rigorous` were ignored.
- Configured `review-depth: thorough` and security/API/dependency/concurrency/schema
  triggers resolved the review to `full`.
- Reviewed commit: `84afe998b63dbd377a17981121ff6ad3ac712d76`.
- Prior commit: `fff446598ba77e064ef1bfd0c7adabbc266238c0`.
- The worktree was clean before review.
- Protected artifacts were not recommended for deletion, replacement, renaming,
  or movement.

## Review Findings

### P0 -- Blocking

**[P0.1]** `research_evidence/src/research_evidence/ui/routes.py:55` -- Source-derived text is inserted through `innerHTML`.

**Why:** A local Markdown resource can contain HTML/event-handler markup. Search results then execute it in the loopback origin, where it can read or mutate the evidence API. The current test only scans the static template for external URLs and does not inject malicious source content.

**Fix:** Construct result nodes with DOM APIs and `textContent` (or a strict sanitizer), add a malicious-source integration test, and add a restrictive CSP.

**[P0.2]** `research_evidence/src/research_evidence/security.py:48, 171, 204` -- Offline enforcement is not wired into the production runtime and is incomplete even when called.

**Why:** `OfflineNetworkGuard` is exercised directly by tests but is not installed around CLI, workbench, API, or model-loading entry points. It only patches TCP connect methods, not UDP `sendto`/`sendmsg`; proxy checks only uppercase variables; and model-loader checks allow alternate download/remote-code flags.

**Fix:** Install the guard at real runtime boundaries, block UDP egress, normalize proxy variables case-insensitively, and enforce a strict model-loader allowlist with explicit boolean types and no remote-code/download/proxy/remote-cache options.

**[P0.3]** `research_evidence/src/research_evidence/workbench.py:224, 381` -- Workbench writes can overwrite the existing CR claim-evidence matrix using a different schema.

**Why:** Existing CR artifacts use `id`, `status: verified`, and nested evidence rows, while the workbench writes `claim_id`, `review_state`, and `evidence_ids` into the same `claim-evidence-matrix.yaml`. Its merge filters only records containing `claim_id`, so existing verified rows can disappear on the next mutation.

**Fix:** Keep workbench state in a separate canonical artifact or implement an explicit schema-validated, non-destructive importer into the CR matrix. Preserve and test existing CR rows through restart and mutation.

**[P0.4]** `research_evidence/src/research_evidence/workbench.py:101-158` -- Rescanning a changed source does not automatically invalidate previously approved evidence.

**Why:** `scan_markdown()` updates source records and the derived index, but does not run lifecycle invalidation for evidence/claims/analysis links. `load_approved_decisions()` filters persisted approval flags and can expose old approvals after a changed source is rescanned.

**Fix:** Compare prior/current source versions during scan, journal invalidation propagation, and fail closed on approved decisions until exact original-authority re-verification succeeds.

**[P0.5]** `research_evidence/src/research_evidence/verification/confidence.py:65-130` -- Unknown source hashes can reach high confidence.

**Why:** `source_hash_matches=None` is not rejected. With an exact quote, available original, and `original_authority_available=True`, the high-confidence branch remains reachable without a confirmed hash match.

**Fix:** Require `source_hash_matches is True` for high confidence; map unknown hashes to `abstained` or review-required medium confidence.

**[P0.6]** `research_evidence/src/research_evidence/reproducibility.py:79-82` -- Reproducibility checks are self-comparisons and do not validate the committed manifest.

**Why:** Both runs use the same in-memory `units` object, and both canonical YAML values are serialized from that same object. The committed JSON is never regenerated and compared. The resulting `passed: true` can miss ingestion, parser, serialization, and artifact drift.

**Fix:** Materialize two independent inputs/runs, compare persisted source/version/locator/verification hashes, hash query/corpus recipes, and add a test that validates the checked-in manifest against a recomputed result.

**[P0.7]** `.cg-docs/research/evidence/dependency-model-inventory.yaml:102+` -- Candidate model profiles use unverifiable `example.org` distribution sources.

**Why:** A candidate profile with `not-acquired` metadata is acceptable only if its source is explicitly unresolved, but an example URL looks like a real distribution source and cannot establish provenance if activated.

**Fix:** Use an explicit `not-acquired`/null source representation or verified real distribution URLs. Activation must require complete source, version, hash, license, and cache evidence.

### P1 -- Critical

**[P1.1]** `research_evidence/src/research_evidence/retrieval/profiles.py:194-215` -- Model activation checks only that a cache directory exists, not its declared hash or canonical inventory identity.

**Why:** Modified weights can run under a declared revision/hash, and profile selection does not require an inventory entry reference.

**Fix:** Require an inventory ID, select through the canonical inventory, and verify a deterministic cache manifest or artifact digest before loading.

**[P1.2]** `research_evidence/src/research_evidence/index/lexical.py:47, 101, 113` -- SQLite thread sharing disables the safety check without acquiring the created `RLock`.

**Why:** FastAPI worker threads can interleave rebuild/search/write operations on one connection, observing partial derived state or triggering SQLite contention.

**Fix:** Acquire the lock around every public connection operation, or use per-thread connections with atomic derived-index replacement.

**[P1.3]** `research_evidence/src/research_evidence/benchmarks.py:231` -- The memory gate measures only `tracemalloc` allocations.

**Why:** SQLite/native allocations and WAL/database footprint are excluded. The reported medium-corpus memory number therefore does not prove the declared process-memory threshold.

**Fix:** Measure normalized RSS plus SQLite/WAL footprint and use those values in the pass/fail gate.

**[P1.4]** `scripts/tests/fixtures/cg_characterization_manifest.json:296` -- Generated-target characterization data is stale.

**Why:** The committed generated `.claude/commands/cr-review.md` hash differs from the fixture. The characterization/release gate fails even though drift/determinism tests pass.

**Fix:** Regenerate the characterization fixture for all affected native target trees and rerun the release gate.

**[P1.5]** `research_evidence/src/research_evidence/compatibility.py:66-120` -- External quarantine is described but not durably persisted.

**Why:** Migration returns an in-memory `MigrationResult`; no `external-quarantine.yaml` is written, so preservation is not guaranteed across restart or migration operations.

**Fix:** Persist quarantine records through the canonical transaction path and test read-only reload, non-indexing, and non-approval.

**[P1.6]** `.cg-docs/work-reports/2026-08-12-cr-local-evidence-workbench-revised.md:4,188,283+` -- Completion evidence is contradictory.

**Why:** The report frontmatter/status and later Phase 5 block disagree with the completed plan and active-state. It contains passed and pending versions of the same final evidence rows.

**Fix:** Reconcile the report to one authoritative terminal status while preserving historical run details as explicitly superseded snapshots.

### P2 -- Important

**[P2.1]** `research_evidence/src/research_evidence/security.py:98-113` -- `validate_browser_target()` is not same-origin enforcement.

**Why:** It accepts arbitrary loopback hosts and ports and does not reject all network-path/backslash forms. A browser target can reach a different local service.

**Fix:** Permit relative paths only, or compare against the exact configured origin and port; wire the validator into every browser/API target boundary.

**[P2.2]** `research_evidence/README.md:48,83` and `docs/reference.md:737+` -- Documentation contradicts itself about browser UI being in v1.

**Why:** The README describes the Phase 4 API/browser surface and later still says no browser UI is part of v1, while the reference page documents it as implemented.

**Fix:** Align the capability statement and add a contradiction regression test.

**[P2.3]** `.github/prompts/cr-work.prompt.md:262+` -- The workbench start/resume instruction is ambiguous.

**Why:** It refers to a “phase command recorded” in active state, but the state exposes `nextCommand` and the Python CLI does not implement phase subcommands.

**Fix:** Explicitly distinguish `/cr-work phaseX` from `uv run --project research_evidence ...` commands and refer to `nextCommand`.

**[P2.4]** `research_evidence/benchmarks/reproducibility-2026-08-13.json` -- The committed reproducibility artifact lacks independent input/environment provenance.

**Why:** It records a unit count and lockfile hash but not the pyproject hash, interpreter/OS/SQLite/package versions, corpus recipe, query identity, or generating command.

**Fix:** Add non-sensitive environment and input digests while retaining `raw_text: false`.

**[P2.5]** `research_evidence/src/research_evidence/benchmarks.py:166` -- `_p95()` underestimates the tail for small samples.

**Why:** With two query observations, it selects the lower value instead of a proper nearest-rank p95.

**Fix:** Use a ceil-based nearest-rank calculation or require a minimum sample count for benchmark claims.

### P3 -- Advisory

**[P3.1]** `cr-lit-review` -- Branch name does not follow the repository’s documented `type/short-description` convention.

**Why:** The branch lacks a `feat/`, `fix/`, or equivalent prefix.

**Fix:** Rename before merge if the convention is enforced.

## Fix Validation

- 112 package Python tests passed, with one existing Starlette/httpx deprecation warning.
- Security, browser, API, lifecycle, compatibility, retrieval-profile, and
  reproducibility regressions passed, including committed-manifest validation.
- Characterization and semantic target-parity checks passed; the two clean-HEAD
  assertions are expected to remain dirty until the review-fix commit is made.
- Canonical Pester runner passed with 2,443 passed, 0 failed, 3 skipped, and
  `filteredFiles: null`.
- Module ownership/dependency/cross-suite validation passed.
- Editor diagnostics were clean.

## Residuals

- P3.1 is skipped because branch renaming was outside the requested review-fix
  scope; `cr-lit-review` should be renamed before merge if the convention is
  enforced.
- The repository Python suite still reports two pre-existing release-fixture
  assertion failures in `test_release_gate_targets.py`; no release files were
  changed by this review fix.
- The design-evidence validator reports a pre-existing stale brainstorm-view
  SHA-256 in `.cg-docs/work-reports/2026-07-31-dual-audience-workflow-artifact-views.design-evidence.json`.

## Review Notes

- Review fixes modified the workbench security, provenance, lifecycle,
  compatibility, benchmark, generated-target, documentation, and test assets.
- Findings from multiple agents were deduplicated by diagnostic class and scope.
- Full route included code quality, testing, documentation, version control,
  reproducibility, performance, architecture, data quality, learnings, adversarial,
  and research-integrity review.
