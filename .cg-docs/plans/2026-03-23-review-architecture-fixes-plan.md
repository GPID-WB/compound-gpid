---
date: 2026-03-23
title: "Review architecture fixes — subagent hardening, anti-pattern dedup, stale plans"
status: completed
brainstorm: "N/A (external architecture review)"
language: "both"
estimated-effort: "medium"
tags: [review, agents, subagents, anti-patterns, documentation, architecture]
---

# Plan: Review Architecture Fixes

## Objective

Fix six concrete issues identified in an architecture review. Four are
mechanical edits to agent/prompt files. One is an anti-pattern deduplication.
One is a stale-status audit. Each task is independent — implement in any order.

## Context

- VS Code Copilot supports subagents (see
  https://code.visualstudio.com/docs/copilot/agents/subagents). Review agents
  are dispatched as subagents by `/cg-review`, which means they run in isolated
  context windows with their own tools and model. The subagent docs introduce
  three frontmatter properties we are not yet using: `tools` (restrict tool
  access), `user-invokable` (hide from dropdown), and `agents` (restrict which
  subagents a coordinator can call).
- The R skill split produced duplicated anti-pattern entries across
  `cg-skill-r-analytical` and `cg-skill-r-technical`.
- `/cg-resume` hardcodes a path that only works for local-machine installs.
- Note: the `.cg-docs/` gitignore issue identified in the same review was
  already resolved on 2026-03-23 (see
  `.cg-docs/solutions/git-workflows/2026-03-23-cg-docs-must-not-be-gitignored.md`).
- Note: the Stata skill was renamed from `cg-skill-stata-core` to
  `cg-skill-stata-best-practices`. This does not affect any task in this plan.

---

## Task 1: Add `tools` and `user-invokable` to all review agents

### Why

Review agents are read-only reviewers dispatched as subagents by `/cg-review`.
They should not have write access (they should never edit files), and they
should not appear in the VS Code agents dropdown (they are never invoked
directly by users — the 16 economists on the team don't need to see 9 review
agents they'll never call manually).

### Files to modify (9 files)

All files in `.github/agents/`:

1. `cg-code-quality.agent.md`
2. `cg-testing.agent.md`
3. `cg-documentation.agent.md`
4. `cg-version-control.agent.md`
5. `cg-reproducibility.agent.md`
6. `cg-performance.agent.md`
7. `cg-architecture.agent.md`
8. `cg-data-quality.agent.md`
9. `cg-learnings-researcher.agent.md`

### What to change

In the YAML frontmatter of each file, add two new properties. The result
should look like this (using `cg-code-quality` as an example):

```yaml
---
description: "Reviews code for style consistency, linting issues, DRY violations, and naming conventions. Trilingual R/Python/Stata."
model: Claude Haiku 4.5 (copilot)
tools: ['read', 'search']
user-invokable: false
---
```

Rules:
- Every review agent gets `tools: ['read', 'search']` — read-only access.
- Every review agent gets `user-invokable: false` — hidden from dropdown.
- Do NOT change `description` or `model` — leave those exactly as they are.
- Do NOT change anything in the body of the agent file.

### Acceptance criteria

- All 9 agent files have `tools: ['read', 'search']` in frontmatter.
- All 9 agent files have `user-invokable: false` in frontmatter.
- No other changes to agent files.

---

## Task 2: Add `agents` restriction to `/cg-review` prompt

### Why

The VS Code subagent docs warn that if agents have similar names or
descriptions, the model might select the wrong one. Adding the `agents`
frontmatter property to `/cg-review` makes dispatch deterministic.

### File to modify

`.github/prompts/cg-review.prompt.md`

### What to change

Add `tools` and `agents` properties to the YAML frontmatter. The updated
frontmatter should be:

```yaml
---
description: "Run multi-agent code review on recent changes. Produces prioritized P1/P2/P3 findings."
model: Claude Sonnet 4.6 (copilot)
tools: ['agent', 'read', 'search']
agents: ['cg-code-quality', 'cg-testing', 'cg-documentation', 'cg-version-control', 'cg-reproducibility', 'cg-performance', 'cg-architecture', 'cg-data-quality', 'cg-learnings-researcher']
---
```

Also add a comment inside the prompt body (near the top, before the Process
section) so future maintainers remember to keep the frontmatter in sync:

```markdown
<!-- When adding or removing review agents, update the `agents` list in the
     YAML frontmatter above to match. -->
```

Rules:
- `tools` must include `agent` (to invoke subagents), `read`, and `search`.
- `agents` must list all 9 review agents by exact name.
- Do NOT change `description` or `model`.
- Do NOT change anything else in the body of the prompt file.

### Acceptance criteria

- `/cg-review` frontmatter includes `tools` and `agents` properties.
- The `agents` list matches the 9 agent names exactly.
- A maintenance comment exists in the prompt body.
- No other changes to the prompt file body.

---

## Task 3: Fix hardcoded path in `/cg-resume`

### Why

`/cg-resume` hardcodes `C:\WBG\.compound-gpid\SCHEMA_VERSION` in Step 2.
Remote server users install to `$env:USERPROFILE\.compound-gpid`, so the
file won't exist at the hardcoded path and the schema check silently skips
with a misleading "old install" message.

### File to modify

`.github/prompts/cg-resume.prompt.md`

### What to change

Replace Step 2's path resolution. Find this text:

```
Read `SCHEMA_VERSION` from the global Compound GPID install at `C:\WBG\.compound-gpid\SCHEMA_VERSION`.

If the file does not exist, skip this check (old install — will be handled by `cg-update`).
```

Replace it with:

```
Locate the global Compound GPID `SCHEMA_VERSION` file. Check these paths in
order and use the first one that exists:

1. `C:\WBG\.compound-gpid\SCHEMA_VERSION` (local machine with OneDrive)
2. `$env:USERPROFILE\.compound-gpid\SCHEMA_VERSION` (remote server)

If neither path exists, this is either a very old install or the install
directory is non-standard. Warn the user:

> ⚠️ **Cannot locate Compound GPID installation.** Expected `SCHEMA_VERSION`
> at `C:\WBG\.compound-gpid\` or `$env:USERPROFILE\.compound-gpid\`. Run
> `cg-update` to verify your installation, or re-run `install.ps1`.

Do not silently skip this check.
```

### Acceptance criteria

- Step 2 checks two paths instead of one.
- Missing install produces a visible warning, not a silent skip.
- The rest of `/cg-resume` is unchanged.

---

## Task 4: Extract shared R anti-patterns into a common reference

### Why

`cg-skill-r-analytical/references/r-analytical-anti-patterns.md` and
`cg-skill-r-technical/references/r-technical-anti-patterns.md` both document
the same patterns: `set_collapse(mask = ...)`, `qDT()` after `fgroup_by`,
and `GRP()` pre-computation. Each file cross-references the other with
"see also the same pattern in [other file]." This is fragmentation.

### What to do

1. **Create** a new shared reference file at:
   `.github/skills/cg-skill-r-shared/references/collapse-anti-patterns.md`

   This file should contain ONLY the anti-patterns that are currently
   duplicated in both skills:
   - `set_collapse(mask = ...)` — never use masking
   - `qDT()` after `fgroup_by` pipe — required to avoid overallocation warning
   - `GRP()` pre-computation — reuse grouping objects across multiple calls

   Copy the content from either existing file (they are identical for these
   patterns). Do not add new content.

2. **Create** the skill folder and a minimal `SKILL.md` at:
   `.github/skills/cg-skill-r-shared/SKILL.md`

   Content:
   ```markdown
   ---
   name: cg-skill-r-shared
   description: "Shared R references used by both cg-skill-r-analytical and cg-skill-r-technical. Not loaded directly — consumed via cross-references."
   ---

   # R Shared References

   This skill contains reference material shared across R skills.

   ## References

   - [collapse Anti-Patterns](references/collapse-anti-patterns.md) — Patterns that apply to all R code using collapse, regardless of whether the work is analytical or technical.
   ```

3. **Edit** `cg-skill-r-analytical/references/r-analytical-anti-patterns.md`:
   - Remove the three duplicated anti-pattern sections (mask, qDT, GRP).
   - At the top of the `## collapse Anti-Patterns` section, add:
     ```markdown
     > **Shared collapse anti-patterns** (masking, `qDT()`, `GRP()` pre-computation)
     > are in [`cg-skill-r-shared/references/collapse-anti-patterns.md`](../../cg-skill-r-shared/references/collapse-anti-patterns.md).
     > The patterns below are specific to analytical work.
     ```
   - Keep all anti-patterns that are specific to analytical work (e.g.,
     "Using unweighted means for published statistics", "Averaging the
     poverty gap only among the poor", "Losing track of PPP units",
     "Aggregate-then-merge instead of using TRA" with its welfare framing).

4. **Edit** `cg-skill-r-technical/references/r-technical-anti-patterns.md`:
   - Remove the three duplicated anti-pattern sections (mask, qDT, GRP).
   - At the top of the `## collapse Anti-Patterns` section, add:
     ```markdown
     > **Shared collapse anti-patterns** (masking, `qDT()`, `GRP()` pre-computation)
     > are in [`cg-skill-r-shared/references/collapse-anti-patterns.md`](../../cg-skill-r-shared/references/collapse-anti-patterns.md).
     > The patterns below are specific to technical work.
     ```
   - Keep all anti-patterns specific to technical work (e.g.,
     "Aggregate-then-merge instead of using TRA" with its performance framing,
     package dev anti-patterns, plumber anti-patterns).

5. **Update** `docs/reference.md` — add `cg-skill-r-shared` to the Skills
   table:
   ```
   | `cg-skill-r-shared` | Shared R references (collapse anti-patterns) used by both analytical and technical skills |
   ```

### Acceptance criteria

- No duplicated anti-pattern content between the two R skill files.
- Shared file exists and contains exactly the patterns that were duplicated.
- Both skill-specific files reference the shared file.
- Skill-specific anti-patterns remain in their respective files.
- `docs/reference.md` lists the new skill.

---

## Task 5: Audit and fix stale plan statuses

### Why

`/cg-resume` scans `.cg-docs/plans/` for `status: active` plans. If
superseded or completed plans still say `status: active`, `/cg-resume` will
surface them as pending work.

### What to do

1. Scan every `.md` file in `.cg-docs/plans/`.
2. Read the YAML frontmatter of each.
3. For each file, check:
   - Does the frontmatter contain `supersedes:` referencing another plan?
     If so, find the referenced plan and verify its status is
     `status: superseded` (not `status: active`).
   - Has the plan clearly been completed (all implementation steps done,
     features are in the codebase)? If so, change `status: active` to
     `status: completed`.
4. Report which files were changed and why.

Known candidates to check:
- `2026-03-02-rename-prefix-and-documentation.md` — still `status: active`
  but all renames are clearly complete in the codebase.
- `2026-03-03-global-install-and-project-setup.md` — likely superseded by
  the v2 plan.
- `2026-03-03-global-install-and-project-setup-v2.md` — the v2 file has
  `supersedes:` pointing to the original. Check whether the original's
  status was updated.
- `2026-03-04-per-subdirectory-junctions.md` — likely completed (junction
  system is working).
- `2026-03-05-cg-docs-migration-and-resume.md` — likely completed (migration
  done, `/cg-resume` exists).
- `2026-03-13-clm-onedrive-install-fix.md` — likely completed (CLM fix
  is in place).
- `2026-03-16-cg-fixbug-prompt.md` — likely completed (`/cg-fixbug` exists).
- `2026-03-19-release-automation.md` — already marked `status: completed`.
- `2026-03-23-fix-cg-docs-gitignore.md` — likely completed (fix is deployed,
  solution doc exists).

### Acceptance criteria

- No plan has `status: active` if it has been superseded or completed.
- Superseded plans have `status: superseded`.
- Completed plans have `status: completed`.

---

## Task 6: Trim ROADMAP.md to actionable scope

### Why

Phases 3–5 list ~40 unchecked items, most solving problems nobody on the
team has encountered. With 3 testers active and 16 economists not yet using
the tool, this creates scope illusion. The roadmap should reflect what's
real.

### File to modify

`ROADMAP.md`

### What to change

1. **Phase 1** — leave as-is (all items checked, accurately reflects current
   state).

2. **Phase 2 (Analytical Quality)** — keep the existing items. This is the
   next actionable phase. No changes.

3. **Phases 3, 4, and 5** — collapse each into a single short paragraph
   (2–3 sentences max) describing the direction, NOT an item-by-item
   checklist. The paragraph should say what the phase is about and that
   specific items will be scoped when adoption data from earlier phases
   exists.

   Example for Phase 3:
   ```markdown
   ## Phase 3: Research Workflow

   End-to-end research support: literature search, data exploration,
   reproducibility audits, writing support, and revision tracking. Specific
   features will be scoped after Phase 2 tools are in active use by the
   analytical team.
   ```

4. **Archived / Deferred** section — keep as-is.

### Acceptance criteria

- Phase 1 unchanged.
- Phase 2 unchanged.
- Phases 3–5 are each 2–3 sentences, no unchecked item lists.
- Archived / Deferred section unchanged.

---

## Task 7: Enhance `cg-link` to remove old `.cg-docs/` gitignore entries

### Why

On 2026-03-23, `.cg-docs/` was removed from the gitignore to ensure
institutional knowledge is committed. However, projects that were set up
before this date still have the old gitignore entries:

```
# Compound GPID knowledge base (local thinking artifacts, typically not committed)
.cg-docs/
```

When users run `cg-link` on existing projects, these stale lines remain in
`.gitignore`, silently preventing `.cg-docs/` from being committed. Users
don't realize the knowledge base isn't being tracked.

### File to modify

`scripts/link.ps1`

### What to change

Add a cleanup step near the end of the linking process (after junctions are
created, before success message). The step should:

1. Check if `.gitignore` exists in the project root.
2. If it exists, read the entire file.
3. Remove the paired comment and entry:
   ```
   # Compound GPID knowledge base (local thinking artifacts, typically not committed)
   .cg-docs/
   ```
4. Write the cleaned content back to `.gitignore`.
5. If the file becomes empty after cleanup, delete `.gitignore`.
6. After cleanup, print a message:
   ```
   Cleaned up stale .cg-docs/ entry from .gitignore
   ```

Rules:
- Match the comment + entry as a unit (both lines together).
- Use case-insensitive matching for the comment (user might have tweaked it).
- Preserve all other gitignore entries exactly as-is.
- Only run this cleanup if `.gitignore` exists.
- If the file is empty after removal, delete it (git doesn't track empty files).

### Acceptance criteria

- `cg-link` removes both the comment line and `.cg-docs/` entry from
  `.gitignore`.
- All other gitignore entries are preserved.
- Empty `.gitignore` file is deleted after cleanup.
- A confirmation message is printed.
- No errors if `.gitignore` doesn't exist (skip silently).

---

## Testing Strategy

- **Tasks 1–3**: Structural validation only. After edits, grep each modified
  file for the expected frontmatter properties. No runtime tests.
- **Task 4**: Verify no duplicated content by searching both skill files for
  the key phrases (`set_collapse(mask`, `qDT()`, `GRP()`). They should only
  appear in the shared file.
- **Task 5**: Run `grep -r "status: active" .cg-docs/plans/` and verify each
  result is genuinely active.
- **Task 6**: Visual inspection of rendered markdown.
- **Task 7**: Manual test — create a test project with stale `.cg-docs/`
  entry in `.gitignore`, run `cg-link`, and verify the entry is removed.

## Documentation Checklist

- [ ] `docs/reference.md` updated with `cg-skill-r-shared` (Task 4)
- [ ] `docs/reference.md` agents table — add "Tools" column noting
      `read, search` for all review agents (optional, low priority)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `tools: ['read', 'search']` too restrictive for some agents | All review agents are read-only by design. If an agent needs write access, it's not a review agent. |
| `user-invokable: false` not supported in current Copilot version | Property is documented as of VS Code 1.109 (Jan 2026). If unsupported, it's silently ignored — no breakage. |
| `agents` list in `/cg-review` goes stale when agents are added/removed | Maintenance comment in the prompt body reminds to update the list. |
| Shared anti-patterns skill not loaded automatically | It's consumed via cross-references, not loaded directly. Both R skills point to it. |

## Out of Scope

- Moving `cg-learnings-researcher` from thorough-only to standard reviews
  (adoption decision, needs usage data).
- Removing `compound-engineering` plugin files from project knowledge
  (separate cleanup task).
