---
date: 2026-05-15
depth: light
parent-review: .cg-docs/reviews/2026-05-15-auto-generated-project-wiki-review.md
type: verification
findings:
  P2.1: open
  P2.2: open
  P3.1: open
  P3.2: open
  P3.3: open
  P3.4: open
  P3.5: open
  P3.6: open
---

## Verify Review Report

**Review depth**: light (forced by mode:verify)  
**Files reviewed**: 19 (12 modified, 7 new)  
**Mode**: mode:verify  
**Prior review**: `.cg-docs/reviews/2026-05-15-auto-generated-project-wiki-review.md` (all 30 findings fixed)  
**Findings**: 8 (P0: 0, P1: 0, P2: 2, P3: 6)

---

### P0 — BLOCKING
*None.*

---

### P1 — CRITICAL
*None.*

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/agents/cg-wiki.agent.md` Pre-Flight step 3 — Halt message when `_wiki.yml` is absent still says "Run `/cg-setup` or `/cg-wiki rebuild` to initialize." But `rebuild` mode itself halts in Pre-Flight when `_wiki.yml` is absent — suggesting it as recovery creates a two-step failure loop. The prompt-level fix (P3.7) removed this from `cg-wiki.prompt.md` Step 2 but did not update the agent Pre-Flight halt message.  
  **Fix**: Change agent Pre-Flight halt message to: "Wiki manifest not found at `<folder>/_wiki.yml`. Run `/cg-setup` to initialize the wiki (it dispatches `@cg-wiki init` automatically)."

- **[P2.2]** [cg-testing] `tests/wiki.Tests.ps1` — The P2.8 test ("`.github/` write prohibition") asserts `($content -match 'must NOT')` which matches *any* "must NOT" phrase in the file. It does not verify the `.github/` prohibition specifically. The original P2.8 finding was about testing that the agent prohibits `.github/` writes — the current test provides no coverage of that specific constraint.  
  **Fix**: Add a targeted test to `cg-wiki.agent.md - security rules` Describe block:
  ```powershell
  # P2.8 — .github/ write prohibition
  It "prohibits writing to .github/ infrastructure files (P2.8)" {
      ($content -match '\.github') | Should -Be $true
  }
  ```
  Or combine with the "must NOT" check for stronger coverage: `($content -match 'must NOT.*\.github|\.github.*must NOT')`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-setup.prompt.md` B1.1.6 — "No project wiki found. Run `/cg-setup` to initialize the wiki for this project." The user is already executing `/cg-setup` (Mode B). Re-running with `compound-gpid.local.md` present re-enters Mode B which does not run A5.8 wiki init.  
  **Fix**: Clarify the note: "No project wiki found. Run `/cg-setup` in a fresh project session, or invoke `@cg-wiki` directly with `mode: init`."

- **[P3.2]** [cg-testing] `tests/wiki.Tests.ps1` ~line 281 — Injection scan test `($content -match 'SYSTEM:|Ignore|Override|Forget')` has false-positive risk. `Ignore`, `Override`, and `Forget` are common English words appearing in unrelated agent prose ("do not override user preferences," "ignore this field"). The test passes even if no injection-scan rule exists.  
  **Fix**: Anchor to the injection context: `($content -match 'SYSTEM:|Ignore previous|Override instructions')` or use the word `injection` as a co-condition.

- **[P3.3]** [cg-testing] `tests/wiki.Tests.ps1` ~line 66 — `($content -match '[Nn]ested')` is too broad. "Nested" appears in many documentation contexts (nested YAML, nested lists, etc.). Test passes without verifying the marker-nesting rule.  
  **Fix**: Use `($content -match '[Nn]ested.*marker|[Nn]ested.*cg:auto')`.

- **[P3.4]** [cg-testing] `tests/wiki.Tests.ps1` lines ~203–207, ~321–326, ~455–456 — Three `It` blocks contain 2–3 `Should` assertions each. When one fails, Pester 4 throws immediately with no indication of which assertion failed — inconsistent with the P3.3 split pattern applied to trigger criteria.  
  **Fix**: Split each multi-assertion `It` block into individual `It` blocks (one assertion per block).

- **[P3.5]** [cg-testing] `tests/wiki.Tests.ps1` ~line 73 — Code-block marker test `($content -match 'code block|fenced code|inline code')` is too broad. The SKILL.md discusses code blocks in multiple unrelated contexts. Test does not verify the specific rule that `cg:auto:end` inside fenced code is ignored.  
  **Fix**: Use `($content -match 'cg:auto:end.*code block|code block.*cg:auto:end|fenced.*cg:auto')` or similar anchored pattern.

- **[P3.6]** [cg-code-quality] `.github/agents/cg-wiki.agent.md` Pre-Flight — `pages[].order` uniqueness is specified only in `cg-skill-wiki/SKILL.md`. The agent Pre-Flight step 3 enumerates `pages[].file` validations with named halt messages, but `pages[].order` uniqueness validation is not co-located as an explicit Pre-Flight check. A model following only the agent's Pre-Flight checklist may skip it.  
  **Fix**: Add to agent Pre-Flight step 3 alongside `pages[].file` validation: "Validate `pages[].order` values: must be positive integers, unique within the manifest. Halt if duplicates: `Duplicate order values in _wiki.yml: <values>`."

---

### ✅ Passed

- **cg-code-quality**: P1.1 permission carve-out is logically sound and unambiguous ✓
- **cg-code-quality**: P2.1 step ordering correct (A5.7 roadmap before A5.8 wiki) with no broken cross-references ✓
- **cg-code-quality**: P2.3 model-guide.md count (39 = 22 prompts + 17 agents) consistent with test sentinels ✓
- **cg-code-quality**: P2.6 `/cg-wiki` present in `copilot-instructions.md` Workflow Entry Points; test at line 249 correctly targets the `$section` variable ✓
- **cg-code-quality**: P2.7/P2.16 `cg:auto:end` and code-block exclusion documented in SKILL.md; test patterns match actual strings ✓
- **cg-code-quality**: P3.7 Step 2 error message reads "Run `/cg-setup`" — actionable and non-circular in prompt context ✓
- **cg-code-quality**: P3.9 `.gitignore` explanatory comment correct ✓
- **cg-testing**: `tests/Run-Tests.ps1` correctly registers `wiki` test file at the right position ✓
- **cg-testing**: `prompt-tools.Tests.ps1` P2.6 test reuses `$section` variable correctly ✓
- **cg-testing**: `prompt-tools.Tests.ps1` `cg-wiki.agent.md` excluded from write-tool sweep ✓
- **cg-testing**: `model-assignments.Tests.ps1` sentinel counts (22 prompt / 17 agent) match actual directory ✓
- **cg-testing**: P3.1 all assertions use `Should -Be` Pester 4 style ✓
- **cg-testing**: P3.3 trigger criteria correctly split into 4 individual `It` blocks ✓
