# Snapshot and External-Research Modes

Compound GPID currently runs in `local-workflow` mode by default. It uses local
repository files, generated Brain artifacts, command summaries, and local
validation outputs.

`.github/shared/snapshot-research-modes.json` tracks future snapshot and
external-research candidates. The registry is an evaluation artifact, not runtime configuration. Phase 2.3 does not implement snapshot capture, browser
automation, web search, or external source fetching.

## Current Mode

- `local-workflow`: default and enabled.

## Candidate Modes

- `snapshot-candidate`: local, evaluate-only, default-disabled.
- `external-research-candidate`: external, deferred, default-disabled.

Both candidates require explicit opt-in before any future implementation can
use them.

## Required Gates

Future snapshot or external-research work needs:

- explicit opt-in
- source attribution
- privacy review
- copyright-safe summary
- reproducibility note
- token-budget review
- rollback plan

External research also requires a concrete user request, clear source URLs or
citations, and a summary that does not copy large source passages.

## Non-Goals

This registry does not enable:

- browser automation
- web search execution
- external source fetching
- snapshot capture or replay
- transcript dumps
- runtime mode switching

Keep ordinary workflows local unless a future roadmap item explicitly implements
and validates a mode.
