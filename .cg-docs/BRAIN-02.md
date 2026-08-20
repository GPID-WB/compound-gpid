# 🧠 Project Brain — Part 2

_Generated 2026-08-17_

## Roadmap.Json / Test Scenarios / Prompt-Tools.Tests.Ps1 _(continued from Part 1)_

_Keywords: `roadmap.json` · `test scenarios` · `prompt-tools.tests.ps1`_ · 96 entities

- **[Test the interface contract between chained prompts \(review -> fix-triage pipeline\)](.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md)** · `solution` · _—_ · `2026-03-30`
  > When two prompts are designed to work in sequence — the OUTPUT of one prompt is the INPUT of a follow-up prompt — the…
- **[Test prompt frontmatter tools: list to guard against silent write failures](.cg-docs/solutions/testing-patterns/2026-03-30-test-prompt-frontmatter-tools-list.md)** · `solution` · _—_ · `2026-03-30`
  > VS Code Copilot prompt files support a `tools:` key in their YAML frontmatter that restricts which tools the agent ma…
- **[Invoke-Pester on full test directory with -PassThru pipeline crashes VS Code](.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md)** · `solution` · _—_ · `2026-04-02`
  > VS Code crashes and requires a manual restart when the agent (or user) runs Pester against the entire `tests/` direct…
- **[AI agent repeats Pester crash pattern despite documented rules — documentation alone is insufficient](.cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md)** · `solution` · _—_ · `2026-04-06`
  > VS Code was crashed **multiple times in a single session** by the AI agent running forbidden Pester patterns — even t…
- **[Four Pester test quality patterns: shared helpers, anchored regex, non-empty value checks, and named-criteria guards](.cg-docs/solutions/testing-patterns/2026-04-07-pester-test-quality-patterns.md)** · `solution` · _—_ · `2026-04-07`
  > Surfaced during the 2026-04-07 model-audit light review (P1.1, P2.1, P3.1–P3.4). All four patterns apply broadly to a…
- **[Cross-cutting enumeration propagation: quality gate inversion and the full-audit pattern](.cg-docs/solutions/testing-patterns/2026-04-08-cross-cutting-enumeration-propagation-audit.md)** · `solution` · _—_ · `2026-04-08`
  > After adding a P0 severity tier to all 8 review agent output templates (`**[P0|P1|P2|P3]**`), the pipeline silently c…
- **[Test instruction file applyTo frontmatter to prevent silent dialect routing failure](.cg-docs/solutions/testing-patterns/2026-04-08-instruction-file-applyto-frontmatter-silent-failure.md)** · `solution` · _—_ · `2026-04-08`
  > `.github/instructions/r.instructions.md` contains an `applyTo:` field in its YAML frontmatter that controls which fil…
- **[New prompt/agent addition checklist: 7 files that must be updated together](.cg-docs/solutions/testing-patterns/2026-04-08-new-prompt-agent-addition-checklist.md)** · `solution` · _—_ · `2026-04-08`
  > Adding a new prompt (`/cg-*`) or agent (`@cg-*`) to compound-gpid requires touching at minimum 4 files. Missing any o…
- **[AI agent uses 2>&1 | Select-String when debugging test failures — crash trigger during failure investigation](.cg-docs/solutions/testing-patterns/2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md)** · `solution` · _—_ · `2026-04-09`
  > VS Code crashed **multiple times in a single session** during a fix-triage cycle. The agent had been told tests were …
- **[Dead-step-after-wait: prompt steps after a user-wait pause never execute](.cg-docs/solutions/testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md)** · `solution` · _—_ · `2026-04-13`
  > `cg-work.prompt.md` had a Step 5 ("Update Roadmap Status") placed **after** Step 4 ("Summary"), which ended with: > "…
- **[Prompt interaction guards: all response branches must be explicitly handled](.cg-docs/solutions/testing-patterns/2026-04-13-prompt-interaction-branch-completeness.md)** · `solution` · _—_ · `2026-04-13`
  > `cg-fix-triage.prompt.md` gained a large-report guard: when more than 15 findings are open, the prompt warns the user…
- **[New validation branch added without a test for the new code path](.cg-docs/solutions/testing-patterns/2026-04-15-new-validation-branch-requires-dedicated-test.md)** · `solution` · _—_ · `2026-04-15`
  > `tests/roadmap.Tests.ps1`'s `Test-RoadmapSchema` function was extended with a cross-milestone duplicate feature ID ch…
- **[Pester regex without \(?s\) gives silent false-negative on multi-line prompt content](.cg-docs/solutions/testing-patterns/2026-04-15-pester-dotall-flag-required-for-multiline-regex.md)** · `solution` · _—_ · `2026-04-15`
  > Several Pester tests for `cg-work.prompt.md` used `.*` to span across a prompt phrase that happened to wrap across a …
- **[Pester verbose output floods agent context window in long fix-triage sessions — crash even with safe PowerShell patterns](.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md)** · `solution` · _—_ · `2026-04-15`
  > VS Code crashed **twice in a single fix-triage session** (2026-04-15) even though all terminal commands exited with c…
- **[Prompt step silent-skip anti-pattern: always provide fallback with candidates when primary key lookup fails](.cg-docs/solutions/testing-patterns/2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md)** · `solution` · _—_ · `2026-04-15`
  > `/cg-work` Step 3.7 ("Update Roadmap Status") matched features by `plan` path. When no features matched (because they…
- **[Roadmap feature linkage must be audited when marking a plan complete](.cg-docs/solutions/testing-patterns/2026-04-15-roadmap-plan-linkage-must-be-audited-at-completion.md)** · `solution` · _—_ · `2026-04-15`
  > A plan was marked `status: completed` on 2026-04-14 but four features it delivered remained unlinked (`plan: null`) a…
- **[Canonical Run-Tests.ps1 + last-run.json artifact decouples test results from agent context window](.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md)** · `solution` · _—_ · `2026-04-17`
  > Despite 18+ documented VS Code crashes and a comprehensive `cg-skill-pester-safety` skill, agents continued to compos…
- **[Exact count assertions prevent silent regression when test name states a specific count](.cg-docs/solutions/testing-patterns/2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md)** · `solution` · _—_ · `2026-04-17`
  > A test in `helpers.Tests.ps1` was named: > "all three unconfigured fields (project-type, language, review-depth) fall…
- **[Behavioral Pester tests for SKILL.md files: guard contracts, not just existence](.cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md)** · `solution` · _—_ · `2026-04-20`
  > When `cg-skill-fix-triage-migrate/SKILL.md` was added to the project, the Pester test suite gained only a reference t…
- **[Prompt step with forward dependency needs explicit deferred-execution marker](.cg-docs/solutions/testing-patterns/2026-04-21-prompt-step-forward-dependency-deferred-marker.md)** · `solution` · _—_ · `2026-04-21`
  > `cg-fix-triage.prompt.md` had a `### Step 0.5: Load Language Skills` section that appeared *before* `### Step 1` in d…
- **[Test fixtures must match function input contract, not full document format](.cg-docs/solutions/testing-patterns/2026-04-21-test-fixture-must-match-function-input-contract.md)** · `solution` · _—_ · `2026-04-21`
  > `Get-ToolsList` in `tests/helpers.ps1` accepts an extracted frontmatter **body** — the inner content between `---` de…
- **[Where-Object returns PSObject\[\] — regex on array coerces to space-joined string](.cg-docs/solutions/testing-patterns/2026-04-21-where-object-returns-array-coercion-trap.md)** · `solution` · _—_ · `2026-04-21`
  > `Get-ToolsList` in `tests/helpers.ps1` extracted the `tools:` line from a frontmatter string and passed it directly t…
- **[Schema constants mirroring JSON registries need value-equality tests and cross-file maintenance anchors](.cg-docs/solutions/testing-patterns/2026-04-22-schema-constant-coupling-value-equality-test-and-maintenance-anchor.md)** · `solution` · _—_ · `2026-04-22`
  > `repos.json` contains a `schemaVersion` field: `cg-review-repos.prompt.md` Step 1 checks that the file's `schemaVersi…
- **[Verify-mode suppression must be anchored to fixed-finding scope, not agent-inferred consequence code](.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md)** · `solution` · _—_ · `2026-04-23`
  > `/cg-review mode:verify` was designed to suppress expected P2/P3 re-findings after a fix-triage cycle so the quality …
- **[Anti-loop exclusion: output file types must be excluded from input scan in iterative review modes](.cg-docs/solutions/testing-patterns/2026-04-24-anti-loop-exclusion-in-iterative-review-modes.md)** · `solution` · _—_ · `2026-04-24`
  > `/cg-review mode:verify` scans `.cg-docs/reviews/` for the most recent review file with at least one `fixed` entry to…
- **[Prompt guard conditions added without Pester regression tests](.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md)** · `solution` · _—_ · `2026-04-28`
  > Five distinct guard conditions were added to `cg-release.prompt.md` during the P0–P3 fix-triage cycle for the cg-rele…
- **[Two-phase injection guard: scan before extracting content from user-controlled files in AI agents](.cg-docs/solutions/testing-patterns/2026-04-29-two-phase-injection-guard-for-agent-file-reads.md)** · `solution` · _—_ · `2026-04-29`
  > `@cg-project-scanner` reads user-controlled files — `README.md`, `DESCRIPTION`, `.gitignore` — to extract charter-dra…
- **[Branch offer must precede user-investment steps in interactive prompts](.cg-docs/solutions/testing-patterns/2026-05-01-branch-offer-must-precede-user-investment-steps.md)** · `solution` · _—_ · `2026-05-01`
  > `/cg-brainstorm` asked "would you like to create a new branch?" at **Step 4.5** — after the brainstorm document was s…
- **[Fix-triage changes to prompt text need co-authored Pester assertions](.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md)** · `solution` · _—_ · `2026-05-01`
  > A thorough review of the smart-setup Phase 2 changes produced 21 findings (P0–P3). Fix-triage was applied across four…
- **[Regex alternation in Pester -match can mask coverage when first branch is always true](.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md)** · `solution` · _—_ · `2026-05-01`
  > A test was written to verify that the scanner injection sanitization block in `cg-setup.prompt.md` named all three tr…
- **[Pester regex for assert-with-string-message false-positives on inlist/inrange](.cg-docs/solutions/testing-patterns/2026-05-05-pester-regex-assert-string-message-false-positive-inlist.md)** · `solution` · _—_ · `2026-05-05`
  > A Pester guard test intended to detect invalid Stata `assert expr, "message"` syntax used the regex `assert\b[^\`\r\n…
- **[Regex alternation branches become stale dead code after prompt refactoring](.cg-docs/solutions/testing-patterns/2026-05-05-stale-alternation-after-prompt-refactoring.md)** · `solution` · _—_ · `2026-05-05`
  > A test was written in two-branch alternation form to cover two possible phrasings of the "skip silently" guard in `cg…
- **[Within-step pre-flight operations must precede the user-facing offer template](.cg-docs/solutions/testing-patterns/2026-05-05-within-step-preflight-must-precede-offer-template.md)** · `solution` · _—_ · `2026-05-05`
  > `cg-plan.prompt.md` Step 0.7 was written in this order: 1. Check current branch 2. **Show the offer template** (`feat…
- **[Cross-prompt user journey must be validated end-to-end, not just per-prompt](.cg-docs/solutions/testing-patterns/2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md)** · `solution` · _—_ · `2026-05-06`
  > During the phased execution verify review, a **P2** finding emerged that all individual-prompt tests had missed: - `c…
- **[Fix applied as HTML comment not executed — prompt instruction must be prose, not markup](.cg-docs/solutions/testing-patterns/2026-05-06-html-comment-as-fix-never-executed.md)** · `solution` · _—_ · `2026-05-06`
  > During fix-triage for the roadmap-visualization review, finding P2.15 required migrating `cg-ideate.prompt.md` to dis…
- **[Pester write-guard regex with ^ always false without \(?m\) — silent false-positive](.cg-docs/solutions/testing-patterns/2026-05-06-pester-caret-anchor-requires-multiline-flag.md)** · `solution` · _—_ · `2026-05-06`
  > A write-guard test for `cg-roadmap-view.agent.md` was written as: This test **always passes** — not because the agent…
- **[Source-scanning regression guard for PowerShell scripting anti-patterns](.cg-docs/solutions/testing-patterns/2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md)** · `solution` · _—_ · `2026-05-12`
  > A scripting anti-pattern (`Read-Host ""`) was introduced during a feature addition to `scripts/link.ps1`. The anti-pa…
- **[CI bypass flag pattern: \[switch\]$Force / --yes for interactive scripts](.cg-docs/solutions/testing-patterns/2026-05-13-ci-bypass-flag-force-yes-interactive-scripts.md)** · `solution` · _—_ · `2026-05-13`
  > PowerShell scripts (`link.ps1`, `unlink.ps1`) and bash scripts (`link.sh`, `unlink.sh`) contain interactive confirmat…
- **[Cross-script parity tests: keeping ps1 and sh scripts in sync](.cg-docs/solutions/testing-patterns/2026-05-13-cross-script-parity-tests-ps1-sh.md)** · `solution` · _—_ · `2026-05-13`
  > `link.ps1` and `link.sh` (and `unlink.ps1` / `unlink.sh`) must produce equivalent behaviour on Windows and macOS. Whe…
- **[Classification steps must exhaustively cover all enum values with terminal actions](.cg-docs/solutions/testing-patterns/2026-05-14-classification-step-must-exhaustively-cover-enum-values.md)** · `solution` · _—_ · `2026-05-14`
  > A prompt step that classifies input into one of N categories must provide a terminal action (halt or proceed) for eve…
- **[Depth-restricted review modes silently bypass domain-specific agents — add forced-dispatch exception for open P0s](.cg-docs/solutions/testing-patterns/2026-05-14-depth-restricted-mode-bypasses-domain-agents-need-forced-dispatch-exception.md)** · `solution` · _—_ · `2026-05-14`
  > `/cg-review mode:verify` was designed to terminate the fix-review cycle: it runs a `light` depth pass (only `@cg-code…
- **[Prompt injection via LLM-authored plan content embedded in AI-generated output](.cg-docs/solutions/testing-patterns/2026-05-14-prompt-injection-via-plan-content-in-ai-generated-output.md)** · `solution` · _—_ · `2026-05-14`
  > A prompt reads a plan file's `## Objective` section and embeds it verbatim into AI-generated output (e.g., a PR body,…
- **[Sibling-prompt symmetry: apply guard fixes to all prompts with the same operation](.cg-docs/solutions/testing-patterns/2026-05-14-sibling-prompt-symmetry-guard-audit.md)** · `solution` · _—_ · `2026-05-14`
  > When a P1 review finding adds a guard to prompt A (e.g., "exit-code check after `git add`"), the fix is scoped to tha…
- **[Write-permission mode flags must be parsed before any tool dispatch, not deferred to a later step](.cg-docs/solutions/testing-patterns/2026-05-14-write-permission-flags-must-be-parsed-before-tool-dispatch.md)** · `solution` · _—_ · `2026-05-14`
  > A prompt's File Permissions block declared: > `--propose` mode: READ-only — no file creation, modification, git commi…
- **[Common-word regex false positives in security and behavioral test assertions](.cg-docs/solutions/testing-patterns/2026-05-15-common-word-regex-false-positive-in-security-assertions.md)** · `solution` · _—_ · `2026-05-15`
  > After the thorough review of the `@cg-wiki` feature, a verify pass found that several new Pester tests passed trivial…
- **[Injection scan required for every agent that reads user-adjacent files, including 'internal' cg-docs/ solution files](.cg-docs/solutions/testing-patterns/2026-05-15-injection-scan-required-for-every-agent-that-reads-user-adjacent-files.md)** · `solution` · _—_ · `2026-05-15`
  > `@cg-wiki` in `update` mode reads a solution file at `solution-path` and uses its content to synthesize updates to wi…
- **[Append-only insertion prevents silent corruption in AI-written shared files](.cg-docs/solutions/testing-patterns/2026-05-18-append-only-insertion-for-ai-written-shared-files.md)** · `solution` · _—_ · `2026-05-18`
  > `/cg-compound` Step 5 was instructed to enrich `compound-gpid.context.md` by inserting "directly into the correct sec…
- **[Agent step carve-outs must not contradict the global P0 deferral policy](.cg-docs/solutions/testing-patterns/2026-05-20-agent-step-carveout-must-not-contradict-global-deferral-policy.md)** · `solution` · _—_ · `2026-05-20`
  > `cr-econometric-reasoning.agent.md` Step 4a contained: > "If you detect a code-math mismatch, **do NOT emit P0 here**…
- **[Boundary-stop test layout: the guarded item must live ABOVE the stop marker, not at the same level](.cg-docs/solutions/testing-patterns/2026-05-20-boundary-stop-test-must-place-config-above-stop-marker.md)** · `solution` · _—_ · `2026-05-20`
  > A test for `_find_local_config()` was written to verify that the function stops walking up the directory tree when it…
- **[Hoist Get-Content/Get-Frontmatter to Context scope — not inside It blocks](.cg-docs/solutions/testing-patterns/2026-05-20-pester-hoist-file-reads-to-context-scope.md)** · `solution` · _—_ · `2026-05-20`
  > Tests for a single file repeated the file read inside every `It` block: A Context block with 10 `It` tests performs 1…
- **[Agent dispatched for multiple task types needs an explicit execution mode guard](.cg-docs/solutions/testing-patterns/2026-05-22-multi-task-type-agent-needs-execution-mode-guard.md)** · `solution` · _—_ · `2026-05-22`
  > `cr-academic-writing.agent.md` was updated to run for both Writing and Tables/Figures task types. The dispatch table …
- **[Hoist all expensive computation \(regex, transforms\) to outer scope — not just file reads](.cg-docs/solutions/testing-patterns/2026-05-22-pester-hoist-expensive-computation-to-outer-scope.md)** · `solution` · _—_ · `2026-05-22`
  > The 2026-05-20 solution established that `Get-Content`/`Get-Frontmatter` should be hoisted to `Context`/`Describe` sc…
- **[Skill/agent forbidden-pattern tables must be kept in sync](.cg-docs/solutions/testing-patterns/2026-05-22-skill-agent-forbidden-pattern-table-must-be-kept-in-sync.md)** · `solution` · _—_ · `2026-05-22`
  > `cr-replication-package.agent.md` Check 6 (Path Portability) was updated to flag parent-traversal paths (`../`) as P1…
- **[Test that reimplements logic with correct code masks bugs in the actual code](.cg-docs/solutions/testing-patterns/2026-05-22-test-reimplements-logic-with-correct-code-masks-bug.md)** · `solution` · _—_ · `2026-05-22`
  > `bash-scripts.Tests.ps1` had a test for the modules-substitution logic in `update.sh` that consistently passed — even…
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
- **[Use Get-ToolsList helper over regex for YAML tools-array assertions](.cg-docs/solutions/testing-patterns/2026-07-29-get-toolslist-over-tools-regex.md)** · `solution` · _—_ · `2026-07-29`
  > Agent frontmatter files declare a `tools:` array. Tests often assert the presence or absence of specific tools using …
- **[Guard Get-Frontmatter at Context scope to prevent silent test-block crashes](.cg-docs/solutions/testing-patterns/2026-07-29-pester-context-scope-frontmatter-guard.md)** · `solution` · _—_ · `2026-07-29`
  > In Pester 4 test files that loop over agent/prompt files and parse frontmatter inside a `Context` block, `Get-Frontma…
- **[Review routing contract changes must update all entry points and coverage layers](.cg-docs/solutions/testing-patterns/2026-07-30-review-routing-contract-changes-must-update-all-entry-points-and-coverage-layers.md)** · `solution` · _—_ · `2026-07-30`
  > The research-route rollout left three different review entry points out of sync: - `.github/shared/review-routing.con…
- **[Advisory inheritance audits need explicit keys and cross-platform legacy cleanup](.cg-docs/solutions/testing-patterns/2026-07-31-advisory-inheritance-audit-and-legacy-cleanup.md)** · `solution` · _—_ · `2026-07-31`
  > The user-selected model migration removed execution assignments and replaced them with advisory-only stage guidance. …
- **[Review artifacts must use machine-readable finding maps and stable validation evidence](.cg-docs/solutions/testing-patterns/2026-07-31-review-artifacts-must-use-machine-readable-finding-maps-and-stable-validation-evidence.md)** · `solution` · _—_ · `2026-07-31`
  > A full `/cg-review` pass over the Compound Research branch exposed two coupled contract defects in saved artifacts: -…
- **[Single-command model overrides need dedicated roles and baseline-aware audits](.cg-docs/solutions/testing-patterns/2026-08-03-single-command-model-overrides-need-dedicated-roles-and-baseline-audits.md)** · `solution` · _—_ · `2026-08-03`
  > `/cr-work` needed to move from `GPT-5.3-Codex` to `GPT-5.6 Luna` without changing any other prompt or agent. The imme…
- **[Evidence manifest tests must require referenced files to exist and be non-empty before hashing](.cg-docs/solutions/testing-patterns/2026-08-10-evidence-manifest-tests-require-referenced-files.md)** · `solution` · _—_ · `2026-08-10`
  > The Schema 2 evidence manifest test (`scripts/evidence/tests/manifest.test.js`) verified that recorded SHA-256 hashes…
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
- **[Compound Research roadmap structuring](.cg-docs/strategy/2026-05-14-compound-research-roadmap.md)** · `strategy` · _—_ · `2026-05-14`
  > The compound-research brainstorm (2026-05-13) produced a comprehensive Deep-scope design for extending compound-gpid …
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

## Architecture Research Objective / Ongoing Ideas Objective / Workflow Maturity Objective

_Keywords: `architecture research
objective` · `ongoing ideas
objective` · `workflow maturity
objective`_ · 151 entities

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
- **[Quarantined external-skill vendoring workflow](roadmap.json#quarantined-external-skill-vendoring)** · `feature` · _idea_ · `—`
  > Quarantined external-skill vendoring workflow
- **[GitHub Actions hardening external-skill pilot](roadmap.json#github-actions-supply-chain-hardening-pilot)** · `feature` · _idea_ · `—`
  > GitHub Actions hardening external-skill pilot
- **[Modular Compound GPID architecture for technical and research suites](roadmap.json#modular-compound-gpid-architecture-for-technical-and-research-suites)** · `feature` · _done_ · `—`
  > Modular Compound GPID architecture for technical and research suites
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
- **[Automated Documentation Deployment and What's New Page](roadmap.json#automated-documentation-deployment-and-whats-new-page)** · `feature` · _active_ · `—`
  > Automated Documentation Deployment and What's New Page
- **[Dual-Deployment: Dev Branch Docs at /dev/](roadmap.json#dual-deployment-dev-branch-docs-at-dev)** · `feature` · _idea_ · `—`
  > Dual-Deployment: Dev Branch Docs at /dev/
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
- **[CR asset classification mapping](roadmap.json#cr-asset-classification-mapping)** · `feature` · _planned_ · `—`
  > CR asset classification mapping
- **[Context-budget enforcement design](roadmap.json#context-budget-enforcement-design)** · `feature` · _planned_ · `—`
  > Context-budget enforcement design
- **[Capability profiles and active project-manifest resolution](roadmap.json#capability-profile-manifest-resolution)** · `feature` · _planned_ · `—`
  > Capability profiles and active project-manifest resolution
- **[Narrow mandatory base capabilities with generated enforcement](roadmap.json#mandatory-base-capabilities-generated-enforcement)** · `feature` · _planned_ · `—`
  > Narrow mandatory base capabilities with generated enforcement
- **[Fail-closed manifest and skill-integrity validation](roadmap.json#manifest-integrity-fail-closed-validation)** · `feature` · _planned_ · `—`
  > Fail-closed manifest and skill-integrity validation
- **[Generate platform adapters from the active manifest](roadmap.json#active-manifest-platform-adapters)** · `feature` · _planned_ · `—`
  > Generate platform adapters from the active manifest
- **[Active-manifest install/update and cross-platform parity matrix](roadmap.json#active-manifest-install-update-parity-matrix)** · `feature` · _planned_ · `—`
  > Active-manifest install/update and cross-platform parity matrix
- **[Token Efficiency vs modular priority resolution](roadmap.json#token-efficiency-vs-modular-priority-resolution)** · `feature` · _planned_ · `—`
  > Token Efficiency vs modular priority resolution
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
- **[Manifest-backed skills discovery catalog and /cg-skills](roadmap.json#manifest-backed-skills-discovery-catalog)** · `feature` · _idea_ · `—`
  > Manifest-backed skills discovery catalog and /cg-skills
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

## Expand Compound Research / Responsible Research Partner Objective / Measurement

_Keywords: `expand compound research` · `responsible research partner
objective` · `measurement`_ · 7 entities

- **[CR evidence and provenance spine with repo-local corpus default](roadmap.json#cr-evidence-provenance-spine)** · `feature` · _done_ · `—`
  > CR evidence and provenance spine with repo-local corpus default
- **[CR Measurement/Classification research archetype](roadmap.json#cr-measurement-classification-archetype)** · `feature` · _done_ · `—`
  > CR Measurement/Classification research archetype
- **[P0 comparability controls for measurement and indicator work](roadmap.json#cr-measurement-comparability-controls)** · `feature` · _done_ · `—`
  > P0 comparability controls for measurement and indicator work
- **[Research scoping and normative-decision gates](roadmap.json#cr-scoping-and-normative-gates)** · `feature` · _done_ · `—`
  > Research scoping and normative-decision gates
- **[Responsible lifecycle and method-pack retrofit](roadmap.json#cr-responsible-lifecycle-method-packs)** · `feature` · _done_ · `—`
  > Responsible lifecycle and method-pack retrofit
- **[Validate the Measurement archetype with a second use case](roadmap.json#cr-second-measurement-use-case-validation)** · `feature` · _idea_ · `—`
  > Validate the Measurement archetype with a second use case
- **[Team-level evidence library](roadmap.json#cr-team-evidence-library)** · `feature` · _idea_ · `—`
  > Team-level evidence library

## Scripts/Cg_Kilo_Preflight.Py / Link.Sh / Cg_Kilo_Preflight.Py

_Keywords: `scripts/cg_kilo_preflight.py` · `link.sh` · `cg_kilo_preflight.py`_ · 4 entities

- **[2026-06-12-goal-driven-execution-verify-review-6](.cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review-6.md)** · `review` · _—_ · `2026-07-05`
  > - **Mode**: verify (`mode:verify`; light depth) - **Parent review**: `.cg-docs/reviews/2026-06-12-goal-driven-executi…
- **[2026-06-12-goal-driven-execution-verify-review-7](.cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review-7.md)** · `review` · _—_ · `2026-07-05`
  > - **Mode**: verify (`mode:verify`; light depth) - **Parent review**: `.cg-docs/reviews/2026-06-12-goal-driven-executi…
- **[2026-08-13-manifest-driven-skill-loading-review](.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md)** · `review` · _—_ · `2026-08-13`
  > **Review mode**: full (auto-routed security/architecture/install changes) **Files reviewed**: Phase 1 implementation,…
- **[2026-08-13-manifest-driven-skill-loading-verify-review](.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-verify-review.md)** · `review` · _—_ · `2026-08-13`
  > **Review mode**: verify (light) **Parent review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.…

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
