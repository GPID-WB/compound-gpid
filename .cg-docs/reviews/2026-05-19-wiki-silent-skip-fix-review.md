---
date: "2026-05-19"
depth: standard
branch: main
files_reviewed:
  - tests/wiki.Tests.ps1
  - docs/_wiki.yml
  - docs/reference.md
  - .github/prompts/cg-compound.prompt.md
  - .github/skills/cg-skill-wiki/SKILL.md
  - compound-gpid.context.md
  - .cg-docs/solutions/bugs/2026-05-19-cg-compound-wiki-update-silently-skipped-all-manual-pages.md
findings:
  P2.1: closed
  P2.2: closed
  P2.3: closed
  P2.4: closed
  P2.5: skipped
  P2.6: closed
  P2.7: fixed
  P2.8: skipped
  P3.1: closed
  P3.2: closed
  P3.3: closed
  P3.4: closed
  P3.5: closed
  P3.6: fixed
  P3.7: fixed
  P3.8: skipped
  P3.9: fixed
  P3.10: closed
  P3.11: skipped
---

# Review: wiki-silent-skip bug fix (2026-05-19)

**Reviewed by**: cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-architecture, cg-reproducibility, cg-performance, cg-data-quality  
**Files changed**: 7 (tests, YAML manifest, wiki reference page, compound prompt, wiki skill, context file, solution doc)

---

## Summary

| Priority | Total | Closed | Open |
|---|---|---|---|
| P2 — IMPORTANT | 8 | 4 | 4 |
| P3 — MINOR | 11 | 7 | 4 |
| **Total** | **19** | **11** | **8** |

---

## P2 Findings — IMPORTANT

### P2.1 — YAML boundary regex in ownership test [CLOSED]
**File**: `tests/wiki.Tests.ps1:698`  
**Agent**: cg-testing  
**Issue**: `reference.md entry has ownership: auto` regex used dotall without a negative lookahead, so it could falsely match across YAML entry boundaries.  
**Fix**: Added `(?:(?!-\s+id:).)*?` non-crossing lookahead. Also fixed sub-entry boundary issue in `managed: true` assertion (simplified to `($ymlContent -match 'managed:\s*true')`).  
**Status**: Closed (autofix applied + tests pass)

### P2.2 — No test for `sections` entry on reference page [CLOSED]
**File**: `tests/wiki.Tests.ps1`  
**Agent**: cg-testing  
**Issue**: Ownership alone is insufficient; `@cg-wiki` uses `sections:` to locate what to write. If that block is removed, auto-writes silently fail.  
**Fix**: Added `It "reference.md entry has a managed sections entry"` with two assertions.  
**Status**: Closed (autofix applied + tests pass)

### P2.3 — No test coverage for Post-init Checklist [CLOSED]
**File**: `tests/wiki.Tests.ps1`  
**Agent**: cg-testing  
**Issue**: No guard means the checklist (primary prevention mechanism for the all-manual bug) can be silently deleted.  
**Fix**: Added `Describe "cg-skill-wiki/SKILL.md - Post-init Checklist is present"` with 3 `It` assertions.  
**Status**: Closed (autofix applied + tests pass)

### P2.4 — `/cg-compound` row hardcodes `wiki/` folder [OPEN]
**File**: `docs/reference.md`  
**Agent**: cg-documentation  
**Issue**: Auto-managed section row says "updates the project wiki (`wiki/`)" but the folder is configured per-project in `compound-gpid.context.md`.  
**Fix**: ~~Already applied as P3.4 (closed).~~ **Note**: P3.4 addressed the sentence but the table row's Command column description may still have residual references. Verify the `/cg-compound` row reads naturally.  
**Status**: Closed via P3.4 — verify

### P2.5 — Working on `main` instead of a feature branch [OPEN]
**File**: n/a  
**Agent**: cg-version-control  
**Issue**: All changes committed directly to `main`. For a wiki-silent-skip bug fix this is acceptable, but advisory.  
**Resolution**: Advisory — acknowledged. No branch created.

### P2.6 — New solution file untracked [CLOSED]
**File**: `.cg-docs/solutions/bugs/2026-05-19-cg-compound-wiki-update-silently-skipped-all-manual-pages.md`  
**Agent**: cg-version-control  
**Issue**: New solution document was untracked (not staged).  
**Fix**: Will be staged in the upcoming commit.  
**Status**: Will be closed at commit time

### P2.7 — Post-init Checklist never emitted by `cg-wiki.agent.md` init [OPEN]
**File**: `.github/agents/cg-wiki.agent.md`  
**Agent**: cg-architecture  
**Issue**: The checklist lives in the skill but neither `cg-wiki.agent.md` nor the `/cg-wiki` prompt dispatches it after `init`. Whether a user sees it depends on the model spontaneously reading to the end of the skill.  
**Fix needed**: Add one line to `cg-wiki.agent.md` init Step 6: "After the report line, emit the Post-init Checklist from `cg-skill-wiki` verbatim."  
**Status**: Open [manual]

### P2.8 — `manual.md` long-term drift risk [OPEN]
**File**: `docs/manual.md`  
**Agent**: cg-architecture  
**Issue**: Manual page (`ownership: "manual"`) may drift from auto-managed content as the plugin evolves.  
**Status**: Open [advisory] — not blocking

---

## P3 Findings — MINOR

### P3.1 — `lastUpdated` stale in `_wiki.yml` [CLOSED]
**Fix**: Updated to `"2026-05-19"`.

### P3.2 — Over-broad `|manual.*page.*user` regex alternation [CLOSED]
**Fix**: Removed from Step 3c test regex — earlier anchored branches are sufficient.

### P3.3 — Verbatim notification template not tested [CLOSED]
**Fix**: Added `It "Step 3c contains the verbatim notification template text"`.

### P3.4 — `wiki/` folder hardcoded in `docs/reference.md` [CLOSED]
**Fix**: Changed to "folder configured via `## Wiki Configuration` in `compound-gpid.context.md`".

### P3.5 — `wiki/<page>.md` hardcoded in skill notification templates [CLOSED]
**Fix**: Changed both occurrences in Conflict Resolution section to `<folder>/<page>.md`.

### P3.6 — Solution doc `language: "both"` ambiguous [OPEN]
**File**: `.cg-docs/solutions/bugs/2026-05-19-...md`  
**Fix needed**: Change to `"n/a"` (prompt/YAML fix, no language-specific code).  
**Status**: Open [advisory]

### P3.7 — `context.md` bullet could reference Post-init Checklist [OPEN]
**Status**: Open [advisory]

### P3.8 — Suggested commit message [OPEN]
```
fix(wiki): promote reference.md to auto-ownership; surface manual-page notifications
```
**Status**: Open [advisory — apply at commit time]

### P3.9 — Step 3c should say "any notifications" not just manual-ownership [OPEN]
**File**: `.github/prompts/cg-compound.prompt.md`  
**Agent**: cg-architecture  
**Fix needed**: Broaden notification surfacing to "any notifications from `@cg-wiki`".  
**Status**: Open [advisory]

### P3.10 — `lastUpdated` stale (duplicate of P3.1) [CLOSED]
**Status**: Closed with P3.1

### P3.11 — Backslash paths in tests (Windows-only) [OPEN]
**Agent**: cg-reproducibility  
**Status**: Open [advisory] — Windows-only project, not blocking

---

## Passed

- `@cg-performance`: No issues found
- `@cg-data-quality`: `_wiki.yml` schema valid — all required fields present, IDs unique, order sequential, sections gated to auto pages only
