---
date: 2026-08-17
depth: full
type: standard
plan: ".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P1.1: open
  P1.2: open
  P1.3: fixed
  P1.4: fixed
  P1.5: open
  P1.6: open
  P1.7: open
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
  P2.5: open
  P2.6: open
  P2.7: open
  P2.8: open
  P3.1: open
  P3.2: open
  P3.3: open
  P3.4: open
  P3.5: open
  P3.6: open
  P3.7: open
---

## Review Report

**Review mode**: full (auto-routed: security-risk — vendor policy, import pipeline, admission checks)
**Files reviewed**: 10
**Findings**: 25 (P0: 3, P1: 7, P2: 8, P3: 7)

### P0 — BLOCKING (immediate remediation required)

- **[P0.1]** [cg-adversarial] `scripts/cg_import_skill.py`:174 — Tar path traversal allows quarantine escape and arbitrary file write
  **Why**: `tarfile.extractall()` extracts all tar members without validating their paths. A crafted or MITM'd `git archive` response can write files outside the quarantine directory via `../` path components. The SHA pins the server-side request but the client does not verify the returned tar against any hash.
  **Fix**: Validate every member name before extraction. For Python 3.12+ use `filter='data'`; for 3.8+ compatibility: check each member's resolved path starts with the destination, reject symlinks/hardlinks.

- **[P0.2]** [cg-adversarial] `scripts/cg_import_skill.py`:512-514 — TOCTOU race on quarantine directory enables symlink/junction injection
  **Why**: `run_import` deletes the quarantine directory then recreates it with `exist_ok=True`. Between `rmtree` and `mkdir`, an attacker can create a junction pointing to `.github/skills/`. The `exist_ok=True` means `mkdir` succeeds silently if the junction already exists.
  **Fix**: Use `mkdir(parents=True, exist=False)` and handle `FileExistsError` by aborting. On Windows, verify the created path is not a reparse point.

- **[P0.3]** [cg-adversarial] `scripts/cg_vendor_policy.py`:321-449 — Files fully read into memory before size validation (DoS)
  **Why**: Every text file is fully read via `item.read_text()` before bundle size limits are checked. A single crafted 1GB `.txt` file causes memory exhaustion before the size violation is flagged.
  **Fix**: Check per-file size BEFORE reading content: if `file_size > max_single`, append error and `continue` without reading.

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-adversarial] `scripts/cg_vendor_policy.py`:174-201 — Secret scanning has false negatives for unquoted values and env-var reads
  **Why**: Regex patterns require quoted values and specific variable names. Secrets as bare assignments (`API_KEY = sk-...`) or base64-encoded values pass undetected.
  **Fix**: Add patterns for unquoted assignments and base64 with keyword context.

- **[P1.2]** [cg-adversarial] `scripts/cg_vendor_policy.py`:206-224 — Prompt injection scanning bypassed via Unicode obfuscation and line splitting
  **Why**: An injection payload split across multiple lines (one word per line) evades per-line regex scanning. Unicode homoglyphs and zero-width characters also bypass the patterns.
  **Fix**: Join content before injection scanning (`" ".join(content.splitlines())`), apply NFKC normalization, strip zero-width characters.

- **[P1.3]** [cg-adversarial] `scripts/cg_import_skill.py`:596-608 — CLI `--quarantine-dir` not validated against project root
  **Why**: `--quarantine-dir` accepts an arbitrary path with no validation that it descends from `--root`. File writes and `rmtree` operations can target an arbitrary filesystem location.
  **Fix**: Validate that quarantine_base is a descendant of root.

- **[P1.4]** [cg-code-quality] `scripts/cg_vendor_policy.py`:184-186 — Regex recompiled on every line of every file
  **Why**: `re.compile(pat_str)` inside the inner loop causes thousands of compilations per file. Performance degradation amplifies DoS.
  **Fix**: Compile all patterns once before the line loop.

- **[P1.5]** [cg-code-quality] `scripts/cg_vendor_policy.py`:356-378 — Duplicate path-safety logic in `run_admission_checks`
  **Why**: The admission checks re-implement traversal, hidden-component, and reserved-name checks that already exist in `is_safe_skill_path`. Any update to one must be mirrored in the other.
  **Fix**: Extract shared checks into private helpers called by both functions.

- **[P1.6]** [cg-testing] `scripts/tests/test_import_skill.py`:567-609 — TestVendorRegistration never calls register_vendor_skill()
  **Why**: The test manually replicates business logic instead of calling the actual function. If `register_vendor_skill` regresses, this test still passes.
  **Fix**: Mock `verify_canonical_source_checkout` and call the actual function.

- **[P1.7]** [cg-testing] `scripts/tests/test_import_skill.py`:276-282 — test_detects_api_key has a tautological assertion
  **Why**: `assert "REDACTED" not in ... or "*" in ...` is `A or B` where `A` is always true (redaction uses `*`, not "REDACTED"). The assertion cannot detect passthrough values.
  **Fix**: Assert both conditions independently.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/cg_import_skill.py`:228,249,424 — `import shutil` scattered across function bodies
  **Why**: Module-level imports are the standard pattern. Three inline imports of the same module is DRY-violating.
  **Fix**: Move `import shutil` to top-level imports.

- **[P2.2]** [cg-code-quality] `scripts/cg_import_skill.py`:291 — `admission_result` typed as `Any`
  **Why**: The function accesses `.ok`, `.errors`, `.secret_findings`, `.injection_findings`, `.warnings` — all `AdmissionResult` attributes. `Any` bypasses static analysis.
  **Fix**: Type as `AdmissionResult` and import the class.

- **[P2.3]** [cg-code-quality] `scripts/cg_vendor_policy.py`:288-430 — `run_admission_checks` is 123 lines with 8 phases
  **Why**: Single function handles file iteration, symlink detection, reparse points, hidden components, reserved names, extensions, content scanning, and frontmatter. Hard to test individual phases.
  **Fix**: Extract per-file check logic into a `_check_single_file()` helper.

- **[P2.4]** [cg-code-quality] `scripts/cg_import_skill.py`:83-122,610-623 — SHA validation duplicated
  **Why**: Full 40-char hex validation in `parse_import_spec` and again inline in `main()`.
  **Fix**: Extract `_validate_sha()` helper called from both paths.

- **[P2.5]** [cg-adversarial] `scripts/cg_import_skill.py`:198 — `/dev/null` hooks path is Unix-only
  **Why**: On Windows, `/dev/null` does not exist. Git emits warnings to stderr.
  **Fix**: Use `NUL` on Windows, `/dev/null` elsewhere.

- **[P2.6]** [cg-adversarial] `scripts/cg_import_skill.py`:512-514 — Unhandled `shutil.rmtree` exception
  **Why**: On Windows, locked files cause `PermissionError`. No error handling means the entire import fails without review evidence.
  **Fix**: Wrap in try/except and return error message.

- **[P2.7]** [cg-testing] `scripts/tests/test_import_skill.py`:325-341 — Missing single-file size violation test
  **Why**: `check_bundle_limits` has 3 possible violations but only 2 are tested.
  **Fix**: Add `test_exceeds_single_file_size`.

- **[P2.8]** [cg-testing] `scripts/tests/test_import_skill.py`:375-380 — Symlink test silently skips on Windows
  **Why**: `_quarantine_skill_with_symlink` does `pytest.skip` on Windows. The test never executes on the primary development platform.
  **Fix**: Add a mock-based fallback.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `scripts/cg_vendor_policy.py`:336 — Unused `import stat as _stat`
- **[P3.2]** [cg-code-quality] `scripts/cg_vendor_policy.py`:56,142 — `import unicodedata` inside function bodies (should be top-level)
- **[P3.3]** [cg-code-quality] `scripts/tests/test_import_skill.py`:23 — `REPO_ROOT` defined but never used
- **[P3.4]** [cg-testing] `scripts/tests/test_import_skill.py` — Missing edge-case tests (empty content, no-extension files, empty spec)
- **[P3.5]** [cg-testing] `scripts/tests/test_import_skill.py` — Missing trailing-space collision test
- **[P3.6]** [cg-testing] `scripts/tests/test_import_skill.py` — Missing `skills/` prefix path safety test
- **[P3.7]** [cg-testing] `scripts/tests/test_import_skill.py` — Unused imports `hashlib`, `datetime`

### ✅ Passed

- [cg-code-quality]: No hardcoded secrets, no debug code, naming conventions consistent
- [cg-documentation]: Documentation covers usage, security checks, workflow, configuration
- [cg-version-control]: .gitignore updated, no secrets in new files, commit-ready
- [cg-architecture]: Module boundary respected (kernel owns vendor-policy.json), registry updated
