---
date: 2026-09-17
depth: full
type: standard
plan: .cg-docs/plans/2026-09-16-documentation-ia-ux-redesign.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: skipped
---

# Documentation Redesign Review

Scope: origin/dev through 9e2ed000 plus phase 5 guidance and genuine host
evidence. Full routing applies because publication and schema contracts changed.

- **[P2.1]** [cg-code-quality] `docs/assets/site.js:194` — retained-page recovery loses mounted command controls and source actions.
  **Trigger**: Start on commands, change deployment metadata, navigate away.
  **Fix**: Preserve the verified page DOM and restore its reading/source controls.
  **Disposition**: safe_auto; covered by the authorized correctness work.
- **[P2.2]** [cg-performance] `docs/assets/docs-search.js:83` — each keystroke fetches deployment metadata and retokenizes the entire index; command filters also duplicate input/change work.
  **Evidence**: 622 entries, roughly 14.5 ms per rank call in reviewer measurement, plus an uncached metadata round trip per input.
  **Fix**: Debounce input, share in-flight identity checks, avoid duplicate initial checks and prepare ranking fields once.
  **Disposition**: reviewed as in-scope local responsiveness work; retain freshness checks before displaying cached data.
- **[P2.3]** [cg-architecture] `scripts/docs-help-build.js:9` — projection reopens catalog facts after strict validation, allowing mixed snapshots.
  **Trigger**: Change a catalog summary after the Python subprocess returns; projection changes while generated tables retain the validated value.
  **Fix**: Emit expected documents and the validated catalog in one envelope, with no later catalog read.
  **Disposition**: reviewed as in-scope canonical-writer correctness; refresh host evidence after sensitive source changes.
- **[P2.4]** [cg-testing] `scripts/tests/test_release_policy.py:199` and `scripts/tests/test_skill_management_migration.py:25` — four native-preflight assertions still enforce pre-redesign assumptions.
  **Evidence**: Full selected preflight found three checks expecting builds in sources/dev or a single-line metadata step, and one check interpreting historical migration text in the generated search index as active command definitions.
  **Fix**: Assert isolated producer-input generation and explicit verification; inspect indexed migration text with the same bounded source rule instead of exempting the entire index.
- **[P3.1]** [cg-architecture] `scripts/help/documentation.py:89` — validated multi-file writes are sequential; a later I/O error can leave mixed generated files.
  **Disposition**: advisory, skipped. Existing stale-output checks block completion/publication after partial writes; transactional multi-file promotion is a separate improvement, not an unverified success path.

## Additional Role Results

- cg-testing: Behavioral migration, route, input, browser and source-derivation cases are registered in the continuing test command. Native certification checks actual queries and final output; platform skips are recorded separately. P2.4 needs correction.
- cg-documentation: No additional issues found. Ownership declarations preserve manual prose, runtime examples name one tested host/model/OS, and the guide explains that help does not generate documentation.
- cg-version-control: No issues found. Feature branch is retained, base is dev, lockfile is tracked, no secret-shaped additions or files over 1 MiB were found, and dependency/test-output directories are excluded from staging.
- cg-reproducibility: No additional issues found beyond P2.3. Frozen v1 fixtures are unchanged since 98c5e718; v2 archives retain de64bf06 bytes. Repeat native and docs generation is deterministic, and final evidence fingerprints the tested working tree.
- cg-data-quality: No additional issues found beyond P2.3. Canonical schema validation, complete kind-qualified inventory, source-digest checks, bounded routes, duplicate rejection and shared-suite eligibility remain enforced.
- cg-adversarial: No additional issues found in local inspection. Producer code is byte-identified against protected code, expected output is independently generated in separate staging, artifact self-digests cannot replace derivation, and browser identity checks loaded shell/content before verified labels.
- cg-learnings-researcher: Applied the existing cross-file-contract lesson (2026-07-24) to validators/tests and the manual-wiki-ownership lesson (2026-05-19) to help-owned sections. No contradictory lesson found.

## Review Execution Limitation

The independent trust-review worker was blocked by the service's cybersecurity
filter and produced no review. It was not retried. Its requested roles were
completed locally by the main agent; they are not independent second opinions.
The independent code reviewer supplied usable quality, performance and
architecture results. No source edits or Pester runs were delegated to reviewers.
