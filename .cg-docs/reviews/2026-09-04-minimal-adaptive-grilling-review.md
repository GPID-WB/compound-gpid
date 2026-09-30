---
date: 2026-09-08
depth: standard
type: standard
plan: .cg-docs/plans/2026-09-04-minimal-adaptive-grilling.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: open
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: open
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P3.1: open
---

# Review Report: Minimal Adaptive Grilling

**Review mode**: standard
**Files reviewed**: 29 implementation and workflow-record paths
**Findings**: 15 (P0: 0, P1: 6, P2: 8, P3: 1)

## P0 - BLOCKING

No P0 findings.

## P1 - CRITICAL

- **[P1.1]** [cg-testing] `.github/prompts/cg-brainstorm.prompt.md:41` - The prior-work choice occurs before fact discovery.
  **Why**: Step 0.5 asks the user to continue or start fresh before Step 1 discovers relevant facts. This conflicts with the new facts-before-first-decision contract.
  **Fix**: Do relevant fact research before the prior-work choice, or defer that choice until after research. Add an order assertion.
- **[P1.2]** [cg-code-quality, cg-testing, cg-architecture] `.github/prompts/cg-brainstorm.prompt.md:171` and `.github/skills/cg-skill-brainstorming/references/decision-template.md:43` - Single-path analysis conflicts with a two-approach capture format.
  **Why**: Step 3 forbids invented alternatives when one path remains, but both capture templates show two required-looking approach headings.
  **Fix**: Require one approach heading and make additional headings conditional. Add a single-path capture regression test.
- **[P1.3]** [cg-code-quality, cg-documentation, cg-architecture, cg-data-quality] `.github/prompts/cg-brainstorm.prompt.md:226` - Rejected scope changes have no complete recovery transition.
  **Why**: The prompt classifies a scope-change objection but does not refresh scope, invalidate affected frontier branches, or repeat analysis and confirmation.
  **Fix**: Define transitions for fact, decision, and scope objections, then route actionable objections through the applicable research, scope, elicitation, analysis, pushback, selection, and confirmation steps.
- **[P1.4]** [cg-documentation, cg-architecture] `.github/prompts/cg-brainstorm.prompt.md:175` and `.github/prompts/cg-brainstorm.prompt.md:186` - The no-viable-path stop conflicts with unconditional Devil's Advocate review.
  **Why**: Step 3 says to stop when no path remains, while Step 3.5 says it runs for every brainstorm without exception.
  **Fix**: Make the no-path branch an explicit exception, or run a defined blocker-focused check before the terminal stop.
- **[P1.5]** [cg-data-quality] `.github/skills/cg-skill-brainstorming/workflows/requirement-elicitation.md:9` - Fact authority and state transitions are incomplete.
  **Why**: Current documentation and user-provided facts have no clear authority classification, and stale, unavailable, or conflicting material facts are not explicitly required to stay unresolved until refreshed or reconciled.
  **Fix**: Retain source provenance, define domain-appropriate authority, and define valid resolution rules for all material fact states.
- **[P1.6]** [cg-version-control] `tests/last-run.json:2` - Verification used `origin/main`, while the active integration branch is `dev`.
  **Why**: `dev` is ahead and also changes the prompt tests and generated manifests. Current evidence does not prove the eventual integration state.
  **Fix**: Integrate current `dev` before merge, regenerate targets, and rerun the focused target tests and full safe Pester gate.

## P2 - IMPORTANT

- **[P2.1]** [cg-code-quality, cg-testing, cg-reproducibility, cg-data-quality] `tests/prompt-tools.Tests.ps1:7021` - Critical fallback tests are not sufficiently section-scoped.
  **Why**: Global common-word matches can pass from unrelated text, and the prompt fallback lacks direct checks for all fact states, authority, materiality dimensions, round maximum, recommendation transparency, and stop behavior.
  **Fix**: Extract guarded workflow and prompt sections and assert each complete contract in its own scope. Run rejection checks only in Step 3.7.
- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1:7125` - The fixed-count negative test misses Unicode dashes.
  **Why**: Reintroducing `usually 3-6 questions` with an en dash or em dash can remain green.
  **Fix**: Use a Unicode-tolerant dash pattern for the isolated Step 3 block.
- **[P2.3]** [cg-testing, cg-documentation, cg-data-quality] `.github/skills/cg-skill-brainstorming/references/decision-template.md:27` - The status note is a visible heading and the status test does not validate the emitted field.
  **Why**: The template differs from the canonical HTML comment, and `status: draft` could pass while the allowed-values comment remains.
  **Fix**: Use the exact canonical HTML comment. Assert an anchored valid `status:` field and reject each legacy value.
- **[P2.4]** [cg-testing, cg-reproducibility] `.cg-docs/work-reports/2026-09-08-minimal-adaptive-grilling.md:39` - The recorded pytest gate does not itself prove generated command-body parity.
  **Why**: Existing tests compare recursive skill bundles and platform format, but not every generated command body against the current generation plan.
  **Fix**: Add a working-tree parity assertion for each generated `cg-brainstorm` command and its ownership entry.
- **[P2.5]** [cg-code-quality, cg-documentation, cg-reproducibility, cg-data-quality] `.cg-docs/active-state/current.json:11` - Focused-run evidence points to an overwritten artifact.
  **Why**: `tests/last-run.json` now contains the full unfiltered run, not the earlier focused run, although it includes the prompt-tools result row.
  **Fix**: Refer to the prompt-tools subsection of the full-run artifact and to the durable work-report summary.
- **[P2.6]** [cg-performance] `.github/prompts/cg-brainstorm.prompt.md:63` - Fact discovery can repeat repository scans.
  **Why**: Step 1 scans the project, then the loaded skill can direct the same reads again without an evidence-reuse rule.
  **Fix**: Load the skill before research, build one fact inventory, reuse current evidence, and make only targeted lookups for unresolved material facts.
- **[P2.7]** [cg-performance] `.github/prompts/cg-brainstorm.prompt.md:232` - Complexity opt-in can repeat without a bound.
  **Why**: An advanced pass returns to Step 3.7, which can offer another advanced pass.
  **Fix**: Make the complexity offer one-shot per brainstorm while preserving the required post-confirmation opt-in.
- **[P2.8]** [cg-reproducibility] `tests/prompt-tools.Tests.ps1:6991` - New test reads use wildcard-sensitive paths.
  **Why**: `Get-Content $path` binds to `-Path` and can fail or read a different path when a checkout contains wildcard characters.
  **Fix**: Use `Get-Content -LiteralPath` for all new test-file reads.

## P3 - MINOR

- **[P3.1]** [cg-version-control] `.cg-docs/active-state/current.json:6` - The worktree branch does not use `type/short-description`.
  **Why**: `resilient-harpymimus` is an Agent Manager name, not the repository's conventional branch style.
  **Fix**: Use a conventional branch name when the work is moved or integrated, without hand-editing generated worktree state.

## Passed Checks

- All eight standard reviewers returned usable output.
- `git diff --check` passed.
- Focused Pester passed: 1,395 tests, 0 failed.
- Full Pester passed: 2,419 tests, 0 failed, unfiltered.
- Native target tests passed: 66 passed, 3 skipped.
- Independent reviewers found 1,079 generated outputs current and no manifest hash mismatch.
- No secrets, PII, data files, unexpected binaries, or direct generated-file edits were found.

## Residual Risk

- Static prompt tests verify shipped instruction text, not model behavior during real brainstorms.
- Verification must be repeated after integration with `dev`.
