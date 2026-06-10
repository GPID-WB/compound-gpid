---
date: 2026-06-10
depth: full
type: standard
plan: .cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: skipped
  P3.10: skipped
  P3.11: fixed
  P3.12: fixed
  P3.13: fixed
  P3.14: fixed
---

# Review Report

**Review mode**: full
**Files reviewed**: 16
**Findings**: 22 (P0: 0, P1: 3, P2: 5, P3: 14)

Auto-routing applied: all changed files are `.cg-docs/` knowledge artifacts and `docs/*.md`
documentation — classified `low` risk. Config `review-depth: thorough` (= `full`) overrides
auto-routing. Resolved review mode: `full`. All 10 agents dispatched.

---

## P0 — BLOCKING

None.

---

## P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `.cg-docs/cost/token-optimization-release-checklist.md`:18-37 — "Passed in Codex" statuses are unanchored self-attestation
  **Why**: Every "Passed in Codex" status is pre-filled static text. A maintainer who makes post-commit changes and does NOT re-run the audit can cite this checklist as-is. The "see generated audit timestamp" reference is invalidated silently each time `context-audit.json` is regenerated. Post-commit regressions pass review against stale attestation.
  **Fix**: Record the specific audit `generated` timestamp inline in each "Passed in Codex" status cell (e.g., `"Passed in Codex 2026-06-09T17:02:00; must re-run if any .github/ files change"`). Add a header note: "Statuses reflect a specific audit run. Re-run the audit after any `.github/` change before citing these statuses." `[manual]`

- **[P1.2]** [cg-adversarial/cg-testing] `.cg-docs/cost/token-optimization-follow-ups.md`:22-29 vs `.cg-docs/cost/token-optimization-release-checklist.md`:31 — Pester named release gate cross-listed as non-blocking
  **Why**: The follow-ups file places "Run the safe Pester suite in VS Code/PowerShell" under Non-Blocking Follow-ups (rationale: "PowerShell may be unavailable in Codex"). The checklist names it a Release Gate with "External validation required." A maintainer can cite the follow-ups file to close the release without running Pester — the only harness that catches `.github/` prompt structural regressions.
  **Fix**: Move the Pester row to a separate "Deferred to VS Code/PowerShell — Required Before Merge" section in the follow-ups file, or add: "Non-blocking *in Codex* only; must run in VS Code/PowerShell before final merge sign-off." `[manual]`

- **[P1.3]** [cg-adversarial/cg-testing] `.cg-docs/cost/token-optimization-release-checklist.md`:40-53 — 12-row manual validation table has no counter-signature or date mechanism
  **Why**: Any maintainer can change all 12 "External validation required" rows to "Passed" in a single commit with no tooling challenge and no diff-visible record of who validated what and when. These 12 items cover exactly the runtime behaviors that static audit cannot prove.
  **Fix**: Add a `Validated by / Date` column, or add a signed-off block: `- [ ] All 12 items validated by: ______ on: ______`. Recording initials and date in each Status cell makes fraudulent sign-off visible in git blame. `[manual]`

---

## P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture/cg-documentation] `docs/workflow.md`:47 — `/cg-setup` scaffolding list omits `cost/` while the audit tool writes there by default
  **Why**: `docs/workflow.md` lists six scaffolded directories but not `cost/`. `cg_audit_context.py` defaults output to `.cg-docs/cost/`. `docs/reference.md` line 370 shows `cost/` in the directory tree, creating a discrepancy. Consumer projects may see a missing-directory error on first audit run.
  **Fix**: Add `cost/` to the scaffolding list in `docs/workflow.md`, or add a parenthetical noting it is created on first audit run. Verify whether `/cg-setup` actually creates `cost/`. `[manual]`

- **[P2.2]** [cg-architecture] `.github/skills/cg-skill-compound-docs/references/solution-schema.md` — `plan:` and `reviewed-in:` optional fields absent from solution schema
  **Why**: `plan:` appears in both new solution docs and cost artifacts; `reviewed-in:` appears in multiple solution files and is used by `cg-learnings-researcher`. Without schema documentation, future authors apply these inconsistently and tooling has no authoritative key.
  **Fix**: Add an "Optional Fields" subsection documenting `plan:` (path to source plan), `reviewed-in:` (path to review report), and `related:` (array of cross-links). `[manual]`

- **[P2.3]** [cg-adversarial/cg-reproducibility] `.cg-docs/cost/token-optimization-release-checklist.md`:58-64 — Command Set uses `python3` and `rg` without Windows PATH guidance
  **Why**: On default Windows installs, Python registers as `python` (not `python3`) and `rg` is not on PATH. A Windows maintainer gets "command not found" and may skip or misclassify gates as broken.
  **Fix**: Add a Windows callout: "**Windows**: Use `python` instead of `python3`. Install ripgrep via `scoop install ripgrep` or `winget install BurntSushi.ripgrep.MSVC`." `[manual]`

- **[P2.4]** [cg-reproducibility] `.cg-docs/cost/token-optimization-release-checklist.md`:33 — No Python environment/pytest version requirement documented
  **Why**: The `python3 -m pytest` gate requires `pytest` but no lockfile or version requirement exists. A fresh environment may lack `pytest` or have an incompatible version.
  **Fix**: Add to Command Set: "Requires `pytest` ≥ 7: `pip install pytest`." Longer term, add a `requirements-dev.txt` or `pyproject.toml` optional dependency. `[manual]`

- **[P2.5]** [cg-adversarial] `.cg-docs/cost/token-optimization-release-checklist.md`:21 — Stale-baseline trap when committed `context-audit.json` is used as `--baseline`
  **Why**: If a maintainer re-runs audit after committing changes, then uses the committed `context-audit.json` as `--baseline`, comparison is against the post-change state — producing zero delta and hiding regressions.
  **Fix**: Add a note: "If using `--baseline`, ensure the baseline JSON was captured before the current change set — never use the same-session output as both output and baseline. Consider naming baselines `context-audit-phaseN-baseline.json`." `[advisory]`

---

## P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.cg-docs/BRAIN.md`:17-20 — Topic 2 label spans multiple lines, breaking the pipe table
  **Why**: The cluster label for Topic 2 contains embedded newlines, violating Markdown pipe table syntax. GitHub and VS Code Preview will misparse the rows.
  **Fix**: Fix in `scripts/brain/renderer.py` — collapse newlines in topic labels before inserting into the table. Do not edit `BRAIN.md` directly; it is overwritten on rebuild. `[manual]`

- **[P3.2]** [cg-documentation] `docs/reference.md`:385 — `inbox/` directory has no documented producer
  **Why**: No command or workflow step identifies the mechanism that places files in `inbox/`. A new maintainer cannot determine if it is manual or automated.
  **Fix**: Add: "inbox items are placed here manually or captured during `/cg-strategy` sessions for later consideration; no command currently auto-populates this directory." `[manual]`

- **[P3.3]** [cg-documentation] `docs/model-guide.md`:76 — "Validation Guardrails" section missing cross-reference to workflow.md procedure
  **Why**: `model-guide.md` directs maintainers to the release checklist but does not link to the workflow.md 7-step Token Optimization Validation procedure.
  **Fix**: Add: "See the [Token Optimization Validation](workflow.md#token-optimization-validation) procedure in `workflow.md` for the full step-by-step process." `[safe_auto]`

- **[P3.4]** [cg-reproducibility] `.cg-docs/cost/token-optimization-release-checklist.md`:44 — Audit command omits `--output-dir`; inconsistent with canonical forms in `docs/workflow.md` and `docs/model-guide.md`
  **Why**: The checklist uses `python3 scripts/cg_audit_context.py --root . --format both` while both workflow.md and model-guide.md use `--output-dir .cg-docs/cost`. The checklist is the canonical reproduction document and should be explicit.
  **Fix**: Add `--output-dir .cg-docs/cost` to the checklist command. `[safe_auto]`

- **[P3.5]** [cg-reproducibility] `.cg-docs/cost/token-optimization-follow-ups.md` — Pester follow-up omits required Pester version
  **Why**: Project mandates Pester 4.10.1; Windows ships with built-in 3.4.0 which cannot run the suite.
  **Fix**: Append: "Requires Pester 4.10.1: `Install-Module Pester -RequiredVersion 4.10.1 -Force -SkipPublisherCheck -Scope CurrentUser`." `[advisory]`

- **[P3.6]** [cg-reproducibility] `.cg-docs/cost/token-optimization-release-checklist.md` — Timestamp regeneration produces expected but unexplained `git diff` noise
  **Why**: Every audit re-run changes the committed `context-audit.json` timestamp, creating a diff that reviewers must recognize as harmless.
  **Fix**: Add to Command Set: "Re-running the audit updates the `_Generated` timestamp in committed artifacts — this diff is expected and harmless." `[advisory]`

- **[P3.7]** [cg-architecture] `.cg-docs/cost/token-optimization-release-checklist.md`:1-16 — Intro describes three tiers but document has two sections
  **Why**: Intro says "static guardrails, Codex-side checks, and manual Copilot checks" (three tiers) but the Release Gates table mixes static and Codex rows without differentiation.
  **Fix**: Either split the Release Gates table at the static/Codex boundary, or revise the intro to "two sections: automated gates and manual VS Code/Copilot runtime checks." `[manual]`

- **[P3.8]** [cg-adversarial] `.cg-docs/cost/token-optimization-release-checklist.md`:5 — `scope: release-candidate` is an undocumented frontmatter field
  **Why**: This field appears in no documented schema and is not processed by current tooling. Benign now; could be silently ignored if future tooling extends to `.cg-docs/cost/`.
  **Fix**: Document `scope` as an allowed field, or remove it from the checklist frontmatter. `[advisory]`

- **[P3.9]** [cg-learnings-researcher] — `DIGEST.md` and `search-index.json` absent after adding new solution files
  **Why**: The learnings researcher checks these first (Tier 1/2). Their absence means new solutions fall through to slower full-scan retrieval. `cg-index --all` was not run (only `--brain`).
  **Fix**: After next `/cg-compound` or `/cg-brain-rebuild`, run `cg-index --all` from repo root. Post-merge housekeeping only. `[advisory]`

- **[P3.10]** [cg-version-control/cg-performance] `.cg-docs/brain-index.json` — Generated blob accumulation in git history
  **Why**: `brain-index.json` is ~549 KB per version; no action needed at current scale (~2 MB pack). Monitor growth.
  **Fix**: No action now. If loose-object size exceeds ~50 MB, run `git gc --aggressive`. Document a threshold in `docs/versioning.md`. `[advisory]`

- **[P3.11]** [cg-testing] `.cg-docs/cost/token-optimization-release-checklist.md`:51 — Pester gate evidence doesn't specify which `last-run.json` property confirms success
  **Why**: Evidence says "`tests/last-run.json` confirms success" without naming the property to inspect.
  **Fix**: Append to the Evidence cell: "…and `FailedCount` is `0` in the JSON output." `[advisory]`

- **[P3.12]** [cg-adversarial] `docs/reference.md`:207-212 — Explicit-mode paragraph documents a valid `light`-on-security escape route
  **Why**: No contradiction with routing contract (adversarial confirmed consistent). However, the documented behavior allows `/cg-review light` on release-automation diffs, bypassing `@cg-adversarial`.
  **Fix**: Add an explicit review-depth recommendation to the release checklist: "Review this checklist's PR with `/cg-review full`." `[advisory]`

- **[P3.13]** [cg-architecture] `docs/workflow.md` — `inbox/` policy documented reactively without workflow entry-point guidance
  **Why**: Three locations warn against treating inbox files as approved roadmap items but no workflow step describes when to use `inbox/` instead of `/cg-brainstorm`.
  **Fix**: Add one sentence to the `/cg-brainstorm` "When NOT to use" block pointing to `inbox/` for ideas not ready for structured clarification. `[advisory]`

- **[P3.14]** [cg-architecture] `.cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md` — Asymmetric `reviewed-in:` across new solution docs
  **Why**: The validation-pattern solution doc has `plan:` but no `reviewed-in:`; the evidence-quality solution doc has both. Produces an incomplete knowledge graph until P2.2 is addressed.
  **Fix**: Either add `reviewed-in:` to the first doc if applicable, or document the distinction in the schema (per P2.2). `[advisory]`

---

## ✅ Passed

- **cg-data-quality**: All counts internally consistent — `total_files: 83`, `total_tokens: 378,080`, `28 warnings`, `0 failures`, `0 premium usage`, `67 pytest tests` verified across `context-audit.json`, `context-audit.md`, checklist, and follow-ups.
- **cg-version-control**: No secrets, credentials, or PII. Committing generated `.cg-docs/` artifacts is correct per project policy. Clean commit on `main`.
- **cg-documentation** (routing consistency): No contradiction between `reference.md` new routing paragraph and the routing contract — both correctly document that explicit modes win.
- **cg-reproducibility**: No hardcoded absolute paths, no RNG/seeds, Pester safe-runner correctly mandated, ad hoc `Invoke-Pester` explicitly prohibited in checklist.
- **cg-performance**: No performance anti-patterns; `brain-index.json` well within git pack limits.
- **cg-learnings-researcher**: All applicable past learnings correctly applied — harness-specific status labels, Pester safe-runner mandated, `.cg-docs/` not gitignored, evidence-type separation documented.
