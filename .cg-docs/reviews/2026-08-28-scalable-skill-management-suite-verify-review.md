---
date: 2026-08-31
depth: light
parent-review: .cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md
type: verification
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
  P1.10: skipped
  P1.11: fixed
  P2.1: skipped
---

# Verification Review: Scalable Skill Management Suite Phase 1

**Review mode**: light verification
**Parent review**: `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md`
**Files reviewed**: current changed and untracked Phase 1 implementation files
**Findings**: 15 (P0: 3, P1: 11, P2: 1)

## P0 -- BLOCKING

- **[P0.1]** [cg-code-quality, cg-testing] `scripts/skill_management/context.py:135` -- Maintainer authority still lacks an external trust anchor.
  **Why**: A copied dispatcher can forge the canonical URL, local default ref, and registry. The current positive test supplies the candidate checkout as its own trust root.
  **Fix**: Bind authority to immutable installation or revision evidence outside candidate-controlled metadata, sanitize all authority-changing Git inputs, and add a forged complete-checkout negative test.

- **[P0.2]** [cg-code-quality, cg-testing] `scripts/cg_skill.py:498` -- Handler code executes before handler origin is validated.
  **Why**: `importlib.import_module()` runs module-level code before `_validate_handler_origin()`. A linked, swapped, hard-linked, stale, or preloaded module can execute before rejection.
  **Fix**: Securely read and validate the exact handler file before execution, bind execution to those captured bytes, reject links and hard links, and test that wrong-origin code has no side effects.

- **[P0.3]** [cg-code-quality] `scripts/cg_validate_modules.py:744` -- Module validation reopens inventoried files by pathname.
  **Why**: Ownership and reference scanners use `Path.read_text()` after inventory, restoring the validation/read race fixed in generation.
  **Fix**: Build or consume one bounded no-follow byte snapshot and use it for all ownership and dependency checks.

## P1 -- CRITICAL

- **[P1.1]** [cg-code-quality, cg-testing] `scripts/skill_management/contracts.py:173` -- Strict contract loading accepts escaped lone Unicode surrogates.
  **Why**: Such keys or values can pass loading and later fail deterministic UTF-8 serialization.
  **Fix**: Validate every parsed key and string as Unicode scalar data and add high/low surrogate fixtures.

- **[P1.2]** [cg-code-quality, cg-testing] `scripts/skill_management/contracts.py:233` -- Safe-regex checks still permit exponential patterns.
  **Why**: Noncapturing nested quantifiers and ambiguous repeated alternation can bypass the current heuristic.
  **Fix**: Use a conservative parsed subset that rejects nested quantifiers and ambiguous repeated alternatives, with deadline-focused fixtures.

- **[P1.3]** [cg-code-quality, cg-testing] `scripts/skill_management/contracts.py:988` -- Action validation lacks exact duplicate and kind-specific root controls.
  **Why**: Conflicting actions for one path and protected target paths can pass common validation.
  **Fix**: Reject every duplicate portable identity and enforce explicit allowed roots or protected-target bans by action kind.

- **[P1.4]** [cg-code-quality] `scripts/skill_management/contracts.py:1033` -- Malformed registry records can crash cross-field validation.
  **Why**: `sorted(record_ids)` mixes strings and missing values after schema findings are collected.
  **Fix**: Make every invariant type-safe and sort only validated strings.

- **[P1.5]** [cg-code-quality] `scripts/cg_skill.py:142` -- Descriptor operation identity is not bound to its contract identity.
  **Why**: A descriptor can select another operation's otherwise valid contract.
  **Fix**: Require the expected contract basename and `$id` prefix for the descriptor operation.

- **[P1.6]** [cg-code-quality, cg-testing] `scripts/skill_management/paths.py:129` -- Shared inventory budgets and closure filtering occur after traversal begins.
  **Why**: Inactive, deep, or wide trees can consume resources or block public generation before selection.
  **Fix**: Enforce depth, entry, and byte budgets during traversal and skip inactive owned directory prefixes before entering them.

- **[P1.7]** [cg-code-quality] `scripts/skill_management/contracts.py:1190` -- Provenance lifecycle is not tied to terminal history evidence.
  **Why**: Removed provenance can end with an imported event, and tombstone revision/digest fields are not connected to removal evidence.
  **Fix**: Require terminal history event and lifecycle agreement and validate tombstone evidence against that event.

- **[P1.8]** [cg-code-quality] `.github/shared/skill-management/contracts/plan-v1.schema.json:75` -- Plan source revisions permit mutable names.
  **Why**: `sourceRevision` accepts any non-empty string rather than an immutable full commit.
  **Fix**: Enforce full commit grammar in runtime invariants and add mutable/short revision tests.

- **[P1.9]** [cg-testing] `scripts/cg_pr_preflight.py:40` -- Authoritative preflight omits new security-critical Phase 1 tests.
  **Why**: CI can pass without contract and dispatcher tests.
  **Fix**: Register both files and add a completeness assertion.

- **[P1.10]** [cg-testing] `.github/workflows/tests.yml:243` -- Required Python 3.8 behavior is not executed in CI.
  **Why**: Local Python 3.12 and grammar checks do not prove the supported runtime.
  **Fix**: Add a Python 3.8 job for the Phase 1 contract, dispatcher, generator, and validator surface.

- **[P1.11]** [cg-testing] `.github/shared/skill-management/contracts/result-v1.schema.json:30` -- Runtime and schema disagree on the automation role.
  **Why**: The schema advertises `automation`, while runtime invariants reject it.
  **Fix**: Keep v1 executable role vocabulary identical or stop rejecting the schema-advertised role until a versioned schema change is permitted.

## P2 -- IMPORTANT

- **[P2.1]** [cg-testing] `.cg-docs/work-reports/2026-08-28-scalable-skill-management-suite.md:40` -- Phase evidence counts are stale.
  **Why**: Current tests and collected counts differ from the initial Phase 1 report.
  **Fix**: Add dated, command-specific, interpreter-specific evidence with a stable result reference.

## Suppressed

- The empty generated bundle directory P2 note was suppressed because it targets the exact test block changed for the explicitly fixed P1.1 scope; no private files are emitted.

## Verification Performed By Agents

- Contracts and dispatcher: 81 passed.
- Packaging, ownership, drift, and registry: 192 passed, 11 skipped.
- Module registry validation passed.
- Python 3.8 runtime was unavailable locally.
