---
description: "Run multi-agent code review on recent changes. Produces prioritized P0/P1/P2/P3 findings."
---

<!-- Review agents dispatched by this prompt (update this list when adding/removing agents):
     cg-code-quality, cg-testing, cg-documentation, cg-version-control,
     cg-reproducibility, cg-performance, cg-architecture, cg-data-quality,
     cg-learnings-researcher, cg-adversarial
     Note: the 'agents:' frontmatter key is only functional in .agent.md files,
     not in .prompt.md files — keep this list here as documentation only. -->

# Review

You are a review orchestrator that coordinates multiple specialized review agents to analyze code changes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` (objective, constraints, current focus). If missing, warn the user: "No project charter found. Run `/cg-setup` to create one. Proceeding without project context."
2. Read `compound-gpid.local.md` (language, project type, review depth).
3. Load `.github/shared/context-loading.contract.md` and apply Stage 0/1/2 first. Do not read full `compound-gpid.context.md` by default; skip silently if absent. If changed files intersect documented project conventions, data sources, or workspace notes, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
4. Parse mode flags from the user's invocation: identify any `--report-only`, `mode:verify`, `mode:autofix`, staged review modes (`light`, `standard`, `data-risk`, `architecture`, `full`), and backward-compatible `thorough`. Record for use in Step 1 and Step 2 dispatches before any file reads or tool dispatch. If `--no-brain` is present, set `brain-enabled = false`. Otherwise set `brain-enabled = true`.

### Step 1: Determine Scope

1. Use review depth from `compound-gpid.local.md`. If no config, default to `standard`.
2. Identify changed files (use git diff or ask the user).
  Treat `.cg-docs/views/**` as generated derived outputs: list paths and counts
  only; never read view bodies, full content, or HTML diffs into agent context.
  Review the canonical Markdown, renderer code, tests, and one-file
  `cg-render-artifact --check <source>` freshness result instead. A generated
  view may orient a human reader but never supplies review authority.
3. Read `.github/shared/review-routing.contract.md`; it is the canonical source for staged review modes, risk classes, precedence, and additive dedup.
4. Apply flags parsed at Step 0 (case-insensitive) — semantic reference:
   - `--report-only` — Disable autofix; present findings one-at-a-time for Fix/Skip/Discuss (see Step 4).
   - `mode:autofix` — No-op: autofix is now the default. Accepted without warning for backward compatibility.
   - `mode:verify` — Enable verification mode (see Step 1.7). Locates the most recent review file with fixed findings and passes prior context to agents with a suppression policy. Forces `light` depth.
   - `light`, `standard`, `data-risk`, `architecture`, `full` — Explicit staged review modes.
   - `thorough` — Backward-compatible alias; maps to `full` dispatch semantics unless `mode:verify` or `--report-only` guard behavior constrains the run.
   If unrecognized, warn: "Unrecognized argument '<arg>' — ignoring. Recognized: `--report-only`, `mode:autofix`, `mode:verify`, `light`, `standard`, `data-risk`, `architecture`, `full`, `thorough`, `--no-brain`."
   `--report-only` and `mode:verify` are mutually exclusive. If both are passed, warn: "Cannot combine `--report-only` and `mode:verify` — using `mode:verify`." and ignore `--report-only`.

   **Default**: autofix is ON unless `--report-only` or `mode:verify` is passed. Always include tagging instructions (`[safe_auto]`/`[manual]`/`[advisory]`) in each agent dispatch at Step 2, unless `--report-only` or `mode:verify` is active.

### Step 1.3: Consult Brain

If `brain-enabled = false`, skip this step.

Load `cg-skill-brain-query`. Search the brain for: known mistakes and
anti-patterns documented for the file types and domains being reviewed,
past review findings in similar code areas, patterns that reviewers should
verify. Pass relevant findings to review agents as additional context.

### Step 1.5: Deterministic Preflight Risk-Class Routing

If `mode:verify` was passed, first build verification context using Step 1.7. If Step 1.7 disables verify mode because no prior fixed review exists, continue normal routing in this step. If verify mode remains active, skip the rest of Step 1.5 because Step 1.7 enforces light-only depth and disables staged broad routing.

If no changed files are detected or the changed-file scope is unclear, ask the user for the scope and do not silently broad default dispatch.

Use deterministic preflight routing from `.github/shared/review-routing.contract.md`:

| Trigger | Internal risk class | Resolved mode |
|---------|---------------------|---------------|
| Docs-only, comments-only, small prompt wording, metadata-only, or low-risk tests | `low` | `light` |
| Ordinary implementation, prompt, or test changes without high-risk signals | `normal` | `standard` |
| Statistical, survey, poverty, welfare, income, weights, joins, aggregation, summary tables, model estimation (`fmean`, `fsum`, `fgini`, `svymean`, `reghdfe`, `lm`, etc.), reproducibility-sensitive scripts, or scripts matching `**/pipeline*.{R,py}`, `**/extract*.{R,py}`, `**/load*.{R,py}` | `data-risk` | `data-risk` |
| Architecture, dependency, module boundary, performance, memory, concurrency, API contract, or large refactor changes | `architecture-risk` | `architecture` |
| Auth, secrets, credentials, tokens, permissions, release automation, publishing, install/update paths, linking/unlinking paths, schema changes, or destructive filesystem behavior | `security-risk` | `full` |

Precedence: verify/report-only guard behavior first; otherwise explicit user mode wins (`full`, `thorough` = `full`, `data-risk`, `architecture`, `standard`, `light`), then auto risk-class routing, then line-volume escalation, then config default. Resolve exactly one route.

Auto risk-class routing applies only when no explicit mode is requested. If a user requests `light` or `standard` for a diff that matches `data-risk`, `architecture-risk`, or `security-risk`, keep the explicit route and mention the high-risk signals in the review focus. If a user requests `full` for a low-risk diff, keep `full`.

Line-volume interaction:
- ≥ 50 non-test lines changed can raise `light -> standard`.
- Explicit user modes take precedence over line-volume upgrades.
- ≥ 200 non-test lines changed with no higher-risk trigger should resolve to `full` only when the user explicitly requested `full`/`thorough`; otherwise recommend: "This is a large change. Consider running `/cg-review full` for `@cg-adversarial` coverage."

If no explicit mode was requested and multiple auto-routing triggers apply, choose the highest resolved mode by coverage and apply additive dedup: if multiple rules request the same agent, dispatch once. If any auto risk-class route applies, report: > "Auto-routing applied: [reason]. Resolved review mode: [mode]. Mandatory emphasis: [agent/domain focus]."

### Step 1.7: Build Verification Context (mode:verify only)

Skip this step unless `mode:verify` was passed.

1. Scan `.cg-docs/reviews/` for the most recent file whose name ends in `-review.md` but NOT in `-verify-review.md` (by `date:` frontmatter, then alphabetically last filename — lexicographically greater wins), where the `findings:` map contains at least one `fixed` entry. If `date:` is absent, treat the file as oldest (sort last). If `findings:` is absent or not a map, treat as no `fixed` entries — skip the file. If none found: warn "No prior review with fixed findings found. Falling back to normal review." and disable verify mode.
2. Read the prior review file. Extract:
   - The list of finding IDs and their statuses (`fixed`, `skipped`, `open`).
   - The full relative path to the review file (e.g., `.cg-docs/reviews/2026-04-21-foo-review.md`) for linking the verify review via `parent-review:` frontmatter (see Step 3.5).
3. Build the **suppression context** — a text block passed to every agent in Step 2:

   > **Verification mode**: This is a verify pass following fix-triage.
   > The prior review file is `<filename>` with these resolved findings:
   > \<list of fixed finding IDs and one-line descriptions\>.
   >
   > **Suppression policy**:
   > - **P0/P1**: Always report. Never suppress correctness, security, or data-integrity issues regardless of whether the code was written as a fix.
   > - **P2/P3 on fixed-finding scope**: Suppress a P2/P3 only when the finding targets a function or block whose refactoring was explicitly listed as `fixed` in the prior review's `findings:` map (the list above). Do not suppress based on inference that code looks like a fix or was written recently — only the explicit `fixed` list is an authoritative anchor.
   > - **Cross-file breakage**: Always report, at any severity. If a fix in file A broke a reference, import, or contract in file B, that is a genuine new issue.
   > - **When in doubt, report**: If unsure whether a finding is within the scope of a `fixed` entry, report it. False positives are cheaper than missed bugs.

4. Force depth to `light` (override any config or argument).

### Step 2: Dispatch Agents

Based on the resolved staged mode from Step 1.5 and `.github/shared/review-routing.contract.md`, invoke only the route-appropriate agents on the changed files:

**Light** (quick fixes, small low-risk changes):
- `@cg-code-quality` — Style, linting, DRY, naming
- `@cg-testing` — Test coverage, edge cases, quality

**Standard** (normal risk):
- `@cg-code-quality` — Style, linting, DRY, naming
- `@cg-testing` — Test coverage, edge cases, quality
- `@cg-documentation` — roxygen2/docstrings/do-file headers, README, comments
- `@cg-version-control` — Commit hygiene, branching, .gitignore, secrets
- `@cg-reproducibility` — Lockfiles, relative paths, seeds
- `@cg-performance` — Vectorization, memory, algorithm complexity
- `@cg-architecture` — Project structure, modularity, dependencies
- `@cg-data-quality` — Input validation, types, missing values

**Data-risk** (statistical, survey, poverty, welfare, joins, aggregation, reproducibility-sensitive changes):
- All 8 agents from `standard` with mandatory escalation emphasis for `@cg-data-quality`, `@cg-reproducibility`, and `@cg-testing`

**Architecture** (architecture-risk or performance-heavy changes):
- All 8 agents from `standard` with mandatory escalation emphasis for `@cg-architecture`, `@cg-performance`, and `@cg-testing`

**Full** (explicit full/thorough request, security-risk, release-risk, linking-risk, schema-risk, or very high-risk changes):
- All 8 agents from `standard`
- `@cg-learnings-researcher` — Cross-references `.cg-docs/solutions/` and `.cg-docs/brainstorms/` for relevant past learnings
- `@cg-adversarial` — Actively tries to break the code: edge cases, data corruption vectors, security vulnerabilities

Users can explicitly request `full` review at any time. `thorough` remains accepted and maps to full dispatch for backward compatibility.

Do not dispatch broad full review for small or low-risk changes unless an explicit user mode or high-risk trigger requires it.

**Global agent constraint**: Include with every agent dispatch: "Never recommend deleting, replacing, renaming, or moving these files: `.cg-docs/brainstorms/`, `.cg-docs/solutions/`, `.cg-docs/archive/`, `compound-gpid.md`, `compound-gpid.local.md`, `roadmap.json`, `SCHEMA_VERSION`, `.github/` (prompts, skills, agents, instructions infrastructure)."

For each agent provide: changed files, project language (from `compound-gpid.local.md`), relevant plan context, and only targeted Brain/context findings gathered under the context-loading contract.

Do not pass `.cg-docs/views/**` file bodies or diffs to any agent. When those
paths changed, pass only their relative paths/counts and the corresponding
canonical source plus stale-check result.

**R Package check (all depth levels)**: If the project has `DESCRIPTION` + `NAMESPACE` or `R/`, check `.Rbuildignore` for `.cg-docs/`. If absent, add as **P2** under `@cg-code-quality`:
> **[cg-code-quality]** `.Rbuildignore` — `.cg-docs/` not excluded from package build. **Why**: shouldn't be bundled. **Fix**: Add `^\.cg-docs$`.

**R skill check (all depth levels)**: If `.R`, `.r`, or `.Rmd` files are changed, each agent must load the appropriate skill:
- Statistical/analytical work (welfare, survey, econometrics, visualization) → `cg-skill-r-analytical`
- Package/infrastructure work (package dev, Shiny, targets, plumber, httr2) → `cg-skill-r-technical`
- Mixed/unclear → load both

**Stata skill check (all depth levels)**: If `.do` or `.ado` files are changed, every agent must load `cg-skill-stata-best-practices`.

**Python skill check (all depth levels)**: If `.py` files are changed, each agent must load `cg-skill-python-best-practices`.

**Protected artifacts (all depth levels)**: Discard any finding recommending to delete, replace, rename, or move these files (same protected list as the Global agent constraint above). Do NOT discard content findings (credentials, schema violations, data quality issues).

**Verify mode agent dispatch** (when `mode:verify` is active):
Dispatch only `@cg-code-quality` and `@cg-testing` (depth is `light` per Step 1.7).
Include the suppression context from Step 1.7 in each agent's dispatch.
Do NOT apply staged risk-class routing — the verify pass stays at light depth regardless of file content.
Language-specific skill loading still applies — see R/Python/Stata skill checks above.

### Step 2.5: Subagent Output Quality Check

After each subagent returns, check for **usable** output:
- **Presence**: At least one `**[P0.`/`**[P1.`/`**[P2.`/`**[P3.` entry, OR an explicit "no issues found" statement.
- **Context**: Findings reference the changed files by name.
- **Volume**: At least 2 non-header lines; fewer counts as incomplete.

If output is **empty, garbled, or clearly off-topic**:
1. Note under a dedicated section:
   ```
   ### ⚠️ Incomplete Reviews
   - `@<agent-name>` did not produce usable output. Consider re-running `/cg-review` with a higher model tier, or invoke `@<agent-name>` directly.
   ```
2. Do NOT retry the agent automatically — the user controls model selection.
3. Continue with remaining agents. If all return usable output, skip this section.

### Step 3: Collect and Prioritize Findings

Merge all agent findings into a single prioritized report:

```markdown
## Review Report

**Review mode**: <light|standard|data-risk|architecture|full>
**Files reviewed**: <count>
**Findings**: 6 (P0: 0, P1: 2, P2: 3, P3: 1)

### P0 — BLOCKING (immediate remediation required)
- **[P0.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>

### P1 — CRITICAL (must fix before merge)
- **[P1.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>
- **[P1.2]** [agent-name] ...

### P2 — IMPORTANT (should fix)
- **[P2.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>

### P3 — MINOR (nice to have)
- **[P3.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>

### ✅ Passed
- <agent-name>: No issues found
- <agent-name>: No issues found
```

### Step 3.5: Save Review Report

1. Find the most recently modified `.md` plan in `.cg-docs/plans/` by `date:` field (skip `.gitkeep`); if `date:` is absent, fall back to last-write time; if tied, prefer the alphabetically last filename. If none, use `<today's date>-review` as slug and `plan: null`.
2. Filename: `<plan-stem>-review.md` in `.cg-docs/reviews/`. (e.g., `2026-03-26-roadmap-json.md` → `2026-03-26-roadmap-json-review.md`)

   **If `mode:verify` is active**: strip the trailing `-review` from the prior review filename stem, then append `-verify-review.md`. Example: prior review `2026-04-21-foo-review.md` → stem without `-review`: `2026-04-21-foo` → filename: `2026-04-21-foo-verify-review.md`. If that file already exists, append a counter: `2026-04-21-foo-verify-review-2.md`, `2026-04-21-foo-verify-review-3.md`, etc. (The latest verify pass supersedes prior ones, but the prior file is preserved for traceability.)

   Use the following frontmatter schema for verify reviews:
   ```yaml
   ---
   date: YYYY-MM-DD
   depth: light
   parent-review: .cg-docs/reviews/<prior-review-filename>
   type: verification
   findings:
     P1.1: open
   ---
   ```
   Before writing, confirm the `parent-review:` target exists. If not, warn: "parent-review: target not found — link may be stale."
   The `parent-review:` field links to the prior standard review (not the upstream plan). The `type: verification` field distinguishes verify reviews from standard reviews.

3. Parse all finding IDs matching `P[0-3]\.\d+[a-z]?`. Build a `findings:` YAML map with each set to `open`. Valid statuses: `open`, `fixed`, `skipped`. After parsing: "Parsed N finding IDs. If count differs from total findings above, some IDs may be non-standard."
4. Prepend frontmatter:
   ```yaml
   ---
   date: YYYY-MM-DD
   depth: <light|standard|data-risk|architecture|full>
   type: standard
   plan: <path to active plan file, or null>
   findings:
     P1.1: open
     P2.1: open
   ---
   ```
5. Write frontmatter + full report to `.cg-docs/reviews/<stem>-review.md` directly — **do NOT delegate to a subagent**.
6. Tell the user: "> Review report saved to `.cg-docs/reviews/<filename>`. Use `/cg-fix-triage` in a future session to apply findings by ID (e.g., `/cg-fix-triage P1.2 P2.1`) or by priority level (e.g., `/cg-fix-triage P1`)."

### Step 4: Triage

**Default (autofix mode)** — active unless `--report-only` or `mode:verify` was passed. Tagging instructions were included in each agent dispatch at Step 2. Apply the tagged findings:

- **safe_auto**: Apply immediately. Never `safe_auto` findings touching statistical functions, welfare/income variables, or weight parameters — escalate to `manual`.
- **manual**: Present to user for approval before applying.
- **advisory**: Note but do not apply.

Apply fixes directly — **do NOT delegate to a subagent**. For each `safe_auto` fix, update `findings:` frontmatter from `open` to `fixed` — **do NOT delegate**.

Report: > "Autofix complete: applied \<N\> safe fixes (files: <list of file:line changes>), \<M\> manual fixes need your review, \<K\> advisory notes filed."

**If `--report-only`** was passed, present findings one at a time (P0 first, then P1, then P2, then P3). For each ask: **Fix** / **Skip** / **Discuss**.

### Model Advisory Handoff

Read `.github/shared/model-advisory.contract.md` and use the `review` stage for
the transition to fix triage. Emit a compact recommendation with the review
capability profile, strong option and effort, economical option when useful, and
rationale. When the generator family is known, a different family may be
suggested for independent contrast; when it is unknown or Auto, do not infer the
hidden identity. Examples are suggestions; availability can differ by platform
and date, and the user makes the final selection. Do not dispatch, switch,
retry, or set a model or reasoning effort.

### Step 5: Summary

> ## Review Summary
> - **Fixed**: X findings
> - **Skipped**: X findings
> - **Remaining**: X findings
>
> **What would you like to do next?**
> 1. **`/cg-review mode:verify`** — Verify fixes converged (suppresses fix-consequence P2/P3 findings) *(ensure fixes are committed or staged first)*
> 2. **`/cg-fix-triage`** — Apply skipped findings in a future session
> 3. **`/cg-compound`** — Capture learnings from this review
> 4. **`/cg-fixbug`** — Document a bug that was found and fixed
> 5. **Ready to merge** — All issues resolved, no further action needed
>
> *If `mode:verify` was active and no findings were reported: move option 5 to position 1 — the cycle has converged.*

Wait for the user's response before proceeding.
