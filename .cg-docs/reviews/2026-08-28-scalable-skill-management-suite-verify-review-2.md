---
date: 2026-09-01
depth: light
parent-review: .cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md
type: verification
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: skipped
  P2.1: skipped
---

# Verification Review: Scalable Skill Management Suite

**Review mode**: light verification
**Parent review**: `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md`
**Files reviewed**: current branch against `main`, plus completion metadata
**Findings**: 10 (P0: 2, P1: 7, P2: 1)

## P0 -- BLOCKING

- **[P0.1]** [cg-testing] `scripts/cg_generate_targets.py:689` -- Non-shared canonical assets still use check-then-pathname reads.
  **Why**: Prompts, agents, skills, instructions, the registry, and target mapping are checked and then reopened by pathname. A leaf or ancestor swap can package different bytes after validation.
  **Fix**: Capture every canonical asset once through a root-anchored no-follow reader with hard-link rejection, then parse and render only those bytes. Add leaf and ancestor swap tests for each asset class.

- **[P0.2]** [cg-testing] `scripts/cg_skill.py:244` -- Captured handler execution does not bind imported dependencies.
  **Why**: The selected operation file is captured securely, but its imports use Python's normal importer. A linked, hard-linked, swapped, or preloaded helper can execute outside the captured-byte trust boundary.
  **Fix**: Bind the complete internal dependency closure to trusted captured bytes or a verified immutable installation. Add a linked-helper side-effect test.

## P1 -- CRITICAL

- **[P1.1]** [cg-code-quality, cg-testing] `scripts/cg_skill.py:282` -- The installed command rejects normal consumer projects.
  **Why**: An omitted `--source-root` defaults to the consumer project. The dispatcher then rejects it because it differs from the installation root. Public wrappers and the prompt omit this undocumented argument.
  **Fix**: Default the source root to the trusted runtime root while retaining the consumer project root. Add an installed-wrapper integration test with separate roots.

- **[P1.2]** [cg-code-quality] `scripts/skill_management/services/admission.py:197` -- Import, vendoring, and update do not enforce `allowedUpstreamSkillRoots`.
  **Why**: The policy is loaded, but normalized source paths are not checked against its approved roots before network acquisition.
  **Fix**: Require a component-aware allowed-root match before provider access and again when apply reloads evidence. Add outside-root and prefix-confusion tests.

- **[P1.3]** [cg-testing] `scripts/skill_management/contracts.py:1102` -- Removal migrations can modify protected or executable repository state.
  **Why**: The denylist does not exclude Git metadata, workflows, executable code, canonical registries, or charter/config files.
  **Fix**: Use a positive allowlist of reference-bearing project files and add no-write negative tests for protected targets and portable case aliases.

- **[P1.4]** [cg-testing] `scripts/skill_management/contracts.py:313` -- The safe-regex guard permits exponential character-class patterns.
  **Why**: `^([a-z]+)+$` passes validation and can cause exponential matching time.
  **Fix**: Enforce a conservative parsed subset that rejects nested quantified groups and ambiguous repeated alternatives. Add exact negative fixtures.

- **[P1.5]** [cg-testing] `scripts/skill_management/contracts.py:790` -- Strict JSON validation does not validate object keys as Unicode scalar data.
  **Why**: Escaped lone-surrogate keys load successfully but later fail canonical UTF-8 serialization.
  **Fix**: Validate every string key before pointer construction or sorting. Add high- and low-surrogate key fixtures.

- **[P1.6]** [cg-testing] `scripts/skill_management/contracts.py:246` -- Contract files are reopened by pathname after validation.
  **Why**: `load_contract()` checks metadata, then reads through a new pathname lookup without pinned handles or hard-link rejection.
  **Fix**: Use a root-anchored no-follow read and pass captured bytes to the strict decoder. Add leaf-swap, ancestor-swap, and hard-link tests.

- **[P1.7]** [cg-testing] `.github/workflows/tests.yml:337` -- Python 3.8 evidence omits the dispatcher and module validator.
  **Why**: The compatibility job runs selected files but does not execute dispatcher and validator surfaces. The completeness assertion searches unrelated workflow text and can remain green.
  **Fix**: Run dispatcher, module-registry, and validator checks in the Python 3.8 job and validate that job's exact command block.

## P2 -- IMPORTANT

- **[P2.1]** [cg-code-quality] `.github/skills/cg-skill-management/SKILL.md:3` -- Public registration conflicts with private skill metadata.
  **Why**: The module registry and `/cg-skill` expose the capability publicly, while the canonical skill still says it is private and unregistered.
  **Fix**: Update the canonical description and body for the released command, then regenerate all platform targets.

## Verification Evidence

- Code-quality focused tests: 164 passed.
- Testing focused suite: 159 passed.
- Exact-tree CI run `33567608454` passed at `ca0891b` on Windows, macOS, Ubuntu, and its configured Python 3.8 surface.
- No Pester command was run during review.
- Generated view bodies were not read.
- P2/P3 findings within explicit prior fixed scope were suppressed according to verification policy.
