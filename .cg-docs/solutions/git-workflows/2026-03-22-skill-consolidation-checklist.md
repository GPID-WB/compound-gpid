---
date: 2026-03-22
title: "Checklist for consolidating (merging/renaming) VS Code Copilot skills"
category: "git-workflows"
language: "both"
tags: [skills, copilot, consolidation, refactoring, instructions, SKILL.md]
root-cause: "No checklist existed for updating all cross-references when skills are merged or renamed"
severity: "P2"
---

# Skill Consolidation Checklist

## Problem

When two skills (`cg-skill-stata-core` + `cg-skill-stata-research`) were merged into
`cg-skill-stata-best-practices`, several cross-references were left pointing at the
deleted skills. The thorough review caught them, but they should have been caught at
merge time.

Symptoms that revealed the problem:
- `docs/reference.md` still listed two old skill rows
- `ROADMAP.md` still named the old skills in two places (lines 17–18 and 57)
- `.cg-docs/solutions/bugs/*.md` Related sections linked to deleted skill files
- `SKILL.md` grew to 412 lines with inline content that belonged in sub-files
- `.github/instructions/stata.instructions.md` contained GPID-specific variable names (`$gpid_root`, `gpid_fgt`) in a file intended to be project-generic

## Root Cause

No standardized checklist existed for "where to update when a skill is renamed or merged."
Changes were made to the new skill but the broader ecosystem of cross-references was not
swept before merging.

Additionally, the instruction file was written during a period when the project was
GPID-specific and never genericized before being shared.

## Solution

### Skill consolidation checklist

Run this checklist whenever a skill is merged, renamed, or removed:

1. **`docs/reference.md`** — Replace old skill rows with a single unified row.
2. **`ROADMAP.md`** — Search for old skill names; update both the checkbox list and phase descriptions.
3. **`.cg-docs/solutions/**/*.md` Related sections** — Search for old skill names in all solution files; update to new skill + section anchors.
4. **`.github/copilot-instructions.md`** — Check the skill routing table; remove or merge old entries.
5. **`.github/instructions/*.instructions.md`** — Search for old skill names in any `applyTo` patterns or inline references.
6. **`.github/agents/*.agent.md`** — Check if any agent explicitly loads the old skill.
7. **`.github/prompts/*.prompt.md`** — Check for old skill names in review/work prompts.
8. **`SKILL.md` of the new skill** — Must remain a routing table, not inline documentation. Target: ≤120 lines. Content belongs in sub-files under `references/` and `packages/`.

```powershell
# Quick grep to find stale references after a rename:
$old = "cg-skill-stata-core", "cg-skill-stata-research"
$old | ForEach-Object { git grep -l $_ }
```

### Generic examples in instruction files

Instruction files (`*.instructions.md`) apply to ALL projects that install Compound GPID,
not just GPID itself. Examples must use generic project identifiers:

| Wrong (GPID-specific) | Right (generic) |
|-----------------------|-----------------|
| `$gpid_root`          | `$project_root` |
| `${gpid_root}/output/logs/` | `${project_root}/output/logs/` |
| `gpid_fgt`            | `proj_measure`  |

### SKILL.md size discipline

A SKILL.md that exceeds ~150 lines almost certainly has inline content that belongs in
sub-files. The routing table should reference sub-files; it should not duplicate them.

| Metric | Target |
|--------|--------|
| SKILL.md lines | ≤120 |
| Inline code blocks in SKILL.md | 0 |
| Inline `##` sections in SKILL.md with >10 lines | 0 |

## Prevention

- Add the consolidation checklist above to the skill-merge PR template or plan doc.
- Before opening a PR for skill work, run: `git grep -l "<old-skill-name>"` to catch stale refs.
- When writing instruction files: no `gpid_` prefixes, no GPID-specific paths, no poverty-specific function names. Use `project_`, `proj_`, or descriptive placeholders.
- When a SKILL.md grows past 150 lines, route the overflow to an appropriate sub-file immediately rather than deferring.

## Related

- `.cg-docs/plans/2026-03-20-merge-stata-skills.md` — the merge plan that prompted this
- `.cg-docs/solutions/bugs/2026-03-19-copilot-hallucinates-stata-label-functions.md` — updated cross-refs
- `.cg-docs/solutions/bugs/2026-03-19-fragile-matrix-indexing-regression-results-stata.md` — updated cross-refs
- `docs/reference.md` — the canonical skill registry
- `.cg-docs/solutions/bugs/2026-04-08-hardcoded-r-hierarchy-in-agent-files-bypasses-dialect-config.md` — related: same "audit the whole hierarchy" principle applied to agent files during a dialect config migration
