---
date: 2026-05-13
title: "PR verification strategy for cross-platform CLI tool"
status: decided
scope: "Focused"
chosen-approach: "Hybrid: Enhanced CI with E2E smoke tests + parity checks + CONTRIBUTING.md"
tags: [ci, testing, pr-review, cross-platform, macos, windows, cg-link, contributing]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# PR Verification Strategy for Cross-Platform CLI Tool

## Context

Received the first external PR (#37 by zander-prinsloo) fixing a macOS `cg-link` bug.
The existing CI (Pester on windows-2022 + macos-14, link-check) passed on prior commits,
but `cg-link` still failed on a real macOS machine because:
- `Join-Path` with hardcoded backslash (`"prompts\cg-setup.prompt.md"`) works on Windows
  CI but fails on macOS.
- The macOS CI matrix runs `link.sh` (bash), not `link.ps1` via `pwsh`, so the path
  bug was never exercised on macOS in CI.

Need a verification strategy that catches this class of bug automatically.

## Requirements

Seven verification dimensions for PR review:

1. **End-to-end smoke test**: Does `cg-link` succeed on a fresh project dir (not just unit tests)?
2. **Cross-script parity**: When link.ps1 changes, does link.sh get the equivalent change?
3. **Documentation freshness**: Are docs/ updated when CLI behavior changes?
4. **Backward compatibility**: Does the change handle existing installs on upgrade?
5. **Idempotency**: Can `cg-link` be run twice without errors or duplication?
6. **Commit hygiene**: Conventional commits, rebased on current main.
7. **Security surface**: Path handling reviewed for symlink attacks or traversal.

## Approaches Considered

### Approach 1: PR Review Checklist (human + existing CI)

A `.github/PULL_REQUEST_TEMPLATE.md` with seven dimensions as checkboxes. Reviewer
verifies manually.

- Pros: Zero overhead, immediate, forces explicit thought.
- Cons: Human-dependent, no enforcement, doesn't catch "passes CI, fails on real machine."
- Effort: Small.

### Approach 2: Enhanced CI with E2E smoke tests + automated parity checks

- E2E smoke job: create temp project, run cg-link, verify file accessible, run again
  (idempotency), run cg-unlink, verify clean. On both platforms.
- Parity check: assert link.ps1 and link.sh reference same managed dirs, same
  verification file, same gitignore entries.
- Commit lint: conventional-commits check via GitHub Action.
- Docs staleness: non-blocking warning if scripts/ newer than docs/.

- Pros: Catches exact bug class. Automatic on every PR. Prevents script drift.
- Cons: More CI maintenance. E2E tests ~30s per platform.
- Effort: Medium (1-2 days).

### Approach 3: Full pipeline (CI + /cg-review + contributor guide)

Everything from Approach 2 plus:
- /cg-review integration for PRs (maintainer runs it).
- CONTRIBUTING.md for contributors.
- Branch protection rules.

- Pros: Most thorough. Guides unfamiliar contributors.
- Cons: Heavier process. /cg-review only practical for maintainer.
- Effort: Medium-large (2-3 days).

## Decision

Hybrid: Approach 2 core + CONTRIBUTING.md from Approach 3.

Specifically:
1. **E2E smoke test CI job** — fresh project dir, cg-link, verify, idempotency, cg-unlink (both platforms)
2. **Cross-script parity test** — automated Pester test asserting link.ps1 and link.sh stay in sync
3. **Conventional commits lint** — lightweight GitHub Action
4. **Docs staleness warning** — non-blocking CI check
5. **CONTRIBUTING.md** — how to run tests locally, what CI checks, when to update docs, self-review guidance
6. **PR template** — seven-dimension checklist as a lightweight human layer

## Next Steps

1. Write `CONTRIBUTING.md` covering local test setup (macOS + Windows), CI explanation, docs expectations.
2. Add E2E smoke test job to `.github/workflows/tests.yml` (or new workflow).
3. Add parity check test to `tests/bash-scripts.Tests.ps1` or new file.
4. Add conventional-commits lint workflow (e.g., `amannn/action-semantic-pull-request`).
5. Add docs-staleness check (compare timestamps of `scripts/` vs `docs/`).
6. Create `.github/PULL_REQUEST_TEMPLATE.md` with the seven-dimension checklist.
