---
date: 2026-07-31
title: "Advisory inheritance audits need explicit keys and cross-platform legacy cleanup"
category: "testing-patterns"
language: "both"
tags: [model-inheritance, advisory-validation, generated-targets, legacy-cleanup, cross-platform]
root-cause: "The model-policy migration treated parsed null values as absent, validated only well-formed advisory bundles, and removed old install ownership without migrating existing consumer manifests."
severity: "P1"
plan: ".cg-docs/plans/2026-07-30-user-selected-model-advisory-routing.md"
reviewed-in: ".cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review-3.md"
related: [
  ".cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md",
  ".cg-docs/solutions/testing-patterns/2026-05-13-cross-script-parity-tests-ps1-sh.md",
  ".cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md",
  ".cg-docs/solutions/testing-patterns/2026-06-09-token-optimization-release-validation.md"
]
---

# Advisory Inheritance Audits Need Explicit Keys and Cross-Platform Legacy Cleanup

## Problem

The user-selected model migration removed execution assignments and replaced them
with advisory-only stage guidance. The initial migration passed its focused happy
path tests, but a verification pass found several gaps:

- `model: null` was treated as if the `model` key were absent.
- An empty or malformed advisory JSON bundle could pass validation or raise while
  the validator was inspecting it.
- Optional local advisory settings did not reliably warn and fall back.
- Generated native commands copied Copilot-only picker wording.
- Existing consumer projects could retain old model-mapping files in managed-file
  manifests after the mapping outputs were removed from the source tree.
- New advisory and audit tests were not part of CI or the release preflight.

## Root Cause

The migration changed the policy contract across Python validation, Markdown
prompts, generated targets, PowerShell/Bash installers, manifests, and tests, but
the first pass checked each layer mostly in isolation. Parsed values were used as
proxies for key presence, malformed optional data was not treated as a separate
fallback state, and removed install units had no upgrade migration path.

## Solution

Distinguish an omitted frontmatter key from an explicit null value:

```python
model_key_present = "model" in fm
model = fm.get("model")
declaration["execution_metadata"] = model_key_present
```

Validate advisory payload shape before accessing nested fields. In particular,
require the top-level schema fields, validate effort labels as a list of strings,
require source `observedDate`, `availabilityStatus`, and `verificationStatus`,
and reject a non-object source without calling `.get()` on it.

Treat local advisory configuration as optional input: parse its bounded block
defensively, validate effort and known example references, warn and fall back for
ordinary malformed preferences, and retain a hard failure for executable keys
such as `model` or `modelMapping`.

Keep canonical prompt prose platform-neutral, regenerate all native targets, and
scan every generated command and agent/subagent format for executable model
metadata. Add the advisory, audit, and documentation tests to both CI and the
release preflight.

For removed consumer install units, migrate old ownership records in both
`link.sh` and `link.ps1`:

```text
if current_checksum == manifest_checksum:
    remove the unchanged legacy file
else:
    preserve the user-modified file
drop the legacy path from the managed-files manifest in either case
```

The migration is protected by Bash/PowerShell parity assertions and fixture tests
for both unchanged deletion and modified-file preservation.

## Prevention

- Treat frontmatter key presence, not only parsed value, as the executable metadata invariant.
- Test malformed, empty, null, wrong-type, unknown-reference, and happy-path advisory inputs.
- Keep canonical prompt sources platform-neutral when generated targets reuse the body verbatim.
- Whenever an install unit is removed, add checksum-guarded cleanup for old manifests and test upgrade behavior on both supported script implementations.
- Scan all generated executable formats, not one representative command or agent.
- Register new Python validation tests in CI and release gates at the same time they are added locally.
- Keep runtime model inheritance and availability explicitly unverified unless observed on the target platform.
- Rerun the committed-`HEAD` drift and release gates after the intended changes are committed; a dirty-worktree success is not release evidence.

## Related

- [Inherited model-picker prompts need explicit audit equivalence](2026-06-15-inherited-model-picker-drift-equivalence.md)
- [Cross-script parity tests](2026-05-13-cross-script-parity-tests-ps1-sh.md)
- [Cross-file state contracts](2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md)
- [Token optimization release validation](2026-06-09-token-optimization-release-validation.md)
