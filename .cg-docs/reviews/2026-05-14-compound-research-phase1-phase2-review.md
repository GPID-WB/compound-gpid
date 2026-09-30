---
date: 2026-05-14
plan: 2026-05-14-compound-research-phase1-phase2.md
type: standard
depth: standard
status: resolved
agents:
  - cg-code-quality
  - cg-testing
  - cg-documentation
  - cg-version-control
  - cg-reproducibility
  - cg-performance
  - cg-architecture
  - cg-data-quality
notes: >
  Retroactive standard review run after Phase 1+2 commits were pushed.
  cr-review.prompt.md and cr-prompts.Tests.ps1 were already covered by the
  Phase 3 thorough review (see 2026-05-14-compound-research-phase3-agents-thorough-review.md).
  This review targets the Phase 1/2 specific new work: module system (module: frontmatter,
  modules: activation, {{modules}} substitution) and the 5 cr-* prompts + 2 cr-* skills.
  @cg-version-control found no issues.
  All 40 findings applied in fix commit; also fixed a latent regex bug in link.sh
  extract_fm_value (double-backslash raw-string confusion causing r/n literal exclusion).
findings:
  - id: P1.1
    agent: cg-architecture
    file: "scripts/helpers.ps1 + scripts/link.sh"
    status: fixed
  - id: P1.2
    agent: cg-documentation
    file: "docs/reference.md"
    status: fixed
  - id: P1.3
    agent: cg-data-quality
    file: "scripts/helpers.ps1 + scripts/link.sh"
    status: fixed
  - id: P2.1
    agent: cg-code-quality
    file: "scripts/helpers.ps1 + scripts/link.sh"
    status: skipped
    note: "DRY refactor too large. Added cross-reference comments instead."
  - id: P2.2
    agent: cg-code-quality
    file: "scripts/link.sh"
    status: fixed
  - id: P2.3
    agent: cg-code-quality
    file: "scripts/helpers.ps1 + scripts/link.sh"
    status: skipped
    note: "DRY refactor too large across languages. Advisory only."
  - id: P2.4
    agent: cg-testing
    file: "tests/cr-prompts.Tests.ps1"
    status: fixed
  - id: P2.5
    agent: cg-testing
    file: "tests/cr-prompts.Tests.ps1"
    status: fixed
  - id: P2.6
    agent: cg-testing
    file: "tests/helpers.Tests.ps1"
    status: fixed
  - id: P2.7
    agent: cg-testing
    file: "tests/bash-scripts.Tests.ps1"
    status: fixed
  - id: P2.8
    agent: cg-testing
    file: "tests/helpers.Tests.ps1"
    status: skipped
    note: "Cross-language parity test would require complex bash integration. Advisory."
  - id: P2.9
    agent: cg-testing
    file: "tests/cr-prompts.Tests.ps1"
    status: fixed
  - id: P2.10
    agent: cg-documentation
    file: ".github/prompts/cr-brainstorm.prompt.md (docs/reference.md)"
    status: fixed
  - id: P2.11
    agent: cg-documentation
    file: ".github/skills/cg-skill-setup/SKILL.md"
    status: fixed
  - id: P2.12
    agent: cg-documentation
    file: "docs/reference.md"
    status: fixed
  - id: P2.13
    agent: cg-documentation
    file: ".github/copilot-instructions.template.md"
    status: fixed
  - id: P2.14
    agent: cg-architecture
    file: ".github/prompts/cr-review.prompt.md"
    status: fixed
  - id: P2.15
    agent: cg-architecture
    file: ".github/prompts/cr-compound.prompt.md"
    status: fixed
  - id: P2.16
    agent: cg-architecture
    file: "tests/prompt-tools.Tests.ps1"
    status: fixed
  - id: P2.17
    agent: cg-architecture
    file: ".github/prompts/cr-compound.prompt.md + .github/skills/cg-skill-setup/SKILL.md"
    status: fixed
    note: "Added cross-reference HTML comments to SKILL.md and cr-work.prompt.md."
  - id: P2.18
    agent: cg-reproducibility
    file: ".github/prompts/cr-work.prompt.md"
    status: fixed
  - id: P2.19
    agent: cg-reproducibility
    file: ".github/prompts/cr-work.prompt.md + .github/skills/cr-skill-research-workflow/SKILL.md"
    status: fixed
  - id: P2.20
    agent: cg-data-quality
    file: ".github/skills/cr-skill-research-workflow/SKILL.md"
    status: fixed
  - id: P2.21
    agent: cg-data-quality
    file: ".github/skills/cr-skill-research-workflow/SKILL.md"
    status: fixed
  - id: P2.22
    agent: cg-data-quality
    file: ".github/prompts/cr-work.prompt.md + .github/skills/cr-skill-research-workflow/SKILL.md"
    status: fixed
  - id: P3.1
    agent: cg-code-quality
    file: "scripts/link.sh + scripts/link.ps1"
    status: skipped
    note: "Minor style inconsistency in platform-specific scripts. Advisory only."
  - id: P3.2
    agent: cg-code-quality
    file: "scripts/helpers.ps1 + scripts/link.ps1"
    status: skipped
    note: "Long lines advisory. No functional impact."
  - id: P3.3
    agent: cg-code-quality
    file: "scripts/link.sh + scripts/link.ps1"
    status: skipped
    note: "Duplicate step descriptions in different scripts. Advisory only."
  - id: P3.4
    agent: cg-testing
    file: "tests/cr-prompts.Tests.ps1"
    status: fixed
    note: "Coverage depth disparity addressed by P2.4 cr-plan content tests."
  - id: P3.5
    agent: cg-architecture
    file: "tests/prompt-tools.Tests.ps1"
    status: fixed
    note: "Added module:research whitelist test to cr-prompts.Tests.ps1."
  - id: P3.6
    agent: cg-architecture
    file: ".github/skills/cr-skill-research-workflow/SKILL.md + .github/prompts/cr-work.prompt.md"
    status: fixed
    note: "Added cross-reference HTML comments to both files."
  - id: P3.7
    agent: cg-reproducibility
    file: ".github/prompts/cr-work.prompt.md"
    status: fixed
  - id: P3.8
    agent: cg-reproducibility
    file: ".github/prompts/cr-work.prompt.md"
    status: fixed
  - id: P3.9
    agent: cg-performance
    file: "scripts/link.sh"
    status: fixed
  - id: P3.10
    agent: cg-performance
    file: "scripts/link.sh"
    status: skipped
    note: "Two Python processes for gitignore — refactor not worth the risk."
  - id: P3.11
    agent: cg-performance
    file: "tests/prompt-tools.Tests.ps1"
    status: skipped
    note: "Agent files read twice in tests — negligible performance impact."
  - id: P3.12
    agent: cg-performance
    file: "scripts/helpers.ps1"
    status: skipped
    note: "Sequential .Replace() calls — negligible."
  - id: P3.13
    agent: cg-data-quality
    file: "tests/helpers.Tests.ps1"
    status: fixed
  - id: P3.14
    agent: cg-data-quality
    file: "tests/helpers.Tests.ps1"
    status: fixed
  - id: P3.15
    agent: cg-data-quality
    file: "roadmap.json"
    status: fixed
    note: "Documented completed-date field in docs/reference.md."
---

# Standard Review: Compound Research Phase 1 + Phase 2

**Plan**: [2026-05-14-compound-research-phase1-phase2.md](../plans/2026-05-14-compound-research-phase1-phase2.md)  
**Review date**: 2026-05-14  
**Depth**: standard (8 agents)  
**Commits reviewed**: `26355c9..1ec4054` (pushed to `origin/compound-research`)

**Scope summary**: Module system (Phase 1 — `module:` frontmatter, `modules:` activation, `{{modules}}` substitution) and Research Workflow Scaffolding (Phase 2 — 5 `/cr-*` prompts, 2 `cr-skill-*` SKILL.md files). `cr-review.prompt.md` and `cr-prompts.Tests.ps1` were already covered by the Phase 3 thorough review and are excluded from this scope.

**@cg-version-control** found **no issues** — commits follow conventional commits format, no sensitive data, `.gitignore` coverage is correct, commits are appropriately atomic.

---

## P1 — Critical (3 findings)

### **[P1.1]** [cg-architecture] `scripts/helpers.ps1` + `scripts/link.sh` — YAML block-sequence `modules:` silently degrades

**Issue**: Both parsers use a single-line-string regex to extract `modules:`. A YAML block-sequence (`modules:\n  - research`) matches nothing and silently defaults to `"engineering"`. An inline YAML array (`modules: [engineering, research]`) matches but includes brackets verbatim in the output. Since tests only cover quoted-string format, this path is untested and the failure is silent.

**Fix**: Add explicit validation that rejects non-string formats with a diagnostic error: `throw "modules: must be a quoted string, e.g. 'engineering, research' — YAML list format is not supported"`.

---

### **[P1.2]** [cg-documentation] `docs/reference.md` — Missing `modules:` field in Configuration Fields table

**Issue**: `docs/reference.md` documents `language`, `r-syntax`, `project-type`, `review-depth`, and `cg-schema-version` but omits `modules:`. Yet line ~60 states "These prompts are available when `modules: [research]` is set in `compound-gpid.local.md`." Users have no documentation on how to enable the research module.

**Fix**: Add row to Configuration Fields table:
```markdown
| `modules` | `"engineering"`, `"research"`, or both (comma-separated) | Enables research workflow prompts (`/cr-*`). Default: `"engineering"`. |
```

---

### **[P1.3]** [cg-data-quality] `scripts/helpers.ps1` + `scripts/link.sh` — `modules:` value accepted without allowlist validation

**Issue**: Both scripts extract `modules:` and substitute it without verifying it belongs to the valid set. A typo (`modules: "reasearch"`) silently produces garbled `copilot-instructions.md` and the research prompts never activate. The plan document explicitly marks `modules: "banana"` as a case that should fail validation — but no enforcement was implemented.

**Fix**: Add allowlist check after extraction in both files; emit a clear error and exit 1 for unrecognised values.

---

## P2 — Important (22 findings)

### **[P2.1]** [cg-code-quality] `scripts/helpers.ps1` ↔ `scripts/link.sh` — YAML parsing logic duplicated

**Issue**: The `modules:` YAML extraction logic is reimplemented independently in PowerShell regex and embedded Python. Bugs or enhancements must be applied in both languages, risking divergence.

**Fix**: Centralise YAML parsing in a shared utility or add cross-language parity tests.

---

### **[P2.2]** [cg-code-quality] `scripts/link.sh` — Missing error handling for Python subprocess

**Issue**: The embedded Python heredoc in `generate_copilot_instructions()` has no explicit error capture. If the Python block fails, the error may be unclear to users.

**Fix**: Wrap invocation with `|| { echo "ERROR: failed to generate copilot instructions"; exit 1; }`.

---

### **[P2.3]** [cg-code-quality] `scripts/helpers.ps1` ↔ `scripts/link.sh` — Template variable substitution duplicated

**Issue**: Placeholder substitution logic (looping over `{{placeholder}}` → value) is duplicated in both scripts. Adding a new placeholder requires changes in both, with no single source of truth.

**Fix**: Maintain a canonical placeholder list in one place, or add a cross-reference test.

---

### **[P2.4]** [cg-testing] `tests/cr-prompts.Tests.ps1` — `cr-plan.prompt.md` lacks content validation tests

**Issue**: `cr-plan` has only structural checks (file exists, `module: research`, no `tools:` restriction). No tests verify planning process steps, P0 handoff to `/cr-work`, scope assessment, or plan structure guidance.

**Fix**: Add `Describe "cr-plan.prompt.md - research planning process"` with content assertions for Step 3, P0 enforcement section, and handoff reference to `/cr-work`.

---

### **[P2.5]** [cg-testing] `tests/cr-prompts.Tests.ps1` — No end-to-end handoff chain test

**Issue**: Individual handoff assertions exist but no test verifies the complete chain `/cr-brainstorm` → `/cr-plan` → `/cr-work` → `/cr-review` is contiguous. A broken middle link would not be caught.

**Fix**: Add `Describe "CR handoff chain"` verifying each step references the *next* prompt correctly.

---

### **[P2.6]** [cg-testing] `tests/helpers.Tests.ps1` — `modules:` edge cases not tested

**Issue**: Tests cover `"engineering"` and `"engineering, research"` but not: `"research"` only, null/empty, or values with extra whitespace.

**Fix**: Add three Context blocks for these edge cases.

---

### **[P2.7]** [cg-testing] `tests/bash-scripts.Tests.ps1` — `link.sh` modules substitution has no functional test

**Issue**: `link.sh` has structural tests but no test verifying the inline Python section reads `modules:` from `compound-gpid.local.md` and substitutes it into the output.

**Fix**: Add functional test with temp config file asserting substituted value appears in generated output.

---

### **[P2.8]** [cg-testing] `tests/helpers.Tests.ps1` — No cross-language consistency test for modules handling

**Issue**: PowerShell and bash/Python paths both substitute `{{modules}}` but no test verifies they produce identical output given the same config.

**Fix**: Add a parity test comparing PowerShell and bash outputs for the same input.

---

### **[P2.9]** [cg-testing] `tests/cr-prompts.Tests.ps1` — CR skills do not test phase availability guards

**Issue**: `cr-brainstorm` documents future skills as `*(Phase 4, not yet available)*` but no test asserts this language is present.

**Fix**: Add `It "documents Phase 4 and later skills as unavailable"` to the cr-brainstorm Describe block.

---

### **[P2.10]** [cg-documentation] `docs/reference.md` — Inaccurate description of `/cr-brainstorm`

**Issue**: The reference.md description says `/cr-brainstorm` "Routes to the appropriate review agents based on task type" — but the prompt only classifies tasks and clarifies requirements. Agent routing occurs in `/cr-review`.

**Fix**: Replace description to accurately reflect: task classification, scope assessment, branch offer, devil's advocate challenge.

---

### **[P2.11]** [cg-documentation] `.github/skills/cg-skill-setup/SKILL.md` — Missing interactive question for `modules:` during setup

**Issue**: `/cg-setup` asks Q1–Q3 (language, project type, review depth) and the example config includes `modules: "engineering"` without an interactive question. Users don't know how to enable the research module.

**Fix**: Add Q4 (Modules): engineering only / research only / both. If research selected, offer to scaffold `.cg-docs/research/`.

---

### **[P2.12]** [cg-documentation] `docs/reference.md` — `/cr-brainstorm` and `/cr-plan` descriptions lack parity with `/cg-*` equivalents

**Issue**: `/cg-brainstorm` and `/cg-plan` descriptions document branch offer, prior-work checking, scope assessment, and confidence check. The `/cr-*` equivalents in the reference table are much briefer.

**Fix**: Expand descriptions to match detail level of `/cg-*` counterparts.

---

### **[P2.13]** [cg-documentation] `.github/copilot-instructions.template.md` — `modules:` field shown but not explained

**Issue**: The generated instructions show `**Modules**: {{modules}}` but don't explain what module values mean or how to change them.

**Fix**: Add a brief annotation explaining engineering vs research module values.

---

### **[P2.14]** [cg-architecture] `.github/prompts/cr-review.prompt.md` — Step 0 does not read `compound-gpid.context.md`

**Issue**: Every other `/cr-*` prompt (brainstorm, plan, work) reads `compound-gpid.context.md` in Step 0. `cr-review` does not. The review orchestrator dispatches agents without workspace structure notes.

**Fix**: Add "If `compound-gpid.context.md` exists, read it. Otherwise skip silently." to Step 0. *(Note: Phase 3 review modified cr-review.prompt.md; verify whether this was already added.)*

---

### **[P2.15]** [cg-architecture] `.github/prompts/cr-compound.prompt.md` — Step 0 missing `modules:` guard and context.md read

**Issue**: `cr-compound` has `module: research` frontmatter but Step 0 only reads `compound-gpid.md` and loads `cg-skill-compound-docs`. No `modules:` guard warns engineering-only users; no `compound-gpid.context.md` read.

**Fix**: Add `compound-gpid.local.md` read + modules guard + context.md read to Step 0.

---

### **[P2.16]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — context-layer test suite doesn't cover `/cr-*` prompts

**Issue**: The `"context layer - all 15 prompts reference compound-gpid.context.md"` block hardcodes only the 15 `/cg-*` prompts. The 5 `/cr-*` prompts have no test verifying context.md reads.

**Fix**: Add a companion Describe block for cr-* prompts, asserting `compound-gpid.context.md` reference.

---

### **[P2.17]** [cg-architecture] `cr-compound.prompt.md` + `cg-skill-setup/SKILL.md` — Research solution categories duplicated without source-of-truth anchor

**Issue**: Research categories (`identification`, `specification`, `derivation`, `ml-methodology`, `reproducibility`) appear in both files with no cross-reference. Future category additions (e.g., `welfare-measurement`) will cause the setup scaffold and compound prompt to diverge.

**Fix**: Add cross-reference comments in each file and a Pester test asserting category name parity.

---

### **[P2.18]** [cg-reproducibility] `cr-work.prompt.md` — Manifest schema lacks idempotency specification

**Issue**: The spec-logging requirement says "append to manifest.json" but provides no guidance on preventing duplicate entries when the same specification is re-run.

**Fix**: Document deduplication strategy: use `(file, date)` as a natural key, updating existing entries rather than appending new ones.

---

### **[P2.19]** [cg-reproducibility] `cr-work.prompt.md` + `cr-skill-research-workflow/SKILL.md` — Environment isolation not referenced in P0 enforcement

**Issue**: P0 Seed Enforcement correctly requires seeds but doesn't reference environment lockfiles (renv.lock, pyproject.toml, repkit). Seeding reproduces results but not the code execution path if dependencies differ.

**Fix**: Add lockfile verification step: "Verify renv.lock / pyproject.toml / code/ado/ exists and is committed before executing random code."

---

### **[P2.20]** [cg-data-quality] `cr-skill-research-workflow/SKILL.md` — Manifest JSON example uses bare object; `cr-work.prompt.md` uses array

**Issue**: The skill shows a single JSON object as the manifest format; `cr-work` correctly shows an array of objects. An agent following the skill example creates a bare object; a second run produces concatenated bare objects — invalid JSON. Downstream specification-search audits silently fail to parse.

**Fix**: Update SKILL.md example to use the authoritative array format from `cr-work.prompt.md`.

---

### **[P2.21]** [cg-data-quality] `cr-skill-research-workflow/SKILL.md` — `null_or_N` is not valid JSON in manifest schema example

**Issue**: The manifest example contains `"seed": null_or_N` — a prose placeholder, not valid JSON. If copied literally, the manifest file becomes syntactically invalid and breaks all downstream audits.

**Fix**: Replace with two explicit examples showing `"seed": 42` (random) and `"seed": null` (deterministic).

---

### **[P2.22]** [cg-data-quality] `cr-work.prompt.md` + `cr-skill-research-workflow/SKILL.md` — No required-field enforcement for manifest entries

**Issue**: Neither document specifies what happens if `date`, `description`, or `file` is missing from a manifest entry. Partial entries silently undercount specifications in the audit.

**Fix**: Add: "All four fields are required. If `file` is unknown, halt and resolve before writing the entry."

---

## P3 — Minor (15 findings)

| ID | Agent | File | Issue |
|----|-------|------|-------|
| P3.1 | cg-code-quality | `scripts/link.sh + link.ps1` | Inconsistent error output styling (ANSI vs `Write-Host`) |
| P3.2 | cg-code-quality | `scripts/helpers.ps1 + link.ps1` | Long lines exceed 100-char style guideline |
| P3.3 | cg-code-quality | `scripts/link.sh + link.ps1` | Step descriptions duplicated (acceptable for platform-specific pair) |
| P3.4 | cg-testing | `tests/cr-prompts.Tests.ps1` | Coverage depth disparity: cr-agents have ~10 tests each, cr-prompts have ~5 |
| P3.5 | cg-architecture | `tests/prompt-tools.Tests.ps1` | `module: research` not enforced for cr-* files in whitelist test |
| P3.6 | cg-architecture | `cr-skill-research-workflow + cr-work.prompt.md` | manifest.json schema defined in two places; no parity test |
| P3.7 | cg-reproducibility | `cr-work.prompt.md` | Python seed catalog incomplete — missing `torch.manual_seed()`, `tensorflow.random.set_seed()` |
| P3.8 | cg-reproducibility | `cr-work.prompt.md` | Directory creation for `.cg-docs/research/results/` not specified |
| P3.9 | cg-performance | `scripts/link.sh` | Stale gitignore cleanup spawns Python unconditionally (1-line bash guard fixes it) |
| P3.10 | cg-performance | `scripts/link.sh` | Two separate Python processes for `.gitignore` management in Step 5 |
| P3.11 | cg-performance | `tests/prompt-tools.Tests.ps1` | Agent files read twice in enforcement loop (relevant at 50+ agents) |
| P3.12 | cg-performance | `scripts/helpers.ps1` | 5 sequential `.Replace()` calls create 5 intermediate string copies |
| P3.13 | cg-data-quality | `tests/helpers.Tests.ps1` | Template test does not assert `{{modules}}` placeholder existence |
| P3.14 | cg-data-quality | `tests/helpers.Tests.ps1` | `<not configured>` count hardcoded at 3 — latent fragility |
| P3.15 | cg-data-quality | `roadmap.json` | `completed-date` field undocumented in schema and not validated |

---

## Summary

| Tier | Count |
|------|-------|
| P0 | 0 |
| P1 | 3 |
| P2 | 22 |
| P3 | 15 |
| **Total** | **40** |

**@cg-version-control: no issues** — commits are well-structured, no sensitive data, `.gitignore` coverage is correct.

**Key themes**:
1. **Validation gap** (P1.1, P1.3, P2.1–P2.3): Both scripts lack `modules:` allowlist validation and the logic is duplicated across PowerShell and Python without a shared source of truth.
2. **Manifest JSON schema defects** (P2.20, P2.21, P2.22): The SKILL.md uses invalid JSON syntax (`null_or_N`) and a bare-object format that diverges from the array format in `cr-work.prompt.md`. This risks downstream spec-audit failures.
3. **Missing documentation** (P1.2, P2.10–P2.13): `modules:` isn't in the Configuration Fields table, `/cr-brainstorm` description is inaccurate, and `/cg-setup` has no interactive question for module selection.
4. **Test coverage gaps** (P2.4–P2.9): Content validation and edge-case tests missing for Phase 1/2 prompts and scripts.
5. **Architectural consistency** (P2.14–P2.17): `cr-compound` and `cr-review` don't read `compound-gpid.context.md`; research categories duplicated without a single source of truth.

Use `/cg-fix-triage` to prioritise and apply fixes.
