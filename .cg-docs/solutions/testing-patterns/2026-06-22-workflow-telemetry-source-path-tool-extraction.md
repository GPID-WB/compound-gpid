---
date: 2026-06-22
title: "Workflow telemetry needs source-aware path and tool extraction"
category: "testing-patterns"
language: "Python/Markdown"
tags: [token-efficiency, workflow-telemetry, context-audit, static-analysis, prompt-parsing, regression-tests]
root-cause: "Workflow telemetry reused legacy narrow reference regexes that were designed for older context-risk counts, so deterministically visible prompt paths and workflow tool names were omitted from the Phase 1.1 baseline"
severity: "P2"
plan: ".cg-docs/plans/2026-06-22-workflow-token-baseline.md"
reviewed-in: ".cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review-4.md"
related: [".cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md", ".cg-docs/solutions/testing-patterns/2026-06-16-reviewed-warning-classifications-close-token-work.md"]
---

# Workflow Telemetry Needs Source-Aware Path and Tool Extraction

## Problem

Phase 1.1 added workflow-level token/context telemetry to
`scripts/cg_audit_context.py`, but the first implementation still populated
`file_references`, `likely_file_reads`, and `tool_references` with the legacy
`FILE_REF_RE` and `TOOL_REF_RE` patterns.

That undercounted the actual static prompt surface. For example, `/cg-work`
explicitly loads or reads:

- `.github/shared/context-loading.contract.md`
- `.github/shared/goal-execution.contract.md`
- `.github/shared/review-routing.contract.md`
- `tests/Run-Tests.ps1`

It also references `execution_subagent` for the safe Pester runner workflow.
The generated audit row omitted those shared-contract paths and reported no
workflow tool references, even though all of that evidence was present in the
prompt source.

## Root Cause

The old reference regexes served a narrower purpose: counting a small set of
always-on project context files for historical context-risk and reference-matrix
outputs. Reusing them for Phase 1.1 workflow telemetry conflated two different
measurement contracts:

1. legacy compatibility counts for `.cg-docs/cost/` consumers;
2. workflow baseline telemetry that should enumerate deterministic source
   references visible in the prompt text.

Because the same patterns were reused, broad workflow references such as
`.github/shared/*.md`, `.github/skills/**/SKILL.md`, `tests/Run-Tests.ps1`, and
`execution_subagent` were invisible to the new telemetry.

## Solution

Keep the legacy reference matrix stable, but add workflow-specific extraction
for workflow telemetry.

The fix added:

```python
WORKFLOW_TOOL_REF_RE = re.compile(
    r"\b(?:read_file|edit_file|run_in_terminal|grep_search|semantic_search|"
    r"execution_subagent|apply_patch|Task|TodoWrite|TodoRead|AskUserQuestion)\b"
)
```

and a workflow path extractor that normalizes prompt-style references before
counting them:

```python
def _normalize_workflow_path_reference(value: str) -> str:
    path = value.strip().strip("`'\"()[]{}<>,;:")
    while path.endswith("."):
        path = path[:-1]
    path = path.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    if path.startswith(". tests/"):
        path = "tests/" + path[len(". tests/"):]
    return path
```

`build_workflow_telemetry()` now uses `_workflow_path_matches()` and
`WORKFLOW_TOOL_REF_RE` for workflow rows, while preserving the existing
reference matrix for backward compatibility.

The regression test uses prompt-like fixture text rather than only generic
paths:

```python
def test_workflow_telemetry_extracts_shared_paths_and_execution_subagent(self, tmp_path: Path) -> None:
    _write(
        tmp_path / ".github/prompts/cg-work.prompt.md",
        _frontmatter(None)
        + "Load `.github/shared/context-loading.contract.md` before Step 1.\n"
        + "Load `.github/shared/goal-execution.contract.md` for the contract.\n"
        + "Read `.github/shared/review-routing.contract.md` for review routing.\n"
        + "Use execution_subagent to run `. tests\\Run-Tests.ps1` safely.\n",
    )
    report = audit.build_report(tmp_path)
    row = next(item for item in report["workflow_telemetry"]["workflows"] if item["workflow"] == "/cg-work")
    assert ".github/shared/context-loading.contract.md" in row["file_references"]
    assert ".github/shared/goal-execution.contract.md" in row["file_references"]
    assert ".github/shared/review-routing.contract.md" in row["file_references"]
    assert "tests/Run-Tests.ps1" in row["file_references"]
    assert "execution_subagent" in row["tool_references"]
```

Final verification evidence:

```text
python3 -m pytest scripts/tests/test_audit_context.py::TestPhase6Benchmark::test_workflow_telemetry_extracts_shared_paths_and_execution_subagent -q
# 1 passed

python3 -m pytest scripts/tests/test_audit_context.py -q
# 88 passed

python3 -m py_compile scripts/cg_audit_context.py
# passed

python3 scripts/cg_audit_context.py --root . --output-dir /tmp/cg-verify-p2-1-full-addressed --format json
# /cg-work missing_files=[]
# /cg-work missing_tools=[]
# guardrail_failures=0

. ./tests/Run-Tests.ps1
# tests/last-run.json: 2194 passed, 0 failed, filteredFiles=null
```

## Prevention

When adding audit metrics for prompt or workflow behavior:

1. Do not assume the legacy reference matrix covers the new metric. Check the
   purpose of the existing regex or parser before reusing it.
2. Keep compatibility fields stable when existing `.cg-docs/cost/` consumers
   depend on them. Add a purpose-built extractor for new telemetry surfaces.
3. Test with realistic prompt idioms: backticked paths, Windows slashes,
   shared contracts, local skills, and known tool names.
4. Verify the generated JSON row for the affected workflow, not only the unit
   test. The artifact is the contract consumed by `/cg-token-audit` and future
   benchmark comparisons.
5. Treat token-saving or token-pressure claims as hypotheses until a fresh
   audit run measures them in this repository.

## Related

- `.cg-docs/plans/2026-06-22-workflow-token-baseline.md` - Phase 1.1 implementation plan.
- `.cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review-4.md` - verification finding P2.1 that exposed the undercount.
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md` - benchmark guardrails for token optimization.
- `.cg-docs/solutions/testing-patterns/2026-06-16-reviewed-warning-classifications-close-token-work.md` - warning classification and generated-evidence pattern for token work.
