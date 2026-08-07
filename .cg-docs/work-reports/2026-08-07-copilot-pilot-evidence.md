---
date: 2026-08-07
title: "Stage 1 — Manual Copilot pilot: evidence pack and go/no-go"
type: evidence
plan: ".cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md"
phase: 3
scope: "Stage 1 manual pilot evidence closeout; GO/NO-GO for Stage 2; no Stage 2 implementation"
---

# Stage 1 — Manual Copilot pilot: evidence pack and go/no-go

This evidence pack is the Phase 3 (Stage 1) closeout for the controlled GitHub
Copilot issue-implementation pipeline (plan v2). It records the verified final
live GitHub state of pilot issue **#127** and pull request **#131**, classifies
each Section 5.8 evidence item, records timing data, evaluates every Section 5.9
success criterion, and records a formal `GO` / `NO-GO` for Stage 2.

**Scope guard**: the pilot already completed. This run performs **no live
mutations** (no reassignment, no issue/PR edits, no Project writes, no
Stage 2 implementation). All repository writes are limited to this evidence
pack, the plan metadata, the execution report, active-state, and the plan's
generated view, per `/cg-work` permissions.

> **Filing status**: this evidence pack is created in the current branch
> (`issue-implementation-pipeline-from-phase-3`) and becomes canonically filed
> in `.cg-docs/work-reports/` only once the Stage 1 closeout PR merges into
> `main`. The closeout PR is PR #132 (this PR); it is distinct from PR #131,
> the pilot implementation PR, which is already merged.

## Evidence classification legend

| Tag | Meaning |
|-----|---------|
| **API-verified** | Confirmed against the live GitHub REST/GraphQL API on 2026-08-07 during this closeout |
| **Operator-confirmed** | Stated by the operator/human during the pilot or in prior-run records; not re-derivable from the API |
| **Not retrievable** | No API surface exposes an exact value (documented explicitly; no value invented) |

> **Cross-map to the plan's §1 legend**: `API-verified` ≡ plan/Stage-0A
> "Verified"; `Operator-confirmed` ≡ plan "User-confirmed"; `Not retrievable`
> ≡ plan "Unresolved" that could not be resolved this closeout. This pack uses
> the operational vocabulary because it classifies live-pilot evidence
> (timestamps, approvals, API fields) rather than planning claims.

---

## 1. Pilot identity

| Fact | Value | Class |
|------|-------|-------|
| Pilot issue | #127 — "Make automatic artifact HTML publication opt-in by default" | API-verified |
| Issue final state | `closed`, `state_reason: completed` | API-verified |
| Issue final body | `<!-- compound-gpid-tracked: artifact-html-opt-in-default -->`; full §5.4 readiness contract; **all four** `Ready for Copilot` boxes checked | API-verified |
| Assignees | `Copilot` and `randrescastaneda` | API-verified |
| Copilot config | **GPT-5.6 Luna, X-High reasoning** | **Operator-confirmed** (industry UI setting; no public API surface) |
| Branch | `copilot/make-html-publication-opt-in-default` | API-verified |
| PR | #131 — `feat(artifact-views): make automatic HTML publication opt-in by default` | API-verified |
| PR author | `app/copilot-swe-agent` (Copilot) | API-verified |
| PR state | `MERGED`; merged by `randrescastaneda` | API-verified |
| Merge commit | `fc4ed30027f702c4adffd7e742f8be416da39576` | API-verified (two-parent merge; matches known fact) |
| Changed files | **17** (`additions: 257`, `deletions: 59`) | API-verified |
| Project item | Issue #127 on CompoundGPID-progress; **Status = Done** (`98236657`) | API-verified (GraphQL) |

All four `Ready` boxes checked include ``Project Status has been changed from
`Backlog` to `Ready` ``, so the readiness gate was fully attested before
assignment.

---

## 2. Evidence E1–E10 (Section 5.8)

### E1 — Issue URL + final body snapshot
- **Class**: API-verified
- Issue: <https://github.com/GPID-WB/compound-gpid/issues/127>, closed
  `2026-08-07T13:49:56Z` with `state_reason: completed`.
- Final body is the full readiness contract (marker, summary, roadmap linkage,
  all four `Ready` boxes, outcome, 20 acceptance-criteria items, scope,
  non-goals, allowed/prohibited paths, required tests, verification commands,
  risk `low`, human-review instructions, blocked-stop conditions). Snapshot
  captured from the live issue body during this closeout.

### E2 — Assignee identity string
- **Class**: API-verified (identity); Copilot model config is operator-confirmed.
- Issue #127 timeline `assigned` events at `2026-08-07T12:00:01Z` by actor
  `randrescastaneda` assigned **`Copilot`** (and `randrescastaneda`).
- Final assignees: `Copilot`, `randrescastaneda`.
- PR #131 author: `app/copilot-swe-agent` (Copilot's app login).
- The specific Copilot configuration **GPT-5.6 Luna / X-High reasoning** is an
  industry UI setting and cannot be re-verified via the public API; it is
  recorded as operator-confirmed.

### E3 — Branch name pattern
- **Class**: API-verified
- PR #131 `headRefName`: `copilot/make-html-publication-opt-in-default`
  (matches the known fact). First commit on the branch: `615026c` "Initial
  plan", authored `2026-08-07T12:00:04Z` by `copilot-swe-agent[bot]`.
- Branch was deleted after merge (`head_ref_deleted` `13:50:02Z`), a normal
  cleanup.

### E4 — PR URL + files changed
- **Class**: API-verified
- PR: <https://github.com/GPID-WB/compound-gpid/pull/131>
- Exactly **17** files changed. Filenames:
  1. `.agents/.compound-gpid-generated.json`
  2. `.agents/shared/artifact-view.contract.md`
  3. `.claude/.compound-gpid-generated.json`
  4. `.claude/shared/artifact-view.contract.md`
  5. `.github/shared/artifact-view.contract.md`
  6. `.kilo/.compound-gpid-generated.json`
  7. `.kilo/shared/artifact-view.contract.md`
  8. `.opencode/.compound-gpid-generated.json`
  9. `.opencode/shared/artifact-view.contract.md`
  10. `docs/configuration/index.md`
  11. `docs/reference.md`
  12. `docs/troubleshooting.md`
  13. `docs/workflow.md`
  14. `scripts/artifact_views/config.py`
  15. `scripts/artifact_views/tests/test_cli.py`
  16. `scripts/artifact_views/tests/test_config.py`
  17. `scripts/artifact_views/tests/test_generic_cli.py`
- **13 files** were explicitly listed in the issue #127 allowed-path list:
  the core resolver (`scripts/artifact_views/config.py`), its three changed
  test files (`test_config.py`, `test_cli.py`, `test_generic_cli.py`), the
  four docs (`docs/configuration/index.md`, `docs/workflow.md`,
  `docs/reference.md`, `docs/troubleshooting.md`), the canonical contract
  (`.github/shared/artifact-view.contract.md`), and the four generated
  platform contract copies (`.agents`/`.claude`/`.kilo`/`.opencode`
  `shared/artifact-view.contract.md`).
- The four **`.compound-gpid-generated.json` manifests were not** in the
  issue's original allowed-path list; they were subsequently authorized by the
  documented human target-generation-closure decision (operator comment
  `2026-08-07T13:37:20Z` — SHA-256 metadata updates only) before the PR was
  marked ready.
- **No prohibited path** (`.github/workflows/**`, prompts/agents/skills,
  `roadmap.json`, `tests/Run-Tests.ps1`, secrets, repo settings) was touched.

### E5 — Check rollup JSON (`statusCheckRollup`)
- **Class**: API-verified
- Full `statusCheckRollup` captured via GraphQL during closeout. Summary:

| Check | Status | First seen | Conclusion |
|-------|--------|-----------|------------|
| Browser evidence manifest tests | COMPLETED | 12:40:11Z | SUCCESS |
| Docs staleness check | COMPLETED | 12:40:12Z | SUCCESS |
| Link Check | COMPLETED | 12:40:10Z | SUCCESS |
| **Native target Python gate on macos-14** | COMPLETED | 12:40:11Z | SUCCESS |
| **Native target Python gate on windows-2022** | COMPLETED | 12:40:12Z | SUCCESS |
| **Pester on macos-14** | COMPLETED | 12:40:17Z | SUCCESS |
| **Pester on windows-2022** | COMPLETED | 12:40:11Z | SUCCESS |
| **PR title follows Conventional Commits** | COMPLETED | 12:40 (fail x3) → 13:08/13:09 (pass) | SUCCESS (final) |

- Required ruleset contexts verified still active and matching the plan:
  `Protect main` ruleset id `16657602`, enforcement `active`, required checks =
  the five bolded rows above, `strict_required_status_checks_policy: true`,
  `required_approving_review_count: 0`, merge methods merge+rebase. Bypass
  actors: only `RepositoryRole` `actor_id 5` (org admin), `bypass_mode: always`.

### E6 — Actions approval events (timestamps)
- **Approval-safeguard status**: **operator-confirmed**, supported by behavioral
  API evidence.
- **Exact approval timestamp**: **not retrievable** — no API approval-event
  endpoint exists; no value invented.
- Runs were **created** by `Copilot` (`actor`) between **12:06:17Z–12:09:18Z**
  but **started** only at **12:40:05Z–12:40:06Z** with
  `triggering_actor: randrescastaneda` (example run `31176801451`). The ~34
  minute created→started gap is the Actions-approval waiting window for
  Copilot-initiated runs, with the human as the triggering actor.
- The exact click/approval moment is inferred to lie within 12:06–12:40Z using
  run `created_at` → `run_started_at`.
- The "approve Copilot-initiated workflow runs" safeguard is
  **operator-confirmed enabled**, with the observed run create→start delay and
  human `triggering_actor` as supporting behavioral evidence. The
  `can_approve_pull_request_reviews` API setting is **not used as evidence**
  here because it concerns a different capability (approving pull-request
  reviews via the API), not Copilot-initiated workflow-run approval.

### E7 — Project Status timeline
- **Class**: timestamps API-verified; intermediate option values
  operator-confirmed; final value API-verified.
- `project_v2_item_status_changed` events on issue #127 (all UTC):

| Timestamp | Actor | Lifecycle position |
|-----------|-------|--------------------|
| 2026-08-06T14:59:04Z | github-project-automation[bot] | Added to project (initial) |
| 2026-08-07T11:44:00Z | randrescastaneda | Human set **Ready** (after PR #128 merge 11:38:17Z) |
| 2026-08-07T12:00:10Z | github-project-automation[bot] | **In progress** (after assignment) |
| 2026-08-07T13:45:29Z | randrescastaneda | Human set **In review** |
| 2026-08-07T13:49:57Z | github-project-automation[bot] | **Done** (after issue close) |

- Final Status confirmed **`Done`** via GraphQL
  (`fieldValueByName(name:"Status").name == "Done"`, option `98236657`) on the
  issue item.
- The REST timeline event payload does not carry the target option value for
  the intermediate transitions; the Ready → In progress → human-set In review →
  automatic Done sequence is operator-confirmed and consistent with the
  timestamps. **Actual lifecycle matches the known fact**.
- GraphQL also confirms the Status field options are exactly:
  `Backlog`, `Ready`, `In progress`, `In review`, `Done` (no new Status added).

### E8 — Wall-clock assign → PR → green CI → merge
- **Class**: API-verified (computed from API timestamps)

| Moment | Timestamp (UTC) |
|--------|-----------------|
| Copilot assigned | 2026-08-07T12:00:01Z |
| PR #131 created | 2026-08-07T12:00:07Z |
| Actions approval granted (inferred) | ~12:06–12:40Z (run start 12:40:05Z) |
| All non-title required checks green | 12:40:11Z–12:42:32Z |
| CC lint green (after title fix) | 13:08:27Z / 13:09:55Z |
| Focused verification reported | 2026-08-07T13:39:12Z |
| Human approval (APPROVED review) | 2026-08-07T13:49:42Z |
| **Merge** | **2026-08-07T13:49:54Z** |
| Issue closed (completed) | 2026-08-07T13:49:56Z |
| Project Status → Done | 2026-08-07T13:49:57Z |
| Branch deleted | 2026-08-07T13:50:02Z |

- Assign → PR: **6 seconds** (12:00:01 → 12:00:07).
- PR → merge: **~1 h 49 m** including the ~34 min Actions-approval wait, the
  Conventional-Commits title fix, focused verification, and human approval.

### E9 — Failures / retries / human nudges
- **Class**: API-verified (rollup + PR timeline + comments)
- **Conventional Commits lint failed 3× at 12:40:12Z–12:40:16Z** on the
  original PR title (`[WIP] Make automatic artifact HTML publication opt-in by
  default`, later `Make automatic artifact HTML publication opt-in by
  default`) — a required check red for title, not code.
- Human corrected the title to the conventional `feat(artifact-views): ...` at
  **13:07:43Z** (`renamed` event by `randrescastaneda`); CC lint then passed at
  **13:08:22-27Z** and **13:09:46-55Z**.
- Human nudges (comments): operator `randrescastaneda` at **13:37:20Z**
  approved the four generated manifest updates as target-generation closure and
  requested the exact focused verification command; Copilot replied at
  **13:39:12Z** reporting `58 passed in 0.70s` and confirming exactly 17 files.
- Second Copilot work session ran 13:37:38Z–13:39:42Z (focused verification);
  `ready_for_review` at 13:45:08Z.
- **No failures were Copilot-code-quality related.** Required checks were red
  only because of the PR title and went green after the human-titled fix.

### E10 — Whether PR and issue are separate Project items
- **Class**: API-verified
- GraphQL unfiltered item dump of the project returned **zero
  `PullRequest`-typed items** (44 Issue items; no PR items among them). PR #131
  is **NOT a separate project item** on CompoundGPID-progress.
- The **issue** is the sole project item for the pilot and is the canonical
  record that reached `Done` (consistent with plan §1.5 design preference; the
  built-in workflows plus the merge closed the issue → Status `Done`).

---

## 3. Timing data (as available / limitations)

| Data point | Value | Class |
|------------|-------|-------|
| PR created | 2026-08-07T12:00:07Z | API-verified (known fact matches) |
| Focused verification reported | 2026-08-07T13:39:12Z | API-verified (known fact matches) |
| Human approval | 2026-08-07T13:49:42Z | API-verified (APPROVED review `submittedAt`) |
| Merge | 2026-08-07T13:49:54Z | API-verified (known fact matches) |
| Assignment | 2026-08-07T12:00:01Z | API-verified (issue `assigned` event) |
| Actions-approval | inferred ~12:06–12:40Z | **Not retrievable precisely** — no API approval-event endpoint; inferred from run create→start gap |
| Green CI | 12:42:32Z (non-title required checks) → 13:09:55Z (all required incl. CC lint) | API-verified (check completions) |

No other timestamp is fabricated. All values above come from the live API
during this closeout.

---

## 4. Known pilot facts — independent verification

| Known fact | Verification | Class |
|------------|--------------|-------|
| Issue #127 closed as completed; Project Status `Done` | `state_reason: completed`; GraphQL Status `Done` | API-verified |
| Copilot config GPT-5.6 Luna, X-High reasoning | recorded as configured | **Operator-confirmed** (not API-recoverable) |
| Branch `copilot/make-html-publication-opt-in-default` | PR #131 head ref | API-verified |
| PR #131 merged normally into `main` | `MERGED`, two-parent merge commit, base `main` | API-verified |
| Merge commit `fc4ed30027f702c4adffd7e742f8be416da39576` | `mergeCommit.oid` + `git cat-file` (two parents: main tip + PR head) | API-verified |
| Exactly 17 changed files | `changedFiles: 17` + files list | API-verified |
| Human approved the four generated manifest updates as target-generation closure | **Operator-confirmed decision**; the API verifies the existence and content of the comment record (`randrescastaneda`, 13:37:20Z, approving exactly the four `.compound-gpid-generated.json` updates, SHA-256-only) | Operator-confirmed decision; API-verified comment record |
| Focused verification `58 passed in 0.70s` | **Copilot-reported result accepted by the operator**; the API verifies the comment record (Copilot, 13:39:12Z, quoting the exact command result) — not independent execution of the command | Agent-reported, operator-accepted; API-verified comment record |
| All required and triggered final checks passed | Rollup: all required green; non-required (browser, docs staleness, link-check) SUCCESS | API-verified |
| Earlier Conventional-Commits failures caused only by original PR title; passed after title corrected | 3× FAILURE at 12:40 on pre-fix title; SUCCESS after 13:07:43Z rename | API-verified |
| Human formally approved and manually merged | `APPROVED` review 13:49:42Z + `mergedAt` 13:49:54Z by `randrescastaneda`; `autoMergeRequest: null` | API-verified |
| No admin/ruleset bypass, secret change, workflow change, auto-merge, disabled approval safeguard | **Operator-confirmed conclusion supported by API evidence**: file list shows no `.github/workflows/**` or settings/secret files changed; ruleset unchanged during pilot (`updated_at` 2026-08-04 pre-pilot); `autoMergeRequest: null`; approval gate observed. "No bypass used" and "secrets unchanged" are operator-confirmed conclusions — the API/file-list evidence supports but does not by itself prove them | Operator-confirmed (supported by API evidence) |
| Actual Project lifecycle Ready → In progress → human-set In review → automatic Done | Event timeline (E7) | API-verified + sequence operator-confirmed |
| PR #131 separate Project item? | **No** (E10; zero PR items on project) | API-verified |

---

## 5. Success criteria evaluation (Section 5.9)

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | All **required** checks green on the PR before merge | **PASS** | Five ruleset-required checks SUCCESS; CC lint green after title fix before merge (13:09:55Z < 13:49:54Z) |
| 2 | Every triggered **non-required** failure inspected and documented | **PASS** | Non-required (browser evidence, docs staleness, link-check) all SUCCESS — nothing failed to inspect; the only red check (CC lint) is required and documented (title fix) |
| 3 | **No** administrator or ruleset bypass used | **PASS** | **Operator-confirmed, supported by API evidence**: merge is a normal two-parent merge under the active `Protect main` ruleset with required checks green; no `.github/workflows/**`/settings/secret files changed; `autoMergeRequest: null`. "No bypass used" is an operator-confirmed conclusion — the API evidence supports but does not by itself prove it |
| 4 | No prohibited path modifications | **PASS** | 13 files are within the issue's explicitly listed allowed paths, and the four generated `.compound-gpid-generated.json` manifests were authorized by the documented human target-generation-closure decision (operator comment 13:37:20Z) before the PR was marked ready; none under prohibited paths (workflows, prompts/agents/skills, roadmap.json, Run-Tests.ps1, secrets, settings) |
| 5 | Acceptance criteria satisfied | **PASS** | Operator-approved target-generation closure + focused suite result `58 passed in 0.70s` (agent-reported, operator-accepted; API verifies the comment record, not independent execution) + docs/contracts updated consistently; human path review/approval recorded |
| 6 | Secrets unchanged; approval setting still enabled | **PASS** (with note) | **Operator-confirmed, supported by API evidence**: no secret files changed; run create→start delay + human `triggering_actor` is behavioral evidence of the approval gate. **Note**: live `default_workflow_permissions` now reports `read` — an intentional pre-pilot change (see notes below), not unexplained drift |
| 7 | Evidence pack filed | **PASS** | **Branch-local closeout artifact**: this evidence pack is complete on this branch; it becomes canonically filed on `main` when the Stage 1 closeout PR (PR #132 — this PR, not the pilot implementation PR #131) merges |

### Accepted-observation notes
- **`default_workflow_permissions` `write` → `read` (live)** — Recorded in the
  continuity handoff as an **intentional change made before the pilot**
  (operator-confirmed). The exact timestamp and actor are **not retrievable**
  from available API surfaces, but this is **not unexplained drift** and is
  therefore **not** a Stage 2 residual decision. It is a hardening (read-only
  default), consistent with the plan's Stage 0A §1.3 recommendation to move the
  default to `read`.
- **Copilot model config** (GPT-5.6 Luna, X-High) is operator-confirmed only
  (no public API surface).

---

## 6. Failure criteria check (Section 5.10) — all absent

| Failure criterion | Observed? |
|-------------------|-----------|
| Copilot could not be assigned | No — assigned 12:00:01Z |
| PR never appeared within window | No — PR in 6 s |
| Edits outside allowlist | No |
| CI red for non-transient agent-quality reasons | No — the only red (CC lint) was title-caused and fixed |
| Status model unusable without constant manual correction | No — built-ins covered transitions; human set only Ready and In review |

---

## 7. GO / NO-GO for Stage 2

**Verdict: GO**

All seven Stage 1 success criteria pass. The GO verdict relies on the
documented combination of API-verified evidence, operator-confirmed
conclusions, agent-reported results, and non-retrievable limitations recorded
above — **not exclusively on API-verified evidence** — with no blocking gap.
The pilot demonstrated, under the same constraints as any contributor:

- a fully readiness-attested issue (#127, 4/4 boxes);
- successful manual Copilot assignment and normal branch/PR creation;
- required checks green after a benign title-only fix;
- human review + formal approval + manual merge with no auto-merge and no
  bypass;
- automatic Project `Done` via built-in behavior with the issue as the sole
  project item;
- no prohibited edits, and (operator-confirmed, supported by API evidence) no
  secret/workflow/settings changes by the pilot, with the Actions-approval
  safeguard intact.

Proceeding to **Stage 2 (readiness contract + deterministic validator)** is
justified by this evidence. Stage 2 remains an explicit future phase per the
plan; this document does **not** implement it.

### Residual operational lesson for the later dispatcher stage
- **Conventional-Commits title compliance**: Copilot's initial PR title did not
  satisfy the Conventional Commits required check and required **one human
  rename** (`[WIP] Make ...` → `feat(artifact-views): ...`) before the required
  check passed. This does **not** block Stage 2's readiness validator, but it
  must be addressed (e.g., explicit conventional-title instruction to Copilot,
  or a dispatcher-side guard) before claiming unattended dispatch.
- Confirm exact configuration of the "approve Copilot-initiated workflow runs"
  toggle in the settings pane (operator UI; no API surface).
- Exact per-approval event timestamps — no API surface; keep run
  create→start gap as the proxy.

---

## 8. Files touched by this closeout

- `.cg-docs/work-reports/2026-08-07-copilot-pilot-evidence.md` (this pack)
- `.cg-docs/work-reports/2026-08-06-copilot-issue-implementation-pipeline-v2.md`
  (execution report: Run 3 section appended)
- `.cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md`
  (frontmatter metadata: `completed-phases`, `current-phase`)
- `.cg-docs/active-state/current.json` (Stage 1 closeout handoff)
- `.cg-docs/views/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.html`
  (regenerated view from canonical Markdown)
