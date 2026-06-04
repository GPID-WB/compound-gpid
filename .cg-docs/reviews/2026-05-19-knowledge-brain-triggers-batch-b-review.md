---
plan: .cg-docs/plans/2026-05-19-knowledge-brain-triggers-batch-b.md
findings:
  P1.1: fixed
  P1.2: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: advisory
  P3.4: advisory
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 7 (`.github/prompts/cg-brain-rebuild.prompt.md`, `.github/copilot-instructions.md`, `.github/prompts/cg-compound.prompt.md`, `tests/prompt-tools.Tests.ps1`, `tests/model-assignments.Tests.ps1`, `roadmap.json`, `.cg-docs/plans/2026-05-19-knowledge-brain-triggers-batch-b.md`)
**Findings**: 16 (P0: 0, P1: 2, P2: 10, P3: 4)

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `scripts/cg_index.py` — `ImportError` not caught; misleading error guidance
  **Why**: The `from brain import build_brain` import is inside a `try/except OSError` block. A partial install or corrupted `sys.path` raises `ImportError`, which escapes the handler, produces an unhandled Python traceback, and exits 1. The prompt's Step 3 then fires and tells the user to "check cg-index PATH or run from project root" — neither of which is the problem. User chases wrong root cause.
  **Fix**: Broaden the except to `except (OSError, ImportError)` or add a pre-flight `importlib.util.find_spec("brain")` check that emits a clean `"brain package not found; reinstall compound-gpid"` message before attempting the import.
  **Tag**: [manual] — catch clause must be deliberately widened without masking real errors.

- **[P1.2]** [cg-adversarial] `scripts/cg_index.py` — legacy deletion inside brain `try` block causes exit 1 after successful build
  **Why**: `legacy_path.unlink()` is inside the same `try/except OSError` block as `build_brain()`. If the file is locked (AV scanner, another process — common on Windows), `unlink()` raises `OSError`, the except handler fires, and `return 1` is issued — even though `BRAIN.md` was written successfully and the stats line was already printed to stdout. The prompt's Step 2 hierarchy trusts exit code as primary signal, so it skips the secondary check entirely and reports failure to the user.
  **Fix**: Move the legacy deletion loop outside (after) the `try/except` block, or wrap it in its own `try/except` that only warns rather than returning 1. Brain build success/failure must not be conflated with legacy cleanup success.
  **Tag**: [safe_auto]

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `cg-brain-rebuild.prompt.md:40-46` — Secondary tier: no fallback when stats line absent despite exit 0
  **Why**: Step 2.2 says "If found, parse counts." It never says what to do if exit code is 0 but `[cg-index] Brain index written to` is NOT found. The success report template leaves X/Y/Z unfilled, or the model guesses/hallucinates them.
  **Fix**: Add after "If found…": "If the stats line is not found despite exit 0, report counts as 'unavailable' and note that the brain was rebuilt but metrics could not be parsed from output."
  **Tag**: [manual]

- **[P2.2]** [cg-code-quality] `cg-brain-rebuild.prompt.md:49-51` — Tertiary tier: no action when `BRAIN.md` absent post-exit-0
  **Why**: "Confirm `.cg-docs/BRAIN.md` exists as a sanity check" — but if it's missing after exit 0 and stats line found, the prompt gives no instruction. Silently proceeding hides a write failure.
  **Fix**: Add: "If `BRAIN.md` is absent despite a successful exit, warn: 'BRAIN.md not found despite a successful run — re-run or check write permissions in `.cg-docs/`'."
  **Tag**: [manual]

- **[P2.3]** [cg-testing + cg-code-quality] `tests/prompt-tools.Tests.ps1` — Missing `model:` assertion in `cg-brain-rebuild.prompt.md - frontmatter` block
  **Why**: Every comparable frontmatter block in the suite tests both `description:` and `model:`. The new block only tests `description:` and `tools:` absence. A typo silently removing `model:` would not be caught (except by the model-assignments sentinel — too coarse).
  **Fix**: Add `It "has a model in frontmatter" { $frontmatter | Should -Match 'model:' }`.
  **Tag**: [safe_auto]

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Missing `Step 0 Get Bearings` test in content block
  **Why**: `cg-commit-push-pr` and `cg-verify-pr` (and others) assert `($content -match '### Step 0')`. The `cg-brain-rebuild.prompt.md` follows the same pattern but the new content block does not test for it.
  **Fix**: Add `It "has Step 0 Get Bearings" { ($content -match '### Step 0') | Should -Be $true }`.
  **Tag**: [safe_auto]

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for secondary stdout success signal
  **Why**: The prompt's most distinctive design is the tiered verification. The secondary pattern `[cg-index] Brain index written to` is tested in neither the content block nor elsewhere. Editing it out would silently break the parsing logic with no test failure.
  **Fix**: Add `It "documents the secondary stdout success pattern" { ($content -match '\[cg-index\] Brain index written to') | Should -Be $true }`.
  **Tag**: [safe_auto]

- **[P2.6]** [cg-documentation] `cg-brain-rebuild.prompt.md` — Missing "When to Use" section
  **Why**: The prompt dives straight into process with no guidance on when to invoke `/cg-brain-rebuild` directly vs. relying on the implicit rebuild in `/cg-compound`. For the target audience (economists who won't read both prompt internals), the standalone use case is invisible.
  **Fix**: Add a `## When to Use` section listing standalone triggers: after pulling `.cg-docs/` changes from collaborators, after batch-editing solution files manually, after a `/cg-compound` run that skipped brain rebuild (e.g., `cg-index` unavailable), or when the brain is stale after a failed run.
  **Tag**: [manual]

- **[P2.7]** [cg-documentation] `cg-brain-rebuild.prompt.md:57` — "partition files" is undefined jargon
  **Why**: The success report template says `"+ partition files and brain-index.json"`. "Partition files" has no prior definition in the prompt. A junior developer or economist cannot verify the output manually.
  **Fix**: Replace with concrete filenames matching what `renderer.py` actually writes.
  **Tag**: [safe_auto]

- **[P2.8]** [cg-architecture] `.github/prompts/cg-compound-refresh.prompt.md:16,143-144` — References deprecated `--all` and stale artifact names `DIGEST.md` / `search-index.json`
  **Why**: After any brain rebuild, `DIGEST.md` and `search-index.json` no longer exist. `cg-compound-refresh.prompt.md` still tells users these files are updated. `--all` is marked deprecated in `cg_index.py` (deprecated alias for `--brain`). Creates user confusion when the tool reports updating files that don't exist.
  **Fix**: Replace `cg-index --all` → `cg-index --brain` (both occurrences: File Permissions and Step 7). Update the Step 7 artifact description to reference `BRAIN.md` and `brain-index.json`.
  **Tag**: [safe_auto]

- **[P2.9]** [cg-adversarial] `cg-brain-rebuild.prompt.md` — Zero-entity "success" reported without warning
  **Why**: On a brand-new project with an empty `.cg-docs/solutions/`, `build_brain()` returns 0 entities, exit code 0, stats line present. The prompt reports "Brain rebuild complete. 0 entities indexed" without flagging that the brain is empty. The user concludes it's working when it's a no-op.
  **Fix**: Add a guard in Step 2 secondary: if entity count is 0, emit an advisory: "No entities indexed — check that `.cg-docs/solutions/` contains at least one captured solution, or run `/cg-compound` to capture your first solution."
  **Tag**: [safe_auto]

- **[P2.10]** [cg-adversarial] `cg-brain-rebuild.prompt.md:62-65` — Step 3 error guidance missing `/cg-setup` path for fresh linked projects
  **Why**: A user who ran `cg-link` but never ran `/cg-setup` gets `ERROR: .cg-docs does not exist`. Step 3 suggests checking PATH and cwd — neither applies. The real fix is `/cg-setup`. Without this guidance, the user is stuck.
  **Fix**: Add a third bullet to Step 3: "`.cg-docs/` directory not yet created: Run `/cg-setup` to initialize the project structure, which creates `.cg-docs/` along with the required subdirectories."
  **Tag**: [safe_auto]

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` — `cg-brain-rebuild.prompt.md - frontmatter` Describe block is non-standard structure
  **Why**: Every comparable prompt test splits into separate `"... - frontmatter"` and `"... - no tool restriction"` blocks. The new block collapses both into one flat Describe, diverging from `cg-fix-triage`, `cg-review`, and `cg-strategy` patterns.
  **Fix**: Split into two Describe blocks matching the established pattern.
  **Tag**: [safe_auto]

- **[P3.2]** [cg-documentation] `cg-brain-rebuild.prompt.md` — No purpose/value statement
  **Why**: The agent role doesn't explain what BRAIN.md contains or how it's used downstream. New team members encounter the prompt cold with no orientation.
  **Fix**: Add a one-sentence opening: "BRAIN.md is the team's semantic knowledge index — it clusters `.cg-docs/` solutions into topics and maps relationships between entities, enabling future work sessions to surface relevant past learnings automatically."
  **Tag**: [safe_auto]

- **[P3.3]** [cg-code-quality] `cg-brain-rebuild.prompt.md:34-36` — Misleading tier-ordering preamble
  **Why**: "each tier is authoritative only if the prior tier is ambiguous" — exit codes are never ambiguous. The intent is "proceed to the next tier for additional confirmation after the prior tier passes."
  **Fix**: Rephrase to "Check each tier in order. Stop at Step 3 on any failure; proceed for additional detail on success."
  **Tag**: [advisory]

- **[P3.4]** [cg-architecture] `cg-learnings-researcher.agent.md` — DIGEST.md fast-path silently broken
  **Why**: After the first brain rebuild, DIGEST.md no longer exists. The agent's Tier 1 fast-path reads DIGEST.md and falls back to Tier 2/3 on missing file. Functionally correct but the fast-path optimization is permanently gone until Batch C migrates Tier 1 to read BRAIN.md.
  **Fix**: Batch C prerequisite — update `cg-learnings-researcher.agent.md` Tier 1 to read `BRAIN.md`. No change needed now.
  **Tag**: [advisory]

---

### ✅ Passed

- cg-version-control: No secrets, correct .gitignore, files correctly tracked/untracked
- cg-reproducibility: No reproducibility concerns in prompt/test files
- cg-performance: No performance concerns in prompt/test files
- cg-data-quality: No statistical functions or data pipelines touched
- cg-code-quality: `cg-compound.prompt.md` migration is clean — all `--digest` refs removed consistently
- cg-version-control: model-assignments.Tests.ps1 sentinel 22→23 correctly updated
- cg-version-control: roadmap.json feature status updates are consistent with the done pattern
