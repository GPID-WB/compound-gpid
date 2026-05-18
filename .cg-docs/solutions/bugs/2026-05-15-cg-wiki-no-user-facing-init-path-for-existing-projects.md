---
date: 2026-05-15
title: "No user-facing path to initialize wiki on existing projects"
category: "bugs"
type: "bug"
language: "both"
tags: [prompt-design, cg-wiki, ux, bootstrap-trap, agent-design, subcommand-gap]
root-cause: "@cg-wiki mode:init existed but /cg-wiki had no init subcommand to expose it; every other entry point either halted or gave a now-wrong recovery suggestion pointing at /cg-setup"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# No User-Facing Path to Initialize Wiki on Existing Projects

## Symptom

On a project with no `_wiki.yml`, every wiki entry point either skips silently
or halts with no forward path:

- `/cg-wiki rebuild`, `/cg-wiki status` — Pre-Flight halts: "manifest not found"
- `/cg-compound` Step 3c — skips silently: "no manifest found"
- `/cg-setup` Mode B (B1.1.6) — reports the gap but takes no action
- `/cg-wiki init` — not a recognized subcommand (shows usage guide and stops)

The only working path was Mode A `/cg-setup` (full re-setup) — unnecessarily
destructive for an already-configured project that simply hasn't initialized
a wiki yet.

## Root Cause

`@cg-wiki` was designed as infrastructure dispatched by `/cg-setup`, with no
direct user-facing bootstrap path for existing projects. When `/cg-wiki` was
authored as the user-facing prompt, its Step 1 parse table listed only
`status|rebuild|restructure|convert|help` — `init` was omitted because the
original design assumed wiki initialization would always happen during full
project setup.

The Step 2 manifest guard (`_wiki.yml` must exist) then halted all other
subcommands, leaving users with no non-destructive way to bootstrap a wiki
mid-project.

Additionally, the "no manifest" recovery messages in `cg-compound.prompt.md`
Step 3c (`"run /cg-wiki rebuild"`) and `cg-setup.prompt.md` B1.1.6
(`"run /cg-setup"`) both pointed at commands that either re-ran the same halt
or were heavier than needed.

## Reproduction Test

Added to `tests/wiki.Tests.ps1`:

```powershell
Describe "cg-wiki.prompt.md - init subcommand" {
    It "documents the init subcommand in the Usage section" { ... }
    It "includes init in the Step 1 parse table" { ... }
    It "dispatches @cg-wiki with mode: init" { ... }
    It "allows init subcommand to bypass the missing-manifest guard" { ... }
}

Describe "cg-compound.prompt.md - Step 3c references /cg-wiki init for missing manifest" {
    It "Step 3c no-manifest message directs user to /cg-wiki init (not rebuild)" { ... }
}

Describe "cg-setup.prompt.md - B1.1.6 references /cg-wiki init" {
    It "B1.1.6 no-wiki message directs user to /cg-wiki init (not /cg-setup)" { ... }
}

Describe "docs/reference.md - /cg-wiki entry includes init subcommand" {
    It "documents init subcommand in /cg-wiki reference entry" { ... }
}
```

All assertions failed on the code prior to the fix.

## Fix

### 1. `.github/prompts/cg-wiki.prompt.md`

- **Usage block**: added `/cg-wiki init` line with description.
- **Step 1 parse table**: added `init` row.
- **Step 2 manifest guard**: extended the bypass exception from `help` only to
  `help` and `init`.
- **Step 3 dispatch**: added `#### init` section that reads `project-type` from
  `compound-gpid.local.md` and `charter-content` from `compound-gpid.md`, then
  dispatches `@cg-wiki` with `mode: init`.

### 2. `.github/prompts/cg-compound.prompt.md` — Step 3c

```markdown
# Before
> "No wiki manifest found — run `/cg-wiki rebuild` to initialize."

# After
> "No wiki manifest found — run `/cg-wiki init` to initialize."
```

### 3. `.github/prompts/cg-setup.prompt.md` — B1.1.6

```markdown
# Before
> "No project wiki found. Run `/cg-setup` to initialize the wiki for this project."

# After
> "No project wiki found. Run `/cg-wiki init` to initialize the wiki for this project."
```

### 4. `docs/reference.md` — `/cg-wiki` table row

Added `init` to the subcommand list in the prompt, updated description to explain
`init` bootstraps from a project-type template, and changed the initialization
note from "Wiki initialized at `/cg-setup`" to "Wiki initialized at `/cg-setup`
or `/cg-wiki init`".

## Lessons Learned

**Agent infrastructure ≠ user-facing subcommand.** When an agent supports a
mode that users might need to invoke directly (especially a bootstrap/init mode),
there must be a corresponding user-facing subcommand. Do not assume that
initialization will always happen through a higher-level workflow (like
`/cg-setup`) — projects upgrade over time and gain new features mid-life.

**Audit all "no manifest" recovery messages together.** This bug caused three
separate files (`cg-wiki.prompt.md`, `cg-compound.prompt.md`, `cg-setup.prompt.md`)
to each carry an incorrect or unhelpful recovery suggestion. When the feature
was first built, these messages were written independently without cross-checking.
Fix pattern: any time you change a "missing X" error message, grep the repo for
all other occurrences of the same missing-X condition and update them atomically.

**Check that recovery commands don't require the precondition they're recovering
from.** See also:
`.cg-docs/solutions/bugs/2026-05-15-circular-error-recovery-command-in-halt-message.md`

## Related

- [2026-05-15-circular-error-recovery-command-in-halt-message.md](2026-05-15-circular-error-recovery-command-in-halt-message.md) — earlier fix that broke the `/cg-wiki rebuild` loop but left no non-destructive init path for existing projects. This bug is the natural follow-on.
