---
date: 2026-06-16
title: "Token Context Optimization Closure"
status: decided
scope: "Standard"
chosen-approach: "Bounded max-benefit refactor plus token audit command"
tags: [token-optimization, context-loading, prompt-splitting, model-governance, audit]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Token Context Optimization Closure

## Context

Roadmap issues #93 and #94 remain active in the `Token Optimization & Model
Governance` milestone:

- #93: "Shrink always-on context."
- #94: "Split large prompts into thin entrypoints and on-demand skills."

Issue #92 is already complete after the OpenAI-first model-governance
migration. The current audit reports `failures = 0`, but still shows
context-loading and token warnings, including `/cg-work` estimated tokens above
5000 and broad context-loading warnings involving `.cg-docs/`, `roadmap.json`,
and `compound-gpid.context.md`.

The goal is to close #93 and #94 with evidence, without weakening safety gates,
Pester safety, roadmap write discipline, review routing, goal-driven execution,
or Codex/Claude compatibility separation.

## Requirements

- Classify current audit warnings as `fix`, `accept`, or `docs-only`.
- Keep changes bounded to audit warnings, measurable token burden, or
  duplication evidence.
- Do not move safety-critical behavior into optional skills.
- Do not split a prompt unless the caller explicitly loads the new skill or
  shared contract at the point of use.
- Treat `roadmap.json` updates as roadmap-agent work, not casual direct edits.
- Keep Codex/Claude compatibility in `AGENTS.md`, not in `.github/` Copilot
  assets.
- Add a small user-facing command that analyzes token/context usage in a user's
  project and suggests efficient plugin usage without loading large artifacts
  into model context.

## Approaches Considered

### Approach 1: Audit-triage closure

Classify each warning, fix only true ordinary-prompt broad-loading problems,
document accepted maintenance/docs warnings, and rerun audit/tests.

Pros:
- Lowest regression risk.
- Directly aligned with the current audit.
- Good fit for closing #93/#94 when failures are already zero.

Cons:
- May leave larger optimization opportunities untouched.
- `/cg-work` could remain over the high-frequency token threshold if only
  rationale is added.

### Approach 2: Focused `/cg-work` split

Perform audit triage and also split one or more clearly reusable `/cg-work`
blocks into explicitly loaded shared contracts or skills.

Pros:
- Directly addresses the only high-frequency prompt above 5000 estimated
  tokens.
- Produces concrete #94 evidence.

Cons:
- Riskier than triage if extracted material is safety-critical.
- Requires proving every caller loads the new contract or skill before use.

### Approach 3: Broad prompt refactor

Rewrite or split many large prompts to maximize token savings across the prompt
system.

Pros:
- Could reduce headline prompt inventory.
- May make the architecture look cleaner if repeated doctrine is extracted
  well.

Cons:
- Static and Pester tests cannot prove full semantic equivalence after prompt
  behavior changes.
- High risk of weakening prompt standalone behavior, Pester safety, roadmap
  discipline, review routing, or completion gates.
- The largest token contributors are generated/context artifacts, not prompt
  prose; broad prompt rewriting may not reduce real runtime context cost unless
  it also prevents broad artifact loading.

### Approach 4: Add a user-facing token audit command

Create a small command such as `/cg-token-audit` or `/cg-cost` that runs
deterministic Python analysis of a user's project context footprint and emits a
compact advisory report.

The command should not ask the model to inspect `.cg-docs/`, BRAIN files, or
context files directly. Python should scan file structure, `BRAIN*.md`,
`.cg-docs/`, context files, roadmap size, prompt references, model assignments,
review-depth settings, and context-loading risks, then output recommendations.

Possible recommendations:

- Use cheaper/inherited models for routine planning.
- Reserve high-effort models for implementation, difficult reviews, or
  high-risk reasoning.
- Use lighter review depth for low-risk changes.
- Reduce or section large `compound-gpid.context.md` files.
- Rebuild/query the Knowledge Brain instead of opening `BRAIN-log.md` or
  `brain-index.json`.
- Avoid broad `.cg-docs/` scans during ordinary workflows.

Pros:
- Converts token optimization into a reusable project diagnostic.
- Helps users understand and reduce real token cost in their own projects.
- Complements #93/#94 without requiring broad prompt rewrites.

Cons:
- Adds one new command and user-facing surface area.
- Needs careful wording so recommendations are advisory and do not weaken
  project safety defaults.

## Decision

Use a **bounded max-benefit refactor plus token audit command**.

This is a middle path between conservative triage and broad prompt rewriting.
It should pursue the highest-value token reductions while preserving behavioral
safety:

1. Treat `/cg-work` as the primary prompt-slimming target because it is the only
   high-frequency prompt currently above 5000 estimated tokens.
2. Convert ordinary broad context-loading instructions to staged, targeted
   reads under `.github/shared/context-loading.contract.md`.
3. Split only reusable, non-safety-heavy doctrine when the caller explicitly
   loads the new skill or shared contract at the point of use.
4. Keep safety-critical rules inline or explicitly loaded at Step 0.
5. Document accepted warnings for maintenance workflows and docs-only strings
   rather than forcing static warning count to zero.
6. Add a user-facing deterministic `/cg-token-audit` command that reports token
   and context usage patterns and suggests more efficient plugin usage.

The success target is not "rewrite all large prompts." It is: no new guardrail
failures, measurable reduction or justified retention of the remaining hot
spots, explicit warning classification, and durable user-facing diagnostics for
future projects.

## Warning Classification Framework

- `fix`: Ordinary workflow broad-loading or high-frequency prompt bulk that can
  be reduced without weakening behavior.
- `accept`: Intentional maintenance, roadmap, setup, release, or knowledge-base
  workflow behavior that needs broader structured reads.
- `docs-only`: Documentation wording that describes user behavior or reference
  tables but does not imply runtime broad loading by prompts.

Likely `fix` targets:

- `/cg-work` token burden above 5000.
- Ordinary prompt full reads of `compound-gpid.context.md`.
- Ordinary broad `.cg-docs/` scans where metadata/search-first would work.
- Ordinary broad `roadmap.json` reads where structured fields are sufficient.
- Wiki context reads that only need `## Wiki Configuration`.

Likely `accept` targets:

- Roadmap agents reading `roadmap.json`.
- Release scanner reading `.cg-docs/` filenames in a release window.
- Compound refresh scanning `.cg-docs/solutions/`.
- Learnings researcher tiered retrieval.
- Setup/context-curation workflows that intentionally create or refresh context
  artifacts.

Likely `docs-only` targets:

- `docs/context-files.md`.
- `docs/reference.md`.
- `docs/workflow.md`.

## Next Steps

Pass this brainstorm to `/cg-plan` and produce an implementation plan with
these phases:

1. Create a warning triage matrix from `.cg-docs/cost/context-audit.json`.
2. Apply targeted context-loading fixes to ordinary prompts.
3. Slim or split `/cg-work` only where audit/token/duplication evidence supports
   it and explicit load points are preserved.
4. Add `/cg-token-audit` as a thin prompt around deterministic Python analysis.
5. Update audit/reporting so accepted and docs-only warnings are documented
   rather than treated as unresolved.
6. Regenerate audit artifacts and collect before/after evidence for #93 and
   #94.
7. Run Python audit tests, `git diff --check`, and the safe Pester runner where
   available.
8. Prepare closure evidence for #93, #94, and then the full milestone.
