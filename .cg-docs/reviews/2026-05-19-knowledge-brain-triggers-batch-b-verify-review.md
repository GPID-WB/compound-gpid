---
date: "2026-05-19"
depth: light
parent-review: .cg-docs/reviews/2026-05-19-knowledge-brain-triggers-batch-b-review.md
type: verification
findings:
  P2.1: open
  P2.2: open
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: advisory
---

## Review Report (Verify Pass)

**Review depth**: light (verify mode)
**Files reviewed**: 7
**Findings**: 8 (P0: 0, P1: 0, P2: 4, P3: 4)

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/cg-index.Tests.ps1:651–665` — P1.1 ImportError tests are static source-only assertions, not behavioral
  **Why**: Both tests match strings in `cg_index.py` source but do not verify that invoking `cg-index --brain` in an environment where `brain` is absent actually exits 1 and emits the expected message. A misindented `except`, a silent swallow, or a return-0 refactor all pass the current tests.
  **Fix**: Add a `Describe "cg-index.py --brain ImportError runtime behavior"` block that shadows the `brain` package (e.g., `PYTHONPATH` pointing to an empty directory) and asserts `$LASTEXITCODE -eq 1` plus `$stderr -match 'brain package not available'`.
  **Tag**: [manual]

- **[P2.2]** [cg-testing] `tests/cg-index.Tests.ps1` — P1.2 (legacy deletion outside try block) has zero behavioral test coverage
  **Why**: No test verifies that when `DIGEST.md` cannot be deleted, the command still returns 0 and stderr contains `WARNING:` (not `ERROR:`). The whole rationale for P1.2 was to prevent false exit-1; without a behavioral test a future regression would be invisible.
  **Fix**: Add an `It` block that marks `DIGEST.md` read-only in the fixture, runs `--brain`, asserts `$LASTEXITCODE -eq 0` and `$stderr -match 'WARNING'`.
  **Tag**: [manual]

- **[P2.3]** [cg-code-quality] `.github/prompts/cg-brain-rebuild.prompt.md:90` — Step 3 preamble says "two most likely causes" but now lists three bullets
  **Why**: P2.10 added a third `/cg-setup` bullet without updating the count. Users reading "two" may miss the third item; it signals incomplete editing.
  **Fix**: Change `"two most likely causes"` → `"three most likely causes"`.
  **Tag**: [safe_auto]

- **[P2.4]** [cg-code-quality] `docs/reference.md` — `/cg-brain-rebuild` artifact list omits partition files
  **Why**: The new reference entry lists only `` `BRAIN.md` + `brain-index.json` ``. P2.7 documented `BRAIN-01.md`, `BRAIN-log.md` as concrete partition names in the prompt; the reference doc was not updated to match. Cross-file inconsistency introduced during fix-triage.
  **Fix**: Expand the artifact list to `` (`BRAIN.md` + `BRAIN-NN.md` partitions + `BRAIN-log.md` + `brain-index.json`) ``.
  **Tag**: [safe_auto]

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-compound-refresh.prompt.md:~143` — Step 7 artifact description omits partition files
  **Why**: P2.8 updated `--all` → `--brain` and changed `search-index.json`/`DIGEST.md` to `brain-index.json`/`BRAIN.md`, but did not add `BRAIN-NN.md`/`BRAIN-log.md`. Creates drift between `cg-compound-refresh` and `cg-brain-rebuild` descriptions.
  **Fix**: Update Step 7 artifact line to match: `BRAIN.md`, `BRAIN-NN.md` partitions, `BRAIN-log.md`, `brain-index.json`.
  **Tag**: [safe_auto]

- **[P3.2]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` — no test for `/cg-setup` recommendation in Step 3 error guidance (P2.10 fix)
  **Why**: The existing `'\.cg-docs|project root'` test was already satisfied before P2.10 and does not verify the new bullet. Removing `/cg-setup` from Step 3 would not fail any test.
  **Fix**: Add `It "includes /cg-setup recommendation in Step 3 error handling" { ($content -match '/cg-setup') | Should -Be $true }` to the `cg-brain-rebuild.prompt.md - content` block.
  **Tag**: [safe_auto]

- **[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1:~4896` — PATH-error test regex `'not on PATH|cg-index --version|not available'` overly broad
  **Why**: The `not available` branch is trivially satisfied by `"brain package not available"` from the ImportError documentation, so the test passes even if PATH-specific guidance is entirely absent.
  **Fix**: Tighten to `'not on PATH|cg-index --version'` (drop the `not available` branch).
  **Tag**: [safe_auto]

- **[P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `docs/model-guide.md` registration test checks filename presence only, not model association
  **Why**: A comment or heading containing `cg-brain-rebuild.prompt.md` would satisfy the assertion without the entry being a proper model-assignment table row.
  **Fix**: Strengthen to `($content -match 'cg-brain-rebuild\.prompt\.md.*Claude')` or assert both the filename and `Claude Sonnet` appear on the same line.
  **Tag**: [advisory]

---

### ✅ Passed

- cg-code-quality: `scripts/cg_index.py` ImportError + legacy-deletion handlers are structurally correct; exception ordering (ImportError before OSError) is idiomatic
- cg-code-quality: `cg-compound-refresh.prompt.md` `--all` → `--brain` replacement is consistent (both File Permissions and Step 7 updated)
- cg-code-quality: `docs/model-guide.md` entry format matches surrounding table rows
- cg-testing: P2.3–P2.6 + P3.1 test assertions in `prompt-tools.Tests.ps1` are non-trivially specific
- cg-testing: P2.11 `docs/reference.md` and `docs/model-guide.md` tests correctly use `Get-Content … -Raw`
