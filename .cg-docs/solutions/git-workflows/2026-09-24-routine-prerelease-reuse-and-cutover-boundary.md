---
date: 2026-09-24
title: "Route routine four-part prereleases through the existing publisher without claiming atomic cutover"
category: "git-workflows"
language: "both"
tags: [routine-prerelease, powershell-publisher, cutover, exact-tag-recovery, evidence-boundaries]
root-cause: "A disabled replacement controller could not serve routine prereleases, while repeated remote policy reads could not make the existing tag push and Release POST atomic."
severity: "P1"
plan: ".cg-docs/plans/2026-09-24-legacy-first-routine-prerelease.md"
reviewed-in: ".cg-docs/reviews/2026-09-24-legacy-first-routine-prerelease-review.md"
---

# Routine Prerelease Reuse And Cutover Boundary

## Problem

GPID needed a routine `/cg-release vX.Y.Z.<build>` path while the new release
controller remained disabled. Treating the four-part request as a controller
`start`, or making exceptional Bridge/Recovery the normal fallback, would not
provide that path. A second publisher would also split the established payload,
tag, Release, build, and attestation checks. The reviewed Reserve path has a
separate limit: a controller cutover between the last policy read and tag push
can leave an exact remote tag without a matching GitHub Release.

## Root Cause

The command did not distinguish a normal four-part release from generic
controller commands or exceptional legacy operations. The protected controller
policy is checked at discrete points; no read reserves exclusive authority
over the later Git push and GitHub Release API call. Even the recheck after a
tag push can only stop the Release POST, not undo the push or prevent another
writer from acting outside this publisher.

## Solution

Route a bare four-component tag, and its ordinary `--resume <tag>` form, to
`-LegacyOperation Routine` in the existing PowerShell `create-release.ps1`
Reserve/Finalize flow. Leave generic `plan/start/status/resume`, explicit
Bridge/Recovery, and three-part stable release rules separate. The native
launcher directs bare-tag users to the slash workflow because it cannot
prepare notes and immutable payloads from the tag alone. Require the trusted
remote controller policy to exist and remain disabled at the applicable
authority checks; keep the controller disabled. Reuse the reviewed payload,
exact source and annotated tag checks, preflight, conflict checks, successful
prerelease build, and attestation gates rather than adding another publisher.

```powershell
# After an authorized, reviewed payload and annotated local tag exist:
.\create-release.ps1 -Phase Reserve -LegacyOperation Routine -SourceBranch dev -PreflightReceipt <receipt-path> -Tag v1.2.0.9020 -Name "<approved name>" -NotesFile RELEASE_NOTES.md
# Finalize only after the exact published pair and successful build are verified:
.\create-release.ps1 -Phase Finalize -LegacyOperation Routine -SourceBranch dev -PreflightReceipt <receipt-path> -Tag v1.2.0.9020 -Name "<approved name>" -NotesFile RELEASE_NOTES.md -BuildRunId <build-id> -Prerelease
```

These are workflow shapes, not evidence that either command ran against a live
repository. The source branch must be verified against the protected remote
policy; `dev` here is an example, not a hardcoded prerelease allowlist.

The review found **P1.1**, a cutover race between final authority read and tag
push. It was **skipped by explicit user decision**, not fixed. Routine can push
an immutable tag just as the controller enables; the later authority check
stops before Release POST, but the tag can already trigger docs work. The
updated offline Routine fixture tests this exact after-push interruption:
remote tag identity remains exact and no Release POST occurs (P2.1 fixed).
Stranded-payload guidance now routes ordinary four-part resume to Routine
rather than Bridge/Recovery, and states that resume never creates a tag (P2.2
fixed). This is a bounded partial-publication response, not race-free cutover
or enforced exclusive GitHub API ownership.

For an interrupted reservation, first reconcile the exact raw tag-object ID,
peeled commit, payload, and GitHub Release metadata read-only. A missing or
stale `release-result.txt`, an uncertain push, or a failed POST is not evidence
that either remote object is absent. Never move or delete the tag, blindly
repeat the POST, or rewrite a Release as rollback. An authorized ordinary
`--resume <tag>` uses the existing annotated tag, validates exact identity,
and runs Reserve before build/Finalize; it does not create a local tag. If a
payload has no local or remote tag, confirm tag/Release/attestation absence,
obtain separate authority to create the annotated tag at the exact merged
payload commit, then use the authorized Routine resume. A cutover-stranded tag
needs separate reviewed recovery authority and reconciliation; do not treat
Routine resume or `--auto-approve` as a cutover override.

### Evidence And Limits

- The completed focused plan records isolated safe Pester passes, 41 launcher/
  source-policy pytest passes, 69 help passes, 24 generated-drift passes, and
  help catalog/document checks. These are local, offline implementation checks.
- The later step 7 report initially identified P1.1, P2.1, and P2.2. Its
  frontmatter now records `skipped`, `fixed`, and `fixed` respectively; the
  original review text is historical and still says the findings were open.
- The subsequent safe full Pester artifact `tests/last-run.json` records
  3,221 passed of 3,223 tests, zero failed, and two skipped at
  `2026-09-24T12:40:39Z`. The reported cleanup warning remains a separate
  qualification; the skip names are not supplied by that artifact. This is
  not a new run performed during compounding.
- No live prerelease, production first-use proof, runtime reliability result,
  remote cutover test, or enforcement against other authorized writers is
  established. P1.1 remains an accepted residual risk, not a passed security
  fix or authorization to publish.

## Prevention

- Keep operation selection explicit. A routine prerelease is not a generic
  controller request and does not inherit Bridge/Recovery authority.
- Put tests at the effect boundary: cut over after the tag push and assert both
  exact tag retention and refusal to POST the Release.
- Report tag reservation, Release creation, build, Finalize, and attestation
  separately. Preserve exact identities and require separate authorization for
  repair; never infer live completion from a local green suite.
- Require a separately controlled cutover/publication protocol before making
  any claim of race-free or exclusive publication.

## Related

- [Controller continuation authority and evidence boundaries](2026-09-13-release-controller-authority-and-evidence-boundaries.md)
- [Release source-branch policy](2026-09-17-release-source-branch-policy-clarified.md)
- [Focused Routine prerelease plan](../../plans/2026-09-24-legacy-first-routine-prerelease.md)
- [Step 7 review and finding dispositions](../../reviews/2026-09-24-legacy-first-routine-prerelease-review.md)
- [GPID release command](../../../.github/prompts/cg-release.prompt.md)
