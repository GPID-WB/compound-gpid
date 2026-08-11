---
date: 2026-08-06
title: "Execution report — Controlled GitHub Copilot issue-implementation pipeline (v2)"
plan: ".cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md"
run: 1
---

# Execution Report — Copilot issue-implementation pipeline (v2)

## Plan reference

- Plan: `.cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`
- Scope: Phase 1 only — "Stage 0A — Read-only verification" (per invocation:
  `phase1`, no Stage 0B / 1 / later phases).
- Active deviation policy: **ask** (plan value; no runtime override provided).
- Artifact validation preflight: `cg-render-artifact --validate-only
  .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md` →
  exit 0 (passed) before any roadmap/report/active-state/write.

## Run summary

- Run date: 2026-08-06.
- Executed steps: Phase 1 step 1 (read-only verification, evidence report).
- Roadmap status handling: no `roadmap.json` feature carries a `plan` path for
  this plan (verified: 137 features, 0 `github` links, none reference this
  plan), so no roadmap active-status dispatch occurred.
- Phase-1 evidence gate: completed via executed checks (artifact validation +
  the Stage 0A evidence report `.cg-docs/work-reports/2026-08-06-stage-0a-verification.md`).

## Completed steps / phases

- Phase 1 "Stage 0A — Read-only verification" -- completed 2026-08-06.

## Deviations

- None required. The one interactive action (local `gh auth refresh -s
  read:project`) is a plan-mandated step 1 item (credential scope only), not a
  deviation. All repository writes were limited to files permitted by `/cg-work`
  permissions (evidence report, execution report, plan frontmatter metadata,
  active-state).

## Accepted exceptions

- **E1 (evidence V* — Phase-1 surface)**: Built-in Project workflow
  **configured Status-target values** are UI-managed and not API-readable.
  Documented semantics captured from GitHub docs/changelog; the configured
  per-project target values are deferred (named consumer: Stage 1 §5.5/§5.8
  evidence E7, and Stage 4 transition matrix — both blocked on this until read
  from the UI). Rationale: no API surface exists; live observation is the only
  reliable source. Recorded per goal-execution contract §Accepted-Exceptions.
- No other evidence items are missing or failed.

## Evidence table (plan Verification Surface)

| ID | Phase | Status | Evidence / artifact |
|----|-------|--------|---------------------|
| V1 | 1 | passed | Plan file exists with frontmatter + 10 architecture sections; `cg-render-artifact --validate-only` exit 0 |
| V2 | 1 | passed | Plan §1 classifies claims; exact workflow/job names and ruleset checks cited; re-verified via API |
| V3 | 1 | passed | Plan §2 sources-of-truth table with one owner per state type |
| V4 | 1 | passed | Plan §4 stages 0A–6; 0A read-only, 0B human-gated, 1 manual |
| V5 | 1 | passed | Plan §5 smallest safe pilot criteria/actions/rollback |
| V6 | 1 | passed | Plan §6 security matrix (separate credentials; no secret exposure to PR CI) — reinforced by §3.3 |
| V7 | 1 | passed | Plan §7 recovery/idempotency table |
| V8 | final | pending | Artifact validation re-run at final completion (Step 3.5) |
| V9 | final | superseded | Stage 0B and Stage 1 approval gates completed in Run 3; superseded by the current PR #135 review/merge handoff |

## Constraints check (plan Constraints)

| ID | Phase | Check | Result |
|----|-------|-------|--------|
| C1 | final | Diff only under plan artifact | passed (this run: evidence + metadata under `.cg-docs/`) |
| C2 | 1 | No invented GitHub API/permission/field-ID claims | passed (all tagged Verified / User-confirmed / documented) |
| C3 | 1 | Pester runner + required checks preserved | passed (no test/workflow changes) |
| C4 | 1 | Human retains merge/milestone control | passed (no automation introduced) |
| C5 | 1 | Existing Status options preferred | passed (Status options verified unchanged) |
| C6 | 1 | Prefer built-in Project workflows | passed (inventory documented, no custom Actions) |
| C7 | 1 | No live GitHub mutations; assign shape from docs only | passed (no-mutations statement in evidence report §10) |

## Remaining uncertainty

- Configured per-workflow Status targets in the UI (deferred — see E1).
- "Approve Copilot-initiated workflow runs" toggle not API-readable (recorded as
  User-confirmed with settings path).
- Whether a live assign/Status write works under the exact volunteered token is
  only proven in the Stage 1 pilot (by design).

## Final status

- Run status: **completed** (Phase 1 finished; plan remains `status: active` /
  `completed-phases: [1]`, paused before Stage 0B, which requires explicit human
  approval).

---

## Run 2 — Stage 0B: Approved pre-pilot repairs (2026-08-06)

- Invocation: `phase2 review:auto`; scope Phase 2 only. Selected pilot: issue
  #127 (`artifact-html-opt-in-default`).
- Step 1 preflight completed; Step 2 human approval gate **approved** by the
  user; Steps 3–5 executed as approved.
- Completed:
  - Added feature `artifact-html-opt-in-default` to milestone `workflow-maturity`
    (status `planned`, `plan: null`, `github` linkage to #127) via @cg-roadmap.
  - Applied minimal approved issue #127 edits (linkage placeholders filled; 3 of
    4 `Ready for Copilot` boxes checked; Project-Status box left unchecked).
  - Verified read-only: #127 on CompoundGPID-progress / Status `Backlog` /
    unassigned / no linked PR; targeted roadmap validation passed (0 failures).
  - Confirmed exact implementation closure for Stage 1 (config-resolution-only;
    generated targets to be regenerated, never hand-edited).
- Deviations: none (all changes within the approved Step 2 gate).
- Phase 2 status: **NOT completed** — this run stops at the required handoff.
  Human must commit/push, merge the Stage 0B PR, and set issue #127 Project
  Status to `Ready` before Phase 3 (Stage 1).
- `completed-phases` unchanged (`[1]`); `current-phase` remains `2`.

---

## Run 3 — Stage 1 (Phase 3): Manual pilot closeout (2026-08-07)

- Invocation: `phase3 review:auto`; scope Phase 3 only — do NOT repeat the
  assignment, modify issue #127 or PR #131, implement Stage 2, or introduce
  automation.
- **Precondition gate**: Phase 2 (Stage 0B) ran and stopped at its required
  handoff. The human completed that gate in the live repo: PR #128 merged into
  `main` at `2026-08-07T11:38:17Z` and issue #127 Project Status was set to
  `Ready` (verified live; issue body shows all four `Ready for Copilot` boxes
  checked). Phase 3 (the manual pilot) then completed in the live repo via
  issue #127 / PR #131. This run records the verified closeout.
- **Artifact validation preflight** (run before any write on 2026-08-07):
  `cg-render-artifact --validate-only
  .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`
  → output `Validated .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`, exit 0.
- **Final validation records** (re-run and recorded 2026-08-07, after all
  Phase 3 closeout edits):
  - `cg-render-artifact --validate-only .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`
    → output `Validated .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`, exit 0.
  - `cg-render-artifact --check .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`
    → `current .cg-docs/views/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.html`, exit 0.
  - Generated-view source/provenance parity: plan source SHA-256
    `7475eec2228b9339f9dddae4dd8002ae519a7bb43cfd5b06dd06682b17d97057` matches
    the view's `<meta name="artifact-source-sha256">` and the
    `artifact-provenance` JSON `sourceSha256` (parity confirmed; generated view
    regenerated via the canonical renderer only when the canonical source
    changed).
  - JSON parse and required-field check of
    `.cg-docs/active-state/current.json`: the file was parsed successfully
    (`python -c "import json; json.load(open(...))"` → `JSON PARSE: OK`,
    exit 0), and the following fields were present: `schemaVersion`,
    `updatedAt`, `workflow`, `status`, `artifactRefs`, `nextCommand`. This was a
    parse plus required-field presence check; no JSON-schema validator ran.
- **Live verification performed** (primary source: authenticated `gh` API /
  GraphQL on 2026-08-07; the merge-parent structure was additionally verified
  locally with `git cat-file`):
  - Issue #127 closed `completed` at `2026-08-07T13:49:56Z`; Project Status
    `Done` (option `98236657`); assignees `Copilot`, `randrescastaneda`.
  - PR #131 `MERGED` at `2026-08-07T13:49:54Z` by `randrescastaneda` (API) with
    merge commit OID `fc4ed30027f702c4adffd7e742f8be416da39576` (API) whose
    two-parent structure was locally verified with `git cat-file`
    (parents: main tip `cbc598b` + PR head `73f948b`);
    17 changed files (API); `autoMergeRequest: null`; branch
    `copilot/make-html-publication-opt-in-default`; author
    `app/copilot-swe-agent`.
  - Required checks all green; CC lint green after human title fix at
    `13:07:43Z`; non-required checks SUCCESS.
  - Project item: PR #131 is NOT a separate project item (zero PR items on
    project); issue item is canonical (E10 verified).
- **Executed steps**: Step 1 (verify live state) and closeout deliverables
  (evidence pack, plan metadata, execution report, active-state, plan view).
- **State reconciliation (no deviation)**: per the execution contract, phase
  metadata must be updated after a phase completes. The plan frontmatter had
  lagged live reality (`completed-phases: [1]`, `current-phase: 2` while Phase
  2's human gate and Phase 3 had already completed in the live repo); this run
  reconciles the metadata to the verified values `completed-phases: [1, 2, 3]`
  and `current-phase: 4`. This is contract-required state reconciliation, not a
  deviation; **no phases were re-run**. Deviation policy remains `ask` with no
  deviations taken.
- **Accepted exceptions**: none. **Evidence mix**: Stage 1 evidence combines
  API-verified fields, operator-confirmed conclusions, agent-reported
  execution results (e.g. the focused-test output), and documented
  not-retrievable values. The GO verdict is based on this documented
  combination with no blocking gap — not on API-verified evidence alone.
  Precision limitations documented instead (see below).
- **Precision limitations (documented, not exceptions)**:
  - Copilot model config (GPT-5.6 Luna, X-High reasoning): operator-confirmed
    UI setting; no public API surface.
  - Actions approval evidence: the ~34-minute `created_at`→`run_started_at`
    run delay (12:06–12:40Z) is described as **consistent with** an approval
    wait and used only as a **proxy**; it is not claimed to prove that approval
    caused the delay. `triggering_actor` identifies who **triggered the run
    start**, not who approved. The exact approval time and approver are
    **not retrievable** via the API (no approval-event endpoint); no value
    invented. The approval safeguard itself is operator-confirmed enabled;
    `can_approve_pull_request_reviews` is NOT treated as evidence for it
    (different capability).
  - Intermediate Project Status option values (Ready/In progress/In review)
    are operator-confirmed from event timestamps; final `Done` is API-verified.
  - Live repo-level `default_workflow_permissions` is now `read`; per the
    continuity handoff this is an **intentional pre-pilot change**
    (operator-confirmed) — exact timestamp/actor not retrievable, but **not
    unexplained drift**, so it is **not** a Stage 2 residual decision.
  - "No administrator/ruleset bypass" and "secrets unchanged" are
    **operator-confirmed conclusions** supported by API evidence (file list,
    ruleset timestamps, `autoMergeRequest: null`), not facts proven solely by
    the API or changed-file list.
- **Evidence table (Phase 3 / §5.8)**: E1–E10 all recorded in
  `.cg-docs/work-reports/2026-08-07-copilot-pilot-evidence.md`,
  cross-classified API-verified / operator-confirmed / not-retrievable. E4
  distinguishes the 13 explicitly listed allowed-path files from the four
  `.compound-gpid-generated.json` manifests subsequently authorized by the
  human target-generation-closure decision.
- **Stage 1 success criteria (§5.9)**: all 7 PASS.
- **Failure criteria (§5.10)**: none observed.
- **Stage 2 go/no-go**: **GO** recorded in the evidence pack.
- **Operational lesson (carried to dispatcher stage)**: Copilot's initial PR
  title failed the Conventional Commits required check and required one human
  rename before green. Not a Stage 2 blocker, but must be addressed (explicit
  conventional-title instruction or dispatcher-side guard) before unattended
  dispatch.
- **Filing status**: evidence pack + this Run 3 section are created in the
  current branch (`issue-implementation-pipeline-from-phase-3`) and become
  canonically filed when the Stage 1 closeout PR — PR #132, distinct from the
  already-merged pilot implementation PR #131 — merges into `main`.
- **Roadmap**: no feature in `roadmap.json` carries this plan's `plan` path, so
  no roadmap status dispatch/update is performed (per /cg-work permissions and
  Step 3.7 no-match fallback; feature `artifact-html-opt-in-default` remains
  `status: planned` — a human decision, not auto-advanced).
- **Phase 3 status**: **completed** — plan remains `status: active`,
  `completed-phases: [1, 2, 3]`, `current-phase: 4` (paused before Stage 2).
- **Next action (metadata handoff)**: PR #132 (Stage 1 closeout) is open for
  review; after it is reviewed and merged, resume with `/cg-work phase4`.
- **V9 traceability (superseded)**: plan Verification-Surface row V9 ("final
  plan handoff — Stage 0B/1 require explicit human approval") is superseded by
  this closeout: both Stage 0B and Stage 1 approvals were obtained and the
  pilot completed. V9 is recorded explicitly in `current.json`
  `evidenceStatus` with `status: superseded` (Stage 0B gate = PR #128 merged;
  Stage 1 gate = PR #131 merged). V8 remains `pending` for the final
  plan-status completion at whole-plan close.

---

## Run 4 — Stage 2 (Phase 4): Readiness contract and validator (2026-08-07)

- Invocation: `phase4 review:auto`; scope Phase 4 only — implement the Stage 2
  readiness contract and deterministic validator. Do NOT implement the Stage 3
  dispatcher, and do NOT start Phase 5.
- **Precondition gate**: working tree clean; `origin/main` = local `main` =
  `54b9b19979c7d201c3c79a4dc4a38950f23247c5` (PR #132 merge); plan frontmatter
  `completed-phases: [1, 2, 3]`, `current-phase: 4`; Stage 1 closed with **GO**
  (Run 3); Stage 2 not started. All preconditions passed.
- **Artifact validation preflight** (run before any write): `cg-render-artifact
  --validate-only .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`
  → `Validated ...`, exit 0.
- **Fixed design decisions** (from the invocation): the primary readiness
  mechanism is the structured Markdown issue contract proven by issue #127. No
  GitHub issue form, no `cg:ready` label, no dispatcher, no automatic Copilot
  assignment, no automatic Project-status mutations, no scheduled workflows, and
  no new credentials/secrets were added. The two authoritative readiness signals
  are (1) the issue's Project Status is `Ready` and (2) the structured contract
  is complete and valid.
- **Language choice**: implemented in Python. No blocking incompatibility found.
  The validator is **stdlib-only** (`argparse`, `json`, `re`, `subprocess`,
  `dataclasses`, `pathlib`); CI installs only `pytest`, so third-party libraries
  (loguru/pydantic/etc.) are intentionally not used, matching the existing
  `scripts/` tooling.
- **Implemented files**:
  - `scripts/issues/__init__.py` — package marker.
  - `scripts/issues/{contract.py,contract_rules.py,clients.py,gh_client.py,fixtures.py,orchestration.py,render.py,cli.py,readiness.py}` — modular validator implementation with a compatibility facade; fence-aware contract rules R001–R018, state rules R019–R021, read-only `GhCliClient` (argv-safe documented `gh`), offline `FixtureClient`, orchestration, renderers, and CLI.
  - `scripts/issue_readiness.py` — thin CLI shim (mirrors `render_artifact.py`).
  - `scripts/tests/fixtures/ready_issue.json` + `ready_issue_body.md` —
    non-production fixture (a Ready #127-style contract clone).
  - `scripts/tests/test_issue_readiness.py` — 158 deterministic tests with
    inline fixtures and mocked GitHub responses; no live GitHub in unit tests.
  - `docs/copilot-readiness.md` — canonical contract spec, CLI usage, JSON
    result, exit codes, and validation-vs-dispatch distinction.
  - `.github/workflows/tests.yml` — **one line** added to the `native-targets`
    job's first (required) pytest list. This is the only GitHub Actions change;
    no new workflow, permissions, triggers, secrets, concurrency, or dispatch.
- **Canonical contract**: 13 required `## ` sections (exact heading text derived
  from #127: `Roadmap linkage`, `Ready for Copilot`, `Outcome`, `Acceptance
  criteria`, `Scope`, `Non-goals`, `Expected allowed paths`, `Prohibited paths`,
  `Verification commands`, `Dependencies / blockers`, `Risk class`, `Human review
  instructions`, `Blocked-stop conditions`) plus the hidden
  `<!-- compound-gpid-tracked: <id> -->` marker and the `**Feature ID:** \`<id>\``
  declaration, which must match the marker. Parsing is deterministic and
  fence-aware; validation does not depend on AI judgment.
- **Deterministic validator**: treats the issue body as untrusted data; rejects
  missing/duplicate sections; validates feature-id ↔ marker; rejects absolute
  paths, `../` traversal, UNC/drive paths, backslashes, empty segments, and
  unbalanced globs; requires non-empty acceptance criteria and verification
  commands; validates risk class `low|medium|high`; validates blocked-stop and
  readiness confirmation; verifies Project Status is `Ready`; detects an open
  implementation PR via `Fixes #N`/`Closes #N`/`Resolves #N`; detects an existing
  Copilot assignee; handles dependencies deterministically; and performs **no**
  issue/Project/PR/assignment/label/comment mutation.
- **CLI**: `python scripts/issue_readiness.py --issue N --dry-run [--json]` or
  `--fixture PATH --dry-run [--json]`. Exit codes: `0` ready, `2` not-ready
  (validation), `3` config error, `4` api/network error — validation failure is
  distinguished from API/network/configuration failure. `--dry-run` is the
  canonical and only mode (the validator never mutates).
- **Bug found and fixed during live dry-run**: the Project Status GraphQL query
  used `project { name }`; `ProjectV2` exposes `title`, not `name` ("Field 'name'
  doesn't exist on type 'ProjectV2'"). Fixed to `project { title }`; GraphQL
  query/schema errors were reclassified from `api_error` to `config_error`
  (exit 3), since they are client-side, not GitHub server/network failures.
- **Validation results** (executed checks):
  - Focused readiness tests: `python -m pytest scripts/tests/test_issue_readiness.py -q`
    → **158 passed**, exit 0.
  - Exact CI-registered invocation (native-targets first pytest list, now
    including `test_issue_readiness.py`): **530 passed, 11 skipped**, exit 0
    (the 11 skips are pre-existing target tests, unrelated).
  - Dry-run evidence (fixture): `--fixture .../ready_issue.json --dry-run --json`
    → **READY**, exit 0, all 21 rules pass.
  - Dry-run evidence (live, read-only): `--issue 127 --dry-run` → **NOT READY**,
    exit 2; #127's contract is valid but state rules fail (R019 `Done`≠`Ready`,
    R021 Copilot already assigned); open closing PRs = 0 (#131 is merged/closed).
  - Markdown/docs: `docs/copilot-readiness.md` is well-formed and registered in
    `docs/navigation.json`; no external links added. Pester suite not affected by these changes
    (no `.ps1`/prompt/agent/install file touched); no Pester test pins the
    pytest list (verified by grep).
- **Review-driven hardening** (`review:auto`, resolved route `standard` with a
  security/path-safety emphasis; `@cg-adversarial`, `@cg-testing`,
  `@cg-architecture`, `@cg-code-quality`, `@cg-version-control`,
  `@cg-documentation` dispatched read-only; `@cg-data-quality`,
  `@cg-reproducibility`, `@cg-performance` assessed out of scope — no
  data/numerics, lockfiles, or perf-critical paths in this read-only validator):
  applied P1/security/correctness fixes before stopping — path validation now
  rejects surrounding-whitespace/control-char bypasses and Windows drive
  prefixes (`c:foo`); bare `*`/`**`/`.` are rejected as **allowed** paths
  (overbroad scope) while remaining valid as **prohibited** paths; uncaught
  `json.JSONDecodeError`/`FileNotFoundError` now map to exit 4/3 (not a
  traceback); `gh` subprocess decodes UTF-8 explicitly (Windows console safe);
  `argparse` usage errors exit 3 (not 2, which collided with `EXIT_NOT_READY`);
  `## Risk class` now requires an exact-class line (no false-ready from prose
  like "low confidence"); Project Status is read from the canonical project
  only (no cross-project fallback); `blocked by` ignores explicit negation;
   ATX trailing hashes are stripped. Added the missing P1 tests (R001/R002
  failure modes, GraphQL error/fallback/None, malformed-JSON, CLI config-error
   exit, missing-fixture, empty sections, `~~~` fences, `projectStatus` None).
   The follow-up review split the validator into responsibility-specific modules
   under the repository's 300-line script rule while retaining the historical
   import facade.
- **No live GitHub mutations**: the validator is read-only by construction; the
  live #127 dry-run issued only `gh issue view`, `gh pr list --state open`,
  `gh repo view --json`, and `gh api graphql` (a read query). No issue edit,
  comment, label, assign, Project-field write, or PR mutation occurred. Issue
  #127 was not modified. Unit tests use mocked responses and touch no live
  state.
- **Stage 3 not started**: no `.github/workflows/copilot-dispatch.yml`, no
  `scripts/issues/dispatch.py`, no assignment logic, no Project-status mutation
  workflow, no scheduled workflow, and no new credential/secret were created.
  Stage 2 delivers the gate only; dispatch is explicitly deferred to Phase 5.
- **Phase 4 acceptance criteria** (plan): validator green/red deterministic on
  fixtures (✓); dry-run used on a non-production fixture (✓); zero dispatch
  side effects (✓); new test file registered in a required CI check (✓). All
  pass.
- **State reconciliation (no deviation)**: per the goal-execution contract,
  Phase 4 completion requires updating phase metadata. Appended `4` to
  `completed-phases: [1, 2, 3, 4]` and set `current-phase: 5` (crash-safe order:
  `completed-phases` written before `current-phase`). No phases were skipped or
  re-run. Deviation policy remains `ask` with no deviations taken.
- **Roadmap**: no feature in `roadmap.json` carries this plan's `plan` path, so
  no roadmap status dispatch/update is performed (per `/cg-work` Step 3.7
  no-match fallback). `roadmap.json` feature status was **not** updated
  automatically.
- **Evidence table**: V8 (final artifact validation) remains `pending` for
  whole-plan completion. V9 is `superseded`; the Stage 0B and Stage 1 approval
  gates were completed in Run 3, and the current handoff is PR #135 review/merge
  before Phase 5.
- **Accepted exceptions**: none.
- **Final status**: Run 4 **completed** — Stage 2 implemented and verified. Plan
  remains `status: active`, `completed-phases: [1, 2, 3, 4]`, `current-phase: 5`
  (paused before Stage 3 dispatcher). **Phase 5 was not started.**
- **Next action**: review and merge PR #135, then run `/cg-work phase5`; Phase 5
  must not run before this PR is merged.

---

## Follow-up review corrections (2026-08-10)

- PR #135 review evidence was refiled under the v2 plan review paths. The three
  editorial-theme-named validator review artifacts were removed as unrelated.
- Focused readiness suite: `python -m pytest scripts/tests/test_issue_readiness.py -q`
  -> 158 passed.
- Exact native-target CI pytest list: 530 passed, 11 skipped, exit 0.
- Documentation site/link check: `node scripts/check-docs-site.js` -> passed
  (34 navigable Markdown pages, 6 groups).
- Plan validation and view parity: `cg-render-artifact --validate-only` -> 0;
  `cg-render-artifact --check` -> current, 0.
- Brain rebuild: `cg-index --brain` -> 628 entities, 4 topics, 268 edges;
  known repository scanner warnings were non-fatal and the success line was
  present.
- Deterministic fixture and injected-client dry runs verified exit codes 0, 2,
  3, and 4. Phase 5 was not started.

---

## Run 5 — Stage 3 (Phase 5): Single-issue manual dispatcher (2026-08-11)

- Invocation: `phase5`; scope Phase 5 only — the bounded Stage 3 dispatcher.
  Phase 6 and later were explicitly out of scope and not started.
- **Precondition gate** (read-only verification, all passed):
  - `main` contains merge commit `8881a2d083d0bf8360c89e7732ba187dea3638a0`
    ("Merge pull request #135 from GPID-WB/issue-implementation-phase-4"); local
    `main`, `origin/main`, and the working branch are all at this commit.
  - Plan frontmatter records `completed-phases: [1, 2, 3, 4]` and
    `current-phase: 5`.
  - Stage 2 readiness validator and its tests are present on `main`
    (`scripts/issues/readiness.py`, `scripts/issue_readiness.py`,
    `scripts/tests/test_issue_readiness.py`).
- **Artifact validation preflight** (run before any write):
  `cg-render-artifact --validate-only
  .cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md` →
  `Validated ...`, exit 0.
- **Active-state reconciliation (2026-08-11, no deviation)**: the pre-merge D6
  blocker ("review, commit, push, and merge the Stage 2 implementation ... before
  running /cg-work phase5") is now obsolete — PR #135 (Stage 2) is merged per the
  precondition gate. The old branch reference (`issue-implementation-phase-4`)
  and the obsolete `nextCommand` ("review and merge PR #135, then run /cg-work
  phase5") were reconciled to the current branch `issue-implementation-phase5`
  and the Phase 5 handoff. D6 was removed from `unresolvedDecisions`; D4 and D5
  (non-blocking) are retained. The historical D6 record remains in this Run 5
  section (and prior runs) — the stale entry in `current.json` was replaced, not
  silently deleted.
- **Fixed design decisions** (bounded Stage 3, per the invocation):
  - A `workflow_dispatch`-only workflow; exactly one explicit `issue_number`
    input and a `dry_run` input defaulting to `true`.
  - Effective concurrency of one via `concurrency: group: copilot-dispatch,
    cancel-in-progress: false`.
  - No schedules, polling, batch selection, automatic merging, automatic
    roadmap updates, or milestone progression.
  - Runs only trusted code from the default branch (checkout pins
    `github.event.repository.default_branch`); never checks out a PR head or
    untrusted ref.
  - Reuses the Stage 2 validator (`validate_readiness`) as the gate; no parsing
    or validation rules were reproduced in the dispatcher.
  - Dry-run is a true zero-mutation path.
  - Before any non-dry-run mutation: validate readiness; perform all
    duplicate/idempotency checks; revalidate readiness immediately before
    assignment; fail closed if either validation fails or state changes.
  - Non-dry-run mutation order: assign only `copilot-swe-agent[bot]`; only after
    assignment succeeds set Project Status `In progress`; then add an audit
    comment.
  - Assignment-succeeds-but-Project-fails: no automatic unassign, no rollback
    speculation, an observable audit/failure comment, non-zero exit, and the
    manual recovery procedure documented (also in `docs/copilot-dispatch.md`).
  - Repeat dispatch on an already-assigned issue or existing implementation PR
    is an idempotent no-op (exit 0) with a clear explanation.
  - Separate least-privilege credentials: `COPILOT_ASSIGN_TOKEN` (assignment +
    audit comments) and `PROJECT_SYNC_TOKEN` (Project Status). No combined
    token; no secrets/settings created by the workflow (documented as required
    setup in the handoff).
  - Neither credential is referenced by any `pull_request` or
    `pull_request_target` workflow (verified statically by tests).
  - Issue content is treated as untrusted input; argv-safe and path-safe
    patterns preserved (temp-file bodies, `gh --input` / `--body-file`, never
    shell interpolation).
- **Implemented files**:
  - `.github/workflows/copilot-dispatch.yml` — `workflow_dispatch`-only
    dispatcher workflow (`issue_number` + `dry_run` default true, concurrency 1,
    least privilege, trusted default-branch checkout, two separate secrets).
  - `scripts/issues/dispatch.py` — dispatcher orchestration (`run_dispatch`),
    result type, exit codes (0/2/3/4/5/6/7), CLI.
  - `scripts/issues/dispatch_client.py` — `GhDispatchMutator` (assign / Project
    Status / comment) with separated credentials and temp-file argv-safe bodies;
    `DispatchMutator` protocol.
  - `scripts/issue_dispatch.py` — thin CLI shim mirroring
    `scripts/issue_readiness.py`.
  - `scripts/tests/test_issue_dispatch.py` — 41 deterministic mocked tests:
    dry-run zero mutations; initial readiness failure (not-ready/config/api);
    idempotent no-op for already-assigned and existing open PR (live + dry-run);
    readiness changing before the second validation fails closed; assignment
    failure leaves status untouched and comments; assignment-succeeds-Project-
    fails keeps assignee and documents recovery; Project update never occurs
    before assignment (ordering indexed check); audit-comment ordering and
    partial-failure reporting; exact `copilot-swe-agent[bot]` bot identity;
    CLI wiring and JSON schema; mutation-client units (per-token separation,
    missing token fail-closed, unsupported status, issue-not-on-project);
    workflow static constraints (trigger, inputs, concurrency, permissions,
    trusted checkout, both secrets) and cross-workflow secret isolation.
  - `.github/workflows/tests.yml` — `scripts/tests/test_issue_dispatch.py` added
    to the required `native-targets` first pytest list (one line).
  - `docs/copilot-dispatch.md` — dispatch inputs, dry-run, permissions,
    mutation order, exit codes, credential isolation, manual recovery;
    registered in `docs/navigation.json`; readiness page cross-ref updated.
- **No live GitHub mutations**: issue #127 was NOT dispatched; no live issue was
  dispatched or run through the new workflow, even in dry-run mode. All
  validation used fixtures, fakes, and stub `gh` runners. No issue, Project,
  PR, comment, label, or assignment mutation was performed. No credentials were
  created or repository settings changed.
- **Validation results** (executed checks):
  - Focused dispatcher suite: `python -m pytest scripts/tests/test_issue_dispatch.py -q`
    → **41 passed**, exit 0.
  - Focused readiness suite (regression guard): → **194 passed**, exit 0.
  - Exact native-targets CI pytest list (17 files incl. the new dispatcher
    test): **607 passed, 11 skipped**, exit 0.
  - `python -m py_compile` on all new modules → pass.
  - `node scripts/check-docs-site.js` → passed (35 navigable Markdown pages,
    6 groups).
  - Workflow YAML parses (PyYAML note: `on:` becomes YAML 1.1 `true` under
    PyYAML — this is a PyYAML quirk, not a GitHub issue; GitHub's parser and the
    repo's other workflows use the same `on:` syntax).
- **Phase 5 status**: **NOT completed** by this run, per the invocation. Live
  workflow validation against a real issue remains outstanding and requires
  explicit human authorization after review/merge, plus the required
  credential/environment setup. `completed-phases` was NOT appended (stays
  `[1, 2, 3, 4]`); `current-phase` stays `5`; `status` stays `active`. No
  `failing-steps` were recorded.
- **Deviation policy**: `ask` (plan value; no runtime override). No deviations
  were taken; all work stayed within the bounded Stage 3 scope.
- **Roadmap**: no feature in `roadmap.json` carries this plan's `plan` path, so
  no roadmap active-status or done dispatch was performed (consistent with
  Runs 1–4).
- **Evidence gate**: Phase 5 has no phased Verification-Surface rows in the plan
  (V1–V7 are Phase 1; V8/V9 are final) and no final phasing is being recorded
  because the phase is intentionally left incomplete pending live validation.
- **Handoff (next)**: review and merge the Phase 5 PR, then before ANY live
  dispatch: create the `COPILOT_ASSIGN_TOKEN` and `PROJECT_SYNC_TOKEN`
  environment-protected repository secrets, create the protected environment,
  and run the workflow first in dry-run mode on a fixture/throwaway issue, then
  a supervised live dispatch under `/cg-work phase5` continuation or `/cg-resume`.
  Manual recovery steps for the partial-failure state are in
  `docs/copilot-dispatch.md`.
- **Final status (Run 5)**: **completed as an implementation+deterministic
  validation run**; Phase 5 itself remains **not completed** (live validation
  pending), paused for review/merge and supervised live validation.

---
