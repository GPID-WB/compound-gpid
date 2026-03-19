---
date: 2026-03-18
title: "Broken relative links in deeply-nested skill files pointing to repo root"
category: "bugs"
language: "both"
tags: [markdown, links, relative-paths, skill-files, documentation, cross-references]
root-cause: "Links authored as if relative to the repo root (e.g. '.cg-docs/...') but resolved relative to the file's actual location 4 directories deep inside .github/skills/"
severity: "P2"
---

# Broken Relative Links in Deeply-Nested Skill Files Pointing to Repo Root

## Problem

A cross-reference link in `r-analytical-anti-patterns.md` read:

```markdown
[collapse na.rm solution](.cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md)
```

This path resolves *relative to the file's location*, which is:
`.github/skills/cg-skill-r-analytical/references/`

So the link actually resolves to:
`.github/skills/cg-skill-r-analytical/references/.cg-docs/solutions/...` — which does not exist.

The link was silently broken. GitHub renders it as a dead link; clicking it returns a 404.

## Root Cause

When authors write cross-references in skill files they often think in terms of repo-root paths
(`.cg-docs/...`, `.github/...`). But Markdown resolves relative links from the *file's own
directory*, not the repo root.

Skill files sit at:
```
.github/skills/<skill-name>/references/<file>.md      # 4 levels deep
.github/skills/<skill-name>/workflows/<file>.md        # 4 levels deep
```

To reach the repo root from these files, every relative upward link needs exactly 4 `../` segments.

## Solution

**Before (broken)**:
```markdown
[collapse na.rm solution](.cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md)
```

**After (fixed)**:
```markdown
[collapse na.rm solution](../../../../.cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md)
```

### Depth reference table for skill files

| File location | Prefix to reach repo root |
|---------------|--------------------------|
| `.github/skills/<skill>/references/<file>.md` | `../../../../` |
| `.github/skills/<skill>/workflows/<file>.md` | `../../../../` |
| `.github/skills/<skill>/SKILL.md` | `../../../` |
| `.github/agents/<file>.md` | `../../` |
| `.github/instructions/<file>.md` | `../../` |
| `.cg-docs/solutions/<category>/<file>.md` | `../../../` |

## Prevention

- When writing cross-references in skill files, always count directory levels from the file's own
  location to the repo root and prepend the correct number of `../`
- Use the depth table above for quick reference
- After adding any new Markdown link in a skill file, verify it resolves by clicking it in VS Code
  preview or checking it renders on GitHub
- For links between two skill files in the same directory, use a simple relative name:
  `[other-ref](collapse-reference.md)` (no leading `../../../../`)

## Related

- [Unclosed code fence](./../2026-03-18-unclosed-code-fence-corrupts-markdown-rendering.md) — companion Markdown authoring bug found in the same review
- [`r-analytical-anti-patterns.md`](../../../../.github/skills/cg-skill-r-analytical/references/r-analytical-anti-patterns.md) — file where this bug was found and fixed
