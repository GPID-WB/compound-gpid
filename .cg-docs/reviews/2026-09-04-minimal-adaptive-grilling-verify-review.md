---
date: 2026-09-09
depth: light
parent-review: .cg-docs/reviews/2026-09-04-minimal-adaptive-grilling-review.md
type: verification
findings:
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
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
---

# Verification Review: Evidence-Backed /cg-help Phases 1-2

**Review mode**: light verification
**Files reviewed**: current tracked and untracked Phase 1/2 worktree changes
**Findings**: 15 (P0: 0, P1: 11, P2: 4, P3: 0)

## P0 - BLOCKING

No P0 findings.

## P1 - CRITICAL

- **[P1.1]** [cg-code-quality, cg-testing] `scripts/tests/test_target_drift.py:230` - Native target outputs and ownership manifests are stale after the source mapping and prompt changes.
  **Why**: Target drift checks report missing help shared files, stale generated commands, and stale ownership manifests. Phase 2 must not leave existing target fixtures red even though full target integration is deferred to Phase 5.
  **Fix**: Adjust the pre-Phase-5 generation contract so current targets remain green without claiming Phase 5 integration, then rerun target drift tests. Do not silently move Phase 5 work into Phase 2.
- **[P1.2]** [cg-code-quality, cg-testing] `scripts/tests/test_skill_management_migration.py:99` - The expected `cap-help` asset list omits `.github/shared/help-catalog.json`.
  **Why**: Phase 2 correctly adds the catalog to `cap-help`, but the existing migration assertion still requires only `shell-commands.json` and now fails.
  **Fix**: Assert the exact sorted two-file Phase 2 ownership contract.
- **[P1.3]** [cg-code-quality] `scripts/skill_management/services/catalog.py:227`, `scripts/cg_skill_catalog.py:344`, `scripts/skill_management/services/lifecycle.py:623` - Several ownership consumers still match raw `ownedAssets` globs without `ownershipExclusions`.
  **Why**: Excluded assets can be treated as active, routed through the wrong module, or retained through removal.
  **Fix**: Use the central resolved-owner helpers for every ownership decision and add an exclusion fixture whose replacement owner is outside the active closure.
- **[P1.4]** [cg-code-quality, cg-testing] `scripts/help/catalog.py:299` - `supportedSuites` validation accepts an incomplete subset of owner closures.
  **Why**: A `cap-help` command can omit `cr` and silently disappear from CR-only projects even though both suite closures contain the owner.
  **Fix**: Derive all suite closures containing the owner and require exact sorted equality.
- **[P1.5]** [cg-code-quality, cg-testing] `scripts/help/catalog.py:378` - Alias collision checks do not apply the planned query normalization contract.
  **Why**: NFKC-equivalent or whitespace-equivalent aliases can pass catalog generation and collide during query lookup.
  **Fix**: Use one NFKC, trim, slash-aware, case-folding normalizer and test Unicode and whitespace collisions.
- **[P1.6]** [cg-code-quality, cg-testing] `scripts/help/catalog.py:98` - Escaped unpaired Unicode surrogates pass strict parsing and later crash UTF-8 serialization.
  **Why**: The CLI can emit a traceback and exit code 1 instead of the documented source-validation error and exit code 2.
  **Fix**: Reject surrogate code points during recursive strict JSON validation and test diagnostics, exit code, and non-mutation.
- **[P1.7]** [cg-code-quality] `scripts/help/catalog.py:630` - Catalog generation performs schema validation but omits full registry layer and ownership validation.
  **Why**: Cycles or illegal cross-layer dependencies can influence ownership closure and supported-suite evidence without stopping generation.
  **Fix**: Run the complete registry layer and ownership checks before help extraction.
- **[P1.8]** [cg-testing] `scripts/cg_project_manifest.py:494` - `ownershipExclusions` is treated as required in legacy schema-v1 manifests.
  **Why**: Five existing skill-catalog tests fail for otherwise valid manifests that predate the optional field.
  **Fix**: Default a missing legacy field to `{}` and add a legacy-manifest regression test.
- **[P1.9]** [cg-testing] `scripts/cg_generate_targets.py:705` - Unfiltered canonical scans now derive both suite IDs and reject schema-v1 or capability-only fixtures.
  **Why**: Twelve generator tests fail with `unknown active suite` when no suite filter was requested.
  **Fix**: Resolve suite closure only when `active_suites` or `loadable_module_ids` is explicitly supplied; preserve prior unfiltered behavior.
- **[P1.10]** [cg-testing] `scripts/help/catalog.py:801` - Installer inventory validation uses substring searches.
  **Why**: Removing real installation logic can remain green when command names still occur in comments or final help text.
  **Fix**: Parse bounded installer declarations and compare exact command sets; add a comment-only negative fixture.
- **[P1.11]** [cg-code-quality, cg-testing] `scripts/cg_projection_benchmark.py:348` - The projection route oracle neither resolves exclusions nor compares the resolved owner with `expectedRoute`.
  **Why**: The benchmark can certify a wrong module route for overlapping ownership patterns.
  **Fix**: Resolve the unique owner through central helpers and require equality with `expectedRoute`; add an overlap-with-exclusion fixture.

## P2 - IMPORTANT

- **[P2.1]** [cg-code-quality] `scripts/help/catalog.py:439` - Slash follow-up syntax conflicts with the approved plan.
  **Why**: Validation requires `/cg-help slash:cg-skill`, while the plan requires `/cg-help /cg-skill`; only shell commands use `shell:` qualification.
  **Fix**: Render slash IDs with a leading slash and shell IDs with `shell:`; update the candidate fixture.
- **[P2.2]** [cg-testing] `scripts/help/catalog.py:1088` - Repinning replaces metadata before final source validation.
  **Why**: A final validation failure can report an error after metadata has already changed.
  **Fix**: Validate prospective bytes and the captured source graph before atomic replacement; test that a forced final failure preserves original bytes.
- **[P2.3]** [cg-testing] `scripts/help/catalog.py:126` - Runtime-validator and JSON-Schema parity is not independently tested.
  **Why**: The two contracts already differ for values such as numeric `1.0` under integer schema rules.
  **Fix**: Run a shared valid/invalid corpus through both validators and align results.
- **[P2.4]** [cg-testing] `scripts/tests/test_help_catalog.py:275` - The sidecar non-emission test does not inspect generated outputs.
  **Why**: It remains green if future target generation emits `.help.json` files as target outputs or ownership entries.
  **Fix**: Build each target plan and assert no output or ownership-manifest record uses a sidecar as source or destination.

## Passed Checks

- Both verification reviewers returned usable, file-specific output.
- `python scripts/cg_generate_help_catalog.py --check` passed.
- `python -m pytest scripts/tests/test_help_catalog.py -q` passed with 26 tests.
- Prior fixed adaptive-brainstorm findings were not re-reported.

## Verification Failures Reported By Reviewers

- Target/projection review runs found target drift and compatibility failures.
- Skill-management migration review found one stale ownership expectation.
- No review agent modified the worktree.
