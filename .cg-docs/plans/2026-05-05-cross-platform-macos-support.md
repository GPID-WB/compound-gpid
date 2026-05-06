---
date: 2026-05-05
title: "Cross-platform macOS support — parallel shell scripts"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-05-05-cross-platform-macos-support.md"
language: "both"
estimated-effort: "large"
tags: [cross-platform, macos, bash, installation, ci, testing]
---

# Plan: Cross-platform macOS support — parallel shell scripts

## Objective

Add macOS support to the Compound GPID plugin distribution by creating parallel
bash scripts (`install.sh`, `link.sh`, `unlink.sh`, `update.sh`) alongside
existing PowerShell scripts, with extensionless bash wrappers in `bin/`, shell
profile PATH registration, and a cross-platform CI pipeline. The existing
Windows scripts remain untouched — zero regression risk.

## Context

The plugin currently uses Windows-only mechanisms: directory junctions, `.cmd`
batch wrappers, Windows registry PATH modification, and PowerShell scripts.
The team now has macOS users who need `cg-link`, `cg-unlink`, `cg-update` to
work without any dependencies (no Homebrew, no pwsh). The developer maintains
both platforms and uses `pwsh` + Pester on macOS for testing.

Key decisions from the brainstorm:
- Parallel bash scripts (zero Mac dependencies) — NOT unified PowerShell
- Symlinks (`ln -s`) instead of junctions — no admin needed on macOS
- Pester remains the single test suite (developer has pwsh on macOS)
- CI validates both platforms on every push
- Linux deferred (not tested/documented this iteration)

## Requirements

| ID  | Requirement                                      | Source           |
|-----|--------------------------------------------------|------------------|
| R1  | Mac consumers can install with zero dependencies | brainstorm       |
| R2  | No admin rights required for Mac consumers       | brainstorm       |
| R3  | `cg-link` creates symlinks to managed dirs       | brainstorm       |
| R4  | `cg-update` refreshes copilot-instructions.md    | brainstorm       |
| R5  | `cg-unlink` removes symlinks cleanly             | brainstorm       |
| R6  | Shell profile modification is idempotent         | brainstorm       |
| R7  | Pester tests pass on both platforms               | brainstorm       |
| R8  | CI matrix: windows-latest + macos-latest         | brainstorm       |
| R9  | Existing Windows scripts unchanged               | brainstorm       |
| R10 | `.gitignore` patterns work for both link types   | brainstorm       |
| R11 | Rollback: `uninstall` removes PATH from profile  | plan-critic      |
| R12 | Template path handling uses `/` on macOS          | plan-critic      |
| R13 | Symlink detection in unlink uses `readlink`       | plan-critic      |
| R14 | install.sh detects existing stale PATH entries    | plan-critic      |

## Implementation Steps

### Phase 1: Core Scripts

#### 1. Create `scripts/install.sh`
- **Requirements**: R1, R2, R6, R11, R14
- **Files**: `scripts/install.sh` (new)
- **Details**:
  - Verify `git` is available
  - Test symlink capability (`ln -s` in `$TMPDIR`)
  - Create `bin/` directory with bash wrappers (`cg-link`, `cg-unlink`, `cg-update`)
  - Detect user's shell (`$SHELL`) — support `zsh` (default macOS) and `bash`
  - Add `bin/` to PATH via shell profile (`~/.zshrc` or `~/.bashrc`):
    - Target `~/.zshrc` for zsh (covers VS Code integrated terminal and most macOS terminal emulators — Terminal.app opens interactive login shells which source both `.zprofile` and `.zshrc`). Document that users with login-shell-only setups should add the block to `~/.zprofile` instead.
    - Use a marker comment block: `# --- Compound GPID ---` / `# --- End Compound GPID ---`
    - Idempotent: remove existing block before rewriting (same pattern as PS1 profile cleanup)
    - Check if PATH entry already exists before adding — both inside the marker block and as a bare `export PATH=...` line elsewhere in the file (R14)
  - Create `.cg-version` with "latest" if not present
  - Print instructions: "Restart your terminal to use cg-link, cg-unlink, cg-update"
  - Include `--uninstall` flag: removes bin/ wrappers and profile PATH block (R11)
- **Test Scenarios**:
  - ✅ Happy path: fresh install on macOS, PATH added to ~/.zshrc
  - ✅ Happy path: re-run (idempotent) — no duplicate entries
  - 🛑 Edge case: user has custom ~/.zshrc with complex content — CG block doesn't corrupt it
  - 🛑 Edge case: `$SHELL` is `/bin/bash` — uses ~/.bashrc instead
  - 🛑 Edge case: PATH already contains the bin dir (from manual add) — skips
  - ❌ Error path: git not found — clear error message and exit 1
  - ❌ Error path: symlinks not working (exotic filesystem) — clear error
- **Tests**: Pester tests in `tests/install.Tests.ps1` — add platform-conditional section
- **Acceptance criteria**: Running `./scripts/install.sh` on macOS adds PATH to profile, creates bash wrappers

#### 2. Create `scripts/link.sh`
- **Requirements**: R1, R2, R3, R4, R10, R12
- **Files**: `scripts/link.sh` (new)
- **Details**:
  - Resolve install dir: `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`, then `COMPOUND_GPID_DIR="$(dirname "$SCRIPT_DIR")"`
  - Validate global install exists
  - Run `update.sh` first **with suppression env var**: `CG_INTERNAL_CALL=1 "$COMPOUND_GPID_DIR/scripts/update.sh"` — this prevents update.sh from refreshing copilot-instructions.md (link.sh handles its own refresh in the next step, same pattern as link.ps1's `$env:CG_INTERNAL_CALL`)
  - Create `.github/` as real directory if not exists
  - Handle legacy: if `.github` is a symlink itself, remove and recreate as directory
  - For each managed dir (`prompts`, `skills`, `agents`, `instructions`):
    - If symlink exists pointing to compound-gpid → skip ("already linked")
    - If symlink exists pointing elsewhere → prompt to relink
    - If real directory exists → error (same as PS1 behavior)
    - Otherwise → `ln -s "$SOURCE/.github/$dir" "$TARGET/.github/$dir"`
  - Generate `copilot-instructions.md` from template (R4, R12):
    - Read `.github/copilot-instructions.template.md` using forward slashes
    - Parse `compound-gpid.md` frontmatter for `project-name`
    - Parse `compound-gpid.local.md` for `language`, `project-type`, `review-depth`, `r-syntax`
    - Replace `{{placeholders}}` using **pipe-delimited sed**: `sed "s|{{project-name}}|${project_name}|g"` — pipe `|` chosen as delimiter because project values may contain `/` (e.g., `R/Python`). Chain multiple sed calls for each placeholder. Guard: if a value contains `|`, fall back to `python3 -c "import sys; sys.stdout.write(open(sys.argv[1]).read().replace(sys.argv[2], sys.argv[3]))"` which is zero-dependency on macOS and fully delimiter-safe.
    - Prepend management marker
    - Skip if file exists without marker (user-managed)
  - Update `.gitignore` (same CG block pattern, idempotent)
  - Verify: check a known file is accessible through the symlink
- **Test Scenarios**:
  - ✅ Happy path: fresh project, all 4 symlinks created + copilot-instructions.md generated
  - ✅ Happy path: re-run — all report "already linked"
  - 🛑 Edge case: one dir is a real directory → error for that dir only
  - 🛑 Edge case: template has no matching placeholder → passes through unchanged
  - 🛑 Edge case: `compound-gpid.local.md` doesn't exist → uses defaults
  - ❌ Error path: install dir missing → clear error
- **Tests**: Pester tests — add macOS symlink assertions (platform-conditional)
- **Acceptance criteria**: After `cg-link`, `.github/prompts` is a symlink → compound-gpid install

#### 3. Create `scripts/unlink.sh`
- **Requirements**: R2, R5, R13
- **Files**: `scripts/unlink.sh` (new)
- **Details**:
  - Check `.github/` exists
  - Handle legacy: if `.github` itself is a symlink to compound-gpid, remove it
  - For each managed dir: if it's a symlink (`-L` test) pointing to compound-gpid → remove
    - **macOS-safe readlink**: Use `readlink "$linkpath"` (no `-f` flag — `-f` is a GNU extension not available on macOS BSD). This returns the raw symlink target. To resolve to an absolute path: `REAL=$(cd "$(dirname "$linkpath")" && cd "$(readlink "$linkpath")/.." && pwd)/$(basename "$(readlink "$linkpath")")`
    - Match target against `*compound-gpid*` pattern (same logic as PS1's `-like "*compound-gpid*"`)
  - Remove `copilot-instructions.md` if it has the management marker
  - Clean `.gitignore` CG block
  - If `.github/` is empty after unlinking, remove it
  - Confirmation prompt before proceeding (same UX as PS1)
- **Test Scenarios**:
  - ✅ Happy path: all symlinks removed, .gitignore cleaned
  - 🛑 Edge case: symlink points to something else → skip
  - 🛑 Edge case: mixed (some symlinks, some real dirs) → only removes symlinks
  - ❌ Error path: .github doesn't exist → "Nothing to unlink"
- **Tests**: Pester platform-conditional tests for symlink removal
- **Acceptance criteria**: After `cg-unlink`, no CG symlinks remain in `.github/`

#### 4. Create `scripts/update.sh`
- **Requirements**: R1, R4, R12
- **Files**: `scripts/update.sh` (new)
- **Details**:
  - Resolve install dir (same pattern as link.sh)
  - Support arguments: `$1` as version (`latest`, `v0.2.0`), `--list`, `--fix`
  - Validate `.cg-version` format
  - Latest mode: `git checkout .` + `git pull --ff-only` on the install dir
  - Pinned mode: `git fetch --tags` + `git checkout <tag>`
  - `--list`: show available releases (filter to 3-component tags)
  - `--fix`: `git clean -fd`, `git checkout .`, `git pull --ff-only`
  - **`CG_INTERNAL_CALL` guard**: If env var `CG_INTERNAL_CALL` is set to `1`, skip the copilot-instructions.md refresh step (caller handles it). This mirrors the `$env:CG_INTERNAL_CALL` pattern in `update.ps1`.
  - Refresh `copilot-instructions.md` in current project (if linked and marker present, and `CG_INTERNAL_CALL` is not set)
  - Show "newer release available" hint (same as PS1)
- **Test Scenarios**:
  - ✅ Happy path: latest mode pulls and reports changes
  - ✅ Happy path: pinned mode checks out specific tag
  - 🛑 Edge case: offline — warns and continues
  - 🛑 Edge case: invalid version argument → clear error
  - ❌ Error path: git not found → error
- **Tests**: Pester tests (version validation, mode detection)
- **Acceptance criteria**: `cg-update` pulls latest, refreshes copilot-instructions

### Phase 2: Bin Wrappers

#### 5. Create bash wrappers in `bin/`
- **Requirements**: R1, R2
- **Files**: `bin/cg-link` (new), `bin/cg-unlink` (new), `bin/cg-update` (new)
- **Details**:
  - Each wrapper: `#!/bin/bash` + resolve own dir + call `scripts/<name>.sh "$@"`
  - Pattern: `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` then `exec "$SCRIPT_DIR/../scripts/<name>.sh" "$@"`
  - **Executable bit persistence in git**: After creating all `.sh` and `bin/cg-*` files, run:
    ```bash
    git add --chmod=+x scripts/install.sh scripts/link.sh scripts/unlink.sh scripts/update.sh bin/cg-link bin/cg-unlink bin/cg-update
    ```
    This ensures the executable bit is tracked in git regardless of which OS commits the files. Windows git does not set POSIX executable bits from the working tree, so `--chmod=+x` at `git add` time is mandatory. Verify with `git ls-files -s scripts/install.sh` — should show `100755` (not `100644`).
  - Add `.gitattributes` entries for safety:
    ```
    scripts/*.sh text eol=lf
    bin/cg-link text eol=lf
    bin/cg-unlink text eol=lf
    bin/cg-update text eol=lf
    ```
    This prevents Windows from committing CRLF line endings into bash scripts.
- **Test Scenarios**:
  - ✅ Happy path: `bin/cg-link` correctly delegates to `scripts/link.sh`
  - 🛑 Edge case: called from a different working directory — resolves correctly
- **Tests**: Pester test validates wrapper content and structure
- **Acceptance criteria**: Running `bin/cg-link` from any directory invokes `scripts/link.sh`

### Phase 3: Test Adaptation

#### 6. Make Pester tests platform-aware
- **Requirements**: R7, R9
- **Files**: `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1`, `tests/install.Tests.ps1`, `tests/helpers.Tests.ps1`, `tests/Run-Tests.ps1` (modify)
- **Details**:
  - **Fix backslash paths in `Run-Tests.ps1`** (P1.2 — blocking): Replace `"tests\$name.Tests.ps1"` with `(Join-Path "tests" "$name.Tests.ps1")` (nested Join-Path, platform-safe). On macOS pwsh, `Join-Path $root "tests\charter.Tests.ps1"` produces a literal backslash in the path component — this breaks file resolution for ALL 13 test files, making CI report 0 tests while appearing green. Apply the same nested-Join-Path fix to:
    - `tests/helpers.Tests.ps1` line ~9: `. (Join-Path $repoRoot "scripts\helpers.ps1")` → `. (Join-Path (Join-Path $repoRoot "scripts") "helpers.ps1")`
    - `tests/run-tests-runner.Tests.ps1`: all `Join-Path $repoRoot "tests\Run-Tests.ps1"` and `"tests\last-run.json"` patterns
    - `scripts/helpers.ps1`: `Join-Path $TemplateDir ".github\copilot-instructions.template.md"` → `Join-Path (Join-Path $TemplateDir ".github") "copilot-instructions.template.md"`
    - `scripts/link.ps1` verification: `Join-Path $TargetGithubDir "prompts\cg-setup.prompt.md"` → nested Join-Path
  - **Platform detection helper** (P2.2 — PS 5.1-safe): Add this block at the top of each modified test file:
    ```powershell
    # Platform detection - works on PS 5.1 (no $IsWindows) and pwsh 6+ (has $IsWindows/$IsMacOS)
    $script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
    $script:OnMacOS   = ($IsMacOS -eq $true)
    ```
    The `$env:OS -eq "Windows_NT"` check is the PS 5.1-safe fallback since `$IsWindows` doesn't exist in PS 5.1.
  - **Conditional test blocks** (Pester 3.4 compatible): Wrap platform-specific `Describe`/`It` blocks in `if` guards:
    ```powershell
    if ($script:OnWindows) {
        Describe "link.ps1 - junction creation" { ... }
    }
    if ($script:OnMacOS) {
        Describe "link.sh - symlink creation" { ... }
    }
    ```
    Do NOT use `-Skip` parameter (Pester 5 syntax — fails on PS 5.1 with Pester 3.4).
  - Add `$IsWindows`/`$IsMacOS` guards around platform-specific assertions:
    - Windows: test `Junction` LinkType, `.cmd` wrapper content
    - macOS: test symlink via `(Get-Item $path).Attributes -band [System.IO.FileAttributes]::ReparsePoint` or shell out to `test -L`
- **Test Scenarios**:
  - ✅ Happy path: full test suite passes on macOS with pwsh
  - ✅ Happy path: full test suite still passes on Windows (unchanged behavior)
  - 🛑 Edge case: pwsh version detection on Windows PS 5.1 (no `$IsWindows` var)
- **Tests**: Self-validating — if tests pass on both platforms in CI, this step is done
- **Acceptance criteria**: `Invoke-Pester tests/<file>.ps1` passes on both macOS and Windows

#### 7. Add bash script integration tests
- **Requirements**: R7
- **Files**: `tests/bash-scripts.Tests.ps1` (new), `tests/Run-Tests.ps1` (modify)
- **Details**:
  - **Register in `Run-Tests.ps1`** (P1.1 — critical): Add `'bash-scripts'` to the `$testNames` array in `tests/Run-Tests.ps1`. Without this, the new test file silently never runs and CI appears green while bash scripts have zero coverage.
  - **Pester 3.4-compatible file-level skip** (P3.1): Use an early-return guard at the top of the file instead of `Describe -Skip` (which is Pester 5-only syntax):
    ```powershell
    $script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
    $script:OnMacOS   = ($IsMacOS -eq $true)

    if (-not $script:OnMacOS) {
        Describe "bash-scripts.Tests.ps1" {
            It "skipped on non-macOS platform" { $true | Should Be $true }
        }
        return
    }
    ```
    This ensures the file is not empty on Windows (Pester 3.4 needs at least one `It`) while cleanly skipping all real tests.
  - Pester tests that invoke the bash scripts on macOS and verify outcomes:
    - `install.sh`: creates wrappers in `$TMPDIR/test-bin/`, modifies a temp profile file
    - `link.sh`: creates symlinks in a temp project
    - `unlink.sh`: removes symlinks
    - `update.sh --list`: exits 0 with version output
  - Use `bash -c` to invoke scripts from Pester
  - Set `$env:HOME` to `$TestDrive` to avoid touching the real profile
- **Test Scenarios**:
  - ✅ Happy path: all bash scripts produce expected filesystem state
  - 🛑 Edge case: script invoked from directory with spaces in path
  - ❌ Error path: script invoked without git → exits 1
- **Tests**: Self-contained Pester file
- **Acceptance criteria**: `Invoke-Pester tests/bash-scripts.Tests.ps1` passes on macOS

### Phase 4: CI Pipeline

#### 8. Create GitHub Actions workflow
- **Requirements**: R8
- **Files**: `.github/workflows/tests.yml` (new)
- **Details**:
  - Trigger: push to `main` and `feat/*` branches, pull requests to `main`
  - Matrix: `os: [windows-latest, macos-latest]`
  - Steps:
    1. Checkout repo
    2. Install PowerShell on macOS (GH Actions macOS runners have pwsh pre-installed; verify with `which pwsh` step and install via `brew install --cask powershell` only if missing)
    3. **Install Pester with version pin** (P3.2): `Install-Module Pester -RequiredVersion 5.6.1 -Force -SkipPublisherCheck -Scope CurrentUser`. Pin to a specific 5.x version to avoid behavior drift. Pester 5.x supports Pester 3.4 assertion syntax (`Should Be` without `-Be`) in legacy compatibility mode. On Windows (PS 5.1), the built-in Pester 3.4 is used — install only on macOS.
    4. Run `. tests/Run-Tests.ps1` via `pwsh`
    5. Upload `tests/last-run.json` as artifact
  - **Windows leg**: Use `powershell` (PS 5.1 with built-in Pester 3.4) to maintain parity with developer machines. Do NOT install Pester 5.x on Windows — the test syntax is written for Pester 3.4.
  - Note: The workflow file lives in `.github/workflows/` which is a real directory (not junctioned). This is fine — `.github/` is real, only the managed subdirs are junctions/symlinks.
- **Test Scenarios**:
  - ✅ Happy path: CI passes on both platforms
  - 🛑 Edge case: Pester version differences (3.4 on Windows vs 5.x on macOS)
  - ❌ Error path: pwsh not available on macOS runner → install step handles it
- **Tests**: CI itself is the test
- **Acceptance criteria**: Green CI on both `windows-latest` and `macos-latest`

### Phase 5: Documentation & Finalization

#### 9. Update documentation
- **Requirements**: R1
- **Files**: `docs/installation.md` (modify), `README.md` (modify)
- **Details**:
  - Add macOS section to `docs/installation.md`:
    - Clone path: `~/.compound-gpid` (or custom)
    - Install: `bash ~/.compound-gpid/scripts/install.sh`
    - Link: `cg-link` (after terminal restart)
    - Unlink/Update same as Windows pattern
  - Add macOS badge/mention to README.md
  - Document: "On macOS, `cg-link` creates symlinks instead of junctions. Behavior is identical."
  - Document `install.sh --uninstall` for cleanup
- **Test Scenarios**:
  - ✅ Happy path: new user follows Mac instructions successfully
- **Tests**: Documentation content tested by existing `prompt-tools.Tests.ps1` patterns (check for broken links)
- **Acceptance criteria**: Mac user can follow docs from clone to working `cg-link`

#### 10. Fix backslash paths in PowerShell scripts for cross-platform
- **Requirements**: R12, R7
- **Files**: `scripts/helpers.ps1` (modify), `scripts/link.ps1` (modify), `tests/Run-Tests.ps1` (modify), `tests/helpers.Tests.ps1` (modify), `tests/run-tests-runner.Tests.ps1` (modify)
- **Details**:
  - **Critical**: On macOS pwsh, `Join-Path $base "subdir\file.ext"` does NOT normalize the backslash. `[System.IO.Path]::DirectorySeparatorChar` is `/` on macOS, and `Path.Combine` treats `\` as a literal character — producing paths like `/repo/tests\charter.Tests.ps1` which don't exist.
  - **Fix pattern**: Replace all `Join-Path $base "dir\file"` with nested calls: `Join-Path (Join-Path $base "dir") "file"`
  - **Files and specific fixes**:
    - `tests/Run-Tests.ps1`: `Join-Path $repoRoot "tests\$name.Tests.ps1"` → `Join-Path (Join-Path $repoRoot "tests") "$name.Tests.ps1"`  (this is the most critical — breaks ALL test execution on macOS)
    - `tests/Run-Tests.ps1`: `Join-Path $repoRoot "tests\last-run.json"` → nested
    - `tests/Run-Tests.ps1`: `Join-Path $repoRoot "tests\.last-run.tmp"` → nested
    - `tests/helpers.Tests.ps1`: `. (Join-Path $repoRoot "scripts\helpers.ps1")` → nested
    - `tests/run-tests-runner.Tests.ps1`: all backslash Join-Path patterns → nested
    - `scripts/helpers.ps1`: `Join-Path $TemplateDir ".github\copilot-instructions.template.md"` → `Join-Path (Join-Path $TemplateDir ".github") "copilot-instructions.template.md"`
    - `scripts/link.ps1`: `Join-Path $TargetGithubDir "prompts\cg-setup.prompt.md"` → nested
  - **Validation**: After all fixes, run the full test suite on macOS pwsh. Every test file must be found and executed (not skipped with "file not found").
- **Test Scenarios**:
  - ✅ Happy path: `New-CopilotInstructions` works on macOS pwsh
  - 🛑 Edge case: path with spaces on macOS
- **Tests**: Existing `helpers.Tests.ps1` covers this — must pass on macOS
- **Acceptance criteria**: `helpers.Tests.ps1` passes on macOS without path errors

## Testing Strategy

- **Single test runner**: Pester via `pwsh` on both platforms
- **Platform detection**: `$script:OnWindows` / `$script:OnMacOS` helper variables
- **Conditional tests**: Junction tests on Windows, symlink tests on macOS
- **Bash integration tests**: Dedicated `tests/bash-scripts.Tests.ps1` skipped on Windows
- **CI as the parity gate**: GitHub Actions matrix ensures both platforms stay green
- **No weakening**: Existing Windows tests remain exactly as-is; new macOS tests are additive

## Documentation Checklist
- [ ] `docs/installation.md` — macOS install section
- [ ] `README.md` — platform support mention
- [ ] `scripts/install.sh` — inline usage comments
- [ ] `scripts/link.sh` — inline comments explaining each step
- [ ] `scripts/unlink.sh` — inline comments
- [ ] `scripts/update.sh` — inline comments and usage documentation

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `Join-Path` backslash on macOS pwsh produces invalid paths | ALL tests silently skip on macOS CI (0 tests run, CI green) | Step 10 fixes every occurrence with nested Join-Path; CI verifies non-zero test count |
| Pester version mismatch (3.4 on Windows PS 5.1, 5.x on macOS pwsh) | Syntax incompatibilities or behavior differences | Pin Pester 5.6.1 on macOS CI; use only Pester 3.4-compatible syntax; Windows leg uses PS 5.1 built-in |
| Shell profile corruption on install | User loses shell config | Marker-block pattern (same as PS1); `--uninstall` rollback; backup `.zshrc` before modify |
| Symlinks not followed by some editors | Plugin content invisible | VS Code/Positron verified to follow symlinks; document limitation for other editors |
| Template substitution in bash (`sed`) — values contain `/` | `copilot-instructions.md` malformed or sed error | Use pipe `\|` delimiter in sed; fall back to `python3` for values containing `\|` |
| macOS file path case sensitivity (APFS default: insensitive) | Path lookups fail on case-sensitive volumes | Use exact case in all file references (already the practice) |
| `readlink -f` used accidentally (GNU-only) | `cg-unlink` fails on macOS | Plan specifies `readlink` without `-f`; test validates on macOS CI |
| Git executable bit lost when committing from Windows | Mac users get "Permission denied" on first run | `git add --chmod=+x` enforced in Step 5; `.gitattributes` ensures LF line endings |
| `$IsWindows` undefined on PS 5.1 | Junction tests silently skipped on Windows | Platform helper uses `$env:OS -eq "Windows_NT"` fallback |
| `CG_INTERNAL_CALL` not propagated in bash | Double copilot-instructions.md regeneration on `cg-link` | Explicitly set env var in link.sh before calling update.sh |

## Out of Scope

- Linux support (deferred — bash scripts will likely work but not tested/documented)
- Refactoring existing `.ps1` scripts
- PowerShell requirement for Mac consumers (explicitly rejected)
- Homebrew formula / tap for distribution
- `create-release.ps1` macOS equivalent (developer-only script, maintainer uses Windows or pwsh)
