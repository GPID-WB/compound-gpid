"""Injected measurements test arithmetic, not live handoff performance."""

import json
import math
import sys

import pytest
from test_timing import benchmark_module as benchmark_module


def measurements() -> dict:
    """Build ten sequential synthetic starts including confirmation time."""
    return {
        "schema_version": 1,
        "repository_id": 123,
        "environment": {"python": "3.11", "platform": "fixture", "history_size": 0},
        "warm_dependencies": True,
        "sequential": True,
        "samples": [
            {
                "total_seconds": float(n + 100),
                "confirmation_seconds": 100.0,
                "outcome": "receipt",
                "error_code": None,
            }
            for n in range(1, 11)
        ],
        "intervals": dict.fromkeys(
            ["queue", "review", "approval", "build", "publication", "recovery"]
        ),
    }


def test_ten_sample_summary_excludes_only_confirmation(benchmark_module) -> None:
    result = benchmark_module.summarize_measurements(measurements(), repository_id=123)
    assert result["min_seconds"] == 1
    assert result["median_seconds"] == 5.5
    assert result["p95_seconds"] == 10
    assert result["sample_count"] == 10
    assert result["within_target_from_supplied_data"] is True
    assert result["evidence_status"] == "unverified-input-summary"
    assert result["live_handoff_passed"] is False
    assert result["legacy_baseline"] is None and result["speedup"] is None
    assert result["intervals"]["approval"] is None


@pytest.mark.parametrize("outcome", ["failed", "blocked", "unknown"])
def test_outage_is_retained_and_cannot_pass_target(benchmark_module, outcome) -> None:
    data = measurements()
    data["samples"][-1].update(
        total_seconds=300.0, outcome=outcome, error_code="E_DEADLINE"
    )
    result = benchmark_module.summarize_measurements(data, repository_id=123)
    assert result["sample_count"] == 10 and result["failure_count"] == 1
    assert result["p95_seconds"] == 200
    assert result["failures"] == [
        {"sample": 10, "outcome": outcome, "error_code": "E_DEADLINE"}
    ]
    assert result["within_target_from_supplied_data"] is False


@pytest.mark.parametrize(
    "change", [{"warm_dependencies": False}, {"sequential": False}]
)
def test_wrong_workload_does_not_establish_target(benchmark_module, change) -> None:
    result = benchmark_module.summarize_measurements(
        measurements() | change, repository_id=123
    )
    assert result["within_target_from_supplied_data"] is False


def test_fewer_than_ten_samples_is_not_a_target_pass(benchmark_module) -> None:
    data = measurements()
    data["samples"].pop()
    assert not benchmark_module.summarize_measurements(data, repository_id=123)[
        "within_target_from_supplied_data"
    ]


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "12"])
def test_invalid_duration_rejected(benchmark_module, value) -> None:
    data = measurements()
    data["samples"][0]["total_seconds"] = value
    with pytest.raises(ValueError):
        benchmark_module.summarize_measurements(data, repository_id=123)


def test_confirmation_cannot_exceed_total_or_identity_drift(benchmark_module) -> None:
    data = measurements()
    data["samples"][0]["confirmation_seconds"] = 102.0
    with pytest.raises(ValueError):
        benchmark_module.summarize_measurements(data, repository_id=123)
    with pytest.raises(ValueError):
        benchmark_module.summarize_measurements(measurements(), repository_id=456)


@pytest.mark.parametrize(
    "durations,expected",
    [
        ([1e308] * 10, 1e308),
        ([sys.float_info.max] * 10, sys.float_info.max),
        ([1e308, 1.6e308], 1.3e308),
        ([1e308] * 9, 1e308),
        ([math.ulp(0.0)] * 2, math.ulp(0.0)),
    ],
)
def test_finite_extreme_medians_remain_json_safe(
    benchmark_module, durations, expected
) -> None:
    data = measurements()
    data["samples"] = [
        {
            "total_seconds": seconds,
            "confirmation_seconds": 0.0,
            "outcome": "receipt",
            "error_code": None,
        }
        for seconds in durations
    ]
    result = benchmark_module.summarize_measurements(data, repository_id=123)
    assert math.isfinite(result["median_seconds"])
    assert result["median_seconds"] == pytest.approx(expected, abs=0)
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert result["live_handoff_passed"] is False
