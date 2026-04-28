# .github/hooks/hello-hook-guard.ps1
# PoC hook script: validates VS Code Copilot agent-scoped Stop hook API.
#
# TEMPORARY -- delete after Phase 0 validation completes.
#
# Purpose: When invoked by the Stop hook, this script:
#   1. Reads the hook payload from stdin and logs it for inspection.
#   2. If stop_hook_active is false/absent: blocks the stop and logs the block response.
#   3. If stop_hook_active is true: allows the stop and logs the allow response.
#
# After invoking @cg-hello-hook, inspect these files to validate assumptions:
#   .cg-docs/autopilot-runs/poc-hook-input-<timestamp>.json -- raw stdin payload (or poc-hook-input-error-<timestamp>.json if malformed)
#   .cg-docs/autopilot-runs/poc-hook-output-block.json  -- first-stop block response (overwritten each run)
#   .cg-docs/autopilot-runs/poc-hook-output-allow.json  -- second-stop allow response (overwritten each run)
#
# NOTE: Output files (poc-hook-output-*.json) reflect the most recent invocation only.
#       Re-running the PoC overwrites them. Input logs are timestamped and accumulate per run.
#
# Validation criteria (all must pass to proceed to Phase 1):
#   A1: poc-hook-input-<timestamp>.json exists  → hook fires at all
#   A2: input contains stop_hook_active field → stdin format is as expected
#   A3: block response causes agent to continue  → hookSpecificOutput.decision=block works
#   A4: second stop (stop_hook_active:true) succeeds → anti-recursion guard works
#
# NOTE: Script blocks indefinitely if VS Code does not close stdin -- acceptable for PoC.
# NOTE: Set-StrictMode and $ErrorActionPreference = "Stop" are intentionally omitted --
#       hook scripts must fail open; a logging error must never prevent Write-Output.

# P2.x comments reference Phase 2 follow-up items tracked in the implementation plan.
# P2.2: Guard against empty $PSScriptRoot (occurs when invoked via -Command instead of -File)
if (-not $PSScriptRoot) { Write-Error 'Must be invoked with -File, not -Command'; exit 1 }

$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
# P2.3 NOTE: In linked user projects, $PSScriptRoot resolves to the compound-gpid install dir,
# so logs land in the install dir's .cg-docs/autopilot-runs/, not the user's workspace.
# For Phase 0 PoC (running inside compound-gpid repo), this is not a blocker.
# Phase 1 must derive workspace root from the hook payload or $PWD instead.
$logDir   = Join-Path $repoRoot ".cg-docs" "autopilot-runs"

# Ensure log directory exists (may not on first run); New-Item -Force is idempotent for existing dirs
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

# CLM sentinel: if running in Constrained Language Mode, [IO.File] methods are blocked.
# Log a warning file via Set-Content (always CLM-safe) so the investigator knows logging is degraded.
if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') {
    try { Set-Content -Path (Join-Path $logDir 'poc-hook-clm-warning.txt') `
              -Value 'CLM active -- [IO.File] logging unavailable; only Set-Content paths produce output' `
              -Encoding UTF8 } catch { <# logging failure - do not block hook output #> }
}

# Read the full stdin payload (CLM-safe: $input works in PS5.1 Constrained Language Mode)
# Empty payload treated as first-stop (block) — intentional fail-open for empty/missing stdin
$rawInput = ($input -join "`n")

# Log raw input regardless of parse outcome (A1, A2 validation)
# Per-invocation timestamp captured once so input log and error log filenames are correlatable
$ts = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$inputLog = Join-Path $logDir "poc-hook-input-$ts.json"
try { Set-Content -Path $inputLog -Value $rawInput -Encoding UTF8 } catch { <# logging failure - do not block hook output #> }

# Parse JSON -- fail open if malformed (don't crash the hook)
$hookData = $null
if ($rawInput -and $rawInput.Trim()) {
    try {
        $hookData = $rawInput | ConvertFrom-Json
    } catch {
        # Malformed JSON: log error to separate file, preserving raw log for A2 diagnostics (P2.6)
        $errorLog = Join-Path $logDir "poc-hook-input-error-$ts.json"
        try { $errJson = @{ error = "malformed stdin JSON"; detail = $_.Exception.Message } | ConvertTo-Json
              Set-Content -Path $errorLog -Value $errJson -Encoding UTF8 } catch { <# logging failure - do not block hook output #> }
        Write-Output "{}"
        exit 0
    }
}

# Anti-recursion guard: if stop_hook_active is true, allow the stop (A4)
# Case-insensitive key lookup: VS Code hook API casing is unverified (Assumption 3)
$stopHookActive = $false
if ($hookData) {
    $key = $hookData.PSObject.Properties.Name | Where-Object { $_ -ieq 'stop_hook_active' } | Select-Object -First 1
    if ($key) { $stopHookActive = $hookData.$key -eq $true }
}

if ($stopHookActive) {
    $allowOutput = "{}" # Empty JSON object = allow signal per VS Code hook API contract
    try { Set-Content -Path (Join-Path $logDir "poc-hook-output-allow.json") -Value $allowOutput -Encoding UTF8 } catch { <# logging failure - do not block hook output #> }
    Write-Output $allowOutput
    exit 0
}

# Block the stop on the first attempt (A3)
# Emits hookSpecificOutput wrapper and decision field, exercising A3.
# Assumption 3: hookSpecificOutput.decision=block schema is unverified — investigate if A3 fails.
$blockResponse = [ordered]@{
    hookSpecificOutput = [ordered]@{
        hookEventName = "Stop"
        decision      = "block"
        reason        = "Hook PoC is blocking the stop (first attempt). This message means A1+A3 pass. Check poc-hook-input.json to verify A2."
    }
} | ConvertTo-Json -Depth 2 -Compress

try { Set-Content -Path (Join-Path $logDir "poc-hook-output-block.json") -Value $blockResponse -Encoding UTF8 } catch { <# logging failure - do not block hook output #> }
Write-Output $blockResponse
exit 0
