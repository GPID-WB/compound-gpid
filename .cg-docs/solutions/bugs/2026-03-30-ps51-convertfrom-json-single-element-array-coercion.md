---
date: 2026-03-30
title: "PS 5.1: ConvertFrom-Json returns bare PSCustomObject for single-element arrays"
category: "bugs"
language: "both"
tags: [powershell, ps51, json, convertfrom-json, array, coercion, type-guard, schema-validation]
root-cause: "PowerShell 5.1 ConvertFrom-Json deserialises a single-element JSON array as a bare PSCustomObject, not a one-element array. Type guards using -isnot [array] therefore pass for single-element arrays, silently skipping the array branch."
severity: "P1"
---

# PS 5.1: ConvertFrom-Json Returns Bare PSCustomObject for Single-Element Arrays

## Problem

Schema validation code that loops over `roadmap.json` `milestones` and `features`
arrays silently skipped records whenever a JSON array contained exactly one element.
The `-isnot [array]` type guard — intended to reject strings incorrectly passed as
arrays — evaluated to `$false` for a single-element array parsed in PS 5.1, so the
element was never iterated.

Symptom: a roadmap with one milestone validated as if it had zero milestones.
No error was raised; ids, statuses, and required fields were never checked.

```powershell
# Broken: -isnot [array] evaluates to $false for a single PSCustomObject
if ($Roadmap.milestones -isnot [array]) {
    $errors += "milestones must be an array"
    return $errors
}

foreach ($m in $Roadmap.milestones) {  # never entered when milestones = one object
    ...
}
```

## Root Cause

PowerShell 5.1 `ConvertFrom-Json` does not preserve JSON array semantics for
single-element arrays. It returns:

| JSON input                  | PS 5.1 type          | PS 7+ type          |
|-----------------------------|----------------------|---------------------|
| `[{"id":"a"},{"id":"b"}]`   | `Object[]`           | `Object[]`          |
| `[{"id":"a"}]`              | `PSCustomObject`     | `Object[]` (fixed)  |
| `[]`                        | `Object[]`           | `Object[]`          |

This means `-isnot [array]` is `$true` for a single-element array in PS 5.1 and
`$false` for multi-element arrays, making array-vs-scalar type checks unreliable.

PS 7+ fixed this behaviour; the issue only affects Windows `powershell.exe` (5.1).

## Solution

Two-pronged fix:

1. **Explicit scalar rejection** — test against concrete scalar types (`[string]`,
   `[int]`, `[bool]`) before any array wrapping. These will never be valid array
   inputs regardless of PS version.

2. **`@()` wrapping** — force array coercion on the value before iterating. `@(x)`
   always produces an array: a bare object becomes a one-element array, an existing
   array stays as-is, and `$null` becomes an empty array.

```powershell
# Correct: scalar-type whitelist check, then @() for coercion
if ($Roadmap.milestones -is [string] -or $Roadmap.milestones -is [int] -or
    $Roadmap.milestones -is [bool]) {
    $errors += "milestones must be an array"
    return $errors
}

# @() wrapping handles the PS 5.1 single-element coercion issue
$milestones = @($Roadmap.milestones)

foreach ($m in $milestones) {
    ...
}
```

Apply the same pattern to nested arrays (e.g. `features` inside each milestone):

```powershell
if ($m.features -is [string] -or $m.features -is [int] -or $m.features -is [bool]) {
    $errors += "Milestone '$($m.id)': features must be an array"
    continue
}
$features = @($m.features)
foreach ($f in $features) { ... }
```

## Prevention

- Never use `-is [array]` or `-isnot [array]` on values that came from
  `ConvertFrom-Json` in code that must run on PS 5.1.
- Always wrap `ConvertFrom-Json` output arrays with `@(...)` before iterating.
- Add a PS 5.1 compatibility test with a single-element array next to every
  multi-element test for schema validators and JSON consumers.

```powershell
# Pester test: validate single-element array round-trip
It "validates a roadmap with a single milestone (PS 5.1 coercion)" {
    $json = '{"schemaVersion":"compound-gpid-roadmap-v1","milestones":[{"id":"m1","title":"T","objective":"O","status":"planned","features":[]}]}'
    $parsed = $json | ConvertFrom-Json
    $errors = Test-RoadmapSchema $parsed
    $errors | Should -BeNullOrEmpty
}
```

## Related

- `.cg-docs/solutions/bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md`
  — another PS 5.1 encoding/parsing gotcha
- `.cg-docs/solutions/testing-patterns/2026-03-30-derived-invariant-validation-in-schema-tests.md`
  — the derived-status invariant check added alongside this fix
