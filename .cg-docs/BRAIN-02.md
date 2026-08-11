# 🧠 Project Brain — Part 2

_Generated 2026-08-11_

## Roadmap.Json / Cg-Work / Prompt-Tools.Tests.Ps1 _(continued from Part 1)_

_Keywords: `roadmap.json` · `cg-work` · `prompt-tools.tests.ps1`_ · 38 entities

- **[Injection scan required for every agent that reads user-adjacent files, including 'internal' cg-docs/ solution files](.cg-docs/solutions/testing-patterns/2026-05-15-injection-scan-required-for-every-agent-that-reads-user-adjacent-files.md)** · `solution` · _—_ · `2026-05-15`
  > `@cg-wiki` in `update` mode reads a solution file at `solution-path` and uses its content to synthesize updates to wi…
- **[Append-only insertion prevents silent corruption in AI-written shared files](.cg-docs/solutions/testing-patterns/2026-05-18-append-only-insertion-for-ai-written-shared-files.md)** · `solution` · _—_ · `2026-05-18`
  > `/cg-compound` Step 5 was instructed to enrich `compound-gpid.context.md` by inserting "directly into the correct sec…
- **[Three-layer test-correctness protocol prevents circular tests in /cg-fixbug](.cg-docs/solutions/testing-patterns/2026-06-03-three-layer-test-correctness-protocol-prevents-circular-tests-in-fixbug.md)** · `solution` · _—_ · `2026-06-03`
  > A `/cg-fixbug` session could produce a "passing" test that provides zero regression protection. The test was written …
- **[Token optimization needs benchmark guardrails, not one-off audits](.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md)** · `solution` · _—_ · `2026-06-08`
  > Phases 2-5 reduced token and model-cost risk by removing ordinary-workflow premium defaults, making `/cg-review` and …
- **[External validation must not be marked passed from static evidence](.cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md)** · `solution` · _—_ · `2026-06-09`
  > The Phase 7 release checklist correctly separated Codex-side checks from manual VS Code/PowerShell validation, but on…
- **[Token optimization release candidates need end-to-end validation evidence](.cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md)** · `solution` · _—_ · `2026-06-09`
  > Phases 2-6 reduced token and model-cost risk across ordinary model-picker prompts, `/cg-review`, `/cg-work`, Knowledg…
- **[Release checklist statuses must be anchored to audit-run timestamps](.cg-docs/solutions/testing-patterns/2026-06-10-release-checklist-statuses-must-be-anchored-to-audit-timestamps.md)** · `solution` · _—_ · `2026-06-10`
  > The Phase 7 release checklist had a column of pre-filled statuses like `"Passed in Codex"` across all automated gates…
- **[Untrusted content containing triple-backtick sequences breaks out of fenced code blocks](.cg-docs/solutions/testing-patterns/2026-06-11-fenced-block-delimiter-collision-in-untrusted-content.md)** · `solution` · _—_ · `2026-06-11`
  > A prompt (e.g., `cg-issues.prompt.md`) instructs an agent to embed untrusted content (plan file body, roadmap descrip…
- **[Within-prompt section drift: operational step and Safety Rules summary can diverge silently](.cg-docs/solutions/testing-patterns/2026-06-11-within-prompt-section-drift.md)** · `solution` · _—_ · `2026-06-11`
  > `cg-issues.prompt.md` maintained an injection-token blocklist in two places: **Step 6 (operational)**: > Strip lines …
- **[Regex arm silently dead from inception due to typo — test passes via sibling arm](.cg-docs/solutions/testing-patterns/2026-06-12-regex-arm-dead-from-inception-typo-passes-via-sibling.md)** · `solution` · _—_ · `2026-06-12`
  > A journey-fixture test was written to verify that `/cg-work` warns when an invalid `deviate:` override is provided an…
- **[Inherited model-picker prompts need explicit audit equivalence](.cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md)** · `solution` · _—_ · `2026-06-15`
  > The OpenAI-first model-governance pass added a durable model catalog and changed `docs/model-guide.md` to describe ea…
- **[Reviewed warning classifications close token work without hiding risk](.cg-docs/solutions/testing-patterns/2026-06-16-reviewed-warning-classifications-close-token-work.md)** · `solution` · _—_ · `2026-06-16`
  > The Token Optimization & Model Governance milestone had no audit failures after the OpenAI-first model-governance mig…
- **[Workflow telemetry needs source-aware path and tool extraction](.cg-docs/solutions/testing-patterns/2026-06-22-workflow-telemetry-source-path-tool-extraction.md)** · `solution` · _—_ · `2026-06-22`
  > Phase 1.1 added workflow-level token/context telemetry to `scripts/cg_audit_context.py`, but the first implementation…
- **[Active-state handoff records should be artifact-reference-first](.cg-docs/solutions/testing-patterns/2026-06-23-active-state-handoff-records.md)** · `solution` · _—_ · `2026-06-23`
  > Long `/cg-work` sessions can span phases, review loops, blocked stops, and crash recovery. Reconstructing state from …
- **[Budgeted Knowledge Brain query needs rendered-output budget gates](.cg-docs/solutions/testing-patterns/2026-06-23-budgeted-knowledge-brain-query.md)** · `solution` · _—_ · `2026-06-23`
  > Phase 1.2 added `cg-index query` so workflow prompts can retrieve bounded Knowledge Brain context. The first implemen…
- **[Command-output summary wrappers should preserve raw evidence without replacing validation](.cg-docs/solutions/testing-patterns/2026-06-23-command-output-summary-wrappers.md)** · `solution` · _—_ · `2026-06-23`
  > Compound GPID workflows often need evidence from tests, diffs, logs, repository trees, and diagnostics. Copying raw o…
- **[Optional retrieval backends must stay default-disabled during evaluation](.cg-docs/solutions/testing-patterns/2026-06-23-optional-retrieval-backends-default-disabled.md)** · `solution` · _—_ · `2026-06-23`
  > Phase 1.2 added a deterministic local Brain query backend. Future retrieval candidates are tempting, but adding a reg…
- **[Progressive-disclosure prompt cleanup should preserve semantics with explicit expansion rationale](.cg-docs/solutions/testing-patterns/2026-06-23-progressive-disclosure-context-loading-contract.md)** · `solution` · _—_ · `2026-06-23`
  > Broad phrases such as "read roadmap.json" or "scan .cg-docs" can be interpreted as default whole-artifact loading. Th…
- **[Snapshot and external-research modes need opt-in gates before implementation](.cg-docs/solutions/testing-patterns/2026-06-23-snapshot-external-research-modes-need-opt-in-gates.md)** · `solution` · _—_ · `2026-06-23`
  > Snapshot and external-research modes are useful future ideas, but they carry different risks from local workflow exec…
- **[Token dashboards need explicit baseline/pass/fail semantics](.cg-docs/solutions/testing-patterns/2026-06-23-token-dashboard-regression-check.md)** · `solution` · _—_ · `2026-06-23`
  > Workflow token artifacts made static prompt/context pressure visible, but a maintainer still had to inspect multiple …
- **[Cross-file state contracts must align across docs, validators, and behavioral tests](.cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md)** · `solution` · _—_ · `2026-07-24`
  > The Phase 1 World Bank report-writing skill shipped with a valid thin router, shared references, deterministic Python…
- **[Positive validator fixtures must avoid placeholder evidence once validation tightens](.cg-docs/solutions/testing-patterns/2026-07-24-positive-validator-fixtures-must-avoid-placeholder-evidence.md)** · `solution` · _—_ · `2026-07-24`
  > The World Bank report-writing validator was tightened to reject placeholder hosts like `example.org` in approved sour…
- **[Advisory inheritance audits need explicit keys and cross-platform legacy cleanup](.cg-docs/solutions/testing-patterns/2026-07-31-advisory-inheritance-audit-and-legacy-cleanup.md)** · `solution` · _—_ · `2026-07-31`
  > The user-selected model migration removed execution assignments and replaced them with advisory-only stage guidance. …
- **[gh CLI fixture JSON keys must match what the client actually parses](.cg-docs/solutions/testing-patterns/2026-08-10-gh-cli-fixture-json-keys-must-match-client-parsing.md)** · `solution` · _—_ · `2026-08-10`
  > The readiness validator's offline fixture (`scripts/tests/fixtures/ready_issue.json`) supplies mocked GitHub state to…
- **[Full backlog structuring into five milestones](.cg-docs/strategy/2026-04-06-full-backlog-structuring.md)** · `strategy` · _—_ · `2026-04-06`
  > - Project charter and roadmap.json already in place. - Roadmap had 1 milestone (Quality Loop) with 6 idea-stage featu…
- **[Workflow automation and external patterns research](.cg-docs/strategy/2026-04-13-workflow-automation-research.md)** · `strategy` · _—_ · `2026-04-13`
  > - Quality Loop: 2 done, 1 active, 7 ideas (3 features actually done but roadmap not updated) - Performance: 1 done, 3…
- **[Move Python and Stata testing skills to Skills Enhancement](.cg-docs/strategy/2026-04-15-move-testing-skills-to-skills-enhancement.md)** · `strategy` · _—_ · `2026-04-15`
  > Quality Loop had 10 features (4 done, 1 planned, 5 ideas). Two of the idea-status features — `testing-skill-python` a…
- **[Context layer restructuring — slim instructions, project context file, multi-folder workspaces](.cg-docs/strategy/2026-04-16-context-layer-restructuring.md)** · `strategy` · _—_ · `2026-04-16`
  > - Quality Loop milestone fully completed (10/10 features done). - Performance and Skills Enhancement milestones in pr…
- **[Post-Context Layer refocus: Onboarding & Setup as primary, Performance to close out](.cg-docs/strategy/2026-04-28-post-context-layer-refocus.md)** · `strategy` · _—_ · `2026-04-28`
  > Context Layer milestone completed (5/5 features done). Quality Loop also fully complete (12/12). Two milestones remai…
- **[Onboarding & Setup milestone expansion](.cg-docs/strategy/2026-04-29-onboarding-milestone-expansion.md)** · `strategy` · _—_ · `2026-04-29`
  > Performance milestone completed (6/6 done). Quality Loop (12/12) and Context Layer (5/5) also done. Skills Enhancemen…
- **[Workflow Maturity milestone — branch management, phased execution, smart debugging, team coordination](.cg-docs/strategy/2026-05-05-workflow-maturity.md)** · `strategy` · _—_ · `2026-05-05`
  > - 8 milestones, 58 features (28 done, 0 active, 30 unstarted) - Two milestones in-progress: Skills Enhancement, Onboa…
- **[Ongoing Ideas milestone for standalone improvements](.cg-docs/strategy/2026-05-14-ongoing-ideas-milestone.md)** · `strategy` · _—_ · `2026-05-14`
  > Workflow Maturity milestone nearly complete (5/7 done). v0.10.3 just released with CI bypass flags and E2E smoke test…
- **[2026-05-19-knowledge-brain](.cg-docs/strategy/2026-05-19-knowledge-brain.md)** · `strategy` · _approved_ · `2026-05-19`
  > The `.cg-docs/` folder is growing dramatically (127+ solutions, 51+ plans, 35+ brainstorms, reviews, strategies). The…
- **[Mid-project idea capture — brainstorm depth, confidence, model strategy, help, outcome verification, goal-driven execution](.cg-docs/strategy/2026-05-28-mid-project-eight-ideas.md)** · `strategy` · _—_ · `2026-05-28`
  > - Knowledge Brain milestone at 62% (Batch D team brain active on `feat/knowledge-brain-engine` branch) - Workflow Mat…
- **[Token-Efficiency Workflow Strategy](.cg-docs/strategy/2026-06-18-token-efficiency-workflow-strategy.md)** · `strategy` · _—_ · `2026-06-18`
  > Compound GPID already has a substantial token/model-governance foundation:
- **[Skills Enhancement Idea Additions](.cg-docs/strategy/2026-07-22-skills-enhancement-idea-additions.md)** · `strategy` · _—_ · `2026-07-22`
  > Compound GPID is in a mid-project phase with the existing `Skills Enhancement` milestone available for additional ski…
- **[Adaptive project workflow capability](.cg-docs/strategy/2026-07-30-adaptive-project-workflow-capability.md)** · `strategy` · _—_ · `2026-07-30`
  > Compound GPID had 12 roadmap milestones and 117 features. Its current focus remained the Token Efficiency Core System…
- **[Trusted External Capability Adoption](.cg-docs/strategy/2026-07-30-trusted-external-capability-adoption.md)** · `strategy` · _—_ · `2026-07-30`
  > Compound GPID had completed the Canonical-to-Native Packaging Foundation on 2026-07-28. The completion was merged to …

## Architecture Research Objective / Workflow Maturity Objective / Knowledge Brain Objective

_Keywords: `architecture research
objective` · `workflow maturity
objective` · `knowledge brain
objective`_ · 138 entities

- **[@cg-fix-problems agent \(auto-dispatched by /cg-work\)](roadmap.json#cg-fix-problems-agent)** · `feature` · _done_ · `—`
  > @cg-fix-problems agent (auto-dispatched by /cg-work)
- **[/cg-fix-problems user-facing prompt](roadmap.json#cg-fix-problems-prompt)** · `feature` · _done_ · `—`
  > /cg-fix-problems user-facing prompt
- **[Testing skill for R \(testthat/mockery\)](roadmap.json#testing-skill-r)** · `feature` · _done_ · `—`
  > Testing skill for R (testthat/mockery)
- **[Per-step test enforcement in /cg-work](roadmap.json#per-step-test-enforcement-in-cg-work)** · `feature` · _done_ · `—`
  > Per-step test enforcement in /cg-work
- **[Per-finding status tracking in review files](roadmap.json#review-finding-status-tracking)** · `feature` · _done_ · `—`
  > Per-finding status tracking in review files
- **[Honest pushback mode in /cg-brainstorm and /cg-strategy](roadmap.json#honest-pushback-in-brainstorm-strategy)** · `feature` · _done_ · `—`
  > Honest pushback mode in /cg-brainstorm and /cg-strategy
- **[Side-idea capture during brainstorming \(save to roadmap\)](roadmap.json#side-idea-capture-in-brainstorm)** · `feature` · _done_ · `—`
  > Side-idea capture during brainstorming (save to roadmap)
- **[Plan review agent and prompt \(@cg-plan-critic + /cg-plan-review\)](roadmap.json#plan-review-agent-and-prompt)** · `feature` · _done_ · `—`
  > Plan review agent and prompt (@cg-plan-critic + /cg-plan-review)
- **[Schema bypass for compound-gpid repo in /cg-resume](roadmap.json#schema-bypass-in-cg-resume)** · `feature` · _done_ · `—`
  > Schema bypass for compound-gpid repo in /cg-resume
- **[CE-inspired improvements integration \(P0 severity, new prompts, smart workflows\)](roadmap.json#ce-improvements-integration)** · `feature` · _done_ · `—`
  > CE-inspired improvements integration (P0 severity, new prompts, smart workflows)
- **[/cg-fix-triage --migrate mode \(backfills findings: frontmatter on legacy review files\)](roadmap.json#fix-triage-migrate-mode)** · `feature` · _done_ · `—`
  > /cg-fix-triage --migrate mode (backfills findings: frontmatter on legacy review files)
- **[Review convergence: mode:verify for /cg-review](roadmap.json#review-verify-mode)** · `feature` · _done_ · `—`
  > Review convergence: mode:verify for /cg-review
- **[Full model audit across prompts and agents](roadmap.json#full-model-audit)** · `feature` · _done_ · `—`
  > Full model audit across prompts and agents
- **[/cg-release scan scope limited to last 60 days](roadmap.json#cg-release-scan-scope-60-days)** · `feature` · _done_ · `—`
  > /cg-release scan scope limited to last 60 days
- **[Split /cg-release into Haiku scan + Sonnet drafting](roadmap.json#cg-release-haiku-sonnet-split)** · `feature` · _done_ · `—`
  > Split /cg-release into Haiku scan + Sonnet drafting
- **[Reduce token cost via prompt prose compression and Step 0 dedup](roadmap.json#reduce-token-cost-late-sequence-content)** · `feature` · _done_ · `—`
  > Reduce token cost via prompt prose compression and Step 0 dedup
- **[Structural prevention of agent-caused Pester crashes \(JSON artifact + prompt hardening\)](roadmap.json#structural-pester-crash-prevention)** · `feature` · _done_ · `—`
  > Structural prevention of agent-caused Pester crashes (JSON artifact + prompt hardening)
- **[R dialect skills architecture \(collapse, data.table, tidyverse\)](roadmap.json#r-dialect-skills-architecture)** · `feature` · _done_ · `—`
  > R dialect skills architecture (collapse, data.table, tidyverse)
- **[tidymodels addition to cg-skill-r-analytical](roadmap.json#tidymodels-addition)** · `feature` · _idea_ · `—`
  > tidymodels addition to cg-skill-r-analytical
- **[Skill discovery metadata and trigger-quality audit](roadmap.json#skill-description-consistency-audit)** · `feature` · _idea_ · `—`
  > Skill discovery metadata and trigger-quality audit
- **[Testing skill for Python \(pytest/parametrize/monkeypatch\)](roadmap.json#testing-skill-python)** · `feature` · _idea_ · `—`
  > Testing skill for Python (pytest/parametrize/monkeypatch)
- **[Testing skill for Stata \(assert-based/reprun\)](roadmap.json#testing-skill-stata)** · `feature` · _done_ · `—`
  > Testing skill for Stata (assert-based/reprun)
- **[World Bank institutional report-writing skill](roadmap.json#world-bank-institutional-report-writing-skill)** · `feature` · _done_ · `—`
  > World Bank institutional report-writing skill
- **[SkillOpt-based improvement of existing skills](roadmap.json#skillopt-existing-skills-improvement)** · `feature` · _idea_ · `—`
  > SkillOpt-based improvement of existing skills
- **[Shared sensitive-data and output-hygiene contract](roadmap.json#shared-writing-guardrails-contract)** · `feature` · _idea_ · `—`
  > Shared sensitive-data and output-hygiene contract
- **[Reusable report source provenance and verification](roadmap.json#exemplar-source-pack-schema)** · `feature` · _idea_ · `—`
  > Reusable report source provenance and verification
- **[Slim project-specific copilot-instructions.md \(generated by cg-link/cg-setup\)](roadmap.json#slim-copilot-instructions)** · `feature` · _done_ · `—`
  > Slim project-specific copilot-instructions.md (generated by cg-link/cg-setup)
- **[compound-gpid.context.md file and Step 0 integration in all prompts](roadmap.json#project-context-file)** · `feature` · _done_ · `—`
  > compound-gpid.context.md file and Step 0 integration in all prompts
- **[/cg-compound proposes context.md additions after completed tasks](roadmap.json#cg-compound-context-enrichment)** · `feature` · _done_ · `—`
  > /cg-compound proposes context.md additions after completed tasks
- **[Multi-folder workspace awareness in copilot-instructions.md and prompts](roadmap.json#multi-folder-workspace-awareness)** · `feature` · _done_ · `—`
  > Multi-folder workspace awareness in copilot-instructions.md and prompts
- **[Auto-update Current Focus when a milestone completes \(/cg-work or /cg-resume detects staleness\)](roadmap.json#auto-update-current-focus-on-milestone-completion)** · `feature` · _done_ · `—`
  > Auto-update Current Focus when a milestone completes (/cg-work or /cg-resume detects staleness)
- **[Model-split pattern for other prompts \(Haiku scan + Sonnet draft\)](roadmap.json#model-split-pattern-reuse)** · `feature` · _idea_ · `—`
  > Model-split pattern for other prompts (Haiku scan + Sonnet draft)
- **[Study OpenAI Codex plugin for Claude Code](roadmap.json#study-codex-plugin)** · `feature` · _idea_ · `—`
  > Study OpenAI Codex plugin for Claude Code
- **[Evaluate GitHub Copilot hooks for compound-gpid](roadmap.json#evaluate-copilot-hooks)** · `feature` · _idea_ · `—`
  > Evaluate GitHub Copilot hooks for compound-gpid
- **[copilot-instructions.md restructuring \(blocked on hooks evaluation\)](roadmap.json#copilot-instructions-restructuring)** · `feature` · _idea_ · `—`
  > copilot-instructions.md restructuring (blocked on hooks evaluation)
- **[Adding hooks to streamline process](roadmap.json#adding-hooks-to-streamline-process)** · `feature` · _idea_ · `—`
  > Adding hooks to streamline process
- **[Include /ce:ideate-style prompt from compound-engineering-plugin](roadmap.json#ideate-prompt-from-compound-engineering)** · `feature` · _idea_ · `—`
  > Include /ce:ideate-style prompt from compound-engineering-plugin
- **[Study GSD-2 and Superpowers workflow patterns](roadmap.json#study-gsd2-superpowers-patterns)** · `feature` · _idea_ · `—`
  > Study GSD-2 and Superpowers workflow patterns
- **[Stage control knobs for workflow prompts \(blocked on external workflow research\)](roadmap.json#stage-control-knobs)** · `feature` · _idea_ · `—`
  > Stage control knobs for workflow prompts (blocked on external workflow research)
- **[Autonomous pipeline command /cg-autopilot \(blocked on workflow research + hooks evaluation\)](roadmap.json#autonomous-pipeline-autopilot)** · `feature` · _idea_ · `—`
  > Autonomous pipeline command /cg-autopilot (blocked on workflow research + hooks evaluation)
- **[Copilot CLI execution with worktrees \(Model C\)](roadmap.json#copilot-cli-model-c-execution)** · `feature` · _idea_ · `—`
  > Copilot CLI execution with worktrees (Model C)
- **[Verification commands — configurable post-task checks](roadmap.json#verification-commands-post-task)** · `feature` · _idea_ · `—`
  > Verification commands — configurable post-task checks
- **[Auto-triggered skills via expanded applyTo hook patterns \[from SP\]](roadmap.json#auto-triggered-skills-via-hooks)** · `feature` · _idea_ · `—`
  > Auto-triggered skills via expanded applyTo hook patterns [from SP]
- **[Add mattpocock/skills to competitive review sources](roadmap.json#mattpocock-skills-review-source)** · `feature` · _idea_ · `—`
  > Add mattpocock/skills to competitive review sources
- **[Cross-model review — adversarial model diversity](roadmap.json#cross-model-adversarial-review)** · `feature` · _idea_ · `—`
  > Cross-model review — adversarial model diversity
- **[Tiered model escalation — super-advanced model dispatch](roadmap.json#tiered-model-escalation)** · `feature` · _idea_ · `—`
  > Tiered model escalation — super-advanced model dispatch
- **[Canonical-to-Native Packaging Foundation](roadmap.json#canonical-to-native-packaging-foundation)** · `feature` · _done_ · `—`
  > Canonical-to-Native Packaging Foundation
- **[External asset provenance and controlled intake](roadmap.json#attribution-documentation)** · `feature` · _idea_ · `—`
  > External asset provenance and controlled intake
- **[GitHub Actions hardening external-skill pilot](roadmap.json#github-actions-supply-chain-hardening-pilot)** · `feature` · _idea_ · `—`
  > GitHub Actions hardening external-skill pilot
- **[End-to-end ID traceability from brainstorm requirements \(R-IDs\) to plan tasks \(U-IDs\) \[from CE\]](roadmap.json#brainstorm-plan-id-traceability)** · `feature` · _idea_ · `—`
  > End-to-end ID traceability from brainstorm requirements (R-IDs) to plan tasks (U-IDs) [from CE]
- **[Inline self-review checklist at end of /cg-brainstorm and /cg-plan \[from SP\]](roadmap.json#inline-self-review-brainstorm-plan)** · `feature` · _idea_ · `—`
  > Inline self-review checklist at end of /cg-brainstorm and /cg-plan [from SP]
- **[Verification-before-completion enforcement in /cg-work tasks \[from SP\]](roadmap.json#verification-before-completion-cg-work)** · `feature` · _idea_ · `—`
  > Verification-before-completion enforcement in /cg-work tasks [from SP]
- **[Append-only DECISIONS.md register for methodology and architecture choices \[from GSD\]](roadmap.json#decisions-register)** · `feature` · _idea_ · `—`
  > Append-only DECISIONS.md register for methodology and architecture choices [from GSD]
- **[HITL review-loop mode \(--review flag\) for section-by-section approval in /cg-brainstorm and /cg-plan \[from CE\]](roadmap.json#hitl-review-loop-mode)** · `feature` · _idea_ · `—`
  > HITL review-loop mode (--review flag) for section-by-section approval in /cg-brainstorm and /cg-plan [from CE]
- **[Systematic 4-phase debugging methodology in /cg-fixbug \(reproduce → isolate → root-cause → fix\) \[from SP\]](roadmap.json#systematic-debugging-4-phase)** · `feature` · _idea_ · `—`
  > Systematic 4-phase debugging methodology in /cg-fixbug (reproduce → isolate → root-cause → fix) [from SP]
- **[Automatic knowledge extraction prompt at end of /cg-work \(enhances /cg-compound capture rate\) \[from GSD\]](roadmap.json#auto-knowledge-extraction-after-work)** · `feature` · _idea_ · `—`
  > Automatic knowledge extraction prompt at end of /cg-work (enhances /cg-compound capture rate) [from GSD]
- **[Brainstorm depth overhaul — grill-me mode + grill-with-docs skill](roadmap.json#brainstorm-depth-grill-mode)** · `feature` · _idea_ · `—`
  > Brainstorm depth overhaul — grill-me mode + grill-with-docs skill
- **[/cg-confidence — honest confidence/assumptions/unknowns assessment](roadmap.json#cg-confidence-prompt)** · `feature` · _idea_ · `—`
  > /cg-confidence — honest confidence/assumptions/unknowns assessment
- **[roadmap.json schema validation after @cg-roadmap writes](roadmap.json#roadmap-schema-validation)** · `feature` · _idea_ · `—`
  > roadmap.json schema validation after @cg-roadmap writes
- **[Required frontmatter field checks from /cg-plan output](roadmap.json#plan-frontmatter-checks)** · `feature` · _idea_ · `—`
  > Required frontmatter field checks from /cg-plan output
- **[status:completed verification from /cg-work output](roadmap.json#work-completion-verification)** · `feature` · _idea_ · `—`
  > status:completed verification from /cg-work output
- **[.cg-docs/evals/ scaffold with probe-and-check pairs](roadmap.json#evals-scaffold)** · `feature` · _idea_ · `—`
  > .cg-docs/evals/ scaffold with probe-and-check pairs
- **[Project scanner agent for deep project analysis](roadmap.json#project-scanner-agent)** · `feature` · _done_ · `—`
  > Project scanner agent for deep project analysis
- **[Smart /cg-setup for existing projects \(scan → draft → targeted questions → approve\)](roadmap.json#smart-setup-existing-projects)** · `feature` · _done_ · `—`
  > Smart /cg-setup for existing projects (scan → draft → targeted questions → approve)
- **[Skip high-confidence setup questions based on scanner results](roadmap.json#skip-irrelevant-setup-questions)** · `feature` · _done_ · `—`
  > Skip high-confidence setup questions based on scanner results
- **[First-run welcome and health check after cg-link](roadmap.json#first-run-welcome-health-check)** · `feature` · _done_ · `—`
  > First-run welcome and health check after cg-link
- **[Migration path from vanilla Copilot \(detect and merge existing instructions\)](roadmap.json#vanilla-copilot-migration)** · `feature` · _idea_ · `—`
  > Migration path from vanilla Copilot (detect and merge existing instructions)
- **[Charter quality gate \(validate no placeholders, all fields populated\)](roadmap.json#charter-quality-gate)** · `feature` · _done_ · `—`
  > Charter quality gate (validate no placeholders, all fields populated)
- **[Roadmap bootstrap from charter \(seed initial milestone from Current Focus\)](roadmap.json#roadmap-bootstrap-from-charter)** · `feature` · _idea_ · `—`
  > Roadmap bootstrap from charter (seed initial milestone from Current Focus)
- **[/cg-setup --refresh mode for non-destructive re-configuration](roadmap.json#cg-setup-refresh-mode)** · `feature` · _idea_ · `—`
  > /cg-setup --refresh mode for non-destructive re-configuration
- **[Onboarding tour prompt /cg-tour \(guided workflow walkthrough\)](roadmap.json#onboarding-tour-prompt)** · `feature` · _idea_ · `—`
  > Onboarding tour prompt /cg-tour (guided workflow walkthrough)
- **[/cg-help — comprehensive interactive help system](roadmap.json#cg-help-interactive)** · `feature` · _idea_ · `—`
  > /cg-help — comprehensive interactive help system
- **[Project scanner evidence, unknowns, and intent-versus-reality gaps](roadmap.json#project-scanner-evidence-reality-gaps)** · `feature` · _idea_ · `—`
  > Project scanner evidence, unknowns, and intent-versus-reality gaps
- **[GitHub Pages website publishing for project wikis](roadmap.json#wiki-github-pages-site-publishing)** · `feature` · _idea_ · `—`
  > GitHub Pages website publishing for project wikis
- **[Branch creation from /cg-plan](roadmap.json#branch-creation-from-plan)** · `feature` · _done_ · `—`
  > Branch creation from /cg-plan
- **[Phased plan structure in /cg-plan](roadmap.json#phased-plan-structure)** · `feature` · _done_ · `—`
  > Phased plan structure in /cg-plan
- **[Phased execution in /cg-work](roadmap.json#phased-execution-cg-work)** · `feature` · _done_ · `—`
  > Phased execution in /cg-work
- **[Roadmap visualization agent + /cg-roadmap-view prompt](roadmap.json#roadmap-visualization-agent-prompt)** · `feature` · _done_ · `—`
  > Roadmap visualization agent + /cg-roadmap-view prompt
- **[/cg-fixbug test-correctness assessment](roadmap.json#fixbug-test-correctness-assessment)** · `feature` · _done_ · `—`
  > /cg-fixbug test-correctness assessment
- **[GitHub Issues integration \(optional, via gh CLI\)](roadmap.json#github-issues-integration)** · `feature` · _idea_ · `—`
  > GitHub Issues integration (optional, via gh CLI)
- **[PR verification pipeline \(E2E smoke tests, parity checks, CONTRIBUTING.md\)](roadmap.json#pr-verification-pipeline)** · `feature` · _done_ · `—`
  > PR verification pipeline (E2E smoke tests, parity checks, CONTRIBUTING.md)
- **[/cg-commit-push-pr — logical commit splitting, push, and PR creation](roadmap.json#cg-commit-push-pr)** · `feature` · _done_ · `—`
  > /cg-commit-push-pr — logical commit splitting, push, and PR creation
- **[/cg-verify-pr — CI check verification and auto-fix dispatch](roadmap.json#cg-verify-pr)** · `feature` · _done_ · `—`
  > /cg-verify-pr — CI check verification and auto-fix dispatch
- **[Goal-driven execution — plan-as-completion-contract with integrated validation](roadmap.json#goal-driven-execution)** · `feature` · _idea_ · `—`
  > Goal-driven execution — plan-as-completion-contract with integrated validation
- **[Explicit plan-path selection for /cg-work](roadmap.json#cg-work-explicit-plan-path)** · `feature` · _idea_ · `—`
  > Explicit plan-path selection for /cg-work
- **[Dual-audience Brainstorm and Plan artifacts with human-readable HTML](roadmap.json#dual-audience-brainstorm-and-plan-artifacts-with-human-readable-html)** · `feature` · _done_ · `—`
  > Dual-audience Brainstorm and Plan artifacts with human-readable HTML
- **[Workflow completion report and human-readable HTML dossier](roadmap.json#workflow-completion-report-and-html-dossier)** · `feature` · _idea_ · `—`
  > Workflow completion report and human-readable HTML dossier
- **[Automatic post-PR CI verification and universal PR targeting](roadmap.json#automatic-post-pr-verification-handoff)** · `feature` · _idea_ · `—`
  > Automatic post-PR CI verification and universal PR targeting
- **[Make automatic artifact HTML publication opt-in by default](roadmap.json#artifact-html-opt-in-default)** · `feature` · _planned_ · `—`
  > Make automatic artifact HTML publication opt-in by default
- **[Full-scope indexer \(all .cg-docs/ + roadmap features\)](roadmap.json#brain-full-scope-indexer)** · `feature` · _done_ · `—`
  > Full-scope indexer (all .cg-docs/ + roadmap features)
- **[Topic/theme extraction \(auto-cluster artifacts into concepts\)](roadmap.json#brain-topic-extraction)** · `feature` · _done_ · `—`
  > Topic/theme extraction (auto-cluster artifacts into concepts)
- **[Relationship/edge detection \(full typed edge set\)](roadmap.json#brain-relationship-detection)** · `feature` · _done_ · `—`
  > Relationship/edge detection (full typed edge set)
- **[BRAIN.md generation \(topic index + entity catalog + edges\)](roadmap.json#brain-md-generation)** · `feature` · _done_ · `—`
  > BRAIN.md generation (topic index + entity catalog + edges)
- **[/cg-brain-rebuild explicit rebuild command](roadmap.json#brain-rebuild-command)** · `feature` · _done_ · `—`
  > /cg-brain-rebuild explicit rebuild command
- **[Auto-trigger brain rebuild on /cg-compound](roadmap.json#brain-auto-rebuild-on-compound)** · `feature` · _done_ · `—`
  > Auto-trigger brain rebuild on /cg-compound
- **[Prompt integration — Consult Brain in Step 0](roadmap.json#brain-prompt-integration)** · `feature` · _done_ · `—`
  > Prompt integration — Consult Brain in Step 0
- **[cg-skill-brain-query \(agent brain search patterns\)](roadmap.json#brain-query-skill)** · `feature` · _done_ · `—`
  > cg-skill-brain-query (agent brain search patterns)
- **[Team brain — central repo schema design](roadmap.json#team-brain-repo-schema)** · `feature` · _done_ · `—`
  > Team brain — central repo schema design
- **[Team brain — push solutions + distilled patterns](roadmap.json#team-brain-push)** · `feature` · _done_ · `—`
  > Team brain — push solutions + distilled patterns
- **[Team brain — pull relevant entries during Step 0](roadmap.json#team-brain-pull)** · `feature` · _done_ · `—`
  > Team brain — pull relevant entries during Step 0
- **[Team brain — conflict/dedup resolution](roadmap.json#team-brain-dedup)** · `feature` · _done_ · `—`
  > Team brain — conflict/dedup resolution
- **[Team brain — privacy filter before push](roadmap.json#team-brain-privacy-filter)** · `feature` · _done_ · `—`
  > Team brain — privacy filter before push
- **[Command default behaviors \(auto-branch, phases, autofix, context enrichment\)](roadmap.json#command-default-behaviors)** · `feature` · _done_ · `—`
  > Command default behaviors (auto-branch, phases, autofix, context enrichment)
- **[Outcome criteria in plans \(verifiable acceptance criteria\)](roadmap.json#outcome-criteria-in-plans)** · `feature` · _idea_ · `—`
  > Outcome criteria in plans (verifiable acceptance criteria)
- **[Conversation audit trail across workflow stages](roadmap.json#conversation-audit-trail)** · `feature` · _idea_ · `—`
  > Conversation audit trail across workflow stages
- **[/cg-strategy --add <idea> quick-add mode for roadmap ideas](roadmap.json#strategy-add-shortcut)** · `feature` · _idea_ · `—`
  > /cg-strategy --add <idea> quick-add mode for roadmap ideas
- **[Auto-generated project wiki \(created at /cg-setup, updated at /cg-compound\)](roadmap.json#project-wiki-auto-documentation)** · `feature` · _done_ · `—`
  > Auto-generated project wiki (created at /cg-setup, updated at /cg-compound)
- **[Planning-stage test strategy + human review facilitation](roadmap.json#planning-stage-test-strategy)** · `feature` · _idea_ · `—`
  > Planning-stage test strategy + human review facilitation
- **[Agent-verified outcome definitions with acceptance evals](roadmap.json#agent-verified-outcome-evals)** · `feature` · _idea_ · `—`
  > Agent-verified outcome definitions with acceptance evals
- **[User-selected execution with advisory model and effort routing](roadmap.json#user-selected-execution-with-advisory-model-and-effort-routing)** · `feature` · _done_ · `—`
  > User-selected execution with advisory model and effort routing
- **[Runtime model-catalog introspection across platforms](roadmap.json#runtime-model-catalog-introspection-across-platforms)** · `feature` · _idea_ · `—`
  > Runtime model-catalog introspection across platforms
- **[Historical HTML backfill for existing Compound GPID artifacts](roadmap.json#historical-html-backfill-for-existing-compound-gpid-artifacts)** · `feature` · _idea_ · `—`
  > Historical HTML backfill for existing Compound GPID artifacts
- **[Generic Markdown publishing skill and deterministic HTML views](roadmap.json#broader-artifact-publishing-formats-and-views)** · `feature` · _active_ · `—`
  > Generic Markdown publishing skill and deterministic HTML views
- **[Audit current context and model usage](roadmap.json#token-audit-context-model)** · `feature` · _idea_ · `—`
  > Audit current context and model usage
- **[Define model tiers and escalation rules](roadmap.json#model-tier-definitions)** · `feature` · _idea_ · `—`
  > Define model tiers and escalation rules
- **[Add model-policy tests](roadmap.json#model-policy-tests)** · `feature` · _idea_ · `—`
  > Add model-policy tests
- **[Update prompt frontmatter model and agent choices](roadmap.json#prompt-frontmatter-model-update)** · `feature` · _idea_ · `—`
  > Update prompt frontmatter model and agent choices
- **[Update custom agents for model and tool governance](roadmap.json#agent-model-tool-governance)** · `feature` · _idea_ · `—`
  > Update custom agents for model and tool governance
- **[Shrink always-on context](roadmap.json#shrink-always-on-context)** · `feature` · _idea_ · `—`
  > Shrink always-on context
- **[Split large prompts into thin entrypoints and on-demand skills](roadmap.json#prompt-skill-split)** · `feature` · _idea_ · `—`
  > Split large prompts into thin entrypoints and on-demand skills
- **[Add stage-specific context contracts](roadmap.json#stage-context-contracts)** · `feature` · _idea_ · `—`
  > Add stage-specific context contracts
- **[Make review cheaper with deterministic checks first](roadmap.json#review-deterministic-first)** · `feature` · _idea_ · `—`
  > Make review cheaper with deterministic checks first
- **[Benchmark before and after](roadmap.json#token-benchmark-before-after)** · `feature` · _idea_ · `—`
  > Benchmark before and after
- **[Capture the learning](roadmap.json#token-optimization-compound)** · `feature` · _idea_ · `—`
  > Capture the learning
- **[Workflow suitability criteria and non-goals](roadmap.json#workflow-suitability-criteria)** · `feature` · _idea_ · `—`
  > Workflow suitability criteria and non-goals
- **[Project scanner workflow-evidence analysis](roadmap.json#project-scanner-workflow-evidence)** · `feature` · _idea_ · `—`
  > Project scanner workflow-evidence analysis
- **[Compound workflow contract and .cg-docs/workflows/ schema](roadmap.json#compound-workflow-contract)** · `feature` · _idea_ · `—`
  > Compound workflow contract and .cg-docs/workflows/ schema
- **[/cg-workflow-builder guided discovery and inferred workflow proposal](roadmap.json#cg-workflow-builder)** · `feature` · _idea_ · `—`
  > /cg-workflow-builder guided discovery and inferred workflow proposal
- **[Workflow scaffolding with stage inputs, processes, outputs, checkpoints, and validation](roadmap.json#workflow-stage-scaffolding)** · `feature` · _idea_ · `—`
  > Workflow scaffolding with stage inputs, processes, outputs, checkpoints, and validation
- **[Existing-workflow lifecycle with create, extend, and revise modes](roadmap.json#workflow-lifecycle-modes)** · `feature` · _idea_ · `—`
  > Existing-workflow lifecycle with create, extend, and revise modes
- **[Deterministic workflow structure and reference validation](roadmap.json#workflow-structure-validation)** · `feature` · _idea_ · `—`
  > Deterministic workflow structure and reference validation
- **[/cg-setup workflow-suitability assessment](roadmap.json#setup-workflow-suitability-assessment)** · `feature` · _idea_ · `—`
  > /cg-setup workflow-suitability assessment
- **[Consent-based handoff from /cg-setup to /cg-workflow-builder](roadmap.json#setup-workflow-builder-handoff)** · `feature` · _idea_ · `—`
  > Consent-based handoff from /cg-setup to /cg-workflow-builder
- **[Lightweight workflow runner with stage entry and completion guidance](roadmap.json#workflow-runner)** · `feature` · _idea_ · `—`
  > Lightweight workflow runner with stage entry and completion guidance
- **[Workflow status and resume from filesystem artifacts](roadmap.json#workflow-status-resume)** · `feature` · _idea_ · `—`
  > Workflow status and resume from filesystem artifacts
- **[Context-budget checks for workflow stage contracts](roadmap.json#workflow-context-budget-checks)** · `feature` · _idea_ · `—`
  > Context-budget checks for workflow stage contracts
- **[Representative analytical and technical workflow pilots](roadmap.json#workflow-representative-pilots)** · `feature` · _idea_ · `—`
  > Representative analytical and technical workflow pilots
- **[Pilot evaluation gate before broader default exposure](roadmap.json#workflow-pilot-evaluation-gate)** · `feature` · _idea_ · `—`
  > Pilot evaluation gate before broader default exposure

## Tests / Filesystem / Python

_Keywords: `tests` · `filesystem` · `python`_ · 4 entities

- **[Secure publication and rollback must not clobber concurrent filesystem changes](.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md)** · `solution` · _—_ · `2026-08-01`
  > The shared artifact and generated-target writer already pinned parent directories, but several operations could still…
- **[httpx.AsyncClient requires ASGITransport for FastAPI async tests](.cg-docs/solutions/testing-patterns/2026-03-17-httpx-async-client-asgi-transport.md)** · `solution` · _—_ · `2026-03-17`
  > FastAPI async endpoint tests using `httpx.AsyncClient(app=app, ...)` fail or emit deprecation warnings on httpx ≥ 0.2…
- **[PS 5.1 `python -c` here-string unreliable — write temp .py file for Pester Python tests](.cg-docs/solutions/testing-patterns/2026-05-07-ps51-python-c-heredoc-unreliable-use-temp-file.md)** · `solution` · _—_ · `2026-05-07`
  > Passing multi-line Python code to `python -c` via a PowerShell here-string (`@"..."@`) in Pester tests produces unrel…
- **[Filesystem race fixes require handle-relative mutation and real boundary tests](.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md)** · `solution` · _—_ · `2026-07-28`
  > The native target generator validated destination ancestors, hashes, and ownership before writing or deleting generat…

## Secure_Fs.Py / Validation / Parser.Py

_Keywords: `secure_fs.py` · `validation` · `parser.py`_ · 3 entities

- **[2026-07-23-wb-report-writing-technical-methodology-verify-review-4](.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review-4.md)** · `review` · _—_ · `2026-07-31`
  > **Review mode**: light (`mode:verify`) **Parent review**: `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-me…
- **[2026-07-23-wb-report-writing-technical-methodology-verify-review-5](.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review-5.md)** · `review` · _—_ · `2026-07-31`
  > **Review mode**: light (`mode:verify`) **Parent review**: `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-me…
- **[2026-07-31-dual-audience-workflow-artifact-views-v2-review](.cg-docs/reviews/2026-07-31-dual-audience-workflow-artifact-views-v2-review.md)** · `review` · _—_ · `2026-07-31`
  > **Review mode**: full, auto-routed for schema, secure-filesystem, installer, and generated-target risk.
