---
date: 2026-03-17
title: "httpx.AsyncClient requires ASGITransport for FastAPI async tests"
category: "testing-patterns"
language: "Python"
tags: [httpx, fastapi, pytest, async, asgi, testing, deprecated]
root-cause: "httpx deprecated the `app=` shorthand parameter in 0.23+; the correct pattern requires wrapping with httpx.ASGITransport"
severity: "P1"
---

# httpx.AsyncClient requires ASGITransport for FastAPI async tests

## Problem

FastAPI async endpoint tests using `httpx.AsyncClient(app=app, ...)` fail or emit
deprecation warnings on httpx ≥ 0.23. The `app=` shorthand was removed.

```python
# BROKEN on httpx >= 0.23
@pytest.fixture
async def async_client():
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## Root Cause

httpx 0.23 removed the `app=` convenience parameter that previously accepted an
ASGI application directly. The correct way to use an ASGI app as the transport
has always been `httpx.ASGITransport`, but the shorthand masked this. Projects
with `httpx>=0.27` (as specified in the GPID API pyproject.toml) will always
fail with the old pattern.

## Solution

Use `httpx.ASGITransport` explicitly:

```python
import httpx
import pytest
from your_api.main import create_app


@pytest.fixture
async def async_client():
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


async def test_endpoint_returns_200(async_client):
    response = await async_client.post(
        "/poverty/estimate",
        json={"country": "ETH", "year": 2022},
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 200
```

Also requires `asyncio_mode = "auto"` in `pyproject.toml` and `pytest-asyncio>=0.23`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[project.optional-dependencies]
dev = [
    "pytest-asyncio>=0.23",
    ...
]
```

## Prevention

- Always use `httpx.AsyncClient(transport=httpx.ASGITransport(app=app), ...)`.
- Never use the deprecated `app=app` shorthand.
- Pin `httpx>=0.23` in dev dependencies to guarantee the correct API is required.
- The `cg-skill-python-best-practices` skill (`workflows/testing-pytest.md`) has
  been updated with the correct pattern as of 2026-03-17.

## Related

- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- `cg-skill-python-best-practices/workflows/testing-pytest.md` — canonical async testing pattern
