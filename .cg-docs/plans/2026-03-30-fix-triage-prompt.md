---
date: 2026-03-30
title: "Add /cg-fix-triage and integrate review-to-fix pipeline"
status: active
brainstorm: ".cg-docs/brainstorms/2026-03-30-fix-triage-prompt.md"
language: "both"
estimated-effort: "small"
tags: [workflow, review, prompts, docs, tests]
---

# Plan: Add `/cg-fix-triage` and Integrate Review-to-Fix Pipeline

## Objective

Create the `/cg-fix-triage` prompt that reads a saved review report from
`.cg-docs/reviews/` and applies fixes selectively by priority level or
individual finding ID. Update all cross-references, docs, and tests to
complete the review-to-fix pipeline.

## Context

The brainstorm (`.cg-docs/brainstorms/2026-03-30-fix-triage-prompt.md`)
decided on compound finding IDs (`P1.1`, `P2.3`, etc.) and the name
`/cg-fix-triage`. During the brainstorm, initial scaffolding was done:

- `cg-fix-triage.prompt.md` was created
- `cg-review.prompt.md` was updated with compound IDs and `/cg-fix-triage` reference
- `docs/reference.md`, `docs/workflow.md`, `cg-setup.prompt.md`,
  `compound-gpid.md` were updated with mentions

What remains:

1. `/cg-resume` does not scan `.cg-docs/reviews/` — it should detect
   pending review reports and suggest `/cg-fix-triage`.
2. Pester tests in `tests/prompt-tools.Tests.ps1` need coverage for the
   new prompt file.
3. `/cg-review` Step 5 Summary should also mention `/cg-fix-triage`
   as a follow-up option for skipped findings.

## Implementation Steps

### 1. Update `/cg-resume` to detect pending review reports

- **Files**: `.github/prompts/cg-resume.prompt.md` (MODIFY)
- **Details**:
  - Add a Step 2e "Pending review findings" after 2d that scans
    `.cg-docs/reviews/` for `.md` files with unresolved P1/P2/P3 findings.
  - In Step 3, add a "📋 Pending Review Findings" section showing the
    review filename and count of findings by priority.
  - In Step 4, add `/cg-fix-triage` as a suggested next action when
    pending review reports exist.
- **Tests**: Manual — invoke `/cg-resume` with a review file present.
- **Acceptance criteria**:
  - `/cg-resume` mentions `.cg-docs/reviews/` in its scanning step.
  - A pending review report surfaces in the context summary.
  - `/cg-fix-triage` is suggested when unfixed findings exist.

### 2. Update `/cg-review` Step 5 to mention `/cg-fix-triage`

- **Files**: `.github/prompts/cg-review.prompt.md` (MODIFY)
- **Details**:
  - In the Step 5 Summary "Next Steps" block, add a line for skipped
    findings: "If findings were skipped: Run `/cg-fix-triage` in a
    future session to apply them."
- **Tests**: Grep for `cg-fix-triage` in the Step 5 section.
- **Acceptance criteria**: The review summary mentions `/cg-fix-triage`
  as a next step when findings were skipped.

### 3. Add Pester tests for `cg-fix-triage.prompt.md`

- **Files**: `tests/prompt-tools.Tests.ps1` (MODIFY)
- **Details**:
  - Add a Describe block for `cg-fix-triage.prompt.md` that verifies:
    - The file exists.
    - It references `.cg-docs/reviews/`.
    - It references compound finding IDs (pattern `P[123]\.\d`).
  - Add a Describe block verifying `cg-review.prompt.md` uses compound
    IDs (pattern `\[P[123]\.\d\]`) in its report template.
- **Tests**: `Invoke-Pester tests/prompt-tools.Tests.ps1`
- **Acceptance criteria**: All new tests pass.

### 4. Verify consistency across all references

- **Files**: all modified files
- **Details**:
  - Grep workspace for any remaining `"/cg-fix"` (without `-triage` or
    `-bug` suffix) references and fix them.
  - Confirm the workflow diagram in `docs/workflow.md` includes
    Fix Triage in the loop.
- **Tests**: `grep -r "cg-fix[^-]" --include="*.md"` returns no false
  positives (only `/cg-fixbug` matches are acceptable).
- **Acceptance criteria**: No stale `/cg-fix` references remain.

## Testing Strategy

- Pester tests for prompt file structure (file existence, content patterns).
- Manual smoke test: invoke `/cg-review` on a small change, verify the
  report uses compound IDs, then invoke `/cg-fix-triage` to confirm it
  loads the report correctly.

## Documentation Checklist

- [x] `docs/reference.md` — `/cg-fix-triage` row added
- [x] `docs/workflow.md` — Step 5b section added
- [ ] `cg-resume.prompt.md` — scanning and suggestion logic
- [x] `cg-setup.prompt.md` — command list updated

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Review reports are empty (no findings) | `/cg-fix-triage` handles this gracefully: "All findings resolved." |
| Finding IDs change if review is re-run | IDs are scoped to a specific review file; re-running creates a new file |
| Resume prompt gets too long | Keep the review scan minimal — just count findings, don't parse details |

## Out of Scope

- Automated test that _invokes_ `/cg-fix-triage` end-to-end (prompt files
  are interactive; testing is structural only).
- Status tracking inside the review file (marking findings as "fixed" in
  the `.md` itself) — deferred to a future iteration.
- A `triage/` subfolder inside `.cg-docs/` — review reports stay in
  `.cg-docs/reviews/` with the `-review` suffix as already established.
