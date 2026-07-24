# Institutional Knowledge Skills

These skills help teams make decisions, retain verified knowledge, write
source-grounded institutional documents, and maintain project documentation.

| Skill | Purpose | When to use | Availability | Source |
|---|---|---|---|---|
| `cg-skill-brainstorming` | Requirement elicitation, alternative comparison, scoping, and decision capture | Requirements are fuzzy or multiple approaches have meaningful tradeoffs | Broad; loaded by design workflows | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-brainstorming/SKILL.md) |
| `cg-skill-brain-query` | Selective project-Brain retrieval, relevance assessment, contradiction handling, staleness checks, and citation | A prompt contains a Consult Brain step or needs bounded prior-project context | Internal retrieval protocol | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-brain-query/SKILL.md) |
| `cg-skill-compound-docs` | Structured capture and discovery of verified, reusable solutions | After solving a non-trivial recurring problem or searching prior solutions | Broad team workflow; internally loaded | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-compound-docs/SKILL.md) |
| `cg-skill-wb-report-writing` | Source-grounded drafting, revision, adaptation, summarization, and QA for eight World Bank document types | Producing institutional prose when an approved source pack and document type are available | Optional domain skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-wb-report-writing/SKILL.md) |
| `cg-skill-wiki` | Wiki manifest, ownership, managed-section, conflict, template, and conversion rules | Before an `@cg-wiki` operation or when maintaining generated documentation | Optional; agent-internal | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-wiki/SKILL.md) |
| `cg-skill-fix-triage-migrate` | Adds finding-status frontmatter to legacy review files without applying fixes | Only with `/cg-fix-triage --migrate` | Internal, optional migration | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-fix-triage-migrate/SKILL.md) |

## Institutional writing boundary

The report-writing skill is an optional, source-pack-driven capability. It does
not authorize invented figures, citations, dates, findings, or institutional
positions. Its presence is not a claim that every organization or publication
workflow is supported.

## Related pages

- [Knowledge and Coordination](../workflows/knowledge.md)
- [Governance and Security](../governance/index.md)
- [Team Brain Schema](../team-brain-schema.md)
