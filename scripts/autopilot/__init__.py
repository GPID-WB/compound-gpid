"""Deterministic evidence and control-state modules for the Kilo-first autopilot.

Phase 2 implements the closed protocol records, strict invocation and plan
validation, bounded evidence acquisition and the owned marker/checkpoint
control transactions. Phase 3 adds the parent transition loop in
``pipeline.py``. Phase 4 adds publication/PR observation in ``queries.py`` and
deadline-aware CI classification in ``ci.py``. Phase 5 adds the installed
helper identity in ``install.py`` and the measurable parent context budgets
in ``context.py``.
"""

__all__ = (
    "contracts", "arguments", "plan", "evidence", "state", "recovery", "pipeline",
    "queries", "ci", "install", "context",
)
