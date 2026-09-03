# Test fixtures

<!-- Created 2026-09-03. -->

Generated-target parity is owned by `scripts/tests/test_target_drift.py` and the
committed native ownership manifests. The latest `dev` architecture removes
the duplicate `cg_characterization_manifest.json` snapshot, so generated files
must be checked through the authoritative target-drift and generator tests.

The CR ML routing fixture remains:

- `cr_ml_skill_evaluation.json` records representative route-to-reference
	cases and required semantic safeguards for the CR ML contract.