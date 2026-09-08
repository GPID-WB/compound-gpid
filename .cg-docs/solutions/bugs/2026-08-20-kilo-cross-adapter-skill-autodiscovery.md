---
date: 2026-08-20
title: "Kilo cross-adapter skill auto-discovery resolves linked skills outside project"
category: "bugs"
type: "bug"
language: "both"
tags: [kilo, skills, codex, claude, symlink, junction, trust-boundary, frontmatter, windows, macos]
root-cause: "Kilo auto-discovers compatibility skill roots such as .agents/skills in addition to configured skills.paths; Compound GPID linked those roots to its external installation, and Kilo masked its external markdown refusal as a skill parse UnknownError."
severity: "P1"
test-written: "yes"
fix-confirmed: "yes"
---

# Kilo Cross-Adapter Skill Auto-Discovery

## Symptom

Kilo in VS Code on Windows and Positron on macOS repeatedly reported:

```text
Failed to parse skill <project>/.agents/skills/<name>/SKILL.md
{ name: UnknownError }
```

The same bytes loaded successfully through `.kilo/skills`. MD5, UTF-8/BOM,
line-ending, hand-parser, and strict-YAML checks all passed.

## Root Cause

Kilo scans `.agents/skills` and `.claude/skills` as compatibility sources in
addition to `skills.paths`. Compound GPID intentionally installs Codex and
other adapters with directory links to the global plugin checkout. Kilo
resolved those links outside the project trust boundary and rejected the
markdown read, then surfaced the rejection through its generic parse wrapper.

The Kilo config schema checked on 2026-08-20 supports `skills.paths` and
`skills.urls`, but no `only`, `exclude`, ignore file, or auto-discovery switch.
Kilo source contains `KILO_DISABLE_EXTERNAL_SKILLS`, but that is a process-level
environment flag and cannot be imposed portably by a project plugin in both VS
Code and Positron. `permission.markdown_source` from upstream PR #12846 applies
to explicit external agent/command sources and does not disable compatibility
skill discovery.

## Fix

`cg-link` now activates a structural compatibility layer whenever a managed
`.kilo/skills` copy is installed:

1. Codex, Claude Code, and OpenCode keep their mapped `link-directory`
   strategies. Their public adapter paths remain junctions on Windows and
   symlinks on macOS/Linux.
2. Each installed compatibility skill link is redirected to an
   adapter-specific, checksum-managed copy under
   `.compound-gpid/kilo-compat-skills/<adapter>/`.
3. The mirror preserves adapter-specific generated content. It is not safe to
   point Codex directly at `.kilo/skills` because generated references differ.
4. Every real path Kilo can reach through the compatibility links now stays
   inside the project root. `.kilo/skills` remains a real managed copy.
5. Relinking updates mirrors; unlinking checksum-removes them. Both PowerShell
   and POSIX linkers preserve user edits, reconcile unchanged stale files, and
   write `.compound-gpid-managed-copy.json` markers.
6. Both linkers reject mirror targets or descendants crossing a project-local
   junction/symlink, and unlinkers require exact canonical source/mirror
   ownership rather than a `compound-gpid` path substring.

The generated `.kilo/kilo.json` uses the supported `watcher.ignore` field only
to suppress redundant watcher churn in the mirror backing directory. That key
is not the security fix and does not disable auto-discovery.

## Parser and Content Hardening

The structural fix addresses the live failure. Defensive hardening also:

- parses only the first line-anchored frontmatter block;
- accepts LF, CRLF, BOM+LF, and BOM+CRLF input;
- folds multiline single- and double-quoted scalars containing colons;
- optionally falls back to PyYAML when the lightweight parser misses required
  skill/agent metadata;
- requires LF, no BOM, ASCII frontmatter, and double-quoted descriptions in CI;
- strict-parses every shipped skill under LF, CRLF, and BOM+LF variants.

## Relationship to Prior Art

- `2026-08-06-kilo-agent-skill-parsing-failures.md` established that the UI
  error is a masking wrapper and introduced YAML/encoding hygiene. This fix
  complements that content hardening and supersedes its explanation for the
  recurring cross-adapter skill case.
- `2026-08-11-windows-link-kilo-copy-directory-parse-failure.md` made the native
  `.kilo/*` units project-local copies. This fix complements it: `.kilo/skills`
  already worked, while auto-discovered `.agents/skills` remained external.

## Version Dependency

Keep the mirror workaround while supported Kilo releases auto-discover
compatibility roots and enforce project-scoped markdown realpaths without a
project-level discovery exclusion. Remove it only after an upstream release
provides and documents a portable config switch, then update the generated
`.kilo/AGENTS.md` note and the cross-platform regression tests together.
