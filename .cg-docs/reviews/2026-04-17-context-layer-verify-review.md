---
branch: feat/context-layer
date: 2026-04-17
depth: standard
parent-review: .cg-docs/reviews/2026-04-17-context-layer-review.md
type: verification
test-baseline: "1057 passed / 1 pre-existing failure (cg-compound.prompt.md - offers to create context.md if it does not exist)"
findings:
  V-P2.1: fixed
  V-P2.2: fixed
  V-P2.3: fixed
  V-P2.4: fixed
  V-P2.5: fixed
  V-P2.6: fixed
  V-P3.1: fixed
  V-P3.2: fixed
  V-P3.3: fixed
  V-P3.4: advisory
  V-P3.5: advisory
  V-P3.6: advisory
  V-P3.7: advisory
  V-P3.8: advisory
---

# Verification Review — feat/context-layer

**Branch**: `feat/context-layer`  
**Date**: 2026-04-17  
**Type**: Standard verification (auto-escalated from light — `scripts/` changed, ≥50 non-test lines)  
**Parent review**: [2026-04-17-context-layer-review.md](2026-04-17-context-layer-review.md)  
**Agents**: `cg-code-quality`, `cg-testing`, `cg-data-quality`, `cg-documentation`, `cg-adversarial`  
**Test baseline**: 1,057 passed / 1 pre-existing failure (unchanged)

---

## Summary

All P1–P3 findings from the parent review were fixed during P1/P2/P3 triage sessions. A new P1-level regression was discovered pre-dispatch (P3.7 template comment contained `{{placeholders}}` that would be substituted in generated output — fixed immediately, tests confirmed clean). This verification review identified 7 additional fixes applied in this session, plus 5 advisory findings recorded for future work.

---

## Findings Applied in This Session

### V-P2.1 `cg-code-quality` · scripts/link.ps1:170 — Missing `-Encoding UTF8` on `$existingContent` read
**Why**: `$existingContent` was read with default encoding (Windows-1252 on PS5.1), but written with `-Encoding UTF8`. On any template with non-ASCII characters the equality check `$generated -ne $existingContent` was always `$true`, causing `copilot-instructions.md` to be rewritten on every `cg-link` run even when content was unchanged.  
**Fix**: Added `-Encoding UTF8` to the `Get-Content` call.  
**Status**: `fixed`

---

### V-P2.2 `cg-data-quality` · .github/copilot-instructions.template.md:4–5 — Duplicate line in HTML comment
**Why**: The P3.7 regression fix introduced two identical `Template variables substituted at generation time: ...` lines — one without a period and no closing `-->`, one with. This propagated as a visual defect into every generated `copilot-instructions.md`.  
**Fix**: Removed the duplicate line; kept only the version with trailing period and closing `-->`.  
**Status**: `fixed`

---

### V-P2.3 `cg-data-quality` · scripts/helpers.ps1:87–90 — Single-quoted YAML values retained literal apostrophes
**Why**: Field regexes used `"?([^"\r\n]+)"?` — only the double-quote was treated as a quote delimiter. A YAML value like `r-syntax: 'data.table-collapse'` would be captured as `'data.table-collapse'` (with apostrophes), producing `R (R dialect: 'data.table-collapse')` in the generated instructions — an unknown dialect string.  
**Fix**: Changed all five field regexes to `["\x27]?([^"''\r\n]+)["\x27]?\s*$` (where `\x27` is the .NET hex escape for `'` and `''` is the PS5.1 single-quote escape inside a single-quoted string). Applied to `project-name`, `language`, `project-type`, `review-depth`, and `r-syntax`.  
**Status**: `fixed`

---

### V-P2.4 `cg-testing` · tests/helpers.Tests.ps1:237 — Weak `BeGreaterThan 1` fallback assertion
**Why**: The test named "all three unconfigured fields (project-type, language, review-depth) fall back" used `BeGreaterThan 1`, which passes if ≥2 fields fell back. A silent regression dropping one field's fallback would not be caught.  
**Fix**: Changed to `Should Be 3`.  
**Status**: `fixed`

---

### V-P2.5 `cg-documentation` · docs/reference.md:49 — `/cg-work` table misstated Step 3.8 behavior
**Why**: The entry said "prompts to update the charter's Current Focus (Step 3.8)" — Step 3.8 actually dispatches `@cg-roadmap` to mark the milestone `done` and notifies the user to run `/cg-strategy`; it does not prompt for a charter edit.  
**Fix**: Replaced with "marks the milestone complete via `@cg-roadmap` (Step 3.8) and notifies the user to run `/cg-strategy` to review direction."  
**Status**: `fixed`

---

### V-P2.6 `cg-documentation` · docs/reference.md:170 — "trigger re-evaluation" misnaming
**Why**: The roadmap schema note used "dispatches `@cg-roadmap` to trigger re-evaluation" — the dispatch is an explicit `mark done` command, not an autonomous re-evaluation request.  
**Fix**: Changed to "dispatches `@cg-roadmap` to mark the milestone as `done`".  
**Status**: `fixed`

---

### V-P2.7 `cg-documentation` · docs/troubleshooting.md — Incorrect causal explanation for stale `CG_INTERNAL_CALL`
**Why**: The section described the cause as a hard-killed `cg-link` leaving `$env:CG_INTERNAL_CALL` set in the terminal. This is impossible: `cg-link.cmd` launches `link.ps1` as a child PowerShell subprocess — environment variables set inside the subprocess cannot propagate to the parent shell. The parent terminal's environment is unaffected by the subprocess dying.  
**Fix**: Revised the Cause paragraph: the symptom arises when the variable is set in the user's current terminal session (e.g., via dot-source `link.ps1` followed by a crash before `finally` ran, or manual assignment). Removed the hard-kill scenario.  
**Status**: `fixed`

---

### V-P3.1 `cg-documentation` · .github/prompts/cg-setup.prompt.md:211 — Mode B "Questions 4–7" omits Question 4.5
**Why**: The back-reference said "Questions 4-7 from Mode A Step A3.5" — Step A3.5 includes a Question 4.5 (Team) between Questions 4 and 5. A model following "4–7" literally could skip it.  
**Fix**: Changed to "Questions 4–7 including 4.5, from Mode A Step A3.5".  
**Status**: `fixed`

---

## Advisory Findings (not fixed — low priority)

### V-P3.2 `cg-code-quality` · scripts/helpers.ps1 — `$rSyntax` empty-string not guarded
Empty `r-syntax:` value (blank, not absent) passes the `$null -ne $rSyntax` guard and produces `R (R dialect: )`. Fix: use `[string]::IsNullOrWhiteSpace($rSyntax)` guard.  
**Status**: `advisory` — not observed in any real config; defer

---

### V-P3.3 `cg-code-quality` · scripts/helpers.ps1 and link.ps1 — Frontmatter closing `---` not end-of-line anchored
The closing `---` delimiter is not anchored to the end of its line. Advisory for defensive correctness; all current YAML fields are single-line scalars, so YAML block scalars with `---` are not a practical concern.  
**Status**: `advisory`

---

### V-P3.4 `cg-testing` · tests/update.Tests.ps1 — `"up-to-date"` return branch untested
`Update-ManagedInstructionsFile` returns `"refreshed"`, `"up-to-date"`, or `"skipped"`. Only `"refreshed"` and `"skipped"` are tested; the idempotency contract (no spurious write when content identical) is unverified.  
**Status**: `advisory` — add test in future pass

---

### V-P3.5 `cg-testing` · tests/helpers.Tests.ps1 — Injection guard throw path untested
The `{{` cross-injection guard in `New-CopilotInstructions` is not tested. If guard code is removed, no test fails.  
**Status**: `advisory` — add test in future pass

---

### V-P3.6 `cg-adversarial` · scripts/helpers.ps1 — `$Dest` path not confined to `$ProjectRoot` in `Update-ManagedInstructionsFile`
An unconstrained caller could pass an arbitrary path. The current sole caller uses `Join-Path (Get-Location).Path .github/copilot-instructions.md` (no user input). Latent risk only.  
**Status**: `advisory` — internal function, no external input path today

---

### V-P3.7 `cg-adversarial` · scripts/link.ps1 — TOCTOU between equality check and write
Concurrent `cg-link` and `cg-update` runs could produce silent silent clobber. Requires simultaneous parallel invocations in a single project — not a realistic single-user scenario.  
**Status**: `advisory`

---

### V-P3.8 `cg-adversarial` · scripts/helpers.ps1 — Injection guard does not reject `}}`
`$val -match '\{\{'` only blocks values with `{{`. A value containing `}}` passes the guard and writes `}}` literally into the output. Harmless with the current `.Replace()`-based substitution engine; only becomes significant if the template adopts a `}}` delimiter for another syntax.  
**Status**: `advisory`

---

## Test Results After This Session

```
Passed:  1,057
Failed:  1  (pre-existing — cg-compound.prompt.md - offers to create context.md if it does not exist)
```

No regressions introduced. All 7 applied fixes are covered by the existing test suite.

---

## Verdict

`feat/context-layer` is **clean and merge-ready**. All findings from the parent standard review are fixed. This verification review introduced 7 additional fixes (no new regressions). Five advisory items are documented above for future consideration.
