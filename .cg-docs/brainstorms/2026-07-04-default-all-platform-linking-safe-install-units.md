---
date: 2026-07-04
title: "Default-All Platform Linking With Safe Install Units"
status: decided
scope: "Deep"
chosen-approach: "Default-all platform linking with per-platform merge-safe install units"
tags: [cross-agent, opencode, codex, claude-code, copilot, installation, junctions, platform-targets]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Default-All Platform Linking With Safe Install Units

## Context

Compound GPID began as a GitHub Copilot-first plugin because most internal World
Bank users were using Copilot. The organization is now exploring multiple AI
coding platforms, including Claude Code, Codex, OpenCode, and others. Internal
users may use several platforms at once and should not need to predict which
platform-specific files to install.

The July 3 brainstorm, "Cross-Agent Native Platform Targets," decided to keep
`.github/` as the canonical source and generate committed native target trees for
Claude Code, Codex, and OpenCode. This brainstorm assesses whether lessons from
EveryInc's Compound Engineering plugin architecture should complement that
decision.

Compound Engineering demonstrates a platform-plugin model: root-native plugin
packaging, OpenCode plugin hooks, marketplace/update flows, and direct plugin
loading where supported. However, World Bank laptops may not reliably allow
marketplace/plugin installation, so Compound GPID must continue to prioritize
enterprise-safe junction/symlink distribution.

## Requirements

- Keep `cg-update` and `cg-link` as the primary user-facing internal workflow.
- Make `cg-link` default to all supported platforms: Copilot, Claude Code,
  Codex, and OpenCode.
- Do not require users to know in advance which platform they will use.
- Do not require Claude Code, Codex, OpenCode, or other platform executables to
  be installed before linking.
- Preserve existing project-owned `.github/`, `.claude/`, `.agents/`, and
  `.opencode/` folders.
- Fail loudly and avoid destructive replacement when generated platform files
  conflict with user-managed files.
- Keep `.github/` as the canonical source for now.
- Defer native marketplace/plugin packaging to future exploration.

## Approaches Considered

### Approach 1: Default-All Junction Distribution

Keep the global install plus `cg-update` and `cg-link` model, but make `cg-link`
include all supported platform outputs by default.

**Pros**

- Best fit for locked-down World Bank machines.
- Minimal change to user behavior.
- Supports multi-platform users automatically.
- Avoids platform marketplace/plugin installation risk.

**Cons**

- More files appear in every linked project.
- Whole-folder linking can conflict with existing `.opencode/`, `.agents/`, or
  `.claude/` folders unless the linker becomes more granular.

### Approach 2: Guided Platform-Aware Linker

Keep `cg-link` conservative and add platform detection/guidance before linking
generated targets.

**Pros**

- Safer for existing platform folders.
- More transparent to cautious users.

**Cons**

- Adds friction.
- Users may not know which platforms they will need.
- Less aligned with minimal setup.

### Approach 3: Dual Track: Junction Default Now, Native Plugin Later

Implement default-all linking now and track platform-native plugin packaging as a
future option inspired by Compound Engineering.

**Pros**

- Captures Compound Engineering's useful lessons without depending on
  enterprise-problematic install mechanisms.
- Preserves current internal distribution.
- Creates a future path if World Bank constraints loosen.

**Cons**

- Adds roadmap complexity.
- Native packaging must remain explicitly deferred to avoid splitting focus.

## Decision

Choose **Approach 1 with Approach 3 as future framing**.

The refined implementation direction is:

**Default-all platform linking with per-platform merge-safe install units.**

`cg-link` should link all supported platform targets by default, while preserving
opt-out behavior through `--platforms copilot` or another explicit platform
list. The linker should not treat each platform root as an all-or-nothing
junction. Instead, it should install/link known platform subpaths and config
files at the safest granular level.

This complements the July 3 decision. The July 3 brainstorm solved generation of
native platform trees. This brainstorm adds the next layer: safe project
installation semantics.

## Installation Semantics

If a platform root does not exist, `cg-link` may create it.

If a platform root already exists, `cg-link` must preserve it and install
Compound GPID assets inside it only where safe.

Examples:

```text
.opencode/commands/
.opencode/agents/
.opencode/skills/
.opencode/opencode.json
```

```text
.claude/commands/
.claude/agents/
.claude/skills/
.claude/CLAUDE.md
```

```text
.agents/commands/
.agents/skills/
.agents/subagents/
.agents/AGENTS.md
```

For directories, prefer per-subdirectory junctions/symlinks where possible.

For files, prefer managed-copy with a marker rather than file symlinks, because
Windows file symlinks are more fragile on locked-down machines.

## Collision Policy

If a target path is absent:

- Create the managed link or managed copy.

If a target path exists and is already managed by Compound GPID:

- Refresh it.

If a target path exists and is user-managed:

- Do not overwrite it.
- Warn clearly.
- Continue installing other safe paths.
- Print platform-specific manual integration guidance.

Example:

```text
.opencode/opencode.json already exists and is user-managed.
Compound GPID did not overwrite it.

To enable Compound GPID in OpenCode, add:
{
  "instructions": [".opencode/AGENTS.md"],
  "skills": { "paths": [".opencode/skills"] }
}
```

For command or agent filename collisions such as `.opencode/commands/cg-work.md`:

- Refresh if the file has the Compound GPID managed marker.
- Skip and warn if it is user-managed.
- Overwrite only with an explicit force option.

## Auxiliary Folder Fallback

An auxiliary folder may be useful as a fallback or staging location:

```text
.compound-gpid/opencode/commands/
.compound-gpid/opencode/skills/
.compound-gpid/opencode/agents/
```

However, this should not be the primary runtime path unless a platform can be
configured to discover commands, skills, and agents there. Most platforms expect
conventional directories, so Compound GPID should put or link files where each
platform actually loads them.

## Target Mapping Implication

`target-mapping.json` should evolve from tree-level output paths toward install
units.

Possible future shape:

```json
{
  "platform": "opencode",
  "installUnits": [
    {
      "type": "directory",
      "source": ".opencode/commands",
      "target": ".opencode/commands",
      "mergeStrategy": "per-file-managed"
    },
    {
      "type": "directory",
      "source": ".opencode/skills",
      "target": ".opencode/skills",
      "mergeStrategy": "per-subdir-junction"
    },
    {
      "type": "file",
      "source": ".opencode/opencode.json",
      "target": ".opencode/opencode.json",
      "mergeStrategy": "managed-copy-or-manual-snippet"
    }
  ]
}
```

This would let `cg-link` handle platform files safely without replacing whole
platform roots.

## Lessons From Compound Engineering

Useful lessons:

- Platform-native UX matters: users should see commands/skills in each platform.
- A single package/repo should be the source of truth.
- Update flows must be explicit and documented.
- OpenCode can be supported through a small plugin hook that registers skill
  paths, but this should remain optional/future for Compound GPID.

Not directly transferable right now:

- Marketplace-first/plugin-first installation as the primary distribution path.
- Requiring native platform plugin installers.
- Assuming users can freely install plugins from GitHub or external package
  managers.

## Devil's Advocate

Problem validation:
This is a real problem. Internal users are moving beyond Copilot and may use
several platforms in parallel.

Simplicity check:
The simplest high-value solution is not native plugin packaging. It is to keep
the existing install/link/update model and make it default to all platform
targets with safer merge semantics.

Effort-value check:
Default-all linking plus safe install units delivers most of the value with
moderate effort. Native marketplace packaging may be valuable later but is not
proportionate under current World Bank machine constraints.

Charter alignment:
This aligns with Compound GPID's objective of providing a structured workflow
plugin for the World Bank team. It expands beyond the original Copilot framing
but does not conflict with project constraints if it remains fail-loud,
non-destructive, release-validated, and branch/test disciplined.

## Next Steps

1. Update `cg-link` defaults so all supported platforms are linked unless
   narrowed by `--platforms`.
2. Redesign linker platform handling from whole-root junctions to per-platform
   install units.
3. Add managed markers for generated platform config/command/agent files where
   file copying is required.
4. Add collision tests for existing `.opencode/`, `.agents/`, `.claude/`, and
   `.github/` directories.
5. Add smoke tests verifying linked projects expose commands, skills, agents,
   and valid OpenCode config.
6. Keep `cg-update` regenerating all platform trees globally.
7. Document opt-out behavior for Copilot-only or platform-specific projects.
8. Add a future roadmap idea for native plugin/marketplace packaging inspired by
   Compound Engineering, explicitly deferred until enterprise constraints are
   better understood.
