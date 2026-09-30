---
date: 2026-07-29
title: "Compound Research module migration from v0.10 branch to v1.0 main"
status: decided
scope: "Deep"
chosen-approach: "Cherry-Pick New Files + Fresh Integration (Approach 3) with phased integration"
tags: [git-workflow, migration, compound-research, v1-integration, branch-strategy]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Compound Research Module Migration to v1.0

## Context

The `compound-research` branch developed the CR module (9 agents, 5 prompts, 12 skills, 4 instructions, 1 test file, plus extensive .cg-docs artifacts) on top of v0.10.2. Meanwhile, the primary developer released v1.0.0–v1.0.3 on `main` with 268 commits of changes including:

- Major new `.agents/` Codex adapter structure (generated from `.github/`)
- New features: brain-rebuild, commit-push-pr, wiki, token-audit, verify-pr, issues
- Shared contracts: review-routing, context-loading, goal-execution, active-state, model-catalog
- Model frontmatter assignments (GPT-5.4 for review, GPT-5.3-Codex for coding)
- Native packaging with security safeguards

The `compound-research` branch is 61 commits ahead and 268 behind `origin/main`. All 61 files modified by CR were also modified by main — making merge/rebase impractical. The intellectual content (research logic, agent behaviors, skill content) is what matters; integration glue will be re-applied against v1.0.

## Requirements

- Personal working branch starting from `origin/main` (v1.0.3)
- All CR-only files (new agents, skills, prompts, instructions, test) ported verbatim
- All `.cg-docs/` artifacts (brainstorms, plans, reviews, solutions, strategy) carried over as historical documentation — not updated
- CR module integrated with v1.0 systems: brain, review routing, model catalog, Codex adapter, context-loading contracts
- All existing main tests continue passing
- CR-specific tests updated to work with v1.0 structure
- Modifications to existing `cg-*` agents/prompts done fresh against v1.0 versions

## Approaches Considered

### Approach 1: Fresh Branch + File Copy + Sequential Integration
Create new branch from main, manually copy CR files one-by-one, then integrate.

- Pros: Clean history, no conflicts, each step reviewable
- Cons: Slower initial setup than cherry-pick
- Effort: Large

### Approach 2: Rebase with Selective Squash
Squash CR commits into logical groups, then interactive-rebase onto main.

- Pros: Preserves some commit authorship
- Cons: 61 bilateral file conflicts would produce stale v0.10 integration code requiring full rewrite. Double the work. High risk of merge artifacts.
- Effort: Very large (conflict resolution + rewrite)

### Approach 3: Cherry-Pick New Files + Fresh Integration (CHOSEN)
Use `git checkout compound-research -- <files>` to pull CR-only files onto a fresh branch from main. Skip all modifications to existing files. Do integration fresh against v1.0.

- Pros: Fastest to clean starting point. One command pulls all new files. Zero conflict risk. Clean provenance.
- Cons: Same integration work as Approach 1
- Effort: Medium (fast port) + Large (phased integration)

## Decision

**Approach 3 with phased integration**. The integration work is split into phases to reduce risk per commit and get CR self-contained and working before deep v1.0 integration.

## Next Steps

### Phase 1: Port CR Content (zero conflict, fast)
1. Create branch `feat/compound-research-v2` from `origin/main`
2. `git checkout compound-research --` all CR-only files:
   - `.github/agents/cr-*.agent.md` (9 files)
   - `.github/prompts/cr-*.prompt.md` (5 files)
   - `.github/skills/cr-skill-*/SKILL.md` (12 skill directories)
   - `.github/instructions/latex.instructions.md`, `math.instructions.md` (only these 2 are CR-only)
   - `tests/cr-prompts.Tests.ps1`
3. **Selective** .cg-docs port — only CR-specific artifacts (do NOT overwrite main's Brain files, active-state, etc.):
   - CR-specific brainstorm: `.cg-docs/brainstorms/2026-05-13-compound-research-extension.md`
   - CR plans: `.cg-docs/plans/2026-05-14-compound-research-*.md`, `.cg-docs/plans/2026-05-20-*.md`, `.cg-docs/plans/2026-05-22-*.md`
   - CR reviews: `.cg-docs/reviews/2026-05-14-compound-research-*.md`, `.cg-docs/reviews/2026-05-15-*.md`, `.cg-docs/reviews/2026-05-20-*.md`, `.cg-docs/reviews/2026-05-22-*.md`
   - CR solutions: `.cg-docs/solutions/bugs/2026-05-14-*`, `.cg-docs/solutions/bugs/2026-05-20-*`, `.cg-docs/solutions/bugs/2026-05-22-*`, `.cg-docs/solutions/data-quality/2026-05-14-*`, `.cg-docs/solutions/data-quality/2026-05-20-*`, `.cg-docs/solutions/data-quality/2026-05-21-*`, `.cg-docs/solutions/testing-patterns/2026-05-14-*`, `.cg-docs/solutions/testing-patterns/2026-05-20-*`, `.cg-docs/solutions/testing-patterns/2026-05-21-*`, `.cg-docs/solutions/testing-patterns/2026-05-22-*`
   - CR strategy: `.cg-docs/strategy/2026-05-14-compound-research-roadmap.md`
4. Commit: `feat(cr): port compound-research intellectual content from v0.10 branch`

**NOT ported in Phase 1** (handled in Phase 2 as integration):
- `python.instructions.md`, `r.instructions.md`, `stata.instructions.md` — these exist on main; CR only added `module: shared` frontmatter. Re-apply against v1.0 versions.
- `copilot-instructions.template.md` — CR adds `{{modules}}` and "Active Modules" section. Merge into main's version.
- Any modifications to existing `cg-*` agents, prompts, or `copilot-instructions.md`.

**Note on skill structure**: Main's skills now use sub-directories (`references/`, `workflows/`). CR skills are flat (`SKILL.md` only). This is fine for initial port — expand to sub-directory structure later if desired for consistency.

### Phase 2: Basic CR Registration (self-contained CR working)
1. Add CR module documentation to `copilot-instructions.md` (skill references, `/cr-*` command table, research task taxonomy, CR agents list, research integrity priority)
2. Merge CR additions into `copilot-instructions.template.md` (add `{{modules}}` variable and "Active Modules" section to main's existing template)
3. Add `module: shared` frontmatter to `r.instructions.md`, `python.instructions.md`, `stata.instructions.md` (trivial — just a frontmatter field addition to main's versions)
4. Update `compound-gpid.md` Current Focus to reference CR module
5. Adopt v1.0 `context-loading.contract.md` staged policy in CR prompts (add Stage 0/1 reads to `/cr-*` Step 0 sections)
6. Verify: CR prompts (`/cr-brainstorm`, `/cr-plan`, `/cr-work`, `/cr-review`, `/cr-compound`) dispatch correctly in isolation
7. Update `cr-prompts.Tests.ps1` for any path/structure changes in v1.0

### Phase 3: Review Routing Integration
1. Add `research` mode to `.github/shared/review-routing.contract.md` (or `.agents/shared/`)
2. Update `/cg-review` prompt to detect research tasks and dispatch CR agents alongside cg agents
3. Add research risk class to routing contract trigger taxonomy
4. Test: `/cg-review` on research code dispatches appropriate CR agents

### Phase 4: Model Catalog + Agent Frontmatter
1. Add `model:` frontmatter to all 9 CR agents (per model-catalog.json conventions)
2. Add CR model assignments to model-catalog.json if needed
3. Verify agent dispatch respects model assignments

### Phase 5: Brain + Shared Contracts Integration
1. Add "Consult Brain" steps to CR prompts where appropriate (`/cr-review`, `/cr-work`)
2. Ensure `cg-skill-brain-query` is referenced in CR skill loading paths
3. Adopt `active-state.contract.md` in `/cr-work` (write active-state JSON on workflow start/completion, enabling `/cg-resume` to pick up CR work)
4. Test brain consultation works for research-domain queries

### Phase 6: Codex Adapter Generation
1. Add CR commands to the generation pipeline (`.agents/commands/cr-*.md`)
2. Add CR agents to `.agents/subagents/cr-*.toml`
3. Add CR skills to `.agents/skills/cr-skill-*/SKILL.md`
4. Update `.compound-gpid-generated.json` with CR entries
5. Verify Codex adapter is complete and consistent

### Phase 7: Cross-Integration Polish
1. Update existing `cg-*` agents to be research-aware (existing agents like cg-reproducibility, cg-data-quality should recognize research context)
2. Update `cg-work.prompt.md` to handle research tasks or redirect to `/cr-work`
3. Final test pass — all existing + CR tests green
4. Update `roadmap.json` to reflect CR milestone on v1.0
