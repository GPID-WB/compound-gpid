---
date: 2026-06-11
depth: light
parent-review: .cg-docs/reviews/2026-06-11-github-issues-integration-review-2.md
type: verification
findings:
  P3.1: fixed
---

## Review Report

**Review mode**: light (verify pass)
**Files reviewed**: 4 (`.github/prompts/cg-issues.prompt.md`, `.github/agents/cg-roadmap.agent.md`, `docs/troubleshooting.md`, `docs/reference.md`, `tests/prompt-tools.Tests.ps1`, `tests/roadmap.Tests.ps1`)
**Findings**: 1 (P0: 0, P1: 0, P2: 0, P3: 1)
**Verified fixes**: 13/13

---

### ✅ All Prior Findings Verified

| Finding ID | Description | Verification |
|------------|-------------|--------------|
| P1.1 | Triple-backtick escape before fenced block insertion | ✅ Present in both Step 6 and Safety Rules |
| P1.2 | Resolve-Path/readlink -f tool call for symlink traversal | ✅ Mandatory tool-call language present |
| P1.3 | labelPrefix shell-safety validation regex in Configure operation | ✅ Correct location; step numbering 1–7 intact |
| P1.4 | `in-progress` → `active` in troubleshooting.md | ✅ Zero `in-progress` occurrences remaining |
| P2.1 | TOCTOU stop with 3 user choices before @cg-roadmap dispatch | ✅ Hard stop + all 3 choices + dispatch gate present |
| P2.2 | Safety Rules blocklist synced with step 6 | ✅ `Assistant:`, `[INST]`, `###` present in both locations |
| P2.3 | labelPrefix Default `—` (not `""`) in reference.md | ✅ Em dash with "absent/null means no prefix" note |
| P2.4 | Duplicate Describe block removed from prompt-tools.Tests.ps1 | ✅ Single block at line 2092 using `$content` |
| P2.5 | Graceful degradation test moved to confirmation/safety Describe | ✅ At line 6218 in correct block; absent from pre-flight |
| P2.6 | Test: strips `Closes #`/`Fixes #`/`Resolves #` from titles | ✅ At line 6224 in confirmation/safety block |
| P2.7 | Test: untrusted content rendered in fenced `text` block | ✅ At line 6228; matches actual prompt instruction |
| P3.5 | Over-broad `read.?only.*status.*mode` regex arm removed | ✅ Arm absent; `Status mode is read.?only` is sole pattern |
| P3.6 | "WHEN FIXING THIS GAP" comment in roadmap.Tests.ps1 | ✅ Present at line 1438 before assertion block |

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/agents/cg-roadmap.agent.md` Configure GitHub Issues step 3 — regex `^[A-Za-z0-9_. :/-]*$` contains the sequence `/-` which is an invalid character range in strict regex engines (POSIX, Python `re`, JavaScript). `/` is ASCII 47, `-` is ASCII 45; since 47 > 45, the range is invalid and raises an error if executed as code. As prose in an agent spec the LLM reads intent rather than executing the regex, so runtime risk is zero. However, if this pattern is ever copy-pasted into validation code it will fail.
  **Why**: `/-` at the end of `[...:/-]` is parsed as the range from `/` (47) to `-` (45), which is invalid.
  **Fix**: Move `-` to the very end of the character class: `^[A-Za-z0-9_. :/\-]*$` or `^[-A-Za-z0-9_. :/]*$`.
  **Tag**: `[advisory]`

---

### ✅ No Cross-File Breakage

No regressions detected across all changed files. The pre-flight Describe block in `tests/prompt-tools.Tests.ps1` retains full appropriate coverage after P2.5 move. No `It` blocks were accidentally removed from unrelated Describe blocks.

---

*Parsed 1 finding ID. Verify pass complete — cycle has converged on all P1/P2 issues.*
