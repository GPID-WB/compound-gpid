---
date: 2026-09-08
depth: light
parent-review: .cg-docs/reviews/2026-08-11-kilo-agent-parsing-linker-copy-directory-review.md
type: verification
findings:
  P1.1: open
  P1.2: open
  P1.3: open
  P1.4: open
  P1.5: open
  P1.6: open
  P1.7: open
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
  P2.5: open
  P2.6: open
  P2.7: open
  P2.8: open
  P2.9: open
  P3.1: open
---

# Verification Review: Minimal Adaptive Grilling

**Review mode**: light verification
**Parent review**: `.cg-docs/reviews/2026-08-11-kilo-agent-parsing-linker-copy-directory-review.md`
**Files reviewed**: current Minimal Adaptive Grilling implementation paths
**Findings**: 17 (P0: 0, P1: 7, P2: 9, P3: 1)

## Verification Context Warning

The selected parent review concerns Windows linker files and is unrelated to
Minimal Adaptive Grilling. The command selected it because the current plan's
standard review has no fixed findings and verification mode uses the newest
global review with fixed findings. No current-scope finding was suppressed.

## P0 - BLOCKING

No P0 findings.

## P1 - CRITICAL

- **[P1.1]** `.github/prompts/cg-brainstorm.prompt.md:63` - Research content has no explicit untrusted-data boundary.
  **Why**: README files, documentation, comments, and tool output can contain instruction-like text.
  **Fix**: Treat research sources as untrusted data, extract factual claims only, and retain source provenance. Add a regression test.
- **[P1.2]** `.github/prompts/cg-brainstorm.prompt.md:45` - The prior-work choice occurs before fact discovery.
  **Why**: Step 0.5 asks a user decision before Step 1 starts research.
  **Fix**: Complete relevant fact discovery before the choice and add an order assertion.
- **[P1.3]** `.github/prompts/cg-brainstorm.prompt.md:173` and `.github/skills/cg-skill-brainstorming/references/decision-template.md:45` - Single-path analysis conflicts with the capture templates.
  **Why**: The workflow forbids invented alternatives, but both templates show two required-looking approach headings.
  **Fix**: Require one heading and make additional headings conditional.
- **[P1.4]** `.github/prompts/cg-brainstorm.prompt.md:226` - Scope-change rejection has no complete recovery transition.
  **Why**: The prompt does not refresh scope, invalidate affected branches, or repeat analysis through confirmation.
  **Fix**: Define a transition for each objection type and repeat the applicable Steps 2 through 3.7.
- **[P1.5]** `.github/prompts/cg-brainstorm.prompt.md:175` and `.github/prompts/cg-brainstorm.prompt.md:186` - The no-path stop conflicts with unconditional Devil's Advocate review.
  **Why**: One instruction stops before Step 3.5, while another requires Step 3.5 for every brainstorm.
  **Fix**: Define no viable path as an explicit exception or add a blocker-focused pushback path.
- **[P1.6]** `.github/skills/cg-skill-brainstorming/workflows/requirement-elicitation.md:9` - Fact authority and resolution rules are incomplete.
  **Why**: Provenance, current documentation, user domain facts, and resolution transitions are not fully defined.
  **Fix**: Record source and authority for each material fact and define refresh and reconciliation rules.
- **[P1.7]** `tests/last-run.json:2` - Verification does not cover the active `dev` integration state.
  **Why**: The evidence is tied to a base at `c94b6bc`; `dev` is ahead and changes tests and manifests.
  **Fix**: Integrate current `dev`, regenerate targets, and rerun target and full Pester gates before merge.

## P2 - IMPORTANT

- **[P2.1]** `tests/prompt-tools.Tests.ps1:7021` - Critical tests use broad whole-file matches.
  **Fix**: Use guarded section extraction and complete section-local assertions.
- **[P2.2]** `tests/prompt-tools.Tests.ps1:7106` - Fixed-count checks omit some Unicode dash variants.
  **Fix**: Reject ASCII hyphen, en dash, and em dash in both isolated blocks.
- **[P2.3]** `.github/skills/cg-skill-brainstorming/references/decision-template.md:27` - The status note and status test do not enforce the emitted schema.
  **Fix**: Use the canonical HTML comment and assert the actual valid `status:` field.
- **[P2.4]** `.cg-docs/work-reports/2026-09-08-minimal-adaptive-grilling.md:39` - Recorded target checks do not prove generated command-body parity.
  **Fix**: Compare each generated command with its generation-plan output and manifest entry.
- **[P2.5]** `.cg-docs/active-state/current.json:11` - Focused evidence points to an overwritten artifact.
  **Fix**: Refer to the prompt-tools row in the current full-run artifact and the durable report.
- **[P2.6]** `.github/prompts/cg-brainstorm.prompt.md:67` - Skill loading can repeat the initial research scan.
  **Fix**: Load the skill before research, keep one fact inventory, and reuse current evidence.
- **[P2.7]** `.github/prompts/cg-brainstorm.prompt.md:234` - Complexity exploration has no iteration bound.
  **Fix**: Make the complexity offer one-shot per brainstorm.
- **[P2.8]** `tests/prompt-tools.Tests.ps1:6991` - New test reads are wildcard-sensitive.
  **Fix**: Use `Get-Content -LiteralPath` for new test-file reads.
- **[P2.9]** `.github/skills/cg-skill-brainstorming/references/decision-template.md:63` - Thinking Partner next steps always direct to `/cg-plan`.
  **Fix**: Make Next Steps conditional on Software/Data versus Thinking Partner mode.

## P3 - MINOR

- **[P3.1]** `.cg-docs/active-state/current.json:6` - The Agent Manager branch does not use the repository's conventional branch form.
  **Fix**: Integrate under a conventional feature branch and refresh workflow metadata.

## Incomplete Reviews

- `@cg-testing` did not produce usable output because the server reset the connection. The command did not retry it automatically.

## Passed Checks

- `@cg-code-quality` returned usable output.
- No current finding was suppressed by the unrelated parent review.
- `git diff --check` passed.
- All 16 changed generated outputs matched the in-memory generation plan and their manifest hashes.

## Residual Risk

- The missing testing verifier reduces confidence in test-specific verification.
- Static prompt tests cannot prove runtime model behavior.
