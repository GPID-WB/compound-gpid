"""Opt-in timing: monotonic local spans and explicitly missing remote intervals."""

import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager

STAGES = {
    "preparation": "Resolve and prepare inputs before gate execution.",
    "gates": "Execute one declared validation gate; repeated spans remain distinct.",
    "subprocess": "One external process; excludes parent work and queue wait.",
    "confirmation": "Human confirmation wait, excluded from submission deadline.",
    "submission": "Persist and verify a durable request receipt, not publication.",
    "queue": "Remote queued interval before execution starts.",
    "review": "Preparation review wait.",
    "build": "Exact-input unprivileged build execution.",
    "approval": "Protected publication approval wait.",
    "publication": "Verified tag, Release, and asset publication.",
    "recovery": "Reconcile an interrupted operation before any retry.",
}
MAX_TIMING_RECORDS = 1000


class TimingRecorder:
    """Collect bounded redaction-safe records without input text or exception bodies."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        """Configure timing, e.g. ``TimingRecorder(enabled=True)``.

        Args:
            enabled: Explicit opt-in; disabled timing never calls clocks.
            clock: Monotonic clock for local elapsed durations.
            wall_clock: Wall timestamps for context, never duration arithmetic.
        """
        self.enabled = enabled
        self.clock = clock
        self.wall_clock = wall_clock
        self.records: list[dict] = []

    def _new_record(self, stage: str) -> dict:
        if stage not in STAGES:
            raise ValueError("Unknown timing stage")
        if len(self.records) >= MAX_TIMING_RECORDS:
            raise ValueError("Timing record limit exceeded")
        record = {
            "schema_version": 1,
            "kind": "timing",
            "stage": stage,
            "sequence": len(self.records) + 1,
            "elapsed_seconds": None,
            "outcome": "running",
        }
        self.records.append(record)
        return record

    @contextmanager
    def span(self, stage: str) -> Iterator[None]:
        """Measure local work, e.g. ``with recorder.span('gates'): validate()``.

        Args:
            stage: One key from STAGES; arbitrary labels cannot carry secrets.
        Yields:
            None. Exceptions and interrupts propagate after recording outcome.
        Raises:
            ValueError: Unknown stage, record limit, or invalid monotonic clock.
        """
        if not self.enabled:
            yield
            return
        record = self._new_record(stage)
        started = self.clock()
        record["wall_started"] = self.wall_clock()
        try:
            yield
        except BaseException:
            record["outcome"] = "interrupted"
            raise
        else:
            record["outcome"] = "complete"
        finally:
            elapsed = self.clock() - started
            record["wall_finished"] = self.wall_clock()
            if not math.isfinite(elapsed) or elapsed < 0:
                record["outcome"] = "invalid-clock"
                raise ValueError("Invalid monotonic clock interval")
            record["elapsed_seconds"] = elapsed

    def remote_interval(
        self, stage: str, *, started: float | None, finished: float | None
    ) -> None:
        """Record an externally observed interval or explicit missing evidence.

        Args:
            stage: Remote timing stage, e.g. ``queue``.
            started: Verified remote start timestamp, or None.
            finished: Verified remote finish timestamp, or None.
        Returns:
            None. Missing timestamps yield null duration, never fabricated zero.
        Raises:
            ValueError: Invalid supplied timestamps or reversed remote interval.
        """
        if not self.enabled:
            return
        for timestamp in (started, finished):
            if timestamp is not None and (
                isinstance(timestamp, bool)
                or not isinstance(timestamp, (int, float))
                or not math.isfinite(timestamp)
            ):
                raise ValueError("Invalid remote timestamp")
        elapsed = None if started is None or finished is None else finished - started
        if elapsed is not None and (not math.isfinite(elapsed) or elapsed < 0):
            raise ValueError("Invalid remote clock interval")
        record = self._new_record(stage)
        record.update(
            elapsed_seconds=elapsed,
            outcome="missing" if elapsed is None else "complete",
        )
