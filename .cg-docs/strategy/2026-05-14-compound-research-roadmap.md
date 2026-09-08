---
date: 2026-05-14
title: "Compound Research roadmap structuring"
trigger: "mid-project"
outcome: "roadmap-updated"
---

# Strategy Session: Compound Research Roadmap Structuring

## Context at Session Start

The compound-research brainstorm (2026-05-13) produced a comprehensive Deep-scope design for extending compound-gpid with a research module for economics and econometrics research. The brainstorm selected Approach 3 (Plugin Module System — same repo, lazy-loaded modules) and outlined 8 implementation phases covering: module system foundation, research workflow scaffolding, core research agents, structural econometrics skills, ML in economics, writing & publication output, reproducibility & replication, and integration polish.

The existing roadmap had 9 milestones (33 done, 33 unstarted features). Three milestones were in-progress: Skills Enhancement, Onboarding & Setup, and Workflow Maturity.

## Discussion Summary

Key decision: whether to structure the 8 phases as separate milestones or as features under a single mega-milestone. Decision: single "Compound Research" milestone with 8 phase-features, because this is a large new addition rather than incremental enhancements to the existing framework.

No changes to existing milestones — compound-research is purely additive.

## Proposed Changes

1. Add new milestone `compound-research` with objective and 8 features (one per phase), all status `idea`.
2. Update charter Current Focus from Workflow Maturity to Compound Research.
3. Archive old Current Focus to charter-history.md.

## Decision

All 3 changes approved and applied.

## Charter Updates

- **Current Focus** updated to: "Compound Research — building a modular research extension for economics and econometrics, starting with the module system foundation (Phase 1) and research workflow scaffolding (Phase 2). Engineering milestones (Workflow Maturity, Skills Enhancement) continue in parallel."
- **last-reviewed** updated to 2026-05-14.
- Old Current Focus archived to `.cg-docs/archive/charter-history.md`.
