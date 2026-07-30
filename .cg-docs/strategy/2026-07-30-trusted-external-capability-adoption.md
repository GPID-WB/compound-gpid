---
date: 2026-07-30
title: "Trusted External Capability Adoption"
trigger: "post-milestone"
outcome: "roadmap-updated"
---

# Strategy Session: Trusted External Capability Adoption

## Context at Session Start

Compound GPID had completed the Canonical-to-Native Packaging Foundation on
2026-07-28. The completion was merged to `main` through releases `v1.0.2` and
`v1.0.3`, with all seven plan phases, verification rows V1-V8, and constraints
C1-C8 recorded as passed. This removed the packaging blocker that had prevented
safe external-skill intake.

At the start of the session, the roadmap contained 12 milestones and 114
features: 54 done, none active, and 60 unstarted. The relevant existing work
included skill-description ideas, the completed project scanner and World Bank
report-writing skill, the completed project wiki, and standalone ideas for
attribution, source packs, and writing guardrails.

The strategy was prompted by an assessment of `github/awesome-copilot`. The
assessment found that Compound GPID already had stronger R, Stata, analytical,
reproducibility, and institutional guidance. The useful upstream opportunities
were therefore governance and infrastructure patterns rather than wholesale
catalog adoption.

The working tree was synchronized with `origin/main` at release `v1.0.3`
before roadmap changes were proposed.

## Discussion Summary

The session organized the remaining Awesome Copilot recommendations after the
completed packaging foundation. The user requested durable, implementation-ready
roadmap descriptions rather than short placeholders.

The adopted sequence is:

1. Establish external asset provenance and controlled intake.
2. Validate intake through a GitHub Actions hardening external-skill pilot.
3. Improve skill discovery metadata and trigger quality.
4. Improve project-scanner evidence, unknowns, and intent-versus-reality gaps.
5. Define shared sensitive-data and output-hygiene safeguards.
6. Extend report source provenance and verification.
7. Reassess optional capability expansion only after evidence from the committed
   phases exists.

The strategy deliberately reuses existing milestones and feature IDs where
possible. No new milestone was created. Existing completed features remain
historical records and were not reopened.

Two additional usability ideas were approved during the session:

- `/cg-wiki` should be able to build and safely publish a navigable project
  website through GitHub Pages while preserving Markdown and `_wiki.yml` as
  canonical sources.
- `/cg-commit-push-pr` should automatically continue into PR verification. It
  should poll every 20-30 seconds for up to five minutes rather than sleeping
  for a fixed interval. `/cg-verify-pr` should also support any accessible PR,
  including manually created and fork PRs, with mutation guarded by checkout,
  permissions, and push-safety checks.

## Proposed Changes

### Architecture Research

- Move `attribution-documentation` from Ongoing Ideas and broaden it as
  **External asset provenance and controlled intake**.
- Add **GitHub Actions hardening external-skill pilot**.
- Keep the completed Canonical-to-Native Packaging Foundation unchanged.
- Make controlled intake a prerequisite for the external-skill pilot.

The intake feature records immutable upstream identity, source and imported
hashes, licensing, attribution, reviewer approval, destination mapping,
adaptations, refresh history, and rejection/removal outcomes. It treats external
content as untrusted and makes automated risk scans advisory rather than an
approval oracle.

The pilot adapts Awesome Copilot's `github-actions-hardening` skill under the
Compound GPID namespace, integrates it with existing review agents, applies the
P0-P3 priority system, audits current workflows, and verifies all four supported
platforms. It does not create a marketplace or automatic external installer.

### Skills Enhancement

- Rename `skill-description-consistency-audit` to **Skill discovery metadata
  and trigger-quality audit** and absorb description-length enforcement.
- Remove the duplicate `skill-description-length-cap` feature.
- Move and broaden `shared-writing-guardrails-contract` as **Shared
  sensitive-data and output-hygiene contract**.
- Move and broaden `exemplar-source-pack-schema` as **Reusable report source
  provenance and verification**.
- Keep SkillOpt as a separate later optimization mechanism.
- Keep the completed World Bank report-writing skill unchanged.

The metadata audit covers WHAT/WHEN/user-vocabulary descriptions, positive and
negative discovery probes, adjacent-skill ambiguity, namespace and catalog
validation, and cross-platform metadata parity.

The safeguards contract separates sensitive-data controls from production
output hygiene. It explicitly preserves rationale and provenance in `.cg-docs`
and other controlled records while preventing prompt narration and restricted
content from leaking into public outputs.

The source-verification feature distinguishes source existence, accessibility,
citation correctness, factual support, and human acceptance. It extends the
existing report-writing source-pack system rather than creating an always-active
generic verification agent.

### Onboarding & Setup

- Add **Project scanner evidence, unknowns, and intent-versus-reality gaps**.
- Add **GitHub Pages website publishing for project wikis**.
- Keep the completed scanner and project-wiki features unchanged.

The scanner enhancement adds exact evidence paths, explicit unknown and
unverifiable outcomes, contradiction reporting, stale-declaration detection,
and safeguards against skipping setup questions when declared intent conflicts
with observed repository state. It does not create a second charter or the
upstream seven-document codebase map.

The website feature extends `/cg-wiki` with deterministic site generation,
responsive navigation, accessibility, cross-linking, optional search, local
validation, and safe GitHub Pages publication. Existing workflows and Pages
configuration must never be overwritten silently. GitHub Wiki conversion
remains a separate compatibility mode.

### Workflow Maturity

- Add **Automatic post-PR CI verification and universal PR targeting**.
- Keep the completed PR verification pipeline unchanged.

The new feature joins `/cg-commit-push-pr` and `/cg-verify-pr` through shared
verification behavior. PR creation polls non-blockingly for checks for up to
five minutes and starts verification as soon as checks appear. Timeout leaves a
valid PR and a resumable handoff. Explicit PR number or URL targeting supports
PRs created outside Compound GPID, while automatic fixes require a matching
writable checkout and safe push target.

### Deferred Evaluation

The following remain recorded strategy candidates but do not receive roadmap
features until prior phases demonstrate demand and fit:

- Optional capability bundles or installation profiles.
- Dependabot guidance beyond observations from the Actions pilot.
- Secret scanning and push-protection guidance.
- A redacted analytical-incident postmortem workflow.
- Additional generic source-verification agents.
- PyPI packaging.
- Native marketplace or plugin packaging.
- Additional external package registries or catalogs.

### Explicit Rejections

Compound GPID should not adopt the following Awesome Copilot assets as proposed:

- Generic R instructions that are weaker than Compound GPID's existing R suite.
- Planning and repository-architecture agents that duplicate current workflows.
- Skills that optimize for 100 percent line coverage rather than behavioral
  confidence.
- Session auto-commit or auto-push hooks.
- Generic always-loaded context instructions.
- Regex-only security hooks presented as complete security controls.

## Decision

The roadmap changes were approved and applied. The final roadmap restructuring:

- Reused the Architecture Research, Skills Enhancement, Onboarding & Setup, and
  Workflow Maturity milestones.
- Added four new features.
- Moved and broadened three existing features.
- Renamed one existing feature in place.
- Removed one duplicate feature.
- Created no new milestone.
- Reopened no completed feature.
- Kept marketplace packaging deferred.

After the changes, the roadmap contains 117 features. The approved descriptions
are intentionally comprehensive so each future brainstorm and plan has clear
scope, dependencies, safety boundaries, non-goals, and success conditions.

No charter update was made during this session. The existing Current Focus and
`last-reviewed` value remain unchanged.
