---
date: 2026-09-11
title: "Generic asynchronous release controller"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-11-generic-asynchronous-release-controller.md"
language: "Python"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
execution-report: ".cg-docs/work-reports/2026-09-11-generic-asynchronous-release-controller.md"
completed-phases: [1, 2, 3, 4, 5, 6, 7]
phases: 7
tags: [release, automation, semver, github, migration, security]
---

# Plan: Generic Asynchronous Release Controller

## Objective

Implement a standalone deterministic release controller with `plan`, `start`,
`status`, and `resume`, plus a thin `/cg-release` interface. Return a durable
request identity and status link within 120 seconds under the measured service
conditions. Do not equate submission with publication or completion.

Publish from the exact reviewed release commit. Keep production branch rules,
protected approval, signed or annotated tags, artifact verification, safe
recovery, and required GPID completion checks.

## Context

The decided brainstorm is the design authority. The user approved the displayed
seven-phase completion contract on 2026-09-11 with: "Approve the contract and
continue". That approval permits this plan, its review, and finding resolution;
it does not authorize implementation, remote setup, secrets, or releases during
the planning session. The stored deviation policy is `ask`.

The work fits the charter's release deliverable and reviewed-change constraints.
The reusable-tool direction does not amend the charter's Current Focus. Older
completed release plans are migration context, not implementation baselines.
There was no matching controller plan or roadmap feature during research.

### Current Evidence

| Source | Consequence for this plan |
|---|---|
| `create-release.ps1:53-90,193-302,419-582` | Existing Reserve/Finalize publication has useful exact-commit and uncertain-write guards. Retain their invariants, not repeated local full gates. |
| `.github/prompts/cg-release.prompt.md:13-173,286-504` | Current command is GPID-specific and handles preparation, publication, waits, and evidence PRs. Replace its orchestration only after the compatibility gate. |
| `scripts/update.ps1:85-97,148-243,348-386,690-705`; `scripts/update.sh:60-68,192-301,396-438` | Both readers reject SemVer pre-releases. Selection, labels, persisted pins, and ordering also need tests. |
| `scripts/generate-whats-new.js:107-214` | Payload grammar is legacy. Chronological history display is not the version-precedence authority. Keep old payload bytes. |
| `.github/workflows/release-docs.yml:27-94`; `release-pages.yml:29-152` | Existing exact-run inventories are useful; guards assume main/dev and old tag grammar. One-day artifact retention is not durable recovery storage. |
| `scripts/skill_management/services/release_attestation.py:204-219,223-343,439-480` | Suffix string ordering is unsafe for numeric pre-release identifiers. Preserve existing attestations and removal-grace semantics. |
| `research_evidence/pyproject.toml` and `uv.lock` | Local precedent supports a separate `src/` package, Hatchling, uv, Pydantic, Loguru, and pytest. Locked dependencies are not proof of installed dependencies. |
| `.github/shared/target-mapping.json`; `scripts/cg_generate_targets.py` | `.github/` remains canonical. Generate Claude Code, Codex, OpenCode, and Kilo outputs; Copilot uses canonical assets. |

### Brain Findings

- Migrate actual reader grammar and workflow guards together; tag-trigger matching alone is insufficient. Source: `.cg-docs/solutions/bugs/2026-08-14-pages-immutable-ref-gate-rejects-dev-series-pre-release-tags.md`.
- Bind trusted publication to commit, run, inventory, and digests. Adapt the old main-only policy to the new source-branch rules. Source: `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`.
- Define irreversible operations and reconcile uncertain outcomes before retry. Source: `.cg-docs/solutions/bugs/2026-08-03-generic-publisher-secure-deletion-and-cross-platform-gates.md`.
- Preserve batched Git queries and measure each stage. The former per-path Git defect is already fixed; it is not a current explanation for eight-hour sessions. Source: `.cg-docs/solutions/bugs/2026-08-26-release-drift-ignore-checks-spawn-thousands-of-git-processes.md`.
- Test real CLI protocols and exact committed inputs, not incomplete mocks. Source: `.cg-docs/solutions/testing-patterns/2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md`.

The budgeted local Brain query succeeded with index warnings; these lessons
were checked against current files. `open-brain` was unavailable. No end-to-end
trace establishes the cause of the reported eight hours. Do not claim a measured
speedup until Phase 7 has comparable results.

### Approved Scope Revision 2026-09-13

Decision `D-2026-09-13-defer-live-rollout`, approved by the user in the
2026-09-13T13:36:27Z continuation under `deviation-policy: ask`:

> Defer Live Rollout
>
> Explicitly revise acceptance to finish local implementation, documentation,
> reviews and the PR. Record bridge delivery, live CI, sandbox trials and
> performance proof as deferred, not passed. Keep the publisher disabled.

This decision changes delivery acceptance, not publisher controls. Current scope
is local implementation, offline verification, documentation, reviews, and the
ordinary PR pipeline. The bridge, release-mode live CI, native clean-client
qualification, sandbox trials, and measured performance proof remain required
before a separately authorized live rollout. They are deferred, not passed.
Ordinary PR CI is not deferred. The committed exact-input gate remains a final
pipeline obligation after the planned pipeline step 11 commit is authorized.
That pipeline step is not this plan's implementation Step 11 (reader migration).
Do not move the commit earlier to satisfy V8 or call prepare-mode evidence a
committed gate. V8 remains pending until its retained pipeline obligations pass.

This dated decision takes precedence over earlier phase/final-gate timing clauses
that required live rollout evidence during local delivery. The original objective,
R1-R19, design/security contracts, rollout procedures, and historical evidence
remain intact as the future rollout requirements. The historical V6-V8 acceptance
rows are retained below. No runtime guard, bridge prerequisite, protection, or
independent review finding is waived. No speedup or 120-second live handoff is
claimed without the later measured evidence.

The current continuation may finalize Phase 6 under the explicit V6 exception.
Phase 7 remains for the parent to start; no implementation, activation, remote
operation, commit, push, or PR creation is authorized by this reporting operation.
See the execution report's dated Accepted Exceptions section for rationale,
evidence, qualifications, and the V8 sequencing obligation.

## Requirements

| ID | Requirement | Source |
|---|---|---|
| R1 | Standalone deterministic CLI; no target-repository dependency on GPID files or AI | Brainstorm Requirements and Architecture |
| R2 | GitHub first; provider operations separate; one managed release identity per target repository | Brainstorm Requirements |
| R3 | Strict SemVer, numeric identifier precedence, explicit release lines and bootstrap, global identity collision checks | Brainstorm Version Rules |
| R4 | Stable releases use configured production branches or remote default; pre-releases may use any same-repository source branch | Brainstorm Execution Lifecycle |
| R5 | Stable branch override requires current maintainer/admin authority, reason, and protected approval bound to inputs | Brainstorm Requirements and Exception |
| R6 | `plan` is read-only and non-reserving; `start` confirms fresh inputs without requiring a prior plan | Brainstorm Plan Versus Start |
| R7 | Durable requests, structured progress, deadlines, status, bounded watch, and remote-reconciling resume | Brainstorm CLI and Recovery |
| R8 | Small declared metadata/changelog adapters; explicit version projections; reviewed preparation PR | Brainstorm Metadata and Workflow |
| R9 | Exact reviewed release commit; trusted controller/policy; source builds without publishing secrets | Brainstorm Architecture and Lifecycle |
| R10 | One verified exact-input gate and build; evidence reuse requires matching provenance | Brainstorm Performance and Lifecycle |
| R11 | Annotated tag object; signing when requested/required; exact ref push; immutable published objects | Brainstorm Publication and Recovery |
| R12 | Stage and verify assets before publication; verify remote tag, Release, metadata, digests, and latest classification | Brainstorm Lifecycle |
| R13 | Serialize conflicting publishers; durable reservations; lost-response reconciliation without destructive rollback | Brainstorm Recovery |
| R14 | Separate submission, queue, review, approval, build, publication, and recovery timings; measured handoff target | Brainstorm Performance |
| R15 | Migrate GPID readers before enabling writers; preserve legacy tags, payloads, pins, and attestations | Brainstorm Migration |
| R16 | GPID-specific required docs, target, payload, and attestation/evidence hooks; published differs from complete | Brainstorm Architecture and Completion |
| R17 | Equivalent CLI/slash behavior on all five platform targets; Windows and Unix installation and operation | Brainstorm CLI and Testing |
| R18 | Adversarial failure tests and actionable, redacted error events | Brainstorm Recovery and Testing |
| R19 | No additional provider, independent-package release graph, registry publisher, or new CI service | Brainstorm Out of Scope |

## Design Contracts

These choices close implementation details left to this plan. They are not
permission to bypass the charter, workflow permissions, or GitHub protections.

### Package and Dependencies

- Add `packages/cg-release/` with a `src/cg_release/` package and console entry point `cg-release = cg_release.cli:main`. This layout isolates it from root scripts and `research_evidence`.
- Use Python 3.11 or later for the new package, tested on 3.11 and 3.12 on Windows, Linux, and macOS. Existing Python 3.8-compatible scripts must not import this package or acquire its minimum version.
- Use Hatchling and a committed `uv.lock`; use `semver` 3.x (`Version.parse` and comparisons, minimum 3.0.4), Pydantic 2.x for strict boundary models, Loguru for redacted stderr diagnostics, `tomlkit` for TOML edits, and `packaging` for checking supported PEP 440 projections. Lock concrete tested versions in Phase 1.
- Use stdlib `argparse` and argv-based Git/GitHub CLI subprocesses with explicit working directories and timeouts. Reuse the pattern in `scripts/issues/gh_process.py`, not its GPID imports. Do not introduce GitPython, a second HTTP transport, a daemon, or a plugin discovery framework.
- Use `pytest`, Ruff, and `build` as development tools. Structured command output goes to stdout through an output writer; logs go to stderr. Never place credentials in argv, URLs, event payloads, or journals.
- The controller's installation version is separate from the version it manages in a target repository. Only declared target metadata participates in that target's one-version contract; unrelated manifests such as `research_evidence/pyproject.toml` are not automatically changed. No PyPI publication or global installation is part of this plan.
- Use narrow modules: `cli.py`, `models.py`, `policy.py`, `versions.py`, `journal.py`, `lifecycle.py`, `github.py`, `process.py`, `metadata.py`, `publisher.py`, and `events.py`. Split only when a responsibility exceeds the project limit or is independently reusable.

Add `.github/workflows/release-controller-ci.yml` in Phase 1. Run offline package
tests, locked install, wheel/sdist build, and installed-wheel smoke checks on
Python 3.11/3.12 across Windows/Linux/macOS. Run on `pull_request`, `merge_group`,
and pushes to configured integration branches, without a path filter that
could leave a required check pending. Each matrix job uses the requested
interpreter explicitly, not uv's machine default. A stable aggregate check
`release-controller-ci` requires all six matrix jobs and Ruff to succeed;
cancelled, skipped, or absent results fail the aggregate.

The same workflow also provides `workflow_dispatch` for release validation,
independent of branch filters. The trusted controller dispatches its workflow
definition on the protected default ref with only a sealed journal build-request
locator and dispatch nonce. A separate trusted registration job validates that
request, records the actual run/attempt and controller SHA, and outputs the
bound release SHA to the unprivileged matrix. Each cell explicitly checks out
that exact release SHA, uses its lockfile, and runs its tests without control or
publication credentials. Only this trusted dispatch path may use the protected
registration environment; ordinary PR/push matrix runs need no such secrets.
Phase 1 supplies the interface and ordinary offline CI; Phase 4 connects and
tests registration/dispatch after Phase 3's journal exists. Do not mark the
release-mode gate available during Phase 1.

For release admission, accept matrix evidence only as the tuple of trusted
workflow path/revision, registered request/source SHA, dispatch nonce, actual
run/attempt, six required cell job identities/conclusions, Ruff result, and
successful `release-controller-ci` aggregate. Query the trusted run/jobs APIs;
an aggregate name or job-output string alone is not evidence. A default-ref
dispatch run's `head_sha` is the controller revision, so it is not compared to
the release SHA. Ordinary PR/merge-group evidence is not a substitute for this
release-mode run. The completed matrix can be reused only for the exact reuse
key. This route must work when a preparation PR merges or squashes to a final
SHA on a branch outside every integration-branch push filter.

Extend `scripts/cg_pr_preflight.py` with a separate controller-package impact
route and locked subprocess command for `packages/cg-release/`, its CI workflow,
and direct integration sources. Update `scripts/tests/test_cg_pr_preflight.py`
to prove package-only changes select it. Keep the native test list and Python
3.8 route intact; the package subprocess requires Python 3.11+ and reports a
missing runtime explicitly. Register the aggregate workflow/producer identity
in the GPID profile's required checks. Ordinary package-only PRs must not pass
by running only the old native selector. Live sandbox tests stay opt-in and
outside these ordinary offline matrix jobs.

### Trusted Policy and Bootstrap

The target policy is `.release-controller.json` on the protected remote default
branch, read at an exact commit. The source checkout's copy is never authority.
Reject unknown schema versions, unknown fields, duplicate keys, missing required
controls, unsupported formats, and unresolved repository identity.

Policy schema v1 declares: repository numeric ID and host; tag prefix; production
branches; named release lines and their branch memberships/core bounds; optional
reviewed bootstrap and legacy baseline records; metadata adapters; changelog;
build argv, working directories, toolchain lock paths and declared artifact
inventory; required check producer/workflow identities; controller package pin;
state branch; GitHub App identities; allowed signing fingerprints; normal and
override publication environments; timeouts; and an optional GPID profile.
`enabled: false` is the initial publishing state.

Bootstrap is an explicit maintainer operation through a reviewed setup PR and
repository settings. Install pinned workflow templates on the default branch;
pin the controller source revision/wheel digest and every external Action to an
immutable commit. Create a non-code `release-controller-state` branch and
rulesets which deny deletion/force-push and restrict its updates to the control
App. Protect release-tag patterns from update/deletion. No source build job may
request the control or publishing credentials.

Store control App credentials in default-ref-restricted environments, never as
unrestricted repository secrets. Admission/preparation jobs use `release-control`.
The control App writes journal and preparation branches and opens PRs; it cannot
bypass review of code branches or update protected release tags. A distinct
publishing App is available only in `release-publish` or `release-override`.
Those environments require reviewers, prevent self-review, disallow admin
bypass, and restrict the trusted workflow ref. Verify these capabilities before
admission; unsupported repository plans/settings fail closed. GitHub environment
ref matching does not establish source-branch eligibility; the controller does
that separately. App permissions and rulesets are verified in sandbox tests.

For normal requests, require current repository write/maintain/admin permission.
For a production-branch exception, require maintain/admin, a nonempty bounded
reason, and `release-override` approval. Read permission to a public repository
does not permit publication. Recheck the original requester and the current
resuming actor before consequential operations. `--yes` is only CLI confirmation.

The trusted publisher also needs control-App journal authority. Make the
control-App credential available inside each protected publication environment,
in addition to the distinct publication-App credential. The publisher uses
the control token only for journal operations and the publication token only
for release/tag/asset operations. This explicit v1 co-residence avoids a second
workflow handshake before every journal checkpoint. It is permitted only in a
fresh trusted publisher job after approval; neither token is passed through job
outputs/artifacts or exposed to any source-executing job. GitHub App tokens are
repository-scoped, not magically ref-scoped: enforce the ref restrictions through
verified rulesets and through the trusted operation allowlist.

| Job | Environment | Credentials and writes | Source execution |
|---|---|---|---|
| Admit/prepare/control | `release-control` | Control App: journal, declared prep branch, PR; no protected tag or code-review bypass | None; parse source files as data |
| Build-request registration | `release-control` | Control App: bind sealed request to actual run ID/attempt | None |
| Source build | None | Read-only checkout token; GitHub artifact-upload capability only | Exact requested source, isolated runner |
| Artifact verifier/pre-approval seal | `release-control` | Control App: verified inventory and immutable approval record | None; artifacts are data |
| Publisher/recovery publisher | `release-publish` or `release-override` | Control App for journal; distinct publishing App for exact release writes; signing key if required | None |
| GPID hook builder | None | Read-only source access and artifact upload only | Declared unprivileged hook |
| GPID hook verifier/deployer | Appropriate protected trusted environment | Only journal or Pages permissions required by that job; no untrusted scripts | None |

The publisher writes intent/checkpoint updates directly with its control-App
token. In order: acquire the publication owner, persist exact signed tag bytes,
persist tag-write intent, push/reconcile the tag, record the result, then repeat
intent/write/reconcile/result for draft, each asset, and final publication.
Cancellation between any two actions leaves sufficient journal data for a new
trusted recovery job. The publication App alone must fail a journal-ref update;
the control App alone must fail a protected-tag update. Sandbox tests verify
both denials and this job topology rather than assuming the names enforce it.

### CLI and Version Resolution

Implement the brainstorm's exact four-command interface and flags. Add
`--line ID` to `plan` and `start` to make its explicit release-line requirement
usable. `--bump` and `--version` are mutually exclusive; `--channel` is an
automatic-bump input and cannot modify an explicit version. `--branch` names a
remote branch in the target repository; forks are not source branches in v1.
Detached HEAD requires `--branch`. Resolve remote URL, repository ID, ref, and
exact SHA; never trust a local branch label or nearest tag alone.

Use only published, non-draft Releases adopted into the selected line's trusted
history. Paginate Releases and refs; verify exact refs and peeled commit
identities. An audited bootstrap records historical Release IDs, tags, commits,
line, and legacy-to-new baseline without renaming tags. If no baseline exists,
require an explicit initial version or reviewed bootstrap. Branch-to-line
mapping must select exactly one line, or `--line` must resolve it. Core bounds
are explicit numeric bounds, not an unlisted range-library dependency.

Stable bumps use the highest stable baseline in the selected line. A base bump
with `--channel` starts `<next-core>-<channel>.1`. `--bump prerelease` continues
exactly one established target-core/channel sequence in that line; ambiguity
requires an explicit core bump or version. Channels are one nonnumeric ASCII
SemVer identifier; ordered channel transitions use an explicit version, not a
hidden alpha/beta/rc ranking. Stable promotion uses `--version <target-core>`.
Require every proposed identity to be valid, within its line, and newer than
the relevant adopted baseline. A newer major on another maintenance line does
not prohibit a valid patch on the selected line.

Keep version and tag prefix separate. Ignore build metadata for precedence and
collision identity; it cannot bypass a reservation or published version. Check
all branches' managed refs, drafts, journal reservations, and adopted history,
not just source ancestry. Malformed managed history, conflicting duplicate
identities, or incomplete managed publication blocks admission with a specific
error. Unrelated non-release tags are excluded by explicit policy, not guessed.

`plan` performs reads only: no journal write, issue, dispatch, PR, build, tag,
version reservation, Git fetch into the user's checkout, or metadata edit.
`start` recomputes the proposal and shows source SHA, policy SHA/digest, line,
baseline, version, tag, metadata changes, signing, approval route, and request
digest. Confirm once. After confirmation, changing these inputs fails with a
stale-proposal error; neither server nor client silently chooses a new version.

### Durable Submission and Journal

Use GitHub Issues as the durable admission inbox, not as publication authority.
Before its first write, `start` creates and emits a portable provisional
`REQUEST_ID`: `rc1.<base64url-canonical-json>`. Its strict, size-bounded payload
contains host, repository numeric ID and routing slug, requester numeric ID,
random nonce, and confirmed proposal digest. It contains no credential and
does not grant authority. `--json` uses JSON Lines: a `submission-intent` event
emits the locator before the write, followed by one final receipt/error event.
Human output also shows it before submission. A provisional locator is not a
queued receipt. Callers can retain it even if the create response is lost.

`start` then creates one issue containing the bounded schema-v1 request JSON
and matching locator fields. It returns a verified receipt with issue node/number
and status URL only after reading back matching content and author. The request
is then `queued` with admission `pending-validation`; this means durable
submission, not approved execution. `status REQUEST_ID` and `resume REQUEST_ID`
accept the same portable locator before or after sealing. Resolve it against
the exact issue author/nonce/digest and immutable journal mapping, never labels
or title. A routing slug change requires verifying the unchanged repository ID.
Issues must be enabled; do not silently substitute an ephemeral dispatch.

The trusted default-branch workflow accepts `issues: opened`, explicit
`workflow_dispatch` wakeups, and a five-minute scheduled recovery scan. Wakeups
are hints; the durable issue/journal inventory is the queue. A missed event,
Actions concurrency eviction, full queue, or cancelled run cannot delete a
request. A scheduled scan uses paginated issue IDs and durable cursors; it must
eventually revisit unsealed requests and unfinished journal records. A backlog
is reported; the five-minute schedule is not a queue-latency guarantee.

Before sealing, verify repository, authenticated author, current permission,
request schema/digest, exact inputs, and that the issue has no body edit history
(`lastEditedAt`, `userContentEdits`). Reject edited or unverifiable inbox data;
neither labels nor comments are executable instructions or approval. Persist
the validated immutable request in the app-controlled state branch. Later issue
edits cannot change sealed inputs. A missing/deleted unsealed issue is an
explicit failure, never inferred admission.

The journal uses per-request JSON records and an append-only event history in
ordinary Git commits on `release-controller-state`. Each write records the
expected parent state commit, revision, prior event digest, and next state. Use
non-force fast-forward ref updates with a commit parented to the observed head.
Concurrent sibling updates conflict; re-read, validate the transition, and retry
within a bound. Never force-update, reset, or rewrite the journal branch. Protect
it against other writers at bootstrap. A branch rewrite, unexpected writer,
missing event, or schema mismatch blocks recovery.

Admission atomically records the request and its normalized version reservation
in the same journal update. Duplicate nonce/digest reuses one request; the same
nonce with different content is a conflict. On an uncertain issue-create result,
search and paginate the remote inbox for the exact nonce/author/digest before
any retry. If absence cannot be established, return `E_SUBMISSION_UNKNOWN` and
the provisional locator; do not create a second request or label the first one
queued. `status` and the discovery part of `resume` resolve that locator
read-only, including from a second machine with no local files. An unresolved
lookup stays unknown and never reissues issue creation; an ambiguous match
stops with a conflict. After exact resolution, resume may dispatch reconciliation
only with fresh authority checks. Retrying start without the retained locator
is not a recovery procedure; document this explicitly.

Retain requests, event history, approved policy snapshots/digests, source and
release SHAs, PR/review IDs, check results, run IDs/attempts, toolchain identities,
artifact names/sizes/digests, approvals, exact public tag-object bytes, remote
Release/asset IDs, errors, and hook results for the repository lifetime. Keep
secrets, build trees, raw unbounded logs, and large binary artifacts out of Git.
Document a maintainer-controlled mirror/backup and restore procedure; automatic
retention or journal compaction is outside v1. Actions logs are supplementary.
Before publication, expired artifact bytes require a new isolated build and
fresh approval; after publication, verified Release assets supply durable bytes.
Missing required evidence is never restored from chat memory.

### Lifecycle, PR, and Build Binding

State progression is `queued -> awaiting-review -> building -> awaiting-approval
-> publishing -> published -> complete`. `failed` records the failed step,
retryability, and last verified checkpoint; it does not erase prior publication.
Every externally mutating step has a durable intent before the write and an
observed result after reconciliation. Resume follows remote state, not a cached
success flag. Both status and JSON errors include request/version, current step,
expected/observed state, timings, and safe next action.

Prepare one request-specific branch and PR against the selected source branch.
Make only declared metadata, changelog, and release-manifest changes. Compute
the expected tree from the approved source SHA and bounded edits. Verify the
PR's reviewed head, merged status, review/check requirements, and resulting
release commit. Merge, squash, and rebase are accepted only when the final tree
matches the approved expected tree and GitHub's merged-PR record identifies that
commit. Reject unrelated source additions or edited release metadata. A moved
source base requires a new confirmed request, not an automatic rebase. Do not
merge a pre-release branch into default merely to publish it.

After binding the release SHA, invoke a trusted workflow from the default
controller revision and check out that SHA as data/source in a separate build
job. Do not dispatch a workflow definition from the arbitrary source branch.
Builds run on fresh GitHub-hosted runners with read-only repository permission,
no publishing/signing/control secrets, `persist-credentials: false`, no shared
writable cache with privileged jobs, and no execution in a privileged
`pull_request_target` context. Build argv and working directories come from
trusted policy. Source hooks execute only inside the unprivileged job.

Before source execution, a trusted registration job reads the sealed build
request and binds its digest and dispatch nonce to the actual GitHub run ID and
attempt in the journal. This job runs separately from source builds and uses
only the trusted workflow/controller revision. A duplicate registration loses
the journal claim and cannot produce accepted evidence. Record separately:
`controller_workflow_sha/ref`, workflow path, `release_source_sha/tree`, request
and dispatch identity, run ID/attempt, and eventual artifact IDs. The workflow's
`head_sha` must match the trusted controller ref at dispatch, not the arbitrary
source SHA checked out later. The trusted build template checks out only the
registered release SHA, verifies HEAD before executing source, and does not
accept a source-written claim as the checkout identity.

Evidence reuse key: repository ID, release SHA/tree, policy and controller
digests, required-check set plus producer identities, build argv, lockfile
digests, toolchain/runner identity, and profile version. Verify run ID/attempt,
workflow/controller identity, sealed source binding, successful required jobs,
artifact ID belonging to that registered run, byte digest,
and complete file inventory through trusted GitHub metadata and a separate
verifier. A status name alone, PR test-merge SHA, skipped job, or source-written
manifest is not sufficient. Failed/cancelled/timed-out evidence is not reusable.
The verifier treats artifacts as untrusted bytes, never executable files. Two
release commits can share a controller workflow SHA; substituting an artifact
from the other registered run must still fail. Do not copy the old tag-triggered
`run.head_sha == release_sha` check into this default-ref dispatch model.

### Metadata and Artifact Scope

Support exactly these v1 adapters; other schemas fail before submission:

| Adapter | Allowed representation | Validation and limits |
|---|---|---|
| JSON field | Declared JSON Pointer string field; exact SemVer | Strict parse; preserve unrelated values; reject duplicate keys, missing/type-mismatched fields, and multiple edits to the same field. |
| Python project TOML | Static `[project].version` | `tomlkit` preserves unrelated content. Stable maps directly; `alpha.N -> aN`, `beta.N -> bN`, `rc.N -> rcN`, `dev.N -> .devN`. Validate syntax and history monotonicity with `packaging`; reject dynamic version fields, arbitrary channels, compound suffixes, and build metadata. Record canonical and projected versions. |
| R DESCRIPTION | Stable `Version` only | Parse DCF, preserve unrelated fields and continuations. Reject SemVer pre-releases rather than inventing an R package projection. |
| Changelog | One explicit Markdown insertion marker | Insert deterministic reviewed notes once; reject missing/duplicate markers. Commit inventory is authoritative; AI editorial text is optional and never selects version or authority. |
| Manifest | `.release-manifest.json`, schema v1 | Canonical version/tag, request ID, source SHA, policy digest, release line, projections, and expected build outputs; no self-referential release SHA/tag-object digest in the reviewed commit. |

For each declared Python distribution and release line, compare the proposed
projection against its adopted projected release history as well as comparing
the canonical SemVer history. Both orders must increase. Missing projection
history requires an explicit audited baseline, not a value inferred from the
working tree. For example `1.5.0-beta.1 -> 1.5.0-dev.1` increases in SemVer but
decreases from `1.5.0b1` to `1.5.0.dev1`; reject it before submission. Conversely,
`dev -> alpha` on the same core fails canonical SemVer ordering. Supported
channel paths are the intersection of the two orders, such as `alpha -> beta
-> rc -> stable` or `dev -> rc -> stable`. This restriction does not prohibit
legitimate older-major maintenance lines or alter historical package versions.

Pure parse, projection, history validation, and proposed-edit calculation belong
to Phase 2. They accept immutable source blobs and return a validated edit set
with input/output digests; they do not write files. Phase 4 consumes the same
edit set to apply changes, create a PR, and verify its merged tree.

Paths are repository-relative and bounded to declared regular files. Reject
absolute paths, traversal, symlink/reparse-point escapes, case-fold collisions,
hardlink aliases where supported, oversized input, invalid encoding, and
ambiguous schemas. Parse first, stage all changes in an isolated worktree, then
write the complete valid set; failure leaves the user's worktree untouched.
Reapplying a request produces no duplicate changelog entries or edits.

Artifacts are named files with declared relative paths, media type, required
flag, and policy size/count limits. Enforce inventory, safe names, uniqueness,
regular files, size, and SHA-256 in a separate job. Do not unpack arbitrary
archives in the publisher or follow user-provided upload URLs. Use only GitHub
API upload endpoints derived from the verified repository/Release response.

### GPID Documentation Provenance

Separate immutable release documentation from the mutable development preview.
The release documentation builder uses only the bound release SHA, not a live
`dev` checkout. It produces a release-snapshot artifact with its own complete
file inventory and digest, included in the release build/approval identity.
Add explicit snapshot build/verify modes to the existing documentation helpers;
preserve their legacy combined main/dev mode for the compatibility bridge.

After publication, a trusted Pages composition hook combines the verified
release snapshot with a separately built and verified development-preview
snapshot. It records both artifact/run identities, the exact `dev` SHA, composer
revision, and final file inventory in a deployment manifest. Development code
builds only in an unprivileged job. The privileged composer/deployer reads static
artifacts and never executes the released or development source scripts.

The release snapshot has a versioned site path and cannot overwrite `/dev/`.
The default stable site selects the highest stable release by policy; a
pre-release or older maintenance release must not replace that selection.
Serialize all site-deployment producers through the same existing Pages
deployment guard, including ordinary main/dev updates. Verify the desired
release selection and current dev snapshot before deployment, using their
separate provenance keys. If `dev` advances, refresh only the mutable preview
and composition; do not rebuild or change release assets, their approval, or
their tag. A failed composition leaves the release `published`, not `complete`,
until a deployment with the requested versioned release snapshot is verified.

This changes the existing `release-pages.yml` current-dev comparison explicitly:
it is a mutable deployment freshness check, not a condition on the immutable
release build. Record composition retries separately from authoritative release
build counts. Add tests for dev advancement during release approval and after
tag publication, and verify existing main/dev documentation flows still work.

### Approval, Publication, and Recovery

Before a protected publication job is queued, run a trusted pre-approval job
which persists a publication-input digest containing repository,
request, line/version/tag, source/release SHAs, policy/controller revisions,
check/build identities, artifact inventory/digests, override reason/authority,
signing requirement/fingerprint, tagger identity/timestamp, notes digest, and
environment. Display the inputs, digest, and immutable journal-commit/blob URL
in this already-completed pre-approval job's summary, before the environment
gate. Use that immutable record URL as the protected deployment's environment
URL. The protected job cannot write its own pre-approval summary.

Use one dedicated publication workflow run per immutable publication record.
The pre-approval record binds its GitHub run ID, attempt 1, trusted workflow
SHA/path, expected environment ID, sealed digest, and operation mode (initial
publication or recovery). Reject GitHub reruns with `run_attempt != 1` before
credentials are used. `resume` creates a new trusted publication run, seal, and
approval even when the artifact digest is unchanged. Query review history for
that exact run and verify approved state, expected environment ID, allowed
reviewer identity, and the current protected job's gate. The API does not supply
the application's digest; the one-run/one-seal invariant supplies that link.
Unavailable or ambiguous review/deployment evidence is a hard stop.

Compare approving reviewer numeric IDs with the original requester and any
human who reconfirmed recovery inputs. At least one permitted approving
reviewer must differ from all those IDs; approvals from them do not satisfy the
gate. Keep GitHub's self-review setting as an additional control, not as proof
of this original-requester rule. Test App dispatch, scheduled wakeup, and manual
resume. The evidence link and digest must be visible while publication waits.

Immediately before the first tag write, recheck policy digest, original/resuming
actor authority, branch eligibility and exact release-tip equality, approved
digest, required checks, reservation, tag/Release inventory, and signing
capability. A stale input fails; do not reinterpret `--yes` as renewed consent.
After a verified matching remote tag exists, recovery instead freezes its exact
object and release SHA, checks that the release commit remains an ancestor of
the permitted current source branch, and requires a fresh recovery seal and
approval with current authority. Ordinary forward branch advancement does not
retarget the release or block completing its missing Release. If the branch was
deleted/rewritten, authority was revoked, or policy changed, ordinary resume
stops and requires explicit reviewed maintainer recovery under current policy;
the original inputs remain recorded and the tag/assets cannot change. Published
asset mismatches are never repairable by replacing bytes.

Take a repository-wide publication
owner through the journal. Builds/reviews do not hold that owner. Use Actions
concurrency with `cancel-in-progress: false` as a second guard, not durable queue
storage. Do not steal an owner on elapsed time alone: require proof the prior
run is terminal, its write credentials are expired/revoked, and its remote
effects are reconciled before reassignment.

Create an annotated tag locally from the bound release SHA. For signed tags,
use Git/GPG in an isolated signing home with an allowlisted fingerprint; missing
key, signing failure, or signature mismatch blocks publication. Persist the
exact public tag-object bytes and object ID before pushing so retries reuse the
same object, including tagger timestamp. Push only `refs/tags/<exact-tag>`
without force. Verify both remote tag-object ID and peeled release commit. Git
tag-name validation and argument separation prevent ref/option injection.

Create/reconcile one draft Release for the existing tag, explicitly setting
`draft: true`, `prerelease`, and `make_latest: false`. Upload declared assets and
the public provenance manifest; verify remote inventory, sizes, and digests by
download when the API digest is missing. Unknown upload outcomes are reconciled
by ID/name/digest; never use clobber. Publish only when all required assets pass.
Compute `make_latest` explicitly under the publication owner: false for every
pre-release and older maintenance stable; true only for the highest adopted
stable SemVer across release lines. Never rely on timestamp, raw string order,
Git version sort, or GitHub's default `make_latest=true`. Verify classification
and the resulting latest endpoint against the intended state.

Credentials must support the required API calls, including workflow-file
permission if the target commit changes `.github/workflows/`. Do not misreport
the resulting 403/404 as an absent release. Tag creation and Release publication
are not atomic. A matching pushed tag plus missing/draft Release is resumable;
a mismatching tag, published asset, approval, or evidence record is a conflict.
Do not move/delete a published tag, overwrite published bytes, or delete a
stranded tag as rollback. Draft asset mismatch also stops for inspected recovery.

`resume` reconciles request/journal, PR, checks, run attempts, approvals, tag,
Release, assets, and required hooks before deciding the next action. Reuse only
matching evidence. If pre-publication artifacts expired, rebuild exact inputs;
changed bytes invalidate approval and cannot replace published assets. New
admission is blocked by a conflicting unfinished publication; GPID additionally
blocks all later preparation when any durable payload lacks its published
Release. Pre-existing stranded objects require an explicit audited maintainer
recovery through the trusted workflow, preserving tag identity. An untagged
failed request's reservation can be retired only through an audited maintainer
abandon action after all possible remote effects are excluded; there is no
automatic expiry or version reuse after a tag write.

Read calls default to a 20-second subprocess timeout, at most three attempts
with bounded exponential backoff, and a shared command deadline. Writes are
attempted once before reconciliation. `start` has a 120-second total deadline,
excluding human time at confirmation but including its subsequent recheck and
submission. `status --watch` defaults to ten minutes with a five-second minimum
poll interval; Ctrl+C/timeout stops observation, not the request. Jobs have
explicit timeouts; approval, queue, and review waits are separate persisted
intervals. Tests use injected clocks, not sleeps. Large history/backlog or an
outage must produce an exceeded-deadline result, not an unproven handoff claim.

## Implementation Steps

## Phase 1: Package, Contracts, and Baseline

### 1. Create the standalone package and contract fixtures

- **Requirements**: R1, R2, R7, R17, R18, R19
- **Files**: new `packages/cg-release/pyproject.toml`, `uv.lock`, `src/cg_release/{__init__,cli,models,events,process}.py`, `src/cg_release/py.typed`, `tests/test_contracts.py`, `tests/test_install.py`, and `tests/fixtures/`; new `.github/workflows/release-controller-ci.yml`; targeted `scripts/cg_pr_preflight.py` and `scripts/tests/test_cg_pr_preflight.py`.
- **Details**: Implement package/build isolation, CLI argument schema, schema-v1 policy/request/event/provenance records, typed/redacted failures, dependency lock, and argv process boundary. Keep behavior beyond contracts disabled. Use strict Pydantic validation and canonical digest fixtures. Include the full invariant and legacy/new SemVer fixture corpus for reuse by all languages. Wire the offline six-cell CI matrix, required aggregate, and separate preflight impact route described above.
- **Test Scenarios**: installed wheel in a generic directory with no `.github` or GPID files; unknown schema; invalid option combinations; no CLI stdout log contamination; secret-bearing failures; unsupported Python; argument injection and subprocess timeout; package-only change selects package gate; a missing matrix result cannot pass the aggregate.
- **Tests**: `uv run --project packages/cg-release pytest packages/cg-release/tests/test_contracts.py packages/cg-release/tests/test_install.py -q`; `uv build --project packages/cg-release`; installed-wheel subprocess smoke test outside the source tree; `python -m pytest scripts/tests/test_cg_pr_preflight.py -q`; workflow configuration checks. Live execution of all matrix cells is required at the final gate, not fabricated in Phase 1.
- **Acceptance criteria**: Wheel and sdist build; the installed CLI exposes all four commands and rejects unsupported contracts; tests prove no GPID imports/runtime file requirement. Record resolved library versions and exact install test commands. Package CI wiring and impact-route tests pass without raising the old scripts' Python minimum.

### 2. Instrument stage timing without changing the old publisher's authority

- **Requirements**: R10, R14, R18
- **Files**: new `packages/cg-release/src/cg_release/timing.py`, `tests/test_timing.py`, `scripts/benchmark_release.py`; narrow instrumentation in `create-release.ps1`; evidence under `.cg-docs/work-reports/release-controller/`.
- **Details**: Add opt-in structured timing for preparation, gates, subprocesses, submission, queue, review, build, approval, publication, and recovery. The benchmark uses fixture repositories/fake provider by default. Instrument existing stages without reordering validation or running an actual release. A real legacy baseline needs separate sandbox authorization; absent data is recorded as missing, not zero. New CLI measures confirmation wait separately.
- **Test Scenarios**: monotonic durations; wall-clock skew; interrupted spans; repeat gate counting; bounded Git subprocess counts; redaction; missing remote timestamps; non-publishing default benchmark.
- **Tests**: `uv run --project packages/cg-release pytest packages/cg-release/tests/test_timing.py -q`; safe Pester runner for `create-release`; new `uv run --project packages/cg-release python scripts/benchmark_release.py --offline`.
- **Acceptance criteria**: Executed offline baseline report records environment and stage definitions; legacy functional tests still pass. No claimed live speedup or unrequested tag/API mutation.

## Phase 2: Deterministic Policy and Preview

### 3. Implement SemVer, release-line, branch, and authority policy

- **Requirements**: R2, R3, R4, R5, R18
- **Files**: new package `policy.py`, `versions.py`, `github.py`, `tests/test_policy.py`, `tests/test_versions.py`, `tests/test_github_reads.py`.
- **Details**: Implement the trusted-policy and version contracts above. Use maintained `semver.Version`; inject provider reads for offline tests. Resolve repository/default/source identity, adopted line history, current authorization, production override eligibility, tag prefix, global collisions, explicit bootstrap, and strict manual versions. Add paginated read adapters with safe error classification.
- **Test Scenarios**: `1.4.2 -> 1.4.3/1.5.0/2.0.0`; `1.5.0-rc.9 < rc.10 < 1.5.0`; leading zeroes/non-ASCII/empty identifiers; build-metadata equality; maintenance line beside a newer major; ambiguous/no baseline; legacy four-part baseline; detached HEAD; fork/repository mismatch; missing branch; hostile source policy; normal and unauthorized override; 403 versus 404; pagination after 100 entries.
- **Tests**: package tests `test_policy.py`, `test_versions.py`, and `test_github_reads.py` with the shared version fixture corpus.
- **Acceptance criteria**: Every resolved proposal is deterministic from recorded inputs; unknown authority/history fails explicitly. No local metadata or remote mutation occurs.

### 4. Implement pure metadata validation and read-only proposal

- **Requirements**: R6, R7, R8, R14, R17, R18
- **Files**: package `cli.py`, `events.py`, pure functions in `metadata.py`, `tests/test_metadata.py`, `tests/test_preview.py`, `tests/test_cli.py`, JSON/TOML/R/changelog fixtures.
- **Details**: Implement pure parsers, projections, dual-history ordering checks, validation, and proposed-edit calculation from immutable source blobs. Then implement human/JSON preview, canonical proposal digest, confirmation, `--yes`, explicit `--line`, all brainstorm flags, and shared command deadlines. Keep submit behind the Phase 3 provider until durable admission exists. Return validated edit sets to Phase 4; no filesystem writes or PR logic in this step.
- **Test Scenarios**: every declared format and unsupported representation; JSON duplicates/types; Python dynamic version and `beta.1 -> dev.1` projection downgrade; R pre-release; duplicate changelog marker; plan before start is optional; source/policy/baseline changes before/after confirmation; declined confirmation; noninteractive start without `--yes`; read-only process/API spies; user worktree dirty or detached; deadline exceeded.
- **Tests**: `test_metadata.py` pure validation/projection cases, `test_preview.py`, `test_cli.py`; subprocess snapshots of JSON Lines events and concise human output.
- **Acceptance criteria**: Proposed edits and all format/history failures are testable in Phase 2 without Phase 4 code. No plan-side writes/reservations; confirmed version cannot drift silently; JSON event/error schema is stable. Phase 2 cannot submit/publish yet and reports this explicitly.

## Phase 3: Durable Requests and Asynchronous Control

### 5. Implement durable ingress, journal, and atomic reservations

- **Requirements**: R5, R7, R9, R13, R18
- **Files**: package `github.py`, `journal.py`, `models.py`, `tests/test_admission.py`, `tests/test_journal.py`, `tests/test_concurrency.py`; new package `templates/controller.yml`, `templates/policy.example.json`.
- **Details**: Implement pre-write portable request locators, issue read-back, edit-history validation, permission verification, sealing, Git journal parent checks, hash chain, reservations, operation intents, and nonce reconciliation. Template workflows remain disabled examples until reviewed bootstrap. Apply the explicit job/credential matrix, app/environment/ref rules, and app-only journal writes; no arbitrary-source credential access.
- **Test Scenarios**: issue response lost before/after remote acceptance; locator available before remote write and usable after process loss; duplicate nonce; edited/deleted issue; changed author/repo; unauthenticated input; event from a bot that does not trigger another workflow; CAS sibling commits; state rewrite; stale actor role; two versions and two branches racing; externally created conflicting tag; missing policy protections.
- **Tests**: `test_admission.py`, `test_journal.py`, `test_concurrency.py`; real temporary local bare-Git tests for sibling non-force updates, not only mocked API calls.
- **Acceptance criteria**: One durable accepted request/reservation per identity; uncertain submission stays explicitly unknown until resolved. Journal updates never lose another request or overwrite history. No publication in Phase 3.

### 6. Implement controller wakeups, status, and bounded resume dispatch

- **Requirements**: R7, R13, R14, R17, R18
- **Files**: package `lifecycle.py`, `cli.py`, `github.py`, `templates/controller.yml`, `tests/test_lifecycle.py`, `tests/test_status.py`, `tests/test_queue.py`.
- **Details**: Enable start submission, issue/default-branch wakeup, manual wakeup, scheduled durable-inventory scan, checkpoints, and structured status/watch. Each controller run performs bounded work and persists the next checkpoint rather than waiting in chat or holding a runner through human review. Resume dispatches a trusted reconciliation pass, not unconditional replay. Implement audited abandon for untagged requests through the maintainer workflow input, not a general destructive CLI.
- **Test Scenarios**: dropped event, >100 requests, queue eviction, two wakeups, superseded run, shutdown between intent/result, status without local files, provisional locator recovery on a second machine with no issue number, unresolved lookup does not resubmit, watch timeout/Ctrl+C, unauthorized resume, retained reservations, corrupt cursor, and unavailable journal.
- **Tests**: `test_lifecycle.py`, `test_status.py`, `test_queue.py`; fault-injected fake-provider end-to-end tests.
- **Acceptance criteria**: A request survives process loss and queue cancellation; status distinguishes queued admission, execution, failed, published, and complete. Watching never controls release lifetime.

## Phase 4: Reviewed Metadata and Exact-Commit Builds

### 7. Apply validated metadata edits and create preparation PRs

- **Requirements**: R6, R8, R9, R18
- **Files**: package `metadata.py`, `lifecycle.py`, `github.py`, `tests/test_metadata.py`, `tests/test_preparation.py`, and representative JSON/TOML/R/changelog fixtures.
- **Details**: Consume Phase 2's pure adapters and validated edit sets; verify input blob digests before applying them. Prepare edits in an isolated worktree from approved source SHA; build expected tree and diff allowlist; create/reconcile one request branch and PR. Do not duplicate projection/parsing logic or implement it for the first time here. Reuse no arbitrary code from the source in the privileged preparer. Verify review/merge result and bind the exact release SHA using the contract above.
- **Test Scenarios**: all supported formats; unsupported R pre-release and Python dynamic version; missing/duplicate field/marker; partial multi-file error; metadata injection; symlink/reparse/traversal/case alias; PR creation response lost; unexpected edit/base advance; merge/squash/rebase; pre-release PR targeting a non-default branch.
- **Tests**: `test_metadata.py`, `test_preparation.py`; temporary-Git expected-tree tests and preserved-format fixture comparisons.
- **Acceptance criteria**: All declared metadata represents the one approved version or preparation stops without a PR; only approved edits enter the reviewed release tree. Resume does not duplicate branches, PRs, or notes.

### 8. Implement isolated builds and reusable exact-input evidence

- **Requirements**: R9, R10, R12, R14, R18
- **Files**: package `lifecycle.py`, `models.py`, new `verification.py`, `templates/build.yml`, `tests/test_builds.py`, `tests/test_artifacts.py`, `tests/test_workflow_security.py`; `.github/workflows/release-controller-ci.yml` release-mode registration and matrix handoff.
- **Details**: Register the sealed build request to the actual trusted-workflow run in a separate control job before source execution. Connect the package CI workflow's trusted `workflow_dispatch` release mode to this registration and verify its six-cell aggregate by the accepted evidence tuple above. Build the exact registered release commit; use no source-controlled workflow as authority. Record separate controller SHA and source SHA/tree, full reuse key, and GitHub run/attempt/artifact identities. Verify regular-file inventory, names, sizes, and digests separately; keep builds/caches isolated from privileged jobs. Reuse matching evidence rather than repeating full preflight in each lifecycle phase.
- **Test Scenarios**: package matrix runs against a final squash/merge SHA outside integration filters; PR aggregate cannot satisfy release-mode evidence; forged same-name check from wrong producer; two release SHAs share one controller revision and swap artifacts; run head SHA differs legitimately from release SHA; PR merge SHA versus release SHA; skipped/failed/cancelled jobs; altered toolchain/lock/policy; missing artifact; expired retention; path traversal/archive injection; identical evidence cache hit; malicious source attempts to read control secrets or poison privileged cache.
- **Tests**: `test_builds.py`, `test_artifacts.py`, `test_workflow_security.py`; sandbox secret-boundary probe in Phase 7 is also required, not replaced by YAML inspection.
- **Acceptance criteria**: One successful authoritative build/gate per unchanged reuse key; publisher receives verified byte inventory, not executable source. Expired or mismatched evidence requires new validation and is not called a cache hit.

## Phase 5: Approval, Publication, and Recovery

### 9. Implement protected approval, exact tagging, and verified Release publication

- **Requirements**: R3, R4, R5, R9, R11, R12, R13, R18
- **Files**: package `publisher.py`, `github.py`, `journal.py`, `templates/publish.yml`, `tests/test_approval.py`, `tests/test_publisher.py`, `tests/test_signing.py`.
- **Details**: Implement the separate pre-approval seal/summary job, one-run/one-digest approval association, original-requester reviewer exclusion, environment verification, checkpoint-dependent authority/policy checks, publication owner, annotated/GPG-signed object persistence, exact non-force tag push, draft staging, verified upload, publication, and explicit latest-stable behavior. Follow the credential matrix: journal writes use only the control App and publication writes only the publication App inside the protected trusted publisher. Never execute target source there.
- **Test Scenarios**: evidence visible while protected job waits; original requester tries to approve an App-dispatched run; recovery reconfirmer as reviewer; `run_attempt > 1` rejected; normal pre-release/stable; maintainer override; self-review/admin bypass settings; wrong environment/run/digest; stale approval; permission revoked; missing/wrong signing key; lost tag-push response; existing lightweight/different tag; journal denial for publication App and tag denial for control App; cancellation between intent and result; draft mismatch; missing/different asset; unsupported workflow-file token permissions; rc and old-maintenance latest behavior.
- **Tests**: `test_approval.py`, `test_publisher.py`, `test_signing.py`; temporary local Git/GPG key tests; mock remote digest downloads. Actual GitHub approval and signing trials remain Phase 7 evidence.
- **Acceptance criteria**: No publication without all bound gates; exactly one expected tag object and verified Release inventory; latest classification is explicit and checked. No tag force-push or asset clobber path exists.

### 10. Implement remote reconciliation and adversarial recovery matrix

- **Requirements**: R7, R10, R11, R12, R13, R14, R16, R18
- **Files**: package `lifecycle.py`, `publisher.py`, `journal.py`, `tests/test_recovery.py`, `tests/test_fault_matrix.py`.
- **Details**: Inject failure before/after every remote write and checkpoint. Reconcile exact observed identities before replay. Restore missing pre-publication evidence with renewed build/approval; complete only missing post-publication hooks. Implement journal restore checks, terminal-owner/credential proof, stranded-history recovery, and strict conflict/error diagnostics.
- **Test Scenarios**: tag exists/no Release and source branch has advanced; unchanged tag recovered with fresh approval; deleted/rewritten source requires explicit maintainer recovery; draft/partial upload; publish response lost; Release exists/journal behind; journal missing or edited; policy/authority changed; expired artifacts; owner appears stale but run still alive; terminal run with unexpired token; mismatched published bytes; failed GPID post-hook; safe audited abandon before tag; repeat resume converges without additional writes.
- **Tests**: `test_recovery.py`, `test_fault_matrix.py`; the fake provider must model irreversible writes, eventual read results, pagination, authentication errors, and real exit-code protocol.
- **Acceptance criteria**: Every irreversible boundary has a tested safe next action; matching reruns are idempotent, mismatches stop, and `published` never means `complete` before required hooks pass.

## Phase 6: GPID Compatibility and Integration

Current local-delivery scope under `D-2026-09-13-defer-live-rollout`: finish
Steps 11-12 implementation, offline checks, and independent review with the
publisher disabled. Accept the missing V6 live evidence only through the dated
user-approved exception. The bridge delivery and source qualification procedures
below remain deferred rollout obligations, not completed implementation tests.

### 11. Migrate version readers and distribute the compatibility bridge

- **Requirements**: R3, R15, R17, R18
- **Files**: `scripts/update.ps1`, `scripts/update.sh`, `scripts/generate-whats-new.js`, `scripts/skill_management/services/release_attestation.py`, `scripts/skill_management/services/lifecycle.py`, `.github/shared/skill-management/contracts/release-attestation-v1.schema.json`; narrow compatibility guards in `.github/workflows/release-docs.yml` and `release-pages.yml`; `scripts/assemble-docs-site.js`, `scripts/check-docs-site.js`; affected existing updater/docs/install/attestation tests.
- **Details**: Accept old stable/four-part and new SemVer identities in readers; use the shared version corpus for numeric precedence and label parity. Keep legacy parse/ordering a distinct compatibility path selected by syntax and explicit migration mapping. Never reinterpret historical four-part identity as a SemVer suffix. Update pin/list/latest behavior on both updaters without adding Python or Node as a new updater runtime requirement. Preserve chronological payload display where intentional; version choice uses SemVer, not chronology. Test install/link persistence without unnecessary parser rewrites.
- **Details**: Ship these reader changes first through an already accepted legacy-format update channel, using the existing reviewed release process and separate maintainer authorization. Record the compatibility bridge tag/Release ID and trusted revision. Verify installation with the old updater and then new-format pin selection with the updated updater in clean Windows/Unix fixtures. Do not enable the new writer until that evidence is recorded. Historical payload and attestation bytes are read-only.
- **Test Scenarios**: old pins and four-part releases; rc.2/rc.10; hidden/show-dev labels; initial installs; maintenance releases; latest.json byte match; publishedAt preparation-time semantics; removal-grace selection; unsupported version; old updater installs bridge; bridge updater accepts new tag; existing docs artifact inventory rules.
- **Tests**: existing Python release/attestation/removal/target-update tests; existing Node payload/docs tests; safe Pester `update`, `bash-scripts`, `install`, `docs-automation`, `create-release`; shared fixture parity tests.
- **Historical rollout acceptance, retained**: Readers pass legacy and new syntax fixtures on both shells; bridge delivery is verified, not just merged locally. New publisher remains disabled. If remote bridge authorization is absent, record V6 blocked and stop before writer cutover.
- **Acceptance criteria**: Current local scope (2026-09-13): local reader fixtures, integration checks, and review pass with actual host/skip limits recorded. Bridge delivery and actual Windows/native Unix clean-client qualification are deferred under V6, not passed. The publisher remains disabled; no writer cutover is permitted.

### 12. Add the GPID profile and thin five-platform command

- **Requirements**: R1, R10, R15, R16, R17, R19
- **Files**: new `scripts/release_profile_gpid.py`, `.release-controller.json`, `.github/workflows/release-controller.yml`, `.github/workflows/release-controller-build.yml`, `.github/workflows/release-controller-publish.yml`; targeted edits to `create-release.ps1`, `.github/prompts/cg-release.prompt.md`, `.github/prompts/cg-devtag.prompt.md`, `.github/agents/cg-release-scanner.agent.md`, `.github/shared/module-registry.json`, `.github/shared/target-mapping.json`; `.github/workflows/release-docs.yml`, `release-pages.yml`, `pages.yml`, `docs-site-build.yml`, and `doc-rebuild.yml`; `scripts/assemble-docs-site.js`, `scripts/rebuild-docs.js`, `scripts/check-docs-site.js`; generated native command assets and new `bin/cg-release`, `bin/cg-release.cmd`; new `scripts/tests/test_release_controller_profile.py` and affected release-policy/docs tests.
- **Details**: Profile owns canonical payload preparation, exact-input `cg_pr_preflight`/target checks, docs build/deployment evidence, and post-tag attestation/evidence PR. Core invokes typed hook stages and validates results without importing GPID modules in generic mode. Notes and durable payload must be reviewed before the release SHA; tag-dependent attestation remains a later evidence PR and does not move the release tag. Complete only after required docs publication and reviewed evidence commit are remotely verified.
- **Details**: Replace legacy slash orchestration with a thin argument-preserving CLI call and structured output; remove the mandatory charter guard only for generic core mode. Keep the old publisher available only for the authorized bridge/recovery path until cutover, then fail explicitly for new routine publication. Do not remove historical recovery support. `/cg-devtag` must not create unmanaged new-format release identities; retain its old temporary-tag behavior as clearly separate legacy tooling, not the controller baseline. Scanner may provide optional editorial notes but cannot resolve versions, approvals, or release completion.
- **Details**: Implement the separate immutable release snapshot and mutable development-preview composition contract above. Define one GPID release-docs build owner; disable duplicate release-trigger paths only after their checks are preserved. Ordinary main/dev builds remain independent, but all deployments share the Pages guard and verify the separate release/dev selections. Register `release-controller-ci` plus native/profile check identities in required policy; invoke its trusted release-mode dispatch for the final bound SHA on every eligible source branch and accept only its registered exact-source evidence tuple. Regenerate native assets from `.github/`; do not hand-edit generated trees. Load Windows launcher and Pester safety skills when implementing launchers/tests.
- **Test Scenarios**: generic repository with no GPID files; explicitly selected profile with missing files fails; payload-before-tag and evidence-after-tag order; failed docs/evidence hook yields published-not-complete; `dev` advances during approval and after tag publication without invalidating immutable release evidence; release snapshot cannot overwrite `/dev/` or displace a newer stable default site; composition retry refreshes only mutable evidence; six-cell CI aggregate is required; five-platform CLI/JSON parity; legacy recovery routing; duplicate build trigger count; installing standalone and GPID launcher without command shadowing.
- **Tests**: new profile tests; `test_release_policy.py`, `test_release_gate_targets.py`, `test_target_drift.py`; Node/docs workflow tests; safe Pester launcher/release tests; `python scripts/cg_generate_targets.py --all --dry-run`.
- **Acceptance criteria**: All five interfaces use the same core; generic mode has no GPID dependency; required GPID evidence remains enforced; compatibility bridge is a hard enablement prerequisite; build/deploy counts do not increase for unchanged input identity.

## Phase 7: Local Handoff and Deferred Rollout Validation

Not started by the 2026-09-13 scope revision. The parent retains the next phase.
Current scope is remaining local implementation, offline trial/performance
harness checks, tested documentation, and local final gates. Step 13's live
operations and measured results remain deferred rollout requirements. Step 14
retains ordinary PR CI and the committed gate as final pipeline obligations;
neither must be moved earlier to close the local phase.

### 13. Run explicitly authorized sandbox trials and performance comparison

- **Requirements**: R4, R5, R7, R9, R11, R12, R13, R14, R15, R16, R17, R18
- **Files**: new package `tests/test_sandbox.py`, `tests/test_performance.py`, package template fixtures; `scripts/benchmark_release.py`; results under `.cg-docs/work-reports/release-controller/`.
- **Details**: Require explicit repository IDs/URLs and approved remote operations before live trials. Default tests remain offline and never discover a production target from `origin`. Provision a generic fixture without GPID assets and a GPID migration fixture with real environment/ruleset/App separation. Exercise preview, pre-release from a non-production branch, stable, permitted and rejected override, signing, maintenance latest, concurrency, dropped wakeup, lost response with portable-locator recovery on another machine, expired evidence, journal restoration, branch advancement after tag push, mutable-dev composition retry, and failed post-hook/resume. Verify the pre-approval link is readable before approval; original requester/reconfirmer approvals do not count; each App is denied the other role's protected ref operation.
- **Details**: Collect at least ten sequential warm-dependency start samples on the generic fixture, excluding user confirmation time only. Require p95 <=120 seconds from proposal computation to verified durable receipt; report min/median/p95, environment, history size, and all failures. Report queue/review/approval/build/publication/recovery intervals separately. Compare the same workload on the instrumented legacy path where applicable; unavailable live baseline forbids a speedup claim. A service outage is a visible failed/blocked trial, not an excluded successful sample.
- **Test Scenarios**: GPID preparation PR merged/squashed onto a non-integration source branch produces a final SHA different from the PR test-merge SHA; its six-cell trusted release-mode CI completes and only that source-bound aggregate is accepted. Also Windows PowerShell 5.1 launcher and Unix shell paths; Python 3.11/3.12; clean install; no secrets in source build; rejected tampering with policy/controller; approval cannot be bypassed; verified exact tag and remote digests; repeated resume converges; Pester output remains bounded.
- **Tests**: default package suite, explicit opt-in sandbox marker with allowlisted repository IDs, benchmark command with explicit sandbox configuration, and captured GitHub run/Release/approval records. Record exact executed argv and exit status in the execution report.
- **Historical rollout acceptance, retained**: V7 has real sandbox evidence, measured handoff passes, and remote identities match. No production enablement or cleanup of published tags/assets is automatic. Missing settings, credentials, authorization, or evidence is blocked, not skipped-as-passed.
- **Acceptance criteria**: Current local scope (2026-09-13): validate the offline trial/performance harness and document the exact opt-in rollout procedure, authorization needs, unexecuted cases, and missing measurements. V7 live sandbox, host/matrix, remote-identity, security, and timing proof is deferred, not passed. Retain all trial scenarios and the ten-sample p95 <=120-second target for later rollout; local timings do not prove it.

### 14. Document installation, bootstrap, migration, and recovery; run final gates

- **Requirements**: R1, R2, R7, R14, R15, R16, R17, R19
- **Files**: new `packages/cg-release/README.md`, `docs/release-controller.md`; targeted edits to `docs/versioning.md`, `docs/development/index.md`, `docs/workflow.md`, `docs/reference.md`, `docs/installation.md`, `docs/skills/management/maintainers/release.md`, and root `README.md`; package tests and relevant docs checks.
- **Details**: Explain read-only plan versus confirming start, policy/line bootstrap, dependency installation, App permissions, protected environments, immutable tag rules, status meanings, journal retention/backup, maintenance latest, supported projections, bridge rollout, legacy recovery, and all error actions. Include tested generic and GPID examples. Re-run final regression/parity gates; retain exact executed evidence and any blocked conditions in the `/cg-work` execution report.
- **Test Scenarios**: clean wheel install without GPID; copied setup templates with explicit repository IDs; documentation examples against fixture repos; status/resume from a second machine; old client bridge path; recovery with expired Actions artifacts.
- **Historical tests/final timing, retained**: entire package suite and build/install smoke; executed six-cell package CI matrix and stable aggregate; existing affected Python/Node suites; canonical full Pester runner through a child; generated-target drift and committed exact-input preflight on an authorized candidate commit; documentation validation commands listed below. If candidate commit/CI authorization is unavailable, the final gate is blocked, not silently conditional.
- **Tests**: Current timing (2026-09-13): run the local package/build/install, affected regression, safe Pester, parity, and documentation checks in Phase 7. Release-mode CI is deferred to rollout. Ordinary PR CI, including the ordinary six-cell package matrix and aggregate, remains required. Run the committed exact-input preflight only after the planned pipeline step 11 commit is separately authorized. Keep those V8 pipeline results pending until executed; do not move the commit or substitute prepare evidence.
- **Historical acceptance, retained**: V1-V8 evidence is present and passing; no unresolved required findings; docs describe tested capability only. Final evidence cannot be claimed from static inspection or from an uncommitted preflight pretending to validate a reviewed release commit.
- **Acceptance criteria**: Current local scope (2026-09-13): required local evidence and reviews pass; documentation separates tested local behavior from deferred rollout proof. The accepted V6-V8 live exceptions permit local delivery, not live readiness. Phase 7 local completion may precede pipeline step 11 under the accepted V8 sequencing exception, but whole-plan/final pipeline acceptance and V8 remain pending until the committed gate and ordinary PR CI pass. No unresolved required finding is excused.

## Dependency Graph

```text
Phase 1 (contracts and offline baseline)
  -> Phase 2 (deterministic policy/preview)
  -> Phase 3 (durable ingress/state/observation)
  -> Phase 4 (reviewed metadata and exact-input builds)
  -> Phase 5 (approval, immutable publication, recovery)
  -> Phase 6 step 11 (local readers; bridge delivery deferred)
  -> Phase 6 step 12 (profile + disabled writer integration)
  -> Phase 7 (local harness/documentation + local final gates)
  -> Planned pipeline step 11 (separately authorized commit; exact committed gate)
  -> Ordinary PR pipeline/CI (required; final V8 acceptance)

Deferred rollout: authorized bridge delivery and native clean-client qualification
  -> registered source-bound live CI + sandbox/security trials + performance proof
  -> separate reviewed enablement decision (not authorized here)
```

No write-heavy phase runs in parallel. Tests/read-only research can run in
independent children. Phase execution uses globally numbered steps; never reset
step numbers inside phases. Do not enable production from a phase-completion
flag. Enablement requires a separate reviewed policy change and maintainer
authorization after all compatibility and sandbox evidence passes.

## Testing Strategy

Tests for new behavior precede implementation. Run red/green tests by step,
then related regressions. Use injected clock/provider boundaries and real local
Git/GPG tests for object/atomicity assertions. Network sandboxes are opt-in and
remain mandatory rollout evidence, deferred from local delivery by the dated
2026-09-13 decision; they are not passed or required for each local unit-test run.

New package commands, introduced in Phase 1:

```text
uv sync --project packages/cg-release --locked
uv run --project packages/cg-release pytest packages/cg-release/tests -q
uv run --project packages/cg-release ruff check packages/cg-release
uv build --project packages/cg-release
uv run --project packages/cg-release python scripts/benchmark_release.py --offline
```

Existing repository interfaces, selected by the affected step:

```text
python -m pytest scripts/tests/test_release_policy.py scripts/tests/test_release_gate_targets.py scripts/tests/test_skill_management_release_attestation.py scripts/tests/test_skill_management_contracts.py scripts/tests/test_skill_management_removal.py scripts/tests/test_update_generates_targets.py -q
npm run test:docs-automation
node --test scripts/tests/assemble-docs-site.test.js scripts/tests/check-docs-site.test.js scripts/evidence/tests/release-pages.test.js
python -m pytest scripts/tests/test_target_drift.py -q
python scripts/cg_generate_targets.py --all --dry-run
node scripts/generate-whats-new.js --validate-release-set
node scripts/generate-whats-new.js --check
node scripts/rebuild-docs.js --all --check
node scripts/check-docs-site.js
```

Pester always runs in a child after loading `cg-skill-pester-safety`, using
`. tests\Run-Tests.ps1 -File <test-name>` for targeted work or
`. tests\Run-Tests.ps1` for the full gate. Read `tests/last-run.json` and return
only `passed`, `failedCount`, `failures`, and `filteredFiles`. A filtered run is
not a full gate. Never invoke `Invoke-Pester` directly in the parent.

The existing `python scripts/cg_pr_preflight.py --phase committed --full-gate
--run-native-target` is the GPID exact committed-input gate. Run it only on an
actually committed candidate, in the required child/safe context. This plan
does not authorize commits or pushes by itself. For local development, record
executed targeted checks without claiming the committed gate has passed.

## Documentation Checklist

- [ ] Standalone install, Python/Git/gh prerequisites, and four-command examples.
- [ ] Trusted setup PR, policy schema, App/environment/ruleset permissions, and sandbox authorization.
- [ ] Version lines, bootstrap/legacy history, projections, and maintenance latest policy.
- [ ] Durable inbox/journal retention, portable provisional request locators, JSON Lines events, backup/restore, progress meanings, deadlines, and checkpoint-dependent recovery.
- [ ] Pre-approval evidence URL, independent reviewer rule, one-run/one-seal binding, role-specific publisher credentials, and separate controller/source provenance.
- [ ] Dual SemVer/PEP 440 ordering restrictions and immutable release-docs versus mutable development-preview composition.
- [ ] GPID compatibility bridge, reader/writer ordering, required hooks, and legacy recovery boundary.
- [ ] Measured handoff scope, full-stage timings, unsupported capabilities, and error reference.

## Risks & Mitigations

| Risk | Mitigation | Verification |
|---|---|---|
| Source branch reaches control/publishing secrets | Explicit credential/job matrix, protected environments, role-specific operations, and fresh unprivileged runners | Workflow tests, cross-role ref denials, and live hostile-source probe |
| GitHub setting/plan cannot enforce approval or journal write restrictions | Capability preflight; fail closed; no weaker fallback | Sandbox negative setup cases |
| Issue edits or lost wakeups corrupt approved input | Unedited inbox verification, digest sealing, durable journal and scheduled scan | Admission/queue fault tests |
| Journal CAS or stale publisher loses another request | Parent-bound non-force updates, one publication owner, terminal/credential proof | Real Git races and recovery tests |
| Tag write succeeds but Release write fails | Durable intent/object bytes, remote reconciliation, no destructive rollback | Failure at every publication boundary |
| Expired artifacts break recovery | Durable provenance; rebuild exact inputs and renew approval before publication | Expiry and restore tests |
| New SemVer writer strands old clients | Bridge release accepted by old reader; only then enable new writer | Two-stage clean-install trials |
| Metadata projection changes meaning | Narrow adapters and explicit grammar/manifest; fail unsupported | Cross-format fixtures |
| Profile reintroduces long repeated gates | Exact reuse key, one build/deploy owner, stage instrumentation | Gate count and performance report |
| Performance claim ignores queues or outages | Separate timing intervals and explicit blocked/failed trials | At least ten measured submissions |
| Scope grows into general CI or registry tooling | Four commands, one provider, declared formats, existing CI | R19 and boundary checks |

## Out of Scope

- Additional hosting/CI providers and a continuously running orchestration service.
- Independently versioned package graphs and npm/PyPI/CRAN publication.
- Arbitrary metadata/plugin execution in privileged jobs; full ecosystem adapter coverage.
- Changing the charter, project schema version, historical release payloads, tags, or attestation identities.
- Production release, repository settings, credentials, commits, or pushes without separate explicit authorization.
- Automatic journal compaction, destructive cleanup, or tag/asset rollback.

## Completion Contract

### Outcome

Current delivery outcome, revised 2026-09-13: local implementation, offline
verification, tested documentation, reviews, and the ordinary PR pipeline are
complete with the publisher disabled. Live rollout proof is explicitly deferred;
final delivery still requires the authorized committed gate and ordinary PR CI.

Historical live capability outcome, retained for deferred rollout:
A repository can use `cg-release plan`, `start`, `status`, and `resume` without a
Compound GPID installation. Publication uses the exact reviewed release commit,
preserves published tags and assets, and reaches `complete` only after all
required checks and project hooks pass.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|---|---|---|---|---|
| V1 | 1 | Installable package, validated contracts, and baseline timing data | Step 1 package build/install/schema tests, CI wiring and package-impact tests; Step 2 timing tests and executed offline baseline report | yes |
| V2 | 2 | Correct SemVer, branch policy, pure metadata validation/projection, and read-only preview | Steps 3-4 policy, version, provider-read, pure metadata/dual-order, preview, and CLI tests | yes |
| V3 | 3 | Durable requests, duplicate protection, and safe recovery after worker loss | Steps 5-6 admission/journal/queue tests, including real Git sibling-update tests | yes |
| V4 | 4 | Bounded metadata writes, reviewed release commit, and isolated exact-commit builds | Steps 7-8 edit-set application, preparation, registered source/controller identity, arbitrary-branch release-mode matrix route, build, artifact, and workflow tests | yes |
| V5 | 5 | Bound approval, signing, verified publication, and partial-failure recovery | Steps 9-10 publisher, signing, approval, recovery, and fault-matrix tests | yes |
| V6 | 6 | Local GPID reader/profile/target and required-hook/CI enforcement checks pass; independent review is closed; publisher stays disabled | Steps 11-12 executed local gates and review evidence; approved D-2026-09-13-defer-live-rollout exception for bridge delivery, native clean clients, and actual registered source-bound release-mode CI; deferred components are not passed | yes |
| V7 | 7 | Remaining offline trial/performance harness and documented rollout procedure are verified locally; no unmeasured live claim | Step 13 executed offline checks and tested procedures; approved D-2026-09-13-defer-live-rollout exception retains sandbox, native-host, final-SHA live CI, security/approval, remote-identity, and ten-sample timing proof as deferred | yes |
| V8 | final | Local phase evidence and tested installation/recovery docs pass with explicit live exceptions; ordinary PR CI and committed exact-input gate still pass before final pipeline acceptance | Step 14 package/affected regression/parity, unfiltered safe Pester, tested docs and report; later authorized pipeline step 11 candidate plus committed preflight; ordinary PR checks including six-cell package CI and aggregate. Release-mode live CI is deferred, not passed; the V8 pipeline component remains pending until executed | yes |

### Historical Acceptance and Deferred Obligations

Original 2026-09-11 rows, retained verbatim for provenance. These are not the
current local-delivery gate; the revised table above and the dated decision
control acceptance. Original review resolution and prior blocked reports remain
valid historical records, not current statements that no exception was approved.

| ID | Phase | Evidence Required | Command/Artifact | Required |
|---|---|---|---|---|
| V6 | 6 | GPID readers accept new versions before writers are enabled; required hooks remain enforced | Steps 11-12 reader/profile/target tests including required source-bound release-mode CI, plus authorized compatibility-bridge delivery and clean-client evidence | yes |
| V7 | 7 | Generic repository trials, Windows/Unix checks, and measured 1-2 minute tracked handoff | Step 13 authorized sandbox records, non-integration-branch final-SHA CI proof, secret/approval probes, ten-sample timing report, and remote identity verification | yes |
| V8 | final | All phase evidence passes; installation and recovery instructions are tested | Step 14 full package/affected regression/parity results, executed source-bound six-cell release CI and aggregate, full safe Pester result, committed candidate preflight, tested docs, and execution report; missing authorization blocks this gate | yes |

Exact deferred rollout obligations:

1. Reviewed legacy-format bridge delivery: published tag/Release ID, trusted revision, commit/tree/tag-object identities, previous/bridge/successor distributions, archive digests, and trusted producer/run/attempt/job/artifact records; actual clean Windows and native Unix old updater -> delivered bridge -> new-format pin qualification receipts.
2. Registered release-mode CI and setup: exact repository and producer identities, controller/workflow revision, sealed request/source SHA/nonce, actual run/attempt, six required Python 3.11/3.12 Windows/Linux/macOS cell results, Ruff, aggregate, and native/profile evidence; non-integration-branch merged/squashed final-SHA proof. Ordinary PR CI is excluded from this deferral.
3. Authorized generic and GPID sandbox trials: the complete Step 13 matrix, including real protected environments/rulesets/App role denials, hostile-source and approval probes, signing, exact remote tag/assets/latest identity, concurrency, lost-response/second-machine recovery, expired evidence/journal restore, branch advancement, mutable-dev composition, and post-hook/resume behavior.
4. Performance proof: at least ten sequential warm-dependency starts, confirmation time alone excluded, min/median/p95 and all failures, p95 <=120 seconds, environment/history size, separate queue/review/approval/build/publication/recovery intervals, and a comparable legacy workload where available. No missing baseline is zero and no speedup is inferred.

V8 sequencing is not a permanent waiver: the planned pipeline step 11 commit,
committed preflight, ordinary PR and its required CI remain final obligations.
Keep V8 pending if they are not executed. This exception permits Phase 6 and
later Phase 7 local checkpoints without an early commit, not a false whole-plan
or pipeline completion. The source freeze/prepare result is not an exact committed
candidate identity. Runtime C1-C6 controls and the requirement for a separate
reviewed enablement decision remain unchanged; live parts of C2/C3/C5 are deferred
proof, not established by offline checks.

### Constraints

| ID | Constraint | Check |
|---|---|---|
| C1 | No moved published tags or changed published asset bytes | Remote object/peeled SHA and digest assertions; no-force/no-clobber tests |
| C2 | Source branches cannot change controller policy or access publishing secrets | Trust-boundary tests and live hostile-source probes |
| C3 | Stable branch exceptions require maintainer authority, a reason, and protected approval | Negative authorization/environment tests and bound sandbox approval records |
| C4 | No silent version change after confirmation | Stale source/policy/baseline and collision tests |
| C5 | Old GPID payloads and release identities remain valid | Legacy fixture, pin, bridge, and original payload/attestation byte checks |
| C6 | Pester uses only the project's safe runner through a child task | Recorded commands and `tests/last-run.json`; full gate is unfiltered |

### Boundaries

- Allowed implementation: the package, tests, templates, narrow source/script/workflow/profile changes, generated native outputs, and documentation paths explicitly listed in the steps. Compound GPID maintenance of the named canonical prompts, registry/mapping, workflow guards, and attestation schema is explicitly in scope; never replace `.github/` wholesale.
- Allowed evidence: the `/cg-work` execution report, active-state records under the shared workflow contract, and release-controller verification artifacts under `.cg-docs/work-reports/release-controller/`. Do not rewrite historical brainstorms, plans, solutions, or release evidence. The user explicitly authorized this plan's dated 2026-09-13 acceptance revision; preserve its original requirements and prior evidence as above.
- Allowed planning-session edits: this plan and its later review artifact only. No implementation, remote trial, release, setup, secret change, or protected-setting change is authorized by plan approval.
- Out of scope: the items in Out of Scope above; roadmap writes only through the roadmap agent after explicit approval. Future production enablement is a separate maintainer action.

### Iteration Policy

1. Implement and verify one phase at a time. Require prior-phase evidence before a later phase; within Phase 6 complete reader/bridge delivery before writer cutover.
2. Write tests before behavior changes. Use the project's two-attempt recovery limit per step; retain failures and stop the evidence-dependent path when required checks remain failed.
3. Reconcile remote state before retrying any uncertain write. Reuse exact matching evidence, never inferred success.
4. Under `deviation-policy: ask`, obtain and record approval before scope, contract, dependency-boundary, or security-control deviations. No missing evidence is passed by static inspection.
5. Record real commands, versions, results, remote identities, and approvals incrementally in the execution report. Required exceptions need explicit evidence-ID approval and cannot bypass higher-priority protections.

### Blocked-Stop Conditions

- Required verification fails after permitted recovery or cannot run through the safe runner.
- Authorization, supported protected environments, signing capability, app/ref protection, or exact-commit approval cannot be enforced or verified.
- Remote tag, asset, Release, journal, request, repository, policy, or evidence identity conflicts with the approved inputs.
- Durable state cannot be written, verified, or restored; an uncertain remote write cannot be reconciled.
- A required scope deviation or protected boundary needs approval that is unavailable.
- Compatibility bridge delivery, explicit sandbox authorization, or required live evidence is missing at the rollout gate. The 2026-09-13 accepted exception defers these from local phase gates only; ordinary PR CI and the later committed gate remain required for final pipeline acceptance.
- The execution report cannot be durably created/updated, or completion would require claiming an unexecuted check passed.
- A missing prior GPID published Release would be concealed by proceeding to a later release.

## Plan Review Resolution

Initial `/cg-plan-review` on 2026-09-11 found two P1 and eight P2 issues, with no
P3 issues. The user requested that all findings be addressed. No risks were
accepted and no findings were deferred. The roadmap remains unchanged by the
user's explicit choice. This is a plan review, not proof of implemented runtime
security or passing future package/sandbox tests.

| Finding | Plan correction | Verification target |
|---|---|---|
| P1.1 | Pre-approval job publishes the sealed evidence URL before the gate; one publication run/attempt-1 per seal; no API-digest assumption | Step 9 and live Step 13 visibility/binding tests |
| P1.2 | Exact tip before first tag; frozen tag and valid lineage on recovery after tag; fresh recovery approval | Step 10 branch-advance recovery case |
| P2.1 | Verified reviewer must differ from original requester and recovery reconfirmers | Step 9 and Step 13 App/schedule/resume cases |
| P2.2 | Explicit credential/job matrix and direct control-App journal writes inside the protected publisher; publication App cannot update journal | Steps 5, 9, 10, and live cross-role denial tests |
| P2.3 | Separate controller workflow SHA and registered source SHA/tree; trusted pre-build run registration and artifact/run association | Step 8 two-source/same-controller substitution test |
| P2.4 | Pure parsers/projections/edit calculation move to Step 4; Step 7 only applies validated edit sets and binds PR results | V2 and V4 phase-local tests |
| P2.5 | Require both SemVer and per-distribution/line PEP 440 history to increase; reject conflicting channel transitions | Step 4 cross-channel fixture corpus |
| P2.6 | Immutable release-only documentation snapshot; mutable dev composition has its own key and retry behavior | Step 12/13 dev-advance and deployment-selection tests |
| P2.7 | Phase 1 offline six-cell package CI, aggregate check, and separate package preflight route; executed final evidence required | Step 1 impact tests and V8 CI records |
| P2.8 | Emit portable provisional REQUEST_ID before first write; status/resume resolve it read-only, without reissuing submission | Steps 5, 6, and Step 13 second-machine recovery |
| P2.9 | Add trusted default-ref package CI dispatch with sealed source registration, accepted six-cell provenance tuple, and arbitrary-branch final-SHA proof | Step 8 route tests; Step 12 required check contract; V4/V6/V7/V8 |

The independent verification pass confirmed all ten original corrections and
found P2.9, the exact-source CI route gap. Its correction is also written.
The final independent critic pass on 2026-09-11 verified all eleven findings
resolved (P1: 2/2; P2: 9/9; P3: 0), found no remaining blocking or significant
design gaps, and confirmed readiness for `/cg-work` at the plan-design level.
The worktree artifact validator and `git diff --no-index --check` both passed.
These checks validate this plan, not the future implementation. No implementation
phase is complete and no runtime V1-V8 evidence is claimed.

## Handoff

Start implementation with the explicit plan path and first phase:

```text
/cg-work phase1 .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
```

The seven phases, globally numbered steps 1-14, R1-R19 mappings, required V1-V8
evidence, and C1-C6 constraints remain the execution contract. Do not skip ahead
to publication or mark remote setup/bridge/sandbox/CI evidence as passed because
the plan review passed. The roadmap remains unchanged. Commits, remote setup,
compatibility-bridge release, live sandbox trials, and production enablement
still require their explicit authorization at the stated execution gates.

## Research References

- [Decided brainstorm](../brainstorms/2026-09-11-generic-asynchronous-release-controller.md).
- [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) and [python-semver comparison API](https://python-semver.readthedocs.io/en/stable/usage/compare-versions.html), checked 2026-09-11.
- [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency): bounded pending queues, including `queue: max`, do not replace the durable journal.
- [GitHub Git refs API](https://docs.github.com/en/rest/git/refs): non-force fast-forward updates and exact ref operations.
- [GitHub environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments): reviewer availability, self-review/admin bypass, secrets, and workflow-ref matching.
- [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows): default-branch issue events, workflow dispatch, and token-trigger limits.
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases): draft/publication state, asset inventories, `make_latest`, and workflow-file token permissions.
- GitHub GraphQL schema inspection on 2026-09-11 verified `Issue.lastEditedAt`, `Issue.userContentEdits`, and `UserContentEdit` audit fields. Runtime availability/permissions still require explicit validation; one PowerShell quoting error was corrected during this read-only research.
