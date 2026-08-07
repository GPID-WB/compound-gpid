---
language: "both"
project-type: "tool"
review-depth: "thorough"
r-syntax: "data.table-collapse"
created: "2026-03-04"
cg-schema-version: "2026-04-07-r-syntax-dialect"
---
# Compound GPID — Project Config

This file configures Compound GPID for this project. It is version-controlled and shared across the team.

## Language: Python, R and PowerShell
## Project Type: tool
## Review Depth: thorough

## Notes

### ⚠️ Pester Safety Rules (CRITICAL — violating these crashes VS Code)

1. **Never run the full test suite as a directory**: `Invoke-Pester tests/` crashes VS Code. Always specify individual files.
2. **Never pipeline `-PassThru` output through `Select-Object -ExpandProperty TestResult`**: this pattern freezes VS Code reliably.
3. **Safe pattern** (single file): `Invoke-Pester tests/roadmap.Tests.ps1 -Quiet`
4. **Safe pattern** (PassThru if needed): assign first, then inspect — do NOT pipeline directly:
   ```powershell
   $r = Invoke-Pester tests/roadmap.Tests.ps1 -PassThru -Quiet
   $r | Select-Object TotalCount, PassedCount, FailedCount
   ```

Load `cg-skill-pester-safety` before writing any `Invoke-Pester` command — it contains a pre-flight checklist and safe patterns for all scenarios.

See also: `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md`
