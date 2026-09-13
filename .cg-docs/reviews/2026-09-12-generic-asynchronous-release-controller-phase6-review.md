---
date: 2026-09-12
depth: full
type: standard
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P1.13: fixed
  P1.14: fixed
  P1.15: fixed
  P1.16: fixed
  P1.17: fixed
  P1.18: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P3.1: fixed
  P3.2: fixed
---

# Phase 6 Independent Review

**Review complete; changes required.** All ten spec analyses returned usable
results. There are **34 open findings: 1 P0, 18 P1, 13 P2 and 2 P3**. The P0 is
an inherited, explicitly scoped Pages integration risk, not a new Phase 6
regression. No finding was fixed or accepted as an exception in this review.

**Phase 6 is not complete. V6 is not the only remaining gate.** Disabled source
policy and workflows are intentional, but they do not establish functional or
safe integration. The findings below are eligible offline corrections; actual
bridge delivery and authorization remain separate external requirements.

## Scope

This is a dedicated `/cg-review full --report-only` of Phase 6, Steps 11-12,
for the linked plan. Release, update, permission and schema risks require the
full route. The explicit instruction disables triage and all source repairs.

Scope authority:

- `.cg-docs/work-reports/release-controller/2026-09-12-phase6-integration-evidence.json`
- `.cg-docs/work-reports/release-controller/2026-09-12-phase6-readers-evidence.json`
- Plan design contracts, Steps 11-12, testing strategy and completion contract.
- Only lines 2994-3068 of the execution report, its latest Phase 6 section.

The integration evidence is newer than that execution-report section. It is the
source of the current counters and failed final gates. Prior-phase package work
is context only, except where a Phase 6 integration connects to that boundary.
Generated HTML bodies are excluded. The reported generation of 1,486 native
outputs is inherited evidence, not a claim that this review read every output.

The source was frozen before review. Only this review and its compact evidence
file may be written. Code, tests, active state, the plan and the execution report
remain outside this review's write authority. Protected project infrastructure
must remain in place; content corrections may be recommended.

**Files reviewed:** The frozen integration inventory identifies 41 primary paths:
5 reader/workflow, 9 profile/package, 10 core-connection, 7 policy/workflow and
10 native-interface paths. Review also covered directly connected selectors,
schemas, fixture metadata, tests, process/transport and authority code. Full files
or targeted sections were read. This count is not a claim that every generated
adapter body was independently read. No R package markers were present, so the
R-package build-ignore check did not apply.

## Retained Gates

These results are inherited from the frozen integration evidence. They are not
fresh full-suite executions by this reviewer.

| Gate | Retained Result | Review Treatment |
|---|---|---|
| Controller package | 709 passed, 1 failed | Required line-bound failure: `models.py` 323 lines; `build_stage.py` 305 lines. No exception accepted. |
| Native suite | 2,539 passed, 2 failed, 50 skipped, 2 deselected | Registry C2 rejects the approved standalone `packages/cg-release` as module relocation. Preserve actual relocation protection. |
| Canonical full Pester | 2,916 passed, 3 failed, 2 skipped | Three obsolete inline-regex Pages routing assertions remain failed. Pester stays in executor `ses_f6b3c8b92ffepfSp9BsF5x6KJC`. |
| Node selection | 26 passed, 1 failed | Existing Windows file-symlink fixture fails with `EPERM`. This is not a pass or native Unix evidence. |
| Frozen targeted behavior | 38 passed | Useful bounded behavior evidence; not proof of full integration. |
| Native preflight tests | 58 passed | Unit results do not override the failed full native gate. |
| Ruff, disabled install check, workflow YAML, generation, launcher smoke | Passed | Static and local evidence only. No writer activation or live result. |

Step 11 remains **1/2 used, resolved**. Step 12 remains **2/2 used, resolved,
final gate failed**. This review does not reset or consume implementation repair
counters. Coordinator-owned ordinary repairs have not started in this review.

## Required Coverage

All ten analyses are complete. Duplicate observations were merged, and priorities
were normalized to the report IDs. Their original counts must not be added.

| Spec | Findings | Other Check Results And Limits |
|---|---|---|
| `cg-code-quality` | P1.2, P1.4, P2.1, P3.1 | Style, names, errors, duplication and Python boundaries checked. Guarded launcher source is consistent; no additional reader defect found. Actual shell parity is covered by P2.6, not inferred from callbacks. |
| `cg-testing` | P1.1, P1.2, P1.4, P1.6, P2.1-P2.6 | Version corpus, pin/commit/byte assertions, malformed input and tamper checks reviewed. No statistical/stochastic/R/Stata tests apply. Full profile lifecycle and real shell boundaries remain unproved. |
| `cg-documentation` | P1.10, P1.17, P2.9, P2.10, P3.2 | Canonical release/devtag/scanner contracts and help reviewed against code. No Phase 7 README/handoff omission was counted. |
| `cg-version-control` | P0.1, P1.2, P1.10, P1.16, P1.17, P2.8 | No embedded secrets or historical payload/attestation rewrite found. Ignore rules and locks inspected. Uncommitted files and the existing branch name are not findings. Remote freshness/settings were not checked. The initial compose-token P1 claim was withdrawn below. |
| `cg-reproducibility` | P1.2, P1.11, P2.7, P2.8 | Receipt-time preparation, source/controller identities, exact artifact digests and generic lazy profile loading checked. No new clean install/build or native Unix-host delivery was claimed. |
| `cg-performance` | P1.1, P1.3, P1.4, P1.6, P1.13, P1.14, P2.11-P2.13 | Producer ownership, unchanged-input reuse, memory/disk/network bounds and all Pages producers inspected. No handoff timing or Phase 7 benchmark claim. Research vectorization is not applicable. |
| `cg-architecture` | P1.1, P1.2, P1.4, P1.6, P1.8, P1.10, P1.12, P1.13, P2.1, P2.13 | Packaged optional profile, generic isolation, typed hooks, pre-review edits, CI registrations, post-tag PR, completion and trust boundaries traced. Disabled scaffolding was not treated as working topology. |
| `cg-data-quality` | P1.1, P1.4-P1.6, P1.12 | Strict hook fields, versions, inventory identities and response shapes checked. No additional confirmed PR wire-format or launcher defect. Deliberately unresolved disabled-policy fields are not defects. |
| `cg-learnings-researcher` | P1.1, P1.6, P1.11, P1.15 | Four directly relevant lessons applied. Historical main-only advice was not imposed on the new controller. No additional immutable-history mutation found. |
| `cg-adversarial` | P1.1, P1.2, P1.5-P1.7, P1.9, P1.11, P1.12, P1.14, P1.18 | Actual input/state boundaries attacked with bounded probes. Approval/effect ordering and caches traced. No separate cached-success tampering exploit, pre-publication hook-write defect or direct new-controller credential exposure established. |

The parent read all ten local specs. Native read-only subagents were dispatched
for their separate analyses. Each received the Phase 6 scope, evidence paths,
protected-file rule, language-skill requirements and prohibition on repairs,
Pester, new full suites, remotes and derived HTML reads.

## Knowledge Context

The bounded Brain query selected these relevant lessons:

- Deploy the exact successful verified artifact and preserve immutable release
  tag authority: `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`.
- Test the real filesystem, credential and API boundary, not only helper calls or
  source ordering: `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md`.

Saved project memory also confirms reader-before-writer migration and separate
post-tag attestation commits. Older legacy command guidance is not authority
over the current CLI contract. `open-brain` is not exposed in this session;
the local Brain query and targeted project memory were used. Query warnings
were retained and are not passing runtime evidence.

The learnings pass also used
`.cg-docs/solutions/testing-patterns/2026-08-10-gh-cli-fixture-json-keys-must-match-client-parsing.md`
and `.cg-docs/solutions/bugs/2026-08-31-trust-anchor-captured-byte-dispatch.md`.
The historical main-only rule is superseded for relevant legacy dev tags by
`.cg-docs/solutions/bugs/2026-08-14-pages-immutable-ref-gate-rejects-dev-series-pre-release-tags.md`;
the approved September 11 design governs the new controller. `DIGEST.md` was
absent, so selected solutions and the relevant brainstorm were used directly.

## External Boundary

External V6 still requires an authorized, reviewed, published legacy-format
bridge, its real Release/tag/source identities, separate source-bound Windows
and Unix clean-client run identities, and actual bootstrap authority. Local
fixtures do not satisfy delivery. Offline omissions and failed gates must be
resolved before this can be called the only remaining gate.

No Phase 7 work, remote action, commit, PR, setting or secret change, publisher
activation, live publication or Pages deployment was performed by this review.

## Findings

All findings are open. A static trigger is not an executed live result. Exact
executed probe commands, inputs, results and limitations are in the companion
JSON evidence; no full suites were rerun by this reviewer.

### P0 - Blocking

**[P0.1]** [cg-version-control] `.github/workflows/pages.yml:28-41,58-64` -
Mutable development code executes with Pages publication authority.

**Proof and impact:** The legacy job checks out `dev`, then runs its documentation
scripts in the same job that has `pages: write` and `id-token: write`. Harmful
development code can act with that job's authority or change the stable site
input before deployment. The new cutover guard permits this path when the policy
is absent or disabled; it does not isolate source execution.

**Scope qualification:** This is an inherited security defect in the explicitly
reviewed Step 12 Pages integration boundary, not a new Phase 6 regression. An
actor must be able to place code in `dev`, and the workflow must pass any actual
environment gates. Those GitHub settings were not inspected. No exploitation,
credential disclosure or live deployment was observed.

**Correction:** Keep the existing infrastructure and guards, but separate the
unprivileged development build from trusted composition/deployment. Transfer an
exact-run artifact and verify source identity, full inventory and digests before
deployment. No mutable source script may run with Pages or OIDC write authority.

### P1 - Critical

**[P1.1]** [cg-data-quality, cg-learnings-researcher, cg-performance]
`scripts/release_profile_gpid.py:142-154` and
`packages/cg-release/src/cg_release/profile_docs.py:200` - Profile calls do not
match the production GitHub reader interface.

**Proof and impact:** Source discovery calls `get('git/trees/<sha>?recursive=1')`
and then nonexistent `api.releases()`. Documentation completion calls
`pages('deployments?environment=github-pages')`. The real `GitHubReads.get()`
rejects query characters at `github.py:71-80`; `pages()` delegates to it.
The parent probe returned `E_ENDPOINT` for both query paths, before its
fail-if-called transport ran, and confirmed that `releases` is absent. Valid
GPID preview/admission and post-publication completion cannot traverse these
connections.

**Correction:** Use bounded dedicated provider operations, including the existing
recursive-tree pattern and `pages('releases')`. Preserve endpoint, pagination,
identity and response-shape checks. Test the hooks through the actual reader with
an injected transport, not a fake API that provides extra methods.

**[P1.2]** [cg-code-quality, cg-reproducibility, cg-version-control]
`.github/workflows/release-controller-build.yml:114-127` and
`scripts/release_profile_build.py:41-48` - The registered native/profile build
does not provision its native Python dependency.

**Proof and impact:** The workflow installs the controller lock and selects its
virtual environment through `PATH`. The builder passes `sys.executable` to full
native preflight. The native test selection imports PyYAML, but the controller
runtime and development dependencies do not include it. The code-quality probe
found no `yaml` module in that local environment. The supplied integration
evidence already records the same interpreter mismatch. A separate passing run
with the developer's native interpreter does not repair the declared source-job
environment. This is not a claimed live Actions failure.

**Correction:** Provision an explicit locked GPID native-test environment in the
unprivileged source job, select its interpreter, and bind its dependency identity
to build evidence. Keep GPID-only dependencies out of the generic core runtime.
Verify the actual environment-to-builder connection in a clean offline fixture.

**[P1.3]** [cg-performance]
`packages/cg-release/src/cg_release/profile_worker.py:132,172,191` - The trusted
composer cannot invoke its packaged Node helper.

**Proof and impact:** The actual workflow invokes this worker, which calls
`run_process('node', ...)`. `process.py:154-166` permits only `git`, `gh`, `gpg`
and `gpgconf`. A parent probe returned `E_PROCESS_ARGUMENT` before process spawn.
Direct Node helper tests bypass this boundary. Composition cannot complete after
the preceding build/download work.

**Correction:** Add a narrow process interface for the installed, pinned
static-data helper, with argv validation, containment, output bounds and deadlines.
Do not permit arbitrary source-selected executables in the privileged worker.
Test the actual worker-to-process connection.

**[P1.4]** [cg-code-quality, cg-data-quality, cg-performance]
`packages/cg-release/src/cg_release/profile_docs.py:115-122` - Failed composition
recovery accesses an absent policy field.

**Proof and impact:** With unchanged desired inputs and a completed failed run,
the branch reads `context.policy.retry_budget`. The strict `Policy` and
`ProfilePolicy` models have no such field and reject undeclared fields. A
code-quality in-memory probe reached the production branch and raised
`AttributeError`. It used a partial real `Policy` constructed without full
validation, plus fake selection and API reads; it was not an end-to-end recovery
test. The model-field inspection independently confirms the missing member.

**Correction:** Define a strict bounded composition retry policy, or an explicit
internal limit if it is not configurable. Test failed, cancelled and timed-out
runs with unchanged inputs and exhausted budgets using valid policy fixtures.
Keep composition repair accounting separate from immutable release builds.

**[P1.5]** [cg-data-quality]
`packages/cg-release/src/cg_release/profile_snapshot.py:52-75` - Snapshot approval
accepts file inventories that the trusted importer cannot use.

**Proof and impact:** A parent probe added `assets` to the five required files,
including `assets/site.css`, and recomputed every digest. The Python verifier
accepted this impossible file/directory structure. It also accepted
`extra file.txt`, which the JavaScript importer's `safeName()` rejects.
`scripts/docs-snapshots.js:172-181` can therefore fail after publication on an
already approved immutable snapshot. The probe was in-memory; no import or
filesystem mutation was attempted.

**Correction:** Validate the complete file/directory structure before approval,
including parent conflicts and directory case aliases. Align Python and JavaScript
path grammar and add shared acceptance/rejection fixtures.

**[P1.6]** [cg-data-quality, cg-learnings-researcher, cg-performance]
`packages/cg-release/src/cg_release/profile_snapshot.py:23-25` - Snapshot capacity
limits conflict across the producer, approval decoder and publication reader.

**Proof and impact:** Policy and snapshot verification advertise a 128 MiB
envelope, but `jsonio.py:35-36` rejects JSON above 4 MiB. The parent probe's valid
small envelope passed, while a valid 3 MiB file produced a 4,195,066-byte envelope
that failed with `E_RESPONSE`. In addition, `publication_remote.py:196-216` caps
asset download at 64 MiB. The current 4 MiB failure masks that downstream mismatch;
this review does not claim that a 64-128 MiB envelope currently passes approval.

**Correction:** Define one supported capacity contract from snapshot export through
approval and remote asset verification. Use a snapshot-specific strict bounded
decoder or enforce a smaller supported limit consistently. Do not raise the
general API limit without need, and do not change published bytes as a repair.

**[P1.7]** [cg-adversarial]
`packages/cg-release/src/cg_release/recovery.py:139-147` - Current policy can
silently remove a published request's sealed completion requirements.

**Proof and impact:** Scheduled `controller.reconcile()` checks actor authority
but reaches `finish_published()` without comparing the current policy digest to
the request when there is no recovery grant. Removing the current GPID profile
fields makes `verified_hooks()` return `{}` and selects `required=set()`. A real
in-memory journal probe reached `complete` with `publication-hooks={}` while the
request retained its earlier policy digest. Publication inspection was mocked
successful, and the probe did not reconstruct a full approved GPID release.
The source path confirms the missing binding before completion selection.

**Correction:** Require the bound policy or an explicit applicable recovery grant
before hook operations. Derive required hooks from immutable request/build
evidence, not only the current profile flag. Test policy changes during published
reconciliation without waiving the original evidence requirements.

**[P1.8]** [cg-architecture]
`scripts/generate-whats-new.js:185-187` - Release-set loading still rejects new
SemVer payload filenames.

**Proof and impact:** `validatePayload()` accepts a pre-release tag, but the real
release-set loader still permits only stable or four-part filenames. The profile
writes `releases/v1.5.0-rc.10.json`. An in-memory filesystem probe through the real
loader rejected that filename; the parent rerun exited 1. The documentation build
cannot produce its required snapshot for an otherwise valid pre-release. Direct
payload-validation tests do not cover this second reader boundary.

**Correction:** Validate the filename tag through the shared parser. Preserve
exact filename/payload equality, historical immutability, and byte equality of
`latest.json` with its versioned payload. Test complete release-set loading.

**[P1.9]** [cg-adversarial]
`scripts/release_profile_gpid.py:142-170` and
`packages/cg-release/src/cg_release/source.py:124-127,194-218` - Selected source
history can hide a stranded protected-default payload.

**Proof and impact:** The core reads policy from the protected default tree, but
the profile scans release payloads only in the selected source tree. If default
contains a durable payload with neither tag nor Release and an older eligible
source branch does not contain it, remote tag/Release inventories cannot reveal
that source-only obligation. A source-only isolation probe proceeded to mocked
blob loading with no historical payloads; it did not prove admission with missing
required files. The cross-tree omission follows from the inspected call chain.

**Correction:** Reconcile durable payload inventories from both exact default and
selected source revisions before preparation. Preserve full remote history checks;
a source branch must not remove a repository-wide publication obligation.

**[P1.10]** [cg-architecture, cg-documentation, cg-version-control]
`create-release.ps1:76-85,575-602` - Legacy operation flags do not enforce actual
cutover and historical recovery authority.

**Proof and impact:** Bridge checks a local policy copy, and an absent copy permits
it. Recovery bypasses that guard and does not require a historical immutable
identity or reviewed recovery record. Reserve can then push an absent remote tag
and create a Release. `tests/create-release.Tests.ps1:556,614-622` explicitly uses
Recovery in a new-publication case. Other permission/ruleset checks may deny a
particular configuration; no live bypass is claimed. They do not supply the
missing operation-specific authorization.

**Correction:** Read cutover authority from the exact protected remote default
policy. Before a Recovery write, require an existing immutable stranded identity
or explicit reviewed historical recovery record. Reject routine new publication
through Recovery. Preserve uncertain-write reconciliation and all old guards.

**[P1.11]** [cg-reproducibility, cg-learnings-researcher, cg-adversarial]
`.github/workflows/release-controller-bridge.yml:29-30,50-51` - Bridge qualification
is connected to synthetic reader fixtures, not actual bridge installation.

**Proof and impact:** The selected test builds a miniature local repository,
invents tags, copies the updater, substitutes a no-op PowerShell helper and uses
`CG_INTERNAL_CALL=1` with an empty consumer. It omits managed-file refresh/link
continuation and actual distribution dependencies. `verify_bridge():112-139`
accepts the resulting run/job conclusions as clean-client evidence. A broken
real bridge helper can therefore escape this designated check. The disabled
workflow's comment that fixtures are not delivery does not repair its wiring.

**Correction:** Retain these useful offline reader tests, but add a distinct
authorized actual-bridge clean-consumer path. Bind it to the real repository,
Release, tag, revision, installed tree and subsequent new-format pin, with managed
assets and continuation paths active. Its implementation is an offline omission;
executing authorized delivery and obtaining real identities remain external V6.

**[P1.12]** [cg-architecture, cg-data-quality, cg-adversarial]
`packages/cg-release/src/cg_release/profile_docs.py:21-63` - Stable documentation
bootstrap is ignored and its prerequisite is checked too late.

**Proof and impact:** Selection reads journal publications but not adopted stable
history. A first controller pre-release with a trusted older stable bootstrap
fails with `E_DOCS_STABLE`; an older maintenance release cannot retain a newer
adopted stable default. Isolated probes confirmed the first case with publication
verification supplied in memory. Admission permits publication before this
completion prerequisite is checked.

**Correction:** Define a reviewed immutable documentation baseline for adopted
history and include it in selection. Check availability before submission or
preparation. If required evidence is unavailable, stop before writes with an
explicit setup error, not after publishing. Do not rewrite old tags/assets or
silently require an unrelated new stable release.

**[P1.13]** [cg-performance, cg-architecture]
`packages/cg-release/src/cg_release/profile_docs.py:105-110,130-134` - An
unregistered documentation dispatch has no recovery path.

**Proof and impact:** Existing dispatch evidence or an uncertain intent causes an
immediate return when registration is absent. There is no bounded run discovery.
Two in-memory passes made zero run reads. A failed registration or a pending run
replaced in the workflow-level `pages` concurrency queue leaves the release
waiting indefinitely. `cancel-in-progress: false` does not preserve every pending
run; legacy producers enter the same queue before their later cutover checks.

**Correction:** Reconcile sealed dispatches against bounded remote run inventory.
Require terminal/absence evidence before a safe replacement. Keep the shared
deployment guard, but do not make durable registration depend on that queue.

**[P1.14]** [cg-performance, cg-adversarial]
`packages/cg-release/src/cg_release/profile_docs.py:124-129` - Repeated mutable
dev refreshes eventually exhaust the immutable release record.

**Proof and impact:** Each refresh retains request, dispatch, registration and
composition entries on the same stable-release record. Requests repeat the full
release selection. `journal_rules.py:24-36` limits retained evidence within the
64 KiB record. A simplified probe through the real limit failed at refresh 42
during dispatch; it omitted normal release evidence, so this is not a guaranteed
real-world refresh count. Unbounded normal refreshes must eventually hit the cap.

**Correction:** Use separate bounded composition records with compact links from
the immutable release. Preserve audit history; do not truncate prior evidence or
only raise the cap. Test repeated refreshes beyond the current boundary.

**[P1.15]** [cg-learnings-researcher]
`packages/cg-release/src/cg_release/profile_worker.py:41-75,79-106,200-205` -
Documentation workers do not recheck the applicable requester's authority.

**Proof and impact:** Registration and composition validate workflow/run identity,
but `verify_run()` can accept the dispatching App without checking the original
requester. `context_for()` verifies policy/journal controls, not that requester's
current role. Revocation after dispatch and before these delayed worker effects
does not stop their journal/composition operations. The earlier coordinator role
check is not a fresh worker-boundary check. This is a static delayed-revocation
scenario, not an executed permission change.

**Correction:** Carry the applicable requester/resumer or approved recovery
principal and recheck authority before consequential worker and deployment
effects. Test denial after queue/build delay with zero further effects. Define
maintenance authority explicitly rather than relying forever on an old creator.

**[P1.16]** [cg-version-control]
`packages/cg-release/src/cg_release/profile_evidence.py:88-98` - The post-tag
evidence PR omits required generated attestation copies and ownership records.

**Proof and impact:** The sealed edit set permits only the canonical attestation.
The generator includes this shared asset family in native outputs; existing
attestations are tracked at `.kilo/.compound-gpid-generated.json:791-801`.
`scripts/tests/test_target_drift.py:219-230,258-269` requires the complete generated
path set. The evidence PR therefore creates native drift. Adding native output
after sealing changes the head/tree that `reviewed_commit.py:24,48` verifies.

**Correction:** Generate and verify the canonical attestation, native copies and
ownership manifests before sealing the evidence PR edit set. Use a safe verified
generation stage, not arbitrary target code with control credentials. Preserve
all historical attestation bytes and never move the release tag.

**[P1.17]** [cg-documentation, cg-version-control]
`.github/workflows/release-pages.yml:53` and `create-release.ps1:649-664` - Cutover
removes the producer needed for some historical recovery.

**Proof and impact:** Every legacy deployment is rejected after cutover, while
Finalize still requires a successful exact `release-pages.yml` run. A historical
release with missing or failed deployment evidence cannot obtain that proof.
Recovery with already valid existing deployment evidence may still work; the
finding is not that every historical recovery is blocked.

**Correction:** Add a narrow authorized historical recovery producer, preserving
tag and artifact bytes, and connect its exact evidence to finalization. Document
supported checkpoints. Do not remove deployment checks or reopen routine legacy
publication.

**[P1.18]** [cg-adversarial]
`.github/workflows/pages.yml:43-58` and
`.github/workflows/release-pages.yml:33-53` - Legacy Pages cutover reads content
from `main` instead of authoritative protected-default policy.

**Proof and impact:** If protected `dev` is the default and enables the controller
while `main` retains a disabled copy, both legacy guards allow deployment. Core
policy/context instead uses the protected remote default. Shared concurrency
serializes these conflicting producers but does not establish ownership. This
configuration was not queried or changed remotely.

**Correction:** Verify cutover from an exact protected-default revision in every
legacy deployer, and recheck before deployment. Keep stable content selection
separate from policy authority; retain the existing workflow infrastructure.

### P2 - Improvements

**[P2.1]** [cg-code-quality, cg-testing, cg-architecture]
`packages/cg-release/tests/test_module_bounds.py:9-13` - The required module bound
is failed. Phase 6 leaves `models.py` at 323 lines and `build_stage.py` at 305.
This is a real gate, not a waived style warning. Extract profile records and
profile artifact validation by responsibility; preserve behavior and do not
relax the 300-line assertion.

**[P2.2]** [cg-testing]
`scripts/cg_validate_modules.py:556-570` - C2 treats every `packages/*/` directory
as canonical module relocation. The approved standalone `packages/cg-release`
therefore fails real-repository tests at `test_module_registry.py:598,605` and
ownership validation without evidence of relocated `.github` assets. Correct the
classification with a narrow standalone-package case and retain negative tests
for actual kernel/capability/suite relocation. Do not move protected infrastructure.
The gate remains failed until corrected; priority reflects a validator conflict,
not approval to ignore it.

**[P2.3]** [cg-testing]
`tests/docs-automation.Tests.ps1:75-105` - Three saved Pester failures require the
removed inline parser instead of testing the new helper boundary:

| Exact Test Name | Failed Assertion |
|---|---|
| `supports unprivileged tag builds through the protected workflow-run controller` | Line 84 requires an inline version regex. |
| `accepts dev-series pre-release tags (v1.2.0.900x) in the unprivileged builder` | Line 90 reports `Expected 2, but got 0` extracted inline regexes. |
| `binds stable tags to main and prerelease tags to dev` | Line 97 requires literal `required_branch="main"`. |

All belong to `Pages exact-artifact deployment contracts`; saved records are at
`tests/last-run.json:163-183`. Test executed helper behavior and verify workflow
delegation. Retain branch/tag/lineage, privilege, exact-run, payload-byte and
artifact-inventory assertions. Only the existing canonical executor may run
Pester. Obsolete assertions are still failed assertions, not passing evidence.

**[P2.4]** [cg-testing] `package.json:14` and `scripts/cg_pr_preflight.py:49-105,892`
- New compatibility suites are absent from ordinary producers.
`test:docs-automation` omits `release-version.test.js` and `docs-snapshots.test.js`.
Native selection omits `test_release_version_readers.py`; its controller route
adds profile/launcher tests only. Connect these suites to appropriate ordinary
CI selectors, including supported shell hosts. A disabled bridge workflow is not
an ordinary regression gate. Preserve older reader-runtime support.

**[P2.5]** [cg-testing]
`scripts/tests/test_release_controller_profile.py:139` and
`packages/cg-release/tests/test_profile_stages.py:112` - Direct helpers and supplied
verified dictionaries do not test the complete profile path. Acquisition,
verification-call placement, evidence PR and composition can break without these
tests detecting it. Add a bounded offline lifecycle fixture with the real journal
and production adapters, replacing only outer I/O. Assert no premature effect and
require exact reviewed payload, snapshot, committed attestation and deployed
artifact evidence before `complete`. No mutation test was actually applied.

**[P2.6]** [cg-testing]
`scripts/tests/test_release_controller_launchers.py:30` - Argument tests inject the
Python runner instead of executing CMD/Bash launchers. Five-platform Markdown
parity and help smoke tests do not prove quoting, empty values, fallback, Store
stub rejection, `.cmd` shim return, exit propagation or shadowing. Add isolated
real-shell fixtures with fake interpreter candidates and an argv-recording child
for all core commands and legacy routes. No actual forwarding bug is claimed.

**[P2.7]** [cg-reproducibility] `packages/cg-release/hatch_build.py:14-16` - An
unpacked sdist prefers a surrounding `scripts/` directory over bundled resources.
For example, extraction under `<checkout>/tmp/cg_release-0.1.0` selects
`<checkout>/scripts`. Thus identical sdist bytes can yield a different or failed
wheel build. Use bundled resources for an sdist and require a complete set; allow
canonical repository inputs only after explicit layout verification. Test a
source-free installed profile and conflicting external scripts without changing
the sdist.

**[P2.8]** [cg-reproducibility, cg-version-control]
`scripts/tests/test_release_version_readers.py:121-123` - Frozen `.fixture` bytes
have no checkout newline protection. `git check-attr text eol` returned
`unspecified` for both updater fixtures. A later `core.autocrlf=true` checkout can
change their bytes before the test hashes them; the inner repository's `* -text`
rule at line 139 is too late. Add exact-path `-text` attributes. Preserve recorded
historical bytes and hashes; do not normalize or repin to hide conversion. No
fresh checkout was performed in this review.

**[P2.9]** [cg-documentation] `create-release.ps1:32,51,70-77` and
`.github/prompts/cg-release.prompt.md:436,504` - Required `LegacyOperation` is
absent from parameter help and executable examples. Copied examples fail the new
runtime guard. Document both operations and their enforced authority/cutover
limits; include the correct operation in every Reserve/Finalize example.

**[P2.10]** [cg-documentation] `scripts/release_profile_gpid.py:173-174,248-249`
- New public profile/launcher APIs lack the required input, return, error,
example and side-effect contracts. Similar gaps occur in `hooks.py`,
`profile_snapshot.py`, `profile_evidence.py`, `profile_docs.py`, `cg_release_cli.py`
and the profile build/install helpers. Document provenance, receipt-time format,
declared edit sets, remote writes and pending results. Correct the worker example
at `profile_worker.py:211` to include required `--nonce`. This is current API help,
not missing Phase 7 documentation.

**[P2.11]** [cg-performance]
`packages/cg-release/src/cg_release/profile_docs.py:22-26` - Every selection
re-inspects all publications before unchanged-input reuse. Each inspection repeats
tag/Release inventories and downloads assets, causing approximately quadratic
metadata work and historical-byte transfer as history grows. Composition repeats
selection and downloads snapshots again. Acquire complete inventories once per
reconciliation, separate selection from byte acquisition, and reuse exact verified
identities/bytes where safe. Retain fresh authority and mutable-state checks.
No elapsed-time cost was measured.

**[P2.12]** [cg-performance] `scripts/docs-snapshots.js:68-80,118-144` - Aggregate
composition bounds are checked only after copying all snapshots. A valid
5,000-file stable snapshot is copied at root and under its version, so adding a
five-file dev snapshot produces 10,005 files and fails only after copying. Validate
final destinations, file count, bytes and depth before materialization and check
deployment capacity before admitting incompatible release output. Keep historical
version paths; do not silently discard snapshots. This was a static count proof,
not a filesystem stress test.

**[P2.13]** [cg-performance, cg-architecture]
`scripts/release_profile_build.py:41-48` and `scripts/cg_pr_preflight.py:885-895`
- The native/profile producer repeats the controller suite, Ruff and wheel/sdist
build already owned by the required six-cell exact-source CI. Separate registered
gate ownership or reuse verified evidence; preserve the normal local full gate
and still require both producer identities. Add gate-count assertions. This is
one extra package pass per attempt, not a measured timing claim.

### P3 - Minor

**[P3.1]** [cg-code-quality] `packages/cg-release/src/cg_release/hooks.py:31-42`
- The advertised `Profile` protocol omits `verify_bridge()`, `verify_snapshot()`
and the resource interface used by callers, and declares a completion return type
different from the raw dictionaries actually validated. Declare the actual typed
boundary and prefer an explicit resource accessor over inspecting `__file__`.

**[P3.2]** [cg-documentation] `scripts/tests/test_release_version_readers.py:112`
- The fixture docstring says `unmodified HEAD reader`, but it uses frozen bytes
identified and hashed in `source.json`. Correct that provenance description;
retain the distinction between local transport evidence and bridge delivery.

## Evidence Assessment

The new source-build, six-cell CI and dev-preview jobs were inspected for control
or publication App credentials; none were found in those source jobs. This does
not cover the inherited privileged legacy Pages path in P0.1. Required build
registrations distinguish controller/source SHAs and include native/profile
producer identities. Their static wiring is not an actual successful Actions run.

Payload and notes enter the expected preparation tree before reviewed-head binding.
`publishedAt` is preparation metadata from the durable receipt. Snapshot validation
is called before `awaiting-approval`. Approval is rechecked in the publication
worker before recomputation and before effects. `finish_published()` inspects the
remote publication before completion-hook effects. No independent pre-publication
hook-write defect was established. P1.7 concerns later policy binding, not a claim
that remote inspection is absent.

The exact-Git-object cache does not cache mutable branch, permission, Release or
run state. Complete-state routing skips new evidence verification, but the probes
did not establish a separate remote-tampering exploit. That observation is not a
second finding. Deliberately empty/unresolved disabled installation fields are not
counted as defects or accepted as bootstrap evidence.

The original version-control claim that compose's `github.token` must fail without
explicit `actions: read` was withdrawn after parent challenge: public resource
access can affect this result, and no HTTP failure was observed. The missing
explicit permission remains a portability consideration, not a counted P1.
An explicit narrow read grant is preferable when qualifying private repositories.

Numeric pre-release ordering, build-metadata precedence, legacy four-part identity,
strict hook booleans, old pin/commit assertions and generic lazy profile loading
have useful inspected coverage. P1.8 and P2.4-P2.6 limit broader claims.
The Node `EPERM` case at `scripts/tests/assemble-docs-site.test.js:154` failed while
creating a file symlink, before rejection assertions. A passing directory-junction
case is not a substitute; later supported-host validation is still needed.

## Handoff

The companion evidence is
`.cg-docs/work-reports/release-controller/2026-09-12-phase6-review-evidence.json`.
It records all ten task identities, retained gates, exact executed probe commands
and limitations, artifact validation, and the unchanged recovery counters.
Quoting/setup failures are recorded as unusable probe attempts, not product bugs.

Coordinator-owned repairs must address the required offline gates and findings
before an external-V6-only state can be claimed. This report authorizes no remote
operation and performs no triage. An independent high-reasoning review remains the
appropriate capability level for later security and release-boundary validation;
no model or reasoning setting was changed by this review.

## Review Repair Cycle 1 Dispositions

Recorded 2026-09-12 after the final source freeze and offline gate execution.
The original review, claims, probes and failed gates above remain historical
evidence. The frontmatter now records **34 source repairs, zero skipped and
zero open source findings**. Here `fixed` means implemented with passing
applicable offline checks, not independently verified, delivered or activated.
The coordinator must run independent verification against this frozen source.
No independent final review was started by the repair writer.

The repair authority is the user's Phase 6 `review:auto` authorization for this
explicit report only. Step 11 remains implementation 1/2 used and resolved;
Step 12 remains implementation 2/2 used and resolved with its original final
gate failed. This separate review repair cycle did not reset those counters.

Evidence paths below share `.cg-docs/work-reports/release-controller/`:

- `2026-09-12-phase6-repair1-security.json`: security RED/GREEN history and source inventory.
- `2026-09-12-phase6-repair1-adapters.json`: real adapter/lifecycle RED/GREEN history.
- `2026-09-12-phase6-repair1-packaging.json`: bridge, package, native and shell evidence.
- `2026-09-12-phase6-repair1-gates.json`: preserved first frozen gate failures.
- `2026-09-12-phase6-repair1-final-gate-fixes.json`: subsequent same-cycle integration corrections.
- `2026-09-12-phase6-repair1-final-gates.json`: actual final frozen non-Pester results.
- `2026-09-12-phase6-repair1-evidence.json`: compact final handoff including full Pester.

### Per-Finding Results

Test filenames in this table identify checks included in the executed batch or
final suites. Exact invocations and counts are in the evidence files, not
inferred from inspection. Counts from overlapping selections are not added.

| Finding | Source Repair | Passing Offline Evidence |
|---|---|---|
| P0.1 | Mutable dev builds are unprivileged; protected-default code verifies and composes exact-run static artifacts. | `legacy-pages.test.js`, `test_legacy_pages_security.py`, actual docs-validator negative cases, full Pester Pages contracts. |
| P1.1 | Dedicated recursive-tree, deployment and bounded release operations match the production reader. | `test_profile_adapter_reads.py`, `test_profile_lifecycle.py` through actual `GitHubReads` transport. |
| P1.2 | Separate locked native environment and interpreter/distribution receipt are bound to registered source/run evidence. | `test_profile_native_environment.py`, `test_release_producer_contracts.py`, full real profile lifecycle. |
| P1.3 | Only RECORD-verified installed static Node resources run through contained argv, bounded output and deadlines. | `test_profile_process.py`, installed-wheel smoke and actual lifecycle composition. |
| P1.4 | Strict bounded composition retry policy covers unchanged failed runs without affecting release build counts. | `test_profile_dispatch.py`, `test_profile_input_boundaries.py`. |
| P1.5 | Python and Node use shared path grammar, directory aliases and file-parent collision checks before mutation. | `test_profile_adapter_reads.py`, `docs-snapshots.test.js`, shared `snapshot-paths.json`. |
| P1.6 | Export, approval, importer and publication reads agree on the snapshot-specific capacity contract. | Large-envelope and installed-import checks in `test_profile_adapter_reads.py` and `test_profile_lifecycle.py`; Node bounds. |
| P1.7 | Fresh policy/grant checks cannot remove original approved-build completion requirements. | `test_profile_security.py`, actual journal/lifecycle policy-change tests. |
| P1.8 | The complete payload loader uses the shared version parser and preserves exact filename/payload/latest equality. | `release-version.test.js`, `generate-whats-new.test.js`, 12-payload canonical validation and full Pester. |
| P1.9 | Preparation reconciles durable payload obligations at both exact protected-default and selected source trees. | `test_profile_input_boundaries.py`, `test_profile_lifecycle.py` before submission/preparation writes. |
| P1.10 | Legacy writes require protected remote-default cutover authority and constrained immutable historical recovery. | Actual offline `create-release` Pester functions, 105 passed; revoked/changed authority produces no next write. |
| P1.11 | Distinct real delivered-bridge qualifier and exact remote evidence decoder replace synthetic reader-job qualification. | `test_bridge_qualification.py`, `test_bridge_client_roundtrip.py`, `test_profile_bridge.py`. Real authorized delivery remains unexecuted. |
| P1.12 | Reviewed immutable docs baselines include adopted stable history and are checked before mutation. | First-prerelease and older-maintenance cases in `test_profile_lifecycle.py`. |
| P1.13 | Sealed dispatches use bounded recent run discovery and terminal/two-observation absence proof before replacement. | `test_profile_dispatch.py`, `test_profile_input_boundaries.py`, including registered-run retention loss. |
| P1.14 | Separate authenticated bounded composition records preserve history without growing the immutable parent record. | `test_composition_journal.py` above 64 KiB total; real-provider 48-refresh run retains 49 compositions. |
| P1.15 | Delayed registration/composition/deployment rechecks original and applicable resuming/recovery authority. | `test_profile_security.py`, `test_gpid_pages_controls.py`, lifecycle `EXPECTED_MANIFEST` and revoked-actor checks. |
| P1.16 | Data-only generation seals canonical attestation, four native copies and four ownership manifests before the evidence PR. | `test_profile_evidence_edits.py`, actual nine-file PR/merge lifecycle and generated working-tree drift checks. |
| P1.17 | Narrow reviewed historical recovery producer binds existing tag, build run, artifact ID and archive digest; Finalize verifies that evidence. | `create-release` Pester and `legacy-pages.test.js`; missing/expired/stale evidence remains blocked. |
| P1.18 | All legacy policy reads and final effect checks use the exact protected remote default, not assumed main. | Pester default-branch/cutover cases, `legacy-pages.test.js`, `test_legacy_pages_security.py`. |
| P2.1 | Profile/model and build verification responsibilities were split below the unchanged 300-line package bound. | `test_module_bounds.py` in complete 807-test package suite. |
| P2.2 | C2 recognizes only the approved standalone package layout and still rejects actual canonical module relocation. | `test_module_registry.py`, all three real-repository module validators, passing full prepare gate. |
| P2.3 | Pester checks helper delegation and current security behavior instead of removed inline regexes. | Final unfiltered Pester 2,931 passed, zero failed, two existing skips. |
| P2.4 | Ordinary native/Node selectors and supported-host CI include readers, snapshots and legacy security tests. | `test_release_producer_contracts.py`, full native selection, actual 102-test Node selection; file-symlink host failure retained. |
| P2.5 | Real offline lifecycle covers acquisition, journal, preparation, approval, publication, evidence PR, installed helper and deployment completion. | `test_profile_lifecycle.py` replaces only outer I/O and checks no premature effect plus exact reviewed/deployed bytes. |
| P2.6 | Actual CMD/Bash fixtures cover forwarding, empty/quoted values, fallback, Store stubs, shim return, exit status and shadowing. | `test_release_controller_launchers.py` in final 28-test profile/launcher selection; native Unix remains separately required. |
| P2.7 | Complete bundled sdist resources take precedence; repository fallback requires a real verified checkout. Trusted installs use owned copies. | `test_profile_sdist.py`, `test_install.py`, conflicting surrounding scripts and real source-free installed Node import. |
| P2.8 | Exact-path `-text` attributes protect both frozen updater fixtures without changing recorded hashes. | `test_release_producer_contracts.py` and frozen-reader hash checks. |
| P2.9 | Legacy help and all executable Reserve/Finalize examples name the operation and enforced recovery/cutover boundary. | Full prompt/install/create-release Pester and regenerated native parity. |
| P2.10 | Public profile/bridge/build/install/CLI/resource APIs document arguments, results, errors, examples and side effects. | Full package/native lint, installed CLI checks, current generated reference docs and contract parity. |
| P2.11 | Selection acquires inventories once, separates metadata from bytes and downloads each exact selected snapshot once. | Actual provider/lifecycle call-count checks with fresh mutable authority and deployment reads retained. |
| P2.12 | Final destination, file/directory count, size and depth checks run before composition copies or admission of incompatible output. | `docs-snapshots.test.js` aggregate pre-copy checks and Python approval capacity checks. |
| P2.13 | Native producer excludes six-cell-owned package gates; local full preflight keeps both producers and all gates. | Executed gate-owner counts and timeout tests; actual full prepare completed all nine commands. |
| P3.1 | Typed profile protocol matches bridge, snapshot, completion and explicit installed-resource interfaces. | `test_profile_hooks.py`, real installed-resource tests and package lint. |
| P3.2 | Reader fixture documentation names frozen source.json-hashed historical bytes instead of moving HEAD. | Reader/hash tests and preserved frozen fixture bytes. |

### Final Gate Results

Final source generation used `python scripts/cg_generate_targets.py --all` and
wrote 1,486 files. The final prepare command with `--format json` passed all
nine selected commands. Its complete results were native 2,585 passed, zero
failed, 50 skipped and two deselected; package 807 passed; profile/launcher
28 passed. Extra plan/parity tests passed 56 with eight existing POSIX-host
skips. This is working-tree/prepare evidence, not a reviewed committed gate.

The dedicated Pester executor ran `. tests\Run-Tests.ps1` without flags or
pipeline. `tests/last-run.json` at 2026-09-12T16:38:16Z reports passed true,
2,931 passed, zero failed, two skipped, total 2,933 and filteredFiles null.
Package lint, all 18 touched-script py38 lint inputs, builds/isolated installs,
19 YAML checks, disabled installation, docs freshness/validation/fingerprint,
canonical release-set validation and generated working-tree parity passed.

`npm run test:docs-automation` remains **failed**: 101 passed and one unchanged
file-symlink `EPERM` at `assemble-docs-site.test.js:154`. It must run unchanged
on a supported host. No skip, elevation, host installation, junction substitute,
assertion weakening or accepted exception was introduced.

### Frozen Handoff

Status: **source-frozen-ready-for-independent-verification**. Source edits have
ceased. Independent verification remains coordinator-owned and unexecuted here.
Phase 6 and V6 are **not complete**, and V6 is not the only outstanding check:
the supported-host file-symlink case, native Unix/old-reader runtime coverage,
actual source-bound six-cell CI and committed-candidate evidence remain unmet.
Real bridge delivery still requires reviewed previous/bridge/successor identities,
Release/tag/source/tree bindings and separate native Windows/Unix run, job,
artifact and digest evidence. No synthetic fixture ID is installation authority.

The writer and installation remain explicitly disabled with unresolved real
authority. No Phase 7, commit, push, PR, release, Pages deployment, settings,
secret, activation or historical tag/payload/attestation rewrite occurred.

## Probe Appendix

The companion JSON contains the parent, code-quality, architecture and testing
probe commands. The longer adversarial inputs and remaining failed invocation
commands are retained here to keep that evidence record bounded. These are
execution records, not instructions to run publication or repair operations.
No subagent exposed a numeric exit code unless the evidence explicitly says so.

### Adversarial Invocation

For A-D, the executor passed each Python block below as the quoted stdin string:
`$env:PYTHONDONTWRITEBYTECODE='1'; '<Python block>' | & "packages/cg-release/.venv/Scripts/python.exe" -B -I -`.
The blocks are retained verbatim from the executor, not condensed reproductions;
the displayed C block omits its final empty line. This wrapper is a command
construction record, not a literal command containing a placeholder.

### Probe A

```python
import sys, json, base64, hashlib
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
sys.path[:0] = [str(Path.cwd()/"packages/cg-release/src"),str(Path.cwd()/"scripts")]
import release_profile_gpid as p
from cg_release.github import GitHubReads
from cg_release.events import ControllerError
from cg_release.profile_snapshot import verify_snapshot
from cg_release.profile_docs import selection
from cg_release.stage_router import advance
from cg_release.recovery import finish_hooks
api=GitHubReads("github.com","example/repo",cwd=Path.cwd(),runner=lambda *a,**k: (_ for _ in ()).throw(AssertionError("Network forbidden")))
errors=[]
for name, action in [("profile source query",lambda:p.source_blobs(api,"a"*40,"v1.0.0")),("docs deployment query",lambda:api.pages("deployments?environment=github-pages"))]:
 try: action()
 except ControllerError as e: errors.append([name,e.code])
with patch.object(api,"get",return_value={"sha":"a"*40,"truncated":False,"tree":[]}):
 try:p.source_blobs(api,"a"*40,"v1.0.0")
 except AttributeError as e: errors.append(["profile releases interface",str(e)])
files={n:b"x" for n in ["index.html","navigation.json","assets/site.css","assets/site.js",".nojekyll","index.html/child","a space.txt"]}
r=dict(schemaVersion=2,kind="release",tag="v1.0.0",sha="a"*40,runId=12,runAttempt=1,files={n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())})
r["snapshotDigest"]=hashlib.sha256(json.dumps(r,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
raw=json.dumps(dict(record=r,files={n:base64.b64encode(b).decode() for n,b in files.items()})).encode()
accepted=verify_snapshot(raw,tag="v1.0.0",sha="a"*40,run_id=12,run_attempt=1)
errors.append(["snapshot file/directory conflict and space accepted",len(accepted["files"])])
ctx=N(api=api,journal=N(records=lambda:[]),policy=N(bootstrap=[N(tag="v1.4.0",version="1.4.0")]))
try:selection(ctx)
except ControllerError as e: errors.append(["adopted stable without controller journal",e.code])
record=N(state="complete",published=True)
calls=[]
with patch("cg_release.profile_docs.docs_step",side_effect=lambda *a:calls.append("docs")):
 advance(N(policy=N(gpid_profile="v1")),record)
errors.append(["complete refresh hook calls",calls])
errors.append(["complete without verified hooks returns cached record",finish_hooks(None,record,required={"docs","evidence"},verified={}) is record])
sys.stdout.write(json.dumps(errors,indent=2)+"\n")
```

### Probe B

```python
import sys, json, importlib.util
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
sys.path[:0]=[str(Path.cwd()/"packages/cg-release/src"),str(Path.cwd()/"scripts")]
import release_profile_gpid as p
from cg_release.publication_remote import GitHubPublicationRemote
from cg_release.profile_docs import selection
from cg_release.journal import digest
rows=[]
api=N(get=lambda endpoint:{"sha":"a"*40,"truncated":False,"tree":[]},releases=lambda:[])
with patch.object(p,"read_blobs",side_effect=lambda api,tree,paths,optional:dict.fromkeys(paths)):
 data=p.source_blobs(api,"a"*40,"v1.1.0")
rows.append(["empty source payload inventory accepted",sorted(data)])
rows.append(["native yaml installed in controller builder environment",importlib.util.find_spec("yaml") is not None])
captured=[]
def runner(*args,**kwargs):
 captured.append(kwargs["max_output_bytes"])
 return N(stdout=b"")
remote=GitHubPublicationRemote(N(runner=runner,host="github.com",slug="example/repo",cwd=Path.cwd(),read_seconds=20,remaining=lambda:20))
remote.download({"id":1,"size":67108865})
rows.append(["download cap for policy-legal 64 MiB plus one byte",captured[0]])
build={"gates":{".github/workflows/release-controller-build.yml":{"run_id":11,"run_attempt":1}}}
inputs={"inventory":[{"name":"release-docs.json","sha256":"c"*64,"size":10}],"build_digest":digest(build)}
receipt={"release_sha":"a"*40,"release_id":12,"assets":{"release-docs.json":13}}
record=N(published=True,request=N(tag="v1.5.0-rc.1",version="1.5.0-rc.1"),evidence={"publication-receipt":receipt,"build-validated-1":build})
ctx=N(api=N(),journal=N(records=lambda:[record]),policy=N(bootstrap=[N(tag="v1.4.0",version="1.4.0")]))
with patch("cg_release.profile_docs.published_inputs",return_value=inputs),patch("cg_release.profile_docs.inspect_publication",return_value={"tag":"verified","release":12}):
 try:selection(ctx)
 except Exception as e:rows.append(["first controller prerelease with verified prior stable bootstrap",e.code])
sys.stdout.write(json.dumps(rows,indent=2)+"\n")
```

### Probe C

```python
import sys, json
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
sys.path[:0]=[str(Path.cwd()/"packages/cg-release/src"),str(Path.cwd()/"packages/cg-release/tests")]
from journal_store import MemoryStore
from cg_release.models import Request
from cg_release.journal import Journal
from cg_release.prepare_stage import checkpoint
from cg_release.recovery import finish_published
from cg_release.events import ControllerError
request=Request(schema_version=1,host="github.com",repository_id=123,repository_slug="example/generic",requester_id=456,nonce="0123456789abcdef0123456789abcdef",proposal_digest="a"*64,source_branch="main",source_sha="b"*40,policy_sha="c"*40,policy_digest="d"*64,line="current",version="1.0.0",tag="v1.0.0",sign=False,override_reason=None,requested_bump=None,requested_channel=None)
journal=Journal(MemoryStore())
record=journal.admit(request)
for operation,state in [("prepare","awaiting-review"),("review","building"),("build","awaiting-approval"),("tag","publishing"),("publication-receipt","published")]:
 record=checkpoint(journal,record,operation,{"release_sha":"b"*40},state)
ctx=N(api=N(),policy=N(enabled=True,gpid_profile=None),journal=journal)
with patch("cg_release.published_history.published_inputs",return_value={}),patch("cg_release.publication_reconcile.inspect_publication",return_value={"tag":"verified","release":1}):
 result=finish_published(ctx,record)
sys.stdout.write(json.dumps({"current_profile":None,"sealed_policy_digest":request.policy_digest,"result":result.state,"publication_hooks":result.evidence["publication-hooks"]})+"\n")
```

### Probe D

```python
import sys, json
from pathlib import Path
from types import SimpleNamespace as N
sys.path.insert(0,str(Path.cwd()/"packages/cg-release/src"))
from cg_release.journal_rules import retained_evidence
from cg_release.journal import digest
from cg_release.events import ControllerError
class R:
 def __init__(self):self.evidence={"publication-hooks":{"docs":{},"evidence":{}}}
 def model_dump(self,**kwargs):return {"request_id":"rc1."+"a"*450,"evidence":self.evidence}
r=R()
snapshot={"tag":"v1.0.0","sha":"a"*40,"release_id":1,"asset_id":2,"sha256":"a"*64,"size":1024,"run_id":12,"run_attempt":1}
for n in range(1,101):
 sealed={"releases":[snapshot],"stable_tag":"v1.0.0","dev_sha":format(n,"040x"),"controller_sha":"b"*40,"controller_ref":"main","workflow_path":".github/workflows/release-controller-docs.yml","repository_id":123,"nonce":format(n,"032x"),"repair_attempts":0}
 parts={"request":sealed,"dispatch":{"ref":"main","inputs":{"request_id":"rc1."+"a"*450,"nonce":sealed["nonce"]}},"registration":{"run_id":100+n,"request_digest":digest(sealed)},"composition":{"request_digest":digest(sealed),"manifest_sha256":"c"*64,"run_id":100+n,"dev_sha":sealed["dev_sha"],"stable_tag":"v1.0.0"}}
 try:
  for stage,value in parts.items():r.evidence=retained_evidence(r,f"profile-docs-{stage}-{n}",digest(value),value)
 except ControllerError as e:
  sys.stdout.write(json.dumps({"refresh_number":n,"stage":stage,"error":e.code,"prior_events":len(r.evidence)})+"\n")
  break
```

### Failed Adversarial Invocation

This command stopped with `SyntaxError: '(' was never closed` before probe
behavior. It is not a product failure or verification result.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & "packages/cg-release/.venv/Scripts/python.exe" -B -I -c 'import sys, json, base64, hashlib; from pathlib import Path; from types import SimpleNamespace as N; from unittest.mock import patch; sys.path[:0] = [str(Path.cwd()/"packages/cg-release/src"),str(Path.cwd()/"scripts")]; import release_profile_gpid as p; from cg_release.github import GitHubReads; from cg_release.events import ControllerError; from cg_release.profile_snapshot import verify_snapshot; from cg_release.profile_docs import docs_step, selection; from cg_release.journal import digest; from cg_release.stage_router import advance; from cg_release.recovery import finish_hooks; api=GitHubReads("github.com","example/repo",cwd=Path.cwd(),runner=lambda *a,**k: (_ for _ in ()).throw(AssertionError("Network forbidden"))); errors=[]
for name, action in [("profile source query",lambda:p.source_blobs(api,"a"*40,"v1.0.0")),("docs deployment query",lambda:api.pages("deployments?environment=github-pages"))]:
 try: action()
 except ControllerError as e: errors.append([name,e.code])
with patch.object(api,"get",return_value={"sha":"a"*40,"truncated":False,"tree":[]}):
 try:p.source_blobs(api,"a"*40,"v1.0.0")
 except AttributeError as e: errors.append(["profile releases interface",str(e)])
files={n:b"x" for n in ["index.html","navigation.json","assets/site.css","assets/site.js",".nojekyll","index.html/child","a space.txt"]}; r=dict(schemaVersion=2,kind="release",tag="v1.0.0",sha="a"*40,runId=12,runAttempt=1,files={n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}); r["snapshotDigest"]=hashlib.sha256(json.dumps(r,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(); raw=json.dumps(dict(record=r,files={n:base64.b64encode(b).decode() for n,b in files.items()})).encode(); accepted=verify_snapshot(raw,tag="v1.0.0",sha="a"*40,run_id=12,run_attempt=1); errors.append(["snapshot file/directory conflict and space accepted",len(accepted["files"])])
ctx=N(api=api,journal=N(records=lambda:[]),policy=N(bootstrap=[N(tag="v1.4.0",version="1.4.0")]));
try:selection(ctx)
except ControllerError as e: errors.append(["adopted stable without controller journal",e.code])
record=N(state="complete",published=True); calls=[]
with patch("cg_release.profile_docs.docs_step",side_effect=lambda *a:calls.append("docs")):
 advance(N(policy=N(gpid_profile="v1")),record)
errors.append(["complete refresh hook calls",calls]); errors.append(["complete without verified hooks returns cached record",finish_hooks(None,record,required={"docs","evidence"},verified={}) is record]); sys.stdout.write(json.dumps(errors,indent=2)+"\n")'
```

### Failed Architecture Invocation

This invocation produced a PowerShell quoting warning and no usable probe result.

```powershell
& ".\packages\cg-release\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, 'scripts'); from pathlib import Path; from cg_release.github import GitHubReads; from cg_release.events import ControllerError; from cg_release.models import Policy; from cg_release.jsonio import decode_json; import release_profile_gpid as profile; calls=[]; api=GitHubReads('github.com','example/gpid',cwd=Path('.'),runner=lambda *a,**k: calls.append(a)); probes=[('profile source read', lambda: profile.source_blobs(api,'a'*40,'v1.5.0-rc.1')),('Pages filtered inventory',lambda: api.pages('deployments?environment=github-pages')),('4MiB snapshot envelope decoder',lambda: decode_json('{\"x\":\"'+'a'*4194304+'\"}'))]; results=[]; [(results.append((name,fn())) ) for name,fn in []]; exec('for name,fn in probes:\n try:\n  fn()\n  results.append((name,\"unexpected-pass\"))\n except ControllerError as error:\n  results.append((name,error.code))'); results.append(('GitHubReads.releases exists',hasattr(api,'releases'))); results.append(('Policy.retry_budget exists','retry_budget' in Policy.model_fields)); results.append(('transport calls',len(calls))); sys.stdout.write(repr(results)+'\n')"
```

### Failed Testing Invocation

This invocation stopped with `SyntaxError: unterminated string literal (detected
at line 1)`. Its literal backslash/quote sequences are retained; no probe code ran.

```powershell
& ".\packages\cg-release\.venv\Scripts\python.exe" -B -c "import sys,json; from pathlib import Path; from types import SimpleNamespace; sys.path.insert(0,'scripts'); import release_profile_gpid as p; from cg_release.github import GitHubReads; api=GitHubReads('github.com','example/offline',cwd=Path('.'),runner=lambda *a,**k: (_ for _ in ()).throw(AssertionError('I/O forbidden'))); results={}; cases={'source_provider':lambda:p.source_blobs(api,'a'*40,'v1.0.0'),'docs_provider':lambda:api.pages('deployments?environment=github-pages')}; [(results.update({name:'unexpected success'}) if call() else None) for name,call in []]; code='for name,call in cases.items():\n try: call(); results[name]=\"unexpected success\"\n except Exception as error: results[name]=type(error).__name__+\":\"+getattr(error,\"code\",str(error))'; exec(code); api.get=lambda endpoint:{'sha':'a'*40,'truncated':False,'tree':[]}; code='try: p.source_blobs(api,\"a\"*40,\"v1.0.0\")\nexcept Exception as error: results[\"source_after_endpoint_fix\"]=type(error).__name__+\":\"+str(error)'; exec(code); sys.stdout.write(json.dumps(results))"
```
