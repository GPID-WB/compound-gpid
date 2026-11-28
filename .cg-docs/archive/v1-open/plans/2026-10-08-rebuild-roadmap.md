---
artifact-schema-version: 1
date: 2026-10-08
title: "Rebuild Roadmap: Saved Memory"
status: active
scope: "Standard"
deviation-policy: "strict"
---

REBUILD ROADMAP, status 2026-10-08

Done:
- Recovery frozen; complete Git bundle and evidence backup verified at
  E:\PovcalNet\01.personal\wb384996\GPID-team\backups\20261007-9017-assessment\
- Rebuild from v1.2.0.9017 on branch chore/rebuild-from-9017,
  worktree w-9022.
- v1.2.0.9022 published as a pre-release (tag -> 30c9daee). It works on
  Windows through cg-update. It works on Mac through re-clone; Mac installs
  from 9006-9016 must re-clone because their updater has an exact Kilo version
  allowlist.

Next steps, in order:
1. v1.2.0.9023: remove EVERY Kilo version and Kilo host dependency from
   install, update, and link. Kilo checks are advisory, only in the optional
   cg-kilo launcher. Must work on Windows and Mac before continuing.
   Constraint: Compound GPID must never depend on a Kilo version or Kilo host
   behavior.
2. Use 9023 for real work for a few days; run cg-link once per project, one
   project at a time; report blocked or preserved messages.
3. Make the rebuild line official: dev, then main, through normal reviewed
   PRs, preserving history and without force-push. Plan first: supersede
   technique, removed-content table, effect on users who follow "latest",
   required checks, PR191 disposition (close as superseded; keep archive refs),
   outdated saved decisions to review, and entry criteria.
4. Port features back one at a time, each as a small pre-release: 9024, 9025,
   ... Start with simplified cg-help answers, without evidence binding. Do NOT
   bring back autopilot, the native Kilo plugin, the async controller,
   receipts, Pages sealing, or the custom process supervisor without an
   explicit decision.
5. Reintroduce guardrails in phases: secret scanning now if available; broader
   tests after several green pre-releases; CodeQL and linting later; provenance
   only for stable releases.
6. Official v2.0.0 after main uses the rebuild line and pre-releases are stable.
   The research module and skill changes are already included.
7. Later: standard plugin packaging (content-only Agent Plugin pilot) and the
   institutional IT discussion.

Working method:
- One bounded session per step, in w-9022, Code mode. No /cg-work and no Goal.
- Run the CI-matched preflight before every push. Run the full Pester gate with
  a short root (E:\t\qN). Use the FULL CI dispatch
  (gh workflow run tests.yml --ref chore/rebuild-from-9017) before publishing.
- Do not build new watchers, monitors, or evidence frameworks.
- The coordinator session reviews each result and provides the next prompt.
