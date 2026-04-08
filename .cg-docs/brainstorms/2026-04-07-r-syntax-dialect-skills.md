---
date: 2026-04-07
title: "R Syntax Dialect Skills — Per-Project Syntax Selection"
status: decided
chosen-approach: "Dialect Skills with Instruction-Level Routing"
tags: [skills, r, architecture, tidyverse, data.table, collapse]
---

# R Syntax Dialect Skills — Per-Project Syntax Selection

## Context

The current R skills (`cg-skill-r-analytical`, `cg-skill-r-technical`) and
`r.instructions.md` enforce a hard hierarchy: collapse > data.table > tidyverse.
Tidyverse is positioned as a "fallback only."

This works for internal GPID team projects, but breaks down for collaborative
work with external coauthors who only know tidyverse. When a coauthor needs to
**read and review** the code, the entire project must be written in a syntax
they understand. The preference is per-project, not per-file.

Inspiration: the [posit-dev/skills](https://github.com/posit-dev/skills) repo
and [PR #43](https://github.com/posit-dev/skills/pull/43) (tidy-r skill by
@statzhero, reviewed by @gadenbuie) demonstrate reference-style skills organized
by topic.

## Requirements

1. **Per-project syntax selection**: User sets `r-syntax` in
   `compound-gpid.local.md`. Options: `data.table-collapse` (default) or
   `tidyverse`.
2. **Backward compatible**: Missing `r-syntax` field defaults to
   `data.table-collapse` — identical to current behavior.
3. **No conflicting signals**: When a user selects `tidyverse`, no file loaded
   by the model should say "prefer data.table over dplyr" or "tidyverse only
   as fallback."
4. **Syntax-neutral shared layer**: ggplot2, roxygen2, testthat, fixest,
   modelsummary, haven — all work the same regardless of dialect. These
   universal rules remain available to both dialects.
5. **Clean separation between instructions and skills**:
   - `r.instructions.md` = thin router (always loaded, low token cost)
   - Skills = deep reference material (loaded on demand)
6. **Dialect scope**: Affects data manipulation, aggregation, I/O, and
   reshaping. Does NOT affect visualization (ggplot2), econometrics (fixest),
   testing (testthat), or documentation (roxygen2).
7. **Full project consistency**: When `r-syntax: "tidyverse"` is set, the
   model writes tidyverse throughout — no mixing.

## Approaches Considered

### Approach 1: Dialect Skills with Instruction-Level Routing (CHOSEN)

Split R syntax knowledge into three standalone dialect skills
(`cg-skill-r-collapse`, `cg-skill-r-datatable`, `cg-skill-r-tidyverse`), make
`r.instructions.md` syntax-neutral, and route via the `r-syntax` field in
`compound-gpid.local.md`. Additionally, extract ggplot2 and other universal R
patterns from `r.instructions.md` into their own skills, leaving
`r.instructions.md` as a thin router.

**Architecture**:
- `r.instructions.md` → universal R routing rules only + directive to read
  `compound-gpid.local.md` for `r-syntax` and load matching skill(s)
- `cg-skill-r-collapse/` → collapse reference (extracted from current skills)
- `cg-skill-r-datatable/` → data.table reference (extracted from current skills)
- `cg-skill-r-tidyverse/` → tidyverse reference (new)
- `cg-skill-r-analytical` and `cg-skill-r-technical` → keep for domain
  knowledge (econometrics, APIs, etc.) but strip syntax preference hierarchy
- `compound-gpid.local.md` gets `r-syntax: "data.table-collapse" | "tidyverse"`
- `copilot-instructions.md` → update skill descriptions and loading logic
- New skills use `user-invocable: false` (background knowledge, not
  slash commands)

**Pros**:
- Clean separation — each dialect is self-contained
- Backward compatible — missing field defaults to current behavior
- No conflicting signals within any combination
- Follows posit-dev pattern of reference-style skills per topic
- `r.instructions.md` stays small (always-on cost minimized)

**Cons**:
- Three new skill folders to create and maintain
- Requires updating `cg-skill-r-analytical`, `cg-skill-r-technical`,
  `r.instructions.md`, `copilot-instructions.md`, and `/cg-setup`
- More complex skill ecosystem to understand

**Effort**: Large

### Approach 2: Two-Track Split (data.table-collapse vs tidyverse)

Keep data.table and collapse together as one merged dialect skill. Create one
new tidyverse skill. Route between the two.

**Pros**: Simpler (two dialects, not three). Less token overhead.
**Cons**: Collapse and data.table serve different purposes (statistics vs
manipulation); lumping them loses the ability to document each clearly.

**Effort**: Medium

### Approach 3: Tidyverse Overlay (Minimal Changes)

Add a tidyverse skill and an override directive, keep everything else as-is.

**Pros**: Fast to ship.
**Cons**: Conflicting signals — model sees "collapse > data.table > tidyverse"
and "use tidyverse" simultaneously. Unreliable enforcement.

**Effort**: Small

## Decision

**Approach 1** — Dialect Skills with Instruction-Level Routing.

Rationale: This is the structural refactoring that eliminates conflicting
signals. The added complexity is manageable because the project already has a
well-understood skills architecture, and the extra maintenance cost is offset
by cleaner, more reliable model behavior.

Extended decision: Also extract ggplot2 and other universal R patterns from
`r.instructions.md` into skills, making the instruction file a pure router.
This follows the design principle: instructions = short, always-on, universal
routing; skills = deep, on-demand, domain-specific reference material.

Key design decisions:
- **Default**: `r-syntax` absent → `data.table-collapse` (backward compatible)
- **No "all" option** in first iteration — pick one dialect per project
- **`user-invocable: false`** on dialect skills (background knowledge, not
  slash commands)
- **`/cg-setup`** will ask about R syntax preference when creating
  `compound-gpid.local.md`

## Next Steps

1. User provides reference material for `data.table` and `collapse` skills
   (save to `.cg-docs/brainstorms/` as working files)
2. Run `/cg-plan` to create a detailed implementation plan covering:
   - New skill creation (collapse, data.table, tidyverse, ggplot2)
   - Refactoring of existing skills (r-analytical, r-technical)
   - Updates to r.instructions.md (thin router)
   - Updates to copilot-instructions.md (skill descriptions, routing)
   - Updates to /cg-setup (r-syntax question)
   - Schema version bump for compound-gpid.local.md
3. Implement skills in order: data.table → collapse → tidyverse → ggplot2 →
   refactor existing → update routing
