"""Strict invocation parsing, batch grammar and single-phase expansion.

Fresh form: ``--plan <path> --batches <segments> --base <branch>
[--ci-timeout 30m]``. Resume form: ``--resume <active-state path>``. Forms are
mutually exclusive; unknown and repeated flags are rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from autopilot.contracts import ArgumentError

DEFAULT_CI_TIMEOUT_SECONDS = 1800
MAX_TIMEOUT_SECONDS = 86400
# Absolute per-segment width cap enforced at parse time, before any phase
# expansion materializes a tuple. Plan-level validation additionally bounds
# segment width by the plan's real phase count, so `--batches 1-99999999`
# fails fast in this module instead of allocating near a billion phases.
MAX_SEGMENT_WIDTH = 1000

_SINGLE_RE = re.compile(r"^\d+$")
_RANGE_RE = re.compile(r"^(\d+)-(\d+)$")
_TIMEOUT_RE = re.compile(r"^(\d+)([smh])$")
_UNITS = {"s": 1, "m": 60, "h": 3600}
_BASE_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

_FORM_FLAGS = ("--plan", "--batches", "--base", "--ci-timeout")
_RESUME_FLAGS = ("--resume",)
_KNOWN_FLAGS = frozenset(_FORM_FLAGS + _RESUME_FLAGS)


@dataclass(frozen=True)
class BatchSegment:
    """One inclusive ascending batch segment or singleton phase."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise ArgumentError("invalid segment: bounds must be integers.")
        if self.start < 1 or self.end < self.start:
            raise ArgumentError(
                f"invalid segment '{self.start}-{self.end}': "
                "phases must be positive and ranges ascending."
            )
        if self.end - self.start + 1 > MAX_SEGMENT_WIDTH:
            raise ArgumentError(
                f"invalid segment '{self.start}-{self.end}': a segment may span "
                f"at most {MAX_SEGMENT_WIDTH} phases; split wider batches into "
                "smaller segments."
            )

    def iter_phases(self):
        """Yield each phase number lazily, without tuple materialization."""
        return iter(range(self.start, self.end + 1))

    def phases(self) -> Tuple[int, ...]:
        return tuple(self.iter_phases())

    def display(self) -> str:
        return str(self.start) if self.start == self.end else f"{self.start}-{self.end}"


def parse_batch_segments(text: str) -> Tuple[BatchSegment, ...]:
    """Parse the closed ``--batches`` grammar.

    Accepts decimal positive phase numbers or inclusive ascending ranges
    separated by commas. Trims surrounding segment whitespace; rejects empty
    segments, internal whitespace, leading signs, reversed ranges, duplicates
    and overlaps. Ordered segments must be strictly ascending.
    """
    if not isinstance(text, str) or not text.strip():
        raise ArgumentError("empty batches: provide e.g. '1-3,5'.")
    segments: list[BatchSegment] = []
    for raw_token in text.split(","):
        token = raw_token.strip()
        if not token:
            raise ArgumentError(f"empty segment in batches {text!r}.")
        range_match = _RANGE_RE.fullmatch(token)
        single_match = _SINGLE_RE.fullmatch(token)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
        elif single_match:
            start = end = int(single_match.group(0))
        else:
            raise ArgumentError(
                f"invalid segment {token!r}: use a positive phase number or "
                "an inclusive ascending range like '1-3'."
            )
        segment = BatchSegment(start, end)
        if segments and segment.start <= segments[-1].end:
            raise ArgumentError(
                f"invalid segment {token!r}: segments must be strictly ascending "
                "with no overlap or duplicates."
            )
        segments.append(segment)
    return tuple(segments)


def parse_ci_timeout(text: str) -> int:
    """Parse a positive integer duration with s, m or h into seconds.

    Accepts 1 second through 24 hours. Rejects zero, fractions, overflow,
    unknown suffixes and other units.
    """
    if not isinstance(text, str):
        raise ArgumentError("invalid timeout: expected a duration string.")
    match = _TIMEOUT_RE.fullmatch(text)
    if not match:
        raise ArgumentError(
            f"invalid timeout {text!r}: use a positive integer with 's', 'm' "
            "or 'h', from 1s through 24h."
        )
    amount = int(match.group(1))
    seconds = amount * _UNITS[match.group(2)]
    if not 1 <= seconds <= MAX_TIMEOUT_SECONDS:
        raise ArgumentError(
            f"invalid timeout {text!r}: duration must be between 1 second and 24 hours."
        )
    return seconds


def validate_base_ref(base: str) -> str:
    """Validate a portable branch base reference without touching Git."""
    if not isinstance(base, str) or not base or not _BASE_RE.fullmatch(base):
        raise ArgumentError(
            f"invalid base {base!r}: use a branch-like ref such as 'origin/dev'."
        )
    if base.startswith(("-", "/")) or base.endswith("/") or ".." in base:
        raise ArgumentError(f"invalid base {base!r}: unsafe branch reference.")
    if len(base) > 256:
        raise ArgumentError("invalid base: branch references are at most 256 bytes.")
    return base


@dataclass(frozen=True)
class Invocation:
    """One validated autopilot invocation form."""

    form: str
    plan: Optional[str]
    segments: Tuple[BatchSegment, ...]
    base: Optional[str]
    ci_timeout_seconds: int
    resume_path: Optional[str]


def parse_invocation(argv: Sequence[str]) -> Invocation:
    """Parse exactly one autopilot form from raw argv.

    Raises:
        ArgumentError: On repeated or unknown flags, missing values, mixed or
            absent forms, unexpected positionals and invalid values.
    """
    if not isinstance(argv, (list, tuple)) or any(
        not isinstance(item, str) for item in argv
    ):
        raise ArgumentError("invalid invocation: argv must be a list of strings.")
    seen: dict[str, str] = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in _KNOWN_FLAGS:
            if token in seen:
                raise ArgumentError(f"repeated flag {token}.")
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                raise ArgumentError(f"missing value for flag {token}.")
            seen[token] = argv[index + 1]
            index += 2
            continue
        if token.startswith("-"):
            raise ArgumentError(
                f"unknown flag {token!r}; only the closed fresh/resume forms are accepted."
            )
        raise ArgumentError(f"unexpected positional argument {token!r}.")
    fresh_flags = [flag for flag in _FORM_FLAGS if flag in seen]
    has_resume = "--resume" in seen
    if has_resume:
        if fresh_flags:
            raise ArgumentError(
                "mutually exclusive forms: --resume cannot be combined with fresh-form flags."
            )
        resume_path = seen["--resume"]
        if not resume_path:
            raise ArgumentError("invalid resume path: must be a non-empty path.")
        return Invocation("resume", None, (), None, DEFAULT_CI_TIMEOUT_SECONDS, resume_path)
    if not fresh_flags:
        raise ArgumentError(
            "no autopilot form provided: use the fresh form (--plan --batches --base) "
            "or --resume."
        )
    required = ("--plan", "--batches", "--base")
    if not all(flag in seen for flag in required):
        raise ArgumentError(
            "incomplete fresh form: --plan, --batches and --base are all required."
        )
    segments = parse_batch_segments(seen["--batches"])
    timeout_text = seen.get("--ci-timeout")
    timeout = (
        parse_ci_timeout(timeout_text)
        if timeout_text is not None
        else DEFAULT_CI_TIMEOUT_SECONDS
    )
    base = validate_base_ref(seen["--base"])
    return Invocation("fresh", seen["--plan"], segments, base, timeout, None)


def expand_single_phase_commands(segments: Sequence[BatchSegment]) -> Tuple[str, ...]:
    """Expand validated segments into the exact single-phase work command.

    Every valid segment expands into one command per phase, in plan order:
    ``/cg-work phaseN review:none``. No other command is ever emitted.
    Segments are consumed lazily and only the final command tuple is
    materialized.
    """
    commands: list[str] = []
    for segment in segments:
        for phase in segment.iter_phases():
            commands.append(f"/cg-work phase{phase} review:none")
    return tuple(commands)
