# `/cg-review mode:verify` — Verification Passes

> **Quick summary**: After applying `/cg-fix-triage` results, run `/cg-review mode:verify` to confirm your fixes converged. It re-runs a `light` review, suppresses the P2/P3 findings you already fixed, and always reports any new P0/P1 or cross-file breakage.

---

## Why This Exists

A standard `/cg-review` → `/cg-fix-triage` cycle can loop indefinitely:

1. Review finds 20 findings.
2. Fix-triage fixes all 20.
3. You run another standard review.
4. The new review finds 12 findings — some are genuinely new, but most are just the same P2/P3 issues re-phrased because the code was restructured during fixing.
5. You fix those 12. Repeat.

`mode:verify` breaks this loop. It knows which findings were explicitly marked `fixed` in the prior review frontmatter. It suppresses P2/P3 re-findings that land on the same scope as those fixed findings. If nothing new surfaces, the cycle terminates. If a real new issue appears — including any P0/P1 at any scope — it is always reported.

---

## When to Use

- **After any `/cg-fix-triage` session** — run `mode:verify` to confirm fixes converged before committing or merging.
- **When P2/P3 suppression is needed** — if fix-triage marked findings as `fixed` in the review frontmatter, `mode:verify` uses those as suppression anchors so re-phrased re-findings don't restart the loop.
- **Between batched fix-triage runs** — for large reports, use `mode:verify` after each priority batch to check P0/P1 convergence before continuing.

## When NOT to Use

- **As a substitute for `/cg-review light`** — if there is no prior review with `fixed` entries in its `findings:` frontmatter, suppression has nothing to anchor to. The result is equivalent to a standard light review with no loop-breaking benefit.
- **When fix-triage touched statistical functions, pipelines, or architecture** — `mode:verify` runs only `@cg-code-quality` and `@cg-testing`. Use `/cg-review standard` or `/cg-review thorough` before the final merge.
- **As the only review before merge** — `mode:verify` is a convergence check, not a comprehensive quality gate. Always run a full review at some point in the cycle.

---

## Invocation

```
/cg-review mode:verify
```

This is the only required argument. Depth is always forced to `light` regardless of what `compound-gpid.local.md` says or any depth argument you provide.

```
# These all behave identically — depth arg is ignored when mode:verify is active:
/cg-review mode:verify
/cg-review thorough mode:verify
/cg-review light mode:verify
```

---

## What Happens Step by Step

### 1. Locate the prior review

`mode:verify` scans `.cg-docs/reviews/` for the most recent file whose name:
- ends in `-review.md`
- does **not** end in `-verify-review.md` (own output is excluded — see [Anti-loop protection](#anti-loop-protection))
- has a `findings:` frontmatter map with at least one `fixed` entry

If no such file is found, `mode:verify` warns: *"No prior review with fixed findings found — running a clean `light` review without suppression."* It then runs a normal light review.

### 2. Build the suppression context

From the prior review's `findings:` map, it collects every entry marked `fixed`. These are the IDs (e.g., `P2.3`, `P3.1`) whose scope is eligible for suppression in the new pass.

### 3. Dispatch light agents

`mode:verify` always dispatches exactly two agents: `@cg-code-quality` and `@cg-testing`. No other agents run, regardless of auto-escalation rules or content triggers. Language-specific skills (R, Python, Stata) still apply if any in-scope files use those languages.

### 4. Apply the suppression policy

| Finding priority | Suppression | Condition |
|---|---|---|
| **P0** | Never suppressed | Always reported |
| **P1** | Never suppressed | Always reported |
| **P2** | Suppressed if... | ...the finding targets a function or block whose refactoring was explicitly listed as `fixed` in the prior review's `findings:` map |
| **P3** | Suppressed if... | ...same condition as P2 |
| **Cross-file breakage** | Never suppressed | Always reported regardless of priority |

> **The suppression anchor is the `findings:` map, not agent inference.** A P2 is suppressed only if its target scope appears in an explicitly `fixed` entry — not because the agent thinks the code "looks like it was changed recently" or "is probably a fix consequence". When in doubt, the agent reports.

### 5. Save the verify-review file

The output is saved as:

```
.cg-docs/reviews/<prior-review-stem>-verify-review.md
```

For example, if the prior review is `2026-04-23-my-feature-review.md`, the verify-review is `2026-04-23-my-feature-verify-review.md`.

If a verify-review file with that name already exists (a second consecutive verify pass), the counter increments: `...-verify-review-2.md`, etc.

**Frontmatter written**:

```yaml
---
date: YYYY-MM-DD
depth: light
parent-review: .cg-docs/reviews/<prior-review-stem>-review.md
type: verification
findings:
  <new finding IDs>: open   # any genuine new issues
---
```

---

## Reading the Results

### Clean convergence

```
Findings: 0 (P0: 0, P1: 0, P2: 0, P3: 0)
✅ Passed — all prior findings resolved, no new issues detected.
```

This is the expected outcome after a thorough fix-triage pass. The cycle is complete — the code is ready to merge.

### Partial convergence

```
Findings: 2 (P0: 0, P1: 0, P2: 1, P3: 1)
```

Two new issues were found that are **not** suppressed by the prior `findings:` map — they are genuinely new, not re-findings from the same scope. Fix these with `/cg-fix-triage`, then run another `mode:verify` pass.

### Regression detected

```
Findings: 1 (P0: 0, P1: 1, P2: 0, P3: 0)
```

A P1 was introduced — possibly by the fix work itself. This is always reported regardless of suppression. Fix immediately with `/cg-fix-triage P1`, then verify again.

---

## Anti-Loop Protection

`mode:verify` writes output to the same directory it reads from. Without a guard, the second `mode:verify` pass would find the first verify-review (which has `findings: P3.1: fixed` in its frontmatter) and use it as the parent — suppressing nothing meaningful and writing over itself.

The guard: **files ending in `-verify-review.md` are excluded from the input scan.** Only canonical `-review.md` files (written by standard `/cg-review` passes) can be parents. Verify passes can never chain from each other.

---

## Mutual Exclusivity with `mode:autofix`

`mode:autofix` and `mode:verify` are mutually exclusive. If both are passed, `mode:verify` wins:

```
/cg-review mode:autofix mode:verify   →   mode:verify runs, mode:autofix is ignored
```

When both are passed, Copilot warns: *"Cannot combine `mode:autofix` and `mode:verify` — using `mode:verify`."*

This is intentional — a verify pass is a read-only quality check. Applying mechanical fixes during a verification pass would change the code under inspection, making the verify result unreliable.

---

## Caveats and Limitations

### What suppression covers

Suppression applies **only to P2/P3 findings on the explicit scope of fixed findings**. It does not suppress:

- Any P0 or P1, ever
- Cross-file breakage (e.g., a function signature changed and a caller was not updated)
- New findings on code that was not touched by the fix work
- Findings on code that is adjacent to (but not explicitly within) a fixed scope

### What it does not check

`mode:verify` runs `@cg-code-quality` and `@cg-testing` only. It does not run:

- `@cg-architecture` — structural changes introduced during fixing are not reviewed
- `@cg-data-quality` / `@cg-reproducibility` — statistical correctness is not re-checked
- `@cg-adversarial` — edge cases are not stress-tested
- `@cg-version-control` — commit hygiene is not reviewed

If the fix-triage session touched statistical functions, pipeline files, or architecture — run a full `/cg-review standard` or `/cg-review thorough` after convergence before merging.

### It does not replace a full review

`mode:verify` is a **convergence check**, not a comprehensive quality gate. Its job is to confirm that fix-triage didn't introduce regressions and that the original findings are resolved. For any non-trivial change, a full review should still precede the final merge.

### Legacy review files

Pre-v0.4.3 review files lack a `findings:` frontmatter map. `mode:verify` will skip them (no `fixed` entries to anchor suppression) and proceed with a clean light review. Use `/cg-fix-triage --migrate` to backfill the `findings:` map on legacy files if needed.

---

## Typical Workflow

```
/cg-review standard          # Full review, saves report with findings
/cg-fix-triage               # Apply all findings
/cg-review mode:verify       # Confirm fixes converged — suppress expected re-findings
```

For large reports, batch the fix work:

```
/cg-review standard          # Full review
/cg-fix-triage P0 P1         # Fix blocking and critical first
/cg-review mode:verify       # Verify P0/P1 fixes — should be clean; P2/P3 still open
/cg-fix-triage P2            # Fix important findings
/cg-fix-triage P3            # Fix minor findings
/cg-review mode:verify       # Final convergence check
```

---

## Output File Naming

| Scenario | Output filename |
|---|---|
| First verify pass | `<prior-stem>-verify-review.md` |
| Second verify pass (when `-verify-review.md` already exists) | `<prior-stem>-verify-review-2.md` |
| Third | `<prior-stem>-verify-review-3.md` |

All verify-review files are stored in `.cg-docs/reviews/` alongside standard review files. They are excluded from future verify-mode input scans (anti-loop protection).

---

## See Also

- [Workflow](workflow.md) — full review + fix-triage loop explanation  
- [Reference](reference.md) — command index and invocation options  
- [2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md](../.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md) — design rationale for the suppression policy  
- [2026-04-24-anti-loop-exclusion-in-iterative-review-modes.md](../.cg-docs/solutions/testing-patterns/2026-04-24-anti-loop-exclusion-in-iterative-review-modes.md) — design rationale for the anti-loop exclusion rule
