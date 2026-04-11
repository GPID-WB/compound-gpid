# Troubleshooting

Known issues and step-by-step fixes for Compound GPID.

> For installation help, see [Installation](installation.md). For workflow guidance, see [Workflow](workflow.md).

---

## `cg-update` (or `cg-link`, `cg-unlink`) not recognized after install

**Symptom**:
```
cg-update: The term 'cg-update' is not recognized as a name of a cmdlet,
function, script file, or executable program.
```
This happens right after running `install.ps1`, even in a "new" terminal tab.

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
# Should list: cg-link.cmd, cg-unlink.cmd, cg-update.cmd
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

---

## `.cg-version` missing or corrupted

**Symptom**: `cg-update` fails with an error about an invalid version, or unexpectedly pins to an unrecognised value.

**Cause**: The `.cg-version` file in your install directory was manually edited, truncated, or written incorrectly.

**Fix**: Delete the file and run `cg-update`. It defaults to `latest` (tracking `main`) when the file is absent.

```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server
Remove-Item (Join-Path $cg ".cg-version") -ErrorAction SilentlyContinue
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

**Fix**: Use the built-in repair command:
```powershell
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

**Fix**: Re-install using the current approach (batch wrappers on PATH - no profile manipulation):
```powershell
# Clone to your chosen path (see Installation > Choose your install path)
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"

# Run the installer
& "C:\WBG\.compound-gpid\install.ps1"

# Restart VS Code / Positron and your terminal
```

The installer automatically removes any old `$PROFILE` block from previous installs.

---

## Upgrading from `$env:USERPROFILE\.compound-gpid` (old default path -- local OneDrive machines only)

> **Remote server users**: `$env:USERPROFILE\.compound-gpid` is the correct path on a remote server -- no migration needed. Just re-run `install.ps1`.

If you are on a **local OneDrive machine** and previously installed to `$env:USERPROFILE\.compound-gpid`, you must migrate to `C:\WBG\.compound-gpid`. Follow the steps below **before** running a fresh install.

### Step A - Remove the old `$PROFILE` block

Run `install.ps1` from the new location -- it will remove the old profile block automatically. If you want to clean it up manually first:

```powershell
$p = Get-Content $PROFILE -Raw
$p = $p -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", ""
Set-Content $PROFILE $p.TrimEnd()
```

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

**Cause**: Windows requires Developer Mode to create directory junctions without admin rights on some configurations.

**Fix**: Enable Developer Mode:
Settings → System → For developers → Developer Mode → On

Then retry `cg-link` from your project root.

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

**Cause**: Three invocation patterns reliably trigger this crash:

1. **Directory-form invocation** — `Invoke-Pester tests/` runs all test files at once, including `link.Tests.ps1` and `unlink.Tests.ps1`, which create and delete directory junctions. When junction cleanup timing races with other tests, the VS Code extension host exhausts memory and hangs.

2. **`ExpandProperty TestResult` pipeline** — `Invoke-Pester ... -PassThru | Select-Object -ExpandProperty TestResult | Where-Object ...` materialises the full Pester result graph as .NET objects inside the PowerShell extension host process, exhausting its memory.

3. **`2>&1 | Select-String` pipeline** — `Invoke-Pester ... 2>&1 | Select-String ...` redirects stderr into stdout then filters. The interleaved stream serialization overwhelms the extension host — even on single-file runs of large test files (300+ tests). This pattern is especially dangerous because it is the natural reflex when debugging failing tests ("I want to see what failed").

These patterns have caused **10+ confirmed VS Code crashes** in this repository.

**Log signatures**:
- `main.log`: `Extension host with pid ... exited` immediately after Pester run
- `terminal.log`: contains one of the forbidden patterns

**Safe alternatives**:

```powershell
# ✅ Canonical: run all tests safely (VS Code task or terminal)
. tests\Run-Tests.ps1

# ✅ Single file (full output)
Invoke-Pester tests\roadmap.Tests.ps1

# ✅ Single file (counts only)
$r = Invoke-Pester tests\roadmap.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount

# ✅ See failure details (two-phase approach)
$r = Invoke-Pester tests\foo.Tests.ps1 -PassThru -Quiet
if ($r.FailedCount -gt 0) { Invoke-Pester tests\foo.Tests.ps1 }
```

**Forbidden patterns** (never use these):

```powershell
# ❌ CRASHES VS CODE — directory form
Invoke-Pester tests/

# ❌ CRASHES VS CODE — ExpandProperty TestResult pipeline
Invoke-Pester tests\foo.Tests.ps1 -PassThru | Select-Object -ExpandProperty TestResult | Where-Object ...

# ❌ CRASHES VS CODE — 2>&1 redirect pipeline
Invoke-Pester tests\foo.Tests.ps1 2>&1 | Select-String -Pattern 'FAIL|error' | ...
```

**VS Code task**: `Ctrl+Shift+P` → **Tasks: Run Task** → **Run all Pester tests (safe)** runs `tests/Run-Tests.ps1` automatically and can never use any forbidden pattern.

**Note on `-Output Minimal` / `-Output None`**: These flags are Pester 5 syntax and fail on the Pester 3.4 that ships with Windows ("ambiguous parameter" error). Use `-Quiet` instead.

**Full diagnosis**: `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md`

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

```
%APPDATA%\Code\logs\<session-folder>\
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

---

> Still stuck? Open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).
> 
> See [Reference](reference.md) for a full list of commands and agents.

