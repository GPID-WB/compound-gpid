---
date: 2026-08-06
title: "Stage 0A — Read-only verification evidence report"
type: evidence
plan: ".cg-docs/plans/2026-08-05-copilot-issue-implementation-pipeline-v2.md"
phase: 1
classification: "Verified / User-confirmed / Inference as noted"
scope: "read-only; no live GitHub mutations performed"
---

# Stage 0A — Read-only verification evidence report

## 1. Scope and method

This evidence report is the deliverable of **Phase 1 (Stage 0A)** of the
controlled GitHub Copilot issue-implementation pipeline plan (v2, 2026-08-05).
It resolves the must-resolve items, ranks pilot candidates, audits token
permissions and roadmap drift, and documents the Copilot assign-API contract.

**Method**: read-only GitHub/API inspection, official GitHub documentation,
repository inspection, and one local credential-scope refresh
(`gh auth refresh -s read:project`, a local change only — not a repository or
control-plane mutation). **No live GitHub mutations of any kind were
performed**: no issue create/edit/label/comment, no assign, no Project Status
write, no roadmap write, no workflow/settings change. The live Copilot assign
trial is deferred to Stage 1 (plan §5.6 step 3).

Classification legend (same as the plan): **Verified** = observed via API/`gh`
or `origin/main` during this run; **User-confirmed** = stated by the operator
during planning (2026-08-05), not re-derived; **Inference** = reasoned from
verified facts, re-check before coding.

---

## 2. Repository identity and permissions (Verified)

| Fact | Value |
|------|-------|
| Repo | `GPID-WB/compound-gpid` (public, `private: false`) |
| Default branch | `main` |
| Planning account | `randrescastaneda`, ADMIN (`admin:true`, `maintain:true`, `push:true`) |
| Actions enabled | `enabled: true`, `allowed_actions: all`, `sha_pinning_required: false` |
| Default workflow permissions | **`default_workflow_permissions: write`** |
| PR review approval | `can_approve_pull_request_reviews: true` |

Branch ruleset **`Protect main`** (id `16657602`, enforcement `active`, target
`branch`, `~DEFAULT_BRANCH`), re-verified via API; active rules: `deletion`,
`non_fast_forward`, `pull_request`, `required_status_checks`. Required check
contexts (verified at planning time, plan §1.3): `Native target Python gate on
macos-14`, `Native target Python gate on windows-2022`, `PR title follows
Conventional Commits`, `Pester on macos-14`, `Pester on windows-2022`.

---

## 3. Copilot assign-API contract (must-resolve — RESOLVED from docs + read-only schema inspection)

No live assign was performed. The contract below is captured from official
GitHub docs (2026-08-05) and one read-only GraphQL query.

### 3.1 Enablement and bot identity (Verified)

`repository.suggestedActors(capabilities:[CAN_BE_ASSIGNED])` on this repo
returns as its **first node**:

```json
{ "login": "copilot-swe-agent", "__typename": "Bot", "id": "BOT_kgDOC9w8XQ" }
```

This confirms Copilot cloud agent is **enabled and assignable** in this repo
and supplies the bot login and node id that the assign API needs. (The earlier
`mentionableUsers(query:"copilot")` empty result recorded in plan §1.6 is
consistent — it is an incomplete surface for bots; `suggestedActors` is the
documented mechanism.)

### 3.2 Assignment mutations (documented)

- **REST (existing issue)**: `POST /repos/{owner}/{repo}/issues/{issue_number}/assignees`
  with body:
  ```json
  {
    "assignees": ["copilot-swe-agent[bot]"],
    "agent_assignment": {
      "target_repo": "OWNER/REPO",
      "base_branch": "main",
      "custom_instructions": "",
      "custom_agent": "",
      "model": ""
    }
  }
  ```
  Also supported on `POST /repos/{o}/{r}/issues` (create) and
  `PATCH /repos/{o}/{r}/issues/{n}` (update).
- **GraphQL**: `updateIssue`, `replaceActorsForAssignable`,
  `addAssigneesToAssignable`, `createIssue` with `assigneeIds:["BOT_kgDOC9w8XQ"]`
  plus optional `agentAssignment { targetRepositoryId baseRef customInstructions
  customAgent model }`; requires header
  `GraphQL-Features: issues_copilot_assignment_api_support,coding_agent_model_selection`.
- **Agent-tasks API (public preview)**: `POST /agents/repos/{owner}/{repo}/tasks`
  with `prompt`, `base_ref`, optional `model`, `create_pull_request`
  (background task; user-to-server tokens only).

### 3.3 Token / permission requirements (documented)

- Issues assignment APIs are in **public preview** and require **user tokens**
  (PAT or OAuth, or GitHub App **user-to-server** token).
- Fine-grained PAT: read metadata + read/write **actions, contents, issues,
  pull_requests**. Classic PAT: `repo` scope.
- The agent-tasks API **does not support server-to-server** (installation)
  tokens.

**Implications (Inference from docs, to re-confirm in Stage 1):**
- A dispatcher must use a **user-authenticated** credential; a GitHub App
  installation token cannot drive the tasks API, reinforcing plan R28 that the
  Copilot-assignment credential is separate from a (server-to-server App)
  Project-synchronization credential — separation is required, not optional.
- The live assign trial is sanctioned only in Stage 1 §5.6 step 3.

---

## 4. GitHub Project CompoundGPID-progress (must-resolve — RESOLVED via read-only GraphQL)

| Item | Value |
|------|-------|
| Project node ID | `PVT_kwDOA9TrWc4BfRSv` |
| Project number / title | `1` / `CompoundGPID-progress` (org `GPID-WB`) |
| Status field ID | `PVTSSF_lADOA9TrWc4BfRSvzhZlWns` |
| Option IDs | Backlog `f75ad846` · Ready `61e4505c` · In progress `47fc9ee4` · In review `df73e18b` · Done `98236657` |

The option names match the planning-time User-confirmed list exactly (now
Verified). Item count: **44**; all sampled items are `type: ISSUE`; sampled
Status values all `Backlog` (e.g. #47, #63, #77, #86 are on the board in
Backlog). No PR items currently present.

**Resolved §1.5 unresolved**: issue #98 IS on the board (project item exists);
REST `projectItems` returned `null` even after adding `read:project`, so the
field is not a reliable membership indicator — the GraphQL project item query
is the reliable source.

### 4.1 Built-in workflows — exact default actions (documented; enabled set User-confirmed)

Enabled per planning (User-confirmed 2026-08-05): Auto-add sub-issues;
Auto-add to project; Auto-close issue; Item added to project; Item closed;
Pull request linked to issue; Pull request merged. Disabled: Auto-archive;
Code changes requested; Code review approved; Item reopened.

Documented default semantics (GitHub docs + 2025-11-06 changelog):

| Workflow | Documented default action |
|----------|---------------------------|
| Item closed | Set Status of the **closed item** to `Done` |
| Pull request merged | Set Status of the **merged PR item** to `Done` |
| Pull request linked to issue | Set the **issue's** Status to `In progress` when a linked PR exists |
| Item added to project | Set Status of a newly added item to a configured value |
| Auto-add to project | Add matching items (issues **and** PRs) on create/update (filterable `is: issue|pr`) |
| Auto-add sub-issues | Add child issues when created/updated |
| Auto-close issue | Close issue when its linked PR is merged (standard linkage path) |

**PRs become separate items** (documented): auto-add adds issue-type and
PR-type items independently; the default Status workflows act on the item that
triggered them (`Item closed`/`Pull request merged` update the PR item, not the
issue item). This means an issue's Status is advanced by the **PR-linked** and
**Item closed** paths (issue item), while PR-merge advances the PR item.
Configurable Status targets are UI-managed and **not API-readable**; they will
be read from the project UI before Stage 1 and observed live there (deferral
below).

> **May-defer (named consumer)**: the *configured Status-target values* of each
> built-in workflow (UI-only) are deferred to **Stage 1 §5.5/§5.8** (live
> Status timeline observation, evidence E7) and **Stage 4** (transition-matrix
> design) — each consuming stage is blocked on this until read from the UI.

---

## 5. GITHUB_TOKEN default-permission audit (must-resolve — RESOLVED)

Repo default is `default_workflow_permissions: write`. Workflow inheritance:

| Workflow | Permission declaration | Inherits default write? |
|----------|------------------------|-------------------------|
| `tests.yml` | job-level `permissions: contents: read` on all 4 jobs (browser-evidence, native-targets, test, docs-staleness) | no |
| `commit-lint.yml` | top-level `permissions: pull-requests: read` | no |
| `pages.yml` | top-level `contents: read`; deploy job adds `pages: write`, `id-token: write` | no |
| **`link-check.yml`** | **none declared** | **yes** |

**Findings / assessment**:
- Exactly **one** workflow — `link-check.yml` (job `link-check`) — declares no
  `permissions:` and therefore inherits the repo default **`write`**.
- The five **required** checks run in `tests.yml` / `commit-lint.yml`, both of
  which declare explicit least-privilege permissions and would be unaffected by
  tightening the default.
- Recommendation (for later, not executed now): set
  `default_workflow_permissions` to `read` and add an explicit job-level
  `permissions: contents: read` to `link-check.yml`. This is a repo-settings
  change and is **out of scope for Stage 0A**; it is recorded as an option for
  Stage 0B/Stage 3 hardening, not as a Stage 0A mutation.

---

## 6. Roadmap-drift audit (verified against `origin/main` — must-resolve RESOLVED)

`git fetch origin` + `git show origin/main:roadmap.json` (fetches update local
tracking refs only — no control-plane or repo-content mutation).

| Metric | Worktree | `origin/main` |
|--------|----------|---------------|
| Features (nested under `milestones[]`) | 137 | 137 |
| Features with `features[].github` link | **0** | **0** |
| Features with a `plan` ref | 57 | n/a |
| Top-level `githubIssues` block | absent | absent |
| Open issues (sample, all) with `compound-gpid-tracked` marker + `cg:roadmap` label | ~44 | live ~44 |

**Discrepancy record**: ~44 open issues carry `compound-gpid-tracked` body
markers and the `cg:roadmap` label, but **zero** roadmap features have a
canonical `features[].github` link on `origin/main` — total linkage drift.
Candidate features exist on `origin/main` at `status: idea` with no `github`
link and no `plan` (e.g. `mattpocock-skills-review-source`,
`attribution-documentation`, `evals-scaffold`, `plan-frontmatter-checks`).
`github-issues-integration` remains `status: idea` while its integration plan is
completed (matches plan §1.4). No linkage repair was performed (Stage 0B +
human approval required). This satisfies R23 (verified against `origin/main`,
not only the planning worktree).

---

## 7. Approve-Copilot-workflows setting (User-confirmed; not API-readable)

An exact API probe for the "Approve Copilot-initiated workflow runs" toggle
was not possible with the endpoints used (consistent with plan §1.3). The
operator confirmed during planning (2026-08-05) that it remains **enabled**.
Evidence-log path for re-verification in the browser:
**Repository → Settings → Actions → General → "Approve Copilot-initiated
workflow runs"**. Not modified.

---

## 8. Pilot candidate ranking (>=3 required; #63 included — OPEN)

All open issues are `idea` placeholders (no acceptance criteria / path bounds /
verification commands), so **any** selected pilot issue must be rewritten into a
full readiness contract in Stage 0B (plan §5.3–5.4) before assignment. No open
PRs exist; none of the candidates is assigned.

### Candidate 1 — Issue **#86** Attribution documentation
- Feature id: `attribution-documentation` (marker OK, on board, Backlog).
- **Required files**: `docs/attribution.md` (new), optional `docs/index` link.
- **Objective verification**: file exists; renders as Markdown;
  `rg` each enumerated source (the three review repos, user-provided, tool docs)
  in `docs/attribution.md`; CI link-check.
- **Subjective ambiguity**: MEDIUM — "what each source contributed" is prose;
  the *source set* is enumerated by the issue, so a checklist + `rg` keeps the
  verdict deterministic.
- **Security/control-plane risk**: none (`docs/**` only; no `.github/`,
  scripts, secrets, rulesets).
- **Estimated scope**: small (1 file, <150 lines).
- **Recommendation**: **Recommended** — lowest risk, objectively verifiable
  after the readiness rewrite pins the entry checklist.

### Candidate 2 — Issue **#63** Add mattpocock/skills to competitive review sources (**open** → included per R26)
- Feature id: `mattpocock-skills-review-source` (marker OK, on board, Backlog).
- **Required files**: `.cg-docs/competitive-reviews/repos.json` (new `mattpocock`
  entry), `.github/prompts/cg-review-repos.prompt.md` (concept-mapping table
  column), `docs/competitive-reviews.md` (registry list).
- **Objective verification**: `repos.json` remains valid JSON and the entry
  satisfies its schema (`id` alnum+hyphen ≤50, `shortName` 1–10 alnum unique,
  URLs `https://github.com/...` with `releasesUrl` ending `/releases`);
  `rg "mattpocock/skills" docs/competitive-reviews.md` + prompt mapping table.
- **Subjective ambiguity**: LOW — deterministic edits, no human-judgment gate.
- **Security/control-plane risk**: MINIMAL–MEDIUM — touches a developer-owned
  prompt (`cg-review-repos.prompt.md`); not a `.github/workflows/**` workflow,
  not secrets, not rulesets, not roadmap schema. Reviewer gate: confirm no
  permission-model change.
- **Estimated scope**: small (3 files, <60 lines).
- **Recommendation**: **Recommended** — small, objective, feature-linked, on
  board. Mandatory inclusion in the ranking per R26 (it is open).

### Candidate 3 — Issue **#77** `.cg-docs/evals/` scaffold with probe-and-check pairs
- Feature id: `evals-scaffold` (marker OK, on board, Backlog).
- **Required files**: `.cg-docs/evals/` scaffold (README + schema + one
  probe/check pair).
- **Objective verification**: scaffold paths exist; JSON schema parses; the
  sample pair validates via the documented script/parser; Markdown renders.
- **Subjective ambiguity**: HIGH — body is "No description provided", so the
  probe/check semantics must be authored during the Stage 0B rewrite (the
  contract becomes the deliverable).
- **Security/control-plane risk**: none (`.cg-docs/` only).
- **Estimated scope**: small–medium.
- **Recommendation**: **Acceptable** (low risk; needs full contract authoring).

### Candidate 4 (secondary) — Issue **#76** Required frontmatter field checks from /cg-plan output
- Feature id: `plan-frontmatter-checks` (marker OK, on board, Backlog).
- Required files: prompt or checker script + a Pester/Python test.
- Objective: deterministic Pester/Python assertion; risk: MEDIUM (touches
  prompts + tests); scope: small–medium.
- **Recommendation**: **Acceptable with caution** (secondary to the three above;
  greater CI/test surface).

### Anti-selection noted
- #49 / #47 (skill rewrites) — avoid for first pilot (plan §5.2 large skill
  rewrites).
- #83 "Goal-driven execution / plan-as-completion-contract" — largely already
  delivered by the goal-execution contract; near-duplicate, avoid.
- #85 conversation audit trail — large, cross-cutting; avoid for pilot.

---

## 9. Must-resolve vs may-defer resolution summary

| Item | Status |
|------|--------|
| Project node ID + Status field/option IDs | RESOLVED (§4) |
| Built-in workflow exact actions; PRs as separate items | RESOLVED semantics (§4.1); configured Status targets deferred to Stage 1 (§4.1 may-defer) |
| GITHUB_TOKEN default permissions + inheriting workflows | RESOLVED (§5) |
| Assign-API shape from docs/schema | RESOLVED (§3); live trial deferred to Stage 1 §5.6 step 3 (per plan) |
| Copilot approval setting | User-confirmed, settings path logged (§7) |
| Roadmap drift vs `origin/main` | RESOLVED (§6) |
| Pilot ranking >=3 incl. #63 if open | RESOLVED (§8) — #63 open, ranked |

---

## 10. No-mutations statement

No live GitHub mutations were performed during Stage 0A: no issue create/edit/
label/comment, no assignment, no Project Status change, no roadmap write, no
repository/organization settings change, no workflow/template/secret change.
The only local change is the `gh auth` `read:project` credential scope refresh
(step 1 of the stage), which is not a repository mutation. Stage 0B (any
repairs) and Stage 1 (pilot) each require explicit human approval before
execution, per the plan and the completion contract.

## 11. References (all read-only)

- `gh api repos/GPID-WB/compound-gpid` (+ `/actions/permissions`,
  `/actions/permissions/workflow`, `/rulesets`, `/issues`, `/issues/{n}`)
- GraphQL: `suggestedActors`, `organization.projectsV2`, `node(... ProjectV2
  fields/items)`
- `git fetch origin`; `git show origin/main:roadmap.json`
- Official docs: Copilot cloud-agent API page (assign via REST/GraphQL),
  Projects built-in automations, auto-add items; GitHub changelog
  2025-11-06 (Pull request linked to issue → issue Status).
