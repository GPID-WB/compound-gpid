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
        schema={"id": pl.Int64, "income": pl.Float64, "region": pl.Utf8}
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

## Edge Cases to Test

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
pytest --cov=src              # With coverage
```
