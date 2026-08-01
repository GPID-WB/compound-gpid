# Skills Catalog

Skills provide reference knowledge to prompts and agents. They are not slash
commands. The public catalog counts each canonical skill once even though the
release contains generated copies for several agent platforms.

## Browse by goal

| Goal | Catalog |
|---|---|
| Analyze data, estimate models, manage surveys, calculate poverty measures, or create charts | [Analysis and Economics](analysis.md) |
| Build technical systems, test code, manage versions, or support platform tooling | [Development and Testing](development.md) |
| Clarify requirements, retain knowledge, create visual briefs, write institutional documents, or maintain a wiki | [Institutional Knowledge](institutional.md) |

The catalog currently contains 23 canonical skills:

- 8 analysis and economics skills.
- 8 development, testing, reproducibility, and platform skills.
- 7 institutional knowledge and documentation skills.

## Availability labels

| Label | Meaning |
|---|---|
| Broad | Guidance relevant to ordinary consumer projects when the language or task matches |
| Conditional | Loaded only for a selected dialect, language, workflow, or optional feature |
| Internal | Used primarily by Compound GPID prompts, agents, migration modes, or maintainers |
| Environment-specific | Protects a known operating environment or platform rather than describing a general capability |

A skill can be both conditional and broad. For example, tidyverse guidance is
broadly useful but loaded only when the project selects that dialect.

## Source of truth

Canonical skill identity and purpose come from:

```text
.github/skills/cg-skill-*/SKILL.md
```

The `.claude/skills/`, `.agents/skills/`, and `.opencode/skills/` trees are
generated mirrors and must not be counted as additional skills. Edit canonical
content only, regenerate target trees, and run drift checks before release.

This catalog adds audience, goal category, and availability labels for public
navigation. Site validation compares every cataloged source link with the
canonical directory set so a new, removed, or renamed skill cannot silently
leave the catalog inconsistent.

Canonical skill directories may also contain `references/`, `workflows/`,
`assets/`, `packages/`, source packs, or evaluation files. Those supporting
files are the detailed source when a skill directs an agent to load them
progressively. Each canonical skill directory is packaged as an atomic bundle,
so its supporting resources are mirrored with `SKILL.md` in every generated
runtime target.

## Related pages

- [Commands](../reference/commands.md)
- [Agents](../reference/agents.md)
- [Configuration](../configuration/index.md)
