---
date: 2026-05-22
plan: .cg-docs/plans/2026-05-22-compound-research-phase8-integration-docs.md
commit: 4212f5f
depth: standard
findings:
  P0.1: open
  P1.1: open
  P1.2: open
  P2.1: open
  P2.2: open
  P2.3: open
  P3.1: open
  P3.2: open
  P3.3: open
---

## Review Report

**Review depth**: standard (no `compound-gpid.local.md` — defaulted)  
**Commit**: `4212f5f` — `fix(compound-research): address Phase 8 review findings`  
**Files reviewed**: 7 (`scripts/update.sh`, `docs/workflow.md`, `compound-gpid.md`, `README.md`, `docs/context-files.md`, `.cg-docs/DIGEST.md`, `.cg-docs/reviews/…-review.md`)  
**Auto-escalation**: `scripts/` directory → `@cg-data-quality` always added (already in standard)  
**Findings**: 9 (P0: 1, P1: 2, P2: 3, P3: 3)

---

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-data-quality / cg-code-quality / cg-architecture] `scripts/update.sh:82` — `extract_fm_value` regex silently fails for any value containing letters `r` or `n`  
  **Why**: The pattern `r':\s*["\']?([^"\'\\r\\n]+)["\']?\s*$'` is a Python raw string. In it, `\\r` is literal `\` + `r` and `\\n` is literal `\` + `n`, not escape sequences. The regex engine therefore interprets `[^"\'\\r\\n]` as "not double-quote, not apostrophe, not backslash, **not letter-r**, **not letter-n**". Every real-world config value contains one or both: `"engineering"` (has `r`, `n`), `"research"` (has `r`, `n`), `"engineering, research"` (same), `"R, Python"` (has `n`), `"standard"` (has `r`, `n`), `"tidyverse"` (has `r`). All return `''`, and the `or '<not configured>'` / `or 'engineering'` fallback always fires. **The research module cannot be activated via `cg-update`; `language`, `review-depth`, and `r-syntax` silently show `<not configured>` for most real values.** This bug was pre-existing in `update.sh`; it is surfaced by this commit because `modules` was added using the same broken function.  
  **Fix**: Replace line 82 with the pattern used in `link.sh` (which was correctly fixed previously):  
  ```python
  pattern = r'(?m)^\s*' + re.escape(key) + r':\s*["\x27]?([^"\x27\r\n]+)["\x27]?\s*$'
  ```
  `\x27` is hex for apostrophe (no raw-string ambiguity); `\r\n` with a single backslash in a raw string passes the regex engine `\r` and `\n` (carriage return / newline), not the letters.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality] `scripts/update.sh:102–106` — VALID_MODULES allowlist validation is inoperative  
  **Why**: Because `extract_fm_value` always returns `''` for any modules value, the `or 'engineering'` fallback fires before validation. The variable reaching `VALID_MODULES` is always `'engineering'` (always valid). A user with `modules: "production"` or `modules: "resarch"` (typo) gets silently wrong output — engineering mode — with no error.  
  **Fix**: Fix P0.1. Validation logic is correct once extraction works.

- **[P1.2]** [cg-testing] `tests/bash-scripts.Tests.ps1` — modules tests for `update.sh` use a corrected regex not present in the code, masking the P0 bug  
  **Why**: The test creates a temporary Python script with `r'[^"\x27\r\n]+'` (correct), not the `r'[^"\'\\r\\n]+'` in `update.sh`. This produces a false-positive pass. `update.Tests.ps1` has zero coverage of the Python heredoc.  
  **Fix**: After fixing P0.1, add integration tests that call `generate_copilot_instructions` from `update.sh` directly with `modules: "research"` and `modules: "engineering, research"` fixtures and assert the correct substitution in output.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture] `scripts/update.sh` / `scripts/link.sh` — Python heredoc duplicated; Windows is already DRY  
  **Why**: `generate_copilot_instructions` logic lives in `update.sh` (Python heredoc), `link.sh` (Python heredoc), and `helpers.ps1` (PowerShell function, shared via dot-source). The Windows side uses a single shared file; the Unix side copies. The P0 bug is a direct consequence — the regex fix was applied to `link.sh` but not propagated to `update.sh`. Any future change to `VALID_MODULES` or substitution logic must be applied twice.  
  **Fix**: Extract to `scripts/helpers.sh` and source from both scripts, mirroring the Windows pattern.

- **[P2.2]** [cg-architecture / cg-data-quality] `scripts/update.sh:63` — Python heredoc call missing `|| { }` error trap  
  **Why**: `link.sh` wraps the `python3 - ... <<'PYEOF'` call with `|| { print_error "Failed to generate copilot-instructions.md from template."; exit 1 }`. `update.sh` has no such handler. When Python exits non-zero, `set -euo pipefail` aborts silently — no user-facing diagnostic.  
  **Fix**: Add the same trap:  
  ```bash
  python3 - "$template_path" "$project_root" "$marker" <<'PYEOF' || {
      print_error "Failed to generate copilot-instructions.md from template."
      exit 1
  }
  ```

- **[P2.3]** [cg-version-control] `.cg-docs/reviews/2026-05-22-compound-research-phase8-integration-docs-review.md` — frontmatter marks findings `resolved` but body's summary table shows `open`  
  **Why**: Cosmetic inconsistency only, but a reader consulting the Findings Summary table at the bottom of the review report sees conflicting status signals.  
  **Fix**: Update the table's status column to match the frontmatter (`resolved`/`deferred`).

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-architecture] `scripts/update.sh:90` — `r_syntax` read before VALID_MODULES check; `link.sh` reads it after  
  **Why**: Minor ordering inconsistency, adds audit overhead when comparing files for parity.  
  **Fix**: Move `r_syntax = extract_fm_value(...)` to after the `VALID_MODULES` block.

- **[P3.2]** [cg-architecture] `scripts/update.sh:72` — `extract_fm_value` missing docstring and regex-rationale comment  
  **Why**: `link.sh` documents both the function contract and why `\x27`/`\r\n` are used. The absence of this comment is causally related to P0.1 — whoever ported the function used a different (broken) form.  
  **Fix**: Copy docstring and regex comment from `link.sh`.

- **[P3.3]** [cg-performance] `scripts/update.sh` — `extract_fm_value` re-reads config file from disk once per key call (5× total)  
  **Why**: Negligible for a one-time generation script on KB-range files.  
  **Fix**: Optional — cache file read at top of script.

---

### ✅ Passed

- **cg-documentation**: All documentation changes in this commit are accurate and complete. Dispatch table, YAML warning, plan-review note, and P0 clarification all verified correct.
- **cg-version-control**: No secrets committed, conventional commit format correct, branch hygiene sound. All prior review findings confirmed applied correctly.
- **cg-reproducibility**: No absolute paths, no non-deterministic operations, portable path handling. Python heredoc reads are `utf-8` explicit. No new issues beyond the regex P0 (overlapping with cg-data-quality).
- **cg-performance**: No meaningful performance concerns for a one-time generation script.

---

> Review report saved to `.cg-docs/reviews/2026-05-22-compound-research-phase8-integration-docs-review-2.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (e.g., `/cg-fix-triage P0.1 P1.1`) or by priority level (e.g., `/cg-fix-triage P0`).
