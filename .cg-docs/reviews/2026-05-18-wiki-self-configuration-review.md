---
date: 2026-05-18
scope: uncommitted changes — docs/ wiki self-configuration bug fix
depth: thorough
mode: autofix
files-reviewed:
  - compound-gpid.context.md
  - docs/workflow.md
  - tests/wiki.Tests.ps1
  - docs/_wiki.yml
  - .cg-docs/solutions/bugs/2026-05-18-compound-gpid-repo-not-wired-as-wiki-consumer.md
agents: [cg-code-quality, cg-testing, cg-documentation, cg-version-control, cg-adversarial, cg-learnings-researcher, cg-reproducibility, cg-performance, cg-architecture, cg-data-quality]
total-findings: 24
applied-safe-auto: 8
open-manual: 6
open-advisory: 10
test-result-before: 1777/1777
test-result-after: 1782/1782
findings:
  - id: R-2026-05-18-001
    priority: P1
    tag: manual
    agent: cg-adversarial
    file: docs/_wiki.yml
    description: "path traversal in file: entries — no guard, agent can escape docs/ sandbox"
    status: fixed
  - id: R-2026-05-18-002
    priority: P2
    tag: safe_auto
    agent: cg-testing/cg-adversarial/cg-learnings-researcher
    file: tests/wiki.Tests.ps1
    description: "_wiki.yml Describe block: existence-only — schema content unvalidated"
    status: applied
  - id: R-2026-05-18-003
    priority: P2
    tag: safe_auto
    agent: cg-adversarial
    file: tests/wiki.Tests.ps1
    description: "non-circular guard window {0,120} too narrow — expanded to {0,500}"
    status: applied
  - id: R-2026-05-18-004
    priority: P2
    tag: safe_auto
    agent: cg-architecture
    file: tests/wiki.Tests.ps1
    description: "no test for agent discard-folder pre-flight rule"
    status: applied
  - id: R-2026-05-18-005
    priority: P3
    tag: safe_auto
    agent: cg-architecture
    file: tests/wiki.Tests.ps1
    description: "no drift-detection test between context.md and _wiki.yml folder values"
    status: applied
  - id: R-2026-05-18-006
    priority: P2
    tag: safe_auto
    agent: cg-documentation
    file: docs/workflow.md
    description: "When NOT to use: direct _wiki.yml edit guidance omits /cg-wiki restructure"
    status: applied
  - id: R-2026-05-18-007
    priority: P3
    tag: safe_auto
    agent: cg-documentation
    file: docs/workflow.md
    description: "Output wording implies _wiki.yml is outside wiki folder"
    status: applied
  - id: R-2026-05-18-008
    priority: P2
    tag: safe_auto
    agent: cg-documentation
    file: docs/workflow.md
    description: "Setup **Output** line missing _wiki.yml"
    status: applied
  - id: R-2026-05-18-009
    priority: P3
    tag: safe_auto
    agent: cg-documentation
    file: compound-gpid.context.md
    description: "Wiki Configuration HTML comment directives undocumented as machine-parsed"
    status: applied
  - id: R-2026-05-18-010
    priority: P2
    tag: manual
    agent: cg-version-control
    file: "(git staging)"
    description: "Untracked files docs/_wiki.yml and bug doc must be git-added before commit"
    status: skipped
  - id: R-2026-05-18-011
    priority: P2
    tag: manual
    agent: cg-adversarial/cg-learnings-researcher
    file: tests/wiki.Tests.ps1
    description: "injection scan test SYSTEM:|Ignore|Override|Forget is common-word false positive — anchor to context"
    status: fixed
  - id: R-2026-05-18-012
    priority: P2
    tag: manual
    agent: cg-learnings-researcher
    file: tests/wiki.Tests.ps1
    description: "[Nn]ested and code block|fenced code alternations are common-word false positives"
    status: fixed
  - id: R-2026-05-18-013
    priority: P2
    tag: manual
    agent: cg-architecture
    file: docs/_wiki.yml + cg-wiki.agent.md
    description: "Dual folder declaration — agent silently discards _wiki.yml.folder with no user warning"
    status: fixed
  - id: R-2026-05-18-014
    priority: P2
    tag: manual
    agent: cg-adversarial
    file: compound-gpid.context.md
    description: "folder directive path-traversal — no negative test for .. in folder value"
    status: fixed
  - id: R-2026-05-18-015
    priority: P3
    tag: manual
    agent: cg-learnings-researcher
    file: tests/wiki.Tests.ps1
    description: "workflow loop assertion too broad — anchor to ### 6b. Wiki heading"
    status: fixed
---

# Review: Wiki Self-Configuration Bug Fix

**Date**: 2026-05-18  
**Scope**: uncommitted changes from `fix/compound-gpid-repo-not-wired-as-wiki-consumer`  
**Depth**: thorough (10 agents)  
**Mode**: autofix  
**Test result**: 1,782/1,782 ✅ (was 1,777 before safe_auto fixes added 5 new tests)

---

## Summary

86 insertions / 4 deletions across 3 tracked modified files + 2 untracked new files. No P0 findings. One P1 [manual] finding (path traversal in `_wiki.yml` file entries). 8 safe_auto fixes applied automatically. 6 manual findings remain open.

---

## P1 — Critical (Manual Review Required)

### R-2026-05-18-001 [manual] `docs/_wiki.yml` — path traversal in `file:` entries
**Agent**: cg-adversarial  
**Why**: `file:` entries accept path traversal values (e.g. `../../compound-gpid.md`). The agent constructs paths as `{folder}/{file}` — a crafted entry could escape the docs/ sandbox and overwrite protected files (charter, roadmap.json).  
**Proof**: Replace `file: "installation.md"` with `file: "../../roadmap.json"` — agent processes the roadmap as a wiki page.  
**Fix**: Add assertions to `tests/wiki.Tests.ps1` validating that every `file:` value matches `^[^./][^/]*\.md$` (filename-only, no slashes, no `..`). Mirror as a validation rule in `cg-skill-wiki/SKILL.md`.

---

## P2 — Important

### R-2026-05-18-002 [safe_auto ✅] `tests/wiki.Tests.ps1` — _wiki.yml schema unvalidated
**Applied**: Added 3 content assertions: schemaVersion, folder, pages.

### R-2026-05-18-003 [safe_auto ✅] `tests/wiki.Tests.ps1` — non-circular guard window too narrow
**Applied**: Expanded `{0,120}` → `{0,500}` in the negative assertion.

### R-2026-05-18-004 [safe_auto ✅] `tests/wiki.Tests.ps1` — no discard-folder pre-flight test
**Applied**: Added `It "pre-flight discards _wiki.yml folder field in favor of context.md value"`.

### R-2026-05-18-006 [safe_auto ✅] `docs/workflow.md` — When NOT to use: omits /cg-wiki restructure
**Applied**: Updated bullet to reference `/cg-wiki restructure` as the preferred path.

### R-2026-05-18-008 [safe_auto ✅] `docs/workflow.md` — Setup Output missing _wiki.yml
**Applied**: Appended `+ \`_wiki.yml\` (if wiki is initialized)`.

### R-2026-05-18-010 [manual] git staging — untracked files must be explicitly staged
**Fix**: Run `git add docs/_wiki.yml ".cg-docs/solutions/bugs/2026-05-18-compound-gpid-repo-not-wired-as-wiki-consumer.md"` before committing.

### R-2026-05-18-011 [manual] `tests/wiki.Tests.ps1` — injection scan false positive
**Agent**: cg-adversarial, cg-learnings-researcher  
**Why**: `SYSTEM:|Ignore|Override|Forget` matches any agent file containing these words in normal prose. Test passes even if the injection scan rule is deleted.  
**Fix**: Scope to injection-scan context: `($content -match 'Injection scan[\s\S]{0,400}SYSTEM:') | Should -Be $true`

### R-2026-05-18-012 [manual] `tests/wiki.Tests.ps1` — `[Nn]ested` and `code block|fenced code` false positives
**Agent**: cg-learnings-researcher  
**Why**: Per `2026-05-15-common-word-regex-false-positive-in-security-assertions.md`, both patterns are permanently green regardless of the tested rule's presence.  
**Fix**: Anchor to the rule context (see cg-learnings-researcher finding P2.2 for exact regexes).

### R-2026-05-18-013 [manual] `cg-wiki.agent.md` — dual folder declaration, no user warning on mismatch
**Agent**: cg-architecture  
**Why**: Agent silently discards `_wiki.yml.folder` with no diagnostic. Users editing `_wiki.yml` directly would get a silent no-op and have no path to diagnosis.  
**Fix**: Add a conflict-detection step in pre-flight step 3: if `_wiki.yml.folder` is present and differs from context.md resolved folder, emit an informational note. Also update SKILL.md to mark `folder` as informational.

### R-2026-05-18-014 [manual] `compound-gpid.context.md` + `cg-skill-wiki` — no path-traversal guard on folder directive
**Agent**: cg-adversarial  
**Why**: A crafted `<!-- folder: docs/../../../sensitive -->` value could be extracted and used as a wiki path. The test validates the literal value `docs` but doesn't validate the extraction regex's safety in consumer projects.  
**Fix**: Add negative assertion: `($content -match '<!--\s*folder:\s*[^-]*\.\.[^-]*-->') | Should -Be $false`. Document in SKILL.md: reject extracted folder values containing `..` or absolute paths.

---

## P3 — Minor

### R-2026-05-18-005 [safe_auto ✅] `tests/wiki.Tests.ps1` — no drift-detection test
**Applied**: Added `Describe "docs/_wiki.yml - folder matches compound-gpid.context.md declaration"` with regex extraction and comparison.

### R-2026-05-18-007 [safe_auto ✅] `docs/workflow.md` — Output wording about _wiki.yml
**Applied**: Clarified "including the updated `_wiki.yml` manifest inside that folder."

### R-2026-05-18-009 [safe_auto ✅] `compound-gpid.context.md` — directives undocumented
**Applied**: Added prose line explaining HTML comment directives are machine-parsed.

### R-2026-05-18-015 [manual] `tests/wiki.Tests.ps1` — workflow loop assertion too broad
**Agent**: cg-learnings-researcher  
**Fix**: Add `($content -match '(?m)^###\s+6b\.\s+Wiki') | Should -Be $true` as a second assertion.

### Advisory findings (informational only)
- [P2.1 cg-code-quality]: workflow test `($content -match '/cg-wiki')` too broad
- [P3.1 cg-code-quality]: no cross-validation test for folder values (addressed by R-005)
- [P3.2 cg-version-control]: direct commit to main (consider branching)
- [P3.3 cg-documentation]: section numbering 6/6b/6c — 6a absent, pre-existing pattern
- [P3.3 cg-documentation]: all pages manual → rebuild auto-dispatch is silent no-op on content
- [P3.4 cg-documentation]: bug doc has `{ ... }` placeholders in Reproduction Test
- [P2.1 cg-reproducibility]: `lastUpdated` will go stale — ensure @cg-wiki update always refreshes it
- [P2.4 cg-reproducibility]: bi-directional alternation in bypass guard test
- [P3.1 cg-performance]: ~21 redundant Get-Content calls across Describe blocks (negligible)
- [P3.2 cg-architecture]: `folder` field in `_wiki.yml` is self-referential — consider removing in v2

---

## Applied Fixes (8 total)

| # | File | Change |
|---|------|--------|
| 1 | `tests/wiki.Tests.ps1` | Added 3 schema assertions to `_wiki.yml` Describe block |
| 2 | `tests/wiki.Tests.ps1` | Added drift-detection Describe block (context.md ↔ _wiki.yml) |
| 3 | `tests/wiki.Tests.ps1` | Expanded non-circular guard window: `{0,120}` → `{0,500}` |
| 4 | `tests/wiki.Tests.ps1` | Added `It "pre-flight discards _wiki.yml folder field"` to security rules block |
| 5 | `docs/workflow.md` | When NOT to use: reference `/cg-wiki restructure` as preferred path |
| 6 | `docs/workflow.md` | Output: clarify `_wiki.yml` lives inside the wiki folder |
| 7 | `docs/workflow.md` | Setup Output: append `+ \`_wiki.yml\`` |
| 8 | `compound-gpid.context.md` | Add prose line explaining machine-parsed directives |
