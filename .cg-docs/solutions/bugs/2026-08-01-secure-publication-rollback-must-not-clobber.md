---
date: 2026-08-01
title: "Secure publication and rollback must not clobber concurrent filesystem changes"
category: "bugs"
language: "Python"
tags: [filesystem, security, toctou, rollback, windows, posix, hardlink, umask, atomic-publication]
root-cause: "Pinned parent handles were combined with replacing publication, replacing rollback, and pathname cleanup, so a concurrent creator could still be overwritten after validation"
severity: "P0"
---

# Secure Publication and Rollback Must Not Clobber Concurrent Filesystem Changes

## Problem

The shared artifact and generated-target writer already pinned parent directories,
but several operations could still destroy bytes created by another process:

- Windows publication used a replacing handle rename after the final test hook.
  A target created in that boundary window was silently overwritten.
- POSIX stale-file rollback used a replacing rename from quarantine to the
  original name. A concurrent creator at the original name lost its file.
- New POSIX files were forced to `0644` or `0755`, overriding a caller's more
  restrictive umask.
- Generated-target cleanup pruned empty parents by pathname after secure file
  deletion, reopening an unpinned mutation surface.
- Brain and context-audit scanners checked pathnames before `read_text()`, so a
  final-component swap or hard-link alias could expose generated view content.

These were P0/P1 boundary failures: the happy path was correct, but collision
and recovery behavior could overwrite user data or admit excluded model context.

## Root Cause

Pinning a parent directory is necessary but not sufficient. The final syscall's
collision semantics still decide who wins a race. Both publication and rollback
used replacement semantics, treating recovery as if it were exempt from
concurrency. It is not: rollback is another mutation and must never overwrite a
name that became occupied after quarantine.

Mode handling and cleanup had the same conceptual error. A post-creation
`fchmod()` erased the process umask, while optional pathname pruning performed a
second mutation outside the pinned file boundary. Scanner reads similarly
validated one path identity and then reopened the pathname later.

## Solution

### Publish Without Replacing a Concurrent Winner

On Windows, open the existing destination, quarantine that exact handle under a
random recovery name, then publish the private temporary handle with
`replace=False`:

```python
_windows_rename_handle(existing_handle, parent_handle, previous_name, replace=False)
_windows_rename_handle(temporary_handle, parent_handle, name, replace=False)
```

If another process creates `name` before publication, the publish fails. Keep
the concurrent file at `name`, keep the previous valid file under its recovery
name, remove only the unpublished temporary file, and report the collision.

### Restore Quarantine Without Replacement

On POSIX, restore a changed quarantine with a non-replacing hard link through
the pinned parent descriptor, then unlink the quarantine only after the link
succeeds:

```python
try:
    os.link(
        quarantine,
        name,
        src_dir_fd=parent_fd,
        dst_dir_fd=parent_fd,
        follow_symlinks=False,
    )
except FileExistsError as error:
    raise SecureMutationError(
        "Original name is occupied; quarantine preserved."
    ) from error
os.unlink(quarantine, dir_fd=parent_fd)
```

An `EEXIST` result is not a cleanup failure to hide. It proves a concurrent
winner exists, so preserve both identities and fail loudly with the quarantine
path for recovery.

### Preserve Umask and Avoid Optional Pathname Mutation

Create new regular and executable files with base modes `0666` and `0777` so the
kernel applies the process umask. Call `fchmod()` only when replacing an existing
file whose established mode must be preserved. Leave empty generated directories
in place rather than pruning them by pathname.

### Pin Model-Context Reads

Route Brain and context-audit reads through `secure_read_bytes()`. Open the final
component once with no-follow semantics, inspect the opened handle, and reject
multiple-link files for model-context ingestion:

```python
source_bytes = secure_read_bytes(
    root,
    relative_path,
    reject_hardlinks=True,
)
```

This closes the check-to-read swap and prevents a hard-link alias from bypassing
the `.cg-docs/views/` body exclusion.

### Verify the Collision, Not Just the Error

Boundary tests must create the competing file after quarantine or immediately
before publication, then assert every byte owner:

- the concurrent file remains at the original name;
- the previous valid or changed file remains under quarantine/recovery;
- the unpublished temporary output is absent;
- restrictive umasks produce `0600`/`0700` new files;
- hard-link aliases and final-component symlink swaps never enter model context.

The completed fix passed 919 Python tests (3 Windows-only skips), 2,292
unfiltered Pester tests, documentation validation, compilation, diagnostics,
and diff hygiene. Windows runtime collision tests remain required on Windows CI.

## Prevention

- Specify collision semantics for every publish, quarantine, restore, and delete
  syscall. "Atomic" does not imply "non-clobbering."
- Treat rollback as a concurrent mutation. Never restore with `replace=True` or
  `os.replace()` when another actor may have recreated the original name.
- Preserve recovery artifacts when restoration cannot prove exclusive ownership.
- Let the kernel apply umask to new files; preserve explicit modes only for
  replacements.
- Do not add optional pathname cleanup after a secure handle-relative mutation.
- Read security-sensitive input once through the pinned handle that was checked.
- Place race injection after quarantine or at the final publish boundary, and
  assert the bytes of every competing identity.

## Related

- `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md` — foundational handle-relative mutation and real-boundary test pattern
- `.cg-docs/solutions/bugs/2026-05-07-python-nonatomic-path-write-use-mkstemp-replace.md` — crash-safe atomic write foundation; replacement alone does not resolve concurrent ownership
- `.cg-docs/solutions/bugs/2026-05-20-python-path-startswith-bypass-use-relative-to.md` — component-aware path containment before handle pinning
- `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review-5.md` — findings and triage ledger that exposed the boundary regressions
- `.cg-docs/solutions/bugs/2026-08-03-generic-publisher-secure-deletion-and-cross-platform-gates.md` — follow-up commit-point, canonical-identity, and supported-backend CI gate pattern