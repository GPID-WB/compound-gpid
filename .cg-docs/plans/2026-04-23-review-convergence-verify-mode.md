---
date: 2026-04-23
title: "Review convergence: mode:verify for /cg-review"
status: completed
completed-date: 2026-04-23
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-23-review-convergence-verify-mode.md"
language: "both"
estimated-effort: "medium"
tags: [review, fix-triage, convergence, prompt-design, workflow]
---

# Plan: Review Convergence — `mode:verify` for `/cg-review`

## Objective

Add a `mode:verify` argument to `/cg-review` that switches agents into
verification mode — checking whether prior fixes landed correctly and only
reporting genuinely new issues. This makes the review-fix cycle converge in
≤2 rounds (full review → fix → verify → fix → done) instead of spiraling
indefinitely.

## Context

The current system treats every review identically: agents see all changed
files and flag everything they can find. When fix-triage applies fixes, the
new code becomes fresh surface area for the next review. Evidence:

- **competitive-repo-review-system**: 3 rounds (27 → 26 → 27 findings)
- **prompt-prose-compression**: 4 review files

Root causes: "missing test for the fix you just added" (~22% of round-2
findings) and cross-file reference drift from renames. The `mode:autofix`
argument pattern already exists, so `mode:verify` follows the same convention.

The brainstorm decided on Approach 1: explicit `mode:verify` argument with a
suppression policy (P0/P1 never suppressed, P2/P3 suppressed on fix code,
cross-file breakage always reported).

## Requirements

| ID  | Requirement                                         | Source     |
|-----|-----------------------------------------------------|------------|
| R1  | `mode:verify` argument recognized by `/cg-review`   | Brainstorm |
| R2  | Verify mode auto-locates the most recent review file with ≥1 `fixed` finding | Brainstorm |
| R3  | Prior review findings + fix status passed to agents as context | Brainstorm |
| R4  | Suppression policy: P0/P1 never suppressed           | Brainstorm |
| R5  | Suppression policy: P2/P3 suppressed on fix-consequence code | Brainstorm |
| R6  | Cross-file breakage always reported regardless of severity | Brainstorm |
| R7  | Verify mode forces `light` depth (`@cg-code-quality` + `@cg-testing`) | Brainstorm |
| R8  | Verify review saved as `<stem>-verify-review.md` with `parent-review:` + `type: verification` frontmatter | Brainstorm + existing convention |
| R9  | `/cg-fix-triage` Step 5 suggests `mode:verify` instead of `light` | Brainstorm |
| R10 | `mode:verify` disables content-based depth overrides (Step 1.5) | Design — verify should stay light, not auto-escalate |
| R11 | Unrecognized argument warning updated to list `mode:verify` | Consistency |

## Implementation Steps

### 1. Add `mode:verify` argument parsing to `/cg-review` Step 1

- **Requirements**: R1, R11
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  - In Step 1 item 3, add `mode:verify` alongside `mode:autofix`:
    ```
    - `mode:verify` — Enable verification mode (see Step 1.7). Locates the
      most recent review file with fixed findings and passes prior context to
      agents with a suppression policy. Forces `light` depth.
    ```
  - Update the unrecognized-argument warning to list `mode:verify`:
    ```
    Recognized: `mode:autofix`, `mode:verify`, `light`, `standard`, `thorough`.
    ```
  - Add: "`mode:autofix` and `mode:verify` are mutually exclusive. If both
    are passed, warn: 'Cannot combine `mode:autofix` and `mode:verify` —
    using `mode:verify`.' and ignore `mode:autofix`."
- **Test Scenarios**:
  - ✅ `mode:verify` documented in prompt text
  - ✅ Unrecognized-argument warning lists `mode:verify`
  - 🛑 `mode:autofix` and `mode:verify` mutual exclusion documented
- **Tests**: Add Pester test block for `mode:verify` argument recognition
- **Acceptance criteria**: `mode:verify` appears in Step 1 argument list,
  unrecognized-argument message lists it, mutual exclusion with `mode:autofix`
  is documented.

### 2. Add Step 1.7: Locate prior review and build suppression context

- **Requirements**: R2, R3, R10
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  Insert a new Step 1.7 (between Step 1.5 and Step 2) that only executes
  when `mode:verify` is active:

  ```markdown
  ### Step 1.7: Build Verification Context (mode:verify only)

  Skip this step unless `mode:verify` was passed.

  1. Scan `.cg-docs/reviews/` for the most recent review file (by `date:`
     frontmatter, then alphabetical) where the `findings:` map contains at
     least one `fixed` entry. **Skip files whose name ends in
     `-verify-review.md`** — verify reviews are not valid prior reviews for
     a new verify pass; the correct prior is always a standard review
     (ending in `-review.md` without the `-verify-` infix). If none found:
     warn "No prior review with fixed findings found. Falling back to
     normal review." and disable verify mode.
  2. Read the prior review file. Extract:
     - The list of finding IDs and their statuses (`fixed`, `skipped`, `open`).
     - The `plan:` field and the review filename (for linking the verify
       review via `parent-review:` frontmatter — see Step 4).
  3. Build the **suppression context** — a text block passed to every agent
     in Step 2:

     > **Verification mode**: This is a verify pass following fix-triage.
     > The prior review file is `<filename>` with these resolved findings:
     > <list of fixed finding IDs and one-line descriptions>.
     >
     > **Suppression policy**:
     > - **P0/P1**: Always report. Never suppress correctness, security, or
     >   data-integrity issues regardless of whether the code was written as
     >   a fix.
     > - **P2/P3 on fix-consequence code**: Suppress findings that are
     >   direct, expected consequences of an applied fix. Examples:
     >   "missing dedicated test for a ≤5-line guard clause added by a fix,"
     >   "style inconsistency in a renamed identifier," "missing docstring
     >   on a helper extracted during a fix." These are expected artifacts,
     >   not new problems.
     > - **Cross-file breakage**: Always report, at any severity. If a fix
     >   in file A broke a reference, import, or contract in file B, that is
     >   a genuine new issue.
     > - **When in doubt, report**: If unsure whether a finding is a fix
     >   consequence or a genuine new issue, report it. False positives are
     >   cheaper than missed bugs.

  4. Force depth to `light` (override any config or argument).
  5. Skip Step 1.5 content-based depth overrides — verify passes must stay
     light to ensure convergence.
  ```
- **Test Scenarios**:
  - ✅ Step 1.7 heading present in prompt
  - ✅ Suppression policy text contains "P0/P1" never-suppress rule
  - ✅ Suppression policy text contains "Cross-file breakage"
  - 🛑 Fallback when no prior review found
  - ❌ Prompt instructs to skip Step 1.5 overrides in verify mode
- **Tests**: Pester tests for Step 1.7 existence and suppression policy content
- **Acceptance criteria**: Step 1.7 exists, suppression policy covers all
  three rules (P0/P1, P2/P3, cross-file), fallback documented.

### 3. Update Step 2 agent dispatch for verification mode

- **Requirements**: R3, R4, R5, R6, R7
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  After the existing agent dispatch instructions in Step 2, add a verify-mode
  block:

  ```markdown
  **Verify mode agent dispatch** (when `mode:verify` is active):
  Dispatch only `@cg-code-quality` and `@cg-testing` (light depth, forced).
  Include the suppression context from Step 1.7 in each agent's dispatch.
  Do NOT apply content-based depth overrides — the verify pass stays at
  light depth regardless of file content.
  ```
- **Test Scenarios**:
  - ✅ Verify mode dispatch text present in Step 2
- **Tests**: Pester test for verify-mode dispatch instruction presence
- **Acceptance criteria**: Step 2 contains explicit verify-mode dispatch
  instructions referencing suppression context from Step 1.7.

### 4. Update Step 3.5 save-filename pattern for verify reviews

- **Requirements**: R8
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  In Step 3.5, add a verify-mode filename rule:
  ```markdown
  If `mode:verify` is active: strip the trailing `-review` from the prior
  review filename stem, then append `-verify-review.md`. Example: prior
  review `2026-04-21-foo-review.md` → stem without `-review`:
  `2026-04-21-foo` → filename: `2026-04-21-foo-verify-review.md`.

  Use the existing verify-review frontmatter schema (matching
  `2026-04-17-context-layer-verify-review.md`):
  ```yaml
  ---
  date: YYYY-MM-DD
  depth: light
  parent-review: .cg-docs/reviews/<prior-review-filename>
  type: verification
  findings:
    P1.1: open
  ---
  ```
  The `parent-review:` field links to the prior standard review (not the
  upstream plan). The `type: verification` field distinguishes verify
  reviews from standard reviews in tooling and search.
  ```
- **Test Scenarios**:
  - ✅ Verify review filename pattern documented (strip `-review` then append)
  - ✅ `parent-review:` and `type: verification` frontmatter documented
- **Tests**: Pester test for `verify-review.md` filename pattern and
  `parent-review` frontmatter instruction in prompt
- **Acceptance criteria**: Step 3.5 documents the verify-review filename
  convention with the strip-then-append rule, and uses `parent-review:` +
  `type: verification` frontmatter schema.

### 5. Update `/cg-fix-triage` Step 5 handoff

- **Requirements**: R9
- **Files**: `.github/prompts/cg-fix-triage.prompt.md`
- **Details**:
  Change the Step 5 suggestion from:
  ```
  "Run `/cg-review light` to verify the fixes."
  ```
  to:
  ```
  "Run `/cg-review mode:verify` to verify the fixes converged."
  ```
  Also update `/cg-review` Step 5, which currently says:
  ```
  1. **`/cg-review light`** — Verify that the applied fixes pass
  ```
  Change to:
  ```
  1. **`/cg-review mode:verify`** — Verify fixes converged (suppresses
     fix-consequence P2/P3 findings)
  ```
- **Test Scenarios**:
  - ✅ `mode:verify` appears in fix-triage Step 5
  - ✅ `mode:verify` appears in review Step 5
- **Tests**: Pester tests for `mode:verify` in both handoff locations
- **Acceptance criteria**: Both prompts suggest `mode:verify` instead of
  `light` for post-fix-triage verification.

### 6. Update documentation

- **Requirements**: R1, R7, R8
- **Files**: `docs/reference.md`, `docs/workflow.md`
- **Details**:
  - **reference.md**: Update the `/cg-review` row to list `mode:verify`:
    ```
    `/cg-review [light|standard|thorough] [mode:autofix|mode:verify]`
    ```
    Add brief description of verify mode.
  - **workflow.md**: Add `mode:verify` to the invocation table. Update
    **both** post-fix-triage references:
    - Line ~278: the "*After applying fix-triage results*" scenario →
      change `/cg-review light` to `/cg-review mode:verify`.
    - Line ~325: the "*Verify after fixing*" scenario → change
      `/cg-review light` to `/cg-review mode:verify`.
    Add a scenario: "*After applying fix-triage results*: Run
    `/cg-review mode:verify` to confirm fixes converged — suppresses
    fix-consequence P2/P3 findings."
- **Test Scenarios**:
  - ✅ `mode:verify` mentioned in reference.md
  - ✅ `mode:verify` mentioned in workflow.md
  - ✅ No remaining `/cg-review light` in a post-fix-triage context in
    workflow.md
- **Tests**: Not Pester-tested (documentation only)
- **Acceptance criteria**: Both docs mention `mode:verify` with usage guidance.

### 7. Add Pester tests

- **Requirements**: R1, R2, R3, R4, R5, R8
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**:
  Add a new Describe block (following the `mode:autofix` block pattern at
  line ~1278):

  ```powershell
  Describe "cg-review.prompt.md - mode:verify argument" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
      $content = Get-Content $promptFile -Raw -Encoding UTF8

      It "documents mode:verify argument" {
          ($content -match 'mode:verify') | Should Be $true
      }

      It "includes Step 1.7 for verification context" {
          ($content -match 'Step 1\.7') | Should Be $true
      }

      It "suppression policy never suppresses P0/P1" {
          ($content -match '(?s)P0/P1.*[Nn]ever suppress') | Should Be $true
      }

      It "suppression policy suppresses P2/P3 on fix-consequence code" {
          ($content -match '(?s)P2/P3.*fix-consequence') | Should Be $true
      }

      It "suppression policy always reports cross-file breakage" {
          ($content -match '(?s)[Cc]ross-file breakage.*[Aa]lways report') | Should Be $true
      }

      It "forces light depth in verify mode" {
          ($content -match '(?si)force.*light|light.*forced') | Should Be $true
      }

      It "verify review filename pattern documented" {
          ($content -match 'verify-review\.md') | Should Be $true
      }

      It "instructs to skip Step 1.5 overrides in verify mode" {
          ($content -match '(?s)Skip Step 1\.5') | Should Be $true
      }

      It "documents parent-review frontmatter for verify reviews" {
          ($content -match 'parent-review') | Should Be $true
      }
  }

  Describe "cg-fix-triage.prompt.md - mode:verify handoff" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
      $content = Get-Content $promptFile -Raw -Encoding UTF8

      It "suggests mode:verify instead of review light" {
          ($content -match 'mode:verify') | Should Be $true
      }
  }
  ```
- **Test Scenarios**:
  - ✅ All assertions pass against the updated prompt files
  - 🛑 Regex patterns match the exact wording in the prompts (verify manually)
- **Tests**: Self-testing (these ARE the tests)
- **Acceptance criteria**: All new Pester assertions pass.

## Testing Strategy

All tests are structural — they verify the prompt text contains the required
instructions. No runtime behavior to test (prompts are natural-language
instructions, not executable code).

Test file: `tests/prompt-tools.Tests.ps1`  
Pattern: Follow existing `mode:autofix` test block (line ~1278) as template.
Run via `execution_subagent` using `. tests\Run-Tests.ps1`.

## Documentation Checklist

- [ ] `docs/reference.md` — `/cg-review` row updated with `mode:verify`
- [ ] `docs/workflow.md` — invocation table and scenarios updated
- [ ] Inline comments in `cg-review.prompt.md` — agent list comment at top
      does not need updating (no new agents added)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-suppression: agents hide real P2 bugs behind "fix consequence" | Missed defects survive to merge | "When in doubt, report" rule in suppression policy; P0/P1 never suppressed |
| No prior review file found when `mode:verify` used | User confusion | Explicit fallback: warn and fall back to normal review |
| `mode:autofix` + `mode:verify` confusion | Ambiguous behavior | Mutual exclusion: `mode:verify` wins, warn user |
| Suppression policy wording too vague → agents interpret differently | Inconsistent verify results | Concrete examples in the policy (guard clause, renamed identifier, extracted helper) |
| Second `mode:verify` picks a verify-review as "prior review" | Cascading filenames, non-standard finding IDs in suppression context | Step 1.7 skips `*-verify-review.md` files — only standard reviews are valid priors |

## Out of Scope

- Changing agent `.agent.md` files (suppression is passed as dispatch context,
  not baked into agent definitions)
- Automating the review-fix-verify cycle (user still invokes each step manually)
- Changing the finding ID scheme or priority system
- Retroactively marking old verify reviews (e.g., the existing
  `*-verify-review.md` files were created manually with `light` depth)
