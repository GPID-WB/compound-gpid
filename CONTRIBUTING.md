# Contributing to Compound GPID

Thank you for contributing! This guide covers everything you need to run tests
locally, understand the CI pipeline, and submit a well-formed PR.

---

## Table of Contents

1. [Local test setup](#local-test-setup)
2. [CI pipeline](#ci-pipeline)
3. [Cross-platform requirements](#cross-platform-requirements)
4. [Commit conventions](#commit-conventions)
5. [PR workflow](#pr-workflow)
6. [When to update docs](#when-to-update-docs)
7. [Self-review checklist](#self-review-checklist)

---

## Local test setup

The test suite uses [Pester 4.10.1](https://github.com/pester/Pester) and runs
on **both Windows and macOS**.

### Windows

```powershell
# Install Pester 4.10.1 (one-time setup)
Install-Module Pester -RequiredVersion 4.10.1 -Force -SkipPublisherCheck -Scope CurrentUser

# Run all tests (from the repo root)
. tests\Run-Tests.ps1

# Run a single test file
. tests\Run-Tests.ps1 -File link
```

> **Note**: Do not run `Invoke-Pester tests/` directly — it bypasses the safe
> runner that enforces junction-cleanup ordering.

### macOS / Linux

```bash
# Install pwsh (PowerShell) if not already installed
# macOS: brew install powershell

# Install Pester 4.10.1
pwsh -Command "Install-Module Pester -RequiredVersion 4.10.1 -Force -SkipPublisherCheck -Scope CurrentUser"

# Make bash scripts executable (one-time)
chmod +x scripts/install.sh scripts/link.sh scripts/unlink.sh scripts/update.sh

# Run all tests
pwsh -Command ". tests/Run-Tests.ps1"
```

### Adding a new test file

Every new `*.Tests.ps1` file must be registered in the `$testNames` array in
`tests/Run-Tests.ps1`. Unregistered files are skipped and the runner emits a
warning at the start of the run to flag the omission.

```powershell
# Run a single test file (stem name only — omit .Tests.ps1)
. tests\Run-Tests.ps1 -File link       # runs tests/link.Tests.ps1
. tests\Run-Tests.ps1 -File parity     # runs tests/parity.Tests.ps1
```

---

## CI pipeline

Every PR runs the following automated checks:

| Check | Tool | What it verifies |
|---|---|---|
| **Pester suite** | Pester 4.10.1 on `windows-2022` + `macos-14` | Unit and structural tests for all scripts |
| **Windows E2E smoke** | GitHub Actions (pwsh) | `link.ps1` creates junctions, `unlink.ps1 -Force` cleans up |
| **macOS E2E smoke** | GitHub Actions (bash) | `link.sh` creates symlinks, `unlink.sh --yes` cleans up |
| **Parity check** | `tests/parity.Tests.ps1` | `link.ps1` and `link.sh` define the same managed directories |
| **PR title lint** | `amannn/action-semantic-pull-request` | PR title follows Conventional Commits format |
| **Docs staleness** | `git diff` heuristic | Warns when `scripts/` changes have no matching `docs/` update |
| **Link check** | markdown link checker | No broken links in documentation |

A PR must pass all checks (except the docs staleness warning, which is
non-blocking) before it can be merged.

---

## Cross-platform requirements

Compound GPID ships dual scripts for each user-facing operation:

| Windows | macOS / Linux |
|---|---|
| `scripts/link.ps1` | `scripts/link.sh` |
| `scripts/unlink.ps1` | `scripts/unlink.sh` |
| `scripts/update.ps1` | `scripts/update.sh` |
| `scripts/install.ps1` | `scripts/install.sh` |

**Rule**: When you change behavior in one script, you must mirror the change in
its counterpart. This includes:

- **Managed directories** (`$ManagedDirs` / `MANAGED_DIRS`): Must be identical
  across the `.ps1`/`.sh` pair. The `parity` test enforces this in CI.
- **Verification file path**: Both scripts check the same file to confirm the
  link succeeded.
- **Gitignore marker**: Both scripts use the same block comment header.
- **Flags**: If you add a flag to one script (e.g., `-Force` / `--yes`), add
  the equivalent to the other.

The `tests/parity.Tests.ps1` test suite catches divergence automatically.

### Platform-specific code

- Windows uses **junctions** (`link.ps1`, `unlink.ps1`). Cleanup must never
  use `Remove-Item -Recurse` on a directory tree that may contain junctions —
  this can follow junctions into the Compound GPID installation and delete
  source files. Use the 2-level scan pattern from the E2E teardown step.
- macOS/Linux uses **symlinks** (`link.sh`, `unlink.sh`). `rm -rf` is safe
  because it does not follow symlinks.

---

## Commit conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/).
The PR title is used as the squash-merge commit message and **must** follow
the format:

```
type(optional-scope): short description
```

**Allowed types:**

| Type | When to use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or improving tests |
| `refactor` | Code change that is not a fix or feature |
| `chore` | Build process, CI, tooling |
| `data` | Data pipeline or data file changes |
| `analysis` | Analysis or reporting changes |

**Examples:**
- `fix(link): replace hardcoded backslash with multi-arg Join-Path`
- `feat(unlink): add -Force flag for non-interactive CI use`
- `docs: add CONTRIBUTING.md`
- `test(parity): cross-script managed-dirs parity checks`

The CI `commit-lint` check will fail if the PR title does not conform.

---

## PR workflow

1. **Fork** the repository and create a feature branch:
   ```
   git checkout -b fix/my-bug-description
   ```
2. **Make changes** and write or update tests.
3. **Run the test suite locally** (see [Local test setup](#local-test-setup)).
4. **Push** and open a PR against `main`.
5. **Fill in the PR template** — complete all checklist items.
6. **Wait for CI** — all required checks must pass.
7. A maintainer will review and merge once checks pass.

Branch naming convention: `type/short-description`  
Examples: `feat/new-managed-dir`, `fix/unlink-confirmation-ci`

---

## When to update docs

Update the relevant documentation files when your change:

- Adds, removes, or renames a CLI flag or command
- Changes an error message or user-visible output
- Changes installation steps or system requirements
- Introduces a new script or removes an existing one
- Changes the managed directories or gitignore behavior

**Files to update:**

| File | When |
|---|---|
| `docs/installation.md` | Setup steps, system requirements change |
| `docs/reference.md` or `docs/reference/commands.md` | Command flags, behavior, or output format change |
| `README.md` | High-level feature or usage change |
| `RELEASE_NOTES.md` | Updated automatically at release time |

The CI docs staleness check will post a warning annotation if `scripts/` files
change without a corresponding `docs/` update.

---

## Self-review checklist

Before requesting review, verify each dimension:

- [ ] **E2E verified** — Ran `cg-link` / `cg-unlink` on a fresh project
  directory locally on your platform (Windows: junctions created; macOS:
  symlinks created; `cg-setup.prompt.md` accessible through the link).

- [ ] **Cross-script parity** — Changes to `.ps1` scripts are mirrored in
  `.sh` equivalents and vice versa. Managed dirs, verification file, and
  gitignore entries match.

- [ ] **Docs updated** — `docs/installation.md`, `docs/reference.md`, or
  another navigable page reflects behavioral changes — or explicitly N/A if no
  user-facing behavior changed.

- [ ] **Backward compatible** — Users with existing installs can run
  `cg-update` and then `cg-link` without errors.

- [ ] **Idempotent** — Running the changed command twice produces no errors,
  no duplicate entries, no extra files.

- [ ] **Commit conventions** — PR title follows `type(scope): description`
  format with an allowed type.

- [ ] **Security reviewed** — Path handling does not introduce traversal
  vulnerabilities or symlink-following attacks. No user-controlled input flows
  into path construction without validation. On Windows, junction cleanup uses
  the safe 2-level scan pattern — no `Remove-Item -Recurse` on directory
  trees that may contain junctions (this can follow junctions into the
  compound-gpid installation and delete source files).

See also: [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)
