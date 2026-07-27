# Why Compound GPID?

Compound GPID adapts a compounding engineering workflow to institutional data
science, economics, research, and supporting software. It is intended for work
where analytical correctness, reproducibility, review evidence, and retained
project knowledge matter more than minimizing every process step.

That engineering workflow is only one foundation. Read [Working with AI
Responsibly](philosophy.md) for the separate philosophy that explains the
epistemic risks of AI-assisted work, the principles for preserving human
judgment, and the responsibilities no plugin can take over for the user.

## Institutional focus

The repository charter describes a mixed team of economists and developers
producing high-stakes poverty statistics. The plugin therefore includes
domain-oriented guidance that is uncommon in a general software workflow:

- R skills for `collapse`, `data.table`, tidyverse, analytical work, technical
  development, testing, and World Bank visualization conventions.
- Stata guidance for data management, econometrics, causal inference, survey
  work, reproducibility, testing, Mata, and community packages.
- Python guidance for data processing, APIs, validation, testing, logging,
  typing, and profiling.
- Explicit analytical constraints around weighted welfare, poverty measures,
  PPP vintages, missing data, and result validation.
- Source-grounded World Bank report-writing guidance for common institutional
  document types.
- Project-local knowledge artifacts, roadmaps, reviews, and active-state
  records designed to make decisions and evidence recoverable.

These capabilities can also be useful to IMF, IDB, government, university, and
other research teams with similar analytical and governance needs. The
repository does not claim formal support, endorsement, or certification from
those organizations.

## Inspiration and relationship

Compound GPID is inspired by
[Every's Compound Engineering philosophy](https://every.to/guides/compound-engineering)
and the separate
[Compound Engineering plugin](https://github.com/EveryInc/compound-engineering-plugin).
Both emphasize deliberate requirements, planning, implementation, review, and
capturing reusable lessons so later work benefits from earlier work.

Compound GPID is not presented as a fork, official extension, or endorsed
distribution of that project. The repositories have distinct maintainers,
packaging, catalogs, and operating policies.

## Verifiable differences

| Area | Compound Engineering plugin | Compound GPID |
|---|---|---|
| Primary orientation | Its current public catalog is broad software and product engineering, including delivery, browser and iOS testing, product feedback, and optimization workflows. | The local charter centers data scientists, economists, official-statistics work, and developers building data infrastructure. |
| Core loop | The observed upstream workflow includes brainstorm, plan, work, simplify, review, and compound, plus an autonomous delivery path. | The documented loop emphasizes brainstorm, plan, work, review, fix triage, and compound, with explicit review artifacts and selective finding resolution. |
| Domain guidance | The current upstream catalog is mostly general software/product guidance. | The canonical catalog includes R, Stata, Python, econometrics, survey, welfare, poverty, visualization, reproducibility, and institutional-writing guidance. |
| Review structure | Upstream selects review personas based on the diff and is report-only by default unless mutation is authorized. | Compound GPID separates review agents and deterministic routes, and restricts automatic fixes for statistically sensitive areas. |
| Packaging | Upstream currently packages its capabilities as skills for several hosts. | Compound GPID authors canonical assets in `.github/` and generates committed native trees for Copilot, Claude Code, Codex, and OpenCode. |

Counts are not used as a quality comparison: the projects package prompts,
personas, agents, skills, and supporting references differently.

## Governance as an operating constraint

Compound GPID's repository rules prioritize statistical correctness, explicit
errors, protected credentials and data, committed lockfiles, documented
evidence, and review priority gates. These are project operating constraints,
not a security or regulatory certification.

The constraints have a practical tradeoff. Additional planning, evidence
collection, routed review, hard stops, restricted automatic fixes, and
institutional computing limitations can increase latency, tool calls, or human
review compared with a less constrained environment. The plugin includes light
routes, staged context loading, compact summaries, and token audits to reduce
avoidable overhead, but it does not claim comparative performance or cost
superiority.

## Sources

Upstream facts were checked on 2026-07-24 against commit
[`a9f6d530d4446d805a3100387dedd86268d7e695`](https://github.com/EveryInc/compound-engineering-plugin/tree/a9f6d530d4446d805a3100387dedd86268d7e695):

- [Upstream README and workflow](https://github.com/EveryInc/compound-engineering-plugin/blob/a9f6d530d4446d805a3100387dedd86268d7e695/README.md)
- [Upstream skill inventory](https://github.com/EveryInc/compound-engineering-plugin/tree/a9f6d530d4446d805a3100387dedd86268d7e695/skills)
- [Upstream `ce-work` documentation](https://github.com/EveryInc/compound-engineering-plugin/blob/a9f6d530d4446d805a3100387dedd86268d7e695/docs/skills/ce-work.md)
- [Upstream review documentation](https://github.com/EveryInc/compound-engineering-plugin/blob/a9f6d530d4446d805a3100387dedd86268d7e695/docs/skills/ce-code-review.md)
- [Compound GPID charter](https://github.com/GPID-WB/compound-gpid/blob/main/compound-gpid.md)
- [Canonical Compound GPID skills](https://github.com/GPID-WB/compound-gpid/tree/main/.github/skills)

## Next pages

- [Working with AI Responsibly](philosophy.md)
- [Getting Started](getting-started/index.md)
- [Skills Catalog](skills/index.md)
- [Governance and Security](governance/index.md)
