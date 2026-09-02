---
date: 2026-08-30
depth: full
type: standard
plan: .cg-docs/plans/2026-08-28-scalable-skill-management-suite.md
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P1.1: fixed
  P1.2: skipped
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
  P1.13: fixed
  P1.14: fixed
  P1.15: fixed
  P1.16: fixed
  P1.17: fixed
  P1.18: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: skipped
  P2.9: skipped
  P2.10: fixed
  P2.11: fixed
  P2.12: skipped
  P2.13: fixed
  P2.14: fixed
  P3.1: fixed
  P3.2: fixed
---

# Review Report: Scalable Skill Management Suite Phase 1

**Requested mode**: `mode:verify`
**Resolved mode**: `full` -- no prior standard review had fixed findings, so
verification mode fell back to deterministic schema/security-risk routing.
**Files reviewed**: 34 changed and untracked files
**Findings**: 37 (P0: 3, P1: 18, P2: 14, P3: 2)

## P0 -- BLOCKING

- **[P0.1]** [cg-adversarial, cg-code-quality, cg-testing] `scripts/skill_management/context.py:119` -- Mutable local repository metadata can grant maintainer authority.
  **Why**: A new repository with the canonical origin string, three copied module IDs, and a feature branch receives `role="maintainer"`. It has no canonical ancestry or trusted checkout identity, so future canonical writes can cross the consumer boundary.
  **Fix**: Bind authority to the trusted checkout that contains the running dispatcher, require a valid committed `HEAD` with trusted lineage, validate the complete registry, reject unsafe `GIT_*` overrides, and add forged-origin/history/registry tests.

- **[P0.2]** [cg-adversarial, cg-architecture] `scripts/cg_skill.py:100` -- Descriptor authority is not bound to the operation or trusted handler code.
  **Why**: A consumer-controlled descriptor can name another allowed operations module, and `importlib` does not verify module origin. Descriptor, contract, and handler revisions can also come from different roots.
  **Fix**: Require the handler identity to match the normalized operation, bind descriptors and handlers to one trusted source revision, verify module origin below the no-follow operations root, and test mismatched handlers and linked modules.

- **[P0.3]** [cg-learnings-researcher, cg-testing, cg-code-quality] `scripts/cg_validate_modules.py:225` and `scripts/cg_generate_targets.py:689` -- Shared resources can change between no-follow validation and pathname reads.
  **Why**: Inventory closes its checked handles and returns paths; generation then opens each path again, twice. A leaf or ancestor swap can package external or sensitive bytes after validation.
  **Fix**: Traverse from pinned no-follow directory handles, read each file once through the checked handle, carry exact bytes into the plan, and add leaf/ancestor substitution-race tests.

## P1 -- CRITICAL

- **[P1.1]** [cg-code-quality, cg-testing, cg-version-control] `scripts/cg_generate_targets.py:570` -- Default generation publishes the private management module.
  **Why**: `active_suites=None` includes every owned module. The normal `--all` command emits the internal skill and contracts into four generated product trees while tests use an explicit filtered closure.
  **Fix**: Resolve the public suite closure by default, require explicit internal selection, and test the production CLI path.

- **[P1.2]** [cg-version-control] `.github/skills/cg-skill-management/SKILL.md:8` -- The private skill is visible through the current whole-root Copilot link.
  **Why**: Copilot receives all of `.github/skills/`, independent of module closure, so the incomplete private bundle is discoverable before Phase 7.
  **Fix**: Add an install-time exclusion or managed selected-bundle projection before merge and prove a consumer Copilot installation does not receive this bundle.

- **[P1.3]** [cg-data-quality, cg-adversarial] `scripts/skill_management/contracts.py:144` -- Contract loading accepts duplicate keys, non-JSON numbers, and invalid Unicode scalar values.
  **Why**: Default `json.loads()` keeps the last duplicate key and accepts `NaN` and infinities. These values can weaken rules or break canonical serialization.
  **Fix**: Use one strict decoder with duplicate-key detection, `parse_constant` rejection, Unicode scalar checks, and exact negative tests.

- **[P1.4]** [cg-data-quality, cg-adversarial] `scripts/skill_management/contracts.py:450` -- Runtime validation does not first prove that the complete instance is bounded JSON.
  **Why**: Tuples, bytes, `Path`, non-string keys, and non-finite values under unconstrained fields can pass validation and fail during JSON output or hashing.
  **Fix**: Validate the full instance recursively as bounded JSON before schema traversal and test nested invalid values.

- **[P1.5]** [cg-data-quality, cg-adversarial] `scripts/skill_management/contracts.py:172` -- Local references and keyword/type combinations can silently disable constraints.
  **Why**: Container references and no-progress cycles such as `$ref: "#"` pass; string keywords on arrays are ignored; anchored patterns can accept trailing newlines.
  **Fix**: Validate reference targets and escapes, reject cycles and incompatible keyword/type combinations, use full-string identity checks, and add exact bypass tests.

- **[P1.6]** [cg-code-quality, cg-documentation] `.github/shared/skill-management/contracts/schema-subset-v1.schema.json:50` -- The committed meta-contract and runtime semantic validator disagree.
  **Why**: Meta-contract validation accepts invalid keyword values, regular expressions, ranges, and unresolved references that runtime validation rejects.
  **Fix**: Route both paths through one canonical semantic entry point and run the same invalid fixture matrix against each path.

- **[P1.7]** [cg-performance, cg-adversarial] `scripts/skill_management/contracts.py:186` -- Schema and instance validation have no depth, node, finding, input-size, or safe-regex budget.
  **Why**: Deep references can raise `RecursionError`, large instances can exhaust memory, and catastrophic patterns can consume exponential CPU.
  **Fix**: Add deterministic central budgets, iterative traversal, a safe pattern subset or timeout, bounded findings, and deadline/depth tests.

- **[P1.8]** [all implementation reviewers] `scripts/skill_management/planning.py:36` -- An error finding can be returned as success.
  **Why**: Explicit exit code 0 overrides error severity, and result invariants accept `ok: true` with an error finding.
  **Fix**: Reject or normalize zero exit codes when errors exist and enforce the same invariant in result validation.

- **[P1.9]** [cg-code-quality, cg-testing, cg-architecture] `scripts/cg_skill.py:215` -- The dispatcher cannot represent plan versus apply.
  **Why**: It always selects the descriptor's first phase and has no common `--apply <digest>` parsing or `planDigest` request binding.
  **Fix**: Parse the common apply digest, derive the phase, validate descriptor support, and test plan/apply/error cases.

- **[P1.10]** [cg-code-quality, cg-testing, cg-architecture] `.github/shared/skill-management/contracts/operation-descriptor-v1.schema.json:52` -- Operation arguments and result data lack complete typed contracts.
  **Why**: The dispatcher validates raw `argv` only, while handler `data` is unrestricted. Unknown options, typed fields, malformed data, and non-JSON values can bypass operation contracts.
  **Fix**: Give each descriptor explicit normalized-argument and result-data schemas and validate both at the generic boundary.

- **[P1.11]** [cg-code-quality, cg-testing, cg-architecture] `scripts/cg_skill.py:286` -- Unexpected exceptions and serialization failures escape the stable redacted result protocol.
  **Why**: `RuntimeError`, `KeyError`, `RecursionError`, and output failures can emit tracebacks and no JSON envelope.
  **Fix**: Catch `Exception` at the outer operation boundary, preserve process-control exceptions, pre-serialize within the boundary, and test secret-bearing failures in both formats.

- **[P1.12]** [cg-code-quality] `scripts/cg_skill.py:301` -- Human output discards successful operation content.
  **Why**: It omits operation data, actions, manifest health, and plan digest, so `find`, `info`, and mutation plans would not be usable in the default format.
  **Fix**: Define and test deterministic common presentation for all required envelope fields without operation-specific router branches.

- **[P1.13]** [cg-testing, cg-reproducibility] `scripts/tests/test_skill_management_dispatch.py:97` -- Dispatcher tests fail on required Python 3.8.
  **Why**: `Path.write_text(..., newline=...)` is not available on Python 3.8; grammar checks do not detect the runtime API failure.
  **Fix**: Write through `path.open(..., newline="\n")` or bytes and add actual Python 3.8 CI execution.

- **[P1.14]** [cg-data-quality, cg-reproducibility, cg-adversarial] `.github/shared/skill-management/contracts/plan-v1.schema.json:138` -- Plan, result, and provenance paths are not confined or collision-safe.
  **Why**: Absolute, traversal, UNC, drive, control-character, reserved, and portable-colliding paths satisfy the contracts.
  **Fix**: Apply shared portable path invariants, action-kind root policy, and collision checks with POSIX and Windows fixtures.

- **[P1.15]** [cg-data-quality, cg-documentation] `scripts/skill_management/contracts.py:607` -- Lifecycle, provenance, successor, migration, tombstone, and attestation invariants are incomplete.
  **Why**: Deprecated records can omit valid successors; tombstone identities and history digests can disagree; attestation keys can collide portably.
  **Fix**: Add deterministic graph and cross-field invariants plus negative fixtures for missing, cyclic, mismatched, and colliding state.

- **[P1.16]** [cg-reproducibility, cg-performance, cg-adversarial] `scripts/cg_generate_targets.py:689` -- Recursive shared scanning reads inactive content before selection and has no resource ceilings.
  **Why**: Excluded binary or oversized files can block public generation; deep/wide trees can exhaust resources.
  **Fix**: Filter by validated closure before reads, use one bounded byte read, and enforce depth, count, per-file, and total-byte limits.

- **[P1.17]** [cg-learnings-researcher] `scripts/cg_generate_targets.py:1175` -- Generated JSON operation descriptors retain canonical `.github/` runtime paths.
  **Why**: Dependency rewriting handles Markdown only. Future native descriptors will point to canonical contract and workflow paths that do not exist in isolated native trees.
  **Fix**: Add descriptor-aware path mapping or a native resolver and test a real descriptor on all four generated platforms.

- **[P1.18]** [cg-data-quality] `scripts/skill_management/contracts.py:562` -- Identity patterns can accept a trailing newline.
  **Why**: Python `$` matches before a final newline, so identifiers and digest strings can differ from displayed identity.
  **Fix**: Use full-string validation or `\Z`, reject control characters, and add newline fixtures for every identity field.

## P2 -- IMPORTANT

- **[P2.1]** [cg-documentation, cg-testing] `scripts/tests/test_skill_management_contracts.py:325` -- Cross-file vocabulary alignment covers only origin, admission, and lifecycle.
  **Why**: Roles, phases, severities, manifest health, availability, action kinds, and exit-code meanings can drift.
  **Fix**: Compare every shared vocabulary across constants, schemas, docs, and representative fixtures.

- **[P2.2]** [cg-testing] `scripts/tests/test_skill_management_contracts.py:195` -- V1 lacks invalid fixtures for each claimed contract and schema keyword.
  **Why**: Descriptor, plan, provenance, attestation, reference, range, and lifecycle failures are under-tested.
  **Fix**: Add exact path/code negative fixtures for every contract and supported keyword.

- **[P2.3]** [cg-testing] `scripts/tests/test_cg_generate_targets.py:202` -- V2 path-safety evidence has platform and attack-surface gaps.
  **Why**: Leaf links, junctions, special files, reserved names, case/Unicode collisions, ancestor links, and swap races are absent or skipped.
  **Fix**: Add platform-independent policy tests and capability-gated real filesystem boundary tests.

- **[P2.4]** [cg-architecture, cg-code-quality] `scripts/cg_validate_modules.py:157` -- Security-sensitive path and inventory rules are duplicated and coupled in the wrong direction.
  **Why**: Generator, validator, and dispatcher have separate path implementations, while the generator imports a validator CLI module.
  **Fix**: Move path, no-follow inventory, and byte capture to one low-level infrastructure module used by all callers.

- **[P2.5]** [cg-code-quality] `scripts/cg_validate_modules.py:923` -- Invalid recursive assets can produce a raw validator traceback in some check combinations.
  **Why**: Ownership handles inventory errors, but dependency and cross-suite paths rebuild inventory without one error boundary.
  **Fix**: Build one validated snapshot, convert failures to stable findings, and pass it to all checks.

- **[P2.6]** [cg-performance] `scripts/cg_generate_targets.py:465` -- Generation planning contains quadratic output and namespace stages.
  **Why**: Asset and destination indexes are rebuilt per output and namespace conflicts compare all pairs.
  **Fix**: Build one render context and use sorted adjacent-key or trie collision checks with scale benchmarks.

- **[P2.7]** [cg-performance] `scripts/cg_validate_modules.py:965` -- Module validation repeatedly rebuilds ownership maps and rereads assets.
  **Why**: Complexity grows by modules, assets, and globs; recursive DFS can also exceed recursion depth.
  **Fix**: Use one validation snapshot and iterative graph traversal with call-count and long-graph tests.

- **[P2.8]** [cg-documentation, cg-code-quality] `scripts/skill_management/contracts.py:133` -- New public APIs and the management skill documentation are incomplete.
  **Why**: Public functions lack parameter/return/raise/example sections, and the skill omits contract meanings, transitions, exit codes, and private-operation state.
  **Fix**: Add concise API docstrings and compact common contract tables.

- **[P2.9]** [cg-learnings-researcher] `.cg-docs/work-reports/2026-08-28-scalable-skill-management-suite.md:36` -- Phase evidence is not independently reproducible.
  **Why**: Counts omit exact commands, run time, interpreter, platform, revision, and a stable result artifact.
  **Fix**: Append run-scoped evidence facts and keep active state as compact pointers.

- **[P2.10]** [cg-reproducibility] `scripts/cg_validate_modules.py:232` -- Nested hidden, cache, and temporary artifacts are treated as shared resources.
  **Why**: Hidden entries are skipped only at the first level, making generated output depend on local workspace state.
  **Fix**: Apply explicit resource policy at every depth and add negative fixtures.

- **[P2.11]** [cg-reproducibility] `scripts/cg_generate_targets.py:790` -- Executable metadata depends on host filesystem mode bits.
  **Why**: The same committed source can produce different ownership manifest bytes on Windows and POSIX.
  **Fix**: Derive executable state from portable canonical metadata and test byte parity.

- **[P2.12]** [cg-code-quality, cg-reproducibility] `.github/shared/skill-management/contracts/request-v1.schema.json:39` -- Root naming and serialization are inconsistent and machine-specific.
  **Why**: Requests use optional `root` plus `sourceRoot`, plans use required `projectRoot`, and runtime emits absolute local paths.
  **Fix**: Use one stable root vocabulary, keep absolute paths only in runtime context, and bind persisted identities to repository-relative or revision data.

- **[P2.13]** [cg-code-quality] `scripts/cg_skill.py:331` -- JSON usage-error format detection is inconsistent.
  **Why**: `--format=json` can emit human output and unrelated operation tokens can cause false JSON selection.
  **Fix**: Use a common-option pre-parser and snapshot both valid option forms and malformed invocations.

- **[P2.14]** [cg-testing, cg-reproducibility] `scripts/skill_management/contracts.py:607` -- Registry ordering and identity limits are not canonical across contracts.
  **Why**: Semantically equivalent array orderings produce different bytes, and ID length rules differ between registry, provenance, tombstone, and successor fields.
  **Fix**: Enforce or normalize canonical ordering and one shared identity grammar/limit across all contracts.

## P3 -- MINOR

- **[P3.1]** [cg-code-quality] `scripts/cg_validate_modules.py:704` -- `_resolve_asset_owner()` is an unused compatibility alias.
  **Why**: It has no callers after migration and keeps an obsolete private API.
  **Fix**: Remove the alias after confirming no external consumer exists.

- **[P3.2]** [cg-performance] `scripts/skill_management/context.py:155` -- Equal roots trigger duplicate Git subprocesses with independent timeouts.
  **Why**: One context lookup can run several identical root probes and wait for multiple full timeouts.
  **Fix**: Cache probes by resolved root, use one total deadline, disable prompts, and bound output.

## Review Quality

- All ten required full-mode agents returned usable, file-specific output.
- No protected artifact deletion, replacement, rename, or move recommendation was retained.
- Review agents reran relevant Python/module checks; no Pester command was run during review.

## Brain Context Applied

- Canonical-to-native packaging must be deterministic, confined, ownership-safe, and independently usable.
- Shared state contracts must stay aligned across documentation, validators, schemas, fixtures, and tests.
- Security-sensitive files must be read through the same checked handle used for validation.
