---
date: 2026-08-07
depth: light
parent-review: .cg-docs/reviews/2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md
type: verification
findings:
  P2.1: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
  P3.13: fixed
  P3.14: fixed
  P3.15: fixed
  P3.16: fixed
---

## Review Report

**Review mode**: light (verify pass, mode:verify)
**Files reviewed**: 10 changed paths (generated `.cg-docs/views/**` bodies excluded)
**Findings**: 17 (P0: 0, P1: 0, P2: 1, P3: 16)

### Verification mode context

This is a verify pass following fix-triage. The most recent prior review with
`fixed` findings is `2026-08-03-editorial-theme-publishing-workflow-evidence-v2-review.md`
(frontmatter date 2026-08-04; 13 findings marked fixed). Per the suppression
policy, P2/P3 findings are suppressed only when they target a function or block
explicitly listed as `fixed` in the prior review's `findings:` map. None of the
prior review's fixed findings target this diff (the Stage 2 readiness validator
is a different code area), so suppression is inert and all findings are reported.

### P0 — BLOCKING

None.

### P1 — CRITICAL

None.

### P2 — IMPORTANT

- **[P2.1]** [cg-code-quality] `scripts/issues/readiness.py:711` — `_repo_owner_name` uses a bare `json.loads(out)` instead of the class's `_parse_json`, so malformed `gh repo view` stdout raises an uncaught `json.JSONDecodeError` → traceback and exit 1.
  **Why**: Violates the documented exit-code contract (API/config failures must use exit 4/3) and contradicts the hardening claim that uncaught `json.JSONDecodeError` paths map to exit 4. Reachable on any live `--issue` run.
  **Fix**: `data = self._parse_json(out, "repo")`.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `docs/copilot-readiness.md:86` — Risk-class rule wording disagrees with the implementation ("first occurrence of low/medium/high" vs. only a line whose entire content is exactly the token).
  **Why**: As the canonical contract, the sentence misleads issue authors writing the Risk class section.
  **Fix**: Rephrase to "A line whose content is exactly `low`, `medium`, or `high` (optionally wrapped in backticks); prose such as 'low confidence' is rejected."

- **[P3.2]** [cg-code-quality] `scripts/issues/readiness.py:318-321` — `_has_blocking_dependency` masks a real blocker when `not blocked by` and `blocked by` appear on the same line.
  **Why**: Probe: `"This is not blocked by A but is blocked by B"` → not blocking → potential false-READY for R014.
  **Fix**: Match negation on the same phrase or parse per-clause.

- **[P3.3]** [cg-code-quality] `scripts/issues/readiness.py:91-92` — Checkbox regexes require whitespace after `]`, so a bare `- [ ]` item goes undetected.
  **Why**: Possible false-READY for R014 (and bare `- [x]` not counted for R006).
  **Fix**: Allow end-of-line: `r"^\s*[-*]\s*\[([ xX])\](?:\s+|$)"` (and same for `UNCHECKED_BOX_RE`).

- **[P3.4]** [cg-code-quality] `scripts/issues/readiness.py:658-662` — `pr list` is capped at `--limit 100`.
  **Why**: A closing PR beyond the first 100 open PRs is silently invisible to R020 → silent false-READY potential.
  **Fix**: Paginate over `pr list` and document the body-keyword-only scope for R020.

- **[P3.5]** [cg-code-quality] `scripts/issues/readiness.py:1009,1033-1037,980-983` — Dead `err` parameter; argparse usage errors route to the real stderr and are not capturable.
  **Fix**: Thread `err` into `build_parser`/`_ReadinessArgumentParser` or remove it.

- **[P3.6]** [cg-code-quality] `scripts/issues/readiness.py:172-194,196-234,325-347` — Three independent fence-state machines with subtly different semantics.
  **Why**: Duplicated logic invites divergence.
  **Fix**: Extract one shared generator.

- **[P3.7]** [cg-code-quality] `scripts/issues/readiness.py:449-613` — `validate_contract` repeats the section-status idiom (5+ copies; R015–R018 identical).
  **Fix**: Add `_section_detail(sec)` and data-drive the nonempty rules.

- **[P3.8]** [cg-code-quality] `scripts/issues/readiness.py:24-31` — Stdlib import order not alphabetical. Cosmetic consistency.
  **Fix**: Reorder imports.

- **[P3.9]** [cg-code-quality] `scripts/issues/readiness.py:938` — `render_human` renders "Issue #None" on the fixture-load-failure path.
  **Fix**: Omit the `Issue #None:` prefix when `result.issue is None`.

- **[P3.10]** [cg-testing] `scripts/issues/readiness.py:737-749` — `_default_run_gh` (the only real subprocess boundary) has no direct test.
  **Why**: argv-safety (no `shell=True`) and FileNotFoundError/TimeoutExpired branches are never exercised; a regression here would pass the suite.
  **Fix**: Add one unit test monkeypatching `subprocess.run` to assert argv-list form, `FileNotFoundError` → `ConfigError`, and `TimeoutExpired` → `ApiError`.

- **[P3.11]** [cg-testing] `scripts/issues/readiness.py:780-790` — `FixtureClient` malformed-JSON and missing-`bodyFile` error branches are untested.
  **Fix**: Add two CLI cases (invalid JSON; valid JSON with missing `bodyFile`) each asserting `EXIT_CONFIG`.

- **[P3.12]** [cg-testing] `scripts/tests/test_issue_readiness.py` — R013, R015, R016, R017, R018 have no dedicated failure test.
  **Fix**: Parametrize one test over the five section names (absent/empty variants) asserting `EXIT_NOT_READY`.

- **[P3.13]** [cg-testing] `scripts/tests/test_issue_readiness.py` — No test for a fully empty/whitespace-only issue body.
  **Fix**: Add a case asserting all R001–R018 fail and `ready is False`.

- **[P3.14]** [cg-testing] `scripts/tests/test_issue_readiness.py:11` — `import re` is unused.
  **Fix**: Drop the import.

- **[P3.15]** [cg-testing] `.github/workflows/tests.yml:46` vs stated baseline — Native target Python gate pins `python-version: "3.11"` while the review brief states 3.12; `docs/copilot-readiness.md` does not state the "~103" test count.
  **Why**: Version/claim inconsistencies mislead the next reviewer/operator (no functional risk; suite passes on both).
  **Fix**: Align the pin with the stated baseline and add the test count to the Testing section.

- **[P3.16]** [cg-testing] `scripts/tests/test_issue_readiness.py` — argparse non-integer `--issue abc` (→ `EXIT_CONFIG`), and `render_human`'s `CANNOT COMPLETE (config)` / `(api/network)` labels are untested.
  **Fix**: Add `--issue abc` case and two `main(...)` cases asserting the config/api labels in human output.

### ✅ Passed

- `@cg-code-quality`: No P0/P1; docstring security claims (read-only by construction, argv-safe invocation, untrusted-body handling) verified accurate.
- `@cg-testing`: No P0/P1/P2; suite hermetic, deterministic, cross-platform clean; 103 passed exactly as the gate invokes it.

## Validation

- `python -m pytest scripts/tests/test_issue_readiness.py -q` — 103 passed (0.11s, verified by @cg-testing).
- No live GitHub interaction in the suite (only injected fake clients and offline fixtures).
- `.cg-docs/views/**` bodies not read per scope.

Parsed 17 finding IDs. If count differs from total findings above, some IDs may be non-standard.
