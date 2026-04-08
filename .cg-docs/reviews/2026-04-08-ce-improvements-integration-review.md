---
plan: .cg-docs/plans/2026-04-08-ce-improvements-integration.md
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
---

## Review Report

**Review depth**: thorough  
**Branch**: dev/ce-improvements  
**Files reviewed**: 17  
**Agents dispatched**: cg-version-control, cg-testing, cg-documentation, cg-architecture, cg-learnings-researcher  
**Findings**: 3 P1, 5 P2, 1 P3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** cg-review `.github/prompts/cg-review.prompt.md` — Step 2.5 quality gate excludes P0
  **Why**: The Presence check reads `Contains at least one **[P1.`/`**[P2.`/`**[P3.` entry`. An agent that returns ONLY P0 findings (e.g., cg-version-control finds committed credentials) matches none of those patterns and gets logged as producing unusable output — the worst possible inversion.
  **Fix**: Update the Presence check in Step 2.5 to:
  ```
  - **Presence**: Contains at least one `**[P0.`/`**[P1.`/`**[P2.`/`**[P3.` entry, OR an explicit "no issues found" statement.
  ```
  *(Flagged by: cg-testing, cg-documentation, cg-architecture)*

- **[P1.2]** cg-fix-triage `.github/prompts/cg-fix-triage.prompt.md` — P0 absent from fix application order and priority-level examples
  **Why**: Two gaps: (1) Step 2 priority-level example shows `(e.g., P1, P2, P3)` — users won't discover `/cg-fix-triage P0`; (2) Step 3 apply-fixes ordering says `P1 first, then P2, then P3` — P0 is skipped. A genuine P0 (credential exposure, data corruption) has no guaranteed first-fix semantics.
  **Fix**:
  - Step 2: change example to `(e.g., P0, P1, P2, P3)`
  - Step 3: change to `in order (P0 first, then P1, then P2, then P3)`
  *(Flagged by: cg-testing, cg-architecture)*

- **[P1.3]** cg-compound `.github/prompts/cg-compound.prompt.md` — Severity field template omits P0
  **Why**: The solution document severity template shows `"<P1|P2|P3>"`. Users capturing solutions for blocking issues (credential exposure, data corruption) have no valid option in the template.
  **Fix**: Update severity field to `"<P0|P1|P2|P3>"`.
  *(Flagged by: cg-testing, cg-documentation)*

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** cg-review `.github/prompts/cg-review.prompt.md` — YAML frontmatter example in Step 3.5 missing P0
  **Why**: The example `findings:` map shows `P1.1: open`, `P2.1: open`, `P2.2: open` — no P0 example. New users won't know P0 findings appear in the frontmatter.
  **Fix**: Add `P0.1: open` as the first entry in the example YAML block.
  *(Flagged by: cg-documentation)*

- **[P2.2]** compound-gpid.md `compound-gpid.md` — Constraints section still describes 3-tier priority system
  **Why**: The Constraints section reads `P1 (security, data corruption, incorrect results) blocks merge; P2 (performance, tests, docs) should be fixed; P3 is advisory` — the P0 tier is absent from the authoritative project charter.
  **Fix**: Update to: `P0 blocks everything (security, PII, data corruption, incorrect published output); P1 blocks merge (correctness, validation); P2 should be fixed (performance, tests, docs); P3 is advisory.`
  *(Flagged by: cg-documentation)*

- **[P2.3]** copilot-instructions.md `.github/copilot-instructions.md` vs. agent files — P0 definition wording diverges
  **Why**: `copilot-instructions.md` says "incorrect statistical results **affecting published outputs**"; all 8 agent files say "incorrect statistical results" (no qualifier). An agent could reasonably downgrade corruption of intermediate datasets to P1 under the agent definition, while the project definition would call it P0.
  **Fix**: Align the wording. The broader agent-file version (no qualifier) is safer. Remove "affecting published outputs" from `copilot-instructions.md` to match the agent files.
  *(Flagged by: cg-architecture)*

- **[P2.4]** cg-skill-compound-docs `.github/skills/cg-skill-compound-docs/` — P0 option missing from skill files
  **Why**: Two files don't yet know about P0: `references/solution-schema.md` shows `severity: "P1"  # P1 | P2 | P3`; workflow capture instructions say "Set severity based on impact (P1/P2/P3)".
  **Fix**: Update both files to include P0 in the severity options and comments.
  *(Flagged by: cg-documentation)*

- **[P2.5]** version-control — Branch name `dev/ce-improvements` does not follow project convention
  **Why**: Project convention (documented in `copilot-instructions.md`) is `type/short-description` where `type` is `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `data`, or `analysis`. The prefix `dev/` is not a recognized type.
  **Fix**: Rename to `feat/ce-improvements` before merging.
  *(Flagged by: cg-version-control)*

---

### P3 — MINOR (nice to have)

- **[P3.1]** docs/reference.md `docs/reference.md` — No standalone priority-system table in docs
  **Why**: The P0/P1/P2/P3 severity definitions exist in `copilot-instructions.md` (a config file) but not in any `docs/` file. New contributors must discover this from the config rather than the reference docs.
  **Fix**: Add a "Priority Levels" section to `docs/reference.md` with the 4-tier table (P0 = BLOCKING, P1 = CRITICAL, P2 = IMPORTANT, P3 = MINOR).
  *(Flagged by: cg-architecture)*

---

### ✅ Passed

- **cg-architecture**: All 8 review agents correctly use `**[P0|P1|P2|P3]**` — verified consistent
- **cg-data-quality**: No data pipeline code changed — N/A
- **cg-performance**: No performance-sensitive code changed — N/A
- **cg-reproducibility**: No environment/lockfile changes — N/A
- **cg-version-control**: Commit messages follow conventional commits format; no sensitive data; .gitignore complete
- **cg-testing**: Regex `[P[0123]` is correct and sufficient; em-dash fix in Run-Tests.ps1 is correct; all 264 tests pass
- **cg-documentation**: All 8 agent files, `copilot-instructions.md`, `docs/reference.md`, `docs/workflow.md`, `cg-review.prompt.md` correctly updated
- **cg-learnings-researcher**: Past learnings confirm: single-source-of-truth for tier definitions (P2.3 above), encoding safety in .ps1 files (addressed by the Run-Tests.ps1 fix), and Pester safety rules (no regressions introduced)
