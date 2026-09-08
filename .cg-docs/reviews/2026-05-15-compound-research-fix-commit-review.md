---
date: 2026-05-15
branch: compound-research
commit: 73e9c62
scope: fix(compound-research): apply phase 4 thorough review findings
depth: standard
agents:
  - cg-code-quality
  - cg-testing
  - cg-documentation
  - cg-reproducibility
  - cg-architecture
  - cg-version-control
  - cg-data-quality
  - cg-performance
total_findings: 27
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
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
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
---

# Review: `73e9c62` — Phase 4 Fix Commit

**Date**: 2026-05-15  
**Branch**: `compound-research`  
**Commit**: `73e9c62` — fix(compound-research): apply phase 4 thorough review findings  
**Depth**: standard (8 agents)  
**Note**: Documentation agent returned pre-fix false positives (read the review report rather than file state); all verified as already fixed. All 27 findings below are confirmed genuine.

---

## P0 — BLOCKING

### [P0.1] [cg-data-quality] `cr-skill-structural-econometrics/SKILL.md:237` — Hessian sign convention contradicts code guard

**File**: `.github/skills/cr-skill-structural-econometrics/SKILL.md`, line 237  
**Issue**: Prose diagnostic says *"Verify Hessian is negative-definite at solution (all eigenvalues < 0)"*. But `optim(hessian = TRUE)` returns the Hessian of the **negative** log-likelihood (the function being minimized); at the MLE this must be **positive-definite** (all eigenvalues > 0). The code guard on lines 218–221 is correct (`if (any(eigenvalues <= 0)) stop("Hessian not positive-definite...")`). The prose directly contradicts the guard.  
**Impact**: A researcher following the prose would declare a valid solution a failure, or accept a saddle point as converged. Wrong SEs propagate throughout the structural model.  
**Fix**: Change line 237 to:
> *"Verify Hessian of the **negative** log-likelihood is positive-definite at solution (all eigenvalues > 0)"* *(equivalently, Hessian of the log-likelihood is negative-definite — but `optim` returns the former)*

---

## P1 — CRITICAL

### [P1.1] [cg-testing] `tests/cr-prompts.Tests.ps1` — Missing test: cr-mathematical-verification 20-file pagination limit

**Issue**: `cr-mathematical-verification.agent.md` line 46 added a "File count limit: If more than 20 derivation files are found…" guard. No test verifies this safety feature exists.  
**Risk**: Future refactor silently removes the limit → context overflow in production.  
**Fix**:
```powershell
It "contains 20-file pagination limit" {
    ($content -match '(?i)more than 20.*derivation|File count limit') | Should -Be $true
}
```

### [P1.2] [cg-testing] `tests/cr-prompts.Tests.ps1` — Missing test: cr-mathematical-verification prompt injection guard

**Issue**: `cr-mathematical-verification.agent.md` added an injection guard detecting `SYSTEM`, `OVERRIDE`, `ignore prior`, imperatives. No test covers this P0-level safety gate.  
**Fix**:
```powershell
It "contains prompt injection guard with SYSTEM/OVERRIDE detection" {
    ($content -match '(?i)prompt injection|SYSTEM|OVERRIDE') | Should -Be $true
}
It "contains structural guard preventing prose relay from derivation files" {
    ($content -match '(?i)structural guard|never relay prose') | Should -Be $true
}
```

### [P1.3] [cg-testing] `tests/cr-prompts.Tests.ps1` — Missing test: cr-mathematical-verification code file path validation

**Issue**: Step 2 of `cr-mathematical-verification.agent.md` now flags P1 when variable mapping tables reference files NOT in the review set. No test covers this check.  
**Fix**:
```powershell
It "includes code file path validation against review set" {
    ($content -match '(?i)code file path validation|not among the files under review') | Should -Be $true
}
```

### [P1.4] [cg-testing] `tests/cr-prompts.Tests.ps1` — Missing test: cr-research-integrity empty-file guard

**Issue**: `cr-research-integrity.agent.md` protocol section added "if the code file is zero-byte or contains only whitespace or comments… do not run Checks 1–7". No test covers this guard.  
**Fix**:
```powershell
It "contains empty-file guard at protocol start" {
    ($content -match '(?i)zero-byte|empty file.*research integrity check skipped') | Should -Be $true
}
```

### [P1.5] [cg-architecture] `cr-econometric-reasoning.agent.md:103` — Contradictory P0 deferral instructions

**File**: `.github/agents/cr-econometric-reasoning.agent.md`  
**Issue**: Line 103–104 says *"If n/p < 10, do NOT emit a P0 finding here — `@cr-research-integrity` Check 6 is authoritative"* (with a partial escape "only if `@cr-research-integrity` is not in scope"). Lines 125–130 say *"P0 deferral policy: Do NOT defer P0 findings… emit it directly… regardless of whether `@cr-research-integrity` is dispatched."* These are directly opposed. When `@cr-research-integrity` is absent, Step 4a's carve-out wins in sequential reading, and the asymptotic P0 is silently dropped.  
**Fix**: Remove the carve-out from Step 4a. Rewrite to match the deferral policy: emit the P0 directly with a cross-reference note to Check 6.

### [P1.6] [cg-architecture] `cr-skill-structural-econometrics/SKILL.md:10` — False dispatch path in frontmatter description

**File**: `.github/skills/cr-skill-structural-econometrics/SKILL.md`  
**Issue**: Frontmatter description says *"Loaded by `@cr-econometric-reasoning` and `/cr-work` for Theory/Modeling and Implementation tasks."* `cr-work.prompt.md` Step 0 loads only `cr-skill-research-workflow`, `cr-skill-research-integrity`, and conditionally `cr-skill-mathematical-derivation`. It never loads `cr-skill-structural-econometrics`. A researcher running `/cr-work` on a structural model has no structural econometrics reference available.  
**Fix**: Either (a) add `cr-skill-structural-econometrics` to `cr-work.prompt.md` Step 0 for Theory/Modeling and Implementation tasks, or (b) remove `/cr-work` from the description until this is implemented.

### [P1.7] [cg-data-quality] `cr-skill-research-eda/SKILL.md:234` — Welfare non-negativity guard gives misleading error for NAs

**File**: `.github/skills/cr-skill-research-eda/SKILL.md`, line 234  
**Issue**: `stopifnot("Welfare variable contains zero or negative values" = all(df$welfare > 0))` — when `df$welfare` contains `NA`, `all(NA > 0)` is `NA`, and `stopifnot` throws `"is not TRUE"`. The error message blames zeros/negatives when the cause is NAs (structurally common in GPID welfare data).  
**Fix**:
```r
stopifnot("Welfare variable contains NA values" = !anyNA(df$welfare))
stopifnot("Welfare variable contains zero or negative values" = all(df$welfare > 0))
```

### [P1.8] [cg-data-quality] `cr-skill-structural-econometrics/SKILL.md:109` — Bellman convergence has no code guard (asymmetric with MLE)

**File**: `.github/skills/cr-skill-structural-econometrics/SKILL.md`, lines 109–113  
**Issue**: The NFXP Bellman iteration convergence diagnostics are prose-only. Section 4 (MLE) provides a hard `stopifnot("Optimizer did not converge" = result$convergence == 0)` guard. When the inner Bellman loop fails to converge and the outer MLE proceeds anyway, it optimizes over invalid value functions — yielding structurally wrong parameter estimates.  
**Fix**:
```r
if (max(abs(V_new - V)) >= tol)
  stop("Bellman iteration did not converge after max iterations — ",
       "check β < 1, transition matrix rows sum to 1, and grid resolution.")
```

---

## P2 — IMPORTANT

### [P2.1] [cg-testing] `tests/cr-prompts.Tests.ps1` — Missing test: cr-econometric-reasoning cr-skill-research-workflow load

**Fix**:
```powershell
It "loads cr-skill-research-workflow for task context" {
    ($content -match '(?is)load.*cr-skill-research-workflow') | Should -Be $true
}
```

### [P2.2] [cg-testing] `tests/cr-prompts.Tests.ps1` — Missing test: cr-econometric-reasoning P0 deferral policy

**Fix**:
```powershell
It "contains P0 deferral policy (do NOT defer P0 to @cr-research-integrity)" {
    ($content -match '(?i)P0 deferral policy|do not defer P0') | Should -Be $true
}
```

### [P2.3] [cg-architecture] `cr-research-integrity.agent.md:105` + `cr-identification-audit.agent.md` — Duplicate P0 emission for identification-theater findings

**Issue**: `@cr-research-integrity` Check 4 and `@cr-identification-audit` both independently scan for missing IV/RDD/DiD diagnostics and emit P0 for the same code lines. A single missing McCrary test generates two P0 entries in the collected findings with different agent tags but pointing to the same line, corrupting `/cg-fix-triage` tracking.  
**Fix**: Add a deduplication step to `cr-review.prompt.md` Step 4 that merges findings with the same file:line and diagnostic class, OR scope Check 4 to lightweight detection only (claim presence without diagnostic) and delegate full per-strategy diagnostics to `@cr-identification-audit`.

### [P2.4] [cg-architecture] `cr-mathematical-verification.agent.md` — Missing `cr-skill-research-workflow` load (inconsistent with rest of agent set)

**Issue**: `@cr-research-integrity`, `@cr-identification-audit`, and `@cr-econometric-reasoning` all load `cr-skill-research-workflow` first. `@cr-mathematical-verification` loads `cr-skill-research-integrity`, `cr-skill-symbolic-verification`, and `cr-skill-mathematical-derivation` but not `cr-skill-research-workflow`. The task taxonomy (8 types, P0–P3 system, `.cg-docs/research/` layout) is missing.  
**Fix**: Add as first load instruction: *"Load `cr-skill-research-workflow` for task taxonomy context before beginning any review."*

### [P2.5] [cg-architecture] `cr-review.prompt.md` — `cr-skill-research-eda` has no dispatch path in orchestrator

**Issue**: `cr-skill-research-eda` description declares it is "Loaded for EDA and Specification Analysis tasks" but no EDA-specific agent exists yet (Phase 5). EDA tasks route to `@cg-performance` + `@cg-data-quality` only. The gap is invisible in the dispatch table.  
**Fix**: Add a placeholder comment in the EDA dispatch row: `# @cr-eda-reviewer — Phase 5 (not yet dispatched)` so the absence is explicit during reviews.

### [P2.6] [cg-data-quality] `cr-skill-research-eda/SKILL.md:168` — `collapse` `na.rm` default warning buried after design-based SE note

**Issue**: The `na.rm` default note documents that `set_collapse(na.rm = FALSE)` silently propagates NAs through all weighted statistics — corrupting **point estimates**. It appears after the design-based SE note which addresses only inference. Readers may stop before reaching the more critical warning.  
**Fix**: Move the `na.rm` default blockquote before the design-based SE blockquote.

### [P2.7] [cg-data-quality] `cr-skill-structural-econometrics/SKILL.md:52` — PPP vintage warning siloed to Section 1 only

**Issue**: PPP vintage consistency callout only appears in Section 1 (Discrete Choice). Welfare/income aggregates appear equally as inputs to MLE (Section 4) and GMM (Section 5). Agents loading the skill for MLE or GMM work miss the vintage warning entirely.  
**Fix**: Add a `> **PPP vintage consistency**` blockquote in Section 4 (MLE) and Section 5 (GMM), mirroring the existing wording.

### [P2.8] [cg-data-quality] `cr-skill-identification-strategies/SKILL.md:263` — MatchIt version pin is comment-only; no runtime guard

**Issue**: `# Requires MatchIt >= 4.0` is prose only. The v3→v4 API change is a breaking change (not a deprecation warning); v3 code can run on v4 with wrong results in some configurations.  
**Fix**:
```r
stopifnot("MatchIt >= 4.0.0 required (v3 → v4 has breaking API changes)" =
  packageVersion("MatchIt") >= "4.0.0")
```

### [P2.9] [cg-performance] `tests/cr-prompts.Tests.ps1:1098` — `math.instructions.md` read 4× in one Context

**Fix**: Hoist `$content = Get-Content $path -Raw -Encoding UTF8` and `$fm = Get-Frontmatter -FilePath $path` to Context scope.

### [P2.10] [cg-performance] `tests/cr-prompts.Tests.ps1:1075` — `latex.instructions.md` read 3× in one Context

**Fix**: Hoist both `$fm` and `$content` reads to Context scope.

### [P2.11] [cg-performance] `tests/cr-prompts.Tests.ps1:1127` — `cr-mathematical-verification.agent.md` read twice in skill-load assertions

**Fix**: Hoist `$mathVerify = Get-Content ... -Raw` to Describe scope.

### [P2.12] [cg-performance] `tests/cr-prompts.Tests.ps1:597` — `$content -split "`n"` repeated 4× in Phase 3 wiring

**Fix**: Add `$lines = $content -split "`n"` once after the `$content` hoist; remove per-`It` assignments.

---

## P3 — ADVISORY

### [P3.1] [cg-architecture] `cr-econometric-reasoning.agent.md:162` — Output format note implies agents can dispatch agents

**Issue**: Line 162: *"P0 findings triggered by underlying research-integrity violations… should also be reported via `@cr-research-integrity`"* implies this agent can instruct another agent to report — impossible. Contradicts the P0 deferral policy's "emit it directly" instruction.  
**Fix**: Replace with: *"Note: P0 findings emitted here will also be detectable by `@cr-research-integrity` — note the cross-reference in your finding using 'Cross-reference: `@cr-research-integrity` Check {N}'. Do not suppress the finding here."*

### [P3.2] [cg-data-quality] `cr-skill-research-eda/SKILL.md:234` — Welfare guard hardcodes `df$welfare` column name

**Issue**: `all(df$welfare > 0)` evaluates `all(NULL > 0)` → `TRUE` if the column doesn't exist, passing vacuously. GPID welfare variables use various names (`welfare_ppp`, `welfare_ppp17`, `pcexp`).  
**Fix**: Add column existence check:
```r
stopifnot("Column 'welfare' not found — adapt guard to actual welfare variable name" =
  "welfare" %in% names(df))
```
Or add inline comment: `# Adapt 'welfare' to actual column name (welfare_ppp17, pcexp, etc.)`

### [P3.3] [cg-performance] `tests/cr-prompts.Tests.ps1:45` — `Get-Frontmatter` called 3× per file in structural checks loop

**Fix**: Hoist `$fm = Get-Frontmatter -FilePath $path` to top of each Context block.

### [P3.4] [cg-performance] `tests/cr-prompts.Tests.ps1:393` — `Get-Frontmatter` called 5× per file in agent checks loop

**Fix**: Hoist `$fm = Get-Frontmatter -FilePath $path` to Context scope.

### [P3.5] [cg-performance] `tests/cr-prompts.Tests.ps1:824` — `Get-Frontmatter` called 3× per skill in Phase 4 skills loop

**Fix**: Hoist `$fm = Get-Frontmatter -FilePath $path` to Context scope.

### [P3.6] [cg-performance] `tests/cr-prompts.Tests.ps1:681` — Secondary file read inside `It` block in dispatch journey

**Fix**: Hoist `$cgReviewContent = Get-Content $cgReviewPath -Raw` to Describe scope alongside `$content`.

---

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| P0 | 1 | open |
| P1 | 8 | open |
| P2 | 12 | open |
| P3 | 6 | open |
| **Total** | **27** | |

**Agents with no findings**: cg-code-quality, cg-reproducibility, cg-version-control  
**False positives discarded**: cg-documentation agent returned 10 pre-fix findings (already resolved in `73e9c62` — agent read the review report rather than verifying file state)  
**Recommended next step**: `/cg-fix-triage` — address P0.1 and P1.5 immediately (correctness), then P1.1–P1.4 (test coverage), then P1.6–P1.8 (data quality), then P2.1–P2.12.
