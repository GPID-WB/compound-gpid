---
applyTo: "**/c-research/derivations/**/*.md,**/c-research/derivations/**/*.tex"
module: research
---

# Mathematical Derivation File Standards

> **Full guidance**: Always load `cr-skill-mathematical-derivation` and
> `cr-skill-symbolic-verification` when working in this directory.
> These skills provide notation conventions, equation numbering, code-math
> mapping tables, and numerical verification patterns.

> **Risk note (P2.1)**: The `applyTo` glob in this file uses a path-based
> pattern (`**/c-research/derivations/**`). VS Code may not apply these
> instructions automatically in all cases, particularly when `.cg-docs/` exists
> at a non-root depth in multi-root workspaces (the leading `**/` matches at
> any depth).
>
> **If this instruction file does not apply automatically**:
> 1. Run `/cg-link` to rebuild the instruction index and reload the window.
> 2. Load `cr-skill-mathematical-derivation` and `cr-skill-symbolic-verification`
>    manually in Copilot Chat for the file you are working on.
> 3. If the problem persists, open a GitHub issue at GPID-WB/compound-gpid.
>
> **Multi-depth risk**: The glob matches `c-research/derivations/` at
> any workspace depth. If you use nested project directories, ensure only
> derivation files live under this path to avoid unintended instruction loading.

---

## Required File Structure

Every derivation file must follow this section order:

1. **Setup** — model definition, notation, parameter list
2. **Assumptions** — numbered list A1, A2, ... of maintained assumptions
3. **Derivation** — step-by-step with numbered equations (`eq:<name>`)
4. **Result** — main result (estimating equation, FOC, closed form)
5. **Variable Mapping Table** — see below
6. **References** — key papers

## Required Frontmatter

```yaml
---
title: "Descriptive title of derivation"
model: "Short model name"
date: YYYY-MM-DD
status: "draft | reviewed | final"
code-file: "relative/path/to/implementation.R"
---
```

## Variable Mapping Table (mandatory)

Include a table linking every math symbol to its code variable:

| Math Symbol | Meaning | Code Variable | Code File | Notes |
|-------------|---------|---------------|-----------|-------|
| $\beta$ | coefficient vector | `beta` | `estimation.R:45` | |

This table is the primary input for `@cr-mathematical-verification`.
Without it, the verification agent cannot perform a code-math audit.

## Equation Numbering

- Number equations referenced in text or code: `$(k)$` or `\label{eq:name}`
- Use `align*` for intermediate algebra (unnumbered)
- Cross-reference by number: "From $(3)$..." or "Applying \eqref{eq:foc}"
- Never renumber equations after code references are established

## Sign and Reparametrization Conventions

Document any sign flips or reparametrizations prominently:

```markdown
> **Sign convention**: The derivation maximizes $\mathcal{L}$, but the code
> minimizes $-\mathcal{L}$. See `estimation.R:50`.
>
> **Reparametrization**: $\sigma^2$ is stored as `log_sigma` in the optimizer
> and back-transformed at line 88.
```

## Verification Checklist

Before marking a derivation `status: final`, confirm:

- [ ] All assumptions (A1, A2, ...) stated explicitly
- [ ] All equations have labels where referenced
- [ ] Variable mapping table complete (no symbols without code references)
- [ ] Sign conventions documented
- [ ] Reparametrizations documented
- [ ] `@cr-mathematical-verification` gradient check completed
- [ ] SOC verified numerically at estimated parameters
