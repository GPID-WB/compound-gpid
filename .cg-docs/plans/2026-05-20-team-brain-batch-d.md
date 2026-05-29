---
date: 2026-05-20
title: "Team Brain (Phase 2) — Batch D implementation"
status: active
scope: "Deep"
phases: 3
brainstorm: ".cg-docs/brainstorms/2026-05-20-team-brain-batch-d.md"
language: "both"
estimated-effort: "large"
tags: [team-brain, knowledge-sharing, cross-project, privacy, dedup, github-actions]
review-findings-addressed: [P1.1, P1.2, P1.3, P2.1, P2.2, P2.3, P2.4, P2.5, P2.6, P2.7, P3.1, P3.2]
completed-phases: [1, 2]
current-phase: 3
---

# Plan: Team Brain (Phase 2) — Batch D Implementation

## Objective

Build the cross-project knowledge sharing system for compound-gpid. When a user
captures a solution via `/cg-compound`, the system privacy-filters and pushes it
to a central team brain repo. When any project's Consult Brain step runs, it
pulls relevant entries from the team brain. A GitHub Actions curation bot
periodically scans for contradictions and opens issues for the team brain manager.

## Context

- **Existing infrastructure**: `scripts/cg_index.py` v0.2.0 with modular
  `scripts/brain/` engine (scanner, extractor, clusterer, edge_detector,
  renderer). Produces `BRAIN.md`, `BRAIN-01.md`, `BRAIN-log.md`,
  `brain-index.json`.
- **Brainstorm decision**: Approach 3 (Hybrid — Direct Push + Async Curation).
  Privacy filter runs locally (blocking). Push is direct to namespaced folder.
  Curation is async via GH Actions.
- **Scale**: 10–15 projects in 2 weeks, 30 within a month.
- **Constraints**: Python 3.8+ stdlib only for core logic. `gh` CLI for GitHub
  operations. Privacy filter must be blocking (fail loudly — nothing sensitive
  leaves the machine). Push must log confirmation.

## Requirements

| ID  | Requirement                                                | Source     |
|-----|------------------------------------------------------------|------------|
| R1  | Central repo schema with namespaced entries + patterns     | brainstorm |
| R2  | `TEAM-BRAIN.yml` config (manager, contributors, schedule)  | brainstorm |
| R3  | Merged `TEAM-BRAIN.md` index for consumption               | brainstorm |
| R4  | 3-layer privacy filter (regex → frontmatter → LLM)         | brainstorm |
| R5  | Push on `/cg-compound` with confirmation logging           | brainstorm |
| R6  | Distilled pattern extraction (one-liner from solution)      | brainstorm |
| R7  | Pull during Consult Brain with problem-context matching     | brainstorm |
| R8  | Contradiction detection (same problem → supersession)       | brainstorm |
| R9  | Contextual variant recognition (different context → both)   | brainstorm |
| R10 | GitHub Actions curation bot (weekly, opens issues)          | brainstorm |
| R11 | Configurable team brain repo in `compound-gpid.local.md`    | brainstorm |
| R12 | TeamBrain manager role defined in `TEAM-BRAIN.yml`          | brainstorm |
| R13 | First-activation gate: explicit approval before first push  | review-P1.2 |

## Phase 1: Foundation (Schema + Privacy Filter)

### 1. Design Central Repo Schema

- **Requirements**: R1, R2, R3, R12
- **Files**:
  - Create `docs/team-brain-schema.md` — schema documentation
  - Create `scripts/team_brain/__init__.py` — team brain module
  - Create `scripts/team_brain/schema.py` — schema constants, validation
- **Details**:
  Define the canonical repo structure:
  ```
  team-brain/
  ├── TEAM-BRAIN.yml          # config: manager, contributors, curation
  ├── TEAM-BRAIN.md           # merged index (rebuilt by CI)
  ├── entries/
  │   ├── compound-gpid/      # one folder per project
  │   │   ├── 2026-05-20-pester-safety.md
  │   │   └── ...
  │   └── pcn-tools/
  │       └── ...
  ├── patterns/
  │   ├── compound-gpid.jsonl  # one file per project
  │   └── pcn-tools.jsonl
  └── .github/
      └── workflows/
          ├── rebuild-index.yml    # on push to entries/ or patterns/
          └── curation-bot.yml     # weekly cron
  ```
  Schema for `TEAM-BRAIN.yml`:
  ```yaml
  schema-version: "1.0"
  manager: "<github-username>"
  contributors:
    - org: "<github-org>"           # all org members
    # OR
    - team: "<org>/<team-name>"     # specific team
  curation:
    schedule: "weekly"              # cron expression or preset
    auto-supersede: false           # require manager approval
  ```
  Schema for pattern JSONL entries:
  ```json
  {"id": "<slug>", "date": "YYYY-MM-DD", "source-project": "<name>",
   "topic": "<topic>", "tags": ["..."], "pattern": "<one-liner>",
   "entry-path": "entries/<project>/<filename>.md",
   "confidence": 1.0, "superseded-by": null}
  ```
  Schema for entry files: same frontmatter as local `.cg-docs/solutions/`
  plus `source-project` and `pushed-date` fields.

  Confidence scoring (static for this iteration — no decay):
  - Base confidence: 1.0 for all new entries
  - Boost +0.1 for each project that independently validates (same solution)
  - No time-based decay (deferred to future iteration)
- **Test Scenarios**:
  - ✅ Valid `TEAM-BRAIN.yml` parses correctly
  - 🛑 Missing required fields (manager) → validation error
  - ❌ Malformed YAML → clear error message
- **Tests**: `scripts/team_brain/tests/test_schema.py` — validate parsing,
  required field checks, JSONL line parsing
- **Acceptance criteria**: Schema documented; validation functions pass all tests

### 2. Implement Privacy Filter — Regex Layer

- **Requirements**: R4
- **Files**:
  - Create `scripts/team_brain/privacy.py` — privacy filter module
- **Details**:
  Regex patterns to strip:
  - Windows absolute paths: `[A-Z]:\\[^\s"']+`
  - Unix absolute paths: `/(?:home|Users|tmp|var|opt)/[^\s"']+`
  - Drive-letter prefixes: `[A-Z]:\\`
  - Email addresses: standard RFC 5322 simplified pattern
  - Internal URLs: configurable list of hostname patterns (from `TEAM-BRAIN.yml`)
  - Credential-adjacent: `(?:password|secret|token|api.?key)\s*[:=]\s*\S+`
  - UNC paths: `\\\\[^\s]+`

  Replacements: `<REDACTED:path>`, `<REDACTED:email>`, `<REDACTED:url>`,
  `<REDACTED:credential>`. Each replacement is logged for the confirmation message.

  The function signature:
  ```python
  def apply_regex_filter(content: str, config: dict) -> Tuple[str, List[Redaction]]:
  ```
  Returns cleaned content + list of redactions made (type, original snippet length, line number).
- **Test Scenarios**:
  - ✅ Windows path `E:\PovcalNet\...` → `<REDACTED:path>`
  - ✅ Email `user@worldbank.org` → `<REDACTED:email>`
  - 🛑 Path-like strings inside code fences (still redact — code may contain real paths)
  - ❌ No false positives on relative paths (`./scripts/foo.py` should NOT be redacted)
- **Tests**: `scripts/team_brain/tests/test_privacy.py`
- **Acceptance criteria**: All regex patterns tested with positive and negative cases; zero false positives on compound-gpid's own solution files

### 3. Implement Privacy Filter — Frontmatter + LLM Layers

- **Requirements**: R4
- **Files**:
  - Extend `scripts/team_brain/privacy.py`
- **Details**:
  **Frontmatter layer**: Parse the solution's frontmatter for `private: true`
  (at document level) or `private-sections: [...]` (list of heading names to
  exclude). Default is `private: false`. If `private: true`, the entire entry
  is excluded from push (log and skip).

  **LLM layer** (non-blocking, auto-applied — addresses P1.1): The LLM layer
  runs automatically after the regex layer. Its suggestions are **auto-applied**
  (not presented for individual approval) because `/cg-compound` is a
  single-pass execution with no mid-step branching. The full list of LLM
  redactions is included in the push confirmation summary so the user can
  audit after the fact:
  > "Privacy filter: 3 regex redactions, 2 LLM redactions (auto-applied: [internal-system-name, project-jargon])."

  If the user wants to disable the LLM layer entirely, they pass `--no-llm`
  to `/cg-compound` (or set `llm-filter: false` in team-brain config).

  The LLM prompt instructs the agent to scan post-regex content for:
  - Project-identifying jargon (team-specific terminology that reveals the source)
  - Internal system names (database names, server aliases, internal tool names)
  - Domain-specific secrets (internal classification codes, budget references)
  - Overly specific examples that should be generalized

  Full pipeline orchestrator:
  ```python
  def run_privacy_filter(content: str, frontmatter: dict, config: dict) -> FilterResult:
      # 1. Check frontmatter exclusion
      # 2. Apply regex layer
      # 3. Apply LLM layer (auto-apply, log results)
      # Returns: FilterResult(clean_content, redactions, llm_redactions, blocked)
  ```
- **Test Scenarios**:
  - ✅ `private: true` → entry blocked entirely
  - ✅ `private-sections: ["Internal Notes"]` → that section stripped
  - ✅ LLM redactions auto-applied and listed in summary
  - 🛑 No frontmatter `private` field → defaults to false (not blocked)
  - 🛑 `--no-llm` flag → LLM layer skipped, regex-only
  - ❌ Malformed private-sections value → warning, proceed without section filtering
- **Tests**: `scripts/team_brain/tests/test_privacy.py` (extend)
- **Acceptance criteria**: Frontmatter layer fully tested; LLM layer
  auto-applies and reports; `--no-llm` bypass works

### 4. Add Team Brain Configuration to `compound-gpid.local.md`

- **Requirements**: R11
- **Files**:
  - Extend `cg-skill-setup` to include team-brain config section
  - Document in `docs/team-brain-schema.md`
- **Details**:
  New section in `compound-gpid.local.md`:
  ```yaml
  team-brain:
    repo: "GPID-WB/team-brain"    # owner/repo on GitHub
    project-name: "compound-gpid"  # namespace in team brain
    enabled: true                   # opt-out switch
    llm-filter: true                # set false to disable LLM privacy layer
  ```
  The push/pull scripts read this config. If `team-brain` section is absent or
  `enabled: false`, team brain features are silently disabled.
- **Test Scenarios**:
  - ✅ Config present and valid → push/pull enabled
  - ✅ Config absent → team brain disabled silently
  - 🛑 `enabled: false` → explicitly disabled
  - ❌ Invalid repo format → clear error at push time
- **Tests**: `scripts/team_brain/tests/test_config.py`
- **Acceptance criteria**: Config parsing works; missing config gracefully
  disables team brain without errors

## Phase 2: Push + Pull (Core Data Flow)

### 5. Implement Pattern Distillation

- **Requirements**: R6
- **Files**:
  - Create `scripts/team_brain/distiller.py`
- **Details**:
  Given a solution entry (frontmatter + markdown body), produce a one-liner
  distilled pattern. The distiller:
  1. Extracts the `## Solution` section
  2. Identifies the core actionable advice (the "what to do")
  3. Produces a single sentence (≤ 200 chars) capturing the reusable lesson
  4. Falls back to the `title` field if distillation fails

  This is LLM-assisted (prompt-based). The function returns a prompt that the
  calling agent uses to generate the pattern. For testing, a deterministic
  fallback (title-based) is used.

  ```python
  def distill_pattern(frontmatter: dict, body: str) -> DistillResult:
      # Returns: DistillResult(pattern_text, source="llm"|"fallback", prompt=...)
  ```
- **Test Scenarios**:
  - ✅ Solution with clear "## Solution" section → meaningful pattern
  - 🛑 No "## Solution" heading → fallback to title
  - ❌ Empty body → fallback to title with warning
- **Tests**: `scripts/team_brain/tests/test_distiller.py`
- **Acceptance criteria**: Fallback path always produces a valid pattern;
  LLM prompt is well-formed

### 6. Implement Team Brain Push

- **Requirements**: R5, R11, R13
- **Files**:
  - Create `scripts/team_brain/push.py` — all push logic including `gh` CLI calls
- **Details**:
  Push uses the **GitHub Contents API** (atomic file PUT, no clone required —
  addresses P1.3). This eliminates shallow-clone/rebase complications entirely.

  Push workflow (invoked after privacy filter passes):
  1. Read team-brain config from `compound-gpid.local.md`
  2. **First-activation gate** (addresses P1.2): Check if
     `entries/<project-name>/` exists in the team brain repo via
     `gh api repos/<owner>/<repo>/contents/entries/<project>`. If the
     directory does NOT exist (404), this is the project's first push. Display:
     > "⚠️ First push to team brain. This will create your project namespace
     > in `<repo>`. Only the current solution will be pushed (existing local
     > solutions are NOT auto-pushed). Continue? [yes/no]"
     If no: abort push, log "Team brain push skipped (first-activation declined)."
  3. Upload filtered entry via GitHub Contents API:
     ```
     gh api repos/<owner>/<repo>/contents/entries/<project>/<filename>.md \
       --method PUT \
       --field message="feat(<project>): add <title>" \
       --field content="<base64-encoded-content>"
     ```
  4. Upload/update pattern in JSONL via Contents API:
     - GET existing `patterns/<project>.jsonl` (may 404 on first push)
     - **Dedup check** (addresses P3.1): If an entry with the same `id` (slug)
       already exists in the JSONL, replace that line in place. Otherwise append.
     - PUT the updated file with the new/updated line
  5. Log confirmation (loud — addresses charter "fail loudly" constraint):
     > "Pushed to team brain: 1 entry + 1 pattern → <repo>.
     > Privacy filter: N regex redactions, M LLM redactions (auto-applied: [types])."
  6. If any API call fails: surface the error with HTTP status code and message.
     Do NOT block the local compound capture.

  All `gh` CLI calls use `subprocess.run(["gh", "api", ...])` from Python
  (addresses P2.6 — no separate PowerShell logic file). The PowerShell wrapper
  (`scripts/team-brain-push.ps1`) is ≤10 lines: parse the entry path and
  invoke `python scripts/team_brain/push.py <args>`.

  ```python
  def push_to_team_brain(entry_path: Path, pattern: str, config: TeamBrainConfig) -> PushResult:
  ```
- **Test Scenarios**:
  - ✅ Successful push → confirmation message with stats
  - ✅ First-activation gate → user prompted, namespace created on approval
  - ✅ Re-push same solution → JSONL line updated in place (no duplicate)
  - 🛑 Network failure → clear error, entry preserved locally
  - 🛑 API returns 409 (conflict) → retry once with fresh SHA
  - ❌ No `gh` CLI available → error with install instructions
  - ❌ No write permission to repo → clear permission error (403)
- **Tests**: `scripts/team_brain/tests/test_push.py` (mocked `subprocess.run`)
- **Acceptance criteria**: Push succeeds via Contents API; first-activation
  gate fires on first push only; dedup prevents JSONL duplicates; all error
  paths produce actionable messages

### 7. Wire Push into `/cg-compound` Prompt

- **Requirements**: R5
- **Files**:
  - Modify `.github/prompts/cg-compound.prompt.md` — add Step 3d (Team Brain Push)
- **Details**:
  Insert new step **after Step 3c** (Update Project Wiki) — NOT after 3b
  (addresses P2.1). Team brain push is the final sub-step of the capture
  sequence:

  ```markdown
  ### Step 3d: Push to Team Brain

  If team-brain is not configured in `compound-gpid.local.md` (section absent
  or `enabled: false`): skip this step silently.

  1. Run the privacy filter on the captured solution (Step 3's output).
  2. If the filter blocks the entry (`private: true`): inform the user and skip.
  3. Distill a one-liner pattern from the solution.
  4. Run `python scripts/team_brain/push.py` with the filtered entry + pattern.
     (First-activation gate and dedup are handled internally by push.py.)
  5. Surface the confirmation message to the user:
     > "Pushed to team brain: 1 entry + 1 pattern → <repo>.
     > Privacy filter: N regex redactions, M LLM redactions (auto-applied: [types])."
  6. If push fails: surface the error but do NOT block the local compound
     capture (the solution is already saved locally).
  ```

  Note: LLM redactions are auto-applied and reported in the summary (no
  mid-step user approval — single-pass execution model).
- **Test Scenarios**:
  - ✅ Team brain configured → push step runs after wiki update (Step 3c)
  - ✅ Team brain not configured → step skipped silently
  - 🛑 Push fails → error shown, local capture unaffected
  - ❌ Privacy filter blocks → user informed, no push
- **Tests**: `tests/prompt-tools.Tests.ps1` — assertion that Step 3d text exists
  in `cg-compound.prompt.md` and comes after Step 3c
- **Acceptance criteria**: `/cg-compound` prompt includes the team brain push
  step after Step 3c with correct guards and ordering

### 8. Implement Team Brain Pull

- **Requirements**: R7, R11
- **Files**:
  - Create `scripts/team_brain/pull.py`
  - Modify `.github/skills/cg-skill-brain-query/SKILL.md` — add team brain step
- **Details**:
  Pull workflow (invoked during Consult Brain):
  1. Read team-brain config; if not configured, skip silently
  2. Fetch `TEAM-BRAIN.md` from the team brain repo via `gh api` with explicit
     Accept header (addresses P2.4):
     ```
     gh api repos/<owner>/<repo>/contents/TEAM-BRAIN.md \
       --header "Accept: application/vnd.github.raw+json"
     ```
     OR read from local cache if fresh (< 1 hour old)
  3. Parse the topic index from `TEAM-BRAIN.md`
  4. Match current task's keywords/tags against topic index entries
  5. For matching topics: fetch the relevant pattern lines from
     `patterns/<project>.jsonl` files (via `gh api` with same raw Accept header)
  6. Return matched patterns + entry references (not full entries — those are
     fetched on drill-down only)

  Cache strategy (addresses P2.2): store `TEAM-BRAIN.md` in
  `~/.cg-cache/team-brain/<repo-slug>/` (user home directory, outside the
  workspace — does NOT violate the "commit all `.cg-docs/`" charter constraint).
  Refresh if stale (> 1 hour) or on explicit `--refresh`. Cache path is
  configurable via `XDG_CACHE_HOME` or `LOCALAPPDATA` on Windows.

  Integration into `cg-skill-brain-query`:
  - After Step 2 (Read the Topic Index), add Step 2b: "Check Team Brain"
  - If team brain is configured: fetch and scan team-level patterns
  - Present team brain findings with source attribution:
    > "From team brain (<source-project>): <pattern>"

  All `gh api` calls use `subprocess.run(["gh", "api", ...])` from Python
  (consistent with push.py — addresses P2.6).

  ```python
  def pull_from_team_brain(keywords: List[str], config: TeamBrainConfig) -> PullResult:
  ```
- **Test Scenarios**:
  - ✅ Matching keywords → relevant patterns returned with source attribution
  - ✅ No matches → empty result, no noise
  - ✅ Accept header produces raw markdown (not base64 JSON)
  - 🛑 Stale cache → refresh from remote
  - ❌ Network failure → use cache if available, warn if not
  - ❌ Team brain repo doesn't exist → clear error on first pull, then disable
- **Tests**: `scripts/team_brain/tests/test_pull.py` (mocked `subprocess.run`)
- **Acceptance criteria**: Pull returns relevant patterns with attribution;
  cache lives in user home (not `.cg-docs/`); network failures degrade gracefully

## Phase 3: Dedup + Curation (Quality Layer)

### 9. Implement Contradiction Detection

- **Requirements**: R8, R9
- **Files**:
  - Create `scripts/team_brain/dedup.py`
- **Details**:
  Contradiction detection algorithm (addresses P2.5 — uses text similarity,
  not just tags):
  1. Load all patterns from `patterns/*.jsonl`
  2. **Primary grouping**: Compute word-overlap (Jaccard similarity on
     tokenized `pattern` text). Pairs with Jaccard ≥ 0.4 are candidates.
  3. **Secondary signal**: Tag overlap (≥ 2 shared tags) boosts candidate
     confidence; used as tiebreaker, not as the sole grouping criterion.
  4. Within each candidate pair, compare problem descriptions (from entry
     frontmatter `root-cause` + `title`) to classify:
     - **Same problem, same context** → true contradiction → flag for supersession
       (newer date + higher confidence wins)
     - **Same problem, different context** → contextual variant → both valid,
       add `context-note` field to distinguish
     - **Different problem** (low Jaccard was a false positive) → skip
  5. Entries from the **same project** → skip (intra-project dedup is the
     local brain's responsibility)

  Confidence scoring (static — no decay, addresses P2.3):
  - Base confidence: 1.0 for all new entries
  - Boost +0.1 for each additional project that independently validates
    (pushes a solution with Jaccard ≥ 0.6 to an existing pattern)
  - No time-based decay in this iteration (deferred to future batch)

  Output: list of `ContradictionReport` objects (pair of entries, classification,
  recommended action, Jaccard score).

  ```python
  def detect_contradictions(patterns_dir: Path) -> List[ContradictionReport]:
  ```
- **Test Scenarios**:
  - ✅ Two entries with high Jaccard + same root-cause → flagged as contradiction
  - ✅ Two entries with high Jaccard + different root-cause → contextual variant
  - ✅ Two entries with low Jaccard → not grouped (no false positive)
  - 🛑 Entries from same project → skip
  - ❌ Empty patterns directory → empty report, no error
- **Tests**: `scripts/team_brain/tests/test_dedup.py`
- **Acceptance criteria**: Contradiction detection uses text similarity as
  primary signal; correctly classifies test cases; no tag-only false negatives

### 10. Implement GitHub Actions Curation Bot

- **Requirements**: R10, R12
- **Files**:
  - Create `scripts/team_brain/actions/rebuild-index.yml` (template)
  - Create `scripts/team_brain/actions/curation-bot.yml` (template)
  - Create `scripts/team_brain/curate.py` — curation script called by the action
- **Details**:
  **rebuild-index.yml** (runs on push to `entries/` or `patterns/`):
  - Checks out the repo
  - Runs a Python script that merges all `patterns/*.jsonl` + scans all
    `entries/` into a unified `TEAM-BRAIN.md`
  - Commits and pushes `TEAM-BRAIN.md` if changed

  **curation-bot.yml** (weekly cron):
  - Runs `curate.py` which calls `detect_contradictions()`
  - For each contradiction found:
    - Opens a GitHub Issue titled: "🔍 Contradiction: <topic> — <entry-A> vs <entry-B>"
    - Issue body contains: both patterns, Jaccard score, links to full entries,
      recommended action (supersede or mark as contextual variant)
    - Assigns the issue to the manager (from `TEAM-BRAIN.yml`)
  - If `auto-supersede: true` in config: auto-apply supersession for clear
    cases (same root-cause, newer date, Jaccard ≥ 0.8) and open a PR instead
    of an issue

  **curate.py**: CLI entry point that wraps `detect_contradictions()` and
  formats output as GitHub Issues via `subprocess.run(["gh", "issue", "create", ...])`.
- **Test Scenarios**:
  - ✅ Contradiction found → issue created with correct title/body
  - ✅ No contradictions → no issues created, clean exit
  - 🛑 `auto-supersede: true` → PR opened instead of issue for high-Jaccard matches
  - ❌ Manager not set in TEAM-BRAIN.yml → issue created unassigned, warning logged
- **Tests**: `scripts/team_brain/tests/test_curate.py` (mocked `subprocess.run`)
- **Acceptance criteria**: Action templates are valid YAML; curate.py produces
  correct issue content; auto-supersede path works

### 11. Team Brain Init Command

- **Requirements**: R1, R2, R12
- **Files**:
  - Create `scripts/team_brain/init.py` — all init logic
  - Create `bin/cg-brain-init` — shell wrapper (addresses P3.2)
  - Create `bin/cg-brain-init.cmd` — Windows wrapper (addresses P3.2)
  - Update `scripts/link.ps1` to include `cg-brain-init` in managed symlinks
  - Update `scripts/link.sh` to include `cg-brain-init` in managed symlinks
- **Details**:
  A one-time setup command for the team brain manager:
  1. Create the team brain repo on GitHub (via `gh repo create`)
  2. Populate initial structure: `TEAM-BRAIN.yml`, empty `entries/`, `patterns/`,
     `.github/workflows/`
  3. Copy action templates from compound-gpid into the new repo
  4. Push initial commit
  5. Configure the local project's `compound-gpid.local.md` with the new repo

  Invocation: `cg-brain-init --repo <owner/name> --manager <username>`

  Distributed via `bin/cg-brain-init` (same pattern as `bin/cg-index`):
  ```sh
  #!/usr/bin/env sh
  exec python "$(dirname "$0")/../scripts/team_brain/init.py" "$@"
  ```

  This is a convenience — the user could do it manually. The command just
  automates the scaffolding.
- **Test Scenarios**:
  - ✅ `gh repo create` succeeds → full scaffold committed
  - ✅ `bin/cg-brain-init` is callable after `link.ps1` runs
  - 🛑 Repo already exists → offer to configure local project to point to it
  - ❌ No `gh` CLI → error with install link
- **Tests**: `scripts/team_brain/tests/test_init.py` (mocked `subprocess.run`);
  `tests/parity.Tests.ps1` — verify `cg-brain-init` in both link.ps1 and link.sh
- **Acceptance criteria**: Init creates a valid team brain repo; `bin/` wrappers
  work on both platforms; link scripts updated

## Testing Strategy

- **Unit tests**: Each module in `scripts/team_brain/` has a corresponding
  test file in `scripts/team_brain/tests/`. All external calls (`subprocess.run`
  for `gh`) are mocked via `unittest.mock.patch`.
- **Integration test**: A single end-to-end test that mocks the GitHub API
  responses, runs push (verifies Contents API PUT calls are correct), then
  runs pull (verifies patterns are returned with attribution).
- **Privacy filter regression**: Run the regex filter against all existing
  `.cg-docs/solutions/` files — verify no false positives on relative paths
  and no missed absolute paths.
- **Prompt tests**: `tests/prompt-tools.Tests.ps1` assertions for new prompt
  content (Step 3d in cg-compound after Step 3c, Step 2b in brain-query skill).
- **Action validation**: YAML lint on workflow templates.
- **Pre-launch smoke test** (addresses P2.7): A manually-triggered test script
  (`scripts/team_brain/tests/smoke_test_push.py`) that exercises a real
  `gh api` call against a designated test repo (e.g., `GPID-WB/team-brain-test`).
  Required before first production deployment. Documents the exact `gh auth`
  scope needed (`repo` scope for Contents API writes).
- **Parity tests**: `tests/parity.Tests.ps1` assertions that `link.ps1` and
  `link.sh` both include `cg-brain-init` in managed directories/symlinks.

## Documentation Checklist

- [ ] `docs/team-brain-schema.md` — full schema reference
- [ ] `docs/manual.md` — add team brain section (setup, push, pull, curation)
- [ ] `scripts/team_brain/` — docstrings on all public functions
- [ ] `TEAM-BRAIN.yml` — inline comments explaining each field
- [ ] Action workflow files — comments explaining triggers and steps
- [ ] `gh auth` scope requirements documented (repo scope for Contents API)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Privacy filter misses sensitive content | High — data leak to shared repo | 3-layer defense (regex + frontmatter + LLM auto-applied); push logs all redactions for audit; first-activation gate prevents accidental bulk push |
| `gh` CLI not installed on contributor's machine | Medium — push fails | Clear error message with install link; team brain is optional (`enabled: false`) |
| GitHub Contents API rate limits (5000/hr) | Low — each push is 2-3 calls | Well within limits even at 30 projects; rate limit header checked before retry |
| TEAM-BRAIN.md grows too large for context | Medium — defeats purpose | Topic-based sections; pattern one-liners are short; full entries only on drill-down |
| LLM layer produces inconsistent results | Low — non-blocking | LLM redactions auto-applied and logged; `--no-llm` flag disables if problematic |
| Curation bot opens too many issues | Low — noise | Weekly cadence; group related contradictions into single issues |
| `gh` token scope insufficient for Contents API | Medium — silent 403 | Smoke test validates scope pre-launch; push.py checks HTTP status and suggests fix |

## Out of Scope

- Cross-organization federation (Phase 3)
- Conflict resolution UI (rich diff view)
- Offline/cached mode (agents require internet)
- Automatic resolution without manager approval (unless `auto-supersede: true`)
- Webhooks or real-time notifications (async curation is sufficient)
- Migration of existing local solutions to team brain (manual or separate command)
- Confidence decay over time (deferred — static scoring only in this iteration)
