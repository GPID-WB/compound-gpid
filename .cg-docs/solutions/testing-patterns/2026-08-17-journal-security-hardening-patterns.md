---
date: 2026-08-17
title: "Journal security hardening patterns for atomic file publication"
category: "testing-patterns"
language: "Python"
tags: [journal, security, path-traversal, transaction-id, containment, validation, atomic-replace]
root-cause: "Journal transactionId and generation directory were not validated against format/containment constraints, enabling path-traversal attacks"
severity: "P0"
---

# Journal Security Hardening Patterns for Atomic File Publication

## Problem

The journaled projection synchronizer writes a `projection-journal.json` with a `transactionId` (32-hex) and records generation directories for crash recovery. Without validation:

1. A forged `transactionId` containing path separators could escape the `.compound-gpid/generations/` directory.
2. A generation directory symlink could point outside the project root.
3. Planned-destination roots in journal records could contain `..` traversal.

## Root Cause

The journal was designed for crash recovery, not adversarial input. No format validation on `transactionId`, no containment check on generation directory resolution, and no prefix validation on planned-destination roots.

## Solution

Four independent validation layers, each fail-closed:

### 1. Transaction ID format validation
```python
_HEX32 = re.compile(r"^[0-9a-f]{32}$")

def _validate_transaction_id(tx_id: str) -> None:
    if not _HEX32.match(tx_id):
        raise ProjectionError(f"Invalid transaction ID format: {tx_id!r}")
```

### 2. Generation directory containment
```python
def _validate_generation_dir(gen_dir: Path, project_root: Path) -> None:
    resolved = gen_dir.resolve()
    compound_pid = (project_root / ".compound-gpid").resolve()
    resolved.relative_to(compound_pid)  # raises ValueError if outside
```

### 3. Journal record root validation
```python
def _validate_record_root(root: str) -> None:
    if not root or "/" in root or "\\" in root or root == ".":
        raise ProjectionError(f"Invalid journal record root: {root!r}")
```

### 4. Planned-destination prefix validation
```python
def _validate_planned_destination(dest: Path, project_root: Path) -> None:
    resolved = dest.resolve()
    resolved.relative_to(project_root)  # raises ValueError if outside
    # Additional prefix check for declared managed roots
```

### 5. Recovery completion re-validates all plannedHashes
After reading the journal for recovery, every planned destination is re-validated with `_validate_repo_relative_path` + root-prefix check before any file operation.

## Prevention

- Every new journal field that could contain user-influenced data must have a validation function called before use.
- Journal tests must include: invalid hex txId, path-separator txId, symlinked generation dir, `..` in planned destination, forged ownership entries outside managed roots.
- The `_declared_managed_roots` function reads `target-mapping.json` `projectRoots.managed` to bound unlink operations to declared roots only.
- Use `pytest.raises(ProjectionError, match="...")` with specific match patterns to verify fail-closed behavior.

## Related

- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md` — foundational secure publication and rollback patterns (handle pinning, atomic rename, concurrent-creator protection)
- `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase3-review.md` (P0.1, P1.1, P2.1, P2.6)
- `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase3-verify-review.md` (P2.6)
- `scripts/cg_project_projection.py` — `_validate_transaction_id`, `_validate_generation_dir`, `_declared_managed_roots`
- `scripts/tests/test_project_projection.py` — `TestJournalSecurity`, `TestManifestFreshness` classes
