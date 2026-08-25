---
name: cr-skill-symbolic-verification
module: research
description: "Symbolic and numerical verification of mathematical derivations
  against code implementation. Covers SymPy gradient/Hessian verification,
  moment condition checks, second-order condition verification, code-derivation
  mapping audits, and numerical verification harnesses. Loaded by
  @cr-mathematical-verification for Theory/Modeling and Implementation tasks."
---

# Symbolic Verification

Reference skill for verifying that code correctly implements mathematical
derivations. Used by `@cr-mathematical-verification` to catch code-math
mismatches (P0 error class per `cr-skill-research-integrity`).

---

## 1. SymPy Gradient Verification

**When to use**: Verify that the analytical gradient implemented in code
matches the symbolic derivative of the objective function.

```python
import sympy as sp

# --- Define symbolic objective ---
beta, sigma2, y, x = sp.symbols('beta sigma2 y x', real=True)

# Log-likelihood of normal linear model (per observation)
log_lik = -sp.Rational(1, 2) * sp.log(2 * sp.pi * sigma2) \
          - (y - beta * x)**2 / (2 * sigma2)

# --- Symbolic gradient ---
grad_beta   = sp.diff(log_lik, beta)    # x*(y - beta*x)/sigma2
grad_sigma2 = sp.diff(log_lik, sigma2)  # -1/(2*sigma2) + (y-beta*x)^2/(2*sigma2^2)

print("∂L/∂β  =", sp.simplify(grad_beta))
print("∂L/∂σ² =", sp.simplify(grad_sigma2))
```

**Verification workflow**:
1. Write the objective symbolically in SymPy using notation from the derivation file
2. Compute symbolic derivative with `sp.diff()`
3. Simplify with `sp.simplify()` or `sp.factor()`
4. Compare expression to the score function in code
5. If they match symbolically → document in variable mapping table
6. If they differ → P0 flag (code-math mismatch); investigate before proceeding

**Gradient check for vectorized objectives**:
```python
import numpy as np

def numerical_gradient(fn, theta, eps=1e-6):
    """Finite-difference gradient check."""
    n = len(theta)
    grad = np.zeros(n)
    e    = np.zeros(n)     # pre-allocate once; reset each iteration
    for k in range(n):
        e[k] = eps
        grad[k] = (fn(theta + e) - fn(theta - e)) / (2 * eps)
        e[k] = 0.0         # reset for next iteration
    return grad

# Compare analytical gradient to numerical gradient at test point
theta_test = np.array([1.0, 0.5])
np.testing.assert_allclose(analytical_gradient(theta_test),
                            numerical_gradient(objective, theta_test),
                            rtol=1e-5, err_msg="Gradient mismatch — P0")
```

---

## 2. Hessian Verification

**When to use**: Verify that the information matrix or Hessian used for standard
errors matches the second derivative of the objective.

```python
# Symbolic Hessian
H = sp.hessian(log_lik, [beta, sigma2])
print("Hessian =", sp.simplify(H))

# Verify negative-definiteness by summing over observations
# (single-observation Hessian is not necessarily negative-definite)
H_numerical = sp.lambdify([beta, sigma2, y, x], H)

# Evaluate at multiple data points and sum
obs = [(2.0, 1.0), (3.0, 1.5), (0.5, 0.8), (1.0, 0.5)]
H_sample = sum(H_numerical(beta=1.2, sigma2=0.8, y=yi, x=xi)
               for yi, xi in obs)

eigenvalues = np.linalg.eigvalsh(H_sample)
assert all(eigenvalues < 0), "Hessian not negative-definite at MLE — check SOC"
```

**Information matrix equality check** (under correct specification):
```python
# H(θ) should equal -S(θ) where S is the outer product of scores
# If H ≠ -S: model is misspecified → use sandwich SE, not -H^{-1}
import numpy as np

def information_matrix_equality_test(scores, hessians):
    """Test Fisher information matrix equality."""
    S = np.mean([s @ s.T for s in scores], axis=0)
    H = np.mean(hessians, axis=0)
    max_discrepancy = np.max(np.abs(S + H))
    return max_discrepancy  # should be < 1e-6 if model is correctly specified
```

---

## 3. Moment Condition Verification

**When to use**: Verify that GMM moment conditions $E[g(y, x, \theta)] = 0$
are correctly implemented in code.

```python
import sympy as sp

# Symbolic moment condition (e.g., IV: Z'(y - X*beta) = 0)
beta, y, x, z = sp.symbols('beta y x z', real=True)
moment = z * (y - beta * x)

# Derivative w.r.t. theta (Jacobian G = E[∂g/∂θ'])
G_sym = sp.diff(moment, beta)  # -z*x
print("G(β) =", G_sym)

# Numerical check: evaluate moments at true theta, verify near zero
def verify_moment_conditions(theta_true, data, moment_fn, tol=1e-10):
    """Verify moments evaluate near zero at true parameters."""
    moments_at_truth = moment_fn(theta_true, data)
    mean_moments = np.mean(moments_at_truth, axis=0)
    max_abs = np.max(np.abs(mean_moments))
    if max_abs > tol:
        raise AssertionError(
            f"Moment conditions not satisfied at true θ: max|g| = {max_abs:.2e}. "
            "Check moment function implementation."
        )
```

---

## 4. SOC Verification (Second-Order Condition)

**When to use**: Verify that the solution to FOCs is a maximum (for maximization)
or minimum (for minimization), not a saddle point.

```python
# Symbolic SOC check
soc = sp.diff(log_lik, beta, 2)  # ∂²L/∂β² should be < 0
print("SOC =", sp.simplify(soc))  # should be -x^2/sigma2 < 0 ✓

# Global concavity check (for linear models)
# Hessian is negative-definite if all eigenvalues are negative
# For normal log-likelihood: Hessian is -X'X/σ² (negative semi-definite)
# Positive-definite if X has full rank

# Numerical SOC at estimated θ̂
def check_soc_at_estimate(hessian_fn, theta_hat):
    H = hessian_fn(theta_hat)
    eigenvalues = np.linalg.eigvalsh(H)
    if not all(eigenvalues < 0):
        raise ValueError(
            f"SOC FAIL: Hessian not negative-definite at θ̂. "
            f"Eigenvalues: {eigenvalues}. "
            "Solution may be saddle point or local minimum."
        )
    return eigenvalues
```

---

## 5. Code-Derivation Mapping Audit

**When to use**: Systematically audit a code file against a derivation file,
checking that every equation in the derivation has a corresponding line in
the code.

**Audit checklist**:

```markdown
## Code-Derivation Audit Checklist

**Derivation file**: `.cg-docs/research/derivations/wage-mle.md`
**Code file**: `estimation.R` (line references from git blame)

| Eq. # | Math Expression | Code Line | Code Expression | Match? | Notes |
|-------|----------------|-----------|-----------------|--------|-------|
| (1)   | L(θ) = Σ log f | 45        | `ll <- sum(log(dnorm(...)))` | ✓ | |
| (2)   | ∂L/∂β = X'(y-Xβ)/σ² | 67 | `score_beta <- t(X) %*% (y - X %*% beta) / sigma2` | ✓ | |
| (3)   | ∂L/∂σ² = -n/(2σ²) + SSR/(2σ⁴) | 72 | `score_sigma2 <- -n/(2*sigma2) + ssr/(2*sigma2^2)` | ✓ | |
| (4)   | V(β̂) = σ²(X'X)⁻¹ | 89 | `vcov <- sigma2_hat * solve(t(X) %*% X)` | ✓ | |

**Sign conventions**: Code maximizes LL; optimizer minimizes -LL → sign flip at line 50
**Reparametrizations**: σ² stored as log(σ) in optimizer; back-transformed at line 88
```

**Common discrepancies to flag**:
- Sign error: code minimizes objective that should be maximized (negation missing)
- Transposition: code uses `X %*% beta` where derivation uses `beta' X'`
- Index shift: code loops from 0 where derivation starts from 1
- Reparametrization: code works in log-scale but derivation is in level
- Constant dropped: derivation includes a normalizing constant that code omits

---

## 6. Numerical Verification Harness

**When to use**: Run a comprehensive numerical verification of a structural
estimation routine against known analytical results (e.g., linear model with
analytical OLS formula).

```r
# R — verification harness for MLE implementation
verify_mle_implementation <- function(estimation_fn, n = 1000,
                                       seed = 42, tol = 1e-4) {
  set.seed(seed)

  # 1. Generate data from known DGP
  beta_true <- c(1.5, -0.8)
  sigma_true <- 1.2
  X <- cbind(1, rnorm(n))
  y <- X %*% beta_true + rnorm(n, sd = sigma_true)

  # 2. Run MLE implementation under test
  result <- estimation_fn(y, X)

  # 3. Compare to analytical MLE (true for normal linear model)
  beta_ols <- solve(t(X) %*% X) %*% t(X) %*% y
  sigma_mle <- sqrt(sum((y - X %*% beta_ols)^2) / n)  # MLE uses n, not n-2

  # 4. Assert results match within tolerance
  stopifnot(
    "Beta estimate mismatch" = max(abs(result$beta - beta_ols)) < tol,
    "Sigma estimate mismatch" = abs(result$sigma - sigma_mle) < tol
  )

  message("Verification PASSED: MLE matches OLS benchmark")
  invisible(TRUE)
}
```

**Python equivalent**:
```python
def verify_mle_implementation(estimation_fn, n=1000, seed=42, tol=1e-4):
    rng = np.random.default_rng(seed)
    beta_true = np.array([1.5, -0.8])
    X = np.column_stack([np.ones(n), rng.standard_normal(n)])
    y = X @ beta_true + rng.standard_normal(n)

    result = estimation_fn(y, X)
    beta_ols = np.linalg.lstsq(X, y, rcond=None)[0]

    np.testing.assert_allclose(result["beta"], beta_ols, rtol=tol,
                                err_msg="MLE beta does not match OLS benchmark")
    print("Verification PASSED")
```

---

## 7. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| No gradient check | Code may silently use wrong formula | Always compare analytical ↔ numerical gradient |
| Verifying at only one test point | Local agreement ≠ global correctness | Test at multiple parameter values and edge cases |
| Comparing floats with `==` | Floating-point equality fails | Use `np.testing.assert_allclose(rtol=1e-5)` or R's `all.equal()` |
| Skipping SOC check | Local maximum may be saddle point | Check Hessian eigenvalues at solution |
| Auditing code against prose, not equations | Prose may be imprecise | Always audit against numbered LaTeX equations |
| Reporting "matches" without tolerance | Ambiguous; reviewer cannot verify | State tolerance explicitly: "matches to rtol=1e-5" |
| Not documenting sign conventions | Common source of mismatch | Add sign convention comment at top of estimation file |
