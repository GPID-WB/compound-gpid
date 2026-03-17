# Testing with pytest

## Project Setup

```
project/
├── src/
│   └── project_name/
│       ├── __init__.py
│       └── module.py
├── tests/
│   ├── conftest.py           # Shared fixtures
│   ├── test_module.py
│   └── fixtures/
│       └── sample_data.csv   # Small test data
└── pyproject.toml
```

In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

## Test Structure

```python
def test_function_does_expected_thing():
    """Test that function produces expected output for normal input."""
    # Arrange
    input_df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

    # Act
    result = my_function(input_df)

    # Assert
    assert result.shape == (3, 3)
    assert result["computed"].to_list() == [100, 200, 300]
```

## Fixtures

```python
import pytest
import polars as pl


@pytest.fixture
def sample_data():
    """Create minimal sample data for testing."""
    return pl.DataFrame({
        "id": [1, 2, 3],
        "income": [1000.0, 2000.0, 3000.0],
        "region": ["SSA", "EAP", "SSA"],
    })


@pytest.fixture
def empty_data():
    """Create empty DataFrame with expected schema."""
    return pl.DataFrame(
        schema={"id": pl.Int64, "income": pl.Float64, "region": pl.String}
    )


def test_aggregation(sample_data):
    result = aggregate_by_region(sample_data)
    assert result.filter(pl.col("region") == "SSA")["mean_income"][0] == 2000.0
```

## Parametrize

```python
@pytest.mark.parametrize("input_val, expected", [
    (0, "low"),
    (50000, "medium"),
    (100000, "high"),
    (-1, "invalid"),
])
def test_categorize_income(input_val, expected):
    result = categorize_income(input_val)
    assert result == expected
```

## Testing Exceptions

```python
def test_invalid_input_raises():
    with pytest.raises(ValueError, match="must be a DataFrame"):
        my_function("not a dataframe")


def test_missing_column_raises():
    df = pl.DataFrame({"wrong_col": [1, 2, 3]})
    with pytest.raises(KeyError):
        my_function(df)
```

## Temporary Files

```python
def test_write_output(tmp_path):
    output_file = tmp_path / "output.csv"

    write_results(data, output_file)

    assert output_file.exists()
    result = pl.read_csv(output_file)
    assert result.shape[0] == expected_rows
```

## Testing polars DataFrames

```python
from polars.testing import assert_frame_equal


def test_transformation():
    input_df = pl.DataFrame({"x": [1, 2, 3]})
    expected = pl.DataFrame({"x": [1, 2, 3], "x_squared": [1, 4, 9]})

    result = add_squared_column(input_df)

    assert_frame_equal(result, expected)
```

## Testing FastAPI Endpoints

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from your_api.main import create_app

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
# test_routes.py
from fastapi import status

def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

def test_endpoint_requires_auth(client):
    response = client.post("/poverty/estimate", json={...})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_valid_request_returns_expected_shape(client, auth_headers):
    response = client.post(
        "/poverty/estimate",
        json={"country": "ETH", "year": 2022},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "data" in body
    assert 0 <= body["data"]["headcount_ratio"] <= 1
```

## Edge Cases to Always Test

```python
def test_empty_dataframe(empty_data):
    result = my_function(empty_data)
    assert result.shape[0] == 0

def test_single_row():
    df = pl.DataFrame({"id": [1], "value": [42.0]})
    result = my_function(df)
    assert result.shape[0] == 1

def test_null_values():
    df = pl.DataFrame({"id": [1, 2], "value": [1.0, None]})
    result = my_function(df)
    assert result["value"].null_count() == 0

def test_duplicate_keys():
    df = pl.DataFrame({"id": [1, 1, 2], "value": [10, 20, 30]})
    result = my_function(df)
    assert result.shape[0] == 2  # deduplicated
```

## Running Tests

```bash
pytest                        # Run all tests
pytest tests/test_module.py   # Run specific file
pytest -k "test_aggregation"  # Run by name pattern
pytest -v --tb=long           # Verbose with full tracebacks
pytest --cov=src --cov-report=html   # With coverage report
uv run pytest                 # Via uv
```

---

## Suppressing loguru in Tests

Prevent loguru from emitting output during test runs. Add once to `conftest.py`:

```python
# conftest.py
import pytest
from loguru import logger

@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress loguru output during tests."""
    logger.remove()
    yield
```

---

## Async Endpoint Testing

For async FastAPI endpoints, configure `pytest-asyncio` and use
`httpx.AsyncClient` with `httpx.ASGITransport` for a proper async test transport.

> **Requirement**: `pytest-asyncio>=0.23` must be installed as a dev dependency
> (see [Project Setup](project-setup.md)) and `asyncio_mode = "auto"` set in `pyproject.toml`.

In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"   # required for async tests
```

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


async def test_async_endpoint(async_client):
    response = await async_client.post(
        "/poverty/estimate",
        json={"country": "ETH", "year": 2022},
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 200
```

---

## Mocking Dependencies

### Mocking external HTTP calls with `httpx.MockTransport`

```python
import httpx


def mock_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"ETH": 1.23})


def test_compute_with_mock_ppp():
    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=transport)
    result = poverty_calc.compute_fgt(country="ETH", ppp_client=client)
    assert result["headcount_ratio"] >= 0
```

### Patching functions with `pytest-mock`

```python
def test_service_calls_db_once(mocker):
    mock_load = mocker.patch("myapp.services.load_from_database")
    mock_load.return_value = pl.DataFrame({"welfare": [1.0, 3.0], "weight": [1.0, 1.0]})

    result = compute_poverty_rate_for_country("ETH", 2022)

    mock_load.assert_called_once_with("ETH", 2022)
    assert 0 <= result <= 1
```
