---
date: 2026-08-06
title: "Kilo agent/skill parsing failures — JSON Schema validation bug + YAML/encoding issues"
category: "bugs"
type: "bug"
language: "both"
tags: [kilo, agents, skills, yaml, frontmatter, parsing, json-schema, config-validation, encoding, mojibake]
root-cause: "Kilo config_validation JSON Schema for agent markdown files fails with 'No context found for instance' on all files regardless of content; compounded by YAML quoting and encoding issues in project files"
severity: "P2"
test-written: "no"
fix-confirmed: "partial"
red-phase-confirmed: "yes"
expected-behavior-source: "package-convention"
test-gap: "missing-test"
---

# Kilo Agent/Skill Parsing Failures — JSON Schema Validation Bug

## Symptom

Both VS Code and Positron report parsing failures for all agent and skill files:
- **VS Code** (v7.4.20, Windows): "Failed to parse agent errors for" all 17 agent
  files in `.kilo/agents/` — listed uniformly, not individually
- **Positron** (macOS): "Failed to parse skill /.../cg-skill-fix-triage-migrate/SKILL.md
  with UnknownError"

Errors persist across reloads, sessions, and machines. The uniform listing of ALL
17 files (rather than specific ones) indicates a directory-level or schema-level
failure, not individual file content issues.

## Expected Behavior Source

**Package convention** — Kilo's Custom Subagents specification
(https://kilo.ai/docs/customize/custom-subagents) defines that agent markdown files
with valid YAML frontmatter containing `description` and `mode` fields should parse
and load successfully. The filename (without `.md`) becomes the agent name — no
`name` field is required in frontmatter. Similarly, the Agent Skills specification
(https://agentskills.io/specification) requires `name` and `description` in
SKILL.md frontmatter.

## Root Cause

**Two distinct root causes were identified, one upstream and one in project files:**

### Primary: Kilo config_validation JSON Schema bug (upstream)

Kilo's internal `config_validation` system fails on ALL agent markdown files with
the error "Failed to parse frontmatter: No context found for instance" — regardless
of file content. This was confirmed by creating a minimal, perfectly valid agent
file:

```yaml
---
description: "Test agent"
mode: subagent
---

Test prompt.
```

This minimal file triggers the same error, proving the issue is NOT about YAML
syntax, quoting, encoding, or missing fields. The error originates from Kilo's
JSON Schema validator (`config_validation`) which cannot resolve its schema context
for agent markdown files. This is the "No context found for instance" error from
the JSON Schema `$ref` resolution system.

This error manifests as "Failed to parse agent" in the VS Code UI and "UnknownError"
in Positron. The error message is misleading — it reports a parse failure when the
actual issue is schema validation.

**Upstream reference**: [Kilo Issue #12076](https://github.com/Kilo-Org/kilocode/issues/12076)
documents this exact pattern — agent frontmatter parse failures are silently caught,
the agent is skipped, and no visible error is shown. The issue reports that ANY YAML
syntax error or schema validation failure triggers silent agent skipping.

### Secondary: YAML quoting and encoding issues in project files

Several project files had content quality issues that would cause independent
parsing failures in stricter parsers:

1. **`cg-skill-fix-triage-migrate/SKILL.md`** — unquoted `description` value containing
   `findings: tracking` (colon-space in unquoted YAML value), causing YAML to interpret
   `tracking` as a new mapping key. **This is the direct cause of the Positron
   "UnknownError" for this specific file** (independent of the schema bug).

2. **`cg-learnings-researcher.md`** — unquoted `description` value (inconsistent
   with the other 16 agent files that all use double-quoted values).

3. **Three agent files** (`cg-project-scanner.md`, `cg-release-scanner.md`,
   `cg-roadmap-view.md`) had non-ASCII em-dashes (`—`, U+2014) in frontmatter
   `description` values.

4. **Ten agent files** had mojibake-encoded characters in body content:
   - `â€"` (U+00E2 U+20AC U+201D) — mojibake for em-dash `—`
   - `â†'` (U+00E2 U+2020 U+2019) — mojibake for arrow `→`
   - `â€"` (U+00E2 U+20AC U+201C) — mojibake for en-dash `–`

   Caused by UTF-8 bytes being misinterpreted through Windows-1252 encoding and
   then re-encoded as UTF-8 (classic cross-platform editing artifact).

## Reproduction Test

No automated test was written because the parsing failure occurs in Kilo's
internal config validator, which is not directly testable from the project side.

The failure was reproduced by:
1. Creating a minimal, perfectly valid agent markdown file
2. Editing it through the Kilo extension
3. Observing the `config_validation` error: "Failed to parse frontmatter: No context
   found for instance" — identical to the error on all 17 existing agent files

This confirms the error is systematic (affects ALL agent files) rather than
content-dependent.

## Test Gap

**missing-test** — The project had no automated validation for YAML frontmatter
conformance in agent/skill files. There was no schema check, no encoding validation,
and no quoting consistency enforcement. A pre-commit hook or CI check validating
YAML frontmatter would have caught the quoting issues before they accumulated.

## Fix

### Applied fixes (defensive hardening — 12 files modified):

1. **`cg-skill-fix-triage-migrate/SKILL.md`**: Quoted the `description` value.
   Before: `description: Migration mode for /cg-fix-triage. Adds findings: tracking...`
   After: `description: "Migration mode for /cg-fix-triage. Adds findings: tracking..."`
   This directly fixes the Positron "UnknownError" for this file.

2. **`cg-learnings-researcher.md`**: Quoted the `description` value to match
   the convention of all other 16 agent files.

3. **`cg-project-scanner.md`, `cg-release-scanner.md`, `cg-roadmap-view.md`**:
   Replaced non-ASCII em-dashes (`—`) with ASCII `--` in frontmatter descriptions.

4. **10 agent files** (`cg-architecture.md`, `cg-code-quality.md`, `cg-data-quality.md`,
   `cg-documentation.md`, `cg-learnings-researcher.md`, `cg-performance.md`,
   `cg-reproducibility.md`, `cg-roadmap.md`, `cg-testing.md`, `cg-version-control.md`):
   Fixed mojibake `â€"` → `--`, `â†'` → `->`, `â€™` → `--` in body content.

### Required upstream fix (not project-side):

The "Failed to parse agent" error for all 17 agent files is caused by Kilo's
`config_validation` JSON Schema validator failing to resolve its schema context.
This is an internal Kilo bug that requires an upstream fix.

**Workarounds**:
- Check Kilo's release notes for any schema validation fixes in versions after v7.4.20
- Report the issue at https://github.com/Kilo-Org/kilocode/issues with the error
  message: "Failed to parse frontmatter: No context found for instance"
- As a temporary measure, try adding a `$schema` field to the agent frontmatter or
  checking if the global `kilo.jsonc` `permission` settings affect agent loading

**Important**: The file content fixes applied above are still valuable. Even after
the upstream schema bug is fixed, the YAML quoting and encoding issues would cause
independent failures in Positron and other strict parsers.

## Lessons Learned

1. **Validate with minimal reproducers**: When ALL files in a directory fail
   uniformly, create a minimal valid file first. If the minimal file also fails,
   the issue is systematic (infrastructure, schema, parser bug) — not content-related.
   This prevents wasted time debugging individual file content when the root cause
   is upstream.

2. **YAML quoting discipline**: All YAML frontmatter `description` values MUST be
   double-quoted, even when the content contains no special characters. This prevents
   breakage when descriptions are later edited to colons, brackets, or other
   YAML-significant characters. The `cg-skill-fix-triage-migrate/SKILL.md` failure
   was directly caused by an unquoted colon in the description value.

3. **Encoding hygiene**: Files authored across different operating systems and editors
   can accumulate mojibake from UTF-8/Windows-1252 round-trips. Use ASCII-safe
   alternatives (`--` for em-dash, `->` for arrow) in files that will be parsed by
   strict parsers, or ensure consistent UTF-8 encoding throughout the toolchain.

4. **Error message quality**: Kilo's "Failed to parse agent" error message masks the
   actual cause (JSON Schema validation failure). Upstream issue #12076 requests
   better error surfacing. When evaluating external tool errors, test with minimal
   reproducers to distinguish file issues from tool bugs.

5. **Cross-platform encoding**: The mojibake patterns (`â€"`, `â†'`, `â€™`)
   are characteristic of UTF-8/Windows-1252 round-trips during cross-platform
   editing. Teams using mixed OS environments should enforce UTF-8 encoding in
   editor configs and `.editorconfig` files.

## Related

- [Kilo Issue #12076](https://github.com/Kilo-Org/kilocode/issues/12076) — Surface visible warnings when agent `.md` frontmatter fails to parse (documents the silent-skip behavior)
- [Kilo Issue #12391](https://github.com/Kilo-Org/kilocode/issues/12391) — Regression: project agents stored through external directory symlinks no longer load (different root cause but same error message pattern)
- [Kilo PR #12846](https://github.com/Kilo-Org/kilocode/pull/12846) — Fix for #12391
- **First structural fix**: `.cg-docs/solutions/bugs/2026-08-11-windows-link-kilo-copy-directory-parse-failure.md` -- made native `.kilo/*` units project-local copies. It complements this entry's YAML hardening.
- **Cross-adapter superseding diagnosis**: `.cg-docs/solutions/bugs/2026-08-20-kilo-cross-adapter-skill-autodiscovery.md` -- Kilo also auto-discovers `.agents/skills`; adapter-specific local mirrors now close the remaining Windows/macOS recurrence without changing Codex's `link-directory` strategy.
