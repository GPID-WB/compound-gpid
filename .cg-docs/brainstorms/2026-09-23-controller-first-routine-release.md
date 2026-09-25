---
date: 2026-09-23
title: "Controller-first routine release with four-part prereleases"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "One controller-backed routine publisher with first-class four-part versions and a shared cutover fence"
tags: [release, prerelease, controller, github-actions, ci-cd, cutover, recovery]
---

# Controller-First Routine Release With Four-Part Prereleases

## Context

PR #179 is merged into `dev` (worktree HEAD `48001ab4`). Bare
`/cg-release v1.2.0.9020` is not a routine operation. The command currently
passes only `plan`, `start`, `status`, and `resume` to the standalone controller;
explicit legacy Bridge and Recovery are not routine fallbacks. The controller
accepts exact SemVer and is disabled in `.release-controller.json`. The prior
Routine draft cannot be used: its read-only authority check cannot prevent a
cutover before a tag or GitHub Release write. The current controller's journal
owner protects controller publishers, not the legacy writer or activation.

The measured `v1.2.0.9018/9019` prerelease flow took over three hours and
repeated preflight and interactive steps. This is historical evidence, not proof
that the newer controller or proposed workflow has passed a live gate. The
September 16 prerelease brainstorm was not continued; this decision starts
fresh from current code and the user's approved CI/CD goal. V12 and V13 remain
pending.

## Requirements

- Provide one supported `/cg-release <tag>` routine path. `vX.Y.Z` is official
  and can use only the verified remote default or configured deployment branch;
  `vX.Y.Z.<build>` is a GPID prerelease and can use any verified same-repository
  remote branch, including `dev`. No stable-branch override for GPID.
- Treat four-part versions as first-class release identities in command input,
  controller policy, line/history/collision rules, persisted request and
  manifest, payload, protected annotated tag, GitHub Release, build artifact,
  final attestation, and active consumers. Do not silently translate to SemVer.
  Preserve existing historical tag bytes and disclose cross-lane ordering
  policy; never infer a stable baseline from a four-part tag.
- Make ownership of publication and controller cutover atomic and shared across
  the legacy Bridge/Recovery writer, controller publisher, and activation path.
  Recheck ownership at consequential boundaries. A read-only enabled flag, a
  prompt instruction, or a local lock is not an enforceable fence.
- Use GitHub Actions already in the project for required CI, source-isolated
  build, protected publication, and exact-run proof. A reviewed release commit
  and required checks precede publication; prereleases then publish without a
  separate human publication approval. Avoid repeated full preflight on
  unchanged inputs. Official approval and protected Pages deployment remain
  separate. A green wrapper with a skipped build is not build proof.
- Preserve branch rules, the existing help-evidence gate, the second evidence
  PR, immutable publication identities, and idempotent recovery. Do not add an
  exact Kilo-version allowlist, an upper runtime version bound, or unrelated
  certification redesign. Keep capability and supported-minimum checks.
- Keep disabled controller setup and workflow guards disabled until a separately
  reviewed activation with real authority and configuration evidence. The
  brainstorm and subsequent plan do not approve settings changes or publication.

## Approaches Considered

### Approach 1: Extend The Controller As The One Routine Publisher

Accept the four-part GPID version as a first-class variant, reuse controller
journal and GitHub Actions jobs, and extend the owner protocol to both legacy
operations and cutover. The command becomes a thin, explicit tag adapter into
the controller's exact request, not a second publisher.

Pros: one routine publication engine, one recovery journal, durable Actions
status, and no parallel maintenance of routine release writers. Cons: the
current strict SemVer parser, branch-to-line mapping, history inventory,
configuration, and trust setup need focused changes. Effort: large, phased.
Recommended: yes, because it minimizes permanent moving parts and supports the
approved CI/CD flow after the safety and activation gates are met.

### Approach 2: Add A GPID-Specific Routine Publisher First

Add a new GPID routine writer around the existing payload and docs process,
share the same owner and cutover fence, and leave the controller disabled until
the controller can adopt the four-part contract later.

Pros: might reach an initial prerelease with less controller setup. Cons: two
publication implementations, split recovery, and a second eventual cutover;
the controller's version contract must still be repaired. Effort: medium for
the first stage and large overall. Recommended: no, because it delays a single
CI/CD release path. Merely adding more authority reads to the legacy script is
not a viable approach: reads cannot close the cutover race.

## Decision

Select Approach 1. The user explicitly selected controller first, confirmed
automatic prerelease publication after reviewed CI, confirmed this minimal
design, and declined added complexity. Use existing GitHub Actions rather than
a new CI service. Submission or a successful CLI exit means a durable request,
not a published or complete release.

The fence design must use one remotely enforced, repository-wide CAS ownership
record with a unique operation/run identity. An activation operation holds the
same exclusive owner while changing the effective writer and must prove the old
publisher is terminal and can no longer bypass it. Both publishing paths must
obtain the fence before any tag, Release, or asset write and retain it through
effect reconciliation. Fresh role and source checks are still required. Review
the actual protected-branch, tag, App, workflow, and credential rules: if they
allow a direct writer or direct activation to bypass the protocol, do not
activate. A timed lease alone is not sufficient. An interrupted owner can be
replaced only after trusted terminal-run proof, credential expiry or revocation,
and reconciliation of exact remote effects; uncertainty remains blocked.

For prereleases, the reviewed PR and exact required CI provide the human
review and test gates; no extra human publication-approval pause is introduced.
The protected publication job still controls credentials. Stable releases keep
their separate approval and protected Pages deployment. GPID rejects the
existing generic `--allow-non-deployment-branch` override instead of exposing
it as an official-release loophole. Existing second evidence PR and help gate
remain required; neither is redesigned here.

## Next Steps

1. **Contract and audit.** Inventory active command adapters, controller
   `versions.py`/`history.py`/`policy.py`, GPID profile, journal schema, current
   payload and attestation code, Node/Python/PowerShell readers, and actual
   metadata paths. Specify exact four-part syntax, numeric bounds, collision
   identity, stable/prerelease precedence and historical cross-lane behavior.
   Do not manufacture a SemVer or PEP 440 projection. Acceptance: a sample
   `v1.2.0.9020` round-trips unchanged from invocation to all records; stable
   ordering and historical identities stay valid; malformed, duplicate,
   occupied, and unsupported projection cases fail closed. Current
   `.release-version.json` is absent; settle its reviewed creation/adapter
   contract before enabling any publisher.
2. **Shared publication/cutover authority.** Design and implement the smallest
   remotely enforced CAS record and broker/permission route both legacy and
   controller can actually use. Require the reviewed activation operation to
   acquire the same owner and prove no legacy job or credential can still write.
   Keep legacy Bridge and Recovery limited to explicit historical purposes.
   Acceptance: fault-inject cutover before/after owner acquisition, source and
   policy validation, intent checkpoint, tag creation/read-back, draft Release,
   asset upload, publication, attestation/hook checkpoint, and owner release.
   In every case at most one authorized writer owns the repository; no
   conflicting tag, Release, or asset is created. A bypass-capable direct write
   or activation is a hard stop, not a test waiver.
3. **CI/CD path and provenance.** Bind verified same-repository source branch,
   source and reviewed release SHAs/tree, policy revision, exact required check
   producer/run/attempt, build workflow and artifact digest, payload bytes,
   annotated tag object/peeled SHA, Release ID and classification, assets, and
   final attestation to one immutable request. Use existing Actions source-build
   isolation and protected publisher; run prerelease docs build proof without
   requiring protected Pages deployment. Keep stable approval and Pages proof
   independent. Acceptance: negative tests reject a foreign/deleted branch,
   stale or skipped check, wrong build attempt, changed payload/artifact/tag,
   missing help evidence, or mismatched Release. A valid prerelease finishes
   without a chat approval pause; a failed post-hook remains published, not
   falsely complete.
4. **Staged activation.** In reviewed changes, supply the real repository ID,
   trusted controller revision and wheel digest, journal root/state branch,
   verified App IDs and scopes, check producer identities, protected tag and
   environment settings, prerelease line membership for `dev`, signing and
   bootstrap/history evidence, and required clean-client bridge receipts.
   Current policy has `enabled: false`, null authority values, only `main` in
   the release line, and a null bridge. Keep it disabled and keep false workflow
   guards until separate maintainer approval and documented sandbox checks.
   Acceptance: an unactivated branch cannot publish; an activation is an
   explicit reviewed state transition under the common owner, with exact
   remote setting and denied-operation evidence. No settings or guard flip is
   implied by merging code alone.
5. **Validation and live acceptance.** Use focused negative/recovery suites,
   cross-platform Windows/Linux/macOS validation and ordinary PR CI. Compare
   minimum supported runtime capability rather than exact Kilo versions. After
   separate activation and live-operation approval, run `v1.2.0.9020` once
   from verified remote `dev`, provided its exact tag and version remain
   unoccupied. Preserve the request/receipt, source and PR, CI, build, tag,
   Release, artifact, attestation, stop/recovery and timing evidence. Target a
   durable tracked handoff within two minutes; report queue, review, build,
   publication, and recovery separately, and measure total wall-clock without
   pretending that local tests prove live speed. V12/V13 remain pending until
   their actual remote acceptance evidence exists.

Stop before any new write when ownership, policy, branch, help evidence, CI,
artifact, or remote identity is missing or contradictory. For unknown tag or
Release write outcomes, read and compare exact remote objects before resuming;
never retry on a mere timeout. Preserve a published tag and Release, do not
silently replace assets, and retry only missing downstream work under renewed
authority. A disabled or unproven controller is not a reason to use routine
legacy Bridge or Recovery. Prepare a separate implementation plan for user
approval before editing source, settings, workflows, or publishing anything.
