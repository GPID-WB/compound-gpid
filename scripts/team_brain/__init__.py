"""team_brain — Cross-project knowledge sharing for Compound GPID.

This package implements the Team Brain (Phase 1) of the Knowledge Brain
milestone. It provides schema validation, privacy filtering, and local
configuration loading.

.. note::

    Phase 1 status: only ``schema.py``, ``config.py``, and ``privacy.py``
    are implemented. The modules below (``distiller``, ``push``, ``pull``,
    ``dedup``, ``curate``) are planned for Phase 2 and will raise
    ``ImportError`` until implemented.

Architecture::

    team_brain/
    ├── schema.py      # TEAM-BRAIN.yml + JSONL entry validation  ✅ Phase 1
    ├── config.py      # Read team-brain config from compound-gpid.local.md  ✅ Phase 1
    ├── privacy.py     # 3-layer privacy filter (regex → frontmatter → LLM)  ✅ Phase 1
    ├── distiller.py   # Distill one-liner patterns from solution entries  ⬜ Phase 2
    ├── push.py        # Push entries + patterns via GitHub Contents API  ⬜ Phase 2
    ├── pull.py        # Pull relevant entries during Consult Brain step  ⬜ Phase 2
    ├── dedup.py       # Contradiction detection (Jaccard text similarity)  ⬜ Phase 2
    └── curate.py      # CLI for GH Actions curation bot (opens issues)  ⬜ Phase 2

Requirements: Python 3.8+, stdlib only. GitHub CLI (``gh``) for API calls.

Usage::

    from team_brain.config import load_team_brain_config
    from team_brain.privacy import run_privacy_filter

    config = load_team_brain_config(project_root)
    if config and config.enabled:
        result = run_privacy_filter(content, frontmatter, config)
        if not result.blocked:
            push_to_team_brain(entry_path, pattern, config)
"""
from __future__ import annotations

__version__ = "0.1.0"
