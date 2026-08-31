---
date: 2026-08-28
depth: full
type: standard
plan: .cg-docs/plans/2026-08-28-compound-gpid-rd-command.md
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P0.4: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: skipped
  P2.8: fixed
  P3.1: fixed
  P3.2: skipped
---

# Review Report: Compound GPID R&D Command

**Review mode**: full (auto-routed security-risk)
**Files reviewed**: canonical prompt, registry utility, tests, audit allowlist,
current documentation, generated command trees and ownership manifests
**Findings**: 22 (P0: 4, P1: 8, P2: 8, P3: 2)

## P0 - BLOCKING

- **[P0.1]** [cg-adversarial, cg-architecture, cg-data-quality,
  cg-learnings-researcher] `.github/prompts/cg-compound-gpid-rd.prompt.md:250`
  and `scripts/cg_compound_gpid_rd_registry.py:388` - Remove authorization is
  not bound to the URL shown for confirmation.
  **Why**: A concurrent actor can replace an entry with the same ID and a new
  URL after confirmation. The utility removes the replacement, and the prompt
  detects the mismatch only after deletion.
  **Fix**: Pass an expected URL or state token to the utility and reject any
  mismatch before transformation and publication. Add a race test that proves
  the concurrent winner remains unchanged.

- **[P0.2]** [cg-data-quality, cg-adversarial]
  `scripts/cg_compound_gpid_rd_registry.py:333` - Strict JSON parsing does not
  preserve all unknown numeric fields exactly.
  **Why**: Decimal JSON numbers are decoded as binary floats and can be rounded
  when the complete registry is serialized. Exponent overflow can become
  infinity without passing through `parse_constant`.
  **Fix**: Preserve numeric tokens exactly or reject values that cannot make an
  exact finite round trip before any write. Add precision and exponent-overflow
  byte-preservation tests.

- **[P0.3]** [cg-adversarial, cg-code-quality, cg-reproducibility]
  `scripts/cg_compound_gpid_rd_registry.py:505` - Success response validation
  occurs after registry publication.
  **Why**: A removed entry containing an unserializable unknown value, a stdout
  failure, or a post-commit warning can make the command report failure after
  the mutation committed.
  **Fix**: Build and validate the complete bounded success response before the
  secure write. Define and test post-commit warning/output behavior so a
  committed mutation cannot be reported as a no-write failure.

- **[P0.4]** [cg-architecture, cg-learnings-researcher]
  `.github/prompts/cg-compound-gpid-rd.prompt.md:489` - Full and delta review
  metadata updates replace the registry without expected-state publication.
  **Why**: A concurrent add, remove, or review update can be overwritten by the
  model-orchestrated whole-file replacement.
  **Fix**: Route review-state updates through deterministic validation and an
  expected-state secure writer. This expands the approved two-subcommand
  utility boundary and requires an explicit plan/deviation decision.

## P1 - CRITICAL

- **[P1.1]** [cg-adversarial]
  `scripts/cg_compound_gpid_rd_registry.py:505` - Rendered output can exceed
  `MAX_REGISTRY_BYTES` and create a registry that no later command can read.
  **Fix**: Reject oversized rendered bytes before secure publication and test
  add/remove at the output boundary.

- **[P1.2]** [cg-testing, cg-adversarial, cg-code-quality]
  `scripts/cg_compound_gpid_rd_registry.py:333` - Large integers and deeply
  nested JSON can raise uncaught `ValueError` or `RecursionError` with a raw
  traceback.
  **Fix**: Enforce a nesting limit and convert parser, copy, and serializer
  failures to controlled one-line exit-1 errors with no-change tests.

- **[P1.3]** [cg-data-quality, cg-architecture]
  `.github/prompts/cg-compound-gpid-rd.prompt.md:79` - Review-mode registry
  validation is weaker than mutation-mode validation.
  **Why**: Noncanonical or mismatched URLs and invalid typed/date fields can
  pass the prompt checks and associate release metadata with the wrong entry.
  **Fix**: Use one deterministic validator for all four modes.

- **[P1.4]** [cg-data-quality]
  `scripts/cg_compound_gpid_rd_registry.py:630` - Review-state invariants allow
  empty release strings, dates with null baselines, and future review dates.
  **Fix**: Define and test consistent baseline/date invariants, then apply them
  in the shared validator.

- **[P1.5]** [cg-data-quality]
  `scripts/cg_compound_gpid_rd_registry.py:77` - Raw ASCII controls and
  whitespace can be stripped by `urlsplit`, with behavior that varies by Python
  version.
  **Fix**: Reject controls, whitespace, and non-printable characters before URL
  parsing; add Python-version-independent tests.

- **[P1.6]** [cg-reproducibility]
  `scripts/cg_pr_preflight.py:40` - The authoritative native CI test list omits
  `test_cg_compound_gpid_rd_registry.py`.
  **Fix**: Add the utility suite and update the preflight ownership assertion.

- **[P1.7]** [cg-reproducibility]
  `.github/prompts/cg-compound-gpid-rd.prompt.md:228` - Relative utility paths
  depend on the terminal working directory.
  **Fix**: Use a quoted root-qualified utility path or explicitly execute from
  the repository root.

- **[P1.8]** [cg-version-control] repository branch/base - The branch has no
  upstream, equals `origin/dev`, and is 141 commits ahead of `origin/main`.
  **Fix**: Use `dev` as the PR base unless the work is intentionally moved to
  `main`; inspect the full base-to-HEAD range before PR creation.

## P2 - IMPORTANT

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1:3132` - Several security
  assertions search the full prompt and can pass from unrelated sections.
  **Fix**: Scope launcher/add/remove/review assertions to bounded sections and
  assert exact allowlists, length bounds, and ordering independently.

- **[P2.2]** [cg-testing]
  `scripts/tests/test_cg_compound_gpid_rd_registry.py:1430` - Mocked writer
  failures do not test real rollback after the final boundary.
  **Fix**: Raise through `_before_secure_replace` with the real writer and assert
  exact restoration and no leaked recovery artifacts.

- **[P2.3]** [cg-testing]
  `scripts/tests/test_cg_compound_gpid_rd_registry.py:116` - The CLI is tested
  only in-process.
  **Fix**: Add subprocess tests for exit 0, 1, and 2 plus exact stream and byte
  preservation contracts.

- **[P2.4]** [cg-testing]
  `scripts/tests/test_cg_generate_targets.py:339` - Generated bodies are
  compared with one another but not directly with the canonical prompt body.
  **Fix**: Strip canonical frontmatter and expected adapter suffixes, then
  compare all generated bodies byte-for-byte with canonical content.

- **[P2.5]** [cg-documentation]
  `.github/prompts/cg-compound-gpid-rd.prompt.md:66` and `docs/reference.md:452`
  - The schema note still says two files, and documentation incorrectly implies
  removed entry metadata remains durable.
  **Fix**: Name all three coupled schema values. State that review files remain,
  while entry-local release/date metadata is removed with the entry.

- **[P2.6]** [cg-documentation]
  `scripts/cg_compound_gpid_rd_registry.py:141` - A public-function doctest
  example has invalid continuation syntax.
  **Fix**: Use a parenthesized multiline call and run the module doctests.

- **[P2.7]** [cg-performance, cg-architecture]
  `scripts/cg_compound_gpid_rd_registry.py:55` - The 697-line utility combines
  domain, validation, storage, rendering, and CLI responsibilities.
  **Fix**: After correctness fixes, consider a thin entry point plus focused
  domain and storage modules without changing the external command contract.

- **[P2.8]** [cg-performance]
  `.github/prompts/cg-compound-gpid-rd.prompt.md:53` - Review modes can load a
  registry of up to about 1 MiB directly into model context before bounded
  utility validation.
  **Fix**: Add a bounded deterministic projection or explicit model-context size
  guard before prompt-level registry loading.

## P3 - MINOR

- **[P3.1]** [cg-code-quality, cg-documentation]
  `.github/prompts/cg-compound-gpid-rd.prompt.md:252` - The remove instruction
  contains the malformed phrase `a A missing ID`.
  **Fix**: Replace it with one direct no-write rule and regenerate targets.

- **[P3.2]** [cg-code-quality]
  `scripts/cg_compound_gpid_rd_registry.py` - Several lines exceed 88
  characters and the module relies heavily on `.format()`.
  **Fix**: Apply Python 3.8-compatible project formatting after behavioral
  findings are resolved.

## Passed Areas

- Planned pytest, Pester, docs, generator, audit, compile, and native preflight
  gates passed before the adversarial review.
- Tracked registry bytes and historical tracked review outputs were unchanged.
- Generated target ownership and current working-tree parity passed.

## Review Handoff

P0.1 through P0.4 were independently verified as fixed on 2026-08-31. The
registry utility now binds removal and review updates to accepted identity,
metadata, scope, and source-state digests; it reconciles ambiguous post-dispatch
outcomes without retry; and it rejects unsafe release values before shell use.
Generated adapters, focused tests, full Pester, and the native preflight passed.
P1.8 was resolved by pull request #146, created with `dev` as its explicit base.
