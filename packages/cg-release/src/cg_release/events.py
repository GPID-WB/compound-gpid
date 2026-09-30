"""Redacted diagnostics and line-oriented structured command output."""

import re
import sys

from loguru import logger

from cg_release.models import Event, canonical_bytes

AUTHORIZATION_FIELD = re.compile(r"(?i)\b(?:proxy-)?authorization[ \t]*[:=]")
_SECRET_PATTERNS = (
    r"(?i)\b(?:proxy-)?authorization[ \t]*[:=][^\r\n]*"
    r"(?:\r?\n[ \t]+[^\r\n]*)*",
    r"(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)",
    r"https?://[^\s/@]+:[^\s/@]+@[^\s]+",
    r"(?i)(?:password|token|api[_-]?key|secret)\s*[:=]\s*[^\s,;]+",
    r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----",
)


def redact(text: str) -> str:
    """Remove common credential forms before emitting diagnostics.

    Args:
        text: Diagnostic text, e.g. ``token=example``.
    Returns:
        Text with credential-shaped values replaced by ``[REDACTED]``.
    """
    for pattern in _SECRET_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text


class ControllerError(Exception):
    """Typed failure with a safe message; raw subprocess errors are not retained."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        """Create a redacted failure, e.g. ``ControllerError('E_TIMEOUT', 'Late')``.

        Args:
            code: Stable error code.
            message: Human diagnostic, never a raw credential or response body.
            retryable: Whether the operation may be retried after reconciliation.
        """
        self.code = code
        self.message = redact(message)[:2048]
        self.retryable = retryable
        super().__init__(self.message)


def emit_event(event: Event, *, json_output: bool) -> None:
    """Write one flushed stdout event; diagnostics use stderr, never stdout.

    Args:
        event: Validated event, e.g. ``Event(kind='status')``.
        json_output: Select JSON Lines instead of concise human output.
    Returns:
        None.
    """
    payload = event.model_dump(mode="json")

    def clean(value: object) -> object:
        if isinstance(value, str):
            return redact(value)
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    payload = clean(payload)
    if json_output:
        line = canonical_bytes(payload).decode("utf-8")
    else:
        line = f"{payload['code'] or payload['kind']}: {payload['message']}"
        for field in ("version", "observed", "step", "expected"):
            if payload.get(field) is not None:
                line += f"\n  {field}: {payload[field]}"
        if payload.get("request_id"):
            line += f"\n  request_id: {payload['request_id']}"
        if payload.get("next_action"):
            line += f"\n  next_action: {payload['next_action']}"
        if payload.get("proposal"):
            line += "\n" + "\n".join(
                f"  {key}: {value}" for key, value in payload["proposal"].items()
            )
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def configure_diagnostics() -> None:
    """Install a stderr-only CLI sink without local-variable exception dumps.

    Example:
        Call ``configure_diagnostics()`` once at CLI startup.
    """
    logger.remove()
    logger.add(sys.stderr, format="{level}: {message}", diagnose=False, backtrace=False)
