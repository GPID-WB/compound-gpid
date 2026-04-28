---
date: 2026-04-24
title: "Multi-day VS Code session (68h) accumulates event listeners — unresponsive freeze and controlled restart"
category: "environment-issues"
language: "both"
tags: [vscode, crash, long-session, listener-leak, environment, copilot, agent, fix-triage, session-management]
root-cause: "A VS Code window left open for 68 hours accumulated enough event listener and memory pressure that the UI became unresponsive, triggering a controlled restart (exit code 0) that interrupted a multi-priority fix-triage session without any data loss"
severity: "P2"
---

# Multi-Day VS Code Session Accumulates Event Listeners — Unresponsive Freeze

## Problem

After a multi-priority fix-triage session (P0→P1→P2→P3) spanning multiple hours,
VS Code became unresponsive and restarted. All in-progress changes were uncommitted.

**Key log evidence** (`main.log`):
```
2026-04-24 11:15:11.247 [error] CodeWindow: detected unresponsive
2026-04-24 11:15:26.734 [info] Extension host with pid 21724 exited with code: 0
2026-04-24 11:15:30.448 [info] Extension host with pid 20084 exited with code: 0
```

The VS Code session had been open since **2026-04-21T15:03:41** — a continuous
**68-hour** window with window12 being the active window at time of crash.

No Pester forbidden patterns appeared in logs. No non-zero exit codes. No
`listener LEAK` entries in `renderer.log`. This was **not** a Pester crash —
it was pure time-based listener accumulation.

## Root Cause

VS Code (Electron/Chromium) accumulates event listeners across the lifetime of
a window. Each terminal spawn, Copilot Chat request, file operation, and extension
activation registers listeners. Most are cleaned up on dispose, but some accumulate
across session boundaries. After 60+ hours, total listener pressure reached a
threshold that made the renderer unresponsive.

Compounding factors:
1. **Session duration**: 68 hours — far beyond the recommended 2–3 hour limit
2. **High agent activity**: Full P0→P1→P2→P3 fix-triage cycle in one session,
   each priority level reading multiple files and running agents
3. **Context compaction**: The conversation was compacted mid-session (token budget
   hit during P3 invocation), indicating the accumulated context was already near limits
4. **Multiple terminal sessions**: Fix-triage runs, git commands, and test verification
   across multiple terminal tabs

The exit code 0 confirms VS Code performed a **controlled restart** (not a hard crash).
All file system writes were complete — no partial edits.

## Solution

This is not a "fix" — it's a prevention pattern. Once the freeze occurs, VS Code
restarts cleanly. Recovery steps:

1. **Check git status** — all uncommitted changes survive the restart (VS Code
   writes files to disk immediately; only unsaved in-memory state is lost)
2. **Verify git diff** — confirm no mid-edit truncations
3. **Run test suite** via `execution_subagent`: `. tests\Run-Tests.ps1`
4. **Resume work** in the new session (use `/cg-resume` if needed)

## Prevention

**Primary**: Restart VS Code every 2–3 hours of intensive agent work.

The warning signs that a restart is overdue:
- Terminal tab count > 10
- Session duration > 3 hours (check log folder timestamps)
- Conversation has been compacted once already
- Fix-triage has run for multiple priority levels in the same session

**Commit cadence**: Commit after each priority level in fix-triage (after P1 complete,
after P2 complete) rather than accumulating all changes into one session. This limits
exposure if a forced restart occurs.

**Session management pattern for long fix-triage cycles**:
```
P0 fixes → commit → (optionally restart VS Code)
P1 fixes → commit → restart VS Code
P2 fixes → commit → restart VS Code
P3 fixes → commit
```

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md`
  — Different cause (Pester output overflow), same symptom (VS Code freeze in long session)
- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md`
  — Pester-specific crash patterns (forbidden pipeline forms)
- `.cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md`
  — Agent rule-slip pattern in long sessions
