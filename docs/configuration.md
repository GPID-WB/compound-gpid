# Project Configuration

This document describes the strict `compound-gpid.local.md` schema and the
resolved per-project active manifest. It applies to Compound GPID projects that
use the versioned module registry and manifest-driven skill loading.

## Strict Configuration Schema

`compound-gpid.local.md` must contain a UTF-8 (no BOM) frontmatter block at the
top of the file, using the restricted grammar below.

### Allowed forms

| Form | Example | Notes |
| --- | --- | --- |
| Quoted scalar | `language: "both"` | ASCII printable values only |
| Simple bare scalar | `project-type: tool` | letters, digits, `.` `_` `/` `+` `-` |
| Inline flow list | `suites: [cg, cr]` | quoted or ASCII identifier values only |
| Trailing comment | `suites: [cg]  # technical` | allowed outside quotes |

### Recognized keys

| Key | Type | Meaning |
| --- | --- | --- |
| `language` | scalar | `both`, `r`, `python`, `stata`, `powershell`; derives language capability packs |
| `project-type` | scalar | project classification (informational) |
| `review-depth` | scalar | `light`, `standard`, `thorough` |
| `r-syntax` | scalar | `data.table-collapse` or `tidyverse` R dialect |
| `suites` | inline list | `cg`, `cr`; only a genuinely absent field defaults to `[cg]` |
| `capabilities` | inline list | additive explicit capabilities (e.g. `python`); never subtracts the derived baseline |
| `created` | scalar | ISO date |
| `cg-schema-version` | scalar | legacy schema marker |
| `config-schema-version` | scalar | strict-schema marker written by migration (`"2"`) |

### Rejected forms (fail closed with line/field remediation)

- UTF-8 BOM, tab characters, non-ASCII keys or control characters.
- Duplicate keys, duplicate `suites`/`capabilities` values.
- Anchors (`&`), aliases (`*`), tags (`!`), block scalars (`|`, `>`).
- Nested mappings/sequences, indented block sequences, inline nested values.
- Empty, scalar, or malformed `suites:` values; unrecognized keys.
- A `config-schema-version` value other than the supported version `2` is an
  explicit migration error rather than an implicit fallback.

The strict parser (`scripts/parsing_utils.py::parse_strict_config`) is the only
parser used for resolver and migration inputs.

## Migration

`python scripts/cg_migrate_config.py [--check]` non-destructively adds
`suites: [cg]` to a config whose `suites:` field is genuinely absent (the only
documented absent-field legacy default) and writes a `config-schema-version`
marker. Malformed or unknown inputs fail closed; re-running is a no-op.

## Active Project Manifest

`cg-project-manifest` resolves the strict config plus the versioned module
registry into one committed, reviewable artifact at
`.compound-gpid/active-manifest.json`:

- `header` / `schemaVersion`: artifact identity.
- `selection.configDigest` / `selection.registryDigest`: immutable input hashes.
- `selection.configSchemaVersion` / `selection.registrySchemaVersion`: schema
  version markers of the config and registry inputs.
- `selection.suites`, `selection.capabilities` (explicit), and
  `selection.derivedCapabilities` (config-selector derived, sorted).
- `selection.moduleClosure`: the resolved loadable module set
  (kernel + suite closure + derived/explicit capabilities).
- `selection.platforms`: selected platform ids in canonical order
  (`copilot`, `claude-code`, `codex`, `opencode`, `kilo` by default).
- `selection.sourceRevision` and `selection.desiredPlanDigest`: recorded source
  stamp and a deterministic digest of the desired projection plan.
- `certifiedKiloLaunchRequired`: records the mandated `cg-kilo` certified launch
  path for a combined Kilo+Codex configuration (set by link/update preflight).
- `platformEligibility`: per-capability supported-platform eligibility.
- `catalogRecords`: compact id/purpose/capability/availability rows.

### Staleness

A committed manifest is stale when any immutable selection field
(config digest, registry digest/schema, source revision, module closure,
platform set, or desired-plan digest) differs from a fresh resolution.
Mismatched fields are reported explicitly.

### Mutable projection state

- `.compound-gpid/projection-ownership.json` — per-file expected/current
  checksums, preservation state, and stale-deletion authorization. Drift in
  this file never marks selection stale; a user-modified projected file is a
  reconciliation outcome.
- `.compound-gpid/projection-transaction.json` — durable per-root publication
  journal used to recover interrupted projection publication.

Both are ignored by git; only `active-manifest.json` is committed.

## Usage

```text
python scripts/cg_project_manifest.py --validate
python scripts/cg_project_manifest.py --output .compound-gpid/active-manifest.json
python scripts/cg_project_manifest.py --platforms copilot,kilo --output ...
python scripts/cg_project_manifest.py --check-stale .compound-gpid/active-manifest.json
python scripts/cg_migrate_config.py --check
```
