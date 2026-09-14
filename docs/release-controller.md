# Release Controller

## Current Scope

The standalone `cg-release` package provides deterministic `plan`, `start`,
`status`, and `resume`. The five `/cg-release` interfaces pass arguments unchanged
to that core. Generic mode does not load a Compound GPID charter or profile.

The publisher remains disabled in the supplied installation. Decision
`D-2026-09-13-defer-live-rollout` permits local implementation, offline checks,
documentation, reviews and the ordinary PR pipeline. Bridge delivery, actual
Windows/native Unix clean-client qualification, registered release-mode CI,
sandbox/security trials and live timing proof are **deferred, not passed**.
Local fixture success is not live readiness. Ordinary PR CI is not deferred.
The committed exact-input gate remains after the separately authorized pipeline
step 11 commit; prepare-mode output cannot replace it. Whole-plan V8 stays pending
until that gate and ordinary required PR checks pass.

## Installation

Use Python 3.11 or later, Git, `gh`, and `uv` for the standalone package. Authenticate
`gh` through its normal secure credential store; never put credentials in command
arguments, URLs, trial records or the journal. Source-free wheel installation uses
the controller's locked dependency export and `--link-mode copy`. See the
[package installation instructions](https://github.com/GPID-WB/compound-gpid/blob/5e879e2d573515b6baa9797ef7418afb2177af55/packages/cg-release/README.md)
at the reviewed source revision.

From the reviewed controller source checkout:

```text
uv sync --project packages/cg-release --locked --python 3.12
uv run --project packages/cg-release cg-release --help
uv build --project packages/cg-release
```

The GPID `bin/cg-release` and `bin/cg-release.cmd` launchers select the package
environment when present, otherwise the installed Python module. They use
`python -I -m cg_release.cli`, not a recursive PATH lookup for `cg-release`.
Install the wheel into that selected interpreter for isolated `-I` invocation.
Node is needed only for GPID documentation hooks; PowerShell is needed only for
GPID legacy tooling and Windows qualification. The ordinary CI matrix targets
Python 3.11/3.12 on Windows, Linux and macOS. This matrix definition is not proof
that all six hosts passed for the current candidate.

## Commands

These examples are syntax-tested, not authorization to submit against a remote
repository. Run them only after the reviewed setup and explicit operation approval.
Use the installed CLI as `cg-release` for a generic project. The slash form below
uses the same core; profile selection comes from trusted policy, not the slash name.
Replace `REQUEST_ID` with the full saved `rc1.` locator before status or resume.

<!-- cg-release:examples -->
```text
/cg-release plan --version 1.0.0 --branch main --line current --json
/cg-release start --version 1.0.0 --branch main --line current --yes --json
/cg-release status REQUEST_ID --json
/cg-release resume REQUEST_ID --json
```

| Command | Meaning |
|---|---|
| `plan` | Reads exact source and protected default-branch policy; calculates proposed edits. No issue, reservation, PR, fetch into the caller checkout, or metadata write. |
| `start` | Recomputes without a prior plan; confirms and rechecks exact inputs. Emits a portable provisional locator before the first issue write, then a verified receipt or explicit error. |
| `status` | Reads remote inbox/journal state. `--watch --timeout 10m` observes within a bound; timeout/Ctrl+C does not cancel the release. |
| `resume` | Resolves the same locator, rechecks current authority and dispatches trusted reconciliation. It is not unconditional replay. |

`--bump major|minor|patch|prerelease` and `--version` are mutually exclusive.
`--channel rc` is an automatic-bump input only. `--branch` selects a remote branch
in the same repository, never a fork; detached HEAD needs it explicitly. `--line`
resolves an otherwise ambiguous release line. `--sign` requires the configured
allowlisted signing identity. A stable branch exception uses
`--allow-non-deployment-branch --reason "Reviewed reason"`, requires current
maintain/admin authority, and still waits for protected `release-override` approval.
`--yes` only supplies CLI confirmation. It does not approve changed inputs or GitHub
publication. The optional scanner supplies editorial notes, never version authority.

## Trusted Setup

Setup is a separate maintainer operation, not performed by local tests or this guide.
Copying templates does not configure a secure repository. Retain the setup PR and
exact setting evidence, then review enablement separately after rollout proof.

1. Select explicit repository numeric ID, host/URL and source branches. Enable Issues. Read the protected remote default branch at an exact SHA; only its `.release-controller.json` is authoritative. The source checkout's copy is data, not authority.
2. Prepare a reviewed setup PR from `packages/cg-release/templates/`. Replace every example ID, journal root, controller revision, wheel URL/digest, artifact filename and placeholder. Keep policy `enabled: false` and workflow false guards until the later reviewed sandbox/enablement operation. `123` and repeated hexadecimal digits are fixture values, not this repository's IDs.
3. Declare one managed release identity, lines/core bounds, audited history/bootstrap, exact metadata/changelog adapters, build argv/cwd/lock paths, artifact names/count/size bounds, required check producer/workflow identities, signing fingerprints and timeouts. Fail on unknown fields, duplicate JSON keys, unsupported formats or incomplete controls.
4. Pin the trusted controller source and wheel digest, all external Actions, and the locked toolchain. Privileged jobs install only the verified wheel and never execute source scripts. Source builds check out the registered release SHA on separate fresh read-only runners, without privileged caches, signing, control or publishing credentials.
5. Create the non-code `release-controller-state` branch with its audited genesis. Rulesets must deny deletion/force-push and restrict journal updates to the control App. Protect published release tags against updates/deletion. The control App cannot create protected release tags; the publishing App cannot update the journal.
6. Configure `release-control`, `release-publish` and `release-override` with exact trusted-default-ref restrictions. Publication environments require independent reviewers, prevent self-review and disallow admin bypass. Put App credentials in these environments, never unrestricted repository secrets. Verify repository-plan support; unavailable or ambiguous settings fail closed.
7. Verify the actual App scopes and cross-role denials in the authorized sandbox. Names do not enforce the boundary. Keep the exact settings, denied-operation responses, workflow/run/attempt and reviewer identities as evidence. Ordinary PR jobs need no control/publishing secrets.

| Role | Minimum Operation Set | Credential Boundary |
|---|---|---|
| Control App | Contents/journal, Issues, preparation/evidence PRs, Actions dispatch; read checks, administration, environment and secret metadata as validated by policy | `release-control`; no protected tag creation or code-review bypass |
| Publishing App | Exact tag, draft Release, declared assets and publication; workflow-file permission when required by the target commit | Only protected publish/override jobs; no journal updates |
| Publisher journal client | Control App journal intents/checkpoints in the protected publishing job | Separate token from publication operations; never job outputs or source jobs |
| GPID Pages control/deploy | Read-only control validation plus required Pages/deployment access | Protected default-ref `github-pages`; no publishing App key; independent delayed authority check |
| Source build | Read-only source checkout and artifact upload capability | No privileged environment; `persist-credentials: false`; no privileged source execution |

Templates declare the exact token permission requests. Review these against the
installed Apps and target policy; unsupported capabilities are a hard stop. There
is no general installer that can safely infer settings or grant missing authority.

## Versions and Metadata

Use strict SemVer with numeric identifier precedence: `rc.9 < rc.10 < stable`.
Build metadata does not create a new collision identity. Adopt only verified
published non-draft Releases into a reviewed line history. Missing baseline needs
an explicit initial version or audited bootstrap, not nearest-tag inference.
Legacy four-part tags remain distinct historical identities; never rename them
into SemVer suffixes. One maintenance line can issue a patch beside a newer major.
Pre-releases and older maintenance stables must not replace the highest stable
latest selection. Select latest by SemVer policy, not creation time or string sort.

| Adapter | Supported Representation |
|---|---|
| JSON | Declared JSON Pointer string with exact SemVer; preserve unrelated fields |
| Python TOML | Static `[project].version`; stable unchanged, `alpha.N -> aN`, `beta.N -> bN`, `rc.N -> rcN`, `dev.N -> .devN` |
| R DESCRIPTION | Stable `Version` only; no invented prerelease projection |
| Changelog | One explicit Markdown insertion marker with deterministic reviewed notes |
| Release manifest | Canonical version, tag, request, source SHA, policy digest, line, projections and declared outputs; no self-referential release SHA |

For every Python distribution/line, both canonical SemVer and PEP 440 projected
history must increase. `beta.1 -> dev.1` increases in SemVer but decreases in
PEP 440 and is rejected. Dynamic versions, arbitrary Python channels, compound
suffixes and build metadata are unsupported. Paths must be bounded declared
regular files; symlinks, reparse escapes, hardlink aliases, traversal and case
collisions are rejected before preparation writes. A moved base needs a new
confirmed request, not an automatic rebase.

## Progress and Approval

Output under `--json` is JSON Lines. Persist the pre-write `submission-intent`
locator before waiting for the next event. It is portable and not a credential.
A verified `receipt` means queued durable submission with admission still pending.
Exit 0 means the CLI operation succeeded, not publication or workflow completion.
Errors use exit 2, a bounded code and safe next action; diagnostics use stderr.

State progresses through `queued -> awaiting-review -> building ->
awaiting-approval -> publishing -> published -> complete`. `failed` retains the
failed step and last verified checkpoint. The journal distinguishes a published
Release from verified completion of required hooks. A five-minute scan supplies
recovery wakeups, not a queue-latency guarantee; bounded workers persist progress
instead of waiting in chat for human review.

Before approval, a separate trusted job seals exact inputs and exposes an immutable
journal-commit/blob URL in its completed summary and deployment environment URL.
One publication run, attempt 1, owns one seal. A rerun is rejected; recovery gets a
new run, seal and approval. At least one allowed reviewer must differ from the
original requester and every recovery reconfirmer. App dispatch does not make the
requester independent. Policy/source/authority drift invalidates the first tag write.

The trusted controller workflow SHA is not the source build SHA. Release CI binds
the sealed request, dispatch nonce, registered source SHA, actual run/attempt,
workflow revision, six Python/OS cells, Ruff and stable aggregate. Source-written
claims and same-name PR checks cannot satisfy that gate. Exact-input evidence reuse
also binds tree, policy/controller/check identities, argv, lock digests, toolchain
and profile version. Changed or expired evidence is not a cache hit.

## Recovery and Retention

Use `status REQUEST_ID` on another authenticated machine without a local request
file. `resume REQUEST_ID` resolves the same identity and checks fresh authority.
After an unknown issue-create response, do not repeat `start`: unresolved absence
is not permission to submit twice. Retain every error and provisional locator.

| Observed Boundary | Safe Action |
|---|---|
| Issue write unknown | Read/discover exact author, nonce, digest and journal mapping; remain unknown if ambiguous |
| Preparation PR pending | Wait for review and exact resulting tree; never auto-merge or include unrelated edits |
| Artifact expired before publication | Rebuild exact source in isolation and obtain fresh approval; no fabricated cache hit |
| Matching tag, no/draft Release | Freeze exact tag bytes/peeled SHA; verify source lineage and current authority; fresh recovery seal/approval completes only missing writes |
| Source advanced after tag | Preserve tag identity; ordinary forward ancestry can be recovered. Deleted/rewritten branch or changed policy requires explicit reviewed maintainer recovery |
| Published asset differs | Stop for inspected conflict; never overwrite bytes, clobber assets, move or delete a published tag |
| Owner appears stale | Require terminal-run proof, expired/revoked credentials and reconciled effects; elapsed time alone is insufficient |
| Required GPID hook failed | Keep `published`, retry only missing docs/evidence work under retained authority; do not retag |

Keep the journal's per-request records, hash-chained events, policy snapshots,
source/release SHAs, run/job/attempt IDs, approvals, exact public tag bytes,
artifact inventories/digests and hook results for the repository lifetime.
Do not store secrets, build trees, binary assets or unbounded logs in it.

Backup is a maintainer-controlled read-only Git mirror of the state branch and
its full history, plus separately retained artifact/provenance records. Record
the observed head, audited root and backup digest; verify them on a second copy.
For restoration, stop writers and obtain explicit recovery approval first. Validate
the root, author identities, complete parent/event chains, reservations and remote
effects against the mirror. Restore only through an approved non-force continuation
that preserves current history. A divergent/re-written branch needs inspected
maintainer recovery; never reset it to the backup. No automatic restore/compaction
command is provided. Missing required evidence cannot be restored from chat.
After publication, verified Release assets provide durable bytes; before publication,
expired Actions artifacts require a fresh build and approval.

## GPID Migration

Deliver a reviewed legacy-format bridge through the old accepted updater channel
before enabling the new writer. Retain published tag/Release ID, trusted revision,
commit/tree/tag-object IDs and previous/bridge/successor archive digests. Execute
the actual previous updater -> delivered bridge -> new-format pin sequence on
clean Windows and native Unix hosts. Synthetic fixtures and Git Bash link copies
are not these receipts. The disabled bridge workflow requires explicit real-bridge
authorization and fresh maintainer authority; `verify_bridge` rereads exact run,
job, artifact and receipt identities remotely.

The GPID launcher exposes `--legacy-bridge` and `--legacy-recovery` only for separate
authorized operations. It supplies `-LegacyOperation Bridge` or `Recovery` to
`create-release.ps1`; normal checks still apply. Bridge is refused after cutover.
Recovery requires an existing stranded identity or reviewed historical recovery
record and cannot create routine new releases. `/cg-devtag` remains separate
temporary four-part tooling, never a new-format controller baseline. No cleanup of
published objects is part of migration.

GPID prepares reviewed immutable payloads before the tag; `latest.json` has matching
bytes. Its preparation-time `publishedAt` is not proof of publication. Every prior
durable payload needs a published Release before later preparation. Post-tag
attestation is a separate reviewed evidence PR and never moves the release tag.

Immutable docs build from the exact release SHA. The trusted composer combines
verified static Release assets with a separate mutable `dev` snapshot under the
shared Pages guard. Versioned `/releases/<tag>/` cannot overwrite `/dev/`; only the
highest stable selection supplies the root. Advancing `dev` refreshes composition,
not release assets or approval. Failed composition leaves `published`, not `complete`.

## Deferred Trial Procedure

The harness is offline by default. It never discovers a live target from `origin`,
dispatches a workflow or enables a publisher. To inspect a synthetic trial checklist:

```text
uv run --project packages/cg-release python scripts/benchmark_release.py --sandbox-config packages/cg-release/tests/fixtures/sandbox.example.json --repository-id 123
```

This explicit ID is a planning allowlist only; `authorization_verified` stays false.
The strict config accepts only schema version, numeric repository ID, GitHub URL,
`generic` or `gpid` profile, and an authorization-reference label. Change the example
to separately approved exact IDs/URL for a future plan, not for automatic execution.
The file contains no credentials or runnable operations. `--output NEW_FILE` uses
exclusive creation and does not overwrite historical evidence.

Future live execution is an explicit opt-in maintainer procedure, not a hidden
pytest marker or an implemented unattended sandbox driver. Approve exact generic
and GPID repository IDs/URLs, allowed setup/release/fault operations and retention
rules. Install reviewed disabled templates, prove settings and bridge prerequisites,
then separately authorize the sandbox workflow activation. Exercise every case
listed by the generic and GPID checklists: preview/versions, override/signing/latest,
App denials/hostile source, pre-approval visibility/independent reviewers, exact
publication, concurrency/dropped wakeup/lost responses, second-machine recovery,
expiry/restore/branch advancement, native hosts, final-SHA CI and post-hooks/dev
composition. Retain exact argv/exit and every remote identity. No unexecuted case
is passed and no production activation or automatic tag/asset cleanup is permitted.

Collect at least ten **sequential warm-dependency** `start` attempts from proposal
computation to verified durable receipt. Exclude only human confirmation time.
Keep outages and all failed/blocked/unknown attempts. Record min/median/nearest-rank
p95, environment, dependency versions, history size, request/receipt IDs, all
failures and separate queue/review/approval/build/publication/recovery intervals.
The target remains p95 <=120 seconds; local Git timings do not establish it.
A missing comparable legacy baseline is not zero and forbids a speedup claim.

The harness can check supplied measurement arithmetic without granting evidence:

```text
uv run --project packages/cg-release python scripts/benchmark_release.py --sandbox-config sandbox.json --repository-id 123 --measurements measurements.json
```

Measurement schema v1 contains `repository_id`, `environment` (`python`, `platform`,
`history_size`), `warm_dependencies`, `sequential`, `samples` and `intervals`.
Each sample has nonnegative finite `total_seconds`, `confirmation_seconds`,
`outcome` (`receipt`, `failed`, `blocked`, `unknown`) and `error_code` (null for receipt,
otherwise a bounded `E_...` code). Confirmation cannot exceed total. All six interval
keys above must exist, with a nonnegative duration or null for missing evidence.
Keep detailed dependency identities and raw receipt/run/argv evidence separately.
Input is limited to 64 KiB with no duplicate/unknown keys. The output retains every
sample and failure, uses nearest-rank p95, and always sets `live_handoff_passed: false`.
`within_target_from_supplied_data` is arithmetic only. Independently verify the
underlying remote receipts and complete workload before accepting live performance.

## Error Actions

| Code or Family | Action |
|---|---|
| `E_ARGUMENT`, `E_BENCHMARK_INPUT` | Fix schema/argv from `--help`; do not put secrets in input or retry remote operations |
| `E_BENCHMARK_OUTPUT` | Report serialization or output creation/write failed; exit 2 with a bounded JSON error. Select a new writable output path; inspect local measurements if the error persists. Existing files are never overwritten. |
| `E_DISABLED`, `E_SUBMISSION_UNAVAILABLE` | Installation is disabled or incomplete. Obtain separate reviewed setup/enablement; do not flip a guard to get past the error |
| `E_REPOSITORY`, `E_DETACHED`, `E_LINE`, `E_BRANCH`, `E_OVERRIDE` | Resolve exact target, explicit branch/line and permitted authority; no fork or guessed baseline |
| `E_POLICY`, `E_POLICY_TRUST`, `E_CONTROLLER_TRUST`, `E_PROTECTIONS`, `E_AUTHORITY` | Stop; inspect trusted setup, current actor and real controls. A local policy edit or `--yes` cannot fix authority |
| `E_STALE_PROPOSAL`, `E_STALE_POLICY`, `E_COLLISION`, `E_HISTORY` | Inspect changed inputs/managed history; require a fresh confirmed request when appropriate, preserving existing reservations and tags |
| `E_SUBMISSION_UNKNOWN`, `E_DISPATCH_UNKNOWN`, `E_DEADLINE` | Keep locator and exact error; inspect remote state before retry. Timeout is not absence or cancellation |
| Journal, owner, approval, signing, build, artifact, profile or publication errors | Follow the reported checkpoint/expected/observed state and safe next action. Stop on identity conflict; use inspected recovery, never destructive rollback |
| `E_PROCESS`, `E_RESPONSE` or unavailable API evidence | Check runtime/authentication and bounded diagnostics. Do not interpret a 403/404 or malformed response as an absent Release |

## Local and Final Gates

```text
uv run --project packages/cg-release pytest packages/cg-release/tests -q
uv run --project packages/cg-release ruff check packages/cg-release
uv build --project packages/cg-release
python scripts/release_profile_install.py --check
python scripts/cg_generate_targets.py --all --dry-run
node scripts/generate-whats-new.js --validate-release-set
node scripts/rebuild-docs.js --all --check
node scripts/check-docs-site.js
```

Regenerate canonical-derived outputs before review, not after it. Run affected
Python/Node regression suites and the unfiltered `. tests\Run-Tests.ps1` through
a dedicated safe Pester child. Record skipped hosts, symlink limitations and
cleanup errors; zero failed assertions does not establish successful cleanup.
Only after the planned authorized candidate commit, run
`python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target`.
Ordinary PR CI must include all six package cells and `release-controller-ci`.
Release-mode source-bound CI remains a distinct deferred rollout gate.
