---
date: 2026-05-20
title: "Team Brain (Phase 2) — Batch D design"
status: decided
scope: "Deep"
chosen-approach: "Hybrid — Direct Push + Async Curation"
tags: [team-brain, knowledge-sharing, cross-project, privacy, dedup, github-actions]
---

# Team Brain (Phase 2) — Batch D Design

## Context

Batch D of the Knowledge Brain milestone (per `.cg-docs/strategy/2026-05-19-knowledge-brain.md`). Builds on the completed local brain engine (Batch A), triggers (Batch B), and read path (Batch C) to enable cross-project knowledge sharing within a team. Five features: repo schema, push, pull, dedup, and privacy filter.

## Requirements

### Scope & Scale
- Primary audience: GPID team's own projects (~10-15 in two weeks, ~30 within a month)
- Configurable: any team adopting compound-gpid can point to their own team brain repo
- Team boundary: GitHub Organization by default, configurable to GitHub Teams
- Each team brain instance has a designated **manager** (defined in `TEAM-BRAIN.yml`)

### Central Repo Structure (Hybrid Namespaced)
- `entries/<project>/` — raw solutions (stripped of private details), full narrative preserved
- `patterns/<project>.jsonl` — distilled one-liner patterns for fast retrieval
- `TEAM-BRAIN.yml` — config (manager, contributors, curation schedule)
- `TEAM-BRAIN.md` — merged index rebuilt by CI after each push (consumable in one context window)
- Zero merge conflicts: each project only touches its own namespace

### Push Model (on `/cg-compound`)
- Direct push to central repo (no PR gate — trusts team members)
- Privacy filter runs **locally before push** (blocking — nothing sensitive leaves the machine)
- Push script logs what was pushed and surfaces confirmation:
  > "Pushed 1 entry + 1 pattern to GPID-WB/team-brain. Privacy filter: 3 regex replacements, 0 LLM flags."
- Retry-with-rebase for rare concurrent pushes (different namespaces = no file conflicts)

### Privacy Filter (3-Layer Pipeline)
1. **Regex layer** (deterministic, fast) — strips absolute paths, drive letters, internal URLs, email addresses, credential patterns
2. **Frontmatter flag** (`private: false` default) — author can mark sections `private: true` to exclude entirely
3. **LLM layer** (additive, complementary) — scans for contextual sensitivity regex missed: project-identifying jargon, internal system names, domain-specific secrets, overly specific examples that should be generalized. Does NOT re-check what regex already handles.

### Pull Model (during Step 0 Consult Brain)
- Problem-context matching: match current problem's context to stored solutions' problem contexts (not just tag matching)
- Patterns index for fast scan; drill into full entries when context is close
- Topic/tag pre-filtering from the merged `TEAM-BRAIN.md` index

### Contradiction Model
- **Contextual variants** (not contradictions): same type of problem, different context → both valid, pull step matches by context similarity
- **True contradictions**: same problem, same context, different solutions → supersession (recency + confidence wins)
- **Curation bot** (GitHub Actions): periodic scanner detects contradictions, opens issues, manager reviews and resolves

### Configuration (`TEAM-BRAIN.yml`)
```yaml
manager: "wb384996"
contributors:
  - org: "GPID-WB"
curation:
  schedule: "weekly"
  auto-supersede: false       # manager must approve
```

### Explicit Exclusions
- **Cross-org federation** — deferred to Phase 3
- **Conflict resolution UI** — not planned (text-based surfacing is sufficient)
- **Offline/cached mode** — not needed (agents require internet)

## Approaches Considered

### Approach 1: Git-Native Push (Direct Commit)
Each project pushes directly via `gh`/`git` — clone, add to namespace, commit, push.
- **Pros**: Full git history, works with existing `gh` CLI, branch protection possible
- **Cons**: Requires clone/pull before push (latency), concurrent push retries, noisy git history
- **Effort**: Medium

### Approach 2: PR-Based Push (Fork + Pull Request)
Each project opens a PR; GH Actions auto-merges if privacy checks pass.
- **Pros**: Built-in review gate, privacy filter as CI check, audit trail as PRs
- **Cons**: High latency, fork management overhead, manager becomes bottleneck at scale
- **Effort**: Large

### Approach 3: Hybrid — Direct Push + Async Curation ✓
Direct push to namespace (zero friction), GH Actions curation bot for async dedup, privacy filter runs locally before push (blocking).
- **Pros**: Zero-friction push, privacy enforcement is local/blocking, curation is async/batched, scales to 30+ namespaces
- **Cons**: No pre-merge review (relies on local privacy filter), manager must check curation issues
- **Mitigations**: Push script logs and confirms what was pushed; if privacy filter has gaps, the LLM layer catches novel sensitivity; curation bot opens issues for manager visibility
- **Effort**: Medium

## Decision

**Approach 3: Hybrid — Direct Push + Async Curation** — chosen for best balance of contributor velocity and safety at 30-project scale. The 3-layer privacy filter (regex → frontmatter → LLM) running locally before push ensures sensitive content never reaches the remote. Curation happens asynchronously via GitHub Actions without blocking contributors. Push confirmation logging addresses the "fail loudly" charter constraint.

## Next Steps

1. **`team-brain-repo-schema`** — Design the full repo layout, `TEAM-BRAIN.yml` schema, and the `TEAM-BRAIN.md` output format. Define the entry/pattern file schemas.
2. **`team-brain-privacy-filter`** — Implement the 3-layer pipeline (regex → frontmatter → LLM). This must be ready before push can work.
3. **`team-brain-push`** — Wire into `/cg-compound`: after local capture, run privacy filter, push entry + distilled pattern to central repo, log confirmation.
4. **`team-brain-pull`** — During Consult Brain step: fetch `TEAM-BRAIN.md` (or local cache), match current problem context to stored solutions, surface relevant entries.
5. **`team-brain-dedup`** — Build contradiction detection logic + GH Actions workflow (weekly cron, opens issues for manager).

Sub-batching recommendation from strategy: (1) alone first, then (2+3) together, then (4+5) together.
