---
date: 2026-08-28
title: "Rename repository review command and add registry management flags"
status: completed
completed-date: 2026-08-28
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-08-28-compound-gpid-rd-command.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
execution-report: ".cg-docs/work-reports/2026-08-28-compound-gpid-rd-command.md"
artifact-schema-version: 1
phases: 2
completed-phases: [1, 2]
tags: [competitive-analysis, command-design, python, powershell, generated-targets]
---

# Plan: Rename Repository Review Command and Add Registry Management Flags

## Objective

Replace the developer-only `/cg-review-repos` command with
`/cg-compound-gpid-rd`, preserve its full and delta review behavior, and add
safe `--add <URL>` and confirmed `--remove <id>` registry operations through a
small deterministic utility. Keep `.github/` canonical, regenerate every native
platform tree, and remove the old live command without changing historical
artifacts or the registry schema.

## Context

The current canonical prompt is
`.github/prompts/cg-review-repos.prompt.md`. It validates and updates
`.cg-docs/competitive-reviews/repos.json`, performs full or delta GitHub
research, and produces feature cards. The registry has a fixed v1 schema and
currently contains three repositories.

The existing prompt can update review metadata, but maintainers must edit the
JSON file manually to add or remove repositories. The new design keeps research
and feature analysis in the prompt. A standard-library Python utility performs
only deterministic registry validation and mutation. The prompt remains the
user-facing orchestrator and retains the Compound GPID development-repository
guardrail.

Native command files in `.claude/`, `.agents/`, `.opencode/`, and `.kilo/` are
generated from `.github/` by `scripts/cg_generate_targets.py`. The canonical
prompt must be renamed first; generated files and ownership manifests must then
be refreshed through the generator rather than edited independently.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Rename the live command and canonical prompt to `cg-compound-gpid-rd`; remove the old command with no alias. | Brainstorm: Rename |
| R2 | Keep the command developer-only and focused on public GitHub repository research for Compound GPID. | Brainstorm: Purpose and Users |
| R3 | Support four mutually exclusive modes: delta, `--full`, `--add <URL>`, and `--remove <id>`; invalid, missing, duplicate, or conflicting flags must stop. | Brainstorm: Command Modes |
| R4 | Normalize and validate a public `https://github.com/<owner>/<repo>` URL, verify accessibility, derive registry fields, reject duplicates, and add null review state without starting a review. | Brainstorm: Add Behavior |
| R5 | Resolve an exact ID, show the matching repo, require explicit confirmation, remove only that entry, and preserve all review history. | Brainstorm: Remove Behavior |
| R6 | Use a narrow deterministic utility for registry parsing, schema checks, derivation, duplicate checks, confirmation validation, and expected-state secure JSON writes while preserving unknown fields and concurrent winners. | Brainstorm: Deterministic Registry Utility |
| R7 | Preserve existing delta and full review behavior; allow add and removal of the last entry, but stop review modes on an empty registry with `--add` guidance. | Brainstorm: Requirements |
| R8 | Update current command docs, developer notes, audit allowlists, and command inventories to the new name and four-mode contract. | Brainstorm: Tests and Documentation |
| R9 | Regenerate all native platform trees from `.github/`; new command files must exist and unchanged old generated command files must be removed. | Brainstorm: Rename |
| R10 | Add pytest and Pester coverage for normal, boundary, and failure paths; remove the fixed three-entry registry count sentinel. | Brainstorm: Tests and Documentation |
| R11 | Keep historical brainstorms, plans, reviews, solutions, token reports, and competitive-review outputs unchanged. | Brainstorm: Rename and Out of Scope |
| R12 | Add no external runtime dependency and do not migrate `compound-gpid-competitive-reviews-v1`. | Brainstorm: Out of Scope |

## Research Decisions

### Utility Command Contract

Create `scripts/cg_compound_gpid_rd_registry.py` with two subcommands and a
non-mutating add preflight:

```text
<pythonCommand> scripts/cg_compound_gpid_rd_registry.py --root <repo-root> add --url "<github-url>" --check-only
<pythonCommand> scripts/cg_compound_gpid_rd_registry.py --root <repo-root> add --url "<github-url>"
<pythonCommand> scripts/cg_compound_gpid_rd_registry.py --root <repo-root> remove --id "<id>" --confirm-id "<id>"
```

- `--root` defaults to the current directory and fixes the registry location at
  `.cg-docs/competitive-reviews/repos.json` below that root.
- Exit `0` means the requested mutation completed.
- Exit `1` means registry, validation, domain, or write failure.
- `argparse` exit `2` means invalid CLI syntax.
- The utility requires Python 3.8+. It must perform the standard top-level
  `sys.version_info >= (3, 8)` guard before project-local imports. Prompt launcher
  discovery accepts only candidates whose probe confirms Python 3.8 or newer.
- Success writes exactly `{"action":"add|remove","changed":<bool>,"repo":{...}}`
  as compact JSON on stdout. Check-only add returns `changed: false`; mutating add
  and remove return `changed: true`.
- Errors go to stderr without a Python traceback for expected failures.
- The prompt treats every nonzero exit as a hard stop and does not infer success
  from partial output.
- `add --check-only` validates the current registry, normalizes the URL, detects
  duplicates, derives the proposed entry, and returns it without writing. The
  prompt fetches only the returned normalized URL, then invokes mutating add,
  which re-reads and revalidates all current state.

The utility does not fetch GitHub content. After check-only succeeds and before
mutating add dispatch, the prompt uses its web-fetching tool to confirm that the
normalized public repository page is accessible and is not a 404, deleted, or
private-repository response. The existing untrusted-content guard applies; this
check extracts accessibility only and must not follow instructions from the
page.

### URL and Field Derivation

- Parse with `urllib.parse.urlsplit` and require `https`, exact host
  `github.com`, no credentials or port, no query or fragment, and exactly two
  non-empty path segments.
- Accept one trailing slash and one `.git` suffix, then store
  `https://github.com/<owner>/<repo>` and derive `<url>/releases`.
- Owner names must be 1-39 ASCII alphanumeric or hyphen characters, start and
  end with an alphanumeric character, and contain no consecutive hyphens.
  Repository names must be 1-100 ASCII letters, digits, `.`, `_`, or `-`, and
  must not consist only of dots. Remove one trailing slash and then one terminal
  `.git` before validating the repository segment.
- Compare normalized URLs case-insensitively for duplicate detection.
- Derive the ID from the lower-case repository name by replacing non-alphanumeric
  runs with hyphens, then strip leading and trailing hyphens. If the repository
  slug is empty, use `<owner-slug>-repo` as the base. On a collision with a
  different URL, use an owner-qualified slug. When a candidate must be shortened,
  reserve nine characters for `-` plus the first eight hexadecimal characters of
  SHA-256 over the case-folded normalized URL. Stop if the final candidate is
  still not unique or valid.
- Split short-name tokens on maximal non-alphanumeric runs and discard empty
  tokens. Derive `shortName` from upper-case token initials when multiple tokens
  remain; otherwise use the repository's first ten alphanumeric characters.
  If no repository token remains, use the first ten alphanumeric owner
  characters.
  Truncate the initial base to ten characters before collision handling. Compare
  short names case-insensitively. On collision, append the smallest suffix from
  `2` through `99`, truncating the base again to keep ten characters. Stop if no
  unique value remains.
- New entries contain `id`, `url`, `releasesUrl`, `shortName`, and
  `lastReviewedRelease: null`; omit `lastReviewDate` until a review succeeds.

### Mutation and Preservation

- Decode UTF-8 strictly. Parse JSON with an `object_pairs_hook` that rejects
  duplicate keys at every object level and a `parse_constant` handler that
  rejects `NaN`, `Infinity`, and `-Infinity`. Serialize with `allow_nan=False`.
- Define `EXPECTED_SCHEMA_VERSION = "compound-gpid-competitive-reviews-v1"`.
  Validate the schema version, root object, `repos` array, required fields,
  field types, ID and short-name format and uniqueness, GitHub URL forms, and
  existing date formats before mutation.
- Preserve root field order, root unknown fields, unknown fields on all existing
  entries, and the order of unchanged entries.
- For add, append the new entry. For remove, require `--confirm-id` to exactly
  equal the case-sensitive `--id`, then remove exactly one matching entry.
- Serialize the complete validated object as UTF-8, two-space-indented JSON with
  a final newline.
- Read the root-relative registry with `secure_fs.secure_read_bytes`,
  `reject_hardlinks=True`, and `max_bytes=MAX_REGISTRY_BYTES`, where
  `MAX_REGISTRY_BYTES = 1_048_576`. Reject a larger file before parsing with
  exit 1 and an actionable size error. Build
  `ExpectedFileState.from_bytes(source_bytes)` and publish with
  `secure_fs.secure_write_bytes(..., expected_state=state)`. Expose only a test
  hook for the final `before_replace` boundary. A changed destination, unsafe
  link, parent-identity change, or concurrent winner must raise a controlled
  error, preserve the winner's bytes, and exit 1.
- Render and validate the complete output in memory before calling the writer.
  Any expected validation or domain failure must leave source bytes unchanged.

## Phase 1: Deterministic Registry Utility

### 1. Add Red-Phase Registry Utility Tests

- **Requirements**: R4, R5, R6, R7, R10, R12
- **Files**: `scripts/tests/test_cg_compound_gpid_rd_registry.py` (create)
- **Details**:
  - Add `tmp_path` fixtures for valid, empty, malformed, and unknown-field v1
    registries. Do not mutate the tracked project registry.
  - Test URL normalization for canonical URLs, trailing slash, and `.git`.
  - Parametrize rejection of HTTP, non-GitHub hosts, credentials, ports, query,
    fragment, subpaths, missing owner/repo, invalid names, and overlong values.
  - Test deterministic ID and short-name derivation, owner-qualified collisions,
    hash shortening, numeric short-name suffixes, duplicate normalized URLs, and
    collision exhaustion. Include `.github`, `-repo`, `_repo`, and `__` to verify
    slug stripping and owner fallback.
  - Test add to a non-empty and empty registry, null review state, final newline,
    and preservation of unknown root and entry fields.
  - Test remove success, exact case-sensitive ID matching, missing ID, mismatched
    confirmation token, removal of the final entry, and preserved history paths.
  - Test malformed JSON, wrong schema, missing fields, wrong types, duplicate IDs
    or short names, invalid existing URLs/dates, missing files, invalid UTF-8,
    duplicate root and entry keys, non-finite values, read/write `OSError`, and
    simulated secure-writer failure.
  - Test `--check-only` proposed output, duplicate detection before network work,
    and byte-for-byte no-change.
  - Test expected-state races with `before_replace`, symlink and hard-link
    rejection, parent-path changes, and preservation of concurrent winner bytes.
  - Test registry size at one byte below, exactly at, and one byte above
    `MAX_REGISTRY_BYTES`; the over-limit case must fail before parsing and preserve
    the original bytes.
  - For every rejected operation, assert the registry bytes are unchanged.
  - Test `main()` return codes and exact nested machine-readable success output
    with `capsys`. On failure, assert empty stdout, actionable stderr, no
    `Traceback`, and exit 1.
- **Test Scenarios**: normal add/remove; normalization and collision boundaries;
  malformed input, rejected confirmation, and write failure.
- **Tests**: `<pythonCommand> -m pytest scripts/tests/test_cg_compound_gpid_rd_registry.py -q`
- **Acceptance criteria**: Tests define the complete utility contract and fail
  only because the implementation does not yet exist.

### 2. Implement the Narrow Registry Utility

- **Requirements**: R4, R5, R6, R7, R12
- **Files**: `scripts/cg_compound_gpid_rd_registry.py` (create)
- **Details**:
  - Implement typed functions for registry loading and validation, GitHub URL
    normalization, ID derivation, short-name derivation, add/remove transforms,
    JSON rendering, and CLI dispatch.
  - Use only Python standard-library modules and the existing project-local
    `secure_fs` API.
  - Add the Python 3.8 top-level version guard before importing `secure_fs`.
  - Add a module docstring and Google-style docstrings with examples for every
    public function. Keep validation errors explicit and domain-specific.
  - Catch expected `OSError`, `UnicodeDecodeError`, `json.JSONDecodeError`, and
    validation exceptions at `main()`; return the documented code and suppress
    raw tracebacks for expected user errors.
  - Emit the exact nested machine-readable JSON shape only on success. Do not
    emit diagnostics to stdout and do not log repository data or fetched
    content.
  - Keep all mutation in pure in-memory transforms until the final secure writer
    call. Re-validate the transformed registry before serialization, bind the
    write to the bytes read through `ExpectedFileState`, and convert
    `SecureMutationError` to an actionable exit-1 error.
- **Test Scenarios**: all Step 1 tests move from red to green; direct function and
  CLI paths produce the same normalized records.
- **Tests**: `<pythonCommand> -m pytest scripts/tests/test_cg_compound_gpid_rd_registry.py -q`
- **Acceptance criteria**: All utility tests pass, no external dependency is
  introduced, the tracked registry is unchanged, and failures preserve fixture
  bytes.

## Phase 2: Prompt Contract, Live References, and Generated Parity

### 3. Rename the Canonical Prompt and Update Its Contracts

- **Requirements**: R1, R2, R3, R4, R5, R7, R12
- **Files**:
  - `.github/prompts/cg-review-repos.prompt.md` (rename/remove)
  - `.github/prompts/cg-compound-gpid-rd.prompt.md` (renamed canonical source)
  - `tests/prompt-tools.Tests.ps1`
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py` (only if an exact path expectation needs update)
  - `scripts/tests/test_cg_compound_gpid_rd_registry.py` (schema coupling contract)
- **Details**:
  - Preserve the exact frontmatter behavior, developer-repository guardrail,
    untrusted-web-content rules, feature-card format, full review, delta review,
    and review metadata update logic unless this plan explicitly changes it.
  - State that `rd` means `research-development`, while this iteration remains
    strictly limited to public GitHub repository research for Compound GPID
    maintainers.
  - Parse invocation arguments immediately after the developer guardrail and
    before any registry read, web fetch, utility call, or write.
  - Match mode flag names case-insensitively but preserve URL and ID values.
    Delta has no mode flag. Missing values, duplicate mode flags, combinations,
    extra positional values, and unknown flags stop; remove the current
    warn-and-fall-back behavior and `--full` precedence rule.
  - Resolve a valid Python launcher in `python3`, `python`, then `py` order. Each
    candidate must execute a version probe that confirms Python 3.8 or newer.
    Hard-stop if none is available or the utility file is missing. Do not require
    Python for unchanged full/delta review paths.
  - In add mode, apply only a lexical raw-argument allowlist before shell
    construction and quote the value as one argument. Run utility
    `add --check-only` first; do not duplicate normalization in prompt prose.
    Parse its JSON, fetch only the returned normalized URL to verify public
    accessibility, then run mutating add. Report the final returned URL, ID,
    short name, and next command `/cg-compound-gpid-rd --full`. Stop after the
    add summary.
  - After every utility call, require one JSON object with exactly the top-level
    keys `action`, `changed`, and `repo`, where `repo` is an object. Check-only
    requires `action == "add"`, `changed == false`, canonical string `url`, string
    `id`, string `shortName`, canonical string `releasesUrl`, and
    `lastReviewedRelease == null`. Mutating add requires the same repo fields with
    `changed == true`. Remove requires `action == "remove"`, `changed == true`,
    and a repo whose exact ID and URL match the confirmed entry. Missing, extra,
    wrongly typed, noncanonical, or mismatched fields are a hard stop.
  - In remove mode, pre-validate the ID allowlist, locate the exact entry, show
    ID and URL, then ask: `Type the exact case-sensitive ID '<id>' to remove it,
    or type 'cancel'.` Invoke the utility only when the complete response equals
    the ID exactly. Generic yes/no responses, leading or trailing whitespace,
    case variants, cancellation, missing ID, or nonzero utility exit produce no
    write. Pass the confirmed value as both `--id` and `--confirm-id`.
  - Move the non-empty-registry stop into full/delta branches so add accepts an
    empty registry and remove can create one. Empty review modes must instruct
    the maintainer to use `--add`.
  - Update all self-references and recovery messages to the new command.
  - Rename the Pester blocks and inventory entry. Assert the new prompt exists,
    the old canonical path does not, and existing guardrail, no-model, no-tools,
    feature-card, security, limits, collision, and registry-update contracts stay
    present.
  - Add independent Pester assertions for add, remove, exclusivity, hard stops,
    Python 3.8 detection, utility existence, check-only ordering, public
    accessibility, exact response-shape validation, exact-ID confirmation,
    empty-registry routing, and preserved full/delta behavior.
  - Replace the exact-three-entry sentinel with dynamic per-entry schema checks.
  - Rename the context-audit allowlist path and update any focused Python
    expectation.
  - Add a read-only pytest contract that imports `EXPECTED_SCHEMA_VERSION`, reads
    the tracked registry without mutating it, and asserts the renamed prompt and
    registry contain the same exact value.
- **Test Scenarios**: each mode routes to one path; add/remove stop before review;
  conflicting flags do not fetch or mutate; empty registry works only for
  mutations; existing full/delta rules remain present; all three schema constants
  agree.
- **Tests**:
  - `<pythonCommand> -m pytest scripts/tests/test_cg_compound_gpid_rd_registry.py scripts/tests/test_audit_context.py -q`
  - Safe execution subagent runs `. tests\Run-Tests.ps1 -File prompt-tools`, then
    reads only `passed`, `failedCount`, and `failures` from `tests/last-run.json`.
- **Acceptance criteria**: The old canonical prompt is absent, the new prompt has
  four exclusive modes, mutation paths call only the narrow utility, and review
  paths preserve prior behavior. Utility pytest and focused Pester pass before
  documentation and target generation continue.

### 4. Update Current Documentation

- **Requirements**: R1, R2, R3, R8, R10, R11
- **Files**:
  - `docs/competitive-reviews.md`
  - `docs/reference.md`
  - `docs/reference/commands.md`
  - `.vscode/settings.json`
- **Details**:
  - Document all four invocation forms, derivation and confirmation behavior,
    no automatic baseline on add, retained history on remove, and developer-only
    distribution guardrail.
  - Replace manual registry-edit instructions with `--add` and `--remove`; state
    that the v1 schema constant is coupled across the registry, renamed prompt,
    and utility `EXPECTED_SCHEMA_VERSION`.
  - Change only current docs and comments. Do not rewrite historical `.cg-docs/`
    references.
- **Test Scenarios**: all four current invocation examples, explicit scope of
  `research-development`, add/remove safety, and three-way schema maintenance
  note.
- **Tests**: Scoped current-documentation search and diff inspection.
- **Acceptance criteria**: Current docs contain only the new operational command
  name and accurately describe the implemented contract.

### 5. Regenerate Every Native Platform Tree

- **Requirements**: R1, R9, R11
- **Files**:
  - Generated changes under `.claude/`, `.agents/`, `.opencode/`, and `.kilo/`,
    including each `.compound-gpid-generated.json` ownership manifest
  - `scripts/tests/test_cg_generate_targets.py` (working-tree parity assertion)
- **Details**:
  - Resolve a valid Python launcher with the project launcher order.
  - Run `<pythonCommand> scripts/cg_generate_targets.py --all` from the repo root.
  - Let the generator create `cg-compound-gpid-rd.md`, remove each unchanged
    owned `cg-review-repos.md`, and update checksums/manifests.
  - Do not manually delete or patch generated command files. If the generator
    reports a modified stale owned file, stop and preserve it for user review.
  - Add a working-tree parity test that builds the current generation plan and
    compares every planned command output and expected ownership manifest with
    disk bytes, without reading blobs from `HEAD`.
  - Preserve the platform adapter contract: Claude and Codex receive the
    canonical body without an injected argument block; OpenCode and Kilo receive
    exactly one platform-specific `$ARGUMENTS` block. Compare command bodies only
    after removing the expected adapter block.
  - Assert all four new command paths exist and all four old command paths are
    absent in both disk outputs and ownership manifests.
- **Test Scenarios**: all targets contain the new command; no target or manifest
  retains the old owned path; canonical `.github/` remains unchanged by
  generation.
- **Tests**:
  - `<pythonCommand> -m pytest scripts/tests/test_cg_generate_targets.py -q`
  - Generator `--all` exits zero.
  - Keep `scripts/tests/test_target_drift.py` for post-commit or CI verification;
    it is not a pre-commit `/cg-work` completion gate because it compares with
    `HEAD`.
- **Acceptance criteria**: The generator working-tree parity test passes, all
  four new command files exist, all four old generated command files are absent,
  and the current working tree matches the current canonical generation plan.
  The HEAD-based drift test remains a required post-commit/CI gate.

### 6. Run Focused Verification and Stale-Reference Audit

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
- **Files**: No new production files; inspect the complete change set.
- **Details**:
  - Run the utility pytest file, audit-context pytest file, generator tests, and
    the new working-tree parity assertion. Do not run the HEAD-based target drift
    test as a pre-commit completion gate.
  - Run `prompt-tools.Tests.ps1` once through the execution-subagent and canonical
    safe runner; use `tests/last-run.json` as the result source.
  - Search `cg-review-repos` across `.github`, `docs`, `scripts`, `tests`,
    `.vscode`, `.claude`, `.agents`, `.opencode`, and `.kilo`. Permit only an
    explicit negative test that asserts the old path is absent. Any operational,
    documentation, audit, or generated-manifest reference is a failure.
  - Search the changed prompt for duplicated mode or safety summaries and ensure
    operational steps and summary rules agree.
  - Inspect `git diff --check`, `git status --short`, and the scoped diff. Confirm
    that historical `.cg-docs/` content and the tracked repo entries did not
    change during implementation tests.
  - If focused checks pass, run the repository's selected preflight for the
    changed files. Do not use raw or piped Pester output.
- **Test Scenarios**: complete happy path, no stale live references, no generated
  drift, no unplanned registry or historical artifact changes.
- **Tests**:
  - `<pythonCommand> -m pytest scripts/tests/test_cg_compound_gpid_rd_registry.py scripts/tests/test_audit_context.py scripts/tests/test_cg_generate_targets.py -q`
  - Execution-subagent safe Pester run for `prompt-tools.Tests.ps1`.
  - `git diff --check` and scoped stale-reference search.
- **Acceptance criteria**: All required checks pass; planned production and
  generated changes are present; unrelated historical artifacts and actual
  registry entries are unchanged by tests.

## Testing Strategy

- Use pytest `tmp_path` registries for every mutation, validation, and CLI
  behavior test. The single schema-coupling contract test may read the tracked
  `.cg-docs/competitive-reviews/repos.json` and renamed prompt, but it must never
  call an add, remove, or writer path.
- Test pure validation and transformation functions separately from CLI return
  codes and expected-state secure-writer integration.
- Assert byte-for-byte no-change after every invalid or rejected operation.
- Keep prompt behavior tests in `tests/prompt-tools.Tests.ps1`; use independent
  assertions for each critical token or behavior so one regex arm cannot mask
  another.
- Run Pester only through `. tests\Run-Tests.ps1 -File
  prompt-tools` in an execution subagent, then read the bounded
  `tests/last-run.json` result.
- Run generation after canonical changes, then use generator-core working-tree
  parity before commit and retain the HEAD-based drift test for post-commit/CI.
- Use a scoped text search as a final rename guard, with historical `.cg-docs/`
  content explicitly excluded.

## Documentation Checklist

- [ ] Rename the canonical prompt title, description, filename, and all internal command examples.
- [ ] Document delta, `--full`, `--add <URL>`, and `--remove <id>` in `docs/competitive-reviews.md`.
- [ ] Update developer-only command tables and registry schema notes in `docs/reference.md`.
- [ ] Update the developer-command note in `docs/reference/commands.md`.
- [ ] Update the VS Code command-discovery comment.
- [ ] State that add derives fields, writes null review state, and requires a later full review.
- [ ] State that remove requires confirmation and preserves assessment history.
- [ ] State that only public canonical GitHub HTTPS repository URLs are accepted.
- [ ] Leave historical `.cg-docs/` artifacts unchanged.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Model-driven JSON writes lose or corrupt fields | Route add/remove through a deterministic utility; validate and render the complete object before one expected-state `secure_fs` publication; test unknown-field and concurrent-winner preservation. |
| Raw URL or ID creates shell injection | Apply strict allowlists before command construction, quote each value as one argument, and validate again inside the utility. |
| Duplicate repository names create unstable IDs | Use a documented repo slug, owner-qualified fallback, deterministic hash shortening, and collision tests. |
| Static prompt validation diverges from utility rules | Keep existing review validation unchanged, mirror its v1 invariants in utility tests, and assert the registry, prompt, and utility schema constants are equal. |
| Empty registry blocks the add path or causes an empty review | Place non-empty checks inside review branches; test add/remove with empty fixtures and explicit review guidance. |
| Rename leaves stale platform files or manifest entries | Rename canonical source first and use the ownership-aware generator; run working-tree parity before commit, retain HEAD drift for CI, and run a scoped stale-name search. |
| Pester output crashes VS Code | Use only the canonical execution-subagent plus `Run-Tests.ps1` and `last-run.json` pattern. |
| Public GitHub reachability is unavailable or ambiguous | Fail before mutation; do not treat an empty, private, redirected, 404, or deleted page as success. |
| Scope expands into a general R&D framework | Keep two utility subcommands only; deviation policy requires approval for schema, dependency, source-type, or review-analysis expansion. |

## Out of Scope

- Private repository authentication or credential handling.
- Research sources other than public GitHub repositories.
- Automatic full assessment during `--add`.
- Deletion or rewriting of historical review outputs during `--remove`.
- A temporary or permanent `/cg-review-repos` alias.
- Registry schema migration or new root/entry fields.
- A general R&D source-management framework or standalone user CLI.
- Automatic roadmap insertion for a newly registered external repository.
- Rewriting historical brainstorms, plans, reviews, solutions, or generated
  token reports to use the new command name.

## Completion Contract

### Outcome

`/cg-compound-gpid-rd` replaces `/cg-review-repos` across all live command
surfaces. It preserves delta and full reviews and adds deterministic, tested
`--add <URL>` and confirmed `--remove <id>` registry operations without changing
the registry schema or historical review files.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Utility add/check-only/remove, strict parsing, collision, empty-registry, size-boundary, preservation, race, unsafe-link, and failure-path tests pass | `<pythonCommand> -m pytest scripts/tests/test_cg_compound_gpid_rd_registry.py -q` | yes |
| V2 | 2 | Prompt guardrail, four-mode parsing, hard stops, utility dispatch, exact-ID confirmation, and dynamic registry assertions pass | Safe execution subagent runs `. tests\Run-Tests.ps1 -File prompt-tools`, then reads `tests/last-run.json` | yes |
| V3 | 2 | Canonical rename reaches every platform and removes unchanged stale command files | `<pythonCommand> scripts/cg_generate_targets.py --all`; generator working-tree parity test; HEAD drift test deferred to post-commit/CI | yes |
| V4 | 2 | No old operational command remains in live sources or generated trees | Scoped `rg "cg-review-repos"` over live and generated paths; only an explicit negative test may match | yes |
| V5 | 2 | Audit allowlists and current documentation use the new command and all four modes | `scripts/cg_audit_context.py`, `docs/competitive-reviews.md`, `docs/reference.md`, `docs/reference/commands.md` | yes |
| V6 | 2 | Failed mutations leave fixture registries byte-for-byte unchanged; successful writes preserve unknown fields and concurrent winners | pytest temporary-registry assertions | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | `.github/` is canonical; generated command files are not edited independently. | Generator working-tree parity and post-commit/CI target drift |
| C2 | No registry schema migration or new runtime dependency. | Schema constant remains v1; standard-library imports only |
| C3 | Historical brainstorms, plans, reviews, solutions, and review outputs remain unchanged. | Git diff scope check |
| C4 | All mutation input is allowlisted; validation completes before an expected-state secure write that preserves concurrent winners. | Utility race, unsafe-link, and failure tests |
| C5 | The developer-repository guardrail remains before mode execution. | Prompt Pester assertions |
| C6 | Pester runs only through the safe `Run-Tests.ps1` execution-subagent workflow. | Verification command audit |

### Boundaries

- Allowed: canonical prompt rename, narrow registry utility, pytest and Pester
  tests, current docs, audit path update, and generated target regeneration.
- Out of scope: private repositories, other R&D sources, old-command alias,
  automatic baseline review after add, deletion of review history, schema
  migration, and real registry mutations during tests.

### Iteration Policy

1. Add failing utility tests before implementation.
2. Keep existing delta and full review behavior unchanged except for the new
   command name, hard-stop flag parsing, and empty-registry guidance.
3. Update canonical and live references before target generation.
4. Use temporary fixture registries for every mutation test.
5. Stop and request approval before adding a dependency, changing the schema, or
   expanding the utility into review analysis.
6. Complete focused tests before final stale-reference and working-tree parity checks.

### Blocked-Stop Conditions

- The current registry is malformed or uses an unexpected schema.
- No valid Python launcher is available.
- The generator refuses to remove a modified stale owned file.
- Safe public GitHub reachability verification cannot be expressed without
  broadening network trust.
- Required pytest, Pester, audit, or working-tree parity checks fail after the
  planned correction budget.
