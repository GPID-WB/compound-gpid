---
date: 2026-07-29
type: review
subject: Phase 1 — Port CR intellectual content
commit: 144066f
branch: feat/compound-research-v2
depth: standard
agents: [cg-code-quality, cg-testing, cg-version-control]
status: complete
findings: 13
p0: 0
p1: 2
p2: 6
p3: 5
safe-auto-applied: [P2.3, P2.4, P2.5]
manual-applied: [P1.1, P1.2]
deferred: [P2.1, P2.2, P3.1, P3.2, P3.3, P3.4, P3.5]
---

# Review: Phase 1 — CR Module Port to v1.0

## Scope

75 files committed in `feat(cr): port compound-research intellectual content from v0.10 branch`
(commit `144066f`): 9 CR agents, 5 CR prompts, 12 CR skills, 2 instruction files,
1 new test file (`tests/cr-prompts.Tests.ps1`), 43 `.cg-docs/` artifacts.

Review depth: **standard** (cg-code-quality, cg-testing, cg-version-control).
No cg-documentation, cg-performance, cg-architecture, cg-data-quality — deferred; changes are
markdown/YAML only with no performance or data-handling code.

---

## P1 — CRITICAL (fixed in this commit)

### P1.1 — CR agent model strings: `(copilot)` suffix not in model-catalog [cg-code-quality]
All 9 CR agents carried `model: Claude Sonnet 4.6 (copilot)` or `model: Claude Opus 4.6 (copilot)`.
The `(copilot)` suffix is not a recognized model identifier in `model-catalog.json` — could cause
silent fallback in routing. **Fixed**: replaced all 9 agents with `model: GPT-5.4`.

### P1.2 — `Claude Opus 4.6` has `policyStatus: user-selected-only` [cg-code-quality + cg-testing]
`cr-econometric-reasoning.agent.md` and `cr-mathematical-verification.agent.md` used Opus —
a catalog-restricted model that must not be hard-coded. Two `cr-prompts.Tests.ps1` assertions
checked for `Claude Opus 4.6`. **Fixed**: both agents now use `GPT-5.4`; both test assertions
updated to check for `GPT-5.4`.

---

## P2 — IMPORTANT

### P2.1 — `docs/model-guide.md` and `model-catalog.json` out of sync [cg-code-quality] [deferred: Phase 4]
Neither file includes the 5 CR prompts or 9 CR agents. The guide says it "must stay in sync."
**Deferred to Phase 4** (model catalog integration phase).

### P2.2 — 7 CR agents use GPT-5.4 — OpenAI-first rule satisfied [cg-code-quality] [resolved by P1.1/P1.2]
After P1.1 + P1.2 fixes, all 9 CR agents use `GPT-5.4`, satisfying the OpenAI-first governance.

### P2.3 — `cr-replication-package` missing from P3.5 `$crAgents` array [cg-testing] [FIXED]
8 agents listed instead of 9 in the module-check loop. Added `cr-replication-package`.

### P2.4 — Unguarded `Get-Frontmatter` at Context scope in agent structural loop [cg-testing] [FIXED]
If an agent file was absent, `Get-Content` would throw at Context scope instead of cleanly failing
the `It "exists"` assertion. Applied `if (Test-Path $path) { ... } else { '' }` guard on line 392.

### P2.5 — `tools:.*'read'` regex fails for multi-line YAML arrays [cg-testing] [FIXED]
Replaced with `Get-ToolsList -Frontmatter $fm` helper (already defined in `tests/helpers.ps1`).
Also replaced the `notmatch "'write'"` check with `Get-ToolsList` for consistency.

### P2.6 — No test validates CR agent model names against catalog [cg-testing] [advisory, deferred: Phase 4]
`model-assignments.Tests.ps1` only checks non-empty model field. No validation against
`model-catalog.json`. To be addressed when catalog is updated in Phase 4.

---

## P3 — MINOR (deferred)

### P3.1 — Commit message body inaccuracy [cg-version-control]
Body claims "No modifications to existing v1.0 files" but `model-assignments.Tests.ps1` was modified.
Harmless; no amend warranted since commit already in history.

### P3.2 — Consider `Phase N/8:` prefix in future commit bodies [cg-version-control]
Advisory for remaining phases; no action on past commit.

### P3.3 — `cr-skill-identification-strategies` uses non-canonical task type [cg-code-quality]
Description references "Identification/Estimation" — not in the 8-type research taxonomy.
Low risk; advisory for Phase 7 polish.

### P3.4 — Multiple `Should` assertions in one `It` block [cg-testing]
`"contains all 8 task types"` bundles 8 assertions; first failure hides others.
Cosmetic; defer to later cleanup.

### P3.5 — Misleading `Describe` name for `cg-review.prompt.md` test [cg-testing]
A `cr-review.prompt.md` Describe block contains an assertion against `cg-review.prompt.md`.
Rename during Phase 7 polish.

---

## Version Control Checks — All Passed [cg-version-control]

- Conventional commits format: ✓
- Branch naming (`feat/compound-research-v2`): ✓
- No secrets or credentials: ✓
- No `.gitignore` gaps: ✓
- No binary/data files: ✓
- Commit atomicity: appropriate for port-only phase

---

## Fixes Applied in Review Follow-up Commit

Files modified:
- `.github/agents/cr-*.agent.md` (9 files): `model:` field → `GPT-5.4`
- `tests/cr-prompts.Tests.ps1`: 2 Opus model assertions, `$crAgents` array, `Get-Frontmatter` guard, tools regex
