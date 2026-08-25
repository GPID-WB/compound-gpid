---
date: 2026-05-20
title: "optim() returns Hessian of negative log-likelihood — must be positive-definite at solution"
category: "bugs"
language: "R"
tags: [structural-econometrics, MLE, Hessian, optim, convergence-guard, research-correctness, sign-convention]
root-cause: "optim() minimizes the objective. When minimizing the negative log-likelihood, the returned Hessian is of the negative LL. At a valid maximum the negative-LL Hessian is positive-definite — not negative-definite as prose incorrectly stated."
severity: "P0"
---

# optim() Hessian Sign Convention: Positive-Definite at Solution

## Problem

A structural econometrics skill document stated:

> "At a maximum, the Hessian of the log-likelihood must be **negative-definite**."

A convergence guard in the same document checked that the Hessian was **positive-definite**.
These two statements were in direct contradiction.

Researchers following the prose would reject valid MLE solutions (or accept saddle points),
producing wrong standard errors with no error message.

## Root Cause

`optim(fn = neg_ll, hessian = TRUE)` **minimizes** the objective function. When the objective
is the negative log-likelihood, `result$hessian` is the Hessian of the **negative** LL — not
the LL itself.

At a **maximum** of the log-likelihood (equivalently, a **minimum** of the negative LL):

| Object | Correct descriptor |
|--------|--------------------|
| Hessian of the log-likelihood | Negative-definite (all eigenvalues < 0) |
| Hessian of the **negative** log-likelihood (`result$hessian`) | **Positive-definite** (all eigenvalues > 0) |

The prose was written from the perspective of the raw log-likelihood; the code guard referenced
`result$hessian`, which is the *negative* LL Hessian. Both framings are valid — but mixing them
silently creates an impossible condition for researchers to reason about.

## Solution

Match the prose to the object `optim()` actually returns:

```r
result <- optim(par = theta_init, fn = neg_ll, hessian = TRUE, method = "BFGS")
stopifnot("MLE did not converge" = result$convergence == 0)

# result$hessian is the Hessian of the NEGATIVE log-likelihood (the function minimized).
# At a valid maximum it must be positive-definite (all eigenvalues > 0).
H <- result$hessian
stopifnot("Hessian not positive-definite at solution" = all(eigen(H)$values > 0))

se <- sqrt(diag(solve(H)))
```

Prose template:

> "The Hessian returned by `optim(hessian=TRUE)` is the Hessian of the **negative**
> log-likelihood (the function minimized). At a valid maximum this must be
> **positive-definite** (all eigenvalues > 0). The covariance matrix is `solve(H)`."

## Prevention

- When documenting MLE, always specify *which* Hessian you are describing. Use one of:
  - "Hessian of the log-likelihood at maximum: **negative**-definite"
  - "Hessian of the negative log-likelihood at minimum — what `optim()` returns: **positive**-definite"
- A convergence guard and its surrounding prose must describe the same object.
- Skill documents that contain both prose descriptions and code guards should have a test that
  the prose uses the same sign word ("positive-definite") as the guard's condition (`> 0`).

## Related

- `.cg-docs/solutions/bugs/2026-05-20-bellman-convergence-guard-missing-asymmetric-with-mle.md` — analogous convergence guard gap in dynamic programming section
- `.github/skills/cr-skill-structural-econometrics/SKILL.md` — MLE convergence guard (fixed 2026-05-20)
