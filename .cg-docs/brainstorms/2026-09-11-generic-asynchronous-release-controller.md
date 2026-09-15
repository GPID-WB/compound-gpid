---
date: 2026-09-11
title: "Generic asynchronous release controller"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Small deterministic release controller"
tags: [release, automation, semver, github, performance, migration]
---

# Generic Asynchronous Release Controller

## Context

Replace the current plugin-specific `/cg-release` workflow with a generic release
tool. The reported problem is release sessions that can exceed eight hours.
The current workflow combines change analysis, repeated validation, reviewed
metadata changes, publication, documentation deployment, and a second evidence
PR. A GitHub Release API call is only one part of that process.

This is a Software/Data task with Deep scope. The design changes version policy,
publication authority, CI execution, recovery, and integrations across projects.
The brainstorm started fresh and stayed on the clean `improve-cg-release` branch.
The older release brainstorms were not adopted as the design baseline.

### Researched Facts

| State | Finding | Source and authority |
|---|---|---|
| Established | The project requires reviewed branch-based changes, explicit failures, and protection of secrets. | Current charter: `compound-gpid.md`, Constraints. |
| Established | Current publication accepts three-part stable tags for `main` and four-part pre-release tags for `dev`. | Current code: `create-release.ps1:73-90,127-154,193-228`. |
| Established | Preparation, Reserve, Finalize, and evidence preparation repeat substantial validation. | Current workflow: `.github/prompts/cg-release.prompt.md:195-281,310-430,467-504`; `create-release.ps1:281-302,498-582`. |
| Established | The current updater and payload readers reject SemVer pre-release tags such as `v1.3.0-rc.1`. | Current code: `scripts/update.ps1:89-97,148-182`; `scripts/update.sh:62-68,196-198,232-247`; `scripts/generate-whats-new.js:107-112,158-214`. |
| Established | Release workflow triggers can match an RC tag, but downstream guards reject its format. | Current configuration: `.github/workflows/release-docs.yml:3-5,32-44`; `.github/workflows/release-pages.yml:53-68`. |
| Established | Attestation accepts RC syntax, but its string-based suffix ordering needs correction before use with sequences such as `rc.2` and `rc.10`. | Current code: `scripts/skill_management/services/release_attestation.py:204-219,439-480`. |
| Established | Recent remote release documentation runs completed in seconds; sampled test workflow runs completed in roughly 3-8 minutes. | GitHub run timestamps, inspected 2026-09-11; links below. These are run-level elapsed intervals, not a release-session profile. |
| Historical, corroborated | A former per-path Git process problem was fixed by batching. The recorded gate time fell from 405.57 to 237.24 seconds. | `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md:88-98`; current drift tests retain batching. Do not present this fixed issue as a current root cause. |
| Unavailable | An end-to-end trace that attributes the reported eight hours to individual stages. | No such trace was established in this research. Instrumentation is required; the design does not assume that remote CI alone caused the delay. |

The local Brain query succeeded with index warnings. Its returned historical
claims were checked against current sources. The `open-brain` service was not
available through this session's tools. No release, build, or test was run as part
of the brainstorm.

Observed runs: [release documentation build, about 19 seconds](https://github.com/GPID-WB/compound-gpid/actions/runs/34526121989),
[release documentation deployment, about 30 seconds](https://github.com/GPID-WB/compound-gpid/actions/runs/34526159624),
and [a test workflow, about 6 minutes 47 seconds](https://github.com/GPID-WB/compound-gpid/actions/runs/34529071010).

## Requirements

- Provide a standalone CLI and an equivalent thin `/cg-release` interface. The core must not require a Compound GPID installation, charter, knowledge directory, or skill registry in a target repository.
- Support GitHub first, with provider-specific operations separated from the core. Additional hosting and CI providers are outside the first version.
- Manage one release version per repository. Multiple metadata files and artifacts may share that identity; independently versioned packages are outside the first version.
- Use SemVer 2.0.0 for new release identities. Apply X.Org's development-snapshot, feature-freeze, release-candidate, and stable-maintenance practices without copying its four-part version format.
- Restrict production releases to configured deployment branches, or the remote default branch when no deployment branches are configured.
- Allow pre-releases from any source branch, subject to normal authorization, validation, and GitHub protections.
- Permit an explicit production-branch override only for a verified maintainer or administrator, with a recorded reason and protected-environment approval.
- Resolve versions automatically from release history and the requested release type. Also support an explicit version, without bypassing validation.
- Update declared metadata, changelogs, and version manifests. Create annotated tags, sign when required, push the exact tag, and publish verified GitHub Release assets.
- Target a tracked handoff within 1-2 minutes when dependencies are installed and services are available. Report publication, queue, approval, and build time separately. Submission is not completion.
- Provide step progress, the proposed and final version, structured errors, and safe status/resume operations.
- Preserve published tag identities and existing durable payloads. Retain required GPID completion checks through a project-specific migration profile.

## Approaches Considered

### Approach 1: Small Deterministic Release Controller

Build one policy and lifecycle controller. Reuse maintained SemVer, Git, GitHub,
and signing tools rather than creating replacements for them. Use bounded,
format-aware metadata adapters and the repository's existing CI build commands.

**Pros:** one authority for branch eligibility, versions, signed tags, progress,
and recovery; direct support for any-branch pre-releases; no mandatory AI step.

**Cons:** the team owns the state machine and the supported metadata adapters.
The adapter scope must remain explicit and small.

**Effort:** large, delivered in phases. No calendar estimate is asserted before
implementation planning and measurement.

**Recommended and selected:** yes. The main need is a consistent release
lifecycle, not another release-note generation layer.

### Approach 2: Release Please Integration

Use Release Please for release PRs, changelogs, and metadata updates. Add a
controller for the required branch rules, signing, approval, and recovery.

**Pros:** existing metadata strategies for Python, R, Node, and other project
types reduce custom metadata-update work.

**Cons:** another configuration and versioning system; custom integration is
still needed for the requested publication policy. Release Please explicitly
does not handle complex branch management or package-manager publication.

**Effort:** medium-large, subject to an integration check against the required
edge cases.

**Recommended and selected:** no. Viable if reduced adapter maintenance becomes
more important than a single authoritative release lifecycle. It is not a
drop-in replacement for the full requirement.

## Decision

Select the small deterministic release controller. The design was explicitly
confirmed. The distinction between `plan` and `start` was then explained and
accepted. The optional offer to explore a more sophisticated design was declined.

### Design Challenge

- **Problem validation:** pre-validated by the reported multi-hour sessions. Attribution still requires an end-to-end trace.
- **Simplicity:** do not build a CI scheduler, signing system, or package registry client. Use existing tools and keep AI outside version resolution and publication authority.
- **Effort and value:** remove repeated local gates and long waits first. Do not delay that benefit with multi-provider or independent-package support.
- **Charter alignment:** keep review, required checks, explicit errors, and secret protection. The branch override changes release eligibility only; it does not permit a direct protected-branch push.

### System Architecture and Workflow Diagram

```text
CLI or /cg-release
  |
  +--> Read trusted repository policy
  +--> Resolve branch, source commit, and proposed version
  +--> Show release preview
  |
  +--> Submit tracked request --------------------> Return request ID
                                                    and status link
                         |
                         v
              Trusted GitHub Actions controller
                         |
              Prepare metadata and changelog PR
                         |
              Review and merge under branch policy
                         |
              Bind the exact release commit
                         |
              Required checks and artifact builds
              [isolated jobs; no publishing secrets]
                         |
              Verify artifacts and approval
                         |
              Annotated/signed tag + exact tag push
                         |
              Stage assets and publish GitHub Release
                         |
              Verify remote identities and contents
                         |
              Required project-specific completion hooks
                         |
                       COMPLETE

CLI/chat status <---- Request state, step timings, errors, recovery action
```

The core owns policy, version resolution, request state, publication, and
recovery. Adapters handle metadata formats, GitHub operations, and declared build
outputs. A Python CLI is a reasonable implementation default given the existing
toolchain; package and library selection belongs in the implementation plan.

Use a small request journal and GitHub run records, not a new orchestration
service. Persist approved inputs, request identity, policy digest, source and
release commits, build/run identities, artifact digests, and completed steps.
Define durable storage and retention in the plan. Recovery must not depend on
chat memory, temporary release notes, or an indefinitely retained CI artifact.
Missing evidence requires renewed validation rather than inferred success.

The controller and authorization policy come from a trusted, reviewed revision,
not from the arbitrary source branch being released. Builds execute without
publishing secrets or signing keys. A separate trusted publisher verifies the
outputs. Source branches cannot weaken their own release policy.

GPID documentation, generated-target checks, and skill attestations become
project-specific extensions. They remain required where the GPID profile
requires them, but other repositories do not load or execute them. Evidence that
depends on the final tag identity remains a post-publication completion step.

### CLI and Slash-command Specification

```text
cg-release plan  (--bump TYPE | --version VERSION) [OPTIONS]
cg-release start (--bump TYPE | --version VERSION) [OPTIONS]
cg-release status REQUEST_ID [--watch] [--timeout 10m] [--json]
cg-release resume REQUEST_ID
```

The slash command accepts the same arguments. These are proposed commands, not
commands implemented or executed during this brainstorm.

| Argument | Contract |
|---|---|
| `--bump major`, `minor`, or `patch` | Compute the next stable core. With `--channel`, start a pre-release for that target core. |
| `--bump prerelease` | Continue an established pre-release sequence for the selected source/release line and channel. An unknown or ambiguous target requires an explicit base bump or version. |
| `--channel NAME` | A validated pre-release identifier, such as `dev`, `alpha`, `beta`, or `rc`. Required when the request otherwise cannot identify its sequence. |
| `--version VERSION` | Explicit SemVer value, mutually exclusive with automatic bump inputs. Branch, uniqueness, precedence, and metadata-format checks still apply. |
| `--branch NAME` | Remote source branch; default to the current branch. Detached HEAD requires an explicit branch. |
| `--allow-non-deployment-branch` | Request a production-branch exception; never disable other release gates. |
| `--reason TEXT` | Required audit reason for that exception. |
| `--sign` | Require a signed annotated tag. Repository policy may require signing without this flag; missing required signing capability is an error. |
| `--yes` | Accept the displayed CLI proposal for automation. Does not bypass server-side authorization, review, or approval. |
| `--json` | Structured output for scripts and chat adapters. |
| `--watch`, `--timeout` | Bounded observation through `status`; stopping observation does not cancel the release. |

Example usage:

```text
/cg-release plan --bump minor
/cg-release start --bump minor --channel rc
/cg-release start --bump prerelease --channel rc
/cg-release start --version 2.0.0
/cg-release start --bump patch --allow-non-deployment-branch --reason "Approved emergency release"
/cg-release status REQUEST_ID
```

#### Plan Versus Start

`plan` is a read-only release preview. It calculates the proposed version, checks
branch eligibility, and lists intended changes. It does not write metadata,
create a PR, reserve a version, start a build, create a tag, or publish a release.
It is unrelated to `/cg-plan`, which creates a software implementation plan.

`start` performs fresh checks, shows the proposal for confirmation, and submits
the asynchronous workflow. It returns a request ID and status link, not a
statement that publication has finished. Running `plan` first is optional:
`start` includes the preview and confirmation.

For example, `plan --bump minor` could report `1.4.2 -> 1.5.0` and no changes
made. `start --bump minor` could then report a tracked request in `queued` state.
The earlier preview does not reserve `1.5.0`. A changed baseline or a collision
must be disclosed; the worker must not silently publish a different version
from the approved request.

### Execution Lifecycle and Validation

1. **Load policy.** Use reviewed configuration from the trusted default branch. Configure production branches explicitly; otherwise use the remote default branch. Do not infer deployment authority from names such as `dev` or `release`.
2. **Validate identity and authority.** Bind repository identity, source branch, exact source SHA, and policy revision. Verify the remote branch relationship rather than trusting a local name. Recheck release authority before publication.
3. **Resolve the version.** Use published release history on the selected release line as the baseline, with proper SemVer comparison. Do not use timestamp ordering, raw string ordering, or an unrestricted nearest-tag lookup as the version authority.
4. **Apply branch rules.** Stable releases need an eligible production branch. Pre-releases can originate from any source branch but still require normal checks and authority. A manual version has the same rules as an automatically resolved version.
5. **Check the exception.** A production-branch override needs verified maintainer or administrator authority, a recorded reason, and protected-environment approval. Bind the approval to the actual request and release inputs. If GitHub's repository plan or configuration cannot enforce the approval, report an error instead of weakening the rule.
6. **Prepare reviewed changes.** Update only declared metadata fields, changelog sections, and the version manifest. Use format-aware adapters. A source branch can be the target of its own release-preparation PR; it need not merge to the default branch for a pre-release. Tag the resulting reviewed release commit, not the earlier source SHA.
7. **Build asynchronously.** Run required checks and artifact builds for the exact release commit. Reuse evidence only when commit, policy, toolchain, and required checks match. Keep build execution separate from publishing credentials.
8. **Publish safely.** Serialize conflicting publication attempts, revalidate branch/version state, and create one annotated tag object. Sign if required and push only that exact ref. Stage and verify required assets before final GitHub Release publication. A staging draft is an intermediate state, not a completed release.
9. **Verify remote state.** Check tag-object identity, peeled commit, Release classification and metadata, asset inventory, and digests. Pre-releases must not become the latest stable release. Maintenance releases must not displace a newer stable release merely because they were published later.
10. **Complete or resume.** Continue required project-specific hooks and persist their results. Resume only missing work after remote reconciliation. Never force-move a published tag, replace published artifact bytes, or blindly repeat an uncertain write.

State vocabulary: `queued`, `awaiting-review`, `building`, `awaiting-approval`,
`publishing`, `published`, `complete`, and `failed`. Submission uncertainty must
also be reported explicitly rather than labelled queued or complete without
evidence. A published GPID release can still await required post-publication
evidence before reaching complete.

#### Version Rules and Edge Cases

| Baseline or request | Result |
|---|---|
| Patch from `1.4.2` | `1.4.3` |
| Minor from `1.4.2` | `1.5.0` |
| Major from `1.4.2` | `2.0.0` |
| Minor with channel `rc` from `1.4.2` | `1.5.0-rc.1` when that name is available |
| Continue the established RC sequence | `1.5.0-rc.2` |
| Release the stable target of that sequence | `1.5.0`, with normal production gates |

- Parse numeric components and pre-release identifiers according to SemVer 2.0.0. Reject invalid leading zeroes, empty identifiers, and non-ASCII identifier characters. `rc.10` follows `rc.9`.
- Keep the version separate from its configurable Git tag prefix, normally `v`. `v1.5.0` is a tag name; `1.5.0` is the version.
- Build metadata does not affect precedence and must not be used to evade a version collision.
- Check tag uniqueness across the repository, including reservations and other branches. A source-branch history alone is not enough to prevent duplicate names.
- Make the release line explicit when multiple maintained lines make the baseline ambiguous. A legitimate maintenance release is compared within its declared line, not rejected merely because a newer major exists elsewhere.
- With no authoritative baseline, require an explicit initial version or reviewed bootstrap policy. Do not invent a baseline from unrelated tags or metadata.
- Metadata formats may have different version grammars. Use an explicit, tested projection where supported, and record it in the manifest. Reject an unsupported representation rather than writing an invalid package version or silently changing its meaning.
- Legacy four-component tags require an explicit migration baseline. Do not rename them or silently reinterpret their fourth component as a SemVer identifier.

X.Org contributes the release stages: development snapshots, feature freeze,
release candidates, and stable bug-fix maintenance. New identities use forms
such as `1.5.0-dev.1` and `1.5.0-rc.1`, not X.Org's `.99` or fourth-component
numbering. Semantic compatibility, not the calendar or a commit prefix alone,
governs major/minor/patch meaning.

#### Failure and Recovery Contract

Git tag creation and GitHub Release publication are not one atomic transaction.
A pushed tag without completed publication is a recoverable intermediate state,
not grounds for a force-push or destructive rollback. Persist enough evidence to
resume the exact request. An incomplete managed publication blocks conflicting
later publication; adoption of pre-existing history requires an explicit audit.

Read retries have deadlines and bounded backoff. For writes with uncertain
outcomes, inspect remote state before any retry. Existing objects are reusable
only when their expected identities and contents match. A mismatch produces an
actionable conflict, not an overwrite. A remote tag collision also protects
against publishers outside the controller's concurrency mechanism.

Each diagnostic includes an error code, failed step, request ID, proposed or
resolved version, expected and observed state, and a safe next action. Example:

```text
E_TAG_CONFLICT
Step: publish-tag
Request: release-123
Version: 1.5.0
Expected commit: <approved-release-sha>
Observed commit: <different-remote-sha>
Action: Stop this request and inspect the existing release. Do not move the tag.
```

Never include tokens, signing material, or unsanitized credential-bearing URLs.
Chat uses the same structured events as the CLI; it does not infer success from
silence, a dispatched job, or a successful tag push alone.

### Performance Analysis and Mitigation

The accepted first-version target is a tracked handoff within 1-2 minutes when
dependencies are installed and services are available. It is not a guarantee
that an arbitrary repository builds, gains approval, and publishes in two
minutes. Report service outages and exceeded deadlines explicitly.

| Bottleneck or risk | Mitigation | Measurement |
|---|---|---|
| Agent waits for CI or review | Submit once and continue on the server; use status or bounded watch. | Submission, queue, review, and approval elapsed time. |
| Repeated full validation | One authoritative exact-input gate; reuse verified evidence rather than rerunning identical work. | Gate count and elapsed time per release input identity. |
| Repeated clones and broad filesystem scans | Reuse an isolated workspace within a job, batch Git queries, and cache immutable inputs. | Clone time, files inspected, and subprocess count. |
| Broad AI release-note scanning | Deterministic commit inventory; optional bounded editorial assistance. | Inventory size, scan time, and optional model time. |
| Duplicate builds and deployments | Build once and use verified artifacts downstream; remove duplicate triggers. | Builds per release SHA and artifact cache hit rate. |
| Network stalls | Explicit call/job deadlines, bounded read retries, and uncertain-write reconciliation. | Request latency, retry count, and timeout stage. |
| Queue contention | Record durable request state; do not treat a queued or superseded job as completed. | Queue time and cancellation/supersession events. |
| Repeated recovery work | Resume from verified state; revalidate only missing or invalidated evidence. | Repeated stages and recovery elapsed time. |

The former per-path Git subprocess defect is a lesson and regression test, not
an unresolved cause. The current repeated validation and workflow boundaries
are verified risks, while multi-hour network/build attribution remains a
hypothesis until instrumented.

## Next Steps

1. **Plan the contracts and baseline measurement.** Specify configuration, request journal and retention, trusted-controller bootstrap, event schema, release-line selection, and recovery invariants. Instrument the existing path before claiming an end-to-end speedup. Select maintained libraries after checking their edge-case behavior.
2. **Implement deterministic policy and preview.** Add branch/version resolution and a read-only `plan` command. Test normal versions, pre-release numeric ordering, manual overrides, bootstrap, ambiguous history, and metadata representation errors. Do not couple the core to GPID files.
3. **Implement asynchronous execution and recovery.** Add start/status/resume, trusted GitHub workflow integration, approval verification, exact-commit validation, tag signing, artifact staging, publication, and remote reconciliation. Do not rely solely on Actions concurrency as an indefinitely durable queue.
4. **Add bounded metadata and artifact adapters.** Declare supported formats and fail on unsupported schemas. Reuse existing build commands in isolated jobs. Test one generic repository and representative metadata formats; do not claim support for every ecosystem without adapter coverage.
5. **Migrate GPID readers before writers.** Update both updater implementations, payload/documentation readers, workflow guards, and attestation ordering. Distribute compatibility through an already accepted update channel. Update the trusted controller before the first new-format tag. Preserve old tags, payload bytes, and attestation identities.
6. **Run a measured rollout.** Exercise preview, pre-release, production, approved override, and partial-failure recovery in test repositories. Compare submission and full publication time separately. Enable the GPID profile after its compatibility checks pass.

Required adversarial tests include stale branch tips, changed policy after
approval, concurrent requests, duplicate dispatch, hostile source-branch
configuration, signing failure, lost API responses, mismatched tags/assets,
expired evidence, failed post-publication hooks, and resumable partial
publication. Test both Unix and Windows CLI paths without weakening the
project's Pester safety requirements.

No material design decisions remain open. Library selection, exact storage
mechanics, and timeout tuning remain implementation-plan details that must
satisfy the confirmed contracts. Additional hosting providers, independently
versioned packages, package-registry publication, and a new CI orchestration
service are outside the first version.

The broader reusable-tool direction may justify a later charter update to
Current Focus or Key Deliverables. This brainstorm does not modify the charter,
roadmap, release implementation, or existing artifacts.

### External References

- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): version grammar, precedence, compatibility, and immutable published versions.
- [X.Org version number scheme](https://www.x.org/wiki/Development/Documentation/VersionNumberScheme/): snapshots, feature freeze, release candidates, and stable maintenance; its numbering is not SemVer.
- [Release Please](https://github.com/googleapis/release-please): release PRs, metadata strategies, and stated branch/publication limits.
- [GitHub environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments): approval, secret boundaries, and repository-plan limitations. Unsupported approval capability must fail explicitly.
