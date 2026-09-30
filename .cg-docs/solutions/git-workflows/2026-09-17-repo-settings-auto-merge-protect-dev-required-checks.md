---
date: 2026-09-17
title: "Auto-merge and Protect dev required checks must be verified read-only before release automation relies on them"
category: "git-workflows"
language: "both"
tags: [repo-settings, auto-merge, rulesets, required-checks, verification]
root-cause: "Relying on maintainer repo-settings actions without read-only verification of allow_auto_merge and the exact required-check contexts leaves the auto-merge design unenforced or silently unsupported."
severity: "P1"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
---

# Repo Settings Verification For Auto-Merge And Protect Dev Required Checks

## Problem

The prerelease overlap design needs GitHub-enforced auto-merge on dev:
payload and evidence PRs merge via `gh pr merge --auto`, so "Protect dev"
must require the same checks as "Protect main". First read-only
verification (2026-09-17) found `allow_auto_merge: false` and "Protect dev"
carrying only `deletion` and `non_fast_forward` rules — no required status
checks and no PR review rule.

## Root Cause

Repo settings are maintainer UI state, not code. The plan's V10 gate exists
precisely because a flow that assumes auto-merge is enforced will either
merge early or never, and a flow that skips verification cannot distinguish
"settings not yet applied" from "settings applied".

## Solution

- Verify read-only via `gh api` before relying on the setting:
  `repos/GPID-WB/compound-gpid` must report `allow_auto_merge: true`, and the
  rulesets read must show the exact required-check contexts under the
  expected names.
- When prerequisites are missing, classify per the plan as a blocked-stop
  (V10): "Required-check contexts on dev do not exist under the expected
  names (auto-merge would not be GitHub-enforced; stop and report instead)."
  Never mutate remote settings from the flow; that is a maintainer UI
  action.
- Record who/when: the maintainer performed the action 2026-09-17
  (approximately 21:41Z/22:07Z), and re-verification confirmed
  `allow_auto_merge: true` and ruleset "Protect dev" (id 21338685,
  refs/heads/dev, `strict_required_status_checks_policy: true`, integration
  15368) carrying exactly five required checks:
  1. Pester on macos-14
  2. Pester on windows-2022
  3. Native target Python gate on macos-14
  4. Native target Python gate on windows-2022
  5. PR title follows Conventional Commits
  plus a `pull_request` rule with 0 required approvals and
  merge/squash/rebase allowed. The ruleset `updated_at` (latest verified
  2026-09-17T18:07:26.021-04:00) is recorded as the settings evidence.
- Verify the ruleset is active on the exact target ref
  (refs/heads/dev), not merely present.

## Prevention

- Treat settings verification as a mandatory pre-flight for any automation
  that relies on GitHub enforcement; record the exact contexts verified so
  later drift is detectable.
- Record the maintainer action timestamp and the verified `updated_at`
  together, so "settings verified" means at-or-after the action.
- Missing settings are a blocked-stop with exact remediation, never an
  implicit wait or a bypass.

## Related

- `.cg-docs/solutions/git-workflows/2026-09-17-preflight-receipt-commit-tree-lf-provenance.md`
- `.cg-docs/solutions/git-workflows/2026-09-13-release-controller-authority-and-evidence-boundaries.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`