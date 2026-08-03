---
date: 2026-08-03
depth: full
mode: auto
plan: ".cg-docs/plans/2026-08-03-generic-markdown-reference-publishing-core-v2.md"
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
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
---

# Review: Generic Markdown and Reference Publishing Core (V2)

## Summary

**Review mode**: full, auto-routed for publishing, provenance schema,
installer, concurrency, and secure-filesystem risk.

**Result**: implementation, V1-V9 evidence gates, focused re-verification, and
branch-ancestry reconciliation completed successfully. All review findings are
fixed. Duplicate agent findings are consolidated below.

## P0 - Blocking

### P0.1 - Ownership authorization is not bound to final publication

- **Files**: `scripts/artifact_views/generic_cli.py`,
  `scripts/artifact_views/cli.py`, `scripts/artifact_views/writer.py`,
  `scripts/secure_fs.py`, `scripts/cg_generate_targets.py`
- **Finding**: Provenance or generated-target ownership is authorized before the
  secure writer starts. The writer then snapshots and replaces whatever file
  exists at its own boundary, without receiving the authorized absence,
  identity, or digest.
- **Impact**: A concurrent unowned file inserted between authorization and
  writer entry can be quarantined, overwritten, and deleted. This violates the
  core non-clobbering ownership contract and can cause arbitrary data loss.
- **Required fix**: Carry expected absence or an exact authorized digest/identity
  into the pinned transaction. Validate the quarantined handle before
  publication; restore or preserve it without replacement on mismatch. Add
  route-level and later-generated-entry race tests.

### P0.2 - Case-folded paths equate distinct owners on case-sensitive hosts

- **Files**: `scripts/artifact_views/publishing.py`,
  `scripts/artifact_views/paths.py`
- **Finding**: Source and output owner identities are compared with unconditional
  `casefold()`.
- **Impact**: Distinct POSIX sources such as `docs/Guide.md` and
  `docs/guide.md` can take over the same explicit destination. Unicode
  case-fold collisions have the same risk.
- **Required fix**: Compare exact canonical owner identities. Use a separate
  normalized case-collision key only to reject portable collisions; never use
  that key as proof that two owners are identical.

### P0.3 - The source digest does not prove exact canonical bytes

- **Files**: `scripts/artifact_views/provenance.py`,
  `scripts/artifact_views/parser.py`, `scripts/artifact_views/renderer.py`
- **Finding**: `sourceSha256` removes a BOM and normalizes CRLF/lone CR before
  hashing, while parsing and visible raw-source rendering can consume original
  bytes.
- **Impact**: Distinct canonical byte streams can share a provenance digest,
  and some newline/BOM changes can remain `current` despite exact-source
  freshness requirements.
- **Required fix**: Record an authoritative SHA-256 of the exact pinned bytes.
  If semantic normalization remains useful, record it as a separately named
  digest and apply one representation consistently to parsing/rendering.

## P1 - Critical

### P1.1 - Publication and rollback lack a safe explicit commit point

- **Files**: `scripts/secure_fs.py`
- **Finding**: POSIX can delete recovery bytes before a fallible directory
  `fsync`; Windows suppresses restoration failures and can leave undisclosed
  recovery files. Windows temporary cleanup also unlinks a pathname after the
  handle closes.
- **Impact**: A reported failure can still change the destination, lose prior
  bytes, hide recovery identity, or delete a concurrent temporary-name winner.
- **Fix**: Define a commit point. Before it, remove the new publication and
  restore without replacement; after it, report successful publication plus
  any cleanup/recovery artifact. Dispose Windows temporary identity by handle.

### P1.2 - Bitmap URI identity permits alternate streams and repeated decoding

- **Files**: `scripts/artifact_views/security.py`, `scripts/secure_fs.py`
- **Finding**: Decoded image paths do not reject colons/device names/trailing
  dots or spaces, and double-encoded separators can survive the first check.
- **Impact**: NTFS alternate data streams and multiple spellings of one resource
  can bypass exact resource identity.
- **Fix**: Decode with one explicit canonical policy, reject encoded separators
  after decoding, and validate every component with the portable path rules
  before filesystem access.

### P1.3 - Bounded sources can still cause aggregate output and memory exhaustion

- **Files**: `scripts/artifact_views/security.py`,
  `scripts/artifact_views/generic_renderer.py`,
  `scripts/artifact_views/generic_cli.py`
- **Finding**: Image limits are per occurrence with no cache or cumulative
  budget. Inline rendering creates dense full-source delimiter tables and
  repeatedly scans image prefixes.
- **Impact**: A small source can repeatedly encode a 5 MiB image into output
  larger than the 32 MiB read limit, while a near-limit paragraph can consume
  hundreds of MiB or quadratic CPU.
- **Fix**: Add one render context with unique-resource caching, image-count,
  cumulative raw/encoded/output limits, and a single-pass inline tokenizer.

### P1.4 - Bitmap validation accepts corrupt prefix-only payloads

- **Files**: `scripts/artifact_views/security.py`,
  `scripts/artifact_views/tests/test_publishing_security.py`
- **Finding**: PNG, JPEG, GIF, and WebP validation checks only short signatures;
  current accepted fixtures are deliberately truncated.
- **Impact**: Publication can succeed while embedding undecodable or malformed
  images, silently breaking document content.
- **Fix**: Validate bounded complete container structure and lengths for each
  format. Replace prefix-only fixtures with minimal valid images and add
  truncated, malformed-length, and polyglot cases.

### P1.5 - Supported CI does not execute both secure publication backends

- **Files**: `.github/workflows/tests.yml`,
  `scripts/artifact_views/tests/test_writer.py`,
  `scripts/tests/test_secure_fs.py`
- **Finding**: The Windows/macOS Python job does not include publisher secure
  filesystem, CLI, or image tests. POSIX runtime races were skipped in the
  reported Windows evidence.
- **Impact**: C4 cannot be considered durable release evidence on both supported
  backends.
- **Fix**: Add focused publisher/security modules to a Windows/macOS Python
  matrix and fail if the applicable backend race tests are skipped.

### P1.6 - Automatic policy and ownership manifests use unpinned reads

- **Files**: `scripts/artifact_views/config.py`,
  `scripts/artifact_views/generic_cli.py`, `scripts/cg_generate_targets.py`
- **Finding**: `compound-gpid.local.md` and the generated ownership manifest use
  pathname check-then-read sequences.
- **Impact**: Link/identity races can change mutation policy or stale-deletion
  authority after validation.
- **Fix**: Use bounded `secure_read_bytes()` with hard-link rejection and strict
  decoding for both files; add final-component swap tests.

### P1.7 - Check-mode corrupt-output behavior is inconsistent

- **Files**: `scripts/artifact_views/generic_cli.py`,
  `scripts/artifact_views/publishing.py`
- **Finding**: Corrupt, oversized, duplicate, unknown-theme, or differently
  owned output can raise publication failure instead of producing the promised
  deterministic stale classification. Explicit-theme check also bypasses the
  normal ownership validation branch.
- **Impact**: Freshness automation differs by output defect and mode.
- **Fix**: Separate nonmutating stale classification from mutation ownership;
  still validate provenance ownership where identity is available.

### P1.8 - Upstream branch state contains an overlapping Windows EOL fix

- **Files**: `scripts/cg_generate_targets.py`,
  `scripts/tests/test_target_ownership.py`
- **Finding**: Review observed the branch behind `origin/main` with an upstream
  EOL-tolerant ownership change overlapping the new Markdown LF normalization.
- **Impact**: A careless merge can reintroduce Windows generation failures or
  discard either fix.
- **Fix**: Reconcile with current `origin/main` before merge and preserve both
  ownership repair and regression coverage.

**Closure status**: Fast-forwarded the feature branch to `origin/main` at
`09a494c`, preserved and reapplied the dirty worktree, reconciled both ownership
files, and verified `git rev-list --left-right --count HEAD...origin/main` as
`0 0`. The upstream Windows line-ending ownership repair and the generic
publisher changes are both present.

## P2 - Important

### P2.1 - Default destinations bypass portable output validation

Route mirrored defaults through the same validator as explicit output and test
reserved names, colons, trailing dots/spaces, and case collisions.

### P2.2 - Relative links are not rebased after publication

Rebase source-relative links from the Markdown source directory to the derived
output directory while preserving fragments and allowed absolute schemes.

### P2.3 - Recovery/help/exit-code contracts are incomplete

Preserve `--output` and explicit theme in recovery, make writer messages
command-neutral, add complete CLI help, and align documented exit-code classes
with behavior.

### P2.4 - Runtime launcher evidence is mostly static

Execute repository-local and installed bash/CMD layouts with fallback
interpreters, spaced arguments, render/check operations, and child failure
status.

### P2.5 - Theme and writer types are advisory rather than authoritative

Bind theme presentation assets to `ThemeContract`, return typed destinations
from path resolvers, and require typed destinations at the writer boundary.

### P2.6 - Shared renderer/theme code retains duplicate dead authorities

Remove unused design/CSS constants and make strict rendering use the shared
source-owner loop to prevent future drift.

## Review Evidence

- Full Python: 1336 passed, 38 platform skips, 5 subtests passed.
- Documentation site: 33 navigable pages, 6 groups, complete skill catalog.
- Full Pester: 2343/2343 passed; `filteredFiles: null`.
- Workspace diagnostics: clear.
- Canonical Plan view: current.

These closure gates verify the exercised behavior and support the fixed statuses
above.
