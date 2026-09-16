---
name: cr-skill-mathematical-derivation
module: research
description: "LaTeX and mathematical derivation conventions for economics research.
  Covers notation discipline, numbered equation conventions, FOC derivation patterns,
  envelope theorem applications, integration by parts in expectation, change of
  variables, asymptotic expansions, and cross-referencing code variables to math
  symbols. Loaded for Theory/Modeling and Implementation tasks."
---

# Mathematical Derivation Conventions

Reference skill for writing, organizing, and documenting mathematical derivations
in economics research. The goal is derivations that are (1) self-contained,
(2) auditable by a colleague or the `@cr-mathematical-verification` agent, and
(3) directly traceable to code implementation.

---

## 1. Notation Discipline

**Rules**:
- Introduce every symbol before first use: *"Let $y_i \in \mathbb{R}$ denote
  the log wage of individual $i$."*
- Distinguish random variables from realizations: $Y$ (random variable),
  $y$ (realization), $\mathbf{Y}$ (random vector), $\boldsymbol{y}$ (observed sample)
- Use consistent subscripts throughout: if $i$ indexes individuals and $t$
  indexes time, never let $i$ mean time in a later section
- Reserve standard notation: $\beta$ for coefficients, $\varepsilon$/$u$ for
  errors, $\theta$ for parameter vectors, $\mathcal{L}$ for likelihood,
  $\mathcal{F}$ for filtrations/information sets
- Avoid overloading symbols: if $f$ is used as a function, do not also use
  $f$ as a frequency

**LaTeX conventions**:
```latex
% Prefer \mathbb for sets, \mathcal for operators
\mathbb{R}, \mathbb{E}, \mathbb{P}   % reals, expectation, probability
\mathcal{L}, \mathcal{F}, \mathcal{N} % likelihood, filtration, normal

% Use \text{} for words inside math mode
p(\text{work} \mid x)   % NOT p(work | x)

% Distinguish vectors and scalars
\boldsymbol{\beta}  % vector
\beta_k             % scalar component
```

**Anti-patterns**:
- Using the same letter for different objects in the same derivation
- Dropping subscripts "for clarity" and then reintroducing them later
- Mixing $E[\cdot]$ and $\mathbb{E}[\cdot]$ in the same document

---

## 2. Equation Conventions

**LaTeX environments**:
```latex
% Use align for multi-line derivations (aligned at =)
\begin{align}
  \mathcal{L}(\theta) &= \sum_{i=1}^{N} \log f(y_i \mid x_i, \theta) \label{eq:loglik} \\
                      &= \sum_{i=1}^{N} \left[ -\frac{1}{2}\log(2\pi\sigma^2)
                         - \frac{(y_i - x_i'\beta)^2}{2\sigma^2} \right]
\end{align}

% Use equation for single numbered equations
\begin{equation}
  \hat{\beta}_{\text{OLS}} = (X'X)^{-1}X'y \label{eq:ols}
\end{equation}

% Use align* for unnumbered multi-line (intermediate steps)
\begin{align*}
  \frac{\partial \mathcal{L}}{\partial \beta} &= \frac{1}{\sigma^2} X'(y - X\beta) = 0
\end{align*}
```

**Numbering policy**:
- Number every equation that is referenced elsewhere (in the text, in the code,
  in a theorem/lemma)
- Label format: `eq:<descriptive-name>` (e.g., `eq:loglik`, `eq:foc-beta`,
  `eq:moment-condition`)
- Do NOT number intermediate algebra steps — use `align*`
- Cross-reference with `\eqref{eq:loglik}` (not `(\ref{eq:loglik})`)

---

## 3. FOC Derivation Patterns

### Unconstrained optimization

```latex
% Step 1: State the objective
\max_{\theta} \; \mathcal{L}(\theta) = \sum_{i=1}^{N} \log f(y_i \mid \theta)

% Step 2: First-order condition
\frac{\partial \mathcal{L}}{\partial \theta} = \sum_{i=1}^{N}
  \frac{\partial \log f(y_i \mid \theta)}{\partial \theta} = 0 \label{eq:score}

% Step 3: Solve (if closed form exists)
\hat{\theta} = \left( \sum_{i=1}^{N} s_i s_i' \right)^{-1}
  \sum_{i=1}^{N} s_i y_i

% Step 4: Check SOC (second-order condition)
\frac{\partial^2 \mathcal{L}}{\partial \theta \partial \theta'} \prec 0
  \quad \text{(negative definite at } \hat{\theta} \text{)}
```

### Constrained optimization (Lagrangian)

```latex
% Lagrangian: objective + λ × constraint
\mathcal{L}(\theta, \lambda) = f(\theta) - \lambda \cdot g(\theta)

% KKT conditions:
\nabla_\theta \mathcal{L} = \nabla f(\theta) - \lambda \nabla g(\theta) = 0
g(\theta) \leq 0, \quad \lambda \geq 0, \quad \lambda g(\theta) = 0
% (last line: complementary slackness)
```

**Anti-patterns**:
- Dropping the SOC check ("existence of FOC solution implies maximum")
- Not specifying the domain of optimization (unbounded domains require
  additional regularity conditions for existence)
- Solving FOCs without verifying the bordered Hessian for constrained problems

---

## 4. Common Derivation Techniques

### Envelope Theorem

For $V(\alpha) = \max_x \{f(x, \alpha)\}$ where $x^*(\alpha)$ is the maximizer:

```latex
\frac{dV}{d\alpha} = \frac{\partial f(x^*(\alpha), \alpha)}{\partial \alpha}
% The indirect effect through x* is zero by the envelope theorem
```

**Application**: Deriving comparative statics without solving for $x^*$ explicitly.

### Leibniz Rule (differentiating under the integral)

```latex
\frac{d}{d\alpha} \int_{a(\alpha)}^{b(\alpha)} f(x, \alpha) \, dx
  = f(b(\alpha), \alpha) \cdot b'(\alpha) - f(a(\alpha), \alpha) \cdot a'(\alpha)
  + \int_{a(\alpha)}^{b(\alpha)} \frac{\partial f(x, \alpha)}{\partial \alpha} \, dx
```

**Application**: Deriving likelihoods for models with censoring or selection.

### Integration by Parts (in expectation context)

```latex
E[X g(X)] = E[g'(X)]   \quad \text{(Stein's lemma, for } X \sim \mathcal{N}(0,1) \text{)}
```

**Application**: Computing moments of truncated normal distributions in selection models.

### Change of Variables

```latex
% If Y = g(X) with g strictly monotone:
f_Y(y) = f_X(g^{-1}(y)) \cdot \left| \frac{dg^{-1}(y)}{dy} \right|
% (Jacobian factor — often forgotten)
```

**Application**: Deriving the likelihood for log-wage models, duration models.

### Taylor Expansion (for delta method / asymptotic approximations)

```latex
g(\hat{\theta}) \approx g(\theta_0) + \nabla g(\theta_0)'(\hat{\theta} - \theta_0)
% Asymptotic variance of g(θ̂):
\text{Avar}(g(\hat{\theta})) = \nabla g(\theta_0)' \cdot \text{Avar}(\hat{\theta}) \cdot \nabla g(\theta_0)
```

---

## 5. Asymptotic Expansions

**Convergence notation**:
```latex
\hat{\theta} \xrightarrow{p} \theta_0        % convergence in probability
\sqrt{N}(\hat{\theta} - \theta_0) \xrightarrow{d} \mathcal{N}(0, V)  % asymptotic normality
O_p(N^{-1/2}), \; o_p(1)                     % stochastic orders
```

**Sandwich variance**:
```latex
\text{Avar}(\hat{\theta}) = \mathcal{H}^{-1} \mathcal{S} \mathcal{H}^{-1}
% where:
\mathcal{H} = -E\left[\frac{\partial^2 \log f}{\partial\theta\partial\theta'}\right]  % Hessian
\mathcal{S} = E\left[\frac{\partial \log f}{\partial\theta} \frac{\partial \log f}{\partial\theta'}\right]  % outer product of scores
% Under correct specification: H = S (information matrix equality → Fisher information)
```

**Documentation requirement**: If asymptotic results depend on regularity
conditions (e.g., compactness of parameter space, bounded moments), state
them explicitly. Cite Newey & McFadden (1994) *Handbook* for sufficient
conditions for MLE/GMM.

---

## 6. Code-Math Variable Mapping

Every derivation file in `c-research/derivations/` should include a
variable mapping table linking math symbols to code variables. This is the
primary input for `@cr-mathematical-verification`.

**Table format**:

| Math Symbol | Meaning | Code Variable | Code File | Notes |
|-------------|---------|---------------|-----------|-------|
| $\beta$ | coefficient vector | `beta` | `estimation.R:45` | `p`-vector |
| $X$ | covariate matrix | `X_mat` | `estimation.R:38` | `n × p` matrix |
| $y$ | outcome vector | `y_vec` | `estimation.R:37` | log-wage |
| $\sigma^2$ | error variance | `sigma2` | `estimation.R:61` | reparametrized as `log_sigma` in optimizer |
| $\hat{\theta}$ | MLE estimate | `theta_hat` | `estimation.R:89` | output of `optim()` |

**Naming conventions** that make mapping transparent:
- Prefer `beta` over `b`, `mu` over `m`, `sigma` over `s`
- Use `_vec` / `_mat` suffixes for vectors/matrices
- Add equation references in code comments: `# Equation (3) in derivation`

---

## 7. Derivation File Organization

Store derivations in `c-research/derivations/`. Each file should:

**Frontmatter**:
```yaml
---
title: "Wage Equation MLE — Derivation"
model: "Normal wage equation with selection"
date: YYYY-MM-DD
status: "draft | reviewed | final"
code-file: "estimation.R"
---
```

**Section structure** (follow this order):
1. **Setup** — state the model, define notation, enumerate parameters
2. **Assumptions** — explicit list (A1, A2, ...) that the derivation relies on
3. **Derivation** — step-by-step with numbered equations
4. **Result** — box or highlight the main result (estimating equation, FOC, etc.)
5. **Variable Mapping Table** — code-math correspondence (see Section 6)

**Cross-referencing**:
```markdown
See [Equation (3)](../derivations/wage-mle.md#eq:foc-beta) for the FOC.
```

---

## 8. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| Skipping algebra steps ("it follows that...") | Reviewer cannot verify; mismatch risk | Show every non-trivial step |
| Inconsistent notation across sections | Ambiguity; code-math mismatch | Use notation table at top of file |
| Undocumented simplifications | e.g., "I dropped the constant" — silent change | Add footnote: "The term $C$ drops out because..." |
| No variable mapping table | `@cr-mathematical-verification` cannot audit | Always include Section 6 table |
| Writing derivations in comments only | Not searchable; no LaTeX rendering | Use `c-research/derivations/` |
| Equations numbered "by feel" | Hard to cross-reference | Number only equations that are cited |
| Mixing proof and implementation in same file | Hard to audit independently | Separate `.tex` derivation from `.R`/`.py` code |
