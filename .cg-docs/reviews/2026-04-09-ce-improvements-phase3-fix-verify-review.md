---
plan: .cg-docs/plans/2026-04-08-ce-improvements-integration.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P3.1: skipped
  P3.2: skipped
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

## Review Report — Phase 3 Fix-Verify (Post-Fix-Triage Light)

**Review depth**: standard (auto-escalated from `light` — ≥ 50 non-test lines changed)
**Files reviewed**: 44 files on `feat/ce-improvements` vs `main`
**Findings**: 0 × P0 / 2 × P1 / 17 × P2 / 6 × P3 = 25 total

---

### P0 — BLOCKING (immediate remediation required)

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality] `cg-fix-triage.prompt.md:Special Mode --migrate:Step 2b` — P0 findings silently excluded from --migrate parsing
  **Why**: The migration parsing pattern lists `**[P1.`, `**[P2.`, `**[P3.` but omits `**[P0.`. After running `--migrate`, P0 (blocking) findings are absent from the `findings:` frontmatter and permanently invisible to `/cg-fix-triage`. The highest-severity findings become untracked.
  **Fix**: Add `**[P0.` to the parsing pattern list. Update the Step 1.4 example IDs to include a `P0.1` example.

- **[P1.2]** [cg-data-quality] `cg-plan.prompt.md:Step 1.5` — Plan scope enum can silently receive invalid Thinking Partner scope values
  **Why**: Step 1.5 says to inherit `scope:` from brainstorm frontmatter. Plan scope enum is `Lightweight|Standard|Deep`; brainstorm scope is `Lightweight|Standard|Deep|Focused|Extended|Strategic`. A Thinking Partner brainstorm with `scope: Focused` passes a non-plan value into the plan. The confidence check's scope-conditional logic (`Standard or Deep`) is undefined for `Focused`/`Extended`/`Strategic`.
  **Fix**: Add guard: "If the inherited scope is `Focused`, `Extended`, or `Strategic` (Thinking Partner values not valid for plans), do not inherit it — run scope assessment normally."

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `cg-plan.prompt.md:Step 6` — Handoff options 2 and 3 both invoke `/cg-brainstorm` with different intents but same label
  **Why**: Options 2 ("Revisit open questions before starting") and 3 ("Explore a related or follow-up topic first") are functionally identical — both route to `/cg-brainstorm` with no mechanism to distinguish intent. Users receive no actionable choice.
  **Fix**: Merge into a single option: "**`/cg-brainstorm`** — Revisit open questions or explore a related topic."

- **[P2.2]** [cg-code-quality / cg-performance] `cg-brainstorm.prompt.md:Step 5c` — Duplicate "Update charter" entries in Thinking Partner handoff
  **Why**: Non-software task handoff lists "Update charter" as both options 1 and 2 with overlapping descriptions. Both route to the same action on the same file.
  **Fix**: Merge into a single entry: "**Update charter** — Revise `compound-gpid.md` (objective, current focus, or key deliverables)."

- **[P2.3]** [cg-architecture] `cg-brainstorm.prompt.md:Step 1.5` + `cg-plan.prompt.md:Step 1.5` — Thinking Partner scope values are incompatible with cg-plan scope inheritance
  **Why**: Brainstorms save `scope: Focused|Extended|Strategic` for non-software tasks and explicitly say plans will inherit this. `cg-plan`'s scope table only maps `Lightweight|Standard|Deep`. No guard handles the mismatch; classification silently falls through.
  **Fix**: Add guard in `cg-plan` Step 1.5: if inherited scope is `Focused|Extended|Strategic`, warn "This brainstorm used Thinking Partner scope classification incompatible with plan scope. Running scope assessment fresh." and proceed normally.

- **[P2.4]** [cg-architecture] `cg-work.prompt.md:Step 1` — Inline plans saved to disk have no frontmatter template; cg-resume display will be inconsistent
  **Why**: When `cg-work` saves an inline plan, no frontmatter template is specified. `cg-resume` extracts `estimated-effort:`, `tags:`, and status from plan frontmatter. Inline plans missing these fields produce incomplete session summaries.
  **Fix**: Add minimum frontmatter template to inline plan save instruction: `date`, `title`, `status: active`, `scope: Lightweight`, `estimated-effort: small`, `tags: [inline]`.

- **[P2.5]** [cg-architecture] `cg-plan.prompt.md:Step 6` — `/cg-review` removed from handoff with no alternative review gate for standard/deep plans
  **Why**: Previous Step 6 option 2 was `/cg-review` (review the plan before coding). The current version replaces it with a second `/cg-brainstorm` option. For Standard/Deep plans where the confidence check adds scrutiny, there is now no displayed path to plan validation before starting implementation.
  **Fix**: Restore `/cg-review` as an option for Standard/Deep plans. Collapse the two brainstorm options into one.

- **[P2.6]** [cg-reproducibility] `SCHEMA_VERSION` — Schema version does not reflect new `scope:` frontmatter field
  **Why**: SCHEMA_VERSION is dated `2026-04-07-r-syntax-dialect` but plans and brainstorms now carry a `scope:` field and brainstorms carry a `status:` comment. These are schema-level changes triggering a new version.
  **Fix**: Update SCHEMA_VERSION to `2026-04-09-scope-fields` (or similar).

- **[P2.7]** [cg-reproducibility] `cg-plan.prompt.md:Step 0.5` — Plan scope inheritance has no fallback mapping for Thinking Partner values
  **Why**: Step 1.5 only says "inherit scope if present" with no mapping between Thinking Partner scope vocabulary and plan scope vocabulary. Ambiguous resolution.
  **Fix**: Add mapping: `Focused→Lightweight`, `Extended→Standard`, `Strategic→Deep` (or guard—see P1.2).

- **[P2.8]** [cg-reproducibility] `cg-plan.prompt.md:Step 0` — Thinking Partner brainstorm artifacts not handled on load
  **Why**: If a user runs `/cg-plan` after a Thinking Partner brainstorm, cg-plan has no instruction to recognize this artifact type and suggest the appropriate action (charter update vs. plan creation).
  **Fix**: Add to Step 0.5: "If a loaded brainstorm has `scope: Focused|Extended|Strategic` (Thinking Partner artifact), warn: 'This brainstorm represents a strategic decision, not a software task. Consider updating `compound-gpid.md` instead. Proceed with planning anyway? (not recommended)'"

- **[P2.9]** [cg-data-quality] `cg-fix-triage.prompt.md:Step 2` — No warning for unrecognized arguments
  **Why**: Step 2 defines valid argument forms but not error behavior for unrecognized inputs (e.g., `--verbose`). Unlike `cg-review` which warns on unrecognized args, `cg-fix-triage` silently falls through to "fix all findings" — a potentially destructive default.
  **Fix**: Add: "If any argument is not in the recognized list, warn: `Unrecognized argument '<arg>' — ignoring. Recognized: P0, P1, P2, P3, individual IDs (e.g., P1.2), or --migrate.`"

- **[P2.10]** [cg-data-quality] `cg-plan.prompt.md:Step 4.5` — Confidence check references "risks table" but plan template uses prose
  **Why**: Step 4.5 says "Does the risks table address the top 3 failure modes?" but the template defines `## Risks & Mitigations` as free-form prose. The "3 risks" threshold is unverifiable against unstructured text.
  **Fix**: Either add a risk table format to the template (`| Risk | Likelihood | Mitigation |`) or change Step 4.5 language to "Risks & Mitigations section" and define what "3 risks" means (e.g., 3 bulleted items).

- **[P2.11]** [cg-data-quality] `cg-fix-triage.prompt.md:Special Mode --migrate:Step 2c` — Migration prepends duplicate frontmatter for files with partial frontmatter
  **Why**: The migration targets files without a `findings:` key. Step 2c instructs "Add YAML frontmatter to the file" as a full new `---` block including `plan:`. For files with existing frontmatter that only lack `findings:`, this creates two frontmatter blocks — malformed YAML.
  **Fix**: Split logic: "If no frontmatter, prepend full block. If existing frontmatter lacks `findings:`, insert only the `findings:` map into the existing block."

- **[P2.12]** [cg-documentation] `docs/reference.md` — `/cg-review` syntax notation uses mutually exclusive pipe syntax for combinable arguments
  **Why**: The notation `/cg-review [light|standard|thorough|mode:autofix]` implies only one argument at a time, but `docs/workflow.md` shows they can be combined (`/cg-review light mode:autofix`).
  **Fix**: Change to `/cg-review [light|standard|thorough] [mode:autofix]` with a note: "Arguments can be combined."

- **[P2.13]** [cg-documentation] `docs/workflow.md` — `/cg-setup` has no "When/What happens/Output" section
  **Why**: Every other command (ideate, brainstorm, plan, work, review, compound, resume, strategy) has a dedicated subsection. `/cg-setup` is only referenced in the charter note and loop diagram preamble.
  **Fix**: Add a `/cg-setup` subsection with When/What happens/Output.

- **[P2.14]** [cg-performance] `cg-work.prompt.md:Step 2` — One-time test-discovery instruction is buried inside the per-step loop
  **Why**: The instruction "(Perform this scan once at session start to build a module→test-file index; reference the index within each step rather than re-scanning.)" is a parenthetical inside the "For **each step**" block. Agents parsing linearly may re-scan every step.
  **Fix**: Promote to a dedicated **Step 1.6: Build Test Index** subsection before "Step 2: Implement Step by Step," removing the parenthetical from inside the loop.

- **[P2.15]** [cg-architecture / cg-reproducibility] `cg-resume.prompt.md:Step 2a` — `scope:` field present in plan frontmatter but not surfaced in resume display
  **Why**: `cg-plan` writes `scope:` to plan frontmatter. `cg-resume` extracts `estimated-effort`, `tags`, date, title from plans but not `scope`. Users can't distinguish Deep from Lightweight plans without opening each file.
  **Fix**: Add `scope` to extracted fields in `cg-resume` Step 2a and include in the pending-work display.

- **[P2.16]** [cg-testing] `tests/prompt-tools.Tests.ps1` — cg-work inline plan save-to-disk instruction not tested
  **Why**: P1.30 Describe block verifies 4 assertions about the inline plan fallback but omits the "save to `.cg-docs/plans/YYYY-MM-DD-<brief-title>.md` before implementing" requirement added in Phase 3.
  **Fix**: Add: `It "saves inline plan to .cg-docs/plans/ before implementing" { ($content -match '\.cg-docs[/\\]plans.*YYYY-MM-DD') | Should Be $true }`

- **[P2.17]** [cg-performance] `tests/prompt-tools.Tests.ps1` — SKILL.md cross-link tests duplicated
  **Why**: "skill SKILL.md - relative markdown links resolve" and "skill file cross-links resolve" both walk the full skills tree checking link resolution. SKILL.md files are a subset — every SKILL.md link is checked twice.
  **Fix**: Remove the SKILL.md-only block and rely on the all-files "skill file cross-links resolve" block which already covers SKILL.md files.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] Multiple prompts — Step 0 boilerplate duplicated verbatim across 8+ prompts
  **Why**: Intentional per design (copilot-instructions.md documents this) but creates maintenance overhead if Step 0 logic changes.
  **Fix**: Document rationale inline if not already present. No action needed unless VS Code prompt includes/macros become available.

- **[P3.2]** [cg-code-quality] `cg-ideate.prompt.md` — Step numbering inconsistency (no sub-steps like 0.5, 1.1, 1.5)
  **Why**: Other prompts use granular sub-step numbering; cg-ideate uses integer steps only.
  **Fix**: Align numbering if/when cg-ideate needs intermediate steps. No immediate action needed.

- **[P3.3]** [cg-documentation] `docs/workflow.md` — Strategy section placement after developer-only Release section is confusing
  **Why**: Strategy is a key re-entry point shown prominently in the loop diagram but documented after dev-only content.
  **Fix**: Add "Non-linear Entry Points" heading before Roadmap and Strategy sections to differentiate from sequential steps.

- **[P3.4]** [cg-performance] `cg-plan.prompt.md:Step 0.5` + `cg-brainstorm.prompt.md:Step 0.5` — 5-file / 3-keyword fallback threshold duplicated with no sync annotation
  **Why**: The threshold policy value is duplicated across two files with no comment indicating they must stay in sync.
  **Fix**: Add `<!-- threshold synced with cg-brainstorm/cg-plan Step 0.5 -->` comment to both files.

- **[P3.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — mode:autofix safe_auto tag test pattern context-independent
  **Why**: The test `($content -match 'safe_auto' -and $content -match 'advisory')` passes if either keyword appears anywhere in the file, including comments.
  **Fix**: Tighten to `($content -match '(?s)Step 4.*safe_auto.*advisory')` to ensure both appear in the autofix Step 4 context.

- **[P3.6]** [cg-testing] `tests/Run-Tests.ps1` — No enforcement that all discovered `.Tests.ps1` files are registered
  **Why**: New test files added but not registered in `$testNames` produce a non-fatal warning and don't run — silent coverage gap.
  **Fix**: Document in Run-Tests.ps1 header that all `.Tests.ps1` files must be registered.

---

### ✅ Passed

- **cg-version-control**: No credentials, API keys, or sensitive data. `.gitignore` correctly excludes `compound-gpid.local.md`. All `.cg-docs/` knowledge artifacts properly committed. Branching follows convention. ✓
- **cg-code-quality**: No broken markdown tables, unclosed code fences, or dead references found. ✓
- **cg-testing**: No encoding/Windows-1252 issues in test patterns. All 11 test files registered in Run-Tests.ps1. ✓
- **cg-documentation**: copilot-instructions.md Workflow Entry Points table accurate. No outdated command references. ✓
