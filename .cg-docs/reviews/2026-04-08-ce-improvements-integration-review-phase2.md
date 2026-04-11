---
plan: .cg-docs/plans/2026-04-08-ce-improvements-integration.md
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
---

## Review Report

**Review depth**: thorough  
**Commit**: `9480983 feat(prompts): add ideation, adversarial review, compound-refresh; extract templates`  
**Files reviewed**: 15  
**Findings**: 2 blocking · 7 critical · 7 important · 5 minor  
**Test suite**: 757/757 passing at time of review

---

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-reproducibility/cg-architecture] `.github/prompts/cg-setup.prompt.md`:77,124,134,159,166,203,229 — References `docs/setup-templates.md` at 7 locations, but `docs/` is outside the junction boundary.
  **Why**: `cg-link` junctions only `.github/` subdirectories (`prompts/`, `skills/`, `agents/`, `instructions/`) into user projects. The `docs/` directory is NOT junctioned. When `/cg-setup` runs in any linked user project, every `Read \`docs/setup-templates.md\`` instruction will target a file that doesn't exist at `<user_project>/docs/setup-templates.md`. This silently breaks the configuration workflow for the entire user population.
  **Fix**: Move `docs/setup-templates.md` → `.github/prompts/setup-templates.md` (inside the junctioned tree). Update all 7 references in `cg-setup.prompt.md` from `docs/setup-templates.md` to `setup-templates.md` (relative to the prompts dir, or full path `.github/prompts/setup-templates.md`). Update the test path in `roadmap.Tests.ps1`.

- **[P0.2]** [cg-reproducibility/cg-architecture] `.github/prompts/cg-resume.prompt.md`:~147,~170 — References `docs/resume-templates.md` at Steps 3 and 4. Same junction boundary violation as P0.1.
  **Why**: Same root cause as P0.1. `/cg-resume` is the session bootstrap command used in every session. Silently breaking it in all user projects means no one can resume work using the plugin's guidance.
  **Fix**: Move `docs/resume-templates.md` → `.github/prompts/resume-templates.md`. Update all 2 references in `cg-resume.prompt.md`.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality] `.github/agents/cg-adversarial.agent.md`:49-66 — ADV output format `### [P0|P1|P2]-ADV-<N>: <title>` is incompatible with the review orchestrator parser.
  **Why**: `cg-review.prompt.md` Step 2.5 checks for `**[P0.`/`**[P1.`/`**[P2.`/`**[P3.` entries to verify agent output is usable. Step 3.5 parses the same patterns to build the YAML `findings:` map. `/cg-fix-triage` expects IDs of the form `P1.1`. The ADV format matches none of these patterns — ADV findings will always fail the step 2.5 quality check ("incomplete review"), be excluded from the consolidated report, absent from the YAML frontmatter, and unreachable by `/cg-fix-triage`.
  **Fix**: Change the output format block (lines 49-66) to use the standard format:
  ```
  - **[P0.{N}]** [cg-adversarial] `<file>`:<line> — <title>
    **Attack vector**: <trigger>
    **Impact**: <consequence>
    **Proof**: <minimal reproducer>
    **Fix**: <concrete fix>
  ```
  The `Attack vector` / `Proof` fields are preserved as indented bullets under a standard parseable header.

- **[P1.2]** [cg-data-quality/cg-architecture] `.github/prompts/cg-compound-refresh.prompt.md`:13 — File Permissions says "You may modify files in `.cg-docs/solutions/` (update, consolidate, or **delete**)" but Rules section says "**Never hard-delete** a solution file."
  **Why**: The word "delete" in the Permissions section grants explicit permission for an action that the Rules section later prohibits. An LLM reading permissions first may delete (hard-delete) a file before encountering the prohibition. The classification table compounds this: it names the tier `Delete` and shows it in the audit table with the Delete label. Line 99 has a parenthetical `(never hard-delete)` that a non-attentive pass can miss.
  **Fix**: (1) Line 13: change `or delete` → `or archive to \`.cg-docs/archive/\``. (2) Classification table line 72: rename the tier from `Delete` to `Archive`. Update all occurrences of `Delete` in this context (lines 72, 88, 99, 122) to `Archive`.

- **[P1.3]** [cg-testing] `tests/model-assignments.Tests.ps1`:104,108,117,121 — Hardcoded stem arrays are stale: still list "12 prompt file stems" and "10 agent file stems", missing `cg-compound-refresh`, `cg-ideate`, and `cg-adversarial`.
  **Why**: The sentinel counts were correctly updated (12→14 prompts, 10→11 agents), and dynamic discovery validates model: frontmatter for all files. But the guide-reference test at lines 103-128 only checks model-guide.md completeness for the explicitly listed stems. With the 3 new stems absent from the arrays, `docs/model-guide.md` can be missing their rows and the test will still pass.
  **Fix**: Add the 3 new stems:
  ```powershell
  # Line 104 comment: update to "All 14 prompt file stems"
  $promptStems = @(
      'cg-strategy', 'cg-brainstorm', 'cg-plan', 'cg-work', 'cg-review',
      'cg-fixbug', 'cg-release', 'cg-compound', 'cg-fix-triage',
      'cg-setup', 'cg-devtag', 'cg-resume',
      'cg-compound-refresh', 'cg-ideate'
  )
  # Line 117 comment: update to "All 11 agent file stems"
  $agentStems = @(
      'cg-architecture', 'cg-performance', 'cg-data-quality', 'cg-code-quality',
      'cg-testing', 'cg-documentation', 'cg-version-control', 'cg-reproducibility',
      'cg-learnings-researcher', 'cg-roadmap',
      'cg-adversarial'
  )
  ```

- **[P1.4]** [cg-testing] `docs/model-guide.md`:3 — Header says "22 Compound GPID prompt and agent files"; drift protection comment also says "all 22 files". Actual count is 25 (14 prompts + 11 agents). Missing rows for `cg-compound-refresh`, `cg-ideate`, and `cg-adversarial`.
  **Why**: The drift protection tests (lines 103-128 in model-assignments.Tests.ps1) check that guide mentions each stem — once P1.3 is fixed, those tests will begin failing until this file is updated. Current state: tests pass but only because the new stems aren't in the checked list.
  **Fix**: (1) Update the count to 25 in line 3 and the drift protection comment. (2) Add rows to the Prompts table for `cg-compound-refresh` (Sonnet, confirmed) and `cg-ideate` (Opus, confirmed). (3) Add row to the Agents table for `cg-adversarial` (Sonnet, `tools: []` intentional restriction).

- **[P1.5]** [cg-reproducibility] `tests/roadmap.Tests.ps1`:688 — CWD-relative path `".\docs\setup-templates.md"` will silently fail if tests are not run from the repo root.
  **Why**: The `$repoRoot` variable is defined at the top of this test file (via `$env:CG_TEST_ROOT` fallback) precisely to avoid CWD-sensitive paths. The prior version also used a relative path (`.github\prompts\cg-setup.prompt.md`) with the same risk — this was a pre-existing pattern — but the fix should use `$repoRoot`.
  **Fix**: Change line 688 to:
  ```powershell
  $setupTemplates = Get-Content (Join-Path $repoRoot "docs\setup-templates.md") -Raw
  ```

- **[P1.6]** [cg-documentation] `.github/prompts/cg-compound-refresh.prompt.md`:93-110 — Step 5 (Interactive Resolution) has no guidance for user rejection. Step 6 (Summary) assumes changes were made.
  **Why**: If the user declines all proposed actions (e.g., keeps all solutions as-is), the prompt reaches Step 6 without any results to summarize. The existing summary table (`Kept/Updated/Consolidated/Replaced/Archived`) only makes sense when actions occurred. A user who declined everything has no clear completion path.
  **Fix**: Add an explicit "Skip All" branch to Step 5 and make Step 6 conditional:
  ```markdown
  - **Skip**: Hold for later — no change made. Document the deferral in the summary.
  
  ### Step 6: Summary
  If any changes were made: [existing summary table]
  If no changes were made (all deferred or skipped):
  > Knowledge base audit complete. No changes made. Re-run `/cg-compound-refresh` when ready to act.
  ```

- **[P1.7]** [cg-documentation] `docs/reference.md`:prompt table — `/cg-ideate` is listed after `/cg-compound-refresh`, contradicting `docs/workflow.md` which shows Ideate at position 0 (immediately after Strategy, before Brainstorm).
  **Why**: New users reading the reference table will learn a different workflow sequence than what the workflow diagram teaches. `/cg-ideate` is a discovery step that precedes planning; `/cg-compound-refresh` is a maintenance step that follows completed work.
  **Fix**: Reorder the reference table so `/cg-ideate` appears after `/cg-strategy` and before `/cg-brainstorm`. Move `/cg-compound-refresh` to after `/cg-compound`.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture] `.github/agents/cg-adversarial.agent.md`:7 — `tools: []` prevents the adversarial reviewer from issuing `read_file` calls during review.
  **Why**: A past solution (`.cg-docs/solutions/bugs/2026-03-30-cg-review-missing-write-tool-disables-file-creation.md`) documents exactly this failure mode. The adversarial agent must rely on what the orchestrator pre-loaded into context. For a review involving 15 scattered files, the orchestrator will not have loaded all file contents inline — the agent will review incomplete information with no error or warning.
  **Fix**: Remove the `tools: []` line completely. Omitting the key grants the agent all available read/write tools (the safe default). If intentional read-only restriction is desired, document the rationale explicitly in a comment and confirm the orchestrator promises to load all file contents before dispatch.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No `tools:` list assertions for `cg-compound-refresh.prompt.md` or `cg-ideate.prompt.md`.
  **Why**: Per the established pattern (`.cg-docs/solutions/testing-patterns/2026-03-30-test-prompt-frontmatter-tools-list.md`), every new prompt file must be audited and tested for tools: correctness on the same commit. Both new prompts write files (compound-refresh modifies `.cg-docs/solutions/`, ideate creates `.cg-docs/brainstorms/`) and need `write` in their tools list. If missing, file creation will fail silently.
  **Fix**: Add tools: validation for both new prompts to `prompt-tools.Tests.ps1`. First verify what tools each prompt body actually requires, then assert the declared tools list includes them.

- **[P2.3]** [cg-architecture] `.github/skills/cg-skill-r-testing/SKILL.md` — Passive Markdown hyperlinks to `references/*.md` don't trigger automatic loading.
  **Why**: The skill has "BLOCKING REQUIREMENT: load this SKILL.md immediately" in copilot-instructions.md. No equivalent instruction exists for the thinned reference files. Inline BDD patterns, `local_mocked_bindings()` signature, and fixture constructor examples are no longer in SKILL.md — the model must follow a link to get them. Markdown links are UI affordances; the model doesn't auto-follow them.
  **Fix**: Add explicit load instructions at each thinned section, e.g. "Before generating BDD-style tests, read `references/bdd.md` in this directory." The reference files are inside the junctioned `.github/skills/` tree, so they are accessible — the problem is trigger, not access.

- **[P2.4]** [cg-performance] `.github/prompts/cg-ideate.prompt.md`:31-43 — 3 parallel "explore agents" are instructed to "scan the codebase" with no directory scope constraints.
  **Why**: Each agent independently reads an unbounded set of files, consuming 3× the context tokens with no coordination. In a mature project (500+ files), each agent may exhaust its usable context window on file-reading before returning its 5-item summary.
  **Fix**: Scope each agent's scan to the directories most relevant to its frame: pain points → `tests/`, source dirs; architecture → project root, source dirs; quality → `docs/`, `.github/`.

- **[P2.5]** [cg-data-quality] `.github/prompts/cg-compound-refresh.prompt.md`:33-38 — Step 1 has no fallback for malformed or absent YAML frontmatter.
  **Why**: If a solution file is missing required fields (`date`, `title`, `status`), the agent will silently proceed with null/empty values, potentially misclassifying the solution. A file with completely absent frontmatter may be classified `Keep` by default.
  **Fix**: Add after the extraction bullet list: "If any required frontmatter field (`date`, `title`, `status`) is absent or unparseable, flag the file as `⚠ frontmatter-missing` and list it separately in the Step 4 audit table. Do not guess its classification — present it to the user for manual review."

- **[P2.6]** [cg-architecture] `.github/prompts/cg-ideate.prompt.md`:31-43 — "3 parallel explore agents" are anonymous inline role descriptions, not actual `@agent` dispatches.
  **Why**: `cg-review` dispatches named agents via `@cg-code-quality`, `@cg-architecture`, etc. — each backed by a `.agent.md` file. `cg-ideate`'s three "agents" are described inline with no corresponding files. When `cg-architecture.agent.md` is updated, the inline description won't track the change.
  **Fix** (minimal): Rename "Launch 3 parallel explore agents" to "Use 3 parallel analysis passes" to set accurate expectations without implying subagent dispatch. Or (comprehensive) dispatch actual named agents: `@cg-architecture`, `@cg-code-quality`, `@cg-testing`+`@cg-documentation`.

- **[P2.7]** [cg-documentation] `.github/skills/cg-skill-r-testing/SKILL.md`:~338 — Trailing whitespace (3 spaces) at end of the mocking section prose line.
  **Why**: "Replace external dependencies during testing with `local_mocked_bindings()`.   " — the trailing spaces could cause rendering differences in some Markdown parsers and indicate an unclean edit.
  **Fix**: Remove the 3 trailing spaces from the mocking section line.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `docs/reference.md` — `/cg-ideate` listed after `/cg-compound-refresh` in prompts table; ordering doesn't match the workflow diagram (Ideate → Brainstorm → Plan vs Compound → Refresh).
  **Why**: Resolved by the P1.7 fix. Listed here as a separate minor item because it affects table readability independently of the P1.7 structural issue.
  **Fix**: Apply the P1.7 reordering (same change).

- **[P3.2]** [cg-code-quality] `docs/resume-templates.md`:1-3 — Missing "Loaded on-demand — do not bulk-load at prompt start" warning present in `docs/setup-templates.md`.
  **Why**: `docs/setup-templates.md` has this on line 3; `docs/resume-templates.md` lacks it. Inconsistent defensive guidance for the same pattern.
  **Fix**: Add the warning to `docs/resume-templates.md` header (after the title and description line).

- **[P3.3]** [cg-performance] `.github/prompts/cg-setup.prompt.md` — `docs/setup-templates.md` loaded at 5+ separate `read_file` call sites across a single execution.
  **Why**: Each step that references a template issues an explicit load. Steps 4, 5, 6, 7, and both Mode B sections all carry `Read \`docs/setup-templates.md\`` instructions. Five redundant reads of the same 242-line file inflate token usage without adding information.
  **Fix**: Consolidate to a single load at the first reference (Step 4): "Read `docs/setup-templates.md` (used throughout Steps 4–7 and Mode B — load once here)." Change subsequent references to "Using the X Template from `setup-templates.md` (already loaded)."

- **[P3.4]** [cg-data-quality] `docs/setup-templates.md`:15 — `cg-schema-version: ""` emits a blank string with no defined valid values or migration procedure.
  **Why**: Currently dormant, but a future upgrade script reading this field may interpret `""` differently from `null` or absent — producing a silent upgrade path mismatch on fresh installs.
  **Fix**: Either (a) remove the field from the template until it has a defined use, or (b) populate it with the current schema version and document valid values in a comment.

- **[P3.5]** [cg-code-quality] `tests/roadmap.Tests.ps1`:688 — Double space: `$setupTemplates  = Get-Content` (two spaces before `=`).
  **Why**: Surrounding code uses single space. Minor style inconsistency that should be cleaned up when P1.5 is fixed (same line).
  **Fix**: Apply single-space alignment when rewriting the line for P1.5.

---

### ✅ Passed

- **cg-code-quality**: No P0/P1 issues. All new files have proper `model:` frontmatter keys. Sentinel counts correctly updated (12→14 prompts, 10→11 agents). Em-dash → ASCII hyphen in Run-Tests.ps1 is a valid cross-platform consistency fix.
- **cg-version-control**: No sensitive data, credentials, PII, or large files. Conventional commit format used. Branch naming follows convention. `.gitignore` coverage complete.
- **cg-performance**: Template extraction to `docs/` is a net positive — prompts no longer carry 242/115 lines of template content at startup. `cg-skill-r-testing` reference file split is correct lazy-loading.
- **cg-learnings-researcher**: 7 relevant past solutions identified. Key learnings applied (P0 junction issue, tools:[] pattern, prompt pipeline contract gaps). All applicable cross-reference audits surface real coverage gaps documented above.

---

### Learnings Cross-References

The following past solutions surfaced relevant context for this review:

| Solution | Category | Applied To |
|----------|----------|-----------|
| `2026-03-30-cg-review-missing-write-tool-disables-file-creation.md` | bugs | P2.1 (cg-adversarial tools:[]) |
| `2026-03-30-test-prompt-frontmatter-tools-list.md` | testing-patterns | P2.2 (missing tools: tests) |
| `2026-03-18-broken-relative-links-in-nested-skill-files.md` | bugs | P2.3 (SKILL.md reference links) |
| `2026-03-22-skill-consolidation-checklist.md` | git-workflows | P0.1/P0.2 (template extraction audit) |
| `2026-04-08-cross-cutting-enumeration-propagation-audit.md` | testing-patterns | P1.3/P1.4 (stem arrays stale) |
| `2026-03-30-prompt-pipeline-contract-testing.md` | testing-patterns | P2.2 (new prompts need tools: tests) |
