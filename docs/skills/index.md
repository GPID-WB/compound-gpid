# Skills Catalog

Skills provide reference knowledge to prompts and agents. They are not slash
commands. The public catalog counts each canonical skill once even though the
release contains generated copies for several agent platforms.

## Browse by goal

| Goal | Catalog |
|---|---|
| Analyze data, estimate models, manage surveys, calculate poverty measures, or create charts | [Analysis and Economics](analysis.md) |
| Build technical systems, test code, manage versions, or support platform tooling | [Development and Testing](development.md) |
| Clarify requirements, retain knowledge, write institutional documents, or maintain a wiki | [Institutional Knowledge](institutional.md) |

The catalog currently contains canonical skills across both suites:

- Analysis and economics skills (including the R family `cg-skill-r-*`).
- Development, testing, reproducibility, and platform skills.
- Institutional knowledge and documentation skills.
- Research suite skills (`cr-skill-*`): identification, measurement,
  econometrics, provenance, replication, publication output, and more.

Counts are derived from the canonical `.github/skills/` directory set, not the
generated mirrors.

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
.github/skills/cr-skill-*/SKILL.md
```

The `.claude/skills/`, `.agents/skills/`, `.opencode/skills/`, and `.kilo/skills/` trees are generated mirrors and must not be counted as additional skills. Edit canonical content only, regenerate target trees, and run drift checks before release.

This catalog adds audience, goal category, and availability labels for public
navigation. Site validation compares every cataloged source link with the
canonical directory set so a new, removed, or renamed skill cannot silently
leave the catalog inconsistent.

Canonical skill directories may also contain `references/`, `workflows/`,
`packages/`, source packs, or evaluation files. Those supporting files are the
detailed source when a skill directs an agent to load them progressively. The
current generated runtime mirrors include `SKILL.md` files but not all
supporting files; this known packaging gap is recorded in the
[documentation migration audit](../about/documentation-audit.md).

## Related pages

- [Modular Guide](../modular-guide.md)
- [Commands](../reference/commands.md)
- [Agents](../reference/agents.md)
- [Configuration](../configuration/index.md)
