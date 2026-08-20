---
date: 2026-08-17
title: "Tar-slip, TOCTOU, and DoS fixes in quarantined import pipeline"
category: "security"
language: "Python"
tags: [security, tar-slip, toctou, dos, quarantine, vendoring, subprocess]
root-cause: "Three security vulnerabilities in the quarantined external-skill importer: tar path traversal, race condition on quarantine directory creation, and memory exhaustion via unchecked file reads."
severity: "P0"
---

# Tar-slip, TOCTOU, and DoS Fixes in Quarantined Import Pipeline

## Problem

The `/cg-import-skill` importer had three security vulnerabilities discovered during code review:

1. **Tar path traversal (tar-slip)**: `tarfile.extractall()` was called without validating member paths. A crafted `git archive` response could write files outside the quarantine directory via `../` path components.

2. **TOCTOU race on quarantine directory**: `quarantine_dir.mkdir(parents=True, exist_ok=True)` after `shutil.rmtree()` creates a time-of-check-to-time-of-use window where an attacker can inject a symlink/junction pointing to `.github/skills/`.

3. **Memory exhaustion DoS**: Files were fully read into memory (`item.read_text()`) before bundle size limits were checked. A single crafted 1GB `.txt` file would exhaust memory before rejection.

## Root Cause

1. **Tar-slip**: Trusted `git archive` output without member validation. The SHA pins the server-side request but the client did not verify returned tar member paths.

2. **TOCTOU**: `exist_ok=True` on `mkdir` means it succeeds silently if a junction/symlink already exists at the target path.

3. **DoS**: Content scanning happened before size validation. The pipeline accumulated `total_bytes` but only checked limits at the end.

## Solution

### Tar-slip fix
Validate every tar member before extraction:
```python
with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:") as tar:
    dest_real = os.path.realpath(str(dest))
    safe_members = []
    for member in tar.getmembers():
        member_dest = os.path.realpath(os.path.join(str(dest), member.name))
        if not member_dest.startswith(dest_real + os.sep) and member_dest != dest_real:
            return False, f"Tar path traversal detected: {member.name}", []
        if member.issym() or member.islnk():
            return False, f"Symlink/hardlink in archive: {member.name}", []
        safe_members.append(member)
    tar.extractall(path=str(dest), members=safe_members)
```

### TOCTOU fix
Use `exist_ok=False` and handle `FileExistsError`:
```python
try:
    quarantine_dir.mkdir(parents=True, exist_ok=False)
except FileExistsError:
    return False, f"Possible symlink/junction injection: {quarantine_dir}"
```
Also wrap `shutil.rmtree` in try/except for Windows file-locking:
```python
try:
    shutil.rmtree(str(quarantine_dir))
except OSError as exc:
    return False, f"Cannot clean quarantine: {exc}"
```

### DoS fix
Check per-file size BEFORE reading content:
```python
max_single_limit = policy.get("maxFileSizeBytes", 262144)
if file_size > max_single_limit:
    errors.append(f"File too large ({file_size} > {max_single_limit}): {rel}")
    continue  # Skip content read
```

### Additional hardening
- Added `GIT_TERMINAL_PROMPT=0` and `GIT_CONFIG_NOSYSTEM=1` to all git subprocess calls
- Added `--config credential.helper=` to git clone to prevent credential prompts
- Pre-compile regex patterns once instead of per-line compilation

## Prevention

1. **Never extract untrusted archives without member validation** — always check paths resolve within the destination directory.
2. **Never use `exist_ok=True` after cleanup** — use `exist_ok=False` and handle the error to prevent TOCTOU races.
3. **Always check resource limits before consuming resources** — validate file sizes before reading, check counts before processing.
4. **Always suppress interactive prompts in subprocess calls** — set `GIT_TERMINAL_PROMPT=0` for any git operation that should never block on input.

## Related

- CWE-22: Path Traversal (tar-slip)
- CWE-367: TOCTOU Race Condition
- CWE-400: Uncontrolled Resource Consumption (DoS)
- Python docs: "Never extract archives from untrusted sources without prior inspection"
