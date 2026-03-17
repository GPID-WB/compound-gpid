---
date: 2026-03-17
title: "run_in_threadpool does not bypass the GIL for CPU-bound work — use ProcessPoolExecutor"
category: "bugs"
language: "Python"
tags: [fastapi, async, gil, threading, multiprocessing, performance, cpu-bound, io-bound]
root-cause: "run_in_threadpool runs in a thread pool; Python's GIL is NOT released for pure CPU computation, so threads serialise rather than parallelise"
severity: "P1"
---

# run_in_threadpool does not bypass the GIL for CPU-bound work

## Problem

A FastAPI endpoint offloads heavy computation to a thread pool using
`run_in_threadpool`, expecting real parallel execution. Under concurrent load,
all requests still serialise — performance is no better than running on the
event loop directly, and the comment "offload to thread pool to avoid blocking
the event loop" is misleading.

```python
# WRONG — threads compete for the GIL; no real CPU parallelism
@router.post("/compute-heavy")
async def compute_heavy(request: HeavyRequest):
    result = await run_in_threadpool(heavy_cpu_computation, request.data)
    return {"result": result}
```

## Root Cause

Python's Global Interpreter Lock (GIL) prevents more than one thread from
executing Python bytecode at the same time. `run_in_threadpool` (and
`asyncio.run_in_executor` with the default `ThreadPoolExecutor`) run the
function in a thread — but pure Python CPU work still holds the GIL for each
~100-bytecode timeslice. Concurrent requests that trigger this code all compete
for the same lock.

**The GIL IS released for:**
- File I/O, network I/O (`socket` calls)
- C-extension work that releases it explicitly (numpy array ops, polars, etc.)
- `time.sleep()`

**The GIL is NOT released for:**
- Pure Python loops, arithmetic, string processing
- Any Python-level computation

`run_in_threadpool` is the correct tool **only for blocking I/O** (sync file
reads, synchronous database drivers, etc.) — where the GIL is released during
the actual wait.

## Solution

For CPU-bound work, use `ProcessPoolExecutor` — each process has its own GIL:

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from fastapi import APIRouter

router = APIRouter()

# Create the pool once at module level — don't create per-request
_process_pool = ProcessPoolExecutor()


@router.post("/compute-heavy")
async def compute_heavy(request: HeavyRequest):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _process_pool, heavy_cpu_computation, request.data
    )
    return {"result": result}
    # NOTE: for sustained heavy workloads, prefer a task queue (Celery, RQ)
    # over in-process ProcessPoolExecutor — better crash isolation and scalability
```

For blocking I/O (the correct use case for `run_in_threadpool`):

```python
from fastapi.concurrency import run_in_threadpool
from pathlib import Path


@router.get("/read")
async def read_file():
    # Correct: releases event loop during I/O wait; GIL IS released for I/O
    data = await run_in_threadpool(Path("large_file.csv").read_text)
    return {"lines": data.count("\n")}
```

## Prevention

| Work type | Tool | Why |
|-----------|------|-----|
| Blocking I/O (file, sync DB) | `run_in_threadpool` | GIL released during I/O; threads fine |
| CPU-bound Python code | `ProcessPoolExecutor` via `run_in_executor` | Separate process, no GIL contention |
| Heavy sustained CPU | Task queue (Celery, RQ) | Better isolation, scaling, retries |
| numpy/polars computations | Neither needed | C-extensions release GIL; run on event loop |

The `cg-skill-python-best-practices` skill (`references/python-anti-patterns.md`
and `workflows/api-patterns.md`) has been updated with split IO-bound vs
CPU-bound anti-pattern entries as of 2026-03-17.

## Related

- `cg-skill-python-best-practices/references/python-anti-patterns.md` — async anti-patterns table
- `cg-skill-python-best-practices/workflows/api-patterns.md` §7 — async patterns
- Python docs: [GIL](https://docs.python.org/3/glossary.html#term-global-interpreter-lock)
