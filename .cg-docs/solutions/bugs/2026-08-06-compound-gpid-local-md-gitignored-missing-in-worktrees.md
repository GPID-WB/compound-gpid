---
date: 2026-08-06
title: "compound-gpid.local.md gitignored causing missing config in fresh worktrees and clones"
category: "bugs"
type: "bug"
language: "both"
tags: [gitignore, compound-gpid.local.md, version-control, worktree, team-config, pester]
root-cause: "compound-gpid.local.md was misclassified as personal user config and gitignored even though it holds team-shared settings and safety notes, so git could never deliver it to clones/worktrees and teams rebuilt it by manual copying."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "missing-test"
---

# compound-gpid.local.md gitignored causing missing config in fresh worktrees and clones

## Symptom

`compound-gpid.local.md` was absent from every fresh git worktree and clone.
Team members had to manually copy the file between computers for Compound GPID
skills and agents to function correctly, and each copy could drift from the
team's canonical settings.

Observed directly: a new git worktree (this repo uses worktree/Agent Manager
heavily — 4+ worktrees) checked out at the same commit as `main` had no
`compound-gpid.local.md`, because the file is untracked and git ignores it
(`.gitignore:2`). `git log --all -- compound-gpid.local.md` is empty — it was
never committed.

## Expected Behavior Source

Source type: **user-requirement** — the bug reporter stated that the file
"must be accessible across machines and team members without manual copying."

Specifically: `compound-gpid.local.md` must (1) exist at the repository root,
(2) not be excluded by `.gitignore`, and (3) be tracked by git, so every
checkout, worktree, and team member receives the team-shared config
automatically. These three contracts became the assertions in the reproduction
test.

## Root Cause

An early intentional classification decision labeled `compound-gpid.local.md`
"user-specific, never committed" (the `.gitignore` comment) and `cg-setup`
prompt A5.5 wrote the ignore rule automatically. That classification was wrong
for what the file actually contains:

- It carries **team-shared fields**: `language`, `project-type`, `r-syntax`,
  `review-depth`, and optional `model-advisory`/`team-brain:`.
- Its `## Notes` section carries **team-wide safety rules** (the Pester crash
  patterns) that the team deliberately duplicates there
  (`compound-gpid.context.md` note: "Duplicate critical safety rules in
  `compound-gpid.local.md`").
- It contains **no secrets** — nothing that justifies staying out of git.
- The team already effectively standardizes on **one** copy — they just rebuild
  it manually because git cannot deliver it.

Because the plugin is worktree/Agent-Manager heavy, an untracked ignored file
is invisible in every fresh worktree and clone. The manual-copy ritual was not
a workflow preference — it was the unavoidable consequence of gitignoring a
file that was never really personal.

## Reproduction Test

`tests/local-config.Tests.ps1` (new file, registered in `tests/Run-Tests.ps1`
`$testNames`). Expected values derived from the user requirement, not from the
implementation:

1. `.gitignore` contains no uncommented `compound-gpid.local.md` rule.
2. `compound-gpid.local.md` exists at the repository root.
3. `git ls-files --error-unmatch -- compound-gpid.local.md` exits 0 (tracked).

Red phase (before fix): `Total=3 Passed=0 Failed=3` —
"is NOT excluded by an uncommented .gitignore rule :: Expected $true, got $false",
"exists at the repository root :: Expected $true, got $false",
"is tracked by git :: Expected 0, but got 1".

## Test Gap

Classification: **missing-test** — no test ever asserted that
`compound-gpid.local.md` is version-controlled. The closest existing test
(`prompt-tools.Tests.ps1` "updates .gitignore to exclude
compound-gpid.local.md") only asserted that `cg-setup.prompt.md` *mentions*
`.gitignore` — a regex that passes whether the prompt ignores or un-ignores the
file. That adjacent test documented the wrong behavior without guarding it, so
the gitignore decision shipped with zero coverage of its real-world consequence
(config missing from worktrees and clones).

## Fix

1. **`.gitignore`** — removed the `compound-gpid.local.md` entry and wrote a
   comment explaining the file is team-shared and must be committed.
2. **`compound-gpid.local.md`** — created the canonical team version at the
   repo root (frontmatter + the shared `## Notes` Pester safety rules) and
   staged it so it is tracked by git.
3. **`.github/prompts/cg-setup.prompt.md` A5.5** — replaced the
   "append to `.gitignore`" step with "Keep `compound-gpid.local.md`
   version-controlled: remove any ignore rule, do NOT add it".
4. **`.github/prompts/setup-templates.md`** — the template text now reads
   "It is version-controlled and shared across the team" instead of
   "gitignored and local to your machine".
5. **`tests/Run-Tests.ps1`** — registered `local-config` in `$testNames` so the
   new regression guard runs in the suite (otherwise a silent coverage gap).
6. **Canonical docs** — corrected `docs/reference/files.md` and
   `docs/configuration/index.md` (ownership "Team; committed", removed the
   "Do not commit `compound-gpid.local.md`" instruction).

Generated provider trees (`.agents/`, `.opencode/`, `.claude/`, `.kilo/`) carry
copies of the prompt/template; per project convention these are regenerated by
`cg-update`, not edited by hand.

## Lessons Learned

The test gap was `missing-test`, and the anti-pattern is a **classification
error** that no test protected against: a file was labeled "personal" and
gitignored even though it contained team-shared configuration, safety notes,
and no secrets. The team's own context note already told them to duplicate
critical rules into this file — i.e., team-shared content — while git treated it
as per-user.

Pattern to follow: **version-control any file the team standardizes on, unless
it genuinely holds secrets or machine-specific credentials.** For config files
that mix shared and personal intent, split them — shared fields into a committed
file, truly personal overrides elsewhere — rather than gitignoring the whole
thing. Always pair a "never commit / gitignore" rule with a regression test that
asserts the **presence and version-control** of the artifact it protects, not
just that some prompt mentions `.gitignore`.

## Related

None found in `.cg-docs/solutions/bugs/`. Adjacent gitignore guidance lives in
`compound-gpid.context.md` (the `.cg-docs/` and `compound-gpid.context.md` must
be committed notes) and `.opencode/skills/cg-skill-git-workflow/references/gitignore-templates.md`
(the template that previously listed `compound-gpid.local.md`).
