---
date: 2026-06-03
depth: light
parent-review: .cg-docs/reviews/2026-06-01-test-correctness-assessment-review.md
type: verification
findings:
  V-P2.1: open
  V-P3.1: open
  V-P3.2: open
  V-P3.3: fixed
  V-P3.4: fixed
  V-P3.5: open
  V-P3.6: fixed
  V-P3.7: fixed
---

## Review Report

**Review depth**: light (verification mode)
**Files reviewed**: 7 (`.github/prompts/cg-fixbug.prompt.md`, `.github/prompts/cg-work.prompt.md`,
`.github/skills/cg-skill-r-testing/SKILL.md`, `.github/skills/cg-skill-r-testing/references/test-integrity.md`,
`tests/prompt-tools.Tests.ps1`, `roadmap.json`, `docs/reference.md`)
**Agents**: cg-code-quality, cg-testing
**Findings**: 8 (P0: 0, P1: 0, P2: 1, P3: 7)

**Verification result**: No P0 or P1 regressions. All 30 original findings appear correctly applied. Eight
new issues found — all introduced by the fix pass itself.

---

### ✅ Passed checks
- cg-code-quality: All 30 prior findings confirmed applied. No P0/P1 regressions.
- cg-testing: All new co-author Pester tests validate real prompt content (no tautological assertions).

---

### P2 — IMPORTANT (should fix)

- **[V-P2.1]** [cg-code-quality] `.github/prompts/cg-work.prompt.md` — Grammatical ambiguity in red-phase skip qualifier: "with **no colocated Pester assertions**" attaches syntactically to "YAML frontmatter" only, leaving "markdown documentation" unconditionally exempt.
  **Why**: An agent modifying a `.prompt.md` with colocated Pester coverage could still reason "this is markdown documentation → skip red-phase" because the qualifier does not apply to "markdown documentation" in the current phrasing. This partially defeats the P1.2 fix.
  **Fix**: Restructure to apply qualifier to all exempted categories unambiguously, e.g.: `config files, markdown documentation, or YAML frontmatter — but only when no Pester test file asserts against the modified file — or directory scaffolding`.
  **Tag**: [manual]

---

### P3 — MINOR (nice to have)

- **[V-P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:~22` — Comment cites wrong finding ID for the `Get-ToolsList` relocation (`P2.17` cited, but P2.17 = source priority order swap).
  **Why**: Misleads anyone tracing change history.
  **Fix**: Correct the finding ID or replace with prose: `# Note: Get-ToolsList is defined in helpers.ps1 (shared helper, moved here to avoid duplication across test files)`.
  **Tag**: [manual]

- **[V-P3.2]** [cg-code-quality] `.github/skills/cg-skill-r-testing/references/test-integrity.md:~62` — Footer claim "the six steps map to Step 4 sub-points 1–6" is inaccurate: step 1 ("Write the test first") maps to cg-fixbug Step 2, not Step 4.
  **Why**: An agent consulting this mapping to understand the protocol flow gets a misleading picture.
  **Fix**: Replace with: `Sub-points 1–5 of Step 4 correspond to steps 2–6 of this protocol (step 1 — write the test first — happens in cg-fixbug Step 2). Sub-point 6 (flawed test repair) is an extension beyond this protocol.`
  **Tag**: [manual]

- **[V-P3.3]** [cg-code-quality] `.github/prompts/cg-fixbug.prompt.md:~73-75` — "See also" cross-reference note and "I cannot determine" speech-act template merged into one blockquote by the P1.3 cross-reference addition (no blank line between them).
  **Why**: Agent may read the speech act as part of the cross-reference annotation rather than as a separate instruction.
  **Fix**: Insert blank line between the `> See also...` line and the `> "I cannot determine..."` block; add explicit label.
  **Tag**: [safe_auto]

- **[V-P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — P3.7 circular-test regex has degenerate second alternative: `circular.test.*subcategory.*wrong.test|subcategory.*wrong.test` — the second arm matches any "subcategory…wrong-test" text, with or without "circular-test."
  **Why**: Weakens the assertion; a regression dropping "circular-test" from the note would still pass.
  **Fix**: Drop the second alternative: `($content -match 'circular.test.*subcategory.*wrong.test') | Should -Be $true`
  **Tag**: [safe_auto]

- **[V-P3.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — P2.18 `It` description says "directs agent to proceed with new failing test from Step 1.5 source" but the regex only checks the opening phrase; the "Step 1.5" direction on the next line is not validated by the regex.
  **Why**: Test name is aspirational, not descriptive of what is actually checked.
  **Fix**: Either split into two `It` blocks (one for opening phrase, one for Step 1.5 mention) or rename to match what is actually tested.
  **Tag**: [manual]

- **[V-P3.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — P2.16 Describe block lacks a negative guard: if `## Mutation Verification Protocol` were accidentally re-added alongside the new heading, all four P2.16 assertions would still pass.
  **Why**: Silent regression path.
  **Fix**: Add: `It "old heading is absent" { ($content -match '(?m)^## Mutation Verification Protocol') | Should -Be $false }`
  **Tag**: [safe_auto]

- **[V-P3.7]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Legacy "file exists" Describe block at line ~5397 still uses the soft pattern `## Red-Green Verification Protocol|## Mutation Verification Protocol`, accepting the reverted old name.
  **Why**: Creates a mixed message between the legacy Describe (permissive) and the dedicated P2.16 Describe (strict). A revert to the old name would pass the legacy test.
  **Fix**: Tighten to: `($content -match '## Red-Green Verification Protocol') | Should -Be $true`
  **Tag**: [safe_auto]
