---
date: 2026-05-22
type: review
depth: standard
scope: commit
commit: 91d4a8c
subject: "fix(install): strip stale cg-* function defs from shell profile on upgrade"
files_reviewed:
  - scripts/install.sh
  - tests/bash-scripts.Tests.ps1
agents:
  - cg-code-quality
  - cg-testing
  - cg-architecture
  - cg-documentation
  - cg-reproducibility
  - cg-performance
  - cg-data-quality
auto_escalation: scripts/ directory → cg-data-quality added
findings_total: 22
findings_open: 0
findings_fixed: 22
findings_skipped: 0
status: closed
triage_date: 2026-05-29
findings_open: 22
findings_fixed: 0
findings_skipped: 0
status: open
---

# Review: install.sh stale cg-* function migration

**Commit**: `91d4a8c` — `fix(install): strip stale cg-* function defs from shell profile on upgrade`
**Branch**: `compound-research`
**Files**: `scripts/install.sh` (+44 lines Step 4a), `tests/bash-scripts.Tests.ps1` (+60 lines migration test)

---

## Summary

The change adds a Python heredoc (Step 4a) to `install.sh` that removes stale `cg-*()` shell function definitions, `COMPOUND_GPID_DIR` exports, and old `# Compound GPID` headers from the user's shell profile on upgrade. This addresses the macOS bug where old function-based installs shadow the new `bin/` wrappers.

Seven agents reviewed the code. No P0 blockers. **Two genuine P1 bugs** in the Python migration logic (blank-collapse write guard, symlink handling), plus **five test coverage P1s** (multiline function bodies, missing cg-index(), test isolation risk). The version control audit found no issues.

---

## P1 — Must Fix Before Merge

### [P1.1] cg-data-quality — `install.sh:278` — Blank-collapse fires without stale lines, silently rewrites profile

**Why**: `if final != lines:` triggers the file write whenever `final` differs from `lines` — which includes blank-line collapse changes (e.g., `\n\n\n` → `\n\n`), even when zero stale `cg-*` lines were removed. On a profile with consecutive blanks but no stale functions, every `install.sh` run silently rewrites the file and prints the misleading message `"Removed stale cg-* function definitions"` when no such lines were present.

**Fix**: Gate the write on whether stale lines were actually found:
```python
cleaned = [line for line in lines if not any(p.match(line) for p in stale)]

if cleaned != lines:          # ← write guard: stale lines found
    # now build final (with blank-collapse)
    final = []
    prev_blank = False
    for line in cleaned:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        final.append(line)
        prev_blank = is_blank
    # ... write ...
```
Change `if final != lines:` → `if cleaned != lines:` so the write only happens when stale lines were removed.

---

### [P1.2] cg-data-quality — `install.sh:276-280` — `os.replace` severs symlinks, breaks dotfiles managers

**Why**: `tempfile.mkstemp(dir=os.path.dirname(path))` uses the symlink path's directory. `os.replace(tmp_path, path)` atomically **replaces the symlink itself** with a new regular file. Users with dotfiles managers (`~/.zshrc → ~/dotfiles/zshrc`) silently lose the symlink — `~/.zshrc` becomes a standalone file, `~/dotfiles/zshrc` is unchanged. No error, no warning.

**Fix**: Resolve the symlink before writing:
```python
real_path = os.path.realpath(path)
tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(real_path))
try:
    with os.fdopen(tmp_fd, 'w') as f:
        f.writelines(final)
    os.replace(tmp_path, real_path)  # write to target, not symlink
except Exception:
    try: os.unlink(tmp_path)
    except (OSError, FileNotFoundError): pass
    raise
```

---

### [P1.3] cg-code-quality — `install.sh:248` — `import sys, re, tempfile, os` on one line (PEP 8 E401)

**Why**: Multiple imports on one line violates PEP 8 E401. Python style convention requires one import per line.

**Fix**:
```python
import sys
import re
import tempfile
import os
```

---

### [P1.4] cg-code-quality — `install.sh:278-282` — Bare `except:` clauses catch `BaseException`

**Why**: Both `except:` clauses (outer exception handler and inner cleanup) catch `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit` in addition to application errors — violating PEP 8 E722.

**Fix**:
```python
    except Exception:
        try: os.unlink(tmp_path)
        except (OSError, FileNotFoundError): pass
        raise
```

---

### [P1.5] cg-testing — `bash-scripts.Tests.ps1:205-210` — Multiline function bodies not removed (potential profile corruption)

**Why**: Regex `^cg-\w+\s*\(\)` matches the opening line of a multiline function (`cg-link() {`) but not the body or closing brace. If any real user's profile had multiline-formatted functions, migration removes the declaration line but leaves orphaned bash code:
```bash
    pwsh "$COMPOUND_GPID_DIR/scripts/link.ps1" "$@"
}
```
This corrupts the profile silently — the test passes, but bash syntax breaks.

**Fix**: Either (a) extend the regex to capture multiline function bodies (complex), or (b) add a test with multiline-formatted seed content and assert body lines are gone too. Minimum: add multiline variant to seed and verify `pwsh` lines are removed. The production regex should handle multiline bodies since the old install.sh format used single-line functions, but explicit test coverage is critical.

---

### [P1.6] cg-testing — `bash-scripts.Tests.ps1:205-210` — `cg-index()` function not in seed or assertions

**Why**: Very old installs had a `cg-index()` function added to the profile. The regex `^cg-\w+\s*\(\)` will match it, but the test neither seeds it nor verifies its removal. The test could pass while silently missing a gap.

**Fix**: Add `cg-index() { python3 "$COMPOUND_GPID_DIR/scripts/cg_index.py" "$@"; }` to the stale seed content, then assert `($profileContent -match 'cg-index\s*\(\)') | Should -Be $false`.

---

### [P1.7] cg-reproducibility — `bash-scripts.Tests.ps1:181-231` — Test isolation not guaranteed: `$env:HOME` may not propagate to bash

**Why**: The test sets `$env:HOME` and `$env:SHELL` in PowerShell then invokes `& bash install.sh`. Bash may read system-level `/etc/passwd` or login scripts during startup and override `$HOME` to the real user home. If `install.sh` resolves `~/.zshrc` to the real profile, the test pollutes the user's actual shell configuration.

**Fix**: After running `install.sh`, verify the **real** user profile was not modified:
```powershell
$realProfile = Join-Path $originalHome ".zshrc"
$realMTimeBefore = if (Test-Path $realProfile) { (Get-Item $realProfile).LastWriteTime } else { $null }
# ... run install.sh ...
$realMTimeAfter = if (Test-Path $realProfile) { (Get-Item $realProfile).LastWriteTime } else { $null }
($realMTimeBefore -eq $realMTimeAfter) | Should -Be $true
```

---

## P2 — Should Fix

### [P2.1] cg-architecture — `install.sh:72` — `--uninstall` leaves stale function artifacts in profile

**Why**: The `--uninstall` handler removes the fenced `# --- Compound GPID ---` block but does NOT run Step 4a's stale function cleanup. A user who upgraded from old function-based install to new bin/ install and then uninstalls would have their `cg-*()` shell functions remain in the profile.

**Fix**: Run the Step 4a Python heredoc inside the `--uninstall` handler after fenced-block removal.

---

### [P2.2] cg-architecture — `scripts/update.sh` — `cg-update --fix` does not trigger migration

**Why**: `--fix` is the documented "repair broken install" path — exactly what affected users would run. It does `git clean && git checkout && git pull` but never touches the shell profile.

**Fix**: After `git pull` in the `--fix` handler, exec `install.sh` to re-run the full profile cleanup.

---

### [P2.3] cg-code-quality — `install.sh:283` — Dead variable `removed` computed but never used

**Why**: `removed = sum(1 for a, b in zip(lines, final + [''] * len(lines)) if a != b)` is computed after the write but never referenced. The `print()` two lines below doesn't use it.

**Fix**: Remove the `removed = ...` line entirely.

---

### [P2.4] cg-code-quality — `bash-scripts.Tests.ps1:184` — `$fakeShell` is misleading — it is actually used

**Why**: Variable named `$fakeShell` implies it's a stub, but it's the real value passed as `$env:SHELL` to influence which profile file `install.sh` targets.

**Fix**: Rename to `$testShell`.

---

### [P2.5] cg-testing — `bash-scripts.Tests.ps1:181-231` — Non-CG profile content not verified as preserved

**Why**: Test only checks that CG content is removed, not that pre-existing user shell config survives. A faulty implementation that truncates the profile would still pass.

**Fix**: Seed with identifiable non-CG content (`export MY_VAR="important"`, `my_func() { echo "hello"; }`), then assert both are present after migration.

---

### [P2.6] cg-testing — `bash-scripts.Tests.ps1:181-231` — Blank-line collapse behavior not tested

**Why**: Blank-collapse is an explicit feature in the Python code but not exercised by the test.

**Fix**: Seed with triple-blank lines between stale entries, assert no `\n\n\n+` patterns remain after migration.

---

### [P2.7] cg-testing — `bash-scripts.Tests.ps1:181-231` — Fresh install (no stale content) not tested

**Why**: The happy path (clean profile, no stale functions, first install) is not covered. If Step 4a has a bug on clean files it would go undetected.

**Fix**: Add `It "migration step is a no-op on profile with no stale content"` seeding only non-CG user content and verifying profile is unchanged.

---

### [P2.8] cg-testing — `bash-scripts.Tests.ps1:181-231` — Migration idempotency not verified

**Why**: Running `install.sh` twice after migration should produce identical output. Not tested.

**Fix**: Run `install.sh` twice, compare profile content: `$profileAfterFirst | Should -Be $profileAfterSecond`.

---

### [P2.9] cg-testing — `bash-scripts.Tests.ps1:181-231` — Profile shell syntax not validated post-migration

**Why**: Test verifies string patterns but not that the result is valid bash. Orphaned lines (P1.5) would pass current assertions.

**Fix**: `$syntaxCheck = & bash -c ". '$tmpZshrc' && echo valid" 2>&1; $syntaxCheck | Should -Match 'valid'`

---

### [P2.10] cg-documentation — `install.sh:6-13` — File header "What this does" list missing Step 4a

**Why**: The file-header comment documents Steps 1, 1b, 2, 3, 4 but not Step 4a. Users reading the header have no idea the script modifies their profile to remove old artifacts.

**Fix**: Add `#   4a. Removes stale cg-*() shell functions and COMPOUND_GPID_DIR exports from profile (migration from pre-bin/ installs).` to the header list.

---

### [P2.11] cg-documentation — `install.sh:243-246` — Inline comment doesn't explain the shadowing priority

**Why**: The comment says old functions "must be removed" but doesn't explain *why* — shell functions have higher precedence than PATH entries and shadow the bin/ wrappers.

**Fix**: Add: `# Shell functions have higher precedence than PATH entries, so these stale definitions shadow the new bin/ wrappers and must be removed for the upgrade to work.`

---

### [P2.12] cg-documentation — `docs/installation.md` — No upgrade guidance for stale function artifacts

**Why**: The docs cover fresh install, pinning, and repair but not the pre-bin/ → bin/ migration path. Users who hit the cg-link error have no documentation to consult.

**Fix**: Add a "Upgrading from pre-bin/ versions" section explaining the issue and that re-running `install.sh` fixes it automatically.

---

### [P2.13] cg-performance — `install.sh:276` — `mkstemp` creates file with mode `0o600`, silently changes profile permissions

**Why**: `tempfile.mkstemp()` creates with `0o600`. After `os.replace()`, the profile inherits that mode, potentially stripping the original `0o644`. Happens on every profile-modifying install run.

**Fix**:
```python
original_mode = os.stat(real_path).st_mode & 0o777
os.chmod(tmp_path, original_mode)
```
Add before the `with os.fdopen(...)` call.

---

### [P2.14] cg-data-quality — `install.sh:250` — No explicit UTF-8 encoding; `UnicodeDecodeError` propagates as raw traceback

**Why**: `open(path, 'r')` uses system-default encoding. A `.zshrc` with non-UTF-8 bytes raises `UnicodeDecodeError` outside the `try/except`, causing an ugly Python traceback and script abort.

**Fix**:
```python
try:
    with open(real_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    print(f"Warning: {real_path} contains non-UTF-8 bytes; skipping migration.", file=sys.stderr)
    sys.exit(0)
```
Also use `encoding='utf-8'` on the write side.

---

## P3 — Nice to Have

### [P3.1] cg-architecture — `install.sh:253` — `^# Compound GPID\s*$` regex too broad

**Why**: Removes any line that is exactly `# Compound GPID` (with optional trailing whitespace), including user-written comments with the same text. The functional stale artifacts (`COMPOUND_GPID_DIR` export, function defs) are already covered by the other two patterns.

**Fix**: Consider removing this pattern entirely. The old unfenced header appears between the `COMPOUND_GPID_DIR` export and function definitions, so removing those two lines will leave an orphaned blank comment — which the blank-collapse step would leave as a single blank line. Acceptable.

---

### [P3.2] cg-documentation — `bash-scripts.Tests.ps1:178` — Test `Describe` block could clarify the shadowing mechanism

**Why**: Future maintainers won't understand why this migration matters without context.

**Fix**: Add inline comment above the `Describe` block: `# Shell functions have higher precedence than PATH entries; stale cg-*() defs shadow bin/ wrappers.`

---

### [P3.3] cg-code-quality — `bash-scripts.Tests.ps1:219-222` — Test regex patterns duplicate production patterns with no cross-reference

**Why**: If the stale patterns in `install.sh` change, the test patterns won't auto-update and the review is silent.

**Fix**: Add comment: `# Patterns mirror the 'stale' list in install.sh Step 4a — keep in sync.`

---

### [P3.4] cg-testing — `bash-scripts.Tests.ps1:211` — No `Test-Path` assertion after symlink creation

**Why**: If the symlink to `scripts/` fails silently, the test setup is invalid but `install.sh` runs anyway, giving misleading results.

**Fix**: `(Test-Path $tmpInstallScripts) | Should -Be $true` immediately after the `New-Item -SymbolicLink` call.

---

## Version Control Audit

**Result**: ✅ All PASS

| Check | Result |
|---|---|
| Conventional commits format | ✅ `fix(install): strip stale cg-* function defs from shell profile on upgrade` |
| Type correctness (`fix` vs `feat`) | ✅ `fix` correct for migration/cleanup |
| Single responsibility | ✅ Implementation + corresponding test, no unrelated changes |
| Sensitive data / credentials | ✅ None |
| Absolute paths / hardcoded values | ✅ Uses `$HOME`-relative and dynamic path expansion |
| `.gitignore` completeness | ✅ No new artifacts need tracking |

---

## Triage Recommendations

**Fix immediately (blocks safe upgrade for users):**
- P1.1 — Wrong write guard (silent blank-collapse rewrites)
- P1.2 — Symlink severance (dotfiles manager users)
- P1.3 — Single-line imports (PEP 8)
- P1.4 — Bare `except:` clauses
- P1.5 — Multiline function body test gap
- P1.6 — Missing `cg-index()` in test seed

**Fix before PR merge:**
- P2.3 — Dead `removed` variable
- P2.5 — Non-CG content preservation test
- P2.10 — Header documentation missing Step 4a
- P2.11 — Inline comment missing shadowing explanation
- P2.13 — mkstemp file permission preservation

**Can batch for follow-up:**
- P1.7, P2.1, P2.2, P2.4, P2.6–P2.9, P2.12, P2.14, P3.1–P3.4
