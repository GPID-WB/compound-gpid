---
date: 2026-05-22
plan: .cg-docs/plans/2026-05-22-compound-research-phase9-publication-output-agent.md
depth: standard
findings:
  P2.1: fixed
  P2.2: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: skipped
  P3.5: fixed
  P3.6: skipped
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
---

## Review Report

**Review depth**: standard
**Files reviewed**: 10 (commit `5068fe2` — Phase 9 review findings applied)
**Findings**: 13 (P0: 0, P1: 0, P2: 2, P3: 11)

### P0 — BLOCKING

*None.*

### P1 — CRITICAL

*None.*

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-documentation] `compound-gpid.md:54` — Charter "Current Focus" section still describes Phase 9 as "remains as planned future work"
  **Why**: Phase 9 was completed in commits `bffb918` (implementation) and `5068fe2` (review fixes). The outdated charter misleads the AI assistant and team members about what capabilities are live vs. planned, potentially causing duplicate effort.
  **Fix**: Update Current Focus to: *"Compound Research milestone — Phases 1–9 complete (module system, research workflow scaffolding, core CR agents, structural econometrics skills, ML-in-economics, academic writing & publication output, dedicated publication output review agent, reproducibility/replication, and integration polish & documentation). Engineering milestones (Workflow Maturity, Skills Enhancement) continue in parallel."*

- **[P2.2]** [cg-code-quality] `tests/model-assignments.Tests.ps1:40-90` — Near-duplicate `foreach` loop patterns (DRY violation)
  **Why**: Two `foreach` blocks (one for `$promptFiles`, one for `$agentFiles`) contain nearly identical structures: `Test-Path` + `Get-Frontmatter` + two `It` assertions each. Divergence risk: if the `model:` assertion pattern changes, both blocks must be updated independently.
  **Fix**: Extract a shared helper function (e.g., `Test-PromptOrAgentAssignment`) that accepts the file collection and description prefix, and call it twice. Or at minimum add a comment noting the intentional duplication.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-performance] `tests/model-assignments.Tests.ps1:51,82` — `Get-Frontmatter` called inside `It` blocks (execution-time reads)
  **Why**: 49 synchronous file reads deferred to test-execution time rather than Describe/foreach-body scope. In cold-cache CI environments each syscall adds latency.
  **Fix**: Hoist to foreach-body scope, guarded: `$frontmatter = if (Test-Path $filePath) { Get-Frontmatter -FilePath $filePath } else { '' }` before the `It` blocks.

- **[P3.2]** [cg-performance] `tests/model-assignments.Tests.ps1:160` — `Get-Content` + full line-split inside `It` block for frontmatter delimiter test
  **Why**: 50 execution-time file reads with an O(line-count) `Where-Object` scan (no early exit). Unnecessarily expensive.
  **Fix**: Hoist read outside `It`; replace line-split pipeline with a single `(?ms)^---\s*$.*?^---\s*$` `-match` on raw content.

- **[P3.3]** [cg-performance] `tests/cr-prompts.Tests.ps1` (~line 1712) — `[regex]::Match()` section-extraction called inside `It` blocks rather than at Describe scope
  **Why**: `$sec5Text` and `$sec6Text` are computed at test-execution time on each `It` invocation instead of once at `Describe` scope alongside `$content`.
  **Fix**: Declare `$sec5Text = [regex]::Match($content, '(?si)## 5\..*?(?=## 6\.)').Value` and `$sec6Text = ...` at `Describe` scope; reference them directly in the `It` bodies.

- **[P3.4]** [cg-performance] `tests/cr-prompts.Tests.ps1` — `cr-review.prompt.md` read 11 times across 11 separate `Describe` blocks
  **Why**: Pester 4 has no cross-`Describe` `BeforeAll`, so each `Describe` re-opens the file. All 11 reads are correctly outside `It` but structurally wasteful as the suite grows.
  **Fix**: `$script:crReviewContent = Get-Content (Join-Path $promptsDir "cr-review.prompt.md") -Raw -Encoding UTF8` at script scope; reference `$script:crReviewContent` in each `Describe`.

- **[P3.5]** [cg-code-quality] `tests/cr-prompts.Tests.ps1` — `$fm` / `$frontmatter` naming inconsistency
  **Why**: `cr-prompts.Tests.ps1` uses `$fm` in 17+ locations but `$frontmatter` in 3 (lines ~810, 820, 830); `model-assignments.Tests.ps1` uses `$frontmatter`. Two names for the same concept across the suite.
  **Fix**: Standardize on one name throughout. `$fm` is dominant in the file; replace the 3 `$frontmatter` occurrences with `$fm`.

- **[P3.6]** [cg-code-quality] `tests/cr-prompts.Tests.ps1` — Inconsistent aligned spacing in variable assignments
  **Why**: Some `Describe` setup blocks use aligned padding (`$fm      = Get-Frontmatter`) while others use plain `$fm = Get-Frontmatter`. Mixed style creates visual noise in diffs.
  **Fix**: Remove alignment padding; use `$fm = Get-Frontmatter` uniformly throughout.

- **[P3.7]** [cg-architecture] `.github/prompts/cr-review.prompt.md` — EDA dispatch row has a spurious third column
  **Why**: `| EDA | @cg-performance, @cg-data-quality | *(No CR agent — @cr-eda-reviewer planned for future phase)* |` has 3 pipe-delimited cells in a 2-column table. Renders as a ghost column in GitHub markdown.
  **Fix**: Move the comment inside cell 2: `| EDA | @cg-performance, @cg-data-quality *(No CR agent — @cr-eda-reviewer planned for future phase)* |`

- **[P3.8]** [cg-architecture] `tests/cr-prompts.Tests.ps1` — No test guards the `@cr-publication-output` entry in the Implementation dispatch row
  **Why**: P2.1 of the prior review added `@cr-publication-output` to the Implementation row. There is an explicit test for Tables/Figures routing but none for Implementation routing. A future edit dropping it would pass the suite silently.
  **Fix**: Add to the "Phase 9 dispatch journey" `Describe`: `It "Implementation dispatch row includes @cr-publication-output" { ($content -match 'Implementation.*cr-publication-output') | Should -Be $true }`

- **[P3.9]** [cg-architecture] `tests/cr-prompts.Tests.ps1` — No test guards the `[cr-publication-output]` tag in `cr-academic-writing` Check 6
  **Why**: P2.2 of the prior review changed Check 6's tag from `[cr-academic-writing]` to `[cr-publication-output]`. The existing cleanup test only checks heading text. A regression to the old tag would pass the suite silently.
  **Fix**: Add to the "cr-academic-writing.agent.md — Phase 9 cleanup" `Describe`: `It "Check 6 'Flag as' uses [cr-publication-output] tag" { ($content -match '\[cr-publication-output\]') | Should -Be $true }`

- **[P3.10]** [cg-data-quality] `roadmap.json` — 5 `compound-research` features have `status: "done"` but no `completed-date`
  **Why**: `cr-core-agents` (Phase 3), `cr-structural-econometrics-skills` (Phase 4), `cr-ml-economics` (Phase 5), `cr-writing-publication` (Phase 6), and `cr-reproducibility-replication` (Phase 7) are all `"done"` but lack `completed-date`. Only Phases 1, 2, 8, and 9 have it. The completion timeline is incomplete.
  **Fix**: Add `"completed-date"` to each entry. Dates from git history: Phases 3 & 4 → `"2026-05-14"`, Phase 5 → `"2026-05-20"`, Phases 6 & 7 → `"2026-05-22"`.

- **[P3.11]** [cg-code-quality] `docs/reference.md` — Research Review Agents table lacks count annotation
  **Why**: Other sections document artifact counts explicitly, but the Research Review Agents table has no count sentinel. With 9 CR agents now, a count comment would catch accidental omissions at a glance.
  **Fix**: Add `<!-- 9 research review agents (cr-*) -->` above the agent table.

### ✅ Passed

- **cg-testing**: No issues found — all new test assertions verified correct against actual file content; pending stub correctly declared
- **cg-version-control**: No issues found — conventional commit format, no secrets/absolute paths, clean atomicity
- **cg-reproducibility**: No issues found — relative paths throughout, consistent model assignments, date conventions followed
