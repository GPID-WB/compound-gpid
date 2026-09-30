---
date: 2026-09-02
depth: full
type: standard
plan: .cg-docs/plans/2026-09-02-c-research-output-workspace-migration.md
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
---

# Review Report: Root-Level c-research Output Workspace and Migration

**Review mode:** full

**Files reviewed:** migration helper and layout contract, setup/update surfaces,
CR prompts/skills/agents/instructions, evidence runtime, project documentation,
generated native targets, tests, roadmap/context changes, and the current
presentation artifacts. Generated `.cg-docs/views/**` bodies were not read.

## Review Findings

### P0 — Blocking

**[P0.1]** `scripts/cg_migrate_research_layout.py` — filesystem migration can
escape through symlinks and races.

**Why:** The source tree checks only the leaf `.cg-docs/research` path, so a
symlinked `.cg-docs/` ancestor can expose an external tree. A dangling
destination symlink makes `Path.exists()` false, after which `shutil.copy2()` can
follow the link outside the project. Source and destination identities are not
revalidated before copy or unlink, so concurrent edits can overwrite or delete
unexpected content.

**Fix:** Reject every source and destination symlink/reparse ancestor, detect
dangling final symlinks with link-aware checks, and use no-follow,
collision-safe publication with source identity revalidation before deletion.
Add ancestor, dangling-link, and replacement-race tests.

**[P0.2]** `research_evidence/src/research_evidence/config.py` and
`research_evidence/src/research_evidence/transactions.py` — the new evidence
root is not fully path-confined.

**Why:** The runtime rejects a symlink at `c-research/evidence` itself but does
not reject a symlinked `c-research/` ancestor or symlinked descendants such as
`runs/` and `index/`. `ArtifactStore` and `LexicalIndex` then create/open state
through those paths, potentially writing canonical evidence or derived indexes
outside the repository.

**Fix:** Validate and pin every existing ancestor from the project root through
`c-research/evidence` and every created journal/index path; use the shared
no-follow filesystem primitives for creation/opening. Add parent and descendant
symlink tests.

**[P0.3]** `scripts/cg_migrate_research_layout.py` — migration does not enforce
the output-only boundary.

**Why:** Every regular file below an allowed legacy artifact directory is moved.
A dataset, source PDF, or code file placed under the old research tree is copied
into the version-controlled `c-research/` output workspace and removed from its
original location without explicit classification.

**Fix:** Require an explicit migration manifest or human classification for
non-output files and reject reserved input/source directories. Add fixtures for
data, raw inputs, source documents, and code in legacy directories.

### P1 — Critical

**[P1.1]** `scripts/cg_migrate_research_layout.py` — apply mode ignores live
operational legacy-path references.

**Why:** `main()` discovers references, but only `--check` uses them to determine
its exit status. Normal apply mode can move files and report success while live
writers still point to `.cg-docs/research/`.

**Fix:** Fail before the first mutation when any operational reference exists,
then run a post-migration scan. Recognize both POSIX and Windows separators.

**[P1.2]** `scripts/update.ps1` — Windows link/update flow can skip the research
migration.

**Why:** The migration block is inside the `-not $env:CG_INTERNAL_CALL` guard,
while `link.ps1` sets that variable. Bash invokes the migration during its
corresponding internal flow, so the platforms diverge.

**Fix:** Run the research migration outside the internal-call guard, or invoke
it explicitly from both link paths, with parity tests for the same behavior.

**[P1.3]** `.github/prompts/cr-work.prompt.md` and
`.github/skills/cr-skill-research-workflow/SKILL.md` — CR activation still checks
obsolete `modules:` terminology.

**Why:** The project configuration uses `suites: [cg]`, `[cr]`, or `[cg, cr]`.
The CR work prompt can therefore fail to recognize that research is active even
when `cr` is configured. The same wording has propagated to generated native
targets.

**Fix:** Gate on the canonical `suites:` field and regenerate all native targets;
add a cross-target assertion.

**[P1.4]** `.cg-docs/research/manuscript/2026-08-26-ai-knowledge-work-presentation-practitioner-tour.md`
and `c-research/manuscripts/2026-08-26-ai-knowledge-work-presentation-practitioner-tour.md`
— divergent untracked manuscript authorities exist.

**Why:** Both copies are present and have different hashes/content. The current
execution report claims the legacy copy was removed, while the migration test
reports the duplicate. A partial commit could preserve the wrong draft or leave
two authorities.

**Fix:** The author must choose or merge the copies. Preserve both until that
choice is explicit, then update provenance, remove only the non-authoritative
copy, and rerun migration/path checks.

**[P1.5]** `presentation/ai-knowledge-work-presentation.html` and the practitioner
tour manuscripts — presentation source lineage is inconsistent.

**Why:** The deck declares the `c-research/manuscripts/` copy as its source, but
the deck contains 21 sections while that manuscript contains a different
structure; the legacy copy appears to match the deck. The migration cannot
silently decide which research output governs the deck.

**Fix:** Reconcile the deck and manuscript authority, then stage/update the deck
metadata and canonical manuscript together.

**[P1.6]** `scripts/update.sh`, `scripts/update.ps1`, and
`scripts/cg_generate_targets.py` — active-suite filtering is not end-to-end.

**Why:** The generator accepts `--active-suites`, but update flows invoke
unfiltered `--all`. A project configured as CG-only can therefore receive CR
content in generated native trees, undermining suite activation.

**Fix:** Either generate consumer-local targets using each project's active
suite configuration or explicitly document and test runtime-only suite
filtering. Add CG-only, CR-only, and mixed end-to-end cases.

**[P1.7]** `.github/prompts/cr-brainstorm.prompt.md` — prompt permissions do not
cover required research-output writes.

**Why:** The workflow creates `c-research/scoping/` and
`c-research/normative-decisions/`, but its permission block authorizes creation
only under `.cg-docs/brainstorms/`.

**Fix:** Authorize the two root-level research-output directories while retaining
restrictions on `roadmap.json`, data, and unrelated project files.

**[P1.8]** `.github/skills/cr-skill-replication-standards/SKILL.md` — replication
output location is ambiguous.

**Why:** The skill uses `replication-package/` for required seeds/codebooks,
while the canonical research layout is `c-research/replication/` and the
replication agent accepts both paths without an authority rule.

**Fix:** Declare `c-research/replication/` canonical; label
`replication-package/` as an explicit export/archive location only.

**[P1.9]** `roadmap.json` and `compound-gpid.context.md` — unrelated uncommitted
changes remove or alter existing project governance records.

**Why:** The current diff removes unrelated roadmap entries and shared context
rules while this migration is in progress. This is outside the approved
c-research scope and risks losing institutional history.

**Fix:** Reconcile those files against their pre-change state before committing.
Do not silently revert them during this review; the owner must decide which
parallel work should be retained.

### P2 — Important

**[P2.1]** `scripts/cg_migrate_research_layout.py` — reference scanning reads
whole files across the repository and includes input trees.

**Why:** Each candidate is loaded with `read_bytes()` even though only a small
legacy-path marker is needed. Large or sensitive `data/` files can be read during
updates, increasing latency and memory pressure.

**Fix:** Prune data/source/dependency trees and scan eligible text files in
bounded chunks with marker overlap.

**[P2.2]** `scripts/research_layout.py` — the canonical artifact list and legacy
mapping are duplicated.

**Why:** The two structures can drift, causing a newly supported artifact type
to be scaffolded but not migrated, or vice versa.

**Fix:** Derive the legacy mapping from the canonical artifact tuple, adding only
the singular `manuscript` compatibility alias.

**[P2.3]** `scripts/cg_migrate_research_layout.py` — historical/preserved reference
classification is incomplete.

**Why:** The classifier duplicates process-directory knowledge and omits
`evidence-fixtures/`, `inbox/`, and `competitive-reviews/`. Old-path text in
those protected or generated areas can be falsely reported as operational.

**Fix:** Centralize preserved/historical/generated prefixes and return an explicit
non-blocking classification for those directories.

**[P2.4]** `scripts/cg_migrate_research_layout.py` — migration writes are not
atomic and source identity is not retained through publication.

**Why:** `copy2()` writes directly to the final path and source deletion follows
only an earlier hash check. An interruption can leave a partial destination,
and a concurrent source edit can be deleted.

**Fix:** Use a temporary same-directory file, flush/sync, publish with
non-clobber semantics, rehash/revalidate the source, and record source/destination
hashes in the migration result.

**[P2.5]** `scripts/cg_migrate_research_layout.py` — direct migration does not
create the complete research scaffold.

**Why:** It creates only parent directories for files encountered. A project with
one artifact type does not receive the complete documented output layout.

**Fix:** After successful migration, create the fixed `RESEARCH_OUTPUT_DIRECTORIES`
scaffold and test sparse/empty legacy trees.

**[P2.6]** `tests/update.Tests.ps1` and `tests/bash-scripts.Tests.ps1` — updater
coverage is source-text-only.

**Why:** The tests assert helper names and arguments but never execute either
updater against a legacy tree, so platform gating, conflict handling, and
failure propagation remain unproved.

**Fix:** Add isolated behavioral fixtures or a shared helper invocation test for
old tree, conflict, dangling link, and no-op cases.

**[P2.7]** `docs/reference.md`, `.github/skills/cg-skill-setup/SKILL.md`, and
related configuration docs — `compound-gpid.local.md` ownership is contradictory.

**Why:** Some documentation calls it user-specific/gitignored, while the project
instructions and file map require it to be committed team configuration. This
can silently drop `suites: [cr]` on another clone.

**Fix:** Make the committed team-config rule canonical and reserve machine-local
status for `.cg-version`; add a consistency test.

## Passed Checks

- The generic Brain remains `.cg-docs/`-only and excludes `c-research/`.
- The artifact-type layout and separate `data/` boundary are documented.
- Focused migration/path tests pass when no duplicate legacy manuscript is
  present; the current worktree duplicate must be resolved before the migration
  gate can pass.
- Full safe Pester run: 2,460 passed, 0 failed, 3 skipped.
- Evidence package: 112 passed with one existing deprecation warning.
- Target generation and focused platform/advisory tests pass when generated
  changes are accepted as the current worktree baseline.

## Review Notes

Generated `.cg-docs/views/**` bodies were not read. Protected Compound GPID
artifacts were not modified by review dispatch. Findings recommending changes to
those protected artifacts must be handled as manual owner decisions.

## Autofix Resolution

The safe fixes applied during this review include:

- root-anchored, no-follow migration reads and deletes;
- atomic, non-clobbering destination publication with source/destination
  rechecks and recovery;
- ancestor-link rejection, stale-reference blocking, bounded scans, explicit
  approval for input-like legacy files, and complete c-research scaffolding;
- evidence-root, transaction-lock, resource, compatibility, retrieval-inventory,
  and derived-index containment checks;
- CR suite activation, brainstorm permissions, replication staging terminology,
  updater parity/dangling-link handling, migrated manuscript links, reference
  documentation, and generated-target propagation;
- regression tests for symlink ancestors, dangling links, source/destination
  races, stale references, sparse trees, compatibility paths, and evidence/index
  containment.

Current verification: 29 migration tests pass; 122 evidence tests pass with one
dependency deprecation warning; 890 repository Python tests pass with one
platform-appropriate skip; 2,446 of 2,449 safe Pester checks pass with zero
failures and three environment-appropriate skips; the migration check reports
`up-to-date`; and `git diff --check` passes.

The deck-matching 21-slide practitioner manuscript is canonical. The former
16-slide draft is retained as an explicitly superseded alternate, the legacy
`.cg-docs/research/` root is absent, and no owner decisions remain open for
this migration review. The shared native trees are documented as an all-suite
distribution baseline; `--active-suites` is reserved for isolated builds.

Supplemental findings `P1.10` (stale retrieval inventory path), `P1.11`
(invalid legacy local-path eligibility), `P1.12` (reproducibility attestation),
`P2.8` (cross-platform environment metadata), and `P2.9` (generated-target
drift) are all fixed and covered by the final verification gates above.
