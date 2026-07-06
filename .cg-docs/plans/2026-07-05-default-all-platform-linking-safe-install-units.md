---
date: 2026-07-05
title: "Default-All Platform Linking With Safe Install Units"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-07-04-default-all-platform-linking-safe-install-units.md"
language: "PowerShell/Bash/Python/Markdown"
estimated-effort: "large"
deviation-policy: "ask"
tags: [cross-agent, opencode, codex, claude-code, copilot, installation, junctions, platform-targets]
phases: 5
---

# Plan: Default-All Platform Linking With Safe Install Units

## Objective

Make `cg-link` install Compound GPID assets for all supported platforms by
default while preserving existing user-owned platform folders. The implementation
must move platform linking from whole-root `.claude/`, `.agents/`, and
`.opencode/` junctions/symlinks to per-platform install units that can coexist
with project-local config and user-authored files.

## Context

The July 4 brainstorm chose **Approach 1 with Approach 3 as future framing**:
keep the enterprise-safe `install` / `cg-update` / `cg-link` workflow, make all
supported platform outputs available by default, and defer native marketplace or
plugin packaging until World Bank machine constraints are better understood.

This plan complements the completed July 3 cross-agent platform work. That work
created generated native platform trees from canonical `.github/` assets. This
plan changes the **project installation semantics** for those generated outputs:
user projects should receive native commands, skills, agents, and necessary
config guidance without replacing whole platform root folders such as
`.opencode/` or `.agents/`.

Brain findings applied:

- Keep generated platform trees committed and release-validated; do not require
  consumer projects to generate them locally. Source:
  `.cg-docs/plans/2026-07-03-cross-agent-native-platform-targets.md`.
- `cg-update` should keep generated platform trees current and PowerShell must
  use consistent Python resolution. Source:
  `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`.
- The prior `.github/` migration from whole-root junctions to
  per-subdirectory junctions is the architectural precedent for preserving user
  content. Source: `.cg-docs/plans/2026-03-04-per-subdirectory-junctions.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | `cg-link` defaults to all supported platforms: Copilot, Claude Code, Codex, and OpenCode. | brainstorm decision |
| R2 | Users can still narrow linking explicitly; `--platforms` governs Copilot `.github/` installation and every generated native platform. | plan-review clarification |
| R3 | Existing project-owned `.github/`, `.claude/`, `.agents/`, and `.opencode/` roots are preserved. | brainstorm requirement |
| R4 | Platform install uses granular install units instead of whole platform root replacement. | brainstorm decision |
| R5 | Directory install units use junctions on Windows and symlinks on macOS/Linux where safe. | existing linker design |
| R6 | File install units use managed-copy semantics and never place invalid markers inside strict JSON config files. | brainstorm + OpenCode schema constraint |
| R7 | User-managed conflicts are warned and skipped, not overwritten; safe install units continue where possible. | brainstorm collision policy |
| R8 | `cg-unlink` removes only Compound GPID-managed install units and leaves user-owned platform files in place. | unlink safety |
| R9 | `.gitignore` entries cover all managed install units without ignoring entire platform roots. | install safety |
| R10 | Tests cover default-all behavior, explicit platform narrowing, existing platform root preservation, conflicts, unlink cleanup, and OpenCode config validity. | verification need |
| R11 | Documentation explains default-all linking, opt-out behavior, existing-folder handling, and manual config snippets when user-managed config blocks managed copy. | user guidance |
| R12 | `cg-update` remains responsible for refreshing generated global platform trees; this plan must not regress update behavior. | July 3 solution |
| R13 | Native marketplace/plugin packaging remains out of scope except as a documented future idea. | brainstorm decision |
| R14 | `cg-update` refreshes project-local managed copied files from `.compound-gpid/managed-files.json` when the current file still matches the recorded managed checksum. | plan-review finding P2.3 |
| R15 | `cg-unlink` discovers managed install units without assuming `.github/` exists, so platform-only installs can be removed safely. | plan-review finding |
| R16 | Missing selected platform source trees fail loudly with a non-zero exit after reporting all missing sources. | plan-review finding |

## Implementation Steps

## Phase 1: Install-Unit Model and Linker Defaults

### 1. Extend target mapping with platform install units

- **Requirements**: R3, R4, R5, R6, R7, R9
- **Files**:
  - `.github/shared/target-mapping.json`
  - `scripts/schemas/target_mapping_schema.json`
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_target_mapping.py`
  - `scripts/tests/test_cg_generate_targets.py`
- **Details**:
  - Add optional `installUnits` to each supported target in
    `target-mapping.json`.
  - Keep existing `outputPaths` for generation and drift tests; `installUnits`
    describe how the generated outputs are installed into consumer projects.
  - Initial platform install units:
    - Copilot:
      - directory `.github/prompts` -> `.github/prompts`
      - directory `.github/skills` -> `.github/skills`
      - directory `.github/agents` -> `.github/agents`
      - directory `.github/instructions` -> `.github/instructions`
      - directory `.github/shared` -> `.github/shared`
      - generated file `.github/copilot-instructions.md` using existing
        `New-CopilotInstructions` / `generate_copilot_instructions` behavior
    - Claude Code:
      - directory `.claude/commands` -> `.claude/commands`
      - directory `.claude/skills` -> `.claude/skills`
      - directory `.claude/agents` -> `.claude/agents`
      - file `.claude/CLAUDE.md` -> `.claude/CLAUDE.md`
      - file `.claude/model-mapping.claude.json` -> `.claude/model-mapping.claude.json`
    - Codex:
      - directory `.agents/commands` -> `.agents/commands`
      - directory `.agents/skills` -> `.agents/skills`
      - directory `.agents/subagents` -> `.agents/subagents`
      - file `.agents/AGENTS.md` -> `.agents/AGENTS.md`
      - file `.agents/model-mapping.codex.json` -> `.agents/model-mapping.codex.json`
    - OpenCode:
      - directory `.opencode/commands` -> `.opencode/commands`
      - directory `.opencode/skills` -> `.opencode/skills`
      - directory `.opencode/agents` -> `.opencode/agents`
      - file `.opencode/AGENTS.md` -> `.opencode/AGENTS.md`
      - file `.opencode/opencode.json` -> `.opencode/opencode.json`
      - file `.opencode/model-mapping.opencode.json` -> `.opencode/model-mapping.opencode.json`
  - Define per-unit metadata fields:
    - `type`: `directory` or `file`
    - `source`
    - `target`
    - `strategy`: `link-directory`, `managed-copy`, `generated-copy`, or
      `config-copy-or-snippet`
    - optional `manualSnippet` for strict config files such as OpenCode JSON
  - For strict JSON configs, do not use inline comments as markers. Track
    managed-copy ownership through a project-local manifest created by the
    linker, e.g. `.compound-gpid/managed-files.json`, and by comparing content
    checksums before refresh/removal.
  - Update schema validation so malformed install units fail tests.
  - Keep `scripts/cg_generate_targets.py --dry-run` output focused on generated
    files, not install operations.
- **Test Scenarios**:
  - Schema accepts valid install units for Copilot and all generated targets.
  - Schema rejects missing `source`, missing `target`, unknown `type`, and
    unknown `strategy`.
  - Generator still emits the same generated files and does not modify `.github/`.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_cg_generate_targets.py`
- **Acceptance criteria**:
  - Target mapping captures all platform install units; only the dynamic
    Copilot instructions generation remains a named generated-copy strategy.

### 2. Prepare platform parsing without flipping defaults yet

- **Requirements**: R1, R2
- **Files**:
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `tests/link.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
  - `docs/reference.md`
  - `docs/installation.md`
- **Details**:
  - Implement normalized platform parsing as a helper in PowerShell and Bash,
    but do **not** change the default value until Phase 2 has replaced
    whole-root platform links with install-unit linking.
  - `--platforms` governs all platform families, including Copilot. Therefore:
    - `cg-link --platforms copilot` installs only Copilot `.github/` units.
    - `cg-link --platforms opencode` installs only OpenCode units and does not
      create or update `.github/`.
    - `cg-link --platforms copilot,opencode` installs only those two families.
  - Add an alias value if useful: `--platforms all` maps to the full supported
    list.
  - Deduplicate and trim platform values.
  - Unknown platforms warn and are skipped only when at least one valid platform
    remains; if no valid platforms remain, exit with an actionable error.
  - In Bash, replace the current `for arg in "$@"` parser with a
    `while [ "$#" -gt 0 ]` parser so `--yes --platforms value` and
    `--platforms value --yes` both work.
  - In PowerShell, add an argv normalization layer before platform resolution so
    both native PowerShell forms and `bin/cg-link.cmd` GNU-style forwarding work:
    `--platforms value`, `--platforms=value`, `-Platforms value`, `--yes`,
    `-y`, and `-Force`.
  - Tests introduced in this step should exercise the parser as an isolated
    behavior. Default-all user behavior is enabled later in Step 5.
- **Test Scenarios**:
  - Parser maps `all` to all platforms.
  - `--platforms copilot` means Copilot only.
  - `--platforms all` means all platforms.
  - Duplicate platforms do not duplicate work.
  - Unknown-only list errors; mixed valid/unknown warns and continues.
  - Windows parser accepts `--platforms=value`, `--platforms value`,
    `-Platforms value`, `--yes`, `-y`, and `-Force`, including through
    `bin/cg-link.cmd` argument forwarding where feasible in tests.
  - Bash parser accepts `--platforms=value`, `--platforms value`,
    `--yes --platforms value`, and `--platforms value --yes`.
- **Tests**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**:
  - Parser behavior is ready for default-all linking, but the runnable default
    has not changed while whole-root platform linking still exists.

## Phase 2: Merge-Safe Platform Linking

### 3. Implement install-unit application helpers for PowerShell

- **Requirements**: R3, R4, R5, R6, R7, R9
- **Files**:
  - `scripts/link.ps1`
  - `scripts/helpers.ps1`
  - `tests/link.Tests.ps1`
- **Details**:
  - Replace whole platform root linking in `link.ps1` with install-unit
    application based on `target-mapping.json`.
  - Gate Copilot `.github/` handling behind the normalized platform list. If
    Copilot is not selected, skip `.github/` directory setup,
    `.github/copilot-instructions.md`, and `.github/` gitignore entries.
  - Apply the same install-unit skip-and-continue collision policy to Copilot
    `.github/*` units as to generated native platforms. Do not let a real
    `.github/prompts`, `.github/skills`, `.github/agents`, `.github/shared`, or
    `.github/instructions` directory block safe selected native platform units.
  - Create platform root directories as real directories when absent.
  - Preflight migration: if `.claude/`, `.agents/`, or `.opencode/` is an
    existing Compound GPID whole-root junction from the July 3 implementation,
    remove only the junction, create a real platform root, then apply install
    units. Do not migrate non-Compound junctions without confirmation.
  - For directory install units:
    - If target absent: create junction to source directory.
    - If target is Compound GPID junction: leave/refresh idempotently.
    - If target is non-Compound junction: prompt before relinking unless
      `-Force` is set.
    - If target is a real directory: warn, skip that unit, and continue other
      units. Do not exit for platform-directory conflicts.
  - For file install units:
    - If target absent: copy source file and record source path + checksum in
      `.compound-gpid/managed-files.json`.
    - If target exists and matches manifest-managed checksum: refresh copy and
      update checksum.
    - If target exists but does not match manifest: warn and skip.
    - For config files with `manualSnippet`, print the snippet when skipped.
  - Update `.gitignore` block from the successful-install manifest only:
    include targets actually installed by Compound GPID and
    `.compound-gpid/managed-files.json`; do not ignore skipped user-owned
    directories or files.
  - Ensure PowerShell remains PS 5.1 compatible and ASCII-only.
- **Test Scenarios**:
  - Existing `.opencode/` real directory survives and receives safe missing
    subdirectory junctions.
  - Existing Compound GPID whole-root `.opencode/` junction is migrated to a
    real `.opencode/` root plus install-unit junctions/copies.
  - Existing `.opencode/commands/` real directory is skipped without blocking
    `.opencode/skills/` or `.opencode/agents/`.
  - Existing user-managed `.opencode/opencode.json` is not overwritten and the
    manual snippet is surfaced.
  - Existing `.github/prompts/` real directory is skipped without blocking other
    selected Copilot or native platform units.
  - Manifest-managed JSON config is refreshed without inline comments.
  - `.gitignore` contains specific platform unit paths, not `.opencode/` as a
    whole root.
  - `.gitignore` does not include skipped user-owned paths.
- **Tests**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File ps51-compat"`
- **Acceptance criteria**:
  - Windows linker installs platform assets into existing platform roots without
    destructive replacement and without invalid JSON markers.

### 4. Implement install-unit application helpers for Bash

- **Requirements**: R3, R4, R5, R6, R7, R9, R16
- **Files**:
  - `scripts/link.sh`
  - `tests/bash-scripts.Tests.ps1`
- **Details**:
  - Mirror PowerShell install-unit behavior in bash with macOS bash 3.2
    compatibility.
  - Gate Copilot `.github/` handling behind the normalized platform list. If
    Copilot is not selected, skip `.github/` setup and Copilot gitignore entries.
  - Apply the same skip-and-continue collision policy to Copilot `.github/*`
    units in Bash as in PowerShell, so a real Copilot subdirectory does not
    block selected native platform units.
  - Preflight-migrate existing Compound GPID whole-root `.claude/`, `.agents/`,
    and `.opencode/` symlinks to real roots before applying install units.
  - Avoid associative arrays.
  - Use Python stdlib snippets where JSON parsing or manifest writing would be
    brittle in shell.
  - Use `ln -s` for directory install units.
  - Use atomic temp-file + move for managed copied files.
  - Preserve existing `.opencode/`, `.agents/`, and `.claude/` directories.
  - Treat missing selected source trees or source files as non-zero installation
    corruption after reporting all missing selected sources.
  - Ensure all user-facing warnings match PowerShell semantics closely enough
    for documentation and tests.
- **Test Scenarios**:
  - Bash script has default-all platform behavior.
  - Bash script has order-independent parsing for `--platforms` and `--yes`.
  - Bash script skips real Copilot subdirectory conflicts while continuing other
    selected native platform units.
  - Bash script can migrate old whole-root platform symlinks.
  - Bash script fails non-zero when a selected source tree is missing.
  - Bash script includes install-unit loop, non-destructive conflict branch, and
    manifest handling.
  - Script remains syntax-valid under bash 3.2-compatible syntax.
- **Tests**:
  - `bash -n scripts/link.sh`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**:
  - macOS/Linux linker behavior matches Windows semantics for platform install
    units.

### 5. Flip the default to all platforms and add platform smoke verification

- **Requirements**: R1, R2, R10, R16
- **Files**:
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `tests/link.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
- **Details**:
  - After Steps 3 and 4 remove whole-root platform linking, change the runnable
    default platform set to `copilot,claude-code,codex,opencode`.
  - Preserve explicit narrowing semantics from Step 2.
  - After linking, verify a known command, skill, and agent path for each
    successfully linked platform when the relevant install units were not
    skipped.
  - OpenCode minimum checks:
    - `.opencode/commands/cg-plan.md`
    - `.opencode/skills/cg-skill-brain-query/SKILL.md`
    - `.opencode/agents/cg-testing.md`
    - `.opencode/opencode.json` when managed by Compound GPID
  - Claude Code and Codex get analogous command/skill/agent checks.
  - If some target units were skipped due to user-managed conflicts, report
    partial availability and required manual action.
  - Missing selected source trees or source files under the Compound GPID install
    are not user conflicts. Collect all missing selected sources, report them,
    and exit non-zero instead of claiming a successful partial link.
- **Test Scenarios**:
  - No `--platforms` now installs all platforms.
  - `--platforms copilot` remains Copilot-only.
  - `--platforms opencode` does not create `.github/`.
  - Full default-all link reports all platform checks as available.
  - Partial conflict reports warning but overall link can still complete.
  - Missing selected source generated tree or source file fails loudly with a
    non-zero exit after all missing selected sources are reported.
- **Tests**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**:
  - Whole-root platform linking no longer exists before the default flips, and
    linker output tells users whether commands, skills, and agents should be
    visible in each platform after restart.

## Phase 3: Safe Unlink and Gitignore Cleanup

### 6. Update `cg-unlink` for install units and manifest-managed files

- **Requirements**: R8, R9, R15
- **Files**:
  - `scripts/unlink.ps1`
  - `scripts/unlink.sh`
  - `tests/unlink.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
- **Details**:
  - Stop treating `.claude/`, `.agents/`, and `.opencode/` as whole-root
    managed platform trees for new installs.
  - Stop using `.github/` existence as the install-detection gate. Discover
    managed content from `.compound-gpid/managed-files.json`, install-unit
    definitions, symlink/junction targets pointing into the Compound GPID
    install, and legacy whole-root platform links.
  - Remove only Compound GPID-managed install units:
    - directory junctions/symlinks whose targets point into the Compound GPID
      install
    - copied files listed in `.compound-gpid/managed-files.json` whose current
      checksum still matches the recorded managed checksum
  - Leave user-modified copied files in place and warn that ownership changed.
  - Remove empty platform roots only if they become empty after managed unit
    removal. Never remove non-empty platform roots.
  - Keep legacy whole-platform-root unlink support for old `.claude/`, `.agents/`,
    and `.opencode/` junction/symlink installs produced by the July 3 PR.
  - Remove only Compound GPID `.gitignore` entries, preserving unrelated project
    ignore rules.
- **Test Scenarios**:
  - Removes managed platform command/skill/agent directory links.
  - Removes manifest-managed config files only when unmodified.
  - Leaves user-modified platform files in place.
  - Cleans empty `.opencode/` but preserves `.opencode/` with user files.
  - Fully unlinks an OpenCode-only install that has `.opencode/*` units,
    manifest entries, and `.gitignore` entries but no `.github/` directory.
  - Still removes legacy whole-root platform symlinks/junctions from older
    installs.
- **Tests**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File unlink"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**:
  - Unlink is non-destructive and reversible for Compound GPID-managed units.

## Phase 4: Tests, CI, and Update Regression Protection

### 7. Refresh manifest-managed copied files during `cg-update`

- **Requirements**: R12, R14
- **Files**:
  - `scripts/update.ps1`
  - `scripts/update.sh`
  - `tests/update.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
- **Details**:
  - Preserve existing post-pull global tree regeneration.
  - After global regeneration, if the current project has
    `.compound-gpid/managed-files.json`, refresh manifest-managed copied files
    whose current checksum still matches the recorded managed checksum.
  - If a managed copied file has been edited by the user, warn and leave it in
    place; do not overwrite.
  - If a source file no longer exists in the global install, warn loudly and
    leave the current project file unchanged.
  - Keep this refresh current-project-only; do not scan the machine for all
    linked projects.
- **Test Scenarios**:
  - `cg-update` refreshes unchanged manifest-managed copied files.
  - `cg-update` skips and warns for user-modified copied files.
  - `cg-update` keeps generated-tree refresh behavior intact.
- **Tests**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File update"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**:
  - Managed copied platform files do not go stale after a normal `cg-update` run
    from a linked project.

### 8. Expand test coverage for default-all and collision behavior

- **Requirements**: R10, R12
- **Files**:
  - `tests/link.Tests.ps1`
  - `tests/unlink.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
  - `tests/update.Tests.ps1`
  - `scripts/tests/test_update_generates_targets.py`
  - `scripts/tests/test_target_opencode.py`
- **Details**:
  - Add PowerShell tests for platform parsing and install-unit collision logic.
  - Add PowerShell tests for GNU-style forwarded Windows flags and missing
    selected source trees failing non-zero.
  - Add Bash static tests for default `PLATFORMS`, order-independent flag
    parsing, missing selected source failures, and conflict branches including
    Copilot subdirectory conflicts.
  - Add update regression assertions that `cg-update` still runs
    `cg_generate_targets.py --all` after pull.
  - Keep existing OpenCode generated-tree smoke tests: valid `opencode.json`,
    command templates include `$ARGUMENTS`, skills and agents are discoverable.
  - If necessary, add small helper functions in scripts solely to make behavior
    testable without creating real platform installations.
  - Follow Pester safety: use `tests/Run-Tests.ps1`; do not invoke Pester
    directory runs directly.
- **Test Scenarios**:
  - Default-all linking is asserted on both Windows and Bash scripts.
  - `--platforms copilot` opt-out is asserted.
  - Existing root directories are preserved.
  - User-managed file conflicts skip and continue.
  - `cg-update` behavior from July 3 remains intact.
- **Tests**:
  - `python3 -m pytest scripts/tests`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
- **Acceptance criteria**:
  - Python and Pester suites pass locally; CI E2E smoke tests pass on Windows and
    macOS.

### 9. Validate generated-tree and OpenCode runtime assumptions

- **Requirements**: R10, R12
- **Files**:
  - `.opencode/opencode.json`
  - `.opencode/commands/*.md`
  - `.opencode/skills/*/SKILL.md`
  - `.opencode/agents/*.md`
  - `scripts/tests/test_target_opencode.py`
  - `scripts/tests/test_target_drift.py`
- **Details**:
  - Re-run `scripts/cg_generate_targets.py --all` after target-mapping changes.
  - Confirm generated trees are committed and drift tests pass.
  - Confirm OpenCode config remains schema-valid: no unknown top-level fields,
    no inline JSON comments, and valid `skills.paths` / `instructions` fields.
  - Do not require the `opencode` executable in automated tests; static smoke
    tests are the required fallback because CI and World Bank machines may not
    have OpenCode installed.
  - If an `opencode` CLI is available locally, optionally run a non-required
    command-discovery smoke check and record it in the work report.
- **Test Scenarios**:
  - Drift tests compare Git-tracked generated files only.
  - OpenCode generated assets include at least one command, skill, and agent.
  - OpenCode config remains valid JSON and valid according to known schema shape.
- **Tests**:
  - `python3 scripts/cg_generate_targets.py --all`
  - `python3 -m pytest scripts/tests/test_target_opencode.py scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py`
- **Acceptance criteria**:
  - Generated OpenCode assets remain usable as the neutral reference platform.

## Phase 5: Documentation, UX Messages, and Future Framing

### 10. Update user-facing docs and linker messages

- **Requirements**: R11, R13
- **Files**:
  - `README.md`
  - `docs/installation.md`
  - `docs/reference.md`
  - `docs/context-files.md`
  - `docs/troubleshooting.md`
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `scripts/unlink.ps1`
  - `scripts/unlink.sh`
- **Details**:
  - Document `cg-link` default-all behavior.
  - Document explicit opt-out examples:
    - `cg-link --platforms copilot`
    - `cg-link --platforms opencode`
    - `cg-link --platforms copilot,opencode`
  - Clarify that `--platforms` governs Copilot `.github/` and generated native
    platform families; `--platforms opencode` is intentionally OpenCode-only.
  - Explain that platform executables do not need to be installed before linking.
  - Explain restart/reload expectations for each platform where known.
  - Explain existing-folder collision behavior and manual config snippets.
  - Update success output from Copilot-only language to platform-inclusive
    language.
  - Document that native marketplace/plugin packaging is intentionally deferred
    and remains a future option inspired by Compound Engineering.
- **Test Scenarios**:
  - Docs mention default-all behavior and Copilot-only opt-out.
  - Docs do not claim native marketplace packaging is currently supported.
  - Linker output does not say only Copilot prompts are available after a
    default-all link.
- **Tests**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
    if docs/prompt auto sections are affected.
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**:
  - Internal users can understand the default path, opt-out path, and conflict
    recovery without knowing the generator architecture.

## Testing Strategy

- **Python generator and platform tests**:
  - `python3 -m pytest scripts/tests`
- **Pester safe full suite**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
- **Targeted Pester during implementation**:
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File unlink"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File update"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File ps51-compat"`
- **Syntax checks**:
  - `bash -n scripts/link.sh`
  - `bash -n scripts/unlink.sh`
- **Manual/runtime checks when available**:
  - Run `cg-link` in a disposable project with no platform folders.
  - Run `cg-link` in a disposable project with pre-existing `.opencode/` and
    `opencode.json`.
  - Restart OpenCode and confirm `/cg-*` commands are visible if OpenCode CLI/UI
    is available.

## Documentation Checklist

- [ ] `README.md` describes default-all platform support.
- [ ] `docs/installation.md` shows default and opt-out linking examples.
- [ ] `docs/reference.md` updates `cg-link [--platforms <list>]` semantics.
- [ ] `docs/context-files.md` explains generated trees and install units.
- [ ] `docs/troubleshooting.md` covers existing `.opencode/`, `.agents/`, and
      `.claude/` folder conflicts.
- [ ] Linker success/warning messages are platform-inclusive and actionable.
- [ ] Future native plugin packaging is documented as deferred, not promised.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| User already has `.opencode/commands` or `.agents/subagents` as real directories. | Medium | High | Skip only conflicting install units, continue safe units, print clear warnings and manual recovery steps. |
| User already has `.github/prompts` or another Copilot subdirectory as a real directory. | Medium | High | Apply the same skip-and-continue install-unit policy to Copilot units and do not block selected native platform units. |
| Strict JSON config such as `opencode.json` becomes invalid due to marker comments or unknown keys. | Medium | High | Never insert markers into JSON; use sidecar manifest/checksum tracking and validate generated OpenCode config shape in tests. |
| Default-all linking surprises Copilot-only users by adding platform folders. | Medium | Medium | Document default-all behavior prominently and keep `--platforms copilot` opt-out. |
| `.gitignore` accidentally hides user-owned platform config. | Medium | High | Add only specific managed unit paths; never ignore whole `.opencode/`, `.agents/`, or `.claude/` roots. |
| Unlink removes user-owned files from existing platform roots. | Low | High | Remove only symlinks/junctions pointing to Compound GPID and manifest-managed copied files whose checksum still matches. |
| PowerShell and Bash linker behavior diverge. | Medium | Medium | Implement mirrored test cases and keep shared semantics documented in target mapping/install-unit schema. |
| `cg-update` generated-tree refresh regresses while linker work is refactored. | Low | High | Preserve update tests and include update behavior in final verification surface. |
| Managed copied files become stale after `cg-update`. | Medium | Medium | Refresh manifest-managed copies in the current project when checksums show they remain CG-managed. |
| Platform-only installs cannot be unlinked because `.github/` is absent. | Medium | High | Make unlink discovery manifest/install-unit based instead of `.github/` based and test OpenCode-only unlink. |
| Missing generated source tree is hidden as a partial success. | Low | High | Treat missing selected Compound GPID source trees/files as non-zero install corruption after reporting all missing sources. |
| Default-all is enabled before whole-root platform linking is removed. | Low | High | Phase order requires install-unit linker completion before Step 5 flips the default. |
| Native plugin packaging scope creeps into this iteration. | Medium | Medium | Keep native packaging explicitly out of scope and record it only as future framing. |

## Out of Scope

- Native marketplace/plugin packaging for OpenCode, Claude Code, Codex, Copilot,
  or other platforms.
- Installing AI platforms or validating that platform executables are present.
- Replacing `.github/` as the canonical source.
- Adding new supported platforms beyond Copilot, Claude Code, Codex, and
  OpenCode.
- Automatically editing user-managed strict config files when safe ownership
  cannot be established.
- Runtime UI automation for OpenCode/Claude/Codex command discovery in CI.

## Completion Contract

### Outcome

`cg-link` installs all supported Compound GPID platform assets by default through
merge-safe install units, preserving existing project platform folders and
providing explicit opt-out and conflict guidance. `cg-unlink`, `cg-update`, docs,
and tests reflect the new default-all, non-destructive platform installation
model.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Target mapping defines valid install units for Claude Code, Codex, and OpenCode. | `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_cg_generate_targets.py` | yes |
| V2 | 1 | Platform parser supports `all`, Copilot-only, OpenCode-only, mixed lists, duplicates, unknowns, Windows GNU-style forwarded flags, and Bash flag ordering without flipping the runnable default yet. | `tests/link.Tests.ps1`, `tests/bash-scripts.Tests.ps1` | yes |
| V3 | 2 | Windows linker preserves existing platform roots and handles native and Copilot directory/file install-unit collisions non-destructively. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"` | yes |
| V4 | 2 | Bash linker mirrors install-unit and collision behavior with syntax-valid bash. | `bash -n scripts/link.sh`; `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"` | yes |
| V5 | 2 | After whole-root platform linking is removed, `cg-link` defaults to all platforms, explicit `--platforms copilot` remains available, and missing selected source trees fail non-zero. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"`; `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"` | yes |
| V6 | 2 | Linked OpenCode assets include discoverable commands, skills, agents, and valid config when managed. | `python3 -m pytest scripts/tests/test_target_opencode.py` | yes |
| V7 | 3 | `cg-unlink` removes only Compound GPID-managed install units, leaves user-owned platform files untouched, and works for OpenCode-only installs with no `.github/`. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File unlink"` | yes |
| V8 | 4 | `cg-update` refreshes manifest-managed copied files without overwriting user-modified copies. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File update"` | yes |
| V9 | 4 | Generated tree refresh and drift gates remain intact. | `python3 scripts/cg_generate_targets.py --all`; `python3 -m pytest scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py scripts/tests/test_update_generates_targets.py` | yes |
| V10 | 4 | Full Python platform/generator suite passes. | `python3 -m pytest scripts/tests` | yes |
| V11 | 4 | Full Pester suite passes through the safe wrapper. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V12 | 5 | User-facing docs describe default-all linking, opt-out behavior, collision handling, and deferred native packaging. | `README.md`, `docs/installation.md`, `docs/reference.md`, `docs/context-files.md`, `docs/troubleshooting.md` | yes |
| V13 | final | PR CI passes on Windows and macOS E2E smoke checks. | GitHub PR status checks | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | Do not overwrite user-managed platform directories or files. | Tests cover real-directory and user-managed file conflicts. |
| C2 | all | Do not place invalid management markers inside strict JSON config files. | OpenCode config tests validate schema-compatible JSON shape. |
| C3 | all | Do not require platform executables to be installed for `cg-link`. | Linker logic uses files only; no platform CLI calls in required tests. |
| C4 | all | Do not regress `cg-update` generated-tree refresh. | Update generator tests remain passing. |
| C4b | all | Do not leave manifest-managed copied files stale after `cg-update` when they remain unmodified. | Update tests cover managed-copy refresh. |
| C5 | all | Keep `.github/` canonical and unchanged by generation. | Generator tests assert `.github/` source is not modified. |
| C5b | all | Do not require `.github/` to exist for platform-only link/unlink workflows. | Link and unlink tests cover OpenCode-only installs. |
| C5c | all | Do not silently skip missing selected Compound GPID source trees or files. | Link tests cover missing source trees as non-zero errors. |
| C6 | all | Use safe Pester runner only. | Verification commands use `tests/Run-Tests.ps1`. |
| C7 | all | Keep PowerShell scripts PS 5.1 compatible and ASCII-only. | `ps51-compat` test passes. |
| C8 | all | Native marketplace/plugin packaging remains deferred. | Docs and implementation avoid plugin marketplace changes. |

### Boundaries

- Allowed: modify linker/unlinker scripts, generated target mapping/schema,
  generator support for install-unit metadata, tests, generated platform trees,
  and user-facing docs.
- Allowed: add a project-local Compound GPID manifest for managed copied files
  if needed for safe config refresh/unlink.
- Out of scope: native plugin package manifests, platform marketplace install
  flows, auto-installing platforms, adding new platform targets, or making
  `.github/` a generated output.

### Iteration Policy

1. Preserve existing user-owned files over convenience; if ownership is unclear,
   warn and skip rather than overwrite.
2. Prefer schema/data-driven install units over hard-coded platform-path branches.
3. Keep Windows and Bash implementations behaviorally equivalent; if parity is
   uncertain, stop and add tests before continuing.
4. If default-all behavior creates unacceptable friction in tests or docs,
   revise the plan before implementing a different default.
5. Under `deviation-policy: ask`, stop before changing the collision policy,
   adding native package support, or modifying strict config files without a
   safe ownership signal.

### Blocked-Stop Conditions

- Existing platform root preservation cannot be implemented without destructive
  replacement.
- OpenCode config cannot remain valid JSON under the proposed managed-copy
  strategy.
- Windows junction behavior cannot be tested safely through the existing Pester
  wrapper.
- Bash implementation would require Bash 4+ features not available on macOS
  default Bash 3.2.
- Required verification fails after the planned fix attempts.
- Implementing the plan would require platform-native marketplace/plugin work.
