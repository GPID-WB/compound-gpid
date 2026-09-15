# Release Controller Integration

## Disabled Installation

The standalone controller owns `plan`, `start`, `status` and `resume`. The five
slash interfaces call that same installed CLI with unchanged arguments. Generic
mode does not load a GPID charter or optional profile module. The GPID launcher
calls `python -I -m cg_release.cli`, not the executable name, so a PATH wrapper
cannot recurse into itself. Python 3.11 or later is required only for this package.

`.release-controller.json` and the four `release-controller*.yml` installations
are disabled. Their unresolved repository, App, journal and controller identities
are null or explicit placeholders. They are not usable authority. A reviewed
setup must supply real identities, declared metadata and changelog files, bridge
evidence, protected environments and immutable installation pins. Never infer
these values from a local source checkout. A valid policy on the protected remote
default branch is the only authority. `enabled: true` alone cannot satisfy it.

`python scripts/release_profile_install.py --check` checks the disabled source
installations. Running it without `--check` regenerates those disabled files only;
it does not change GitHub settings or secrets. Do not use it to overwrite a
separately reviewed active installation after cutover.

## Optional Profile

The pinned wheel bundles the canonical `scripts/release_profile_gpid.py` as a
separate optional module. Core generic mode never imports it. The typed hook
boundary checks stage, exact release SHA, remote identity and evidence digest.
Only trusted installed code runs in a control job. Source hooks run in separate
unprivileged jobs, with no control, publication or signing credential.

The GPID profile declares `releases/<tag>.json` and `releases/latest.json` edits.
Their notes are bound to the confirmed commit inventory. Both payload files have
identical bytes before the preparation PR review. `publishedAt` is the durable
submission receipt timestamp used for preparation metadata, not a claim that
publication already happened. Existing historical payloads are never rewritten.
Every prior durable payload must have a published GitHub Release before another
preparation can start.

The profile requires the registered six-cell `release-controller-ci` workflow and
the `gpid-native-profile` job from the registered build workflow. PR-only evidence,
same-name check runs from another producer, and skipped cells cannot pass. Native
preflight, generated-target checks and immutable docs build run at the bound
release SHA. Their snapshot bytes and exact run identity are checked before
approval. There is one authoritative release-docs artifact producer.

The source job creates a separate `gpid-native` environment with `uv sync --locked
--group gpid-native --no-install-project` against the exact source lock. The
non-default dependency group includes pinned PyYAML; it is not a core runtime
dependency. `CG_RELEASE_NATIVE_PYTHON` identifies that interpreter. The pinned
build worker keeps its own interpreter and selects the native interpreter through
PATH for the declared profile builder. The builder rejects a different interpreter.
`--check-environment` checks this boundary without building or writing evidence.

Both `uv.lock` and `pyproject.toml` digests enter the sealed build ticket. The
required `native-environment.json` artifact records the lock digest, Python and
installed dependency versions, native gate owner, source SHA and run/attempt. The
approval verifier reads the exact source lock and checks this receipt before
approval. Its 64 KiB limit is separate from the unchanged 64 MiB snapshot envelope.
The native/profile producer runs native/profile checks and docs only. It does not
repeat package pytest, Ruff or distribution builds owned by the separate required
six-cell producer. Local preflight retains the full gate by default; the explicit
`--gate-owner gpid-native-profile` route cannot replace either registered identity.

## Publication Completion

The post-tag attestation is prepared only after the remote tag and published
Release have been reconciled. A separate control-App PR writes the immutable
attestation. Its head, final tree, reviewer identities, checks and committed bytes
must be remotely verified. The evidence PR never moves or recreates a release tag.

The documentation builder uses only the exact release SHA. It does not check out
live `dev`. The trusted composer reads approved Release assets as static data and
a separately registered, unprivileged dev snapshot. It records both source/run
identities and the final file inventory. Release snapshots live under
`/releases/<tag>/` and cannot replace `/dev/`. Only the highest stable selection
can supply the default root site. A first GPID pre-release needs a previously
published stable snapshot; an unavailable stable selection fails closed.

All deploy producers share `concurrency.group: pages` with cancellation disabled.
Legacy `pages.yml` executes dev scripts only in an unprivileged artifact build.
The protected-default `release-pages.yml` controller verifies the exact run,
archive digest, source fingerprint and full file inventory, then composes static
data. It never executes scripts from the downloaded artifact or dev checkout.
The legacy main/dev workflows remain unchanged in purpose while the policy is
disabled. After cutover they refuse legacy deployment. The controller's bounded
scheduled scan refreshes mutable composition, including for an already complete
release, without rebuilding or changing its immutable release assets. The stable
release owns shared composition so different requests do not build duplicate
sites for the same desired input identity. Development advancement retries only
composition; it does not invalidate publication approval.

`published` remains distinct from `complete`. Missing or failed documentation or
evidence proof leaves the release published. Source-written `verified: true`, chat
memory and successful local fixtures are not remote completion evidence.

## Compatibility Bridge

The bridge must use the old stable/four-part grammar. Enablement requires its
published Release ID, exact annotated tag commit, trusted workflow/producer and
separate successful `bridge-clean-client-windows` and `bridge-clean-client-unix`
run identities. These are re-read remotely. A local bridge fixture is not delivery.
The disabled `release-controller-bridge.yml` has a distinct real qualification
path. It does not select synthetic reader tests. Its explicit `qualification`
input is a strict `BridgeSpec`: repository ID/slug and `previous`, `bridge`, and
`successor` records, each with tag, Release ID, revision, annotated tag-object ID
and tree. Previous/bridge use legacy grammar; successor is a new SemVer pre-release.
All IDs remain unresolved in source policy. A reviewed external V6 operation must
authorize each native platform run at the published bridge revision.

`cg_release.bridge_qualifier` requires `--authorize-real-bridge`, exact Actions
source/run identity and fresh maintainer authority. It re-reads all three published
distributions, clones into a new private directory, runs the actual previous
updater to install the bridge, then runs the updated reader to select the new pin.
It uses complete delivered helpers and dependencies, real Copilot/OpenCode links,
managed-copy refresh and normal link continuation. Its own updater calls do not
set `CG_INTERNAL_CALL` or `CG_SKIP_UPDATE`; normal internal link behavior is kept.
The PowerShell profile cleanup path is confined to the private home. A native Unix
run is required; Git Bash directory-copy link emulation does not prove that gate.

Qualification emits one `qualification.json` with exact installed-tree/content,
managed-file, link and pin evidence. Reviewed policy records distinct Windows/Unix
run IDs, job IDs, artifact IDs and archive SHA-256 digests. `verify_bridge` reads
those exact successful workflow/jobs/qualifier steps and artifacts, then compares
the complete receipt with fresh remote distributions. A successful arbitrary
fixture job, XML report, expired artifact, changed bytes or merely similar name
cannot qualify. The source workflow remains explicitly disabled. The separate
synthetic reader fixtures retain their original `source.json` hashes and exact
`-text` checkout attributes; they never count as delivered bridge evidence.

`--legacy-bridge` and `--legacy-recovery` are explicit GPID-only paths. Every
legacy script call must pass `-LegacyOperation Bridge` or `Recovery` and retain
all existing permission, branch, payload, tag and docs checks. Bridge is rejected
after cutover. These checks read the exact protected remote default policy and
current maintainer authority again before each effect, never local policy or an
assumed `main` policy. Historical recovery requires an existing exact stranded
tag or a reviewed `.github/release-recovery/<tag>.json` historical identity.
Routine new publication through Recovery is forbidden.

Missing historical Pages evidence can use the manual `release-pages.yml` producer
with an exact `build_run_id`. The protected-default reviewed recovery record must
bind `schema_version: 1`, `repository_id`, `tag`, `tag_object`, `release_sha`,
`actor_ids`, `reason`, `build_run_id`, `artifact_id`, and `artifact_digest`.
The producer and Finalize verify those identities, and Finalize requires the exact
manual `PagesRunId`. The old lineage, latest-payload and current-dev guards remain:
expired artifacts or stale content block this route. No tag, artifact or payload
rewrite is a supported recovery. Existing valid deployment evidence still works.
The manual producer requires the protected Pages control-App credential with
read-only repository, Actions and administration permissions to verify review
protections. Normal pre-cutover deployments need no new App credential: their
existing token reads the protected default branch and exact cutover policy bytes.

Required completion hooks come from the immutable approved build tickets. A
current profile removal cannot waive them, including during maintainer recovery.
Composition tickets carry `authority_actor_id` and `policy_digest`. Registration,
composition and the read-only `authorize-deploy` worker recheck the original
requester and applicable resumer, or the exact current maintainer recovery grant.
Scheduled maintenance uses that request authority until a reviewed recovery grant
replaces it; an App dispatch never supplies human authority by itself. The final
gate runs after the Pages environment delay and artifact upload. The disabled
installation requires separately reviewed read-only control-App credentials in
the protected default-ref `github-pages` environment for that gate.
GPID control validation requires reviewers, prevents self-review and admin bypass,
allows only the exact default branch, and rejects publishing-App keys in this
Pages environment. These are setup requirements, not live settings changed here.
`/cg-devtag` remains separate temporary four-part tooling; it cannot create managed
SemVer pre-release identities or select a controller baseline. The release scanner
can supply optional editorial text but cannot decide version, approval or completion.

## Profile Interfaces

The profile returns raw `HookResult` dictionaries, which the generic controller
validates. `source_blobs(api, tree, tag, default_tree=...)` reads both exact trees.
Dedicated provider operations are `tree(sha, recursive=True)`, `pages("releases")`,
`deployments("github-pages")`, and `composition_runs(workflow, since=epoch)`.
General endpoint
input does not accept query strings. The installed profile exposes
`verify_bridge`, `verify_snapshot`, and `resource(name)` explicitly; consumers
must not derive resource paths from `__file__`.

`resource(name)` returns only the absolute regular installed file for the fixed
Node resource set. It checks every member against the pinned wheel's SHA-256
RECORD before returning any member. Missing/aliased/modified resources raise
`E_PROFILE_RESOURCE`; there is no source-checkout fallback. Wheel builds from an
sdist require its complete bundled `profile/` set, even if surrounding `scripts/`
exists. Repository builds may use canonical scripts only after the exact
`packages/cg-release` layout and repository markers are verified. Generic mode
does not import the optional module or require these resources. For example,
`selected_profile(policy).resource('docs-snapshots.js')` is a read-only lookup;
the bounded `run_snapshot('import', [input_path, output_path], cwd=scratch)`
creates only an exclusive contained data directory.
Trusted uv wheel installs use `--link-mode copy`: the installed resources must
not remain hard-link aliases of mutable cache files. This requirement does not
weaken resource containment or RECORD verification.

`profile.composition_retries` is a strict integer from 0 through 10, with default
3. A new dev SHA or release selection resets that mutable repair count. A failed
run with unchanged inputs consumes one repair. Registration runs outside the
Pages concurrency queue; only the deploy job uses the shared `pages` group.
Discovery checks the exact workflow, repository, controller SHA/ref, attempt and
`release-docs <nonce>` run title. A lost registration is not success. An active
run remains pending. A terminal run permits replacement. Absent runs require two
complete bounded inventories at least 120 seconds apart, after an initial
120-second propagation window. Incomplete or ambiguous inventories fail closed.
Discovery is limited to runs since ticket creation, with a five-minute clock
margin, not to the first 1,000 runs in the lifetime history. A registered run
removed by retention uses the same absence proof; its old registration stays in
the journal.
Every replacement invalidates the old ticket before a delayed worker can write.

Composition tickets, intents, registration, manifests, and terminal/absence proof
use independent versioned records under `compositions/<digest>.json`. They share
the existing authenticated append-only event chain and expected-head CAS. Each
record and event remains within the unchanged 64 KiB journal bound. A release
contains only one compact `profile-docs-journal` link; refreshes do not expand or
truncate its immutable evidence. Old composition history is retained in full.
Tickets seal `authority_actor_id` and `policy_digest`. Registration, composition,
and the delayed deployment gate recheck both, plus the original requester.

## Snapshot Bounds

Python and JavaScript use the same snapshot path contract. Components use ASCII
characters from `[A-Za-z0-9_.+-]+`. Dot segments, trailing dots, device names,
prototype names, reserved roots, full-directory case aliases, and file/directory
prefix conflicts are forbidden. A snapshot has at most 10,000 files, 10,000
directories including its root, 33 path components, and 255 path characters.
Its decoded files total at most 32 MiB; its UTF-8 envelope is at most 64 MiB.
Duplicate JSON keys, noncanonical base64, wrong registered identities, and digest
changes fail before import creates an output directory. The generic API JSON
decoder retains its separate 4 MiB bound. Export, approval, download, and import
all use the snapshot-specific bounds.

A dev snapshot reserves at most 1,000 files and 1,000 child directories, 32 MiB,
32 path components, and 251 path characters. Approval accounts for stable-root
duplication, every versioned snapshot, and this dev reserve. Final composition
checks the complete directory graph, 10,000-file/directory limit and 512 MiB
deployment byte limit before copying. It never drops a historical path to fit.
The installed Node process runs only the RECORD-digest-verified snapshot helper
and its fixed dependencies. It accepts contained absolute data paths and finite
deadlines up to 120 seconds, bounds both output streams to 64 KiB, and removes
Node preload variables and credentials. Source code is never an argv entry.

## Reviewed History

Adopted stable history can supply immutable documentation through reviewed
`profile.docs_baselines` entries. Each entry binds `tag`, `sha`, `release_id`,
`asset_id`, `sha256`, envelope `size`, `run_id`, and `run_attempt` to one bootstrap
record and an existing published snapshot. This does not regenerate historical
bytes. The highest adopted stable baseline must be available before a first
pre-release or older-line maintenance submission. A first newer stable release
can supply its own root. Missing or conflicting setup fails before submission
and preparation mutations. The complete durable payload set from both protected
default and selected source must have matching published Releases, even when the
selected source is older.

The evidence PR seals exactly nine files: the canonical attestation, four native
shared JSON copies, and four ownership manifests. A fixed installed data
projection validates the exact mapping and historical ownership bytes before PR
creation. It preserves unrelated entries, then uses the native manifest format
and ordering. It does not run repository generator code under control credentials.
The merged tree must contain every exact sealed output, not only the canonical
attestation. Publication, reviewed payload and tag identities stay unchanged
while this declared post-tag PR is reviewed.

No part of this integration authorizes activation, commits, pushes, PR creation,
bridge publication, repository settings, secrets or live sandbox operations.
