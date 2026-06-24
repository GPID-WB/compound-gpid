---
date: 2026-06-18
title: "Token-Efficiency Workflow Strategy"
trigger: "mid-project"
outcome: "no-change"
---

# Strategy Session: Token-Efficiency Workflow Strategy

## Context at Session Start

Compound GPID already has a substantial token/model-governance foundation:

- `scripts/cg_audit_context.py` inventories prompt, agent, skill, instruction, documentation, Brain, context, and roadmap token pressure.
- `/cg-token-audit` runs deterministic tooling and summarizes `.cg-docs/cost/token-advice.md`.
- `.github/shared/context-loading.contract.md` defines staged context loading.
- `cg-skill-brain-query` already prohibits wholesale `brain-index.json` reads and routes ordinary agents through `BRAIN.md` plus targeted `BRAIN-NN.md` sections.
- Existing closure evidence says the current audit has `failures=0`, reviewed warnings `fix=0`, and `/cg-work` below the high-frequency warning threshold.

The current audit still shows where the next-order problem lives. The largest context masses are generated and tactical artifacts, not only prompt files:

| Artifact class | Current pressure |
| --- | ---: |
| `.cg-docs/brain-index.json` | ~147k estimated tokens |
| `.cg-docs/BRAIN*.md` | ~66k estimated tokens |
| `docs/` | ~50k estimated tokens |
| `.github/prompts/` | ~62k estimated tokens |
| `.github/skills/*/SKILL.md` | ~27k estimated tokens |
| `compound-gpid.context.md` | ~16k estimated tokens |
| `roadmap.json` | ~16k estimated tokens |

That means the strategic question is no longer "make prompts shorter" in isolation. The next phase should make every workflow declare, retrieve, summarize, and measure context more deliberately.

No implementation changes were made in this session. This document is the strategy artifact for later `/cg-plan` and `/cg-work` runs.

## Discussion Summary

The primary design principle is:

> Reduce token usage without reducing correctness, review quality, reproducibility, statistical safety, or the compound-learning value of the plugin.

The strategy should preserve the current Brainstorm -> Plan -> Work -> Review -> Fix Triage -> Compound loop, but add a context economy around it:

1. Measure workflow-level context, not just file sizes.
2. Make skills and instructions progressively disclosed across Copilot, Codex, Claude Code, and Cursor.
3. Store durable state in `.cg-docs/` and resume from artifact references instead of transcript repetition.
4. Query the Knowledge Brain through a budgeted retrieval interface.
5. Replace noisy terminal output with summary artifacts and paths to full logs.
6. Treat MCP/code-intelligence integrations as optional pilots, not default dependencies.
7. Add minimal-change review pressure so the agent produces less unnecessary code, not just shorter prose.
8. Add dashboards and regression checks so savings are measured before they are claimed.

A second-opinion strategy check reached the same practical constraint: do not
start with a new retrieval architecture or broad prompt rewrite. Start with
native baselines, query-first context loading, high-frequency workflow
measurement, and safety-preserving prompt/skill boundaries.

## Research Principles Used

Material external references were used for design principles only. Third-party token-saving claims are treated as hypotheses until benchmarked in this repository.

| Source | Reusable principle | Compound GPID mapping |
| --- | --- | --- |
| Agent Skills standard: https://agentskills.io/ and spec: https://agentskills.io/specification | Skills use progressive disclosure: metadata first, `SKILL.md` on activation, references/scripts only when needed. | Add skill-budget audit and split oversized/default-loaded doctrine into focused references. |
| Codex Skills: https://developers.openai.com/codex/skills | Codex loads only skill name, description, path initially, with an explicit startup budget for skill listings. | Keep skill descriptions specific but short; make AGENTS.md and Codex skill adapters first-class outputs. |
| Claude Code Skills: https://code.claude.com/docs/en/skills | Skills replace repeated pasted procedures; skill bodies load only when used; some work can run in isolated/forked contexts. | Move repeated workflow doctrine out of global prompts; consider fork/subagent-compatible packaging where platforms support it. |
| GitHub Copilot skills: https://code.visualstudio.com/docs/agent-customization/agent-skills | Skill frontmatter controls description, invocation, and optional forked context; large investigations can return focused results to parent context. | Use skill metadata/tests to prevent overly broad activation; design heavy audits/retrieval as summary-returning commands. |
| GitHub Copilot custom instructions: https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot | Copilot supports repo-wide, path-specific, and AGENTS.md-style agent instructions. | Generate scoped instruction/adapters rather than one giant always-on file. |
| AGENTS.md: https://agents.md/ | Dedicated agent instructions can be nested; nearest file wins. | Treat AGENTS.md support as a portability target and generate it from canonical GPID context. |
| Cursor Rules: https://cursor.com/docs/rules.md | Rules can be always-on, file-glob scoped, agent-selected by description, or manual. | Map GPID instructions to adapter-specific inclusion modes instead of duplicating all instructions everywhere. |
| Anthropic context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | Context is finite; use just-in-time retrieval, compaction, structured notes, and subagents for long-horizon work. | Make `/cg-resume`, `/cg-work`, and Brain queries artifact-reference-first. |
| Anthropic tool design: https://www.anthropic.com/engineering/writing-tools-for-agents | Tool responses should support concise/detailed formats, filtering, pagination, truncation, and actionable errors. | Add `cg-*-summary` wrappers and make full output available by path. |
| Anthropic MCP/code execution: https://www.anthropic.com/engineering/code-execution-with-mcp | Tool definitions and intermediate results can bloat context; code execution can keep intermediate results out of the model. | Keep MCP optional and prefer repo-native summarizers before adding default servers. |
| Aider repo map: https://aider.chat/docs/repomap.html | A concise, budgeted repository map can expose key symbols and relationships without full file reads. | Extend `cg-index query` toward budgeted symbol/context maps for changed files. |
| RTK: https://github.com/rtk-ai/rtk | Command-output compression can reduce noisy dev-command context; published savings vary by project. | Borrow the wrapper pattern natively; do not adopt RTK as a default dependency. |
| code-review-graph: https://github.com/tirth8205/code-review-graph | Local structural graph and blast-radius queries can reduce review context. | Pilot for `/cg-review` only after native summary baselines exist. |
| Serena: https://oraios.github.io/serena/01-about/000_intro.html | Symbol-level retrieval/editing via MCP can improve large-codebase navigation. | Optional backend for technical code-heavy projects; disabled by default. |
| Code Context Engine: https://elara-labs.github.io/code-context-engine/ | AST-aware chunking, hybrid search, compression, local savings tracking. | Watch/pilot as an optional backend; benchmark against native `cg-index query`. |
| CocoIndex Code: https://cocoindex.io/cocoindex-code/ | Incremental AST-aware indexing and MCP search. | Optional pilot for large repos; avoid default due to dependency and MCP overhead. |
| mcp-language-server: https://github.com/isaacphi/mcp-language-server | LSP-backed definition/reference/diagnostic tools. | Optional for code-heavy refactors; not relevant as a default for statistical prompt workflows. |
| Context7: https://github.com/upstash/context7 | Query external library docs by library and task. | Use only for library/API documentation tasks; do not load as always-on MCP. |
| Claude Context: https://github.com/zilliztech/claude-context | Semantic code search via MCP/vector DB, but requires external services/API keys in common setup. | Watchlist or opt-in only; not a default GPID dependency. |
| Repomix: https://repomix.com/guide, Gitingest: https://github.com/coderamp-labs/gitingest, code2prompt: https://github.com/mufeedvh/code2prompt | Whole-repo snapshots are useful for onboarding/audits but produce large prompt packs. | Allow snapshot mode for one-time strategy/audit, never ordinary workflow default. |
| Matt Pocock handoff skill: https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md | Handoffs should reference existing artifacts instead of duplicating them. | Apply to `/cg-resume`, `/cg-work`, and long-run compaction records. |
| Matt Pocock caveman skill: https://github.com/mattpocock/skills/tree/main/skills/productivity/caveman | Terse modes can reduce prose, but can harm clarity when reasoning matters. | Add opt-in terse/internal modes only for mechanical summaries and progress. |
| Ponytail: https://github.com/DietrichGebert/ponytail | A minimal-change reviewer can reduce overbuilt implementations while preserving safety. | Add native anti-overengineering skill/reviewer in planning/review loops. |
| token-optimizer: https://github.com/alexgreensh/token-optimizer | Local telemetry, checkpoints, output compression, and dashboard concepts. | Borrow local audit/dashboard patterns; avoid platform hooks as default until GPID has its own benchmark evidence. |

## Proposed Changes

### Strategic Direction

Compound GPID should implement token efficiency as a native workflow capability, not as a pile of optional tools. The core should remain stdlib Python, PowerShell, Bash/CMD, Markdown, and existing Pester/Pytest practices. External retrieval or MCP tools should be evaluated later through a controlled pilot interface.

The next token-efficiency effort should be tracked as two real roadmap milestones,
not eight. The detailed work should be numbered as phases inside those two
milestones so `/cg-plan` and `/cg-work` can proceed in order without turning
the roadmap into a long list of near-duplicate milestones.

### Milestone Roadmap

**Milestone 1: Core Token-Efficiency System**
_Make the existing Compound GPID workflow measurably more token-efficient using native, portable mechanisms first._

This milestone should be implemented in numbered order. Later phases may
discover refinements to earlier phases, but they should not start by adding
external retrieval dependencies or platform adapters.

**Phase 1.1: Baseline Token Audit and Workflow Inventory**
_Move from static file-size audit to workflow-level context telemetry and budgets._

- Feature: `.cg-docs/token/` audit artifact family: `TOKEN-BUDGET.md`, `token-audit.json`, `context-map.json`, `workflow-costs.csv`, `large-context-warnings.md`.
- Feature: Extend `scripts/cg_audit_context.py` to track workflow budgets, repeated blocks, skill/agent references, command-output pressure, Brain usage, MCP/tool usage, and context requisition compliance.
- Feature: Add a workflow context map for `/cg-brainstorm`, `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-fix-triage`, `/cg-compound`, `/cg-resume`, `/cg-diagnose`, and `/cg-token-audit`.
- Feature: Integrate Python audit/brain/team-brain tests more cleanly into validation, preferably through a platform-guarded Pester wrapper registered in `tests/Run-Tests.ps1` that invokes `python -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests` when Python is available.

**Phase 1.2: Knowledge Brain Query and Budgeted Retrieval**
_Turn Knowledge Brain into a query API rather than a prompt-readable corpus._

- Feature: `cg-index query --intent <brainstorm|plan|work|review|compound|resume> --changed-files ... --budget ...`.
- Feature: Query output includes short answer, selected artifact paths, selected snippets, confidence, why selected, why excluded, stale/conflict flags, and token estimate.
- Feature: Add JSON and Markdown output formats for prompts and humans.
- Feature: Update `cg-skill-brain-query` to prefer `cg-index query` when available, with `BRAIN.md` topic-index fallback.
- Feature: Add query benchmarks against known tasks and prior `.cg-docs/` artifacts.

**Phase 1.3: Command-Output Summarization Wrappers**
_Keep raw terminal output on disk and return compact, structured summaries to agents._

- Feature: `cg-test-summary` for Pester/Pytest/R/Stata validation summaries, building on `tests/last-run.json`.
- Feature: `cg-diff-summary` for file list, hunks by file, risk tags, and path to full diff.
- Feature: `cg-log-summary` for branch-local commits, first-parent counts, and notable files.
- Feature: `cg-tree-summary` for bounded repository/file-tree summaries.
- Feature: `cg-problems-summary` for VS Code/GitHub/CI diagnostics where available.
- Feature: Standard output artifact directory under `.cg-docs/token/outputs/`, with redaction and retention rules.

**Phase 1.4: Progressive-Disclosure Skills and Scoped Instructions**
_Reduce always-on and default-loaded doctrine while preserving safety contracts._

- Feature: Skill budget audit for `SKILL.md` body length, description length, trigger specificity, reference-file size, and deep reference chains.
- Feature: Split any large or over-triggering skill into a short landing page plus focused `references/`, `workflows/`, or `packages/` files.
- Feature: Move repeated workflow doctrine into shared contracts or skills loaded only by prompts that need them.
- Feature: Add native minimal-change reviewer skill: asks whether abstractions, dependencies, files, test scope, and generated code size are justified.

**Phase 1.5: Handoff, Resume, and Active-State Compaction**
_Make long workflows restart from durable artifacts instead of repeated transcript context._

- Feature: Compact active-state summaries for `/cg-work`, `/cg-resume`, `/cg-diagnose`, and long-running fix/review loops.
- Feature: Store active-state records in `.cg-docs/` with artifact paths, current phase, unresolved decisions, evidence status, and exact next command.
- Feature: Make handoff summaries reference existing plans, work reports, reviews, and issues by path rather than duplicating content.
- Feature: Add opt-in terse/internal modes for mechanical summaries and progress notes; keep analytical/statistical reasoning explicit by default.

**Phase 1.6: Token Dashboard and Regression Checks**
_Make token efficiency visible, comparable, and protected from regression._

- Feature: Add local dashboard/audit artifacts under `.cg-docs/token/`.
- Feature: Add before/after baseline comparison for representative workflows.
- Feature: Add regression thresholds for always-on context, high-frequency prompts, skill metadata, command output summaries, Brain query result sizes, and adapter duplication.
- Feature: Add release-readiness checklist for token-efficiency claims.

**Milestone 2: Portability and Optional Retrieval Expansion**
_Only after the native core is measurable, add cross-agent packaging and evaluate external retrieval backends behind explicit opt-in gates._

This milestone should not block the core token-efficiency work. It is the
expansion layer: valuable, but dependent on Milestone 1 evidence.

**Phase 2.1: Cross-Agent Packaging Adapters**
_Generate platform-specific agent context from one canonical GPID context model._

- Feature: Define canonical context schema for commands, prompts, skills, contracts, instructions, adapters, and platform capabilities.
- Feature: Generate or validate Copilot, Codex/AGENTS.md, Claude Code, and Cursor adapters from the schema.
- Feature: Prevent duplication of long content across adapter outputs.
- Feature: Add adapter drift tests so platform files stay semantically aligned without repeating full doctrine.

**Phase 2.2: Optional Retrieval Backend Evaluation**
_Evaluate external code-intelligence backends behind an opt-in interface._

- Feature: Define a backend interface: native, code-review-graph, Serena, Code Context Engine, CocoIndex Code, mcp-language-server, Context7, Claude Context.
- Feature: Add evaluation harness with the same changed-file/task suite, same budget, same expected relevant artifacts, and same correctness checks.
- Feature: Keep all backends disabled by default; enable only by explicit config and documented prerequisites.
- Feature: Report dependency risk, setup friction, Windows/macOS support, privacy/security constraints, and observed token/correctness impact.

**Phase 2.3: Snapshot and External-Research Modes**
_Support whole-repo snapshot tools only for explicit onboarding, strategy, audit, or external review workflows._

- Feature: Document when Repomix, Gitingest, code2prompt, and similar tools are useful.
- Feature: Add guardrails preventing snapshot tools from becoming ordinary workflow defaults.
- Feature: If implemented, route snapshots through explicit budget, redaction, and artifact-output rules.

### Prioritization Table

| Feature | Expected token-efficiency impact | Complexity | Dependency risk | Affected areas | Test requirements | Mode |
| --- | --- | --- | --- | --- | --- | --- |
| Workflow context budgets and `.cg-docs/token/` audit schema | High for measurement, prerequisite for claims | Medium | Low | `scripts/cg_audit_context.py`, `/cg-token-audit`, docs | Python unit tests, Pester prompt/docs tests, fixture audits | Default |
| Python test integration for brain/team-brain/audit | Medium quality impact, indirect token impact | Medium | Low | `tests/Run-Tests.ps1`, `tests/*.Tests.ps1`, `scripts/*/tests` | Platform-guarded Pester wrapper plus pytest groups | Default |
| Skill budget audit and split plan | Medium to high | Medium | Low | `.github/skills/`, docs/reference | Pester source-scan tests, audit thresholds | Default |
| Scoped instruction/adapters schema | High long-term | High | Medium | `.github/instructions`, `AGENTS.md`, future `.claude/`, `.cursor/` | Adapter snapshot/drift tests, generated output tests | Default for AGENTS.md/Copilot, optional for others |
| Minimal-change reviewer skill | Medium token and code-size impact; high quality leverage | Low/Medium | Low | `/cg-plan-review`, `/cg-work`, `/cg-review`, new skill/agent | Prompt tests, small fixture plans, review-output tests | Default in plan-review/review; light-touch in work |
| Active-state/handoff compaction | High for long workflows | Medium | Low | `/cg-resume`, `/cg-work`, `/cg-diagnose`, work reports | Artifact schema tests, prompt contract tests | Default |
| Terse/internal mode | Low to medium | Low | Low | Progress summaries, command wrappers | Prompt tests for opt-in and clarity exceptions | Optional |
| `cg-test-summary` | High because test output is noisy | Medium | Low | `tests/Run-Tests.ps1`, Python/R/Stata test adapters | Pester + pytest fixture tests, artifact schema tests | Default for workflows |
| `cg-diff-summary` / `cg-log-summary` / `cg-tree-summary` | Medium to high | Medium | Low | scripts/bin wrappers, `/cg-work`, `/cg-review`, `/cg-commit-push-pr` | Golden-output tests with temp repos | Default |
| `cg-index query` budgeted Brain retrieval | Very high; targets largest generated artifacts | High | Low if stdlib/native | `scripts/cg_index.py`, `scripts/brain/`, `cg-skill-brain-query` | Python query tests, relevance fixtures, prompt fallback tests | Default when available |
| Retrieval backend interface | Potentially high but unproven | High | Medium | config, docs, optional wrappers | Benchmark harness, setup detection, disabled-by-default tests | Experimental |
| Context7 docs lookup rule | Medium for library-doc correctness, low for repo tokens | Low | Medium external source risk | docs tasks, technical skills | Rule tests, citation/source tests | Optional |
| Repo-pack snapshot mode | Low for ordinary workflows, useful for onboarding | Low | Medium | `/cg-strategy`, `/cg-review-repos`, docs | Guard tests that prevent default use | Optional snapshot |
| Token dashboard/regression checks | High governance value | Medium | Low | `.cg-docs/token/`, audit script, release docs | Baseline comparison tests, threshold tests | Default |

## Decision

Adopt the two-milestone roadmap above as the strategy for the next
token-efficiency cycle.

The implementation order should be:

1. Milestone 1, Phase 1.1: baseline and test integration.
2. Milestone 1, Phase 1.2: native `cg-index query` retrieval, because it targets the largest token masses.
3. Milestone 1, Phase 1.3: command-output summaries, because these reduce long-session context pollution without changing workflow semantics.
4. Milestone 1, Phase 1.4 and 1.5: progressive-disclosure cleanup and resume/handoff compaction.
5. Milestone 1, Phase 1.6: dashboard/regression checks, added once the major sources are measurable.
6. Milestone 2, Phases 2.1-2.3: cross-agent packaging, optional retrieval backends, and snapshot modes, after native contracts are stable.

Do not update `roadmap.json` yet. This document is the strategy input for a later `/cg-plan` run.

## Do Not Implement Yet

These ideas are strategically relevant but should not be defaults in the next implementation pass:

- Do not enable many MCP servers by default. Tool definitions and verbose outputs can increase context cost.
- Do not make code-review-graph, Serena, Code Context Engine, CocoIndex, Claude Context, or mcp-language-server default dependencies before repo-specific benchmarks.
- Do not use Repomix, Gitingest, or code2prompt as ordinary workflow inputs. Keep them as one-time snapshot tools for onboarding, audits, or external reviews.
- Do not claim third-party savings numbers as Compound GPID savings.
- Do not replace the existing Knowledge Brain with vector search before a native `cg-index query` baseline exists.
- Do not make terse mode global. Statistical and analytical work still needs explicit assumptions, caveats, and reasoning.
- Do not move Pester safety, statistical correctness, roadmap write discipline, or evidence gates into optional skills unless every caller has an explicit required load point.
- Do not add cloud/vector backends that require credentials as default behavior.
- Do not generate platform adapters by copying long prompt bodies into every target platform.

## Benchmark Plan

Token-efficiency changes become official only after benchmark evidence from this repo.

### Benchmark Workflows

Use representative workflow probes:

1. `/cg-resume` on current roadmap with active plans.
2. `/cg-plan` for a small prompt/instruction change.
3. `/cg-work phase1` on a controlled markdown/prompt task.
4. `/cg-review light` on a small prompt diff.
5. `/cg-review data-risk` on a simulated R/Stata/Python analytical change.
6. `/cg-compound` after a completed fix.
7. `/cg-token-audit`.
8. `cg-index query` against known prior solution topics.

### Metrics

Track:

- files read;
- estimated input tokens by source category;
- skill descriptions loaded at startup;
- `SKILL.md` files activated;
- reference files opened;
- agents dispatched;
- command raw output bytes;
- command summary bytes;
- Brain query result size;
- full Brain/roadmap/context reads avoided;
- repeated context blocks;
- MCP/tool definitions exposed;
- elapsed time;
- correctness/evidence result;
- whether the right artifact was found;
- whether any safety/reproducibility guard was skipped.

### Artifacts

Write results under `.cg-docs/token/`:

- `token-audit.json`;
- `workflow-costs.csv`;
- `context-map.json`;
- `large-context-warnings.md`;
- `benchmark-runs/YYYY-MM-DD-<slug>.json`;
- `benchmark-runs/YYYY-MM-DD-<slug>.md`;
- `TOKEN-BUDGET.md`.

Keep `.cg-docs/cost/` backward compatible for the existing `/cg-token-audit` command, or document a migration path if `.cg-docs/token/` becomes canonical.

### Acceptance Gates

A phase can claim token-efficiency improvement only when:

- baseline and after runs use the same workflow probes;
- token estimates are reported as estimates, not exact billing;
- correctness/evidence gates still pass;
- Pester safe runner remains the canonical validation path;
- relevant Python tests pass;
- `reviewed_warnings.fix = 0` or every remaining fix warning is explicitly deferred;
- a human-readable benchmark note explains tradeoffs and residual risk.

## Recommended First `/cg-plan` Prompt

Use this as the first implementation prompt after accepting the strategy:

```text
/cg-plan

Create a Phase 1 implementation plan for the Compound GPID token-efficiency strategy saved at `.cg-docs/strategy/2026-06-18-token-efficiency-workflow-strategy.md`.

Scope Phase 1 only:
- Extend the existing deterministic audit layer into a `.cg-docs/token/` workflow-level baseline without changing workflow behavior.
- Preserve backward compatibility with `.cg-docs/cost/` and `/cg-token-audit`.
- Add workflow context budgets for the core loop: `/cg-brainstorm`, `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-fix-triage`, `/cg-compound`, `/cg-resume`, `/cg-diagnose`, and `/cg-token-audit`.
- Track files read, skills loaded, agents dispatched, command-output size, summary size, Brain usage, MCP/tool usage, repeated context blocks, and large prompt/instruction/skill files where deterministically observable.
- Integrate Python audit/brain/team-brain tests cleanly into the project validation story, preferably through a platform-guarded Pester wrapper registered in `tests/Run-Tests.ps1`, while respecting all Pester safety rules.
- Do not implement retrieval backends, command wrappers, cross-agent adapters, or skill rewrites in Phase 1.

The plan must include tests, documentation updates, acceptance criteria, and a benchmark artifact format. Treat all token-saving claims as hypotheses until measured in this repo.
```

## Charter Updates

No charter update was applied. If this strategy is accepted as the next focus, update `compound-gpid.md` Current Focus later through the approved `/cg-strategy` charter-update path and archive the replaced focus text first.
