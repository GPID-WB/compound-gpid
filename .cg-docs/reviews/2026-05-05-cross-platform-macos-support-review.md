---
plan: .cg-docs/plans/2026-05-05-cross-platform-macos-support.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P2.1: skipped
  P2.2: skipped
  P2.3: fixed
  P2.4: open
  P2.5: open
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P2.17: fixed
  P2.18: fixed
  P2.19: fixed
  P2.20: fixed
  P2.21: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: skipped
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
  P3.10: fixed
  P3.11: fixed
  P3.12: fixed
  P3.13: skipped
  P3.14: fixed
  P3.15: fixed
---

## Review Report

**Review depth**: standard + cg-data-quality (auto-escalated: files in `scripts/` directory detected)
**Files reviewed**: 22 (7 staged new, 8 modified, 5 untracked new, 2 untracked `.cg-docs/`)
**Findings**: 41 (P0: 0, P1: 5, P2: 21, P3: 15)
**Agents**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality

> ⚠️ 1,661+ non-test lines changed. Consider running `/cg-review thorough` for `@cg-adversarial` coverage.

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing / cg-architecture / cg-reproducibility] `scripts/install.sh`:1, `scripts/link.sh`:1, `scripts/unlink.sh`:1, `scripts/update.sh`:1 — Shebang mismatch: all 4 scripts use `#!/bin/bash` but `tests/bash-scripts.Tests.ps1` asserts `Should Match "^#!/usr/bin/env bash"`.
  **Why**: Every macOS CI run will fail the 4 "starts with shebang" test assertions. `#!/usr/bin/env bash` also resolves to Homebrew bash 5.x if installed, while `/bin/bash` on macOS is frozen at 3.2.57.
  **Fix**: Change all four scripts' first line to `#!/usr/bin/env bash`.

- **[P1.2]** [cg-code-quality] `scripts/link.sh`:371 — Duplicate script body starting at line 371: the entire script (shebang, `set -euo pipefail`, all six steps) is copy-pasted after the success block with no `exit 0` separating them.
  **Why**: Bash falls through and executes the entire main body a second time: `cg-update` fires twice, symlink steps are re-tried, `copilot-instructions.md` is regenerated again, and any `read -r answer </dev/tty` prompts may re-fire.
  **Fix**: Add `exit 0` after the success block (before line 371), then delete the duplicate content (lines 371–745).

- **[P1.3]** [cg-data-quality] `scripts/install.sh`:~83 and ~170 — Shell profile (`~/.zshrc`/`~/.bashrc`) is written non-atomically via `open(path, 'w')` which truncates the file immediately before writing.
  **Why**: A SIGTERM or SIGKILL between the `open()` and the `write()` completing leaves the user's shell profile at 0 bytes. The user loses all shell customizations silently — no error is printed.
  **Fix**: Write to a temp file and replace atomically:
  ```python
  import tempfile, os
  fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
  try:
      with os.fdopen(fd, 'w') as f:
          f.write(updated + '\n')
      os.replace(tmp, path)
  except:
      os.unlink(tmp)
      raise
  ```

- **[P1.4]** [cg-reproducibility] `scripts/install.sh`:~85–91 — The `--uninstall` Python block uses `os.remove(path)` when the profile contains only the CG block (i.e. `updated` is an empty string, which is falsy), permanently deleting `~/.zshrc` or `~/.bashrc`.
  **Why**: If the user's entire shell profile consists of only the compound-gpid PATH block, uninstall silently deletes the file. The install path uses `open(path, 'w').close()` (truncate to empty) — the uninstall path must do the same.
  **Fix**: Replace the `os.remove(path)` branch in the uninstall block:
  ```python
  else:
      open(path, 'w').close()
  ```

- **[P1.5]** [cg-version-control] Staging area is critically incomplete — 11 files are either untracked (`??`) or modified-but-unstaged (` M`):
  - Untracked: `.gitattributes`, `.github/workflows/tests.yml`, `tests/bash-scripts.Tests.ps1`
  - Unstaged modified: `docs/installation.md`, `tests/Run-Tests.ps1`, `tests/charter.Tests.ps1`, `tests/helpers.Tests.ps1`, `tests/install.Tests.ps1`, `tests/link.Tests.ps1`, `tests/run-tests-runner.Tests.ps1`, `tests/unlink.Tests.ps1`
  **Why**: A commit right now would push only the 7 new `scripts/` and `bin/` files — no `.gitattributes` (LF enforcement), no CI workflow (feature is untested on GitHub), no test updates, no doc updates. Additionally, `bin/*.cmd` wrappers are staged but missing `eol=crlf` in `.gitattributes` because `.gitattributes` itself is not staged.
  **Fix**: Stage all files together for a single atomic commit:
  ```
  git add .gitattributes .github/workflows/tests.yml tests/bash-scripts.Tests.ps1
  git add docs/installation.md tests/Run-Tests.ps1 tests/charter.Tests.ps1 tests/helpers.Tests.ps1 tests/install.Tests.ps1 tests/link.Tests.ps1 tests/run-tests-runner.Tests.ps1 tests/unlink.Tests.ps1
  git add .cg-docs/brainstorms/2026-05-05-cross-platform-macos-support.md .cg-docs/plans/2026-05-05-cross-platform-macos-support.md
  git commit -m "feat(cross-platform): add macOS bash scripts and CI support"
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-architecture / cg-code-quality] `scripts/link.sh`, `scripts/update.sh` — `generate_copilot_instructions` function (~70 lines including embedded Python heredoc) is copy-pasted verbatim in both files.
  **Why**: Any fix to the template logic, placeholder handling, or `extract_fm_value` regex must be applied in two places; one copy will inevitably drift. The PowerShell side avoids this by delegating to `New-CopilotInstructions` in `scripts/helpers.ps1`.
  **Fix**: Extract to `scripts/common.sh` and source it: `. "$SCRIPT_DIR/common.sh"` in both scripts.

- **[P2.2]** [cg-architecture / cg-code-quality] `scripts/install.sh`, `scripts/link.sh`, `scripts/unlink.sh`, `scripts/update.sh` — Six color/print helper functions (`print_cyan`, `print_green`, `print_yellow`, `print_gray`, `print_warn`, `print_error`) are copy-pasted identically across all four files (~36 lines × 4 = 144 duplicate lines).
  **Why**: Any change (e.g., adding `print_red`, adjusting a colour code) must be applied in four places.
  **Fix**: Extract to `scripts/common.sh` (same file as P2.1). Source once per script. Removes ~108 lines of duplication.

- **[P2.3]** [cg-architecture] `scripts/link.sh` — Missing Step 5b: removal of the legacy `# Compound GPID knowledge base` + `.cg-docs/` gitignore entry written by older cg-link versions.
  **Why**: Users upgrading from old installs will permanently gitignore `.cg-docs/` (institutional memory lost from version control) unless they run a manual cleanup. `link.ps1` handles this explicitly.
  **Fix**: Add a targeted Python `re.sub` (consistent with the existing `.gitignore` manipulation pattern) to remove the legacy block before writing the new one.

- **[P2.4]** [cg-architecture] `scripts/update.sh` — Missing schema version stamping (parity gap with `update.ps1`).
  **Why**: `update.ps1` reads `SCHEMA_VERSION` and stamps `cg-schema-version:` in `compound-gpid.local.md`. `update.sh` has no equivalent. macOS-linked projects never receive schema version stamps, silently disabling schema-gated migrations and future compatibility checks.
  **Fix**: Add shell equivalent after the structural migration block: read `"$COMPOUND_GPID_DIR/SCHEMA_VERSION"`, update `compound-gpid.local.md` via inline Python (consistent with existing patterns).

- **[P2.5]** [cg-architecture] `scripts/update.sh` — Missing project charter migration notice (parity gap with `update.ps1`).
  **Why**: `update.ps1` checks whether `compound-gpid.md` exists and emits an advisory if missing. `update.sh` omits this. New macOS users without a charter receive no guidance to run `/cg-setup`.
  **Fix**: After the schema stamp block: `if [[ ! -f "$CWD_ROOT/compound-gpid.md" ]]; then print_yellow "Notice: No project charter found. Run /cg-setup in VS Code Copilot Chat."; fi`

- **[P2.6]** [cg-architecture / cg-code-quality] `scripts/install.sh`, `scripts/link.sh`, `scripts/unlink.sh`, `scripts/update.sh` — `python3` availability is never verified before use. `install.sh` checks for `git` with a clear error and install instructions but makes no equivalent check for `python3`.
  **Why**: On macOS without Xcode CLT installed, `python3` is absent. Scripts fail deep in execution with `bash: python3: command not found` rather than a human-readable error. On Monterey+, invoking `python3` can trigger a macOS dialog.
  **Fix**: Add after the `git` check in `install.sh`, and at the top of the validation block in `link.sh`, `unlink.sh`, `update.sh`:
  ```bash
  if ! command -v python3 &>/dev/null; then
      print_error "python3 is required. Install Xcode Command Line Tools: xcode-select --install"
      exit 1
  fi
  ```

- **[P2.7]** [cg-data-quality] `scripts/install.sh`:~224, `scripts/update.sh`:~256 — Non-atomic `.cg-version` writes via `printf '...' > "$VERSION_FILE"`.
  **Why**: `>` truncates the file before writing. An interrupt (SIGTERM, Ctrl+C, disk-full) leaves `.cg-version` empty. On next run, `update.sh` reads empty string → `"Malformed .cg-version: ''"` error blocks all subsequent `cg-update` calls.
  **Fix**: `printf '%s' "$VERSION_MODE" > "${VERSION_FILE}.tmp" && mv "${VERSION_FILE}.tmp" "$VERSION_FILE"`

- **[P2.8]** [cg-data-quality] `scripts/link.sh`:~265, `scripts/update.sh`:~388 — Non-atomic `copilot-instructions.md` writes via shell redirect.
  **Why**: `printf '%s' "$GENERATED" > "$DEST"` truncates the file immediately. An interrupt leaves an empty file with no management marker, causing the script to treat it as user-managed on the next run and skip regeneration — permanently and silently.
  **Fix**: `TMP_DEST="${COPILOT_INSTRUCTIONS_DEST}.tmp"; printf '%s' "$GENERATED" > "$TMP_DEST" && mv "$TMP_DEST" "$COPILOT_INSTRUCTIONS_DEST"`

- **[P2.9]** [cg-data-quality] `scripts/link.sh`:~295, `scripts/unlink.sh`:~130 — Non-atomic `.gitignore` writes in Python `open(path, 'w')` blocks.
  **Why**: Truncates `.gitignore` before writing. If interrupted between truncation and write, all gitignore rules are lost. Previously-ignored secrets and build artifacts may be staged accidentally with no error trace.
  **Fix**: Use `tempfile + os.replace()` pattern (same as P1.3 fix) in all Python `.gitignore` write blocks.

- **[P2.10]** [cg-data-quality / cg-architecture] `scripts/link.sh`:~340 — Post-link symlink verification checks only `$TARGET_GITHUB_DIR/prompts/cg-setup.prompt.md`.
  **Why**: If `ln -s` succeeded for `prompts/` but silently failed for `skills/`, `agents/`, or `instructions/`, the script reports "Symlinks verified." and exits cleanly. Users find missing skills/agents in VS Code with no actionable error.
  **Fix**: Verify a representative file or the directory itself for each managed directory:
  ```bash
  for dir in "${MANAGED_DIRS[@]}"; do
      if [[ ! -d "$TARGET_GITHUB_DIR/$dir" ]]; then
          print_warn "Verification failed — $dir/ not accessible"
      fi
  done
  ```

- **[P2.11]** [cg-code-quality] `bin/cg-link`, `bin/cg-unlink`, `bin/cg-update` — Missing `set -euo pipefail`.
  **Why**: If `cd "$(dirname "$0")"` fails (path removed), `SCRIPT_DIR` is empty and `exec "" link.sh "$@"` runs with a garbage path. Without `set -e`, this silently continues.
  **Fix**: Add `set -euo pipefail` as the second line of each wrapper.

- **[P2.12]** [cg-code-quality] `.gitattributes` — No `eol=crlf` entry for `bin/*.cmd` Windows batch wrappers.
  **Why**: CMD.EXE requires CRLF. If a macOS developer edits a `.cmd` file, Git stores it with LF and Windows will silently misparse multi-line blocks.
  **Fix**: Add `bin/*.cmd    text eol=crlf` to `.gitattributes`.

- **[P2.13]** [cg-reproducibility] `.github/workflows/tests.yml`:20, :47 — `actions/checkout@v4` and `actions/upload-artifact@v4` are mutable refs.
  **Why**: Tags can be force-pushed to point to different commits, silently changing CI behaviour between runs.
  **Fix**: Pin to commit SHAs (e.g. `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`). Review and update deliberately.

- **[P2.14]** [cg-reproducibility] `scripts/update.sh` — `CG_INTERNAL_CALL=1` guard suppresses both `copilot-instructions.md` regeneration **and** the structural `docs/→.cg-docs/` migration, sharing a single `if [[ "${CG_INTERNAL_CALL:-}" != "1" ]]` check.
  **Why**: When `link.sh` calls `update.sh` with `CG_INTERNAL_CALL=1`, a project that still has the old `docs/brainstorms/` layout silently skips migration. The user must then run a separate bare `cg-update` to trigger it — undocumented, unintuitive.
  **Fix**: Extract the migration into a separate function called unconditionally, keeping only `refresh_copilot_instructions` guarded by `CG_INTERNAL_CALL`.

- **[P2.15]** [cg-testing] `tests/bash-scripts.Tests.ps1`:~128 — Idempotency smoke test sets `$env:HOME` to a temp directory but does not sandbox `COMPOUND_GPID_DIR`. `install.sh` resolves its own path, so Step 3 (bin wrapper creation) and Step 4 (`.cg-version` init) write to the actual checked-out repo.
  **Why**: Test runs modify the source tree — violates test isolation. On CI, this mutates the runner checkout.
  **Fix**: Either introduce a `CG_TEST_INSTALL_DIR` env var that `install.sh` honours for bin/version targets, or document it as an intentional integration test.

- **[P2.16]** [cg-testing] `tests/bash-scripts.Tests.ps1`:~154 — `finally` block calls `Remove-Item Env:\HOME` instead of restoring the original value.
  **Why**: Any test or OS call after this block that depends on `$HOME` will see an empty or missing value. The original `HOME` is never saved.
  **Fix**:
  ```powershell
  $originalHome = $env:HOME
  # ... test body ...
  } finally {
      if ($originalHome) { $env:HOME = $originalHome } else { Remove-Item Env:\HOME -ErrorAction SilentlyContinue }
  }
  ```

- **[P2.17]** [cg-documentation] `docs/reference.md`:~7 — Section heading "PowerShell Commands" is now inaccurate.
  **Why**: `cg-link`, `cg-unlink`, `cg-update` are now bash commands on macOS too. macOS users will assume this section doesn't apply to them.
  **Fix**: Rename to "Shell Commands" and add a note: *"Available from PowerShell on Windows and bash/zsh on macOS."*

- **[P2.18]** [cg-documentation] `README.md`:~20 — "directory junctions" is Windows-only NTFS terminology.
  **Why**: Any macOS reader interprets this as Windows-only.
  **Fix**: Change to *"one global clone, per-subdirectory symlinks (junctions on Windows, symlinks on macOS), and three shell commands"*.

- **[P2.19]** [cg-documentation] `docs/installation.md` — macOS uninstall example hardcodes `~/.compound-gpid`.
  **Why**: If the user installed to any other path, the command silently targets the wrong directory and appears to succeed.
  **Fix**: Generalize: `bash <your-install-path>/scripts/install.sh --uninstall  # e.g. ~/.compound-gpid/scripts/install.sh --uninstall`

- **[P2.20]** [cg-version-control] `.cg-docs/brainstorms/2026-05-05-cross-platform-macos-support.md`, `.cg-docs/plans/2026-05-05-cross-platform-macos-support.md` — Untracked institutional knowledge files.
  **Why**: The project charter requires `.cg-docs/` to be version-controlled. These files will be lost if the branch is merged without them.
  **Fix**: Include in the commit (see P1.5 fix command).

- **[P2.21]** [cg-code-quality / cg-data-quality] `scripts/update.sh`:~277 — `git checkout . 2>/dev/null || true` discards all working-tree changes in the compound-gpid install directory with no warning.
  **Why**: A developer with local edits (e.g., testing a skill change) loses them silently on every `cg-update` run. The `|| true` means failures are also swallowed.
  **Fix**:
  ```bash
  if ! git diff --quiet 2>/dev/null; then
      print_warn "Local changes in compound-gpid will be reset before pulling."
  fi
  git checkout . 2>/dev/null || true
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/bash-scripts.Tests.ps1`:~318 — `.gitattributes` test asserts only the `bin/cg-link` entry; `bin/cg-unlink` and `bin/cg-update` entries are unchecked.
  **Fix**: Add `It` blocks asserting `$content | Should Match "cg-unlink.*eol=lf"` and `"cg-update.*eol=lf"`.

- **[P3.2]** [cg-testing] `tests/run-tests-runner.Tests.ps1`:~42 — No `$testNames includes 'bash-scripts'` assertion. The `bash-scripts` entry could be silently removed with no test catching it.
  **Fix**: Add: `It "'bash-scripts' is in testNames" { ($runnerContent -match "'bash-scripts'") | Should Be $true }`

- **[P3.3]** [cg-testing] `tests/bash-scripts.Tests.ps1` — No live execution tests for `link.sh`, `unlink.sh`, or `update.sh`. Only `install.sh` has a live run.
  **Fix**: Add a minimal happy-path smoke test for `link.sh` (create temp project with `compound-gpid.md`, run `cg-link`, assert symlinks exist). Similarly for `unlink.sh` using stdin redirect (`echo y | bash unlink.sh`).

- **[P3.4]** [cg-architecture / cg-version-control] `.gitattributes` — `bin/cg-link`, `bin/cg-unlink`, `bin/cg-update` listed individually instead of with a glob.
  **Fix**: Replace the three explicit lines with `bin/cg-*    text eol=lf`. Covers all current and future extension-free wrappers.

- **[P3.5]** [cg-architecture] `scripts/link.sh` — Success message missing the restart reminder and `/cg-setup` call-to-action present in `link.ps1`.
  **Why**: New macOS users who don't restart VS Code will be confused when prompts aren't visible.
  **Fix**: Mirror the `link.ps1` success block: print managed-dirs warning, restart reminder, and `/cg-setup` CTA.

- **[P3.6]** [cg-version-control] `.gitattributes` — `.github/workflows/tests.yml` and other YAML files not covered for LF enforcement.
  **Fix**: Add `*.yml    text eol=lf` and `*.yaml    text eol=lf`.

- **[P3.7]** [cg-reproducibility] `.github/workflows/tests.yml`:13–14 — Mutable runner labels `macos-latest` and `windows-latest`.
  **Why**: GitHub advances these labels, changing test environments without repo changes.
  **Fix**: Pin to `windows-2022` and `macos-14` (or current concrete versions) and update deliberately.

- **[P3.8]** [cg-code-quality] `scripts/install.sh`:~46 — `detect_profile()` silently falls back to `~/.zshrc` for unrecognized shells (fish, nushell, tcsh).
  **Why**: PATH block is written to a file the user's shell never sources.
  **Fix**: Add a warning branch for unrecognized shells and print a manual instruction.

- **[P3.9]** [cg-documentation] `docs/installation.md` — macOS Step 4 body says "Same as Windows" without the `⚠️ Do not skip this step` warning present in the Windows step.
  **Fix**: Expand macOS Step 4 with the full warning block matching the Windows phrasing.

- **[P3.10]** [cg-documentation] `scripts/update.sh` — `git pull --ff-only` failure prints only "git pull failed" with no recovery guidance.
  **Fix**: After the error: `printf 'To repair: run cg-update --fix\n' >&2`

- **[P3.11]** [cg-performance] `scripts/install.sh`:~232, `scripts/link.sh`:~252, `scripts/update.sh`:~400 — Three uses of `$(cat "$FILE")` (subprocess fork) instead of `$(< "$FILE")` (bash built-in).
  **Fix**: Replace with `$(< "$FILE")` at each location.

- **[P3.12]** [cg-code-quality] `.github/workflows/tests.yml` — No `permissions:` block; inherits default GITHUB_TOKEN permissions which may be `read-write` depending on org settings.
  **Fix**: Add `permissions: contents: read` at the job level.

- **[P3.13]** [cg-testing] `tests/bash-scripts.Tests.ps1` — No test for `unlink.sh` TTY interaction in non-interactive environments (CI, Docker). `unlink.sh` uses `read -r answer </dev/tty` which fails or hangs when `/dev/tty` is unavailable.
  **Fix**: Verify `unlink.sh` handles non-interactive mode gracefully, or add a `--yes`/`--no-confirm` flag. Add a test that invokes it with stdin redirect.

- **[P3.14]** [cg-code-quality] `scripts/update.sh`:~265 — `git log --oneline "$BEFORE..$AFTER"` unguarded against empty `$BEFORE` (if `rev-parse` fails).
  **Fix**: `if [[ -n "$BEFORE" && "$BEFORE" != "$AFTER" ]]; then git log --oneline "$BEFORE..$AFTER"; fi`

- **[P3.15]** [cg-reproducibility] `scripts/install.sh`:~206 — Absolute `$BIN_DIR` path baked into shell profile becomes stale if the repo is moved.
  **Fix**: Write path relative to `$HOME` using `"\$HOME/${BIN_DIR#$HOME/}"` so it survives home-directory migration. (Self-heals on `install.sh` re-run, so P3.)

---

### ✅ Passed

- **cg-version-control**: Executable bits — all `.sh` and `bin/cg-*` files correctly staged as `100755`; `.cmd` wrappers as `100644`.
- **cg-version-control**: No secrets, API keys, tokens, or credentials in any new file.
- **cg-version-control**: No `.gitignore` collisions for new files.
- **cg-data-quality**: No unquoted variable bugs, no path traversal risks.
- **cg-architecture**: CI workflow matrix strategy is sound (`fail-fast: false`, correct Pester version selection per platform, `chmod +x` step, artifact upload with `if: always()` + `if-no-files-found: ignore`).
- **cg-performance**: No `sleep`/polling loops, no large-file operations, no extraneous network calls. Bin wrappers are single-line `exec` delegates — startup overhead minimal.
- **cg-testing**: Platform guard pattern (`$IsMacOS -eq $true` with PS 5.1 fallback), Pester 3.4 compatibility (no `Describe -Skip`, no `BeforeAll`/`AfterAll`), `Run-Tests.ps1` `$testNames` registration — all correct.
