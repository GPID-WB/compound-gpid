---
date: 2026-04-08
title: "Hardcoded R hierarchy in agent Expertise sections bypasses dialect configuration"
category: "bugs"
language: "R"
tags: [agents, r-syntax, dialect, copilot-instructions, configuration-drift, review-agents, tidyverse, data.table, collapse]
root-cause: "Agent .agent.md files carry self-contained Expertise sections that are not routed through r.instructions.md; hardcoded collapse > tidyverse hierarchy in three agents produced wrong review feedback on tidyverse projects"
severity: "P1"
---

# Hardcoded R Hierarchy in Agent Files Bypasses Dialect Config

Surfaced as P1.1–P1.3 in the thorough review of the R dialect skills architecture
feature (`2026-04-07-r-dialect-skills-architecture-review.md`). Three review agents
produced actively incorrect feedback on tidyverse projects after the dialect system
was added.

---

## Problem

When the R dialect skills architecture was introduced (new `r-syntax` field in
`compound-gpid.local.md`, dialect routing in `r.instructions.md`), three review
sub-agents were not updated:

- `cg-code-quality.agent.md` — line 12: *"Preference hierarchy: collapse >
  data.table > tidyverse"*
- `cg-data-quality.agent.md` — same hardcoded preference
- `cg-performance.agent.md` — same line, plus a review section asking
  *"Are `collapse` functions used instead of dplyr?"* as if dplyr were always wrong

**Symptoms on a `r-syntax: "tidyverse"` project:**

- `cg-code-quality` flagged correct `filter()`, `if_else()`, and dplyr joins as
  violations and suggested data.table replacements.
- `cg-data-quality` applied `checkmate` + data.table validation idioms to
  tibble-based code, ignoring the project's actual patterns.
- `cg-performance` raised false positives: marked `mutate()` + `summarize()` usage
  as "should use collapse", which is incorrect for a tidyverse project.

---

## Root Cause

Agent files (`.github/agents/*.agent.md`) carry **self-contained Expertise sections**
that are read directly by the sub-agent. They are **not** routed through
`r.instructions.md`.

The dialect routing change correctly updated `r.instructions.md` (which applies to
the main agent via `applyTo: **/*.R`) and introduced the new dialect skills. But
sub-agents read their own file's instructions — not the instruction file — so the
routing never reached them.

```
r.instructions.md   (main agent ← dialect-aware ✓)
         ↓ applyTo *.R
     main agent
         ↓ dispatches
  cg-code-quality.agent.md   ← reads OWN expertise section ← still hardcoded ✗
  cg-data-quality.agent.md   ← reads OWN expertise section ← still hardcoded ✗
  cg-performance.agent.md    ← reads OWN expertise section ← still hardcoded ✗
```

The three agent files were written before the dialect system existed and were not
included in the dialect refactoring scope.

---

## Solution

Each agent's Expertise section was updated to be **dialect-conditional**, following
the same pattern as `r.instructions.md`:

```markdown
# cg-code-quality (before fix)
- R: `collapse > data.table > tidyverse` preference hierarchy. Flag `ifelse()` ...

# cg-code-quality (after fix)
- R: Check `compound-gpid.local.md` for `r-syntax` to determine dialect before
  reviewing. For `data.table-collapse`: flag `ifelse()` instead of
  `fifelse()/fcase()`, missing `:=` for in-place mutation. For `tidyverse`: flag
  `%>%`, `.data$` pronoun usage, old-style `group_by()/ungroup()` chains, `ifelse()`
  instead of `if_else()`. Load dialect skills per `r.instructions.md` before
  reviewing any `.R` file.
```

```markdown
# cg-performance (before fix)
- R: ... "Are `collapse` functions used instead of dplyr?" (asked unconditionally)

# cg-performance (after fix)
- R: Check `compound-gpid.local.md` for `r-syntax` before reviewing. For all
  dialects: `collapse` for fast statistics (dialect-neutral, works on tibble and
  data.table equally). For `data.table-collapse` additionally: data.table
  performance (keys, GForce, `.SD` optimization, `fifelse`/`fcase`). Load dialect
  skills before reviewing.
```

The rename "collapse + data.table Optimization" → "Vectorization and Aggregation (R)"
was also applied, with dplyr flagging conditioned on dialect detection.

---

## Prevention

**When adding a new project-wide configuration dimension (like a dialect system),
ALL agents must be audited for hardcoded assumptions the config was designed to
replace.**

Unlike instruction files (`*.instructions.md`, which use `applyTo`) and skills
(which are loaded explicitly on demand), agent files carry self-contained expertise.
They will not automatically benefit from routing changes made elsewhere.

### Agent audit checklist for configuration migrations

Run this after adding any new behavioral config (dialect, language level, framework
preference):

1. **`r.instructions.md` / `python.instructions.md`** — update routing ✓ obvious
2. **`.github/agents/*.agent.md`** — search each Expertise section for hardcoded
   assumptions that the new config replaces. **This is the most commonly missed step.**
3. **`.github/skills/*/SKILL.md`** — check skill descriptions and load conditions
   for hardcoded assumptions (see P2.2 in the same review: `cg-skill-r-testing`
   had "Tidyverse is never used in test code" after dialect support was added)
4. **`copilot-instructions.md`** — check the skill routing table and agent
   descriptions for hardcoded language preferences

```powershell
# Quick check: find remaining hardcoded hierarchy mentions after a dialect migration
git grep -n "collapse > data.table > tidyverse" .github/
git grep -n "Preference hierarchy" .github/
```

---

## Related

- `.cg-docs/reviews/2026-04-07-r-dialect-skills-architecture-review.md` —
  thorough review that caught this (P1.1, P1.2, P1.3)
- `.cg-docs/solutions/git-workflows/2026-03-22-skill-consolidation-checklist.md` —
  related pattern for propagating changes through the agent/skill ecosystem
  (specifically about skill renames; the principle of "audit the whole hierarchy"
  applies here too)
- [`.cg-docs/solutions/bugs/2026-08-14-capability-eligibility-namespace-mismatch.md`](./2026-08-14-capability-eligibility-namespace-mismatch.md) —
  same theme: a configured selection silently short-circuits because two
  unrelated identifier namespaces are compared; normalize names and gate with
  tests.
