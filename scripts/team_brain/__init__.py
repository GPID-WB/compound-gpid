"""team_brain — Cross-project knowledge sharing for Compound GPID.

This package implements Phases 1 and 2 of the Team Brain (Knowledge Brain
milestone). It provides schema validation, privacy filtering, local
configuration loading, pattern distillation, GitHub push, and remote pull.

.. note::

    Phase 1 (schema, config, privacy) and Phase 2 (distiller, push, pull)
    are complete. Phase 3 modules (``dedup``, ``curate``) are planned and
    will raise ``ImportError`` until implemented.

Architecture::

    team_brain/
    ├── schema.py      # TEAM-BRAIN.yml + JSONL entry validation  ✅ Phase 1
    ├── config.py      # Read team-brain config from compound-gpid.local.md  ✅ Phase 1
    ├── privacy.py     # 3-layer privacy filter (regex → frontmatter → LLM)  ✅ Phase 1
    ├── distiller.py   # Distill one-liner patterns from solution entries  ✅ Phase 2
    ├── push.py        # Push entries + patterns via GitHub Contents API  ✅ Phase 1+2
    ├── pull.py        # Pull relevant entries during Consult Brain step  ✅ Phase 2
    ├── dedup.py       # Contradiction detection (Jaccard text similarity)  ⬜ Phase 3
    └── curate.py      # CLI for GH Actions curation bot (opens issues)  ⬜ Phase 3

Requirements: Python 3.8+, stdlib only. GitHub CLI (``gh``) for API calls.

Usage::

    from team_brain.config import load_team_brain_local_config
    from team_brain.privacy import run_privacy_filter
    from team_brain.push import push_entry

    config = load_team_brain_local_config(project_root)
    if config and config.enabled:
        result = run_privacy_filter(content, frontmatter, config)
        if not result.blocked:
            push_entry(entry_path, config)
"""
from __future__ import annotations

__version__ = "0.1.0"
