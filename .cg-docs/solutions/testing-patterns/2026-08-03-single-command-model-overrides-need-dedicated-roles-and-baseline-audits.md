---
date: 2026-08-03
title: "Single-command model overrides need dedicated roles and baseline-aware audits"
category: "testing-patterns"
language: "Python/Markdown/JSON"
tags: [model-governance, cr-work, native-targets, audit-baseline, regression-tests, target-mapping]
root-cause: "A one-command model override was introduced into a shared model-governance system that had no command-specific role for the override and already had pre-existing missing catalog assignments, so naive exact-match or zero-finding checks would either spill into other agents or report false regressions."
severity: "P1"
related: [".cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md", ".cg-docs/solutions/build-errors/2026-07-29-cr-agent-model-strings-must-use-gpt-catalog-compliant.md", ".cg-docs/plans/2026-08-02-cr-work-gpt-5-6-luna-plan.md", ".cg-docs/work-reports/2026-08-03-cr-work-gpt-5-6-luna-plan.md"]
---

# Single-Command Model Overrides Need Dedicated Roles And Baseline-Aware Audits

## Problem

`/cr-work` needed to move from `GPT-5.3-Codex` to `GPT-5.6 Luna` without
changing any other prompt or agent. The immediate temptation was to edit only
the prompt frontmatter or to reuse an existing shared role.

That was unsafe for two reasons:

1. The model-governance system projects canonical `.github/` metadata into
   target-specific native trees for Codex, Claude Code, and OpenCode. A prompt
   frontmatter-only change would leave generated targets, docs, and audits out
   of sync.
2. The repository already had pre-existing missing catalog assignments for
   other CR prompts. A repository-wide expectation of "zero missing
   assignments" would fail before and after the change, hiding whether the new
   `/cr-work` override was correct.

## Root Cause

The existing governance model handled shared roles such as inherited,
OpenAI-first, Sonnet, and Haiku, but there was no role representing "this one
research execution command has a different canonical model and different native
target projections."

At the same time, the audit surface mixed two classes of findings:

- new regressions introduced by the current change;
- older catalog debt outside the approved scope.

Without separating those concerns, the change could either:

- leak into other prompts by reusing a shared role; or
- look permanently broken because the audit asserted a clean repo state that did
  not exist yet.

## Solution

Use a dedicated catalog role for the single-command override, map that role per
native target, and verify the change against a before/after audit baseline.

### 1. Add a command-specific role instead of reusing a shared one

Register a dedicated role in the model catalog and audit allow-list:

```json
{
  "path": ".github/prompts/cr-work.prompt.md",
  "role": "research-execution",
  "preferredModel": "GPT-5.6 Luna"
}
```

```python
MODEL_ROLES = {
    "inherited",
    "openai-first",
    "sonnet-tier",
    "haiku-tier",
    "research-execution",
}
```

This isolates the override to `/cr-work` and preserves the user requirement
that no other agent changes.

### 2. Keep canonical and native behavior separate

Declare the canonical Copilot model on the prompt, then map the dedicated role
per target in `.github/shared/target-mapping.json`:

```json
{
  "codex": {
    "modelMapping": {
      "research-execution": "GPT-5.6 Luna"
    }
  },
  "claude-code": {
    "modelMapping": {
      "research-execution": "sonnet"
    }
  }
}
```

OpenCode stays inherited by omitting a mapping for the role. After changing the
canonical files, regenerate native trees with `scripts/cg_generate_targets.py`
instead of hand-editing `.agents/`, `.claude/`, or `.opencode/`.

### 3. Use a baseline-aware audit, not a false zero-finding gate

Capture the model audit before the change and compare it with the post-change
inventory. The acceptance rule is not "all missing assignments disappear." The
acceptance rule is:

- `/cr-work` disappears from `missing_catalog_assignments`;
- no new invalid roles, unknown models, or drift appear;
- the remaining missing assignments are exactly the pre-existing out-of-scope
  CR prompts.

This turns the audit into a regression detector instead of a repository-cleanup
wish.

### 4. Keep support status truthful

If the exact Copilot frontmatter label has not been manually validated, keep the
catalog status as `not-tested` and let the audit emit a visible warning. Do not
invent a runtime fallback engine in docs or metadata.

Static governance can truthfully express:

- canonical Copilot declaration: `GPT-5.6 Luna`;
- Codex native mapping: `GPT-5.6 Luna`;
- Claude native mapping: `sonnet`;
- OpenCode native behavior: inherited.

It must not claim that Copilot will silently substitute another model at
runtime.

### 5. Add focused guardrails around the exact slice

Protect the override with tests at each layer:

- audit role acceptance and baseline comparison;
- target mapping resolution;
- generated Codex and Claude command projections;
- OpenCode non-pinning assertion;
- docs/model-guide/reference synchronization;
- focused Pester model-assignment coverage.

## Prevention

For future one-command model changes:

1. If only one prompt or agent should move, add a dedicated role. Do not reuse
   a shared role unless every consumer is intended to move together.
2. Update the canonical prompt, model catalog, audit role registry, target
   mappings, docs, and tests in one session. A frontmatter-only change is
   incomplete by definition.
3. Regenerate native target trees from `.github/` sources. Never patch
   generated targets directly.
4. When the repository already has governance debt, capture a before/after
   audit baseline and assert only the approved delta.
5. Preserve the inherited-model equivalence rule for ordinary model-picker
   prompts; dedicated explicit overrides are a different case and should remain
   exact.
6. Keep static metadata truthful about support status. `not-tested` plus a
   warning is better than fictional fallback behavior.

## Related

- `.cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md`
- `.cg-docs/solutions/build-errors/2026-07-29-cr-agent-model-strings-must-use-gpt-catalog-compliant.md`
- `.cg-docs/plans/2026-08-02-cr-work-gpt-5-6-luna-plan.md`
- `.cg-docs/work-reports/2026-08-03-cr-work-gpt-5-6-luna-plan.md`