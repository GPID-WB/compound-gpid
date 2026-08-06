---
date: 2026-08-05
title: "Controlled GitHub Copilot issue-implementation pipeline"
status: active
scope: "Deep"
brainstorm: null
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
tags: [github, copilot, issues, project, ci, dispatch, security, workflow-maturity, automation]
phases: 8
execution-report: ".cg-docs/work-reports/2026-08-06-copilot-issue-implementation-pipeline-v2.md"
completed-phases: [1]
current-phase: 2
---

# Plan: Controlled GitHub Copilot issue-implementation pipeline

phases: 8  # convenience hint -- may be stale; always recount from ## Phase headers

## Objective

Design a staged, human-controlled pipeline that selects only implementation-ready GitHub issues, delegates them one-at-a-time to the GitHub Copilot coding agent, lets Copilot open traceable PRs, relies on existing repository CI as the merge gate, keeps GitHub Project `Status` synchronized without inventing competing sources of truth, and defers automation until a smallest safe manual pilot produces evidence.

Completing this master plan authorizes **documentation of the architecture and Stage 0A read-only verification only**. Stage 0B requires explicit human approval after reviewing the Stage 0A evidence report. Stage 1 (smallest safe manual pilot) requires another explicit human approval after Stage 0B. It does **not** authorize implementing Stages 2–6, creating workflows/tokens/apps/new labels/templates, or changing GitHub settings.

## Context

### Revision note

This is **v2** (2026-08-05); it supersedes `2026-08-05-copilot-issue-implementation-pipeline.md` (v1), preserved as historical data. v2 applies six plan-review findings (1 P1 blocking, 5 P2) plus minor P3 clarifications: **P1.1** makes Stage 0A genuinely read-only (assign-API shape from docs only; live assign trial deferred to Stage 1 Section 5.6 step 3); **P2.1** splits must-resolve vs may-defer Unresolved items; **P2.2** makes the R26 "including issue #63 if open" conditional decidable; **P2.3** makes the Section 7 Status retry race-safe; **P2.4** clarifies Objective authorization for Stage 0B repairs; **P2.5** corrects the `native-targets` pytest registration (three explicit file lists, no auto-discovery); P3 tweaks clarify `git fetch`, the `project`-scope staging, the `linked:issue` search qualifier, and environment-protected secret storage. Completion of this master plan authorizes Stage 0A only. Stage 0B requires explicit human approval after reviewing the Stage 0A evidence report; Stage 1 requires another explicit human approval after Stage 0B repairs. Architecture, sources of truth, and phase structure (0A-6) are unchanged.

### Charter alignment

- **Product**: Compound GPID is an AI-assisted development workflow/plugin (prompts, agents, skills, adapters, scripts, docs) — not a survey-data analytical application.
- **Current charter focus** (Token Efficiency Core System) does not block this work, but this plan is **outside** that focus. Treat it as Workflow Maturity / self-hosting operational infrastructure.
- **Constraints that bind this design**: never commit secrets; fail loudly; conventional commits + feature branches; P0 security findings block merge; preserve deterministic validation and Pester safety.

### Classification legend (Section 1)

| Tag | Meaning |
|-----|---------|
| **Verified** | Observed in this repository or via authenticated `gh`/API during planning (2026-08-05) |
| **User-confirmed** | Stated by the operator for this planning session; not re-derived from API |
| **Inference** | Reasonable design inference from verified facts; must be re-checked before coding |
| **Unresolved** | Capability, permission, field ID, or API behavior not verified; Stage 0A must resolve |

### Planning environment notes

- Planning branch: `issues-implementation-pipeline` (worktree).
- `compound-gpid.local.md` was missing in the worktree during planning.
- Local `gh` token scopes observed: `gist`, `read:org`, `repo`, `workflow`. **Missing** `read:project` / `project` — Project GraphQL/list failed with scope error (**Verified**).
- `roadmap.json` has **no** top-level `githubIssues` block and **zero** `features[].github` links in the worktree snapshot, while GitHub has many open `cg:roadmap` issues with hidden markers (**Verified** drift).

---

## Section 1 — Current-state findings

### 1.1 Repository identity and role

| Finding | Class |
|---------|-------|
| Public repo `GPID-WB/compound-gpid`; default branch `main`; viewer permission ADMIN for planning account | Verified |
| Distributes `.github/` prompts/agents/skills/instructions, multi-platform adapters (`.kilo/`, `.agents/`, `.opencode/`, `.claude/`), `scripts/`, `bin/`, `tests/`, `.cg-docs/` | Verified |
| Not a conventional analytical app; validation is plugin/tooling oriented (Pester, Python gates, link/parity/packaging) | Verified |

### 1.2 Existing workflow mechanisms to reuse

| Mechanism | Path / surface | Role | Class |
|-----------|----------------|------|-------|
| Issues manager | `.github/prompts/cg-issues.prompt.md` | status/backfill/link/adopt/setup; one-way roadmapâ†”issue linkage; no `gh issue close` | Verified |
| Roadmap writes | `@cg-roadmap` / `.github/agents/cg-roadmap.agent.md` | sole schema-aware `roadmap.json` mutator | Verified |
| Plan â†’ work contract | `.github/shared/goal-execution.contract.md` | completion contract, verification surface, deviation policy | Verified |
| Active-state pointer | `.github/shared/active-state.contract.md` â†’ `.cg-docs/active-state/current.json` | compact restart aid, not transactional execution DB | Verified |
| PR open | `/cg-commit-push-pr` | push + `gh pr create`; optional `Refs #` / `Closes #` | Verified |
| CI fix loop | `/cg-verify-pr` | read check rollup, classify failures, optional auto-fix | Verified |
| PR template checklist | `.github/PULL_REQUEST_TEMPLATE.md` | E2E, tests, parity, docs, security checklist | Verified |
| Canonical tests | `tests/Run-Tests.ps1` â†’ `tests/last-run.json`; Pester **4.10.1** | only approved full-suite runner | Verified |
| Roadmap schema tests | `tests/roadmap.Tests.ps1` | validates optional `githubIssues` + `features[].github` | Verified |
| Prompt structure tests | `tests/prompt-tools.Tests.ps1` | guards `/cg-issues` safety patterns | Verified |
| Prior integration plan | `.cg-docs/plans/2026-06-11-github-issues-integration.md` (completed) | established one-way linkage, confirmation gates, markers | Verified |
| Security lesson | `.cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md` | argv-safe `gh`, realpath plan paths, `--body-file` | Verified |

### 1.3 CI and validation surfaces

Workflow files (**Verified**):

| Workflow file | Name | Triggers (summary) | Jobs (names as defined) |
|---------------|------|--------------------|-------------------------|
| `.github/workflows/tests.yml` | Pester tests | push `main`/`feat/**`/`fix/**`/`chore/**`; PR â†’ `main` | `Browser evidence manifest tests`; `Native target Python gate on ${{ matrix.os }}` (windows-2022, macos-14); `Pester on ${{ matrix.os }}` (windows-2022, macos-14); `Docs staleness check` (PR only, non-blocking warning) |
| `.github/workflows/commit-lint.yml` | Conventional commits lint | PR opened/edited/synchronize/reopened | `PR title follows Conventional Commits` |
| `.github/workflows/link-check.yml` | Link Check | path-filtered push/PR; weekly cron; `workflow_dispatch` | `link-check` |
| `.github/workflows/pages.yml` | Deploy documentation site | docs paths on `main`; `workflow_dispatch` | `deploy` |

**Branch ruleset** `Protect main` (id `16657602`, enforcement active, target default branch) (**Verified** via API):

| Rule | Parameters |
|------|------------|
| deletion restricted | yes |
| non_fast_forward (force-push blocked) | yes |
| pull_request required | `required_approving_review_count: 0`; `required_review_thread_resolution: true`; merge methods merge+rebase; no code-owner requirement |
| required_status_checks | `strict_required_status_checks_policy: true` (branch must be up to date) |
| Required check contexts | `Native target Python gate on macos-14`; `Native target Python gate on windows-2022`; `PR title follows Conventional Commits`; `Pester on macos-14`; `Pester on windows-2022` |
| Bypass | `RepositoryRole` actor_id `5`, mode `always`; planning user `current_user_can_bypass: always` |

**Not required by ruleset** (still may run): Browser evidence, Docs staleness, Link Check, Pages (**Verified**).

**Classic branch protection API** returned 404; protection is ruleset-based only (**Verified**).

**Actions repo settings** (partial): Actions enabled; `allowed_actions: all`; `default_workflow_permissions: write`; `can_approve_pull_request_reviews: true` (**Verified**). Fine-grained â€œapprove Copilot-initiated workflow runsâ€ setting was **not** readable via the endpoints used; treat operator statement as **User-confirmed**.

### 1.4 Issue–roadmap linkage

| Finding | Class |
|---------|-------|
| Hidden body marker pattern: `<!-- compound-gpid-tracked: <feature-id> -->` | Verified (e.g. issue #98, #84) |
| Issue body template is roadmap placeholder: milestone, feature ID, status (often `idea`), short description in fenced `text` block | Verified |
| Label `cg:roadmap` exists and is applied to tracked issues | Verified |
| ~44 open issues, all observed sample labeled `cg:roadmap` | Verified |
| Worktree `roadmap.json` lacks `githubIssues` and all `features[].github` links â†’ **linkage drift** vs live issues | Verified |
| Roadmap feature `github-issues-integration` still `status: idea` while integration plan is `completed` | Verified drift |
| Many open issues are **not implementation-ready** (idea placeholders, no acceptance criteria / path bounds / verification commands) | Verified |
| No `.github/ISSUE_TEMPLATE/` present | Verified |
| `/cg-issues` never closes issues; closure only via PR keywords | Verified |
| No bidirectional sync of assignees/labels/comments into `roadmap.json` (intentional v1) | Verified |

### 1.5 GitHub Project (CompoundGPID-progress)

| Finding | Class |
|---------|-------|
| Org project: GPID-WB/Projects/1, name CompoundGPID-progress | User-confirmed |
| Field name exactly `Status` with options: `Backlog`, `Ready`, `In progress`, `In review`, `Done` | User-confirmed |
| Other fields: Sub-issues progress, Priority, Size, Estimate, Start date, Target date | User-confirmed |
| Enabled built-in workflows: Auto-add sub-issues; Auto-add to project; Auto-close issue; Item added to project; Item closed; Pull request linked to issue; Pull request merged | User-confirmed |
| Disabled: Auto-archive; Code changes requested; Code review approved; Item reopened | User-confirmed |
| Field option IDs, project node ID, whether PRs become separate project items | **Unresolved** (token missing `read:project`) |
| Issue #98 `projectItems: []` via issue JSON — may mean not on board **or** insufficient project scope in response | Unresolved |

**Design preference (Inference, pending Stage 0A):** treat the **issueâ€™s** Project item as the canonical operational record; do not depend on PR project items unless Stage 0A proves PRs are the only reliable item.

### 1.6 Copilot coding agent

| Finding | Class |
|---------|-------|
| Copilot cloud agent enabled; appears as issue assignee; Actions approval for Copilot-initiated runs remains enabled | User-confirmed |
| Do not disable Actions approval during pilot | User-confirmed constraint |
| `mentionableUsers(query:"copilot")` returned empty; assignable users list is humans only | Verified (API surface incomplete for bots) |
| Exact assign API (REST vs GraphQL), bot login, required permissions, session/branch naming | **Unresolved** — Stage 0A must capture the assign mutation contract from GitHub docs + REST/GraphQL schema inspection only (no live assign); the live assign trial occurs in the Stage 1 manual pilot (Section 5.6 step 3) |
| Org installations observed (non-exhaustive): codecov, claude, devin-ai-integration, chatgpt-codex-connector, coderabbitai | Verified (not proof of Copilot agent install shape) |

### 1.7 Gaps (current)

1. No machine-verifiable **implementation-ready** contract on issues (only roadmap placeholders).
2. No dispatcher, concurrency lock, or dry-run assignment path.
  3. No Project sync beyond built-ins; custom lifecycle gaps unknown until Stage 0A field/workflow inspection with project scope.
4. `roadmap.json` â†” GitHub issue linkage **drift** in this worktree.
5. No issue forms/templates for readiness.
6. No security-separated automation identity for Project updates. **Correction**: requires two separate credentials (Copilot-assignment + Project-synchronization); no god-token.
7. No recovery runbook for abandoned Copilot sessions / stale PRs / status drift.
8. Zero-approval main protection is intentional for single maintainer, but **human merge inspection remains mandatory** (User-confirmed + Verified ruleset).

---

## Section 2 — Sources of truth

| State type | Canonical owner | Non-canonical / derived | Drift prevention |
|------------|-----------------|-------------------------|------------------|
| Strategic feature identity, grouping, milestone membership, feature status (`idea`/`planned`/`active`/`done`) | `roadmap.json` via `@cg-roadmap` | ROADMAP.md render; issue title/body summary | One-way links only; no automatic feature-status writes from Project/CI in v1 pipeline |
| Stable issue linkage | `features[].github` in `roadmap.json` — **canonical persistent linkage** once present | `compound-gpid-tracked` issue body markers (recovery + duplicate-detection identifiers only); `cg:roadmap` label | `/cg-issues` three-tier duplicate checks; marker alone does not constitute linkage; repair via `link` |
| Executable implementation contract | **GitHub issue body** (structured readiness block) once Ready | optional plan path under `.cg-docs/plans/` referenced by issue | Validator (Stage 2) is gate before dispatch; plan files remain design docs, not runtime locks |
| Operational execution status | GitHub Project field **`Status`** on the **issue item** | issue labels (avoid duplicating Status); PR â€œopen/draftâ€ | Prefer built-in Project workflows; reconciliation job only for unambiguous drift (Stage 4) |
| Implementation evidence | PR + required CI check runs + human review notes | Copilot session UI; local `tests/last-run.json` on runner | Ruleset required checks; `/cg-verify-pr` for diagnosis only |
| Batch / milestone progression | **Human decision** (chat + optional roadmap milestone status) | Project views filtered by milestone/date | **No** automatic milestone advancement; **no** `.github/active-milestone` file unless Stage 0A proves necessity |
| Local agent restart during human `/cg-work` | `.cg-docs/active-state/current.json` | — | Out of band for Copilot cloud path; do not overload for cloud dispatch |

### Explicit anti-patterns

- Do **not** make `roadmap.json` a transactional execution-status database (In progress / In review mirrors).
- Do **not** invent parallel state in labels + Project Status + roadmap feature status for the same fact.
- Do **not** treat PR merge alone as roadmap `done` without human roadmap update (existing one-way philosophy).

---

## Section 3 — Long-term target architecture

Smallest maintainable end state (architectural, not a build-everything mandate):

```text
[Human marks issue Ready]
        │
        ▼
[Readiness validator]──fail──► report; no assign
        │ pass
        ▼
[Dispatcher: single slot]──dry-run──► report only
        │ live
        ▼
[Assign Copilot via supported API]──fail──► remain Ready + failure comment
        │ success
        ▼
[Project Status â†’ In progress] (after assign success only)
        │
        ▼
[Copilot branch + PR linked to issue]
        │
        ▼
[Required CI on PR] + optional advisory review later
        │
        ▼
[Project Status â†’ In review] (built-in PR-linked workflow and/or thin sync)
        │
        ▼
[Human inspects diff + CI + acceptance] ──reject──► close/abandon runbook
        │ merge
        ▼
[Built-in PR merged / issue closed workflows â†’ Done]
        │
        ▼
[Human updates roadmap feature status when strategically done]
```

### Components

1. **Readiness contract** — structured Markdown sections in the issue (or issue form fields mapping to the same schema). Minimum fields:
   - `feature_id` (matches marker)
   - `outcome`
   - `acceptance_criteria` (checklist)
   - `scope` / `non_goals`
   - `verification_commands` (must include safe Pester/Python patterns where applicable)
   - `allowed_paths` / `prohibited_paths`
   - `dependencies_blockers`
   - `risk_class` (`low|medium|high`)
   - `human_review_notes`
   - `blocked_stop`
   - `ready_confirmation` (explicit human token / label)
2. **Readiness gate** — deterministic parser + checks: schema present; feature_id marker consistent; no open implementation PR for same issue; no active Copilot assignee; dependencies open/closed per GitHub native deps if used; prohibited paths non-empty for control-plane safety; dry-run report.
3. **Dispatcher** — `workflow_dispatch` with `issue_number` + `dry_run`; concurrency group size 1; revalidate immediately before assign; assign Copilot; only then set Status `In progress`; comment audit trail on issue.
4. **Copilot execution** — unchanged vendor agent; human approves Copilot-triggered Actions during pilot; PR must reference issue.
5. **CI gate** — existing required checks only; no new merge bot.
6. **Project sync** — maximize built-ins (item added, PR linked, PR merged, item closed). Add metadata-only Actions **only** for missing transitions (e.g. Readyâ†’In progress after assign if not automatic).
7. **Reconciliation** — scheduled or manual workflow: read issue+PR+Status; fix only **unambiguous** drift (e.g. merged+closed but Status not Done); comment and skip ambiguous cases.
8. **Limited batching** — human-selected set â‰¤ N (start N=1, raise only after evidence); still one assign slot unless pilot proves safe.
9. **Human milestone control** — batch boundaries and roadmap progression stay manual forever in this architecture.

### Status model recommendation

**Keep existing Status options.** Mapping:

| Status | Meaning in this pipeline |
|--------|--------------------------|
| Backlog | Not ready; placeholder OK |
| Ready | Human attested implementation-ready; validator green |
| In progress | Successfully assigned to Copilot (or human actively coding) |
| In review | PR open / awaiting human merge decision |
| Done | Issue closed completed (prefer via merge path) |

**Do not add** `Dispatching` / `Blocked` / `Needs triage` unless pilot shows recovery pain that labels + issue comments cannot solve more cheaply (**Inference**). Prefer label `cg:dispatch-failed` (optional, later) over new Status values.

---

## Section 4 — Staged implementation

## Phase 1: Stage 0A — Read-only verification

### 1. Read-only verification of GitHub and repository state

- **Requirements**: R1, R2, R3, R14, R16, R23, R24, R25, R26
- **Files**: one evidence report under `.cg-docs/work-reports/YYYY-MM-DD-stage-0a-verification.md`; **no** workflow files, issue edits, roadmap writes, Project field mutations, label changes, settings changes, or workflow modifications in this stage
- **Details**:
  1. Refresh `gh auth` with `read:project` only. (The `project` write scope is acquired later on the Stage 3/4 dedicated automation identity — not the PR CI token).
  2. Record Project node ID, Status field ID, option IDs for Backlog/Ready/In progress/In review/Done.
  3. Inspect each enabled Project workflow's exact action (especially **Pull request linked to issue** and **Pull request merged**): does it move issue item Status? Do PRs get separate items?
  4. Confirm Copilot assignee identity (login/node) via GitHub docs + REST/GraphQL schema inspection only; document the assign mutation contract and required permission. **Do not perform a live assign in Stage 0A** -- the sanctioned live trial is Stage 1 Section 5.6 step 3 (manual UI assign).
  5. Confirm "approve workflows from Copilot" remains enabled; screenshot or settings path in evidence log.
  6. **Roadmap drift audit**: verify linkage drift against `origin/main`, not only the planning worktree. Run `git fetch origin && git show origin/main:roadmap.json` and compare against live GitHub issues. Record all discrepancies between `features[].github` links in `origin/main` and issue body markers. (`git fetch origin` is permitted -- it updates local tracking refs only; "read-only" means no GitHub control-plane or repository-content mutations.)
  7. **GITHUB_TOKEN default permission audit**: read repository Actions settings (`gh api repos/{owner}/{repo}/actions/permissions/workflow`). Record the current `default_workflow_permissions` value. List every workflow file inheriting the default write permission (i.e. workflows that do **not** declare explicit `permissions:` at workflow or job level). Assess whether the default can later be changed to read-only without breaking existing workflows. Record in evidence report.
  8. Rank at least three potential pilot issues against Section 5 criteria. For each candidate, report:
     - **Required files**: which files the issue would need Copilot to modify
     - **Objective verification**: commands that deterministically pass/fail
     - **Subjective ambiguity**: any acceptance criterion that requires human judgment rather than command output
     - **Security/control-plane risk**: whether the change touches workflows, secrets, rulesets, or repo settings
     - **Estimated scope**: small (â‰¤3 files, <100 lines), medium, or large
     - **Recommendation**: recommended / acceptable / avoid, with rationale. Record issue #63's open/closed status as evidence so the R26 "including issue #63 if open" conditional is decidable; if #63 is open, include it among the ranked candidates (>=3).
  9. **Do not** select, modify, or assign any issue yet. Do not run `/cg-issues setup`. Do not repair roadmap linkage. Do not update any feature status. Stage 0A performs **no live GitHub mutations** of any kind (no assign, no label, no Project Status, no repository settings); `gh auth refresh` adding `read:project` is a local credential-scope change, not a repository mutation. The live Copilot assign trial is deferred to Stage 1 (Section 5.6 step 3).
- **Test Scenarios**: N/A (read-only)
- **Tests**: none
- **Acceptance criteria**: written evidence report **resolves** the must-resolve-in-Stage-0A items in §1.5–1.6 (must-resolve: Project node ID + Status field/option IDs; each enabled built-in Project workflow's exact action incl. whether PRs get separate items; GITHUB_TOKEN default_workflow_permissions + workflows inheriting default write; assign-API *shape* from docs/schema; **may defer** only if each deferral names the consuming stage and blocks that stage until resolved; the assign-API shape is not deferrable -- resolved in Stage 0A from docs, live trial in Stage 1); pilot candidate ranking has â‰¥3 entries and includes issue #63 when open (with #63 open/closed status recorded as evidence); GITHUB_TOKEN audit identifies workflows inheriting default write permission; roadmap drift is verified against `origin/main`.

## Phase 2: Stage 0B — Optional pre-pilot repairs

### 2. Pre-pilot repairs requiring explicit human approval

- **Requirements**: R3, R16, R24
- **Files**: issue body rewrites (via `gh`), `roadmap.json` writes (via `@cg-roadmap`), optional application of existing labels only (no new label definitions) — all require explicit human approval before execution
- **Details**:
  1. Present Stage 0A evidence report and drift findings to the human.
  2. For each proposed repair, wait for explicit human approval before executing:
     - **Issue linkage repair**: if Stage 0A found open issues with body markers but no `features[].github` link in `origin/main:roadmap.json`, propose running `/cg-issues setup` + selective `link` to restore canonical linkage. **Ownership clarification**: `features[].github` is the canonical persistent issue linkage once present; `compound-gpid-tracked` body markers are recovery and duplicate-detection identifiers used by `/cg-issues` three-tier duplicate prevention. The marker alone does not constitute linkage.
     - **Roadmap status repair**: if Stage 0A found features whose plan is `completed` but feature status is still `idea` (e.g. `github-issues-integration`), propose status update via `@cg-roadmap`.
     - **Pilot issue selection**: after human reviews the ranking from Stage 0A step 8, select one issue for the pilot. Rewrite its body from idea placeholder into full readiness contract per Section 5.4.
  3. Do **not** auto-execute any repair. Each mutation requires the human to approve individually.
  4. After repairs, verify the selected pilot issue is on Project CompoundGPID-progress and has Status set to **Ready** (human does this in UI).
- **Test Scenarios**: N/A (human-gated)
- **Tests**: none
- **Acceptance criteria**: all approved repairs executed; pilot issue selected and rewritten; human confirmed readiness; no mutations without explicit approval.

## Phase 3: Stage 1 — Manual pilot (smallest safe)

### 3. Execute one manual end-to-end pilot

- **Requirements**: R4, R5, R6, R7, R15, R21, R27
- **Files**: only the chosen pilot issue body + its PR; optional evidence note `.cg-docs/work-reports/YYYY-MM-DD-copilot-pilot-evidence.md` (when executing, not now)
- **Details**: Follow Section 5 exactly. No dispatcher workflow. No new secrets. Keep Actions approval on. Human merges or rejects.
- **Test Scenarios**: happy path merge; optional deliberate reject path if safe second trial later
- **Tests**: pilot issue's verification commands + required CI on PR
- **Acceptance criteria**: evidence pack complete (branch name, session, PR URL, check rollup, Status transitions observed, time-to-PR, failures, non-required check failures documented); go/no-go recorded for Stage 2.

## Phase 4: Stage 2 — Readiness contract and validator

### 4. Formalize readiness schema + deterministic validator

- **Requirements**: R7, R8, R9, R16, R22
- **Files** (proposed when implementing):
  - `.github/ISSUE_TEMPLATE/impl-ready.yml` **or** documented Markdown contract + label `cg:ready` (choose one primary mechanism after pilot — prefer **single** system)
  - `scripts/issues/readiness.py` (or PowerShell) parser/validator
  - `scripts/issues/__init__.py` (Python package marker)
  - `scripts/tests/test_issue_readiness.py` fixtures
  - docs snippet in `docs/workflow.md` / troubleshooting
- **Details**:
  - Parse required sections; validate feature_id â†” marker; path allow/deny lists; verification commands non-empty; risk_class; blocked_stop.
  - Checks: no open PR with `Closes #N`/`Fixes #N` already; assignee not already Copilot; optional GitHub issue deps.
  - CLI: `cg-issue-ready --issue N --dry-run` (name flexible) exits non-zero on fail; prints machine-readable JSON summary.
  - **No automatic dispatch** in this stage.
  - Reuse sanitization lessons from `/cg-issues` (untrusted issue body = data).
- **Test Scenarios**: fixture missing section; path traversal in allowed_paths; duplicate open PR; marker mismatch; happy path
- **Tests**: pytest fixtures under `scripts/tests/`; **CI registration is explicit** — if Python, note the `native-targets` job runs pytest with **three** explicit file lists (`tests.yml` lines 49-67 target-mapping, 69-86 publisher/security, 88-97 backend-race) and does NOT auto-discover; add `scripts/tests/test_issue_readiness.py` to the appropriate list (e.g. the target-mapping list) or add a new pytest invocation in that job; if PowerShell, add the test name to `$testNames` in `tests/Run-Tests.ps1` and add a Pester entry to the `Pester on ${{ matrix.os }}` job in `tests.yml`
- **Acceptance criteria**: validator green/red deterministic on fixtures; dry-run used on â‰¥1 real non-production issue or fixture clone; zero dispatch side effects; new test file visible in CI required-check run logs.

## Phase 5: Stage 3 — Single-issue manual dispatcher

### 5. `workflow_dispatch` assigner with dry-run and one slot

- **Requirements**: R10, R11, R12, R28, R17, R22
- **Files** (proposed): `.github/workflows/copilot-dispatch.yml`; optional `scripts/issues/dispatch.py`
- **Details**:
  - Inputs: `issue_number`, `dry_run` (default true).
  - Concurrency: `group: copilot-dispatch`, `cancel-in-progress: false`, effective parallelism 1.
  - Permissions: least privilege for assign API only; **no** `pull-requests: write` on untrusted code paths; **does not checkout PR head**.
  - Steps: checkout **default branch only** (validator scripts) â†’ run readiness validator â†’ re-check assignee/PR â†’ if dry_run, exit 0 with report â†’ else assign Copilot â†’ on success comment + set Project Status `In progress` (if token allows) â†’ on failure comment and leave Ready.
  - Secrets: dedicated Copilot-assignment credential **not** available to `pull_request` workflows that execute PR code; separate from Project-synchronization credential.
  - Idempotency: second dispatch on already-assigned issue is no-op success with explanation.
- **Test Scenarios**: dry-run; assign API 403; assign OK status update fail; duplicate dispatch
- **Tests**: unit tests with mocked HTTP; workflow `workflow_dispatch` dry-run on a throwaway issue
- **Acceptance criteria**: live assign succeeds once under human watch; Status In progress only after assign success; secrets not readable from PR workflows (`github` token permission review checklist signed).

## Phase 6: Stage 4 — Project synchronization and reconciliation

### 6. Fill lifecycle gaps without duplicating built-ins

- **Requirements**: R13, R18
- **Files** (proposed): `.github/workflows/project-reconcile.yml` (manual + optional low-frequency schedule)
- **Details**:
  - Inventory built-in coverage from Stage 0A evidence; implement **only missing** transitions.
  - Metadata-only: Project GraphQL mutations; never checkout PR code; never run tests from PR.
  - Reconciliation rules (examples — finalize after Stage 0A):
    - Issue closed+merged PR, Status â‰  Done â†’ set Done
    - Status In progress, no assignee, no open PR for >SLA â†’ comment `stale-dispatch` for human (do not auto-Backlog without policy)
    - Ambiguous (multiple open PRs) â†’ comment only
  - Prefer issue item; ignore or detach accidental PR items if they confuse rollup (**after evidence**).
- **Test Scenarios**: fixture graph states; permission denied; partial update
- **Tests**: mocked GraphQL; no production bulk mutate in CI
- **Acceptance criteria**: documented transition matrix â€œbuilt-in vs customâ€; reconcile dry-run report; zero secret exposure to PR CI.

## Phase 7: Stage 5 — Review enhancement

### 7. Advisory review and acceptance reporting

- **Requirements**: R19
- **Files** (proposed): optional PR workflow `copilot-review-advisory.yml` **or** prompt `/cg-review` checklist extension; issue comment template for acceptance criteria evaluation
- **Details**:
  - Advisory only — cannot replace required CI, human merge, or issue acceptance criteria.
  - Report each acceptance criterion pass/fail/unknown with evidence links.
  - Metrics log (manual spreadsheet or `.cg-docs/` note): rework rounds, CI fail rate, review minutes, false-ready rate.
  - Do **not** add survey-data regression fixtures.
- **Test Scenarios**: criteria checklist renders; unknown criteria flagged
- **Tests**: snapshot of report formatter if scripted
- **Acceptance criteria**: one pilot PR uses checklist; metrics template exists; no merge gating on advisory bot.

## Phase 8: Stage 6 — Limited batching

### 8. Human-selected batch with numeric cap

- **Requirements**: R20
- **Files**: dispatcher input `issue_numbers` (capped) **or** separate batch prompt; docs only until Stage 3 stable
- **Details**:
  - Cap N=2 or 3 only after Stage 3–5 evidence; default remains 1.
  - No cron autonomous dispatch; no predictive file-overlap engine.
  - Stopping rules: any P0 CI flake storm; >50% pilot fail; secret/permission incident; human overload.
  - Still no automatic roadmap/milestone advancement.
- **Test Scenarios**: cap enforcement; partial batch failure isolation
- **Tests**: unit test on cap parser
- **Acceptance criteria**: written go/no-go from metrics; if no-go, remain single-issue forever until revisit.

---

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Stage 0A is read-only verification; no control-plane implementation | User objective |
| R2 | Unresolved GitHub capabilities marked until verified | Quality requirements |
| R3 | Pilot is single-issue, manual assign, human merge | User objective |
| R4 | Keep Copilot Actions approval enabled during pilot | User-confirmed |
| R5 | Pilot issue must be objectively verifiable and avoid sensitive control-plane paths | User objective |
| R6 | Record evidence and failure modes before further automation | User objective |
| R7 | Dispatchable issues carry machine-verifiable execution contract | User objective |
| R8 | Single readiness mechanism (not overlapping form+labels+deps systems) | User objective |
| R9 | Validator supports dry-run and blocks dispatch on failure | User objective |
| R10 | Dispatcher is workflow_dispatch, issue-number input, dry-run default, concurrency 1 | User objective |
| R11 | Status â†’ In progress only after successful Copilot assignment | User objective |
| R12 | Credential separation: assign/Project secrets never on untrusted PR execution workflows | User objective |
| R28 | Separate credentials required: user-authenticated Copilot-assignment credential; GitHub App Project-synchronization credential. One god-token only if separation proven impossible | User objective |
| R13 | Prefer built-in Project workflows; custom sync is metadata-only | User objective |
| R14 | Existing required CI checks remain the merge gate | Verified ruleset |
| R15 | Zero required approvals retained; human still inspects every PR | User-confirmed + Verified |
| R16 | roadmap.json stays strategic; not transactional execution DB | User constraints + prior plan |
| R17 | Idempotent dispatch and explicit failure comments | User objective |
| R18 | Reconciliation handles unambiguous drift only; human for ambiguous | User objective |
| R19 | Advisory review never replaces CI/human/acceptance | User objective |
| R20 | Limited batching only after evidence; no auto milestone progression | User objective |
| R21 | Preserve Pester safety and `tests/Run-Tests.ps1` as canonical runner | Verified repo rules |
| R22 | Reuse `/cg-issues` marker and argv-safe gh patterns | Verified prior work |
| R23 | Roadmap drift findings must be verified against `origin/main`, not only the planning worktree | User objective |
| R24 | `features[].github` is canonical persistent issue linkage; `compound-gpid-tracked` markers are recovery/duplicate-detection only | User objective |
| R25 | Stage 0A must audit repository-level default `GITHUB_TOKEN` permissions and identify workflows inheriting default write | User objective |
| R26 | Stage 0A must rank â‰¥3 pilot candidates (including issue #63 if open) with required files, verification, ambiguity, risk, scope, recommendation | User objective |
| R27 | Pilot success requires all required checks green, non-required failures documented, no admin/ruleset bypass | User objective |

## Implementation Steps

Implementation steps are the Phase 1–8 stage entries above. Requirement mapping:

| Step | Requirements |
|------|--------------|
| 1 Stage 0A verification | R1, R2, R3, R14, R16, R23, R24, R25, R26 |
| 2 Stage 0B repairs | R1, R3, R16, R24 |
| 3 Stage 1 pilot | R4–R7, R15, R21, R27 |
| 4 Stage 2 readiness | R8–R10, R16, R22 |
| 5 Stage 3 dispatch | R11–R12, R28, R17, R22 |
| 6 Stage 4 project sync | R13, R18 |
| 7 Stage 5 review | R19 |
| 8 Stage 6 batching | R20 |

---

## Section 5 — Smallest safe pilot

### 5.1 Selection criteria (all required)

| # | Criterion |
|---|-----------|
| 1 | Linked (or linkable) to a real `feature_id` via marker |
| 2 | **Low risk**: touches â‰¤ few files; no secrets; no auth; no release packaging |
| 3 | **Objectively verifiable** with existing commands (Pester and/or pytest already in CI) |
| 4 | **Prohibited paths** include at least: `.github/workflows/**`, secrets, `roadmap.json` schema breaks, `tests/Run-Tests.ps1` safety model, branch rulesets |
| 5 | Not already assigned; no open implementation PR |
| 6 | Description rewritten from idea placeholder into full readiness contract |
| 7 | Preferred domains: docs typo/clarity in `docs/**`, pure test assertion fix, isolated script help text — **not** prompt permission model, not Pester runner, not link/unlink junction semantics unless already expert-owned |
| 8 | Avoid issues whose acceptance requires subjective â€œfeels betterâ€ UX only |

### 5.2 Anti-selection

Do **not** pilot: anything under `.github/workflows/`, credential docs with live values, multi-platform generator ownership changes, roadmap schema migrations, large skill rewrites, or issues still `Status: idea` without rewrite.

### 5.3 Recommended pilot shape (template — pick concrete issue in Stage 0B)

Because live issues are mostly idea placeholders (**Verified**), the pilot issue should be **rewritten** (or a new narrow issue opened and linked) rather than assigned as-is.

**Example shape** (illustrative, not a selected number):

- **Outcome**: Documentation page X states the five required status check names exactly as the ruleset.
- **Allowed paths**: `docs/**/*.md`, optionally `README.md`
- **Prohibited paths**: `.github/**`, `scripts/**`, `tests/**`, `roadmap.json`, `bin/**`, adapter trees
- **Verification**:
  - `rg "Native target Python gate on windows-2022" docs/`
  - `rg "PR title follows Conventional Commits" docs/`
  - Link-check not required for pilot merge if docs-only and ruleset does not require it
- **Risk**: low
- **Blocked-stop**: any change outside allowed paths; any workflow edit; failing required checks

Final issue number is chosen in Stage 0B after scanning open issues for the closest match **or** creating one deliberate pilot issue.

### 5.4 Rewrite checklist (issue body)

````markdown
<!-- compound-gpid-tracked: <feature-id> -->

## Ready for Copilot
- [x] Human attests implementation-ready on <date>

## Outcome
...

## Acceptance criteria
- [ ] ...

## Scope
...

## Non-goals
...

## Verification commands
```text
# exact commands
```

## Allowed paths
- `docs/foo.md`

## Prohibited paths
- `.github/workflows/**`
- `roadmap.json`
- `tests/Run-Tests.ps1`
- ...

## Dependencies / blockers
None

## Risk class
low

## Human review instructions
- Confirm diff touches only allowed paths
- Confirm acceptance criteria
- Merge manually; do not squash-skip PR title conventions

## Blocked-stop
- Copilot edits prohibited paths
- Required CI red after fix attempts exhausted
````

### 5.5 Expected Project transitions (observe; do not force-fit)

| Moment | Expected Status (hypothesis) | Class |
|--------|------------------------------|-------|
| Before pilot | Backlog or Ready | User-confirmed model |
| Human finished rewrite + Ready | Ready | Human |
| After assign Copilot | In progress | Hypothesis — verify if manual set needed |
| PR opened + linked | In review (or stays In progress) | **Unresolved** until built-in workflow inspected |
| PR merged + issue closed | Done | Hypothesis via built-ins |

Record **actual** transitions in evidence pack even if they differ.

### 5.6 Exact human actions

1. Select/create issue; rewrite contract; set Project Status **Ready** (UI).
2. Ensure issue on Project CompoundGPID-progress.
3. Manually assign **Copilot** coding agent (UI).
4. When Copilot requests Actions approval â†’ **approve** (do not disable the requirement).
5. Watch for branch + PR; ensure PR body references `Closes #N` or `Refs #N` per intent.
   5b. If PR body does **not** contain `Closes #N` or `Refs #N`, edit the PR body to add the appropriate reference before merge. Without it, the built-in "Pull request merged" workflow will not close the issue and Statusâ†’Done will not trigger automatically.
6. Wait for required checks:
   - Native target Python gate on macos-14
   - Native target Python gate on windows-2022
   - PR title follows Conventional Commits
   - Pester on macos-14
   - Pester on windows-2022
7. Human path review + PR template checklist.
8. Merge manually or close without merge; document why.
9. Confirm Project Status and issue state; note any drift.
10. **Do not** auto-advance roadmap milestone; optionally `@cg-roadmap` status update if strategically complete.

### 5.7 Expected Copilot actions

- Accept assignment; open working branch; push commits; open PR linked to issue; trigger Actions (subject to approval).

### 5.8 Evidence to collect

| ID | Evidence |
|----|----------|
| E1 | Issue URL + final body snapshot |
| E2 | Assignee identity string |
| E3 | Branch name pattern |
| E4 | PR URL + files changed |
| E5 | Check rollup JSON (`gh pr checks` / `statusCheckRollup`) |
| E6 | Actions approval events (timestamps) |
| E7 | Project Status timeline (screenshots or API after scope fix) |
| E8 | Wall-clock: assign â†’ PR â†’ green CI â†’ merge |
| E9 | Failures/retries/human nudges |
| E10 | Whether PR and issue are separate Project items |

### 5.9 Success criteria

- All **required** checks green on the PR before merge.
- Every triggered **non-required** check failure inspected and documented in the evidence pack (failure class, whether transient, whether Copilot-related).
- **No** administrator or ruleset bypass used during the pilot — the pilot must succeed (or fail) under the same constraints as any normal contributor.
- No prohibited path modifications.
- Acceptance criteria satisfied.
- Secrets unchanged; approval setting still enabled.
- Evidence pack filed.

### 5.10 Failure criteria

- Copilot cannot be assigned via available UI/API.
- PR never appears within agreed wait window (document window in Stage 0A, e.g. 24h).
- Edits outside allowlist.
- CI red for non-transient reasons tied to agent quality.
- Status model unusable without constant manual correction (**triggers Stage 4 design change**, not silent new Status spam).

### 5.11 Rollback / cleanup

- Unassign Copilot; close PR without merge; delete branch if safe; set Status back to Ready or Backlog; comment `pilot-aborted` with reason; leave roadmap feature status unchanged unless issue was disposable.

### 5.12 Decisions deferred until after pilot

- Exact assign API and automation identity (separate Copilot-assignment + Project-synchronization credentials).
- Whether Project built-ins already cover In review/Done.
- Whether issue form vs Markdown contract wins.
- Whether any new Status option is justified.
- Concurrency >1.
- Any roadmap writebacks from merge events.
- Advisory Copilot review enablement.

---

## Section 6 — Security and permissions matrix

| Identity / workflow | Trigger | Required permissions (target) | Credential type | Checkout | Execute untrusted PR code | Secrets available | Project access | Failure behavior |
|---------------------|---------|-------------------------------|-----------------|----------|---------------------------|-------------------|----------------|------------------|
| Human operator | UI / local `gh` | repo + project as needed | User OAuth/PAT | local | no | user env only | yes | human fixes |
| PR CI `tests.yml` / `commit-lint.yml` | `pull_request` / push | `contents: read` (tests); `pull-requests: read` (lint) | `GITHUB_TOKEN` | PR head (yes) | **yes** (tests) | **none** for dispatch/Project | **no** | fail check |
| Link-check / pages | path/schedule | contents read; pages write on deploy | `GITHUB_TOKEN` | default/PR | limited | none dispatch | no | fail/warn |
| Stage 3 dispatch | `workflow_dispatch` | issues: write; contents: read (default branch scripts only) | **Dedicated** Copilot-assignment credential (user-authenticated or narrow GitHub App) | **default branch only** | **no** | `COPILOT_ASSIGN_TOKEN` (name TBD); must **not** be available to PR-executing workflows | **no** (separate credential) | comment + exit non-zero; leave Ready |
| Stage 4 reconcile | `workflow_dispatch` / rare schedule | project write; issues: read; pull_requests: read | **Dedicated** GitHub App Project-synchronization credential | none or default branch metadata scripts | **no** | `PROJECT_SYNC_TOKEN` (name TBD); must **not** be available to PR-executing workflows | yes | alert comment; no loop storm |
| Copilot agent | issue assign | vendor-managed | Copilot cloud identity | its branch | its environment | vendor | n/a | human recovery |
| Future advisory review | `pull_request` | contents read, PRs read | `GITHUB_TOKEN` | PR head | yes (read) | **no** dispatch secrets | no | advisory comment only |

### Hard rules

1. **Never** pass dispatch/Project secrets to workflows that check out and execute PR code.
2. **Never** use a single god-token for CI + dispatch + Project. The plan requires separate credentials: a **user-authenticated Copilot-assignment credential** for Stage 3 dispatch and a **GitHub App Project-synchronization credential** for Stage 4 reconcile. Propose one combined credential only if Stage 0A capability verification proves separation impossible with current GitHub token models. Both `COPILOT_ASSIGN_TOKEN` and `PROJECT_SYNC_TOKEN` must be stored as **environment-protected** repository secrets, not plain repository secrets. Environment secrets are available only to jobs referencing the environment and only after required approval. No `pull_request` or `pull_request_target` workflow may reference the Copilot-dispatch or Project-synchronization environment. Environment protection is an additional gate, not the sole credential-isolation boundary (credential separation across tokens and workflow types remains the primary control).
3. Prefer GitHub App installation tokens with narrow permissions over classic PATs when Stage 0A confirms support for Copilot assign + Project mutations (**Unresolved** exact matrix).
4. Public repo: assume issue/PR bodies are untrusted input (injection lesson already documented).

---

## Section 7 — Recovery and idempotency

| Scenario | Detection | Recovery | Auto-retry? |
|----------|-----------|----------|-------------|
| Duplicate dispatch | assignee already Copilot or open agent PR | no-op; comment â€œalready dispatchedâ€ | no |
| Assign API fails | non-2xx | remain Ready; comment error class | no (human) |
| Assign OK, Status update fails | assign success + Project error | keep assignee; comment `status-drift`; reconcile later | optional single Status retry **only after re-reading Status** and confirming it is still `Backlog`/`Ready` (not already `In review`/`Done`); never overwrites a Status a built-in workflow already advanced; otherwise skip and rely on reconcile-later |
| PR never appears | timer exceeded | human unassign; Ready; document | no |
| Multiple PRs close same issue | the issue's `timelineEvents` cross-references (GitHub PR search has no `linked:issue` qualifier) | human choose survivor; close extras | no |
| PR closed without merge | PR state closed unmerged | Status â†’ Ready or Backlog per human; unassign | no |
| PR stale after other merge | conflicts / required checks fail behind main | human rebase request or close | no |
| Issue closed manually | issue state | Status Done via built-in or reconcile; cancel Copilot work | no |
| Project Status drifts | reconcile report | unambiguous auto-fix; else comment | limited |
| Reconcile workflow fails | Actions failure | alert maintainer; do not cascade | no |
| Credential expired | 401/403 | disable dispatch via environment protection; human rotate | no |
| Copilot edits prohibited paths | path filter on PR | request changes / close PR; tighten validator | no |
| Human merges with failing non-required checks | rollup | allowed if intentional; note in evidence | n/a |

Prefer **observable comments + human action** over hidden retry loops.

---

## Section 8 — Tests and acceptance criteria for automation

| Component | Test approach | Acceptance |
|-----------|---------------|------------|
| Readiness parser | Fixture issue bodies (good/bad) in `scripts/tests/` or `tests/` | 100% fixture pass; no network |
| Dry-run dispatch | Mock assign API; assert zero mutate calls when dry_run | enforced |
| API failure simulation | 403/404/500 mocks | non-zero exit + comment payload shaped |
| Idempotency | second dispatch fixture | no double comment spam (or single idempotent comment) |
| Permission review | workflow YAML review test: PR workflows lack dispatch secret env | static test |
| Project field lookup | unit test with recorded GraphQL fixtures (redact IDs in public if needed) | stable option name mapping |
| Status transition | table-driven allowed transitions | reject illegal jumps in helper |
| Duplicate PR / deps | fixtures | block dispatch |
| Secret exposure | `rg`/actionlint-style check that `pull_request` jobs do not reference dispatch secrets | CI gate when workflows exist |
| E2E | **one** controlled issue on a fork or dedicated pilot issue; dry-run then live under human watch | checklist signed |

**Local runner rules**: any new Pester file must be registered in `tests/Run-Tests.ps1` `$testNames`; agents must use safe runner patterns (never `Invoke-Pester tests/`).

---

## Section 9 — Decisions requiring human confirmation

1. **Pilot issue identity**: rewrite existing open issue vs open a disposable pilot issue.
2. **Automation identity**: separate credentials: user-authenticated Copilot-assignment + GitHub App Project-synchronization (after Stage 0A API proof). One god-token only if separation proven impossible.
3. **Readiness representation**: issue form fields vs structured Markdown + single `cg:ready` label (pick one primary).
4. **Whether Project write is required in Stage 3** or human continues to set In progress during early automation.
5. **SLA for â€œPR never appearsâ€** (suggested default 24h — confirm).
6. **Whether merged PR should ever auto-update `roadmap.json` feature status** (default **no**; confirm remains no).
7. **Org policy**: who may run `workflow_dispatch` dispatch (maintainer only via environment protection). Secret storage: dispatch/Project credentials live as environment-protected secrets (environment-available-only-after-approval; no PR workflow may reference the environment; protection is an additional gate, not the sole isolation boundary).
8. **Charter focus tradeoff**: schedule this work vs Token Efficiency priority.

Ordinary choices already answered by the repo (required check names, Pester runner, one-way issues linkage, zero approvals, no auto milestone) are **not** re-listed.

---

## Section 10 — Explicitly deferred machinery

Do **not** build until evidence justifies:

- Scheduled / cron autonomous dispatch
- Automatic milestone or batch progression
- Unlimited concurrency or predictive file-overlap gates
- `.github/active-milestone` or duplicate active-batch files
- Custom implementer agents replacing Copilot cloud agent
- Disabling Copilot Actions approval
- Automatic `roadmap.json` status writes from Project/CI
- New Project Status values without observed recovery need
- Bidirectional issueâ†”roadmap state sync
- Survey-data regression fixtures
- Merge bots / auto-merge
- Multi-issue speculative planning agents

---

## Testing Strategy

- **Now (this plan)**: artifact validation only (`cg-render-artifact`).
- **Stage 0A**: manual evidence; GITHUB_TOKEN audit; roadmap drift verified against `origin/main`.
- **Stage 0B**: human-approved repairs only.
- **Stage 1**: required CI on pilot PR; non-required failures documented.
- **Stage 2+**: pytest fixtures for readiness/dispatch helpers; Pester prompt/schema tests if prompts change; register new Pester files in `Run-Tests.ps1`.
- **Never**: full-suite `Invoke-Pester tests/` directory form; never expose dispatch secrets to PR-executing jobs.

## Documentation Checklist

- [ ] Stage 0A evidence report path agreed
- [ ] Stage 0B repair approvals documented
- [ ] After Stage 2: document readiness contract in `docs/workflow.md` + troubleshooting
- [ ] After Stage 3: document dispatch inputs, dry-run, permissions
- [ ] After Stage 4: transition matrix built-in vs custom
- [ ] CONTRIBUTING / PR template only if human checklist gains Copilot-specific items

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Copilot assign API differs from assumptions | Stage 0A verification + manual pilot before coding dispatcher |
| Project built-ins already move Status — custom sync races | Stage 0A inventory first; implement only gaps |
| Roadmap â†” issue drift confuses feature_id | Stage 0A drift audit against `origin/main` + Stage 0B `/cg-issues setup` + link repair before pilot |
| Secret leakage via PR CI | hard separation matrix; static tests |
| Pilot issue too vague â†’ false negative on Copilot quality | rewrite to full contract; path allowlists |
| Zero-approval merges bad PR | mandatory human path review; keep required CI strict |
| Scope creep to full autonomous factory | Section 10 + deviation-policy `ask` |
| Pester misuse in new tests | cg-skill-pester-safety + Run-Tests registration |
| Public issue body injection | treat as untrusted; argv-safe; fence data |

## Out of Scope

- Implementing Stages 2–6 in this planning session
- Creating workflows, apps, tokens, labels, templates now
- Changing GitHub org/repo settings now
- Mutating `roadmap.json` as part of saving this plan
- Replacing Copilot with in-house coding agents
- Stage 0B repairs or Stage 1 pilot without explicit human approval at the preceding stage gate
- Token-efficiency charter deliverables

## Completion Contract

### Outcome

A durable master plan documents verified current-state findings, sources of truth, long-term architecture, and staged implementation (0–6) for a controlled Copilot issue-implementation pipeline on `GPID-WB/compound-gpid`, with Stage 0A (read-only verification) as the only authorized action upon plan completion. Stage 0B requires explicit human approval after reviewing the Stage 0A evidence report; Stage 1 (smallest safe manual pilot) requires another explicit human approval after Stage 0B. No automation is implemented by completing this plan alone.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Plan file exists under `.cg-docs/plans/` with required frontmatter and all 10 architecture sections | `.cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md` | yes |
| V2 | 1 | Section 1 classifies claims as verified / inference / unresolved; cites exact workflow job names and ruleset checks | Plan §1 | yes |
| V3 | 1 | Sources-of-truth table assigns one owner per state type; no competing transactional DB on `roadmap.json` by default | Plan §2 | yes |
| V4 | 1 | Stages 0A–6 are independently implementable; Stage 0A is read-only; Stage 0B is human-gated; Stage 1 is manual-only | Plan §4 | yes |
| V5 | 1 | Smallest safe pilot specifies selection criteria, allowed/forbidden paths, verification commands, human actions, success/fail/rollback | Plan §5 | yes |
| V6 | 1 | Security matrix covers dispatch vs Project update vs PR CI credentials and no secret exposure to untrusted PR code | Plan §6 | yes |
| V7 | 1 | Recovery/idempotency covers duplicate dispatch, orphan assignment, missing PR, status drift, credential failure | Plan §7 | yes |
| V8 | final | Plan passes artifact validation (`cg-render-artifact`) | CLI exit 0 | yes |
| V9 | final | Next action is Stage 0A read-only verification; Stage 0B and Stage 1 require separate explicit human approvals | Plan handoff | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No implementation outside the plan artifact | Diff only under `.cg-docs/plans/` |
| C2 | 1 | Do not invent GitHub API/permission/field-ID claims | Unverified items marked unresolved |
| C3 | 1 | Preserve Pester runner safety and existing required checks | Named checks match ruleset |
| C4 | 1 | Human retains merge and milestone control | No auto-merge / auto-milestone advancement |
| C5 | 1 | Existing Project Status options preferred | §3 recommendation |
| C6 | 1 | Reuse built-in Project workflows before custom Actions | §1 + §4 Stage 4 |
| C7 | 1 | Stage 0A performs no live GitHub mutations; assign-API shape from docs only | Plan §1.6 + Phase 1 Step 4/9 |

### Boundaries

- **Allowed**: This plan artifact; executing Stage 0A (read-only verification); optional roadmap link via `@cg-roadmap` after user asks.
- **Out of scope**: See Out of Scope section; Stages 2–6 implementation; Stage 0B or Stage 1 without explicit human approval at the preceding stage; GitHub settings mutation during planning.

### Iteration Policy

1. Prefer simpler mechanism when governance is equivalent.
2. Defer automation until pilot evidence justifies it.
3. On deviation (`ask`): pause for human decision; record impact.
4. Unresolved external capabilities stay marked until Stage 0A verifies them.
5. Do not treat completion of this master plan as authorization for Stages 0B, 1, or 2–6.

### Blocked-Stop Conditions

- Cannot write/validate plan artifact under `.cg-docs/plans/`.
- User rejects contract with no alternative.
- Implementation of automation requested under planning-only authority without a new explicit decision.
- Required verification cannot be run for later stages through safe runners.
- Protected boundary must be crossed (secrets in PR CI, disable approval, auto-merge).

---

## Next action (only)

**Prepare and execute Stage 0A read-only verification** (evidence report, roadmap drift against `origin/main`, GITHUB_TOKEN audit, pilot candidate ranking including issue #63), Stage 0B requires explicit human approval after reviewing the Stage 0A evidence report; Stage 1 requires another explicit human approval after Stage 0B. Do not implement dispatcher/validator workflows until pilot evidence is filed and a human go/no-go is recorded.
