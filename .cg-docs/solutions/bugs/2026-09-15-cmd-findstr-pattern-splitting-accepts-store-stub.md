---
date: 2026-09-15
title: "CMD FINDSTR splits space-separated patterns into ORs, letting the Windows Store stub pass a .cmd launcher probe"
category: "bugs"
type: "bug"
language: "both"
tags: [cmd, findstr, windows, store-stub, python-detection, cg-help, launcher]
root-cause: "FINDSTR treats each space-separated token as a separate alternative pattern, so '^Python [0-9]' matched the Store-stub line 'Python was not found' through the '^Python' alternative instead of rejecting it"
severity: "P1"
plan: ".cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md"
reviewed-in: ".cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md"
related: [".cg-docs/solutions/bugs/2026-06-05-cg-index-cmd-python3-stderr-leak.md", ".cg-docs/solutions/bugs/2026-06-10-cg-brain-init-cmd-python3-stderr-leak.md"]
---

# CMD FINDSTR Splits Space-Separated Patterns Into ORs, Letting the Windows Store Stub Pass a `.cmd` Launcher Probe

## Problem

The `/cg-help` Windows installer gate failed with two current red cases
`rejects absent Python and Store stubs without running them as interpreters
(store-stub)` and `(fallback)` — each `Expected $false, but got $true.`
Evidence: `tests/last-run.json` `ranAt: 2026-09-12T17:39:04Z`, 102 total /
100 passed / 2 failed, `filteredFiles: "install"`, asserted at
`tests/install.Tests.ps1:938`. The Store-stub message `Python was not found`
was accepted by the launcher probe, so the stub flow reached the `-c` probe
and created the forbidden marker. The symptom was invisible in normal
interactive use because a real Python matches both the correct and the
defective probe.

## Root Cause

`bin/cg-help.cmd` probed Python with `findstr /i "^Python [0-9]"`. CMD
`FINDSTR` splits a space-separated pattern list into separate OR
alternatives, so the expression behaved as `"^Python" OR "[0-9]"`. The line
`Python was not found` (emitted by the Windows Store stub instead of a real
interpreter banner) matched the `^Python` alternative. Inert diagnostic
probes proved the split: `cmd.exe /d /c "echo Python was not found|findstr /i
"^Python [0-9]" >nul"` returned 0, while the anchored form
`findstr /i /R /C:"^Python [0-9]"` returned 1. Both forms returned 0 for
`Python 3.8.0` and `Python 3.12.0`; `unrelated 123` returned 0 with the old
form and 1 with the corrected form.

## Solution

Use a single quoted literal regex pattern at all three `bin/cg-help.cmd`
Python probes:

```bat
findstr /i /R /C:"^Python [0-9]" >nul
```

`/C:` treats the whole quoted string as one literal search string, so the
space cannot split it into alternatives. The `where` guards, Python 3.8
minimum, fallback order, `call`, argument forwarding, exit propagation, and
every existing test assertion were preserved. Focused installer gate passed:
`ranAt: 2026-09-12T19:07:56Z`, 102/102, 0 failed; focused bash parity 3/3 at
`2026-09-12T19:14:55Z`. Repaired wrapper object:
`8d75d8b5583c1decd4873d1cddbb95610b7addbb`.

## Prevention

- Always anchor Store-stub rejection probes with verbatim quoted patterns:
  `/i /R /C:"^Python [0-9]"`, never space-separated bare patterns.
- Cross-check all sibling `.cmd` launchers when fixing one: the parity audit
  (Installer Repair Recovery, `2026-09-12T19:03:16Z`) found the same defect
  still present in `bin/cg-brain-init.cmd`, `bin/cg-index.cmd`,
  `bin/cg-kilo.cmd`, `bin/cg-render-artifact.cmd`, `bin/cg-skill.cmd`, and
  `bin/cg-token-audit.cmd`; `bin/cg-publish-markdown.cmd` already used
  `/R /C:`; `bin/cg-link.cmd`, `bin/cg-unlink.cmd`, and `bin/cg-update.cmd`
  delegate to PowerShell and have no CMD Python probes.
- Follow the Windows CMD launcher pattern with the `where` pre-check guard
  and parity rule in
  `.kilo/skills/cg-skill-windows-cmd-python-detection/SKILL.md`.

## Related

- `.cg-docs/solutions/bugs/2026-06-05-cg-index-cmd-python3-stderr-leak.md` — sibling `.cmd` launcher defect (`python3` absent from PATH)
- `.cg-docs/solutions/bugs/2026-06-10-cg-brain-init-cmd-python3-stderr-leak.md` — same launcher family