# Release Skill Management Changes

Release uses two separate complete gates.

1. While the current public commands remain active, run all operation evidence,
   authoritative native preflight, full unfiltered safe-runner Pester, docs,
   modules, target dry-run, and Windows/macOS/Linux plus Python 3.8 CI.
2. Record exact-tree evidence, then stage public registration and old-surface
   removal as one changeset generated from canonical source.
3. Run the complete final-tree gate and exact-tree CI again. A failure keeps the
   prior released tree active.

Future releases that cover plugin deprecations also create a reviewed
post-release attestation bound to the annotated tag object, peeled commit,
immutable release payload, and deprecation-record digests.

The new [release controller](../../../release-controller.md) preserves these
evidence requirements. Payloads are reviewed before the release tag; the
post-tag attestation is a separate reviewed evidence PR that never moves that
tag. `published` is not `complete` until required documentation and evidence
hooks are remotely verified. Historical payloads and attestations remain unchanged.

The supplied publisher stays disabled. Bridge delivery, native clean-client
qualification, registered release-mode CI and sandbox/performance proof are
deferred, not passed. This does not defer ordinary PR CI or the authorized final
committed-input gate. Legacy bridge/recovery requires explicit maintainer
authorization and retains the old permission, branch, payload and tag checks.
