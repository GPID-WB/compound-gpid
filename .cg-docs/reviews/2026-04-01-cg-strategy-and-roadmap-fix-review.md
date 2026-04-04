## Review Report

**Review depth**: standard
**Files reviewed**: 9 (8 modified + 1 new/untracked)
**Findings**: 3 P1 · 16 P2 · 12 P3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-performance] `.github/prompts/cg-strategy.prompt.md` Step 4 — Serial `@cg-roadmap` dispatches, one per change.
  **Why**: Step 4 instructs dispatching `@cg-roadmap` for each individual change (new milestone, each new feature, each retired feature), then reading `roadmap.json` after every dispatch to verify. A typical session (1 milestone + 4 features) = 5 full agent invocations + 5 file reads. `@cg-roadmap` is capable of applying all changes in a single call.
  **Fix**: Replace the per-change loop in Step 4 with a single batched dispatch: "Dispatch `@cg-roadmap` ONCE with all approved changes listed together. Read `roadmap.json` once afterward to verify all changes were applied."

- **[P1.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test coverage for `cg-strategy.prompt.md`.
  **Why**: Every other orchestrator prompt has at least file-existence and frontmatter-structure tests. `cg-strategy.prompt.md` is the newest and most complex workflow entry point, yet it is completely untested.
  **Fix**: Add a `Describe "cg-strategy.prompt.md"` block with: (1) file-existence test, (2) `description:` frontmatter key present, (3) `model:` frontmatter key present.

- **[P1.3]** [cg-version-control] All changes are on `main` — violates the project's own branching policy.
  **Why**: `compound-gpid.md` Constraints: "Conventional commits and feature branches — `type(scope): description` format required; work on branches, not main."
  **Fix**: Create a feature branch before committing: `git checkout -b feat/cg-strategy-and-roadmap`. Commit there and merge via PR.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `docs/workflow.md:11–14` — Workflow loop diagram is misaligned.
  **Why**: The `^` caret arrows and labels ("Resume", "Fix Bug") on lines 12–14 don't vertically align with their target words on the first line. The diagram is hard to parse as rendered ASCII art.
  **Fix**: Align carets directly under "Strategy" and "Brainstorm":
  ```
  Setup -> Strategy -> Brainstorm -> Plan -> Work -> Review -> Fix Triage -> Compound -> Release
               ^              ^
        (vision/rethink)  (one task)
            Resume       Fix Bug  (enter at any stage when a bug is found)
  ```

- **[P2.2]** [cg-code-quality + cg-performance] `.github/copilot-instructions.md:22–47` — Charter Rules section injected into every session context.
  **Why**: `copilot-instructions.md` is loaded on every Copilot Chat session. The Charter Rules block (~25 lines including an archive format code block) is only relevant during charter edits — zero relevance when reviewing Stata code, running tests, or asking a Python question. Every token here costs on every agent session.
  **Fix**: Replace the full Charter Rules block with a one-line summary and pointer: `"Never remove body content from compound-gpid.md without archiving it to .cg-docs/archive/charter-history.md first. Using /cg-strategy handles this automatically."` Keep the full rules in `cg-strategy.prompt.md` where they're needed.

- **[P2.3]** [cg-performance] `.github/prompts/cg-strategy.prompt.md` Step 0 — Speculative directory scans on every invocation.
  **Why**: Step 0.4 scans both `.cg-docs/brainstorms/` and `.cg-docs/plans/` (potentially dozens of files for a mature project) before the user has said a single word. For trigger 1 (new project), these reads are entirely wasted; for trigger 3 (post-milestone), they're useful.
  **Fix**: Move the brainstorm/plan scan to Step 2, conditional on trigger type: "If trigger is 2 or 3: scan recent brainstorms and plans for context. For trigger 1, skip."

- **[P2.4]** [cg-performance] `.github/prompts/cg-resume.prompt.md:235–253` — 60%-threshold condition stated twice in Step 4 and once more in the nudge section (3 occurrences total).
  **Why**: Three independent occurrences create drift risk — if the threshold changes, a partial update creates inconsistent behavior (nudge fires at a different threshold than the next-action suggestion).
  **Fix**: Define the condition once at first use with a label: `<!-- SCOPE_THRESHOLD: 60% -->` and reference it by name in subsequent occurrences.

- **[P2.5]** [cg-version-control] `.github/prompts/cg-strategy.prompt.md` is untracked (`??` in git status).
  **Why**: The new cg-strategy prompt was created but never staged. The rest of the related changes (copilot-instructions.md, docs, setup) are staged. The untracked file will be silently omitted from any commit.
  **Fix**: `git add .github/prompts/cg-strategy.prompt.md` 

- **[P2.6]** [cg-version-control] Changes mix three distinct concerns in one uncommitted changeset.
  **Why**: (1) Feature: `/cg-strategy` command, (2) Bug fix: `@cg-roadmap` model downgrade, (3) Data: mark plan completed. Mixing these obscures history and complicates bisect/revert.
  **Fix**: Commit as three atomic commits:
  - `feat(cg-strategy): add /cg-strategy prompt and update workflow docs`
  - `fix(cg-roadmap): downgrade agent model from Sonnet to Haiku`
  - `data(plans): mark 2026-04-01-cg-strategy-and-roadmap-fix completed`

- **[P2.7]** [cg-reproducibility] `.github/prompts/cg-setup.prompt.md` — `.cg-docs/reviews/` missing from the setup scaffold.
  **Why**: The scaffold lists `archive/`, `brainstorms/`, `plans/`, `strategy/`, and `solutions/` but NOT `reviews/`. New projects set up from scratch won't have a `reviews/` directory. `/cg-review` will fail to write its report on first run.
  **Fix**: Add `reviews/` and `.gitkeep` to the scaffold structure (same pattern as `strategy/` added in this PR).

- **[P2.8]** [cg-reproducibility] `scripts/link.ps1` and `install.ps1` — `.cg-docs/` subdirectories are not created by install/link.
  **Why**: A user who runs `cg-link` without running `/cg-setup` gets no `.cg-docs/` scaffold. First use of `/cg-strategy`, `/cg-review`, or `/cg-compound` will fail writing their output artifacts.
  **Fix**: Either (a) add minimal `.cg-docs/{strategy,reviews,archive}/` scaffolding to `link.ps1`, or (b) update `docs/installation.md` to make `/cg-setup` a mandatory step (not optional) with a warning that prompts will throw directory errors otherwise.

- **[P2.9]** [cg-architecture] `.github/copilot-instructions.md` — Charter Rules reference `.cg-docs/archive/` without defensive creation.
  **Why**: Charter Rules instruct agents to append to `.cg-docs/archive/charter-history.md`. If the directory doesn't exist (migrated project, partial setup), the write fails silently — making the "never delete without archiving" rule unenforceable.
  **Fix**: Add to Charter Rules: "If `.cg-docs/archive/` does not exist, create it before appending."

- **[P2.10]** [cg-architecture] `.github/copilot-instructions.md` — Workflow Entry Points table omits the entire execution half of the workflow.
  **Why**: Table lists only 6 entry-point commands. Missing: `/cg-work`, `/cg-review`, `/cg-fix-triage`, `/cg-compound`, `/cg-fixbug`, `/cg-release`. A model using this table as its only reference has no pointer to the implementation and quality-feedback loop.
  **Fix**: Rename "Workflow Entry Points" to "Starting a Workflow" and add a note: `"For follow-up commands (/cg-work, /cg-review, /cg-fix-triage, /cg-compound), see docs/reference.md."` Or extend the table with the follow-on commands.

- **[P2.11]** [cg-data-quality] `.github/prompts/cg-strategy.prompt.md` Step 0.2 — `compound-gpid.local.md` read without validating extracted fields.
  **Why**: `project-type` controls which question branch is taken in Step 2 (analytical vs. technical). A missing or null `project-type` causes silent fallthrough to the wrong conversation branch.
  **Fix**: Add: "If `project-type` is missing from `compound-gpid.local.md`, ask the user before proceeding: 'I couldn't determine your project type. Is this an analytical (statistics/modeling) or technical (infrastructure/API) project?'"

- **[P2.12]** [cg-data-quality] `.github/prompts/cg-resume.prompt.md:221–223` — Unhandled state: `roadmap.json` absent but strategy documents present.
  **Why**: The new conditional handles two cases (`roadmap.json` exists → normal; `roadmap.json` missing AND no strategy docs → "No roadmap found"). But misses: `roadmap.json` missing AND strategy docs exist — a user who ran `/cg-strategy` but whose `@cg-roadmap` dispatch never completed.
  **Fix**: Add branch: "If `roadmap.json` does NOT exist but `.cg-docs/strategy/` documents exist: say 'No roadmap yet, but strategy documents exist. Run `@cg-roadmap` to initialize one.'"

- **[P2.13]** [cg-data-quality] `.github/prompts/cg-resume.prompt.md:237` — Strategy directory check may throw on pre-update projects.
  **Why**: The 60%-threshold condition lists `.cg-docs/strategy/` docs. On projects linked before this release, the `strategy/` directory doesn't exist. Listing a non-existent directory will error, not return an empty list.
  **Fix**: Add: "(treat a missing `.cg-docs/strategy/` directory as equivalent to zero documents)."

- **[P2.14]** [cg-testing] `tests/roadmap.Tests.ps1` — No test for the strategy-document age check in cg-resume.
  **Why**: The 60%-AND-no-recent-strategy condition is new logic with edge cases (empty directory, multiple files, how to compute "60 days old" from filename vs modification date).
  **Fix**: Add test function `Test-RecentStrategyDocument` and tests for: empty directory → false, directory missing → false, file older than 60 days → false, recent file → true.

- **[P2.15]** [cg-testing] `tests/charter.Tests.ps1` — No test for the Charter archiving format.
  **Why**: The Charter Rules format (`## Archived YYYY-MM-DD` / `**Removed from**: <section>`) is defined in prose. No test validates that the format in copilot-instructions.md matches what archive-writing agents will produce.
  **Fix**: Add test: parse copilot-instructions.md and assert the archive block template contains the correct date-stamp format and "Removed from" label.

- **[P2.16]** [cg-documentation] `.github/prompts/cg-strategy.prompt.md` — Description wording inconsistent with `docs/reference.md`.
  **Why**: Prompt frontmatter says "Produces concrete roadmap changes." Reference table says "Dispatches `@cg-roadmap` for all writes." Same outcome, different phrasing; users reading both will see a mismatch.
  **Fix**: Align to the reference description: "...Dispatches `@cg-roadmap` for all roadmap writes." (more specific about the mechanism).

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-resume.prompt.md` — Mixes `->` and `→` arrow styles within the file.
  **Fix**: Standardize to `→` throughout (matches cg-setup.prompt.md style).

- **[P3.2]** [cg-architecture] `.github/agents/cg-roadmap.agent.md` — Haiku 4.5 for the only user-directly-invokable agent.
  **Why**: Haiku handles atomic JSON writes well but may miss cross-milestone nuance when users invoke it directly with complex restructuring requests. The `user-invokable: true` flag creates an implicit expectation it handles complex use.
  **Fix**: Either (a) promote to Sonnet 4.6, or (b) narrow the description: "handles atomic roadmap write operations — for strategic restructuring, use `/cg-strategy`."

- **[P3.3]** [cg-architecture] `.github/prompts/cg-strategy.prompt.md` Step 3 — Iteration loop has no convergence exit.
  **Why**: "Iterate until the user approves" has no cap after repeated revision cycles, leaving no escalation path.
  **Fix**: Add to Rules: "If the user requests more than 3 revisions without approving, present exactly two options explicitly: 'Option A: <X>. Option B: <Y>. Which would you like, or shall we end the session?'"

- **[P3.4]** [cg-performance] `.github/prompts/cg-strategy.prompt.md` Rules section — 6 of 10 bullets restate constraints already enforced in the steps.
  **Fix**: Trim to only constraints not already structurally enforced by step hard-stops (keep: "Never suggest adding features you haven't discussed," "Always end with a decision," "If no decision, do not save a strategy document").

- **[P3.5]** [cg-performance] `.github/prompts/cg-strategy.prompt.md` — Full document template (~30 lines) always loaded even when session ends without a save.
  **Fix**: Condense to frontmatter fields + section headings only; remove inline explanatory comments that are self-evident.

- **[P3.6]** [cg-data-quality] `.github/prompts/cg-strategy.prompt.md` — YAML `description:` field spans 3 lines; other prompts use single-line.
  **Fix**: Condense to: `description: "Strategic project visioning and direction-setting. Use when you have a full project in mind to structure, or when you need to rethink direction mid-project. Dispatches @cg-roadmap for all writes."`

- **[P3.7]** [cg-data-quality] `.github/prompts/cg-strategy.prompt.md` — No `tools:` frontmatter key; write restrictions are prose-only.
  **Why**: File Permissions section restricts writes, but with no platform-level `tools:` enforcement.
  **Fix**: If VS Code Copilot supports scoped tool access for `.prompt.md` files, add `tools: [read_file, write_file, list_dir]`. Otherwise, document the restriction as advisory in the frontmatter comment.

- **[P3.8]** [cg-data-quality] `.github/prompts/cg-strategy.prompt.md` Step 0.4 — Brainstorm/plan skimming assumes valid frontmatter.
  **Fix**: Add: "If a file's frontmatter is missing `title` or `status`, skip it and note it as `<filename> (unreadable frontmatter)`."

- **[P3.9]** [cg-data-quality] `.cg-docs/plans/2026-04-01-cg-strategy-and-roadmap-fix.md:7` — `language: "both"` is inaccurate (no R or Python code was written).
  **Fix**: Change to `language: "config"` or `language: "N/A"`.

- **[P3.10]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the Workflow Entry Points table in copilot-instructions.md.
  **Fix**: Add test: parse copilot-instructions.md and assert `/cg-strategy`, `/cg-brainstorm`, `/cg-plan`, `@cg-roadmap`, `/cg-resume` are present in the table.

- **[P3.11]** [cg-documentation] `.github/copilot-instructions.md` Workflow Entry Points — missing header note that the table is "entry points only."
  **Fix**: Add: "> **Entry points only.** For all commands, see [docs/reference.md](../docs/reference.md)."

- **[P3.12]** [cg-documentation] Inconsistent prerequisite docs for `/cg-strategy` between `docs/workflow.md` and references elsewhere.
  **Why**: `workflow.md` says `compound-gpid.md` is a "hard prerequisite" that blocks the prompt. `reference.md` implies all prompts handle a missing charter gracefully.
  **Fix**: Add a note in `docs/reference.md` `/cg-strategy` row: "Requires `compound-gpid.md` (hard prerequisite — run `/cg-setup` first)."

---

### ✅ Passed

- **cg-code-quality**: No encoding mojibake detected in `cg-strategy.prompt.md`. No secrets or credentials in changed files.
- **cg-reproducibility**: `.cg-docs/strategy/` correctly added to `cg-setup.prompt.md` scaffold. `.cg-docs/archive/` already exists in project.
- **cg-data-quality**: `cg-roadmap.agent.md` Haiku 4.5 version is intentional and consistent with agent version conventions (Haiku = 4.5, Sonnet/Opus = 4.6 — no schema error).
- **cg-data-quality**: Plan frontmatter `completed-date: 2026-04-01` is correctly set.
- **cg-documentation**: `docs/workflow.md` Strategy section format is consistent with other sections and documents the output artifact correctly.
- **cg-documentation**: `docs/installation.md` migration note for `strategy/` folder is clear and complete.
- **cg-documentation**: `cg-setup.prompt.md` correctly adds `/cg-strategy` to the setup success message.
- **cg-version-control**: No sensitive data, API keys, or data files in the changeset.
