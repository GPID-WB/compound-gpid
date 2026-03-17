# API Patterns

Conventions for building REST APIs with FastAPI and pydantic. The GPID technical
team uses FastAPI for all HTTP services — data access APIs, model serving, and
internal tooling.

---

## 1. Project Structure for APIs

```
gpid-api/
├── src/
│   └── gpid_api/
│       ├── __init__.py
│       ├── main.py            # App factory, lifespan, middleware
│       ├── config.py          # Settings via pydantic-settings
│       ├── dependencies.py    # Shared FastAPI dependencies
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── poverty.py     # /poverty endpoints
│       │   ├── inequality.py  # /inequality endpoints
│       │   └── health.py      # /health endpoint
│       ├── models/
│       │   ├── __init__.py
│       │   ├── requests.py    # Pydantic request models
│       │   └── responses.py   # Pydantic response models
│       └── services/
│           ├── __init__.py
│           └── poverty_calc.py  # Business logic, no FastAPI imports
├── tests/
│   ├── conftest.py
│   ├── test_poverty.py
│   └── test_inequality.py
├── pyproject.toml
└── README.md
```

**Key rule:** `services/` must never import from `fastapi`. Business logic is
tested independently of the HTTP layer.

---

## 2. Application Factory with Lifespan

```python
# src/gpid_api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from gpid_api.config import settings
from gpid_api.routers import poverty, inequality, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting GPID API", version=settings.version)
    # Load reference data, warm caches, open DB connections
    app.state.ppp_factors = load_ppp_reference()
    yield
    # Cleanup on shutdown
    logger.info("Shutting down GPID API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="GPID Data API",
        version=settings.version,
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(poverty.router, prefix="/poverty", tags=["poverty"])
    app.include_router(inequality.router, prefix="/inequality", tags=["inequality"])
    return app


app = create_app()
```

---

## 3. Pydantic Models — Request and Response

Never use raw dicts as request/response bodies. Every endpoint gets typed models.

```python
# src/gpid_api/models/requests.py
from pydantic import BaseModel, Field, field_validator
from typing import Annotated


class PovertyRequest(BaseModel):
    country: Annotated[str, Field(min_length=3, max_length=3, pattern="^[A-Z]{3}$")]
    year: Annotated[int, Field(ge=1990, le=2030)]
    poverty_line: Annotated[float, Field(gt=0, le=100, default=2.15)]
    welfare_type: str = "consumption"

    @field_validator("welfare_type")
    @classmethod
    def validate_welfare_type(cls, v: str) -> str:
        allowed = {"consumption", "income"}
        if v not in allowed:
            raise ValueError(f"welfare_type must be one of {allowed}")
        return v

    model_config = {"json_schema_extra": {"example": {
        "country": "ETH",
        "year": 2022,
        "poverty_line": 2.15,
        "welfare_type": "consumption",
    }}}
```

```python
# src/gpid_api/models/responses.py
from pydantic import BaseModel
from typing import Optional


class PovertyEstimate(BaseModel):
    country: str
    year: int
    poverty_line: float
    headcount_ratio: float
    poverty_gap: float
    severity: float
    n_observations: int
    currency: str = "2017 PPP USD"
    notes: Optional[str] = None


class PovertyResponse(BaseModel):
    status: str = "ok"
    data: PovertyEstimate
    request_id: str
```

For cross-field validation (e.g., `start_year <= end_year`), use `@model_validator`:

```python
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Self


class YearRangeRequest(BaseModel):
    start_year: Annotated[int, Field(ge=1990, le=2030)]
    end_year:   Annotated[int, Field(ge=1990, le=2030)]
    country:    Annotated[str, Field(min_length=3, max_length=3)]

    @model_validator(mode="after")
    def check_year_range(self) -> Self:
        if self.start_year > self.end_year:
            raise ValueError(
                f"start_year ({self.start_year}) must be <= end_year ({self.end_year})"
            )
        return self
```

---

## 4. Router Organization

```python
# src/gpid_api/routers/poverty.py
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from loguru import logger

from gpid_api.dependencies import get_ppp_data, require_api_key
from gpid_api.models.requests import PovertyRequest
from gpid_api.models.responses import PovertyResponse
from gpid_api.services import poverty_calc

router = APIRouter()


@router.post(
    "/estimate",
    response_model=PovertyResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute FGT poverty estimates",
)
async def estimate_poverty(
    request: PovertyRequest,
    ppp_data: dict = Depends(get_ppp_data),
    _: None = Depends(require_api_key),   # auth dependency
) -> PovertyResponse:
    """Compute headcount ratio, poverty gap, and severity for a country-year."""
    logger.info("Poverty estimate request", country=request.country, year=request.year)

    # Let domain exceptions propagate to app-level exception handlers (see §8)
    result = poverty_calc.compute_fgt(
        country=request.country,
        year=request.year,
        poverty_line=request.poverty_line,
        ppp_data=ppp_data,
    )

    return PovertyResponse(data=result, request_id=str(uuid4()))


@router.get("/countries", summary="List available countries")
async def list_countries() -> list[str]:
    return poverty_calc.available_countries()
```

---

## 5. Dependency Injection

```python
# src/gpid_api/dependencies.py
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from gpid_api.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(api_key_header)) -> None:
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )


async def get_ppp_data(request: Request) -> dict:
    """Load PPP reference data from app state (loaded at startup)."""
    return request.app.state.ppp_factors
```

---

## 6. Configuration with pydantic-settings

```python
# src/gpid_api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    version: str = "0.1.0"
    api_key: str                    # required — no default, must be in env
    data_path: str = "data/"
    log_level: str = "INFO"
    max_page_size: int = 1000


settings = Settings()   # instantiated once at module import
```

```bash
# .env (never committed to git)
API_KEY=your-secret-key-here
DATA_PATH=/mnt/gpid/data
LOG_LEVEL=DEBUG
```

---

## 7. Async Patterns

Use `async def` for endpoints. Use `asyncio` for concurrent I/O. Do not block
the event loop with CPU-bound or synchronous I/O operations.

```python
import asyncio
import httpx
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI, Request
from loguru import logger


# Create the shared HTTP client once in lifespan — never once per request
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.http_client.aclose()


router = APIRouter()


# WRONG — blocks the event loop for the duration of the request
@router.get("/data")
def get_data_sync():
    import time
    time.sleep(1)           # blocks all other requests during this sleep
    return {"data": "..."}


# RIGHT — async endpoint, non-blocking; reuses shared client from app.state
@router.get("/data")
async def get_data(request: Request):
    client: httpx.AsyncClient = request.app.state.http_client
    response = await client.get("https://api.external.org/data")
    return response.json()


# Concurrent external calls — fetch multiple things in parallel
@router.get("/combined")
async def get_combined(country: str, year: int, request: Request):
    client: httpx.AsyncClient = request.app.state.http_client
    base = "https://internal-api.gpid.org"

    poverty_resp, inequality_resp = await asyncio.gather(
        client.get(f"{base}/poverty?country={country}&year={year}"),
        client.get(f"{base}/inequality?country={country}&year={year}"),
    )

    return {
        "poverty":    poverty_resp.json(),
        "inequality": inequality_resp.json(),
    }


# Blocking I/O in a sync function — offload to thread pool
from fastapi.concurrency import run_in_threadpool


@router.get("/read")
async def read_file():
    # run_in_threadpool is for blocking I/O only (file reads, sync DB calls)
    # It releases the event loop during the wait — but does NOT bypass the GIL
    from pathlib import Path
    data = await run_in_threadpool(Path("large_file.csv").read_text)
    return {"lines": data.count("\n")}


# CPU-bound work — use ProcessPoolExecutor (bypasses GIL via separate processes)
# run_in_threadpool is WRONG for CPU-bound work: threads still share the GIL
import asyncio
from concurrent.futures import ProcessPoolExecutor

_process_pool = ProcessPoolExecutor()   # create once at module level, reuse


@router.post("/compute-heavy")
async def compute_heavy(request: HeavyRequest):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_process_pool, heavy_cpu_computation, request.data)
    return {"result": result}
    # NOTE: for sustained heavy workloads, prefer a task queue (Celery, RQ)
    # over in-process ProcessPoolExecutor — better crash isolation and scalability
```

---

## 8. Error Handling

Define a custom exception hierarchy in `exceptions.py`. Never raise bare
`HTTPException` from service layer code — that couples business logic to HTTP.

The canonical hierarchy is defined in `AppError` — see
[Logging and Errors](logging-and-errors.md#2-custom-exceptions) for the full
exception class definitions. Register HTTP mappings in `main.py`:

```python
# Register exception handlers in main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from your_package.exceptions import DataNotFoundError, DataQualityError, InsufficientSampleError

@app.exception_handler(DataNotFoundError)
async def data_not_found_handler(request: Request, exc: DataNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(DataQualityError)
async def data_quality_handler(request: Request, exc: DataQualityError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(InsufficientSampleError)
async def insufficient_sample_handler(request: Request, exc: InsufficientSampleError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

---

## 9. Testing FastAPI Endpoints

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from gpid_api.main import create_app

@pytest.fixture(scope="session")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-key"}
```

```python
# tests/test_poverty.py
from fastapi import status


def test_poverty_estimate_returns_200(client, auth_headers):
    response = client.post(
        "/poverty/estimate",
        json={"country": "ETH", "year": 2022, "poverty_line": 2.15},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert 0 <= data["headcount_ratio"] <= 1


def test_unknown_country_returns_404(client, auth_headers):
    response = client.post(
        "/poverty/estimate",
        json={"country": "ZZZ", "year": 2022},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_missing_api_key_returns_403(client):
    response = client.post(
        "/poverty/estimate",
        json={"country": "ETH", "year": 2022},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_year_rejected(client, auth_headers):
    response = client.post(
        "/poverty/estimate",
        json={"country": "ETH", "year": 1800},   # before valid range
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
```
