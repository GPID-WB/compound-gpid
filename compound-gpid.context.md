# Compound GPID — Project Context

This file captures project-specific conventions, workspace notes, and domain
rules that help Copilot produce accurate outputs across all prompts and sessions.

---

## Prompt Design Conventions

- **Mode-specific step skipping**: Steps depending on in-scope findings (e.g., skill loading) are skipped when a mode flag (`--migrate`) is present. The flag is evaluable at invocation time — no formal arg-parsing step needed.

- **Within-step pre-flight ordering**: Inside a prompt step, all guard checks, derivations, and pre-condition warnings must appear textually before the user-facing offer or question. A model executing linearly displays the offer before evaluating any rule that follows it. Canonical order: guards → derive values → normalize → warn on pre-conditions → show offer. See `.cg-docs/solutions/testing-patterns/2026-05-05-within-step-preflight-must-precede-offer-template.md`.

- **Deferred side-effects come after the primary deliverable**: In interactive prompts, side-effect offers (e.g., "open a PR", "add to roadmap") must come after the primary deliverable is created — not before. Pattern: complete the main output first, then offer optional follow-on actions. **Exception — branch selection**: "Which branch should this work go on?" is workspace *configuration*, not a side-effect. Ask it **before any clarifying questions or work begins** so the user's investment lands on the right branch. Burying it in the handoff menu causes it to be missed. See `.cg-docs/solutions/testing-patterns/2026-05-01-branch-offer-must-precede-user-investment-steps.md`.

## Testing Conventions

- **IndexOf guard pattern**: Block-scoped prompt tests that extract text via `$content.Substring($start, $end - $start)` must first assert both index values with `$start | Should BeGreaterThan -1` and `$end | Should BeGreaterThan $start`. Without guards, a missing section header throws `ArgumentOutOfRangeException`, obscuring which assertion failed.

- **Test only current state, never future state**: Pester tests must assert what is true now. Writing a test for a schema marker before the marker is applied creates a persistent pre-existing failure that pollutes every test run until resolved. Either apply the marker in the same commit as the test, or mark it `-Pending` to defer without failing. See `.cg-docs/solutions/testing-patterns/2026-04-29-premature-schema-marker-test-creates-persistent-failure.md`.

- **SCHEMA_VERSION bumps are not additive**: each bump overwrites the file entirely; pending markers from prior deferred review findings are silently lost. Before bumping `SCHEMA_VERSION` for a new feature, check `.cg-docs/solutions/` and `.cg-docs/reviews/` for any deferred markers (e.g., `scope-fields`) that must be included in the same bump.

- **Fix-triage prompt changes need co-authored tests**: Every fix applied to a `.prompt.md`, `.agent.md`, or `SKILL.md` file during fix-triage must be accompanied by a `($content -match '...') | Should Be $true` assertion in the same session. Do not defer test authoring to the end — add it immediately after each fix. A verify pass on a 21-finding triage found 10 changes had zero regression coverage. See `.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md`.

- **Regex alternation masks coverage when first branch is always true**: `A.*B|C.*D` in `-match` short-circuits on first match. If `A.*B` always matches, `C.*D` is never required. When verifying N independent words must all be present, use N separate `Should Be $true` assertions — not a single alternating regex. See `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md`.

- **Stale regex alternation after prompt refactoring**: OR-pattern tests (`A|B`) that tolerate two phrasings become stale when the prompt settles on one. The dead branch silently passes via the surviving branch, masking any future regression on the live branch. After any prompt refactoring pass, audit all `-match` expressions containing `|` and verify each branch independently against the updated text; drop dead branches. See `.cg-docs/solutions/testing-patterns/2026-05-05-stale-alternation-after-prompt-refactoring.md`.

- **Cross-prompt journey consistency**: When a prompt step ends with "Run `/cg-X`" or "Next: `/cg-X argY`", verify that the target prompt's handler for the implied state does NOT halt before completing the intended action. A per-prompt test that X "contains the text" is insufficient — only a negative assertion (`Should Be $false`) on the broken advice, or a behavioral contract test covering both prompts together, catches this class of bug. See `.cg-docs/solutions/testing-patterns/2026-05-06-cross-prompt-user-journey-must-be-validated-end-to-end.md`.

## Bash Scripting Conventions

- **Command substitution functions must be stdout-clean**: Any bash function whose return value is captured via `VAR="$(fn)"` must write only the return value to stdout. All warnings and progress messages must go to `>&2`. Color helpers (`print_yellow`, `print_gray`, etc.) are **not** stderr-safe by default — always add `>&2` when calling them inside a function used via command substitution. Without `>&2`, the warning text is captured into the variable alongside the intended return value, corrupting every downstream file operation silently (exit code 0, no error). See `.cg-docs/solutions/bugs/2026-05-05-print-yellow-stdout-corrupts-command-substitution-variable.md`.
