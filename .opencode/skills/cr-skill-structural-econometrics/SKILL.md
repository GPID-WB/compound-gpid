---
name: cr-skill-structural-econometrics
module: research
description: "Structural econometric methods for economics research. Covers
  discrete choice (logit, probit, nested logit, mixed logit, BLP), dynamic
  programming (Rust, Hotz-Miller CCP), simulation-based estimation (MSM, SMM,
  indirect inference), MLE for structural models, GMM (moment selection,
  overidentification, Hansen J-test), standard error variants (sandwich, bootstrap,
  delta method), identification at infinity, exclusion restrictions, and parametric
  vs semi-parametric trade-offs. Loaded by @cr-econometric-reasoning
  for Theory/Modeling tasks."
---

# Structural Econometrics

Reference skill for structural econometric methods in economics research.
Covers estimation, identification, and inference for structural models.

---

## 1. Discrete Choice Models

**When to use**: Agents make discrete choices from a finite set of alternatives
(job choice, product purchase, migration, technology adoption). Utility is
latent; only choices are observed.

**Key patterns**:

```r
# R — mlogit (multinomial logit)
library(mlogit)
ml <- mlogit(choice ~ price + quality | income, data = mlogit.data(df, choice="chosen", shape="long", alt.var="alt"))

# R — mixed logit (random coefficients) via mlogit
ml_mixed <- mlogit(choice ~ price | income, data = mld,
                   rpar = c(price = "n"), R = 500, halton = NA)

# R — BLP-style mixed logit via BLPestimatoR or PyBLP via reticulate
# Stata — asclogit, mlogit, xtlogit
asclogit choice price quality, case(id) alternatives(alt) casevars(income)
```

**IIA test**: Use Hausman-McFadden test for logit; violation suggests nested or
mixed logit.

> **Survey design note**: `mlogit`, `asclogit`, and `xtlogit` do not account
> for survey clustering or stratification by default. For survey data, use
> `svyglm()` (binary outcomes) or pass `weights` and cluster-robust SEs.
> Unweighted estimates on survey data represent the sample, not the population.

> **PPP vintage consistency**: When utility or budget-share variables include
> income or welfare aggregates, ensure all series use the same PPP vintage
> (2011 or 2017). Mixing vintages invalidates cross-country comparisons.

```r
# Hausman test for IIA (mlogit)
hmftest(ml, alt.subset = c("alt1", "alt2"))
```

**Model selection**:
- Logit: IID Type-I extreme value errors; closed-form probabilities; fast
- Nested logit: allows within-nest correlation; requires tree structure
- Mixed logit: fully flexible substitution; requires simulation (R ≥ 500 Halton draws)
- BLP: market-level data; instrument endogenous prices with cost shifters

**Anti-patterns**:
- Using standard logit when IIA is violated (e.g., red bus/blue bus problem)
- Fewer than 500 simulation draws for mixed logit
- Ignoring panel structure in individual choice data (use `xtlogit` or `feglm`)
- Treating market share as unit of analysis without controlling for price endogeneity

**References**: Train (2009) *Discrete Choice Methods with Simulation*; Berry (1994) RAND; BLP (1995) Econometrica

---

## 2. Dynamic Programming

**When to use**: Agents make sequential decisions under uncertainty where current
choices affect future states (job search, investment, health behavior, retirement).

**Key patterns**:

### Rust (1987) NFXP — Nested Fixed-Point Algorithm

```r
# Bellman equation: V(x) = max_a { u(x,a) + β E[V(x')|x,a] }
# NFXP: solve fixed-point V = T(V) for each parameter guess θ

# R — use nloptr or optim as outer loop; solve Bellman as inner loop
bellman_iter <- function(V, params, beta = 0.9, tol = 1e-8) {
  repeat {
    V_new <- apply(utility_matrix(params) + beta * transition %*% V, 1, max)
    if (max(abs(V_new - V)) < tol) break
    V <- V_new
  }
  V
}
```

### Hotz-Miller CCP — Conditional Choice Probability Approach

```r
# Step 1: estimate CCPs from data (non-parametrically or logit)
ccp_hat <- glm(action ~ state_vars, family = binomial, data = df)

# Step 2: recover value functions from CCPs (Hotz-Miller inversion)
# V(x) = (I - β*F(ccp))^{-1} * flow_utilities(ccp)
```

**Convergence diagnostics**:
- Value function iteration: monitor sup-norm convergence; ≥ 1000 state grid points
  for continuous state spaces
- NFXP: outer MLE tolerances tighter than inner Bellman tolerance
- Starting values: try multiple starting points; objective is often non-convex

```r
# Bellman convergence guard — required before proceeding to outer MLE
if (max(abs(V_new - V)) >= tol)
  stop("Bellman iteration did not converge after max iterations — ",
       "check beta < 1, transition matrix rows sum to 1, and grid resolution.")
```

**Anti-patterns**:
- Assuming convergence without checking the Bellman contraction criterion
- Using policy iteration without checking that β < 1 (discount factor must be
  strictly less than 1 for contraction)
- Ignoring curse of dimensionality for high-dimensional state spaces (use
  approximation methods: Rust's discretization, neural network VFI, or
  endogenous grid method)

**References**: Rust (1987) Econometrica; Hotz & Miller (1993) ReStud;
Arcidiacono & Miller (2011) Econometrica

---

## 3. Simulation-Based Estimation

**When to use**: The likelihood or moment conditions lack closed form — common
in structural models with continuous unobservables, dynamic models, or
models with high-dimensional integration.

### MSM — Method of Simulated Moments

```r
# Simulate moments: draw ε_s, compute model moments m_s(θ), minimize
# || (1/S) Σ_s m_s(θ) - m_data ||²_W

msm_objective <- function(theta, data, n_sims = 1000, W = diag(length(moments))) {
  set.seed(12345)  # ALWAYS seed before simulation
  sims <- replicate(n_sims, simulate_model(theta))
  m_sim  <- rowMeans(sims)
  m_data <- compute_data_moments(data)
  t(m_sim - m_data) %*% W %*% (m_sim - m_data)
}
```

### SMM — Simulated Method of Moments (with analytical gradient)

Same as MSM but W is the optimal weighting matrix (inverse of asymptotic
variance of data moments):

```r
W_opt <- solve(var(moment_matrix(data)))
```

### Indirect Inference

```r
# Auxiliary model: fit a flexible model to data → get β_data
# For each θ, simulate data → fit same auxiliary model → get β_sim(θ)
# Minimize: || β_sim(θ) - β_data ||²
```

**Simulator requirements**:
- Smoothness: simulator must be differentiable w.r.t. θ for gradient-based
  optimization; use antithetic variates or common random numbers
- Bias: MSM is unbiased for the moments but biased for the parameters;
  the only remedy is increasing S
- Number of simulations: S ≥ 5N (N = sample size) for low bias; more for
  complex models

**Memory note**: For S ≥ 5,000, `replicate()` materialises the full
`n_moments × S` matrix before `rowMeans()` reduces it (~20 MB+ per optimizer
call at scale). Prefer the streaming accumulator:
```r
# Streaming alternative for large S — avoids n_moments × S matrix
m_sim <- numeric(length(compute_data_moments(data)))
for (s in seq_len(n_sims)) {
  m_sim <- m_sim + simulate_model(theta)
}
m_sim <- m_sim / n_sims
```

**Anti-patterns**:
- Unseeded simulation (P0 — results are not reproducible)
- S < 100 simulations (bias dominates)
- Using different random draws for different parameter values (breaks
  smoothness of objective function)
- Ignoring simulation noise in standard errors (inflate SEs by (1 + 1/S)^{1/2})

---

## 4. Maximum Likelihood for Structural Models

**When to use**: Likelihood of observed data can be written (or simulated) as a
function of structural parameters.

**Key patterns**:

```r
# R — optim with BFGS; use log-likelihood, maximize by minimizing negative
log_lik <- function(theta, data) {
  ll <- sum(log(model_density(data, theta)))
  if (!is.finite(ll)) return(1e10)  # large positive penalty — tells minimizer to avoid this region
  -ll  # minimize negative log-likelihood
}

result <- optim(theta0, log_lik, data = df,
                method = "BFGS",
                control = list(maxit = 2000, reltol = 1e-12),
                hessian = TRUE)

# Standard errors from Hessian (information matrix)
stopifnot("Optimizer did not converge" = result$convergence == 0)
eigenvalues <- eigen(result$hessian, only.values = TRUE)$values
if (any(eigenvalues <= 0))
  stop("Hessian not positive-definite at solution — SEs are invalid. ",
       "Check for boundary solutions or local optima.")
se <- sqrt(diag(solve(result$hessian)))
```

**Score function** (analytical gradient speeds convergence):

```r
score <- function(theta, data) {
  # ∂ log L / ∂ θ — derive analytically from the model
}
# Pass to optim via gr = score
```

**Convergence diagnostics**:
- Check gradient norm at convergence: `max(abs(result$gradient)) < 1e-5`
- Try multiple starting values (especially for multimodal likelihoods)
- Verify Hessian of the **negative** log-likelihood is positive-definite at solution (all eigenvalues > 0) *(equivalently, Hessian of the log-likelihood is negative-definite — but `optim` returns the former)*
- For constrained parameters, use reparametrization (log for σ > 0, logit for p ∈ (0,1))

**Anti-patterns**:
- Using `nlm` without checking `code` field (3 or 4 = convergence failure)
- Single starting value for non-convex likelihoods
- Ignoring boundary solutions (parameters hitting bounds signal
  misspecification or identification failure)
- Using numerical Hessian for SE when analytical formula available

> **PPP vintage consistency**: When the likelihood includes income, welfare, or
> budget-share variables as observables or conditioning variables, ensure all
> series use the same PPP vintage (2011 or 2017). Mixing vintages produces
> structurally misspecified likelihoods in cross-country structural models.

---

## 5. GMM

**When to use**: Moment conditions E[g(y, x, θ)] = 0 are available but the
likelihood is unknown or misspecified. Robust to distributional assumptions.

**Key patterns**:

```r
# R — gmm package
library(gmm)
g_fn <- function(theta, data) {
  # Returns n × k matrix of moment conditions (n obs, k moments)
  cbind(data$x * (data$y - theta[1] - theta[2]*data$x),
        data$z * (data$y - theta[1] - theta[2]*data$x))
}

fit <- gmm(g_fn, data, theta0 = c(0, 0), wmatrix = "optimal")

# Two-step: first step W = I, second step W = S^{-1}
# Continuous updating (CUE): jointly optimize θ and W
```

**Optimal weighting matrix**:
```r
# S = Avar(n^{-1/2} Σ g_i(θ)) — use moment matrix directly for HAC
# First-step: get moment conditions at first-step estimates
g_mat <- g_fn(coef(step1_fit), data)              # n × k moment conditions
S_hat <- (1/nrow(g_mat)) * t(g_mat) %*% g_mat    # k × k (HAC-consistent)
W_opt <- solve(S_hat)
# Note: sandwich::NeweyWest() requires a fitted model object, not a raw vector;
# passing residuals directly returns a 1×1 scalar, not a k×k weighting matrix.
```

**Overidentification (Hansen J-test)**:
```r
# Under H0 (all moments valid): n * J(θ_hat) ~ χ²(k - p)
# k = number of moments, p = number of parameters
j_stat <- n * min_value  # from gmm() output
p_value <- 1 - pchisq(j_stat, df = k - p)
# Report: J = X.X (df = k-p), p = X.XX
```

**Moment selection criteria**:
- Andrews-Lu (2001): BIC-type for GMM moment selection
- Add moments one-by-one; report J-test at each step

**Anti-patterns**:
- Using identity weighting matrix (sub-optimal; inefficient estimates)
- Not reporting J-test for overidentified models
- Ignoring weak identification in GMM (use Kleibergen 2005 robust tests)
- Using two-step GMM with many moments (finite-sample bias; use CUE or
  jackknife GMM instead)

**References**: Hansen (1982) Econometrica; Newey & West (1987) Econometrica;
Stock & Wright (2000) Econometrica

> **PPP vintage consistency**: When moment conditions include income, welfare,
> or budget-share aggregates, ensure all series use the same PPP vintage
> (2011 or 2017). Mixing vintages invalidates the moment conditions in
> cross-country structural models.

---

## 6. Standard Errors

**When to use which**:

| SE Type | When | R | Stata |
|---------|------|---|-------|
| OLS/analytic | iid errors, correct model | `lm()` default | `reg` default |
| Sandwich/HC | heteroscedasticity | `sandwich::vcovHC()` | `, robust` |
| Cluster-robust | within-cluster correlation | `sandwich::vcovCL()` | `, cluster()` |
| Bootstrap (nonparam) | non-normal, small n | `boot::boot()` | `bootstrap` |
| Bootstrap (wild) | heteroscedasticity + few clusters | `fwildclusterboot` | `boottest` |
| Delta method | nonlinear functions of estimates | `car::deltaMethod()` | `nlcom` |
| Bootstrap (param) | structural models w/ simulation | custom | custom |

**Cluster level rule**: Cluster at the level of treatment variation, not the
level of the unit of analysis. (P0 risk if wrong.)

```r
# R — cluster-robust SE with fixest
library(fixest)
feols(y ~ x | fe1 + fe2, data = df, cluster = ~cluster_var)

# Delta method for nonlinear function
library(car)
deltaMethod(fit, "exp(b1) / (1 + exp(b1))")  # logit → probability
```

**Anti-patterns**:
- Clustering at a finer level than treatment (under-states SEs)
- Reporting heteroscedasticity-robust SEs when clustering is needed
- Wild bootstrap with G < 10 clusters (use exact permutation instead)
- Delta method for highly nonlinear functions far from normality (use
  parametric bootstrap instead)

---

## 7. Identification

**Formal identification**: A parameter vector θ is identified if no two
distinct θ, θ' produce the same distribution of observables.

**Key concepts**:

- **Order condition** (necessary): number of instruments ≥ number of endogenous variables
- **Rank condition** (necessary and sufficient): E[Z'X] has full column rank
- **Identification at infinity**: identification relies on observations at the
  boundary of the support (e.g., Heckman selection model at exclusion restriction);
  fragile in finite samples
- **Local vs. global identification**: most structural models are only locally
  identified (Jacobian rank condition); test for multiple optima

**Exclusion restrictions**:
```r
# An instrument Z must satisfy:
# (1) Relevance: Cov(Z, X) ≠ 0 — testable (first-stage F)
# (2) Exogeneity: Cov(Z, ε) = 0 — not directly testable; requires argument
# Document the economic justification for exogeneity in the plan/derivation
```

**Anti-patterns**:
- Claiming identification without formal argument (order + rank condition check)
- Relying on functional form for identification (normality assumption, log-linearity)
  without discussion
- Not checking for multiple local optima in structural estimation
- Identification at infinity without noting finite-sample fragility

**References**: Rothenberg (1971) Econometrica; Matzkin (2007) Handbook;
Lewbel (2019) JEL

---

## 8. Anti-Patterns in Structural Estimation

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| Estimating without convergence check | Silent failure → wrong estimates | Check gradient norm, eigenvalues of Hessian |
| Single starting value | Local optima contaminate results | Grid search or multi-start |
| Ad-hoc functional forms | Identification from functional form is fragile | Justify from theory; sensitivity-test to functional form |
| Unreported simulation count | Reader can't assess bias | Always report S (simulation draws) |
| Unseeded simulation | Non-reproducible | `set.seed()` before every random call |
| Ignoring boundary estimates | Signals misspecification | Investigate; consider reparametrization |
| Using MLE for misspecified model without robustness check | Inconsistent estimates | Report sandwich SE or GMM robustness |
| Not checking IIA for discrete choice | Wrong substitution patterns | Hausman test; consider nested/mixed logit |
