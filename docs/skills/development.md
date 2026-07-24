# Development and Testing Skills

These skills cover reusable software, testing, version control, project setup,
and environment-specific maintenance.

| Skill | Purpose | When to use | Availability | Source |
|---|---|---|---|---|
| `cg-skill-r-shared` | Universal R style, naming, assignment, formatting, errors, and documentation rules | Any R creation or review, regardless of dialect | Broad; automatically loaded | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-shared/SKILL.md) |
| `cg-skill-r-technical` | R package development, plumber APIs, Shiny, targets, HTTP clients, testing, and dependency management | Building reusable R packages, applications, APIs, or pipelines | Broad; task-conditional | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-technical/SKILL.md) |
| `cg-skill-r-testing` | testthat 3 expectations, fixtures, mocking, snapshots, BDD, and test-integrity patterns | Writing, reviewing, debugging, or improving R tests | Broad; testing-conditional | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-r-testing/SKILL.md) |
| `cg-skill-git-workflow` | Branch naming, conventional commits, pull requests, and data-science gitignore patterns | Routine version-control work and contribution preparation | Broad | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-git-workflow/SKILL.md) |
| `cg-skill-setup` | Language, dialect, project type, review depth, charter, and `.cg-docs/` setup knowledge | Used by `/cg-setup` while onboarding or reconfiguring a project | Conditional; workflow-internal | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-setup/SKILL.md) |
| `cg-skill-project-scanner` | Repository signal catalog and confidence rules for project detection | Used by setup automation to infer language, framework, type, and charter signals | Internal | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-project-scanner/SKILL.md) |
| `cg-skill-pester-safety` | Safe Pester execution rules, forbidden crash patterns, and canonical runner usage | Before any Pester command in this Compound GPID workspace | Internal and environment-specific | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-pester-safety/SKILL.md) |
| `cg-skill-windows-cmd-python-detection` | Safe `python3`/`python`/`py` probing, Windows Store stub rejection, parity, and tests | Maintaining a `bin/*.cmd` launcher that invokes Python | Internal and Windows-specific | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cg-skill-windows-cmd-python-detection/SKILL.md) |

## Reproducibility coverage

Reproducibility is also enforced through language skills, review agents, and
project instructions: lockfiles, relative paths, explicit seeds, repkit, data
validation, and executable test evidence are not isolated to one catalog item.

## Related pages

- [Analysis and Economics Skills](analysis.md)
- [Contribute and Develop](../development/index.md)
- [Agents](../reference/agents.md)
