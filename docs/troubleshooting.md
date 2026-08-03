# Troubleshooting

Known issues and step-by-step fixes for Compound GPID.

> For installation help, see [Installation](installation.md). For workflow guidance, see [Workflow](workflow.md).

---

## Python not found

> **Added in v0.10** — `install.ps1` and `install.sh` now require Python 3.8+. This is a breaking change for users who have never installed Python.

**Windows symptom** (during `install.ps1`):
```
Python is required but not found (checked: python3, python, py).
```

**Windows symptom** (when running `cg-index` or `cg-token-audit` directly):
```
ERROR: Python is not available (checked: python3, python, py).
```

**Cause**: `cg-index` (`scripts/cg_index.py`) is the knowledge indexer that powers `cg-learnings-researcher` tiered retrieval and the `/cg-compound` workflow. `cg-token-audit` runs the Python context/model audit that powers `/cg-token-audit`. Both require Python 3.8+. Compound GPID probes `python3`, then `python`, then `py` and accepts the first real Python executable whose `--version` output starts with `Python`. On Windows, `python3` in a fresh install may point to a Windows Store stub that opens the Store App instead of running Python; the wrappers reject that stub.

**Fix (Windows)**:
```powershell
# Option 1: winget (recommended)
winget install Python.Python.3.11

# Option 2: direct download
# https://www.python.org/downloads/
# Check "Add python.exe to PATH" during install
```
After installing, open a new terminal and verify one of `python3 --version`, `python --version`, or `py --version` prints `Python 3.x`. Then re-run `install.ps1`.

**Fix (macOS)**:
```bash
# Install Xcode Command Line Tools (ships python3)
xcode-select --install

# Or install via Homebrew
brew install python@3.11
```

**Note**: if Python is absent, install/update/link operations that need Python will stop or skip Python-backed refreshes with a warning. The prompt files themselves remain usable once linked. `cg-index`, `/cg-brain-rebuild`, and `/cg-token-audit` are unavailable until Python is installed.

---

## Brainstorm or Plan view is missing or stale

Run the one-file freshness check from the project root:

```bash
cg-render-artifact --check .cg-docs/plans/YYYY-MM-DD-example.md
```

It reports the expected view as `missing`, `stale`, or `current`. For one-file
recovery, run:

```bash
cg-render-artifact .cg-docs/plans/YYYY-MM-DD-example.md
```

The explicit command works even when `artifact-html: false`. A validation,
security, path, or write failure leaves canonical Markdown and any prior valid
view unchanged and prints the exact expected view path plus the same recovery
command. Do not edit the HTML to repair it.

If the command is not found, restart the terminal after installation. If Python
is not found, follow the installation steps above. Open Design is not required:
it is design-time only and is never part of rendering or recovery.

## Generic Markdown output is missing, stale, or differently owned

Run the one-file generic freshness check from the project root:

```bash
cg-publish-markdown --check docs/guide.md
```

Recover a missing or stale same-owner view with
`cg-publish-markdown docs/guide.md`. Output defaults to
`.cg-docs/views/documents/docs/guide.html`. Use `--output` only for a portable
relative `.html` destination in `.cg-docs/views/documents/`.

If publication reports corrupt, unowned, or differently owned output, the file
is preserved. Inspect its provenance and either select the correct source or
move the conflicting file before rerunning. An unknown recorded theme requires
`--theme reference`. Recovery is non-clobbering; if another process wins the
destination, preserve both the winning bytes and any reported recovery file.

Brainstorms and Plans cannot be recovered through the generic command. Run
`cg-render-artifact <source>` so strict validation remains authoritative.

---

## `cg-update` (or `cg-link`, `cg-unlink`) not recognized after install

**Windows symptom**:
```
cg-update: The term 'cg-update' is not recognized as a name of a cmdlet,
function, script file, or executable program.
```

**macOS symptom**:
```
bash: cg-update: command not found
```

This happens right after running the installer, even in a "new" terminal tab.

**Cause**: `install.ps1` writes `C:\WBG\.compound-gpid\bin` (or `$env:USERPROFILE\.compound-gpid\bin`) to your user `PATH` in the Windows registry. However, VS Code's integrated terminal inherits its environment from the VS Code process, which in turn inherits from **Explorer.exe**. Explorer only re-reads the registry when it receives a `WM_SETTINGCHANGE` message. Until Explorer gets that broadcast, every new terminal tab — including ones opened after `install.ps1` ran — will be missing the new entry.

**Fix (fastest)**: Add the path to the current terminal session manually, then re-run `install.ps1` so the broadcast fires:

```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server

$env:PATH = "$cg\bin;" + $env:PATH
& "$cg\install.ps1"
```

After this, open a **brand new terminal tab** and `cg-update` will work.

**Fix (alternative)**: Sign out of Windows and sign back in. This forces Explorer to re-read the registry, so all new processes (including VS Code) inherit the updated PATH automatically.

**Verify the PATH is set**:
```powershell
$env:PATH -split ';' | Select-String 'compound'
# Should print: C:\WBG\.compound-gpid\bin
```

**Verify the bin directory exists and contains the wrappers**:
```powershell
Get-ChildItem "C:\WBG\.compound-gpid\bin"   # adjust path if needed
# Should list: cg-link.cmd, cg-unlink.cmd, cg-update.cmd, cg-index.cmd,
# cg-brain-init.cmd, cg-token-audit.cmd
```

> **PATH length truncation**: If `C:\WBG\.compound-gpid\bin` is present in the registry
> but never appears in a live terminal (even after a sign-out), your combined system + user
> PATH may be too long for Windows to merge without truncation. Fix: remove duplicate
> entries from your user PATH.
> ```powershell
> $raw = (reg query "HKCU\Environment" /v PATH) |
>     Where-Object { $_ -match 'REG_' } |
>     ForEach-Object { ($_ -replace '.*REG_EXPAND_SZ\s+', '').Trim() }
> $deduped = ($raw -split ';' | Where-Object { $_ -ne '' } | Select-Object -Unique) -join ';'
> reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $deduped /f
> ```
> Then re-run `install.ps1` to trigger the broadcast.

**macOS cause**: `install.sh` writes a PATH block to `~/.zshrc` (or `~/.bashrc`). The PATH change only takes effect in **new shell processes** — terminal tabs that were already open when you installed won't see it.

**macOS fix**: Open a new terminal window (not tab in the same window), then run `cg-update`. Or source your profile in the current session:
```bash
source ~/.zshrc    # for zsh users (default on macOS)
# or
source ~/.bashrc   # for bash users
```

**Verify the PATH is set (macOS)**:
```bash
echo $PATH | tr ':' '\n' | grep compound
# Should print: /Users/<you>/.compound-gpid/bin
```

**Verify the bin directory exists (macOS)**:
```bash
ls ~/.compound-gpid/bin
# Should list: cg-link  cg-unlink  cg-update
```

> **Unrecognized shell warning**: if you use fish, nushell, or another non-bash/zsh shell, `install.sh` will warn that your shell is unrecognized and default to `~/.bashrc`. The PATH block is written there, but your actual shell may not source it. Add the export manually to your shell's config file:
> ```
> export PATH="$HOME/.compound-gpid/bin:$PATH"
> ```

---

## `.cg-version` missing or corrupted

**Symptom**: `cg-update` fails with an error about an invalid version, or unexpectedly pins to an unrecognised value.

**Cause**: The `.cg-version` file in your install directory was manually edited, truncated, or written incorrectly.

**Fix**: Delete the file and run `cg-update`. It defaults to `latest` (tracking `main`) when the file is absent.

**Windows:**
```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server
Remove-Item (Join-Path $cg ".cg-version") -ErrorAction SilentlyContinue
cg-update
```

**macOS:**
```bash
rm -f ~/.compound-gpid/.cg-version   # adjust path if you chose a different install location
cg-update
```

After this, `cg-update` runs in `latest` mode. To re-pin, run `cg-update v0.2.0` (or your desired tag).

---

## `cg-update` fails with "Updated 0 paths from the index"

**Symptom**:
```
cg-update
Checking for updates...
update.ps1 : Update failed: Updated 0 paths from the index
```

**Cause**: The global clone has an old version of `update.ps1` that crashes on PowerShell 5.1 before it can pull the fix.

**Fix — run these two commands once in any terminal** (substitute your install path: `C:\WBG\.compound-gpid` or `$env:USERPROFILE\.compound-gpid`):
```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server
git -C $cg checkout . 2>$null              # suppress stderr (PS5.1 stderr-to-error promotion)
git -C $cg pull --ff-only
```

This manually updates the global clone. After that, `cg-update` works normally from all projects.

> **If `pull --ff-only` fails** with `fatal: Not possible to fast-forward`, the global clone has an unexpected local commit. Fix it with:
> ```powershell
> git -C $cg reset --hard origin/main
> ```

**Then run `cg-update` from each linked project** to apply any structural migrations:
```powershell
cg-update  # run from your project root
```

If the issue persists, open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).

---

## `cg-update` fails due to untracked files or local changes

**Symptom**: `cg-update` fails with messages about untracked files, merge conflicts, or local changes in the global clone.

**Fix**: Use the built-in repair command (works on both Windows and macOS):
```bash
cg-update --fix
```

This cleans untracked files, discards local changes, and pulls the latest code. If `--fix` itself fails (e.g. the installed copy is too old), see the [Repairing a broken installation](installation.md#repairing-a-broken-installation) section.

---

## `. $PROFILE` fails with "Cannot dot-source" error (Constrained Language Mode)

**Symptom**:
```
. $PROFILE
Microsoft.PowerShell_profile.ps1 : Cannot dot-source this command because it was defined in a different language mode.
```

**Cause**: Your organization enforces Constrained Language Mode (CLM) via AppLocker or Windows Defender Application Control. OneDrive has redirected your Documents folder to a path CLM treats as untrusted, blocking profile dot-sourcing.

**Fix**: Re-install using the current approach (batch wrappers on PATH; no new profile registration):
```powershell
# Clone to your chosen path (see Installation > Choose your install path)
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"

# Run the installer
& "C:\WBG\.compound-gpid\install.ps1"

# Restart VS Code / Positron and your terminal
```

The installer automatically removes the exact managed `$PROFILE` block and
exact legacy wrappers from previous installs.

The byte-preserving profile cleanup intentionally uses .NET file and encoding
APIs and must run in FullLanguage mode. Those APIs are unavailable to the
helper in a CLM-restricted process, so it stops before changing the profile,
reports a warning, and leaves the file untouched rather than performing a
potentially lossy rewrite. Run the no-profile PATH wrapper directly, for
example `& "C:\WBG\.compound-gpid\bin\cg-update.cmd"`, or remove the exact
legacy function manually after backing up `$PROFILE`.

If you already have the current PATH-wrapper installation and do not want to
run the installer again, `cg-update` also removes exact legacy `cg-link`,
`cg-unlink`, and `cg-update` wrappers from `$PROFILE` before pulling updates.
The cleanup only removes the one-statement wrappers emitted by old Compound
GPID versions. It preserves customized functions, personal profile content,
and the profile's existing encoding and BOM. If a customized function has the
same name, remove or rename it manually after reviewing the warning; otherwise
it can continue to shadow the PATH wrapper in the current shell.

Cleanup preserves the profile's existing CRLF or LF line-ending style and
refuses to replace a symlinked or other reparse-point profile. In either case,
review the warning and remove the exact legacy wrapper from the real target
profile manually if needed.

### Updating from an already-running old updater

The updater must start with the old script that is already loaded in the
current PowerShell process. Therefore, a `cg-update` process that was started
from a pre-remediation installation cannot execute cleanup code that was added
by the update it pulls during that same process. If the first run reports that
the installation was updated but the old function still resolves in the
current shell, start a new terminal or run `cg-update` once more. The second
run starts the newly pulled updater and performs the profile cleanup. This
limitation does not apply to a fresh shell that starts the current updater.

---

## Upgrading from `$env:USERPROFILE\.compound-gpid` (old default path, local OneDrive machines only)

> **Remote server users**: `$env:USERPROFILE\.compound-gpid` is the correct path on a remote server -- no migration needed. Just re-run `install.ps1`.

If you are on a **local OneDrive machine** and previously installed to `$env:USERPROFILE\.compound-gpid`, you must migrate to `C:\WBG\.compound-gpid`. Follow the steps below **before** running a fresh install.

### Step A - Remove the old `$PROFILE` block

Run the current installer from the new location -- it removes old managed
blocks and exact legacy wrappers without changing the profile's encoding. If
an old `cg-update` function shadows the PATH wrapper, invoke the wrapper
directly so the profile is not loaded:

```powershell
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"   # remote server
Copy-Item -LiteralPath $PROFILE -Destination "$PROFILE.compound-gpid-backup" -Force
& "$cg\bin\cg-update.cmd" latest
```

If the `bin\cg-update.cmd` wrapper does not exist, run `install.ps1` from the
current clone instead. When the first direct run starts an older updater, run
the same wrapper once more after the pull so the newly installed updater can
perform the profile cleanup.

### Step B - Remove the old `bin\` directory from PATH

> **Note**: `[Environment]::GetEnvironmentVariable` is blocked in Constrained Language Mode. Use `reg.exe` instead -- it works in all language modes.

```powershell
$oldBin = "$env:USERPROFILE\.compound-gpid\bin"
$currentPath = (reg query "HKCU\Environment" /v PATH 2>$null |
    Where-Object { $_ -match 'PATH' }) -replace '.*REG_[A-Z_]+\s+', ''
$newPath = ($currentPath.Trim() -split ';' |
    Where-Object { $_ -and $_ -ne $oldBin }) -join ';'
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f
```

### Step C - Delete the old clone

```powershell
Remove-Item -Path "$env:USERPROFILE\.compound-gpid" -Recurse -Force
```

### Step D - Restart your terminal and IDE

Restart your terminal **and VS Code / Positron** to pick up the PATH change, then proceed with the [Installation](installation.md) steps.

---

## `cg-link` fails with a junction/symlink error

**Windows cause**: Windows requires Developer Mode to create directory junctions without admin rights on some configurations.

**Windows fix**: Enable Developer Mode:
Settings → System → For developers → Developer Mode → On

**macOS cause**: macOS symlink creation (`ln -s`) requires that the filesystem supports symlinks. On most APFS/HFS+ volumes this works without admin rights. Failures are most common when the install or project directory is on a network share, external FAT drive, or inside a cloud-synced folder that doesn't support symlinks (some configurations of OneDrive for Mac).

**macOS fix**: Move your install directory to a local APFS volume (e.g., `~/.compound-gpid`) and re-run:
```bash
bash ~/.compound-gpid/scripts/install.sh
# then from your project root:
cg-link
```

Then retry `cg-link` from your project root.

---

## `cg-link` skips a platform directory or config file

**Symptom**: `cg-link` completes but prints warnings such as:
```
.opencode/opencode.json exists and is not manifest-managed; skipping.
.github/prompts is a real directory; skipping this unit.
```

**Cause**: Compound GPID installs merge-safe platform units instead of replacing whole roots. If a selected unit already exists as a real directory or user-owned file, `cg-link` skips that unit and continues with the rest of the selected platforms.

**Fix**:
1. If the existing file/directory is intentional, leave it in place. For OpenCode config, apply the manual snippet printed by `cg-link` if needed.
2. If you want Compound GPID to manage that unit, move or remove the existing path, then re-run `cg-link`.
3. To install only one platform, run `cg-link --platforms opencode` or `cg-link --platforms copilot`.

---

## `cg-update` skips a managed platform config file

**Symptom**: `cg-update` prints:
```
Managed file modified by user, skipping refresh: .opencode/opencode.json
```

**Cause**: Strict config files cannot carry inline management comments. Compound GPID records checksums in `.compound-gpid/managed-files.json`. If your local copy no longer matches the recorded checksum, `cg-update` treats it as user-managed and preserves it.

**Fix**: Keep your version and manually merge any needed changes from the corresponding file in the Compound GPID install, or delete the file and manifest entry then re-run `cg-link` to restore CG management.

---

## Native target generation reports an ownership conflict

This section is for maintainers running `python scripts/cg_generate_targets.py
--all` in the Compound GPID source repository. It does not apply to consumer
`.compound-gpid/managed-files.json` warnings.

Generation fails before destructive cleanup for these states:

| Diagnostic/state | Meaning | Resolution |
|------------------|---------|------------|
| **modified stale** owned file | A path is stale, but its checksum differs from the prior `.compound-gpid-generated.json` entry. | Inspect the diff. Move an intentional canonical change into `.github/`; otherwise restore the generated file to its recorded bytes. Never delete it automatically. |
| **malformed manifest** or wrong schema/target/hash | Ownership cannot be proven. | Recover the manifest from version control after reviewing local changes, then rerun generation. Do not hand-author ownership for unknown files. |
| **unsafe path** or non-regular/symlink entry | A source, destination, or manifest path could escape/collide or cannot be safely hashed. | Correct the canonical path or mapping. Do not weaken validation or manually relocate generated output. |
| conflicting **unowned destination** | Existing user/maintainer content occupies an expected generated path with different bytes. | Compare it with the canonical source, then move, rename, or deliberately remove it before rerunning. Byte-identical unowned expected files may be safely adopted. |

An interrupted write may leave some new output bytes while the old manifest
remains because the manifest is written last. This is intentional recovery
behavior: leave the old manifest in place and rerun the generator. Preflight
accepts safely attributable prior or newly planned checksums and writes the new
manifest only after all files and checksum-guarded stale cleanup succeed.

If the conflict's ownership is uncertain, stop and have a maintainer resolve it;
do not delete the target tree, edit checksums, or substitute the consumer
managed-files manifest. After resolution, run the documentation/target tests and
the drift gate described in [Native Target Packaging](reference.md#verification-and-release-gates).

---

## VS Code crashed — what to do

If VS Code crashed or froze and you had to force-close it, follow these steps:

### Step 1: Restart VS Code

Reopen VS Code normally. Your workspace, open files, and terminal history are preserved across restarts. **No data is lost** if you committed recently — VS Code does not modify your git repository on crash.

### Step 2: Run `/cg-diagnose`

In the new Copilot Chat session, type:

```
/cg-diagnose
```

This command automatically:
- Checks for uncommitted changes or stashed work
- Locates and reads the VS Code crash logs
- Classifies the crash into a known category
- Presents a structured report with recovery steps and prevention advice

### Step 3: Follow the recommendations

`/cg-diagnose` will suggest specific recovery steps based on the crash category. Common next actions:
- Run `/cg-resume` to scan pending work and pick up where you left off
- Run `. tests\Run-Tests.ps1` to verify the test suite still passes
- Review `git diff` if a multi-file edit was interrupted mid-flight

### Quick self-service (if you don't want `/cg-diagnose`)

1. Check for lost work: `git status --short` — if files are modified, review `git diff` before committing
2. Check for stashed work: `git stash list`
3. Verify integrity: `. tests\Run-Tests.ps1` (canonical safe test runner)
4. Resume: run `/cg-resume` to see pending plans, open review findings, and roadmap progress

---

## Known Crash Categories

VS Code crashes in this project fall into well-documented categories.
`/cg-diagnose` classifies crashes automatically, but here is the reference
for manual investigation.

### Category A: Pester Unsafe Invocations

**Symptom**: VS Code becomes completely unresponsive immediately after (or during) a Pester test run. The terminal hangs with no output, or output arrives and then VS Code freezes. No error message — the window must be force-quit.

**Cause**: Four invocation patterns or conditions reliably trigger this crash:

1. **Directory-form invocation** — `Invoke-Pester tests/` runs all test files at once, including `link.Tests.ps1` and `unlink.Tests.ps1`, which create and delete directory junctions. When junction cleanup timing races with other tests, the VS Code extension host exhausts memory and hangs.

2. **`ExpandProperty TestResult` pipeline** — `Invoke-Pester ... -PassThru | Select-Object -ExpandProperty TestResult | Where-Object ...` materialises the full Pester result graph as .NET objects inside the PowerShell extension host process, exhausting its memory.

3. **`2>&1 | Select-String` pipeline** — `Invoke-Pester ... 2>&1 | Select-String ...` redirects stderr into stdout then filters. The interleaved stream serialization overwhelms the extension host — even on single-file runs of large test files (300+ tests). This pattern is especially dangerous because it is the natural reflex when debugging failing tests ("I want to see what failed").

4. **Verbose run inside a long session** — Running `Invoke-Pester tests\prompt-tools.Tests.ps1` (or any large test file) **without `-Quiet`** during a long fix-triage session floods the agent context window with 300+ test lines. VS Code crashes from context overflow even though PowerShell exits with code 0. This is a pure context-overflow crash — no forbidden pipeline is needed.

These patterns have caused **14+ confirmed VS Code crashes** in this repository.

**Log signatures**:
- `main.log`: `Extension host with pid ... exited` immediately after Pester run
- `terminal.log`: contains one of the forbidden patterns

**Safe alternatives**:

```powershell
# ✅ Canonical: run all tests safely (VS Code task or terminal)
. tests\Run-Tests.ps1

# ✅ Single file (full output — only in short sessions)
Invoke-Pester tests\roadmap.Tests.ps1

# ✅ Single file (counts only — always safe)
$r = Invoke-Pester tests\roadmap.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount

# ✅ See failure details (two-phase approach)
$r = Invoke-Pester tests\foo.Tests.ps1 -PassThru -Quiet
if ($r.FailedCount -gt 0) { Invoke-Pester tests\foo.Tests.ps1 }
```

**Long-session rule**: In a long fix-triage session (accumulated brainstorm + plan + review context), always use `-Quiet` on large test files (`prompt-tools.Tests.ps1` has 300+ blocks). Better: apply all fixes first, then run one test pass at the very end. For pure markdown edits (`.prompt.md`, `.agent.md`) that don't change frontmatter or tool lists, consider skipping the test run entirely and noting the prior passing state.

**Forbidden patterns** (never use these):

```powershell
# ❌ CRASHES VS CODE — directory form
Invoke-Pester tests/

# ❌ CRASHES VS CODE — ExpandProperty TestResult pipeline
Invoke-Pester tests\foo.Tests.ps1 -PassThru | Select-Object -ExpandProperty TestResult | Where-Object ...

# ❌ CRASHES VS CODE — 2>&1 redirect pipeline
Invoke-Pester tests\foo.Tests.ps1 2>&1 | Select-String -Pattern 'FAIL|error' | ...

# ❌ CRASHES VS CODE in long sessions — verbose run on large test file mid-session
Invoke-Pester tests\prompt-tools.Tests.ps1  # no -Quiet during long fix-triage
```

**VS Code task**: `Ctrl+Shift+P` → **Tasks: Run Task** → **Run all Pester tests (safe)** runs `tests/Run-Tests.ps1` automatically and can never use any forbidden pattern.

**Note on Pester version**: This project requires **Pester 4.10.1**. The Windows built-in Pester 3.4.0 cannot run the test suite — all assertions use `Should -Be` syntax (Pester 4+). Install with: `Install-Module Pester -RequiredVersion 4.10.1 -Force -SkipPublisherCheck -Scope CurrentUser`. `-Output Minimal` and `-Output None` are Pester 5 flags that don't work on Pester 4 — use `-Quiet` instead (it shows a deprecation warning on Pester 4 but works correctly).

**Full diagnosis**:
- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` — forbidden PowerShell patterns
- `.cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md` — context-window dilution; dual-location documentation
- `.cg-docs/solutions/testing-patterns/2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md` — `2>&1` debugging reflex
- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md` — long-session context overflow (PowerShell exits 0, crash is from context flooding)

---

### Category B: Long-Session Listener Accumulation

**Symptom**: VS Code becomes unresponsive and must be force-closed, but no Pester command was running. This typically happens during or after a long Copilot Chat session (multiple hours) with many tool calls — especially during rapid-fire file edits.

**Cause**: Event listener accumulation in the VS Code renderer process. Three sources compound over a long session:

1. **Chat panel rendering** — Each tool call response (file contents, terminal output, search results) renders as a tree item with attached event listeners. Over hundreds of tool calls, these listeners accumulate past the VS Code threshold.

2. **Terminal accumulation** — Each `run_in_terminal` tool call creates a terminal instance. Over a long session with many terminal operations, these pile up (visible in the terminal panel as 10–20+ tabs).

3. **Rapid-fire edit operations** — When the agent makes many file edits in quick succession (e.g., rewriting a large documentation file with 10+ sequential edits), the renderer struggles to keep up with the diff computation and tree view refresh.

The combination reaches a tipping point where the renderer thread becomes unresponsive. VS Code's main process detects this and may kill the window.

**Log signatures**:
- `main.log`: `CodeWindow: detected unresponsive` + `UnresponsiveSampleError` with 10+ samples
- `renderer.log`: `potential listener LEAK detected` with stack traces pointing to `renderAttachments`, `createDetachedTerminal`, or `_instantiateById`

**Prevention** (no permanent fix — this is a VS Code/Copilot Chat extension limitation):

1. **Start a new chat session every 2–3 hours** of intensive agent work. Close the old chat panel before starting a new one.
2. **Close unused terminals periodically**. Right-click in the terminal panel → **Kill Terminal** for any old sessions you no longer need.
3. **Avoid very long single turns** with 10+ sequential file edits. If a large rewrite is needed, consider breaking it across multiple user turns.
4. **Restart VS Code** if you notice sluggishness in the chat panel, terminal, or editor. The listener leaks do not recover — only a restart clears them.
5. **Commit and push before intensive operations** so no work is lost if VS Code crashes.

---

### Category C: Rapid-Fire Large Operations

**Symptom**: VS Code freezes during a multi-file edit turn where the agent is making many rapid changes (10+ `replace_string_in_file` calls in quick succession).

**Cause**: The renderer cannot keep up with diff computation and tree view refreshes for each edit. This is a subcategory of B (listener accumulation) but can trigger independently in shorter sessions if edits are dense enough.

**Log signatures**:
- `main.log`: `CodeWindow: detected unresponsive` with < 10 samples
- `renderer.log`: `.splice` errors or tree view rendering errors
- Copilot Chat log: many rapid requests (< 5s apart) just before crash
- No `potential listener LEAK detected` in renderer.log (distinguishes from Category B)

**Prevention**: Break large rewrites across multiple user turns. Commit after each logical unit of work.

---

### Category D: Extension Host Crash

**Symptom**: VS Code suddenly restarts or shows "Extension Host terminated unexpectedly" — not a freeze, but an abrupt crash.

**Cause**: An extension (any, not just Copilot) hit an unhandled exception or ran out of memory.

**Log signatures**:
- `exthost.log`: error stacktrace ending in process exit
- `main.log`: `Extension host with pid ... exited with code: 1` (non-zero exit code)
- No `CodeWindow: detected unresponsive` — crash was sudden, not a freeze

**Prevention**: Keep VS Code and extensions updated. If a specific extension crashes repeatedly, consider disabling it temporarily and reporting the issue.

---

## How to find VS Code crash logs

When VS Code crashes or freezes, the logs are at:

**Windows:**
```
%APPDATA%\Code\logs\<session-folder>\
```

**macOS:**
```
~/Library/Application Support/Code/logs/<session-folder>/
```

Key files:

| File | Contains |
|------|----------|
| `main.log` | Unresponsive window detection, extension host exits |
| `window<N>\renderer.log` | Listener leaks, rendering errors, tree view issues |
| `window<N>\exthost\exthost.log` | Extension host errors, activation failures |
| `terminal.log` | Terminal creation/destruction, shell output |
| `window<N>\exthost\GitHub.copilot-chat\GitHub Copilot Chat.log` | Copilot request timing, model calls |

To find the most recent logs:

**Windows:**
```powershell
Get-ChildItem "$env:APPDATA\Code\logs" -Recurse -Filter "*.log" |
    Where-Object { $_.Length -gt 0 } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 Name, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}}, LastWriteTime |
    Format-Table -AutoSize
```

To find the most recent window directory:
```powershell
$logBase = "$env:APPDATA\Code\logs"
$session = Get-ChildItem $logBase -Directory | Sort-Object Name -Descending | Select-Object -First 1
$window = Get-ChildItem $session.FullName -Directory -Filter "window*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Session: $($session.Name)"
Write-Host "Window:  $($window.FullName)"
```

**macOS:**
```bash
# Find the most recent session folder and list large logs
logbase="$HOME/Library/Application Support/Code/logs"
ls -t "$logbase" | head -1 | xargs -I{} find "$logbase/{}" -name '*.log' -size +0c | head -20
```

To open the logs folder directly:
```bash
open "$HOME/Library/Application Support/Code/logs"
```

---

## `cg-update` silently skips refreshing `copilot-instructions.md`

**Symptom**: Running `cg-update` from a linked project completes without errors, but `copilot-instructions.md` is not refreshed even though the management marker is present.

**Cause**: `cg-link` sets `CG_INTERNAL_CALL=1` in the environment of the subprocess that calls `update` to suppress the refresh step (to avoid doing it twice). The variable is cleared when the subprocess exits. The symptom appears when `CG_INTERNAL_CALL` is set in your current shell session — for example, if you sourced `link.sh` (`. scripts/link.sh`) and it exited abnormally, or if the variable was set manually. Subsequent `cg-update` calls in that shell inherit the variable and silently skip the refresh.

**Fix**: Open a new terminal — environment variables do not persist across sessions. Then run `cg-update` from your project root.

**Windows:**
```powershell
# Verify the stale variable is the cause (in the affected terminal):
$env:CG_INTERNAL_CALL   # prints "1" if stale

# Clear it manually (if you don't want to open a new terminal):
Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
cg-update
```

**macOS:**
```bash
# Verify the stale variable is the cause:
echo $CG_INTERNAL_CALL   # prints "1" if stale

# Clear it manually:
unset CG_INTERNAL_CALL
cg-update
```

---

> Still stuck? Open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).
> 
> See [Reference](reference.md) for a full list of commands and agents.

---

## GitHub Issues Integration

### `gh: command not found` or `'gh' is not recognized`

Install the GitHub CLI: https://cli.github.com

On Windows: `winget install GitHub.cli` or download from the site.

After install, authenticate: `gh auth login`

### `Not authenticated with GitHub` error from `/cg-issues`

Run `gh auth login` and follow the prompts (browser or token-based auth).

Verify after: `gh auth status`

### `/cg-issues backfill` creates duplicate issues

Duplicate prevention checks three tiers:
1. Stored `github.issueNumber` in `roadmap.json` — already linked.
2. Hidden body marker `<!-- compound-gpid-tracked: <feature-id> -->` — issue was created by Compound GPID.
3. Title similarity search — surfaced for user review.

GitHub search can be fuzzy. If a broad search appears to match a different hyphenated feature ID, verify the issue body contains the exact `compound-gpid-tracked: <feature-id>` marker before linking.

If a duplicate is created despite these checks, link the feature to the existing issue manually:

```
/cg-issues link
```

Then specify the existing issue number. The duplicate can be closed manually on GitHub.

### Missing labels cause `/cg-issues backfill` to fail

`/cg-issues backfill` validates that all required labels exist before creating an issue. When a label is missing, it surfaces a **create / skip / cancel** choice. Choosing **skip** omits the label from that issue. Choosing **create** creates the label via `gh label create` with a default color.

If a label creates inconsistency across issues, audit labels with `gh label list --repo <owner/repo>`.

### Linked issue number in `roadmap.json` is wrong or stale

Edit `roadmap.json` via `@cg-roadmap`. For example:

> "Update the `github.issueNumber` for feature `<feature-id>` to `<correct-number>` and set `issueUrl` to `<correct-url>`."

`@cg-roadmap` validates the URL format before writing.

### `/cg-commit-push-pr` adds `Refs #` for a closed issue

This is normal — `Refs #` is informational and does not reopen the issue. If the issue should close when the PR merges, ask the agent to change it to `Closes #` (it will confirm before updating the PR body).

### GitHub repository is inaccessible (`404` or permission error)

Check that you have at least **read** access to the repository: `gh repo view <owner/repo>`

For private repositories, ensure your `gh` auth token has the `repo` scope: `gh auth status --show-token`

The `project` scope is not required in v1 (GitHub Projects integration is out of scope).

### Adopted feature is stuck at `planned`

This is expected behavior. `/cg-issues adopt` intentionally creates new features at `status: "planned"` — it does not advance status automatically. To start work on the feature, use `@cg-roadmap` to update its status:

> "Update feature `<feature-id>` in milestone `<milestone-id>` to status `active`."

### `/cg-issues status` shows a closed GitHub issue

Roadmap status and GitHub issue state are tracked independently — a closed issue does not automatically update the roadmap. Options:

1. **Keep the linkage**: If work is complete, advance the roadmap feature status separately via `@cg-roadmap`.
2. **Update the linked issue**: Use `/cg-issues link` with a new open issue number to replace the stale reference.
3. **Remove the linkage**: Ask `@cg-roadmap` to clear the `github` block: "Remove the `github` block from feature `<feature-id>`."

### `/cg-strategy` or `/cg-resume` suggests `/cg-issues backfill`

This is expected when GitHub Issues are enabled and newly added, changed, active, planned, or otherwise relevant work items do not have a `github` block in `roadmap.json`. The prompt is a handoff only: `/cg-strategy` and `/cg-resume` do not create issues automatically.

After a one-time backlog backfill, this reminder should usually be delta-based. Use `/cg-issues backfill` for newly added unlinked roadmap items, or `/cg-issues link` when an existing GitHub issue should track the feature.
