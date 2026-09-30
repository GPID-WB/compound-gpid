---
date: 2026-09-17
title: "Preflight receipts bind exact commit, tree, LF provenance and owner so one full gate serves one commit"
category: "git-workflows"
language: "both"
tags: [preflight, receipt, provenance, line-endings, clean-clone, ownership, fail-safe]
root-cause: "The ~33-minute native preflight re-ran three to four times against the same release commit because no durable, identity-bound artifact proved a specific clean committed gate had already passed."
severity: "P1"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
reviewed-in: ".cg-docs/reviews/2026-09-16-cg-release-prerelease-automation-phase1-review.md"
---

# Preflight Receipts Bind Exact Commit, Tree, LF Provenance And Owner

## Problem

The v1.2.0.9018/9019 sessions ran the native preflight (~33 minutes) three to
four times per commit (Step 4 gate, Reserve temp-clone re-run, Finalize
re-run, evidence step), pushing a single prerelease past three hours
wall-clock. There was no way for Reserve or Finalize to know a specific clean
commit had already passed the full gate.

## Root Cause

Gate evidence was tied to "the latest local run", not to a durable,
identity-bound artifact. Nothing recorded which commit/tree, which line-ending
environment, and which exact command set produced a success, so every later
phase re-derived confidence by re-running.

## Solution

Phase 1 implemented a canonical receipt protocol:

- `cg_pr_preflight.py --emit-receipt <path>` writes canonical JSON atomically
  (temp file + replace): `schema_version: 1`, `commit_sha`, `tree_sha`,
  `line_ending_provenance` (`core.autocrlf` / `core.eol`), UTC timestamp,
  exact command tuples, per-command exit codes, and a SHA-256 digest over the
  canonical sorted-key JSON. A receipt is emitted only after a complete
  successful committed gate; failed, interrupted, selection-only, or
  non-native runs emit nothing, and a new gate invalidates the previous
  receipt at the supplied external path.
- The receipt lives OUTSIDE the working tree (system temp dir): an untracked
  in-tree receipt would trip the strict clean-checkout guard in Reserve and
  Finalize. Lifetime: gate run through Finalize of the same release.
- `create-release.ps1 -PreflightReceipt` verifies before the temp-clone
  re-run: schema version, digest recomputation, exact commit and tree SHA,
  and LF provenance (`core.autocrlf=false`, `core.eol=lf` — the same
  conditions the re-run enforced). Any mismatch, malformed/missing file, or
  digest failure keeps the full re-run: never fail open, never treat an
  invalid receipt as a pass.
- A read-only `--verify-receipt` interface owns canonical JSON and the
  authoritative command list so PowerShell does not duplicate either. The
  digest is a local corruption check, not a signature or remote
  authorization.

Review-driven ownership repairs (phase 1 review): the producer owns creation
of a fresh LF clone at the exact commit using command-local settings
(`git -c core.autocrlf=false -c core.eol=lf` for clone, checkout and
read-only provenance queries) — no persisted clone config writes, no
elevation; committed CRLF attributes for CMD files are preserved by intent;
exact logical commands with one consistent absolute recorded Python path,
never executed during verification; and exclusive destination ownership
(`<path>.lock`) from before invalidation through publication so concurrent
writers cannot interleave. A caught failure releases the lock; an
uncatchable termination leaves the lock file, so use a fresh receipt path or
remove the stale lock only after confirming no owner is running. No automatic
stale-lock recovery.

## Prevention

- One full gate per commit: bind every reuse to exact commit + tree + LF
  provenance + valid digest.
- Receipts are external to the repository; any in-tree receipt scheme is an
  anti-pattern (breaks the clean-checkout guard).
- Gate consumers fail safe: invalid receipt → full re-run, never acceptance.
- Producer ownership: the party that emits the receipt also creates and
  audits its clean LF clone; do not trust a receipt from an unowned or
  persisted-config environment.
- If a receipt path or its lock is stale, prefer a fresh path; manual lock
  removal requires confirmation that no owner process is running.

## Related

- `.cg-docs/solutions/git-workflows/2026-08-21-pr-ci-preflight-native-target-kilo-capability-gates.md`
- `.cg-docs/solutions/git-workflows/2026-09-13-release-controller-authority-and-evidence-boundaries.md`
- `.cg-docs/solutions/git-workflows/2026-09-17-repo-settings-auto-merge-protect-dev-required-checks.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`