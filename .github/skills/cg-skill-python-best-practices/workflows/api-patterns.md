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

---

## 4. Router Organization

```python
# src/gpid_api/routers/poverty.py
from fastapi import APIRouter, Depends, HTTPException, status
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

    try:
        result = poverty_calc.compute_fgt(
            country=request.country,
            year=request.year,
            poverty_line=request.poverty_line,
            ppp_data=ppp_data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return PovertyResponse(data=result, request_id="...")


@router.get("/countries", summary="List available countries")
async def list_countries() -> list[str]:
    return poverty_calc.available_countries()
```

---

## 5. Dependency Injection

```python
# src/gpid_api/dependencies.py
from fastapi import Depends, HTTPException, Security, status
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
from fastapi import APIRouter

router = APIRouter()


# WRONG — blocks the event loop for the duration of the request
@router.get("/data")
def get_data_sync():
    import time
    time.sleep(1)           # blocks all other requests during this sleep
    return {"data": "..."}


# RIGHT — async endpoint, non-blocking
@router.get("/data")
async def get_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.external.org/data")
    return response.json()


# Concurrent external calls — fetch multiple things in parallel
@router.get("/combined")
async def get_combined(country: str, year: int):
    async with httpx.AsyncClient() as client:
        poverty_task   = client.get(f"/poverty?country={country}&year={year}")
        inequality_task = client.get(f"/inequality?country={country}&year={year}")

        poverty_resp, inequality_resp = await asyncio.gather(
            poverty_task, inequality_task
        )

    return {
        "poverty":    poverty_resp.json(),
        "inequality": inequality_resp.json(),
    }


# CPU-bound work — offload to thread pool to avoid blocking event loop
import asyncio
from fastapi.concurrency import run_in_threadpool


@router.post("/compute-heavy")
async def compute_heavy(request: HeavyRequest):
    # run_in_threadpool runs blocking code in a thread without blocking the loop
    result = await run_in_threadpool(heavy_cpu_computation, request.data)
    return {"result": result}
```

---

## 8. Error Handling

Define a custom exception hierarchy. Never raise bare `HTTPException` from
service layer code — that couples business logic to HTTP.

```python
# src/gpid_api/exceptions.py
class GPIDError(Exception):
    """Base exception for all GPID API errors."""

class CountryNotFoundError(GPIDError):
    """Raised when a country code is not in the reference data."""

class YearOutOfRangeError(GPIDError):
    """Raised when requested year has no survey data."""

class InsufficientDataError(GPIDError):
    """Raised when sample size is too small for reliable estimates."""
```

```python
# Register exception handlers in main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from gpid_api.exceptions import CountryNotFoundError, YearOutOfRangeError

@app.exception_handler(CountryNotFoundError)
async def country_not_found_handler(request: Request, exc: CountryNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(YearOutOfRangeError)
async def year_out_of_range_handler(request: Request, exc: YearOutOfRangeError):
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
