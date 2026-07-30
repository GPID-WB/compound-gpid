---
date: 2026-07-30
title: "Adaptive project workflow capability"
trigger: "mid-project"
outcome: "roadmap-updated"
---

# Strategy Session: Adaptive Project Workflow Capability

## Context at Session Start

Compound GPID had 12 roadmap milestones and 117 features. Its current focus
remained the Token Efficiency Core System. Recent work had already established
progressive context disclosure, compact active-state handoffs, project scanning,
and cross-platform packaging.

The session evaluated whether ideas from the Interpretable Context Methodology
(ICM) and its workspace-builder should inform project setup and workflow design.
The evaluation used the ICM repository, its conventions, workspace-builder, and
the associated March 2026 paper.

## Discussion Summary

ICM is a strong fit for sequential, repeatable, human-reviewed production
processes such as data-to-report and research-to-publication workflows. Compound
GPID already follows several related principles internally, including filesystem
artifacts, staged work, quality gates, canonical context, and selective loading.

The useful addition is a project-facing capability that infers and builds
production workflows from repository evidence and guided conversation. It must
not restructure Compound GPID, impose fixed product templates, replace executable
pipelines, or copy the ICM repository. Setup should assess suitability and offer
a consent-based handoff to a dedicated builder. Users should also be able to
invoke the builder later to create, extend, or revise workflows. A lightweight
runner should support stage entry, status, and resume behavior.

## Proposed Changes

- Add an Adaptive Workflow Foundation milestone covering suitability criteria,
  scanner evidence, a Compound-native workflow contract, guided workflow
  building, stage scaffolding, lifecycle modes, and deterministic validation.
- Add a Workflow Setup and Operation milestone covering setup assessment and
  handoff, workflow execution guidance, status and resume, context budgets,
  representative pilots, and an evaluation gate.
- Keep all existing milestones and Compound GPID's own workflow unchanged.
- Treat executable systems such as targets, CI, build tools, and data pipelines
  as authoritative; generated workflow contracts guide human-agent production
  work around them.

## Decision

The proposal was approved. `roadmap.json` now contains two new planned
milestones with 14 idea-stage features:

- `adaptive-workflow-foundation`
- `workflow-setup-operation`

The roadmap now contains 14 milestones and 131 features. The charter was not
changed; Current Focus remains the Token Efficiency Core System.
