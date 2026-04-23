---
date: 2026-04-23
title: "Review convergence: mode:verify for /cg-review"
status: decided
scope: "Standard"
chosen-approach: "mode:verify argument on /cg-review"
tags: [review, fix-triage, convergence, workflow, prompt-design]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Review Convergence: `mode:verify` for `/cg-review`

## Context

The `/cg-review` + `/cg-fix-triage` cycle never converges. Each fix round
generates new findings on the fix code itself — especially "missing test for
the fix you just added" (22% of review-2 in the competitive-review-system
task) and cross-file reference drift from renames. Evidence:

- **competitive-repo-review-system**: 3 rounds (27 → 26 → 27 findings)
- **prompt-prose-compression**: 4 review files

The system has no mechanism to distinguish "fresh implementation review" from
"verify the fixes landed correctly." Both use the same agent dispatch with
the same instructions, so agents treat fix code as new surface area.

## Requirements

1. **Convergence contract**: full review → fix → verify → fix → done. The
   second verify pass must return zero new findings.
2. **P0/P1 findings on fix code are never suppressed** — correctness issues
   must always surface, even in verify mode.
3. **P2/P3 findings on fix code are suppressed** when they are direct
   consequences of an applied fix (e.g., "no test for 3-line guard clause,"
   "renamed function should use shorter name").
4. **Cross-file breakage always surfaces** — if a fix broke a reference in
   an untouched file, that's a real finding regardless of severity.
5. **Verify mode is opt-in** — existing workflows unchanged. User must
   explicitly pass `mode:verify`.
6. **Light depth forced** — verify passes only run `@cg-code-quality` +
   `@cg-testing`.

## Approaches Considered

### Approach 1: `mode:verify` argument on `/cg-review` (CHOSEN)

Add `mode:verify` to `/cg-review`. When set:
- Auto-locate the most recent review file with ≥1 `fixed` finding.
- Pass prior review file to agents with suppression policy.
- Force `light` depth.
- Save as `<stem>-verify-review.md`.
- Update `/cg-fix-triage` Step 5 to suggest `mode:verify`.

**Pros**: Explicit, follows existing `mode:autofix` pattern, clean file naming.
**Cons**: User must remember the argument.
**Effort**: Medium.

### Approach 2: Automatic verify detection

`/cg-review` auto-enters verify mode when it detects a recent review file
(same plan, ≥50% fixed, within 7 days). No argument needed.

**Pros**: Zero friction.
**Cons**: Magic behavior, needs escape hatch (`mode:fresh`), confusing when
user wants a genuine fresh review on the same files.
**Effort**: Medium.

### Approach 3: Separate `/cg-verify` prompt

New prompt dedicated to verification.

**Pros**: Clean separation.
**Cons**: Duplication of Step 0 boilerplate, agent dispatch, report saving.
Another prompt to maintain and document.
**Effort**: Large.

## Decision

Approach 1: `mode:verify`. Explicit opt-in via the existing argument pattern.
Agents receive the prior review as context plus a clear suppression policy:
- P0/P1: always report, never suppress.
- P2/P3 on fix code: suppress if direct consequence of an applied fix.
- Cross-file breakage: always report regardless of severity.

## Next Steps

1. Add `mode:verify` argument parsing to `/cg-review` Step 1 (alongside
   `mode:autofix`).
2. Add Step 1.7 (or similar): locate prior review file, extract fixed
   findings, build suppression context.
3. Add suppression policy text to agent dispatch in Step 2 (only when
   `mode:verify`).
4. Force `light` depth when `mode:verify`.
5. Update save-filename pattern: `<stem>-verify-review.md`.
6. Update `/cg-fix-triage` Step 5 handoff to suggest `mode:verify` instead
   of plain `light`.
7. Update `docs/reference.md` and `docs/workflow.md` with the new argument.
8. Add tests for `mode:verify` argument recognition and suppression policy
   presence in prompt-tools.Tests.ps1.
