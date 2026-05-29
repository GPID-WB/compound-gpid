"""team_brain — Cross-project knowledge sharing for Compound GPID.

This package implements the full Team Brain (Knowledge Brain milestone):
schema validation, privacy filtering, local configuration loading, pattern
distillation, GitHub push, remote pull, contradiction detection, curation
bot, and team brain initialisation.

Architecture::

    team_brain/
    ├── schema.py      # TEAM-BRAIN.yml + JSONL entry validation  ✅ Phase 1
    ├── config.py      # Read team-brain config from compound-gpid.local.md  ✅ Phase 1
    ├── privacy.py     # 3-layer privacy filter (regex → frontmatter → LLM)  ✅ Phase 1
    ├── distiller.py   # Distill one-liner patterns from solution entries  ✅ Phase 2
    ├── push.py        # Push entries + patterns via GitHub Contents API  ✅ Phase 1+2
    ├── pull.py        # Pull relevant entries during Consult Brain step  ✅ Phase 2
    ├── dedup.py       # Contradiction detection (Jaccard text similarity)  ✅ Phase 3
    ├── curate.py      # CLI for GH Actions curation bot (opens issues)  ✅ Phase 3
    └── init.py        # One-time team brain repo initialisation  ✅ Phase 3

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
