---
description: "Analyze Compound GPID token/context usage and suggest cost-efficient workflow choices."
---

# Token Audit

You are helping the user understand how Compound GPID token/context cost is
used in the current project. This command is advisory: it reports evidence and
recommendations, but it does not modify project configuration or source files.

## File Permissions

- You may read `compound-gpid.md` and `compound-gpid.local.md` in the project
  root if present.
- You may load `.github/shared/context-loading.contract.md`.
- You may run `cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations`.
- Context expansion: reading `.cg-docs/cost/token-advice.md` because this
  command summarizes the deterministic audit report it just generated.
- Context expansion: reading `.cg-docs/token/TOKEN-DASHBOARD.md`,
  `.cg-docs/token/regression-check.json`, `.cg-docs/token/TOKEN-BUDGET.md`,
  and `.cg-docs/token/workflow-costs.csv` when the user asks for workflow
  baseline or regression details.
- You must not modify source files, roadmap state, prompt files, or project
  configuration. The audit command may write only its report files under
  `.cg-docs/cost/` and `.cg-docs/token/`.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` if it exists for project identity and constraints.
2. Read `compound-gpid.local.md` if it exists for local review/model
   preferences.
3. Load `.github/shared/context-loading.contract.md`.
4. Do not read `.cg-docs/`, `BRAIN*.md`, `brain-index.json`,
   `compound-gpid.context.md`, or `roadmap.json` directly unless the user asks
   for a specific follow-up and the context-loading contract permits targeted
   expansion.

### Step 1: Run the deterministic audit

Run this exact command from the current project root:

```bash
cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations
```

The explicit `--root .` is required so the audit analyzes the user's current
project, not the installed plugin repository.

The command also writes additive workflow baseline, dashboard, and regression
artifacts under `.cg-docs/token/` by default. These do not replace the legacy
`.cg-docs/cost/` reports used by existing `/cg-token-audit` summaries.

If `cg-token-audit` is unavailable, run the repository-local fallback only when
`scripts/cg_audit_context.py` exists in the current project:

```bash
python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations
```

If neither command is available, report that the installed Compound GPID CLI
needs to be updated and stop.

### Step 2: Summarize recommendations

Context expansion: reading `.cg-docs/cost/token-advice.md` because Step 1
generated it as the compact recommendations source. Summarize:

- guardrail failures and warnings;
- warning classification counts: fix, accept, docs-only;
- highest-priority recommendations;
- workflow advice such as using lighter models for simple planning, matching
  review depth to risk, and avoiding broad context reads.

Keep the answer concise and evidence-driven. Do not auto-fix anything.
