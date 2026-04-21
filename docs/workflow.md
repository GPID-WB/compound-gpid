# Workflow

This page explains the Compound GPID workflow loop and how to use each step — including when to use each command, the different scenarios each supports, and when **not** to use them.

> **Not installed yet?** See [Installation](installation.md) first. For all commands and shortcuts, see [Reference](reference.md).

---

## The Loop

```
Setup -> Strategy -> Ideate -> Brainstorm -> Plan -> Work -> Review -> Compound
                ^           ^            ^                      ^          ^
       (vision/rethink)  (discover)  (one task)             Fix Bug    Refresh
Resume (re-entry at any stage)
```

All steps are invoked as `/cg-*` prompts in GitHub Copilot Chat. **Prompts are not interactive commands** — invoke a prompt, answer its questions when asked, and let it run to completion.

> **Project Charter** (`compound-gpid.md`): Before any workflow step, Copilot reads your
> project's charter to understand objective, deliverables, constraints, and current focus.
> Create or update it via `/cg-setup`. The charter has exactly four sections (Objective, Key
> Deliverables, Constraints, Current Focus) — content that doesn't fit belongs elsewhere
> (see `/cg-setup` for where each type belongs). Content removed from the charter is archived
> to `.cg-docs/archive/charter-history.md`. `/cg-resume` will nudge you if `last-reviewed`
> is missing or more than 30 days old.

---

## Steps

### Setup (`/cg-setup`)

**When to use**:
- The first time you use Compound GPID in a new project
- When you want to update language preferences, project type, or review depth
- When re-entering an existing project that has no `compound-gpid.md` or `compound-gpid.local.md`

**What happens**: Creates `compound-gpid.md` (the project charter), `compound-gpid.local.md` (your personal config), and `compound-gpid.context.md` (a growing knowledge base for project-specific facts). Walks you through setting the project objective, language, project type, and review depth. Scaffolds the `.cg-docs/` directory structure (`brainstorms/`, `plans/`, `reviews/`, `strategy/`, `solutions/`, `archive/`).

**Scenarios**:
- *New project*: Run once at the start. `/cg-setup` asks about language, project type, review depth, and optionally the project charter.
- *Returning project (no config)*: Run `/cg-setup` — it detects the existing repo and offers to create the config files without overwriting existing work.
- *Change review depth*: Run `/cg-setup` again and update the `review-depth` field. You can also edit `compound-gpid.local.md` directly.
- *Team member onboarding*: Each team member runs `/cg-setup` independently since `compound-gpid.local.md` is gitignored. The shared `compound-gpid.md` charter is already committed.

**When NOT to use**:
- When you just want to resume interrupted work — use `/cg-resume` instead
- To read the charter — all `/cg-*` prompts read it automatically

**Output**: `compound-gpid.md` + `compound-gpid.local.md` + `compound-gpid.context.md` + `.cg-docs/` directories

---

### 0. Ideate (`/cg-ideate`)

**When to use**:
- You want to discover what to work on next without having a specific task in mind
- You need fresh ideas for project improvement or addressing known pain points
- Your backlog is stale and you want a codebase-grounded scan for issues
- Before a planning session when you're unsure which improvement is highest value

**What happens**: Launches parallel agents to scan the codebase for pain points, architecture issues, and quality gaps. Generates 8–12 improvement ideas, filters them against the roadmap and project constraints, and presents the survivors ranked by impact/effort ratio. Hands off to `/cg-brainstorm` or `/cg-plan`.

**Scenarios**:
- *Backlog grooming*: Run `/cg-ideate` at the start of a sprint to surface what the codebase actually needs, not just what you remembered.
- *Post-milestone discovery*: After completing a milestone, use `/cg-ideate` to find the next highest-value improvement.
- *Quality debt scan*: Any time you feel the code is accumulating debt but can't pinpoint where.

**When NOT to use**:
- When you already have a specific, well-defined task — skip to `/cg-brainstorm` or `/cg-plan` directly
- When you need to fix a known bug — use `/cg-fixbug`
- When you're mid-session with an active plan — use `/cg-work` to finish what you started

**Output**: Interactive ranked list of improvement ideas.

---

### 1. Brainstorm (`/cg-brainstorm`)

**When to use**:
- Requirements are fuzzy and you're not sure what to build
- Multiple approaches exist and you need to think through trade-offs
- You want to explore a design decision before committing to an implementation plan
- The task is non-technical (strategy, process, documentation-only) and you want a Thinking Partner

**What happens**: The prompt first **checks for prior work** — it scans `.cg-docs/brainstorms/` for any existing brainstorm on the same topic and offers to continue from it instead of starting fresh. It then scans your project, classifies the task type (software vs. non-software), assesses scope, asks clarifying questions one at a time, and proposes 2–3 approaches with pros/cons. Once you pick one, it saves a decision document to `.cg-docs/brainstorms/`. If `roadmap.json` exists, it also offers to register the brainstorm outcome as a feature idea in the roadmap.

**Task Classification**: The prompt auto-detects whether the task is software/data work or a strategy/process/documentation-only discussion:
- **Software/Data mode**: asks about technical implementation approaches, dependencies, testing strategy
- **Thinking Partner mode**: asks about decision criteria, stakeholders, success metrics, and trade-offs — no code output. Scope is classified as Focused / Extended / Strategic.

**Scope assessment**: The prompt classifies the scope before asking questions:

| Scope | Criteria | Effect |
|-------|----------|--------|
| **Lightweight** | Single file, < 2 days, no new dependencies | 2–3 focused questions, concise options |
| **Standard** | Multiple files, 2–5 days, minor dependencies | Full 6-question set, detailed options |
| **Deep** | Cross-cutting, > 5 days, architectural impact | Extended questioning, risk analysis, phased proposal |

**Scenarios**:
- *First brainstorm on a topic*: Start fresh; the prompt proposes 2–3 approaches.
- *Continuing a previous brainstorm*: The prompt finds the prior file and asks if the decision still applies, saving you from re-covering solved ground.
- *Non-technical decision*: Thinking Partner mode — e.g., "Should we migrate from Stata to R?" structures a decision framework rather than an implementation plan.
- *Pre-plan clarity*: Use brainstorm to decide between two architectural approaches before writing a formal plan.
- *Small task (Lightweight)*: The prompt keeps questioning brief and handoff to `/cg-plan` is fast.

**Handoff options**: `/cg-plan` (turn into a plan), update charter, `/cg-brainstorm` again (related topic), or `/cg-work` directly (Lightweight tasks only).

**When NOT to use**:
- When requirements are already well-defined — go to `/cg-plan` directly
- For trivially small one-file changes — use `/cg-work` directly (it handles inline planning)
- For debugging a known bug — use `/cg-fixbug`
- To repeat a brainstorm you've already done — `/cg-brainstorm` will find the prior file and offer to continue from it

**Output**: `.cg-docs/brainstorms/YYYY-MM-DD-<title>.md`

---

### 2. Plan (`/cg-plan`)

**When to use**:
- After brainstorming, when you have a clear understanding of what to build
- When requirements are precise and you need a step-by-step implementation roadmap with acceptance criteria
- For Standard or Deep tasks before invoking `/cg-work`
- When you want `/cg-work` to have clear scope boundaries and verification checkpoints

**What happens**: The prompt first **checks for prior work** — it scans `.cg-docs/plans/` for any existing plan on the same feature and offers to refine, follow up from, or start fresh. It then reads any relevant brainstorm, researches your codebase, assesses the implementation scope, and creates a step-by-step plan with files to create/modify, tests to write, and acceptance criteria. A confidence check validates completeness, testability, dependencies, risk coverage, and scope clarity before finalizing. If `roadmap.json` exists, the prompt offers to link the plan to a matching roadmap feature.

**Scope assessment**: The prompt classifies scope before writing the plan:

| Scope | Criteria | Plan detail |
|-------|----------|-------------|
| **Lightweight** | 1–3 steps, single concern, < 2 days | Short plan, minimal risk section |
| **Standard** | 3–8 steps, multi-file, 2–5 days | Full plan template, complete risk table |
| **Deep** | 8+ steps, architecture change, > 5 days | Phased plan, detailed requirements table, dependency graph |

**Scenarios**:
- *New feature*: Normal flow — plan the implementation, link to roadmap, then run `/cg-work`.
- *Existing plan needs revision*: `/cg-plan` finds the prior plan and offers to refine it in-place.
- *Follow-on work from a finished plan*: Choose "follow-up" to create a new plan that inherits context from the prior one.
- *Brainstorm-first flow*: If a brainstorm was loaded, the scope classification is inherited from it — no redundant assessment step.
- *Deep architectural change*: Use a phased plan with numbered phases; `/cg-work` will implement one phase at a time.

**Handoff options**: `/cg-work` (start implementing), `/cg-brainstorm` (revisit open questions).

**When NOT to use**:
- For trivial one-file changes that take under an hour — use `/cg-work` directly (it generates an inline Lightweight plan if none exists)
- For debugging a known bug — use `/cg-fixbug`, which has its own structured flow including reproduce/verify hard stops
- When the brainstorm used **Thinking Partner mode** (strategy/process outputs) — a Thinking Partner brainstorm produces decisions, not software plans. Consider updating `compound-gpid.md` instead
- For emergency production hotfixes — go to `/cg-fixbug` directly to avoid the overhead of a full plan

**Output**: `.cg-docs/plans/YYYY-MM-DD-<title>.md`

---

### 3. Work (`/cg-work`)

**When to use**:
- After `/cg-plan` has created an implementation plan
- To implement a known Lightweight task without a prior plan (the prompt generates a brief inline plan)
- To continue an implementation that was interrupted in a previous session

**What happens**: The prompt loads the most recent plan (or generates a short inline plan for Lightweight tasks when no plan file exists) and implements it step by step — writing code, tests, and documentation. Before implementation, it builds a test index mapping each module to its test file. When work begins, the linked roadmap feature is automatically marked `active`. After all steps complete, a **mechanical self-review** (Step 3.2) scans for debug code, missing tests, broken imports, incomplete TODO markers, and hardcoded secrets. The plan file is updated to `completed` status.

**Inline plan handling** (when no plan file is found):
- The prompt does a keyword search across `.cg-docs/plans/` first — an existing relevant plan may not have been the most recent.
- For requests containing words like "refactor", "replace", "migrate", or "pipeline", or touching multiple files: declines inline planning and asks you to run `/cg-plan` first.
- For **Standard** or **Deep** scope: warns strongly that `/cg-plan` is recommended, offers to generate the inline plan anyway (not recommended).
- For **Lightweight** scope only: generates a 3–5 step inline plan, saves it to `.cg-docs/plans/`, and asks for confirmation before proceeding.

**Self-review** (automatic, runs after implementation):
The prompt scans its own output for:
- Debug code: `print(`, `console.log(`, `browser()`, `breakpoint()`, `cat("DEBUG`
- Missing tests: every new public function needs at least one test
- Broken imports: new `library()`, `import`, or `use` statements must reference packages in the project
- Incomplete work: `TODO`, `FIXME`, `HACK`, `XXX` added during the session
- Secrets: `api_key`, `password`, `secret`, `token`, `AWS_`, `OPENAI_`

> ⚠️ **Self-review does not replace `/cg-review`.** Statistical and logical correctness are **not** checked mechanically — always run `/cg-review` before merging analytical code.

**Scenarios**:
- *Normal implementation*: Load the plan, implement step by step, commit at each checkpoint.
- *Resuming interrupted work*: Run `/cg-work` in a new session — it re-loads the active plan from `.cg-docs/plans/` and skips any steps already marked complete.
- *Lightweight task (no prior plan)*: Describe the change; the prompt generates and confirms a 3–5 step inline plan before starting.
- *Large refactor (Deep scope)*: Should have a phased plan from `/cg-plan`. Work through one phase at a time; each phase has its own commit checkpoint.
- *Roadmap-linked feature*: The roadmap feature transitions automatically: idea → planned (on `/cg-plan`) → active (on `/cg-work` start) → done (when you complete the plan).

**Handoff options**: `/cg-review` (review the changes), `/cg-compound` (capture learnings), `/cg-fixbug` (discovered a bug mid-implementation), `/cg-plan` (next feature).

**When NOT to use**:
- For tasks that clearly span multiple files or days without a plan — use `/cg-plan` first. `/cg-work` will warn you if the scope looks too large for an inline plan.
- For debugging a known bug — use `/cg-fixbug`, which enforces a reproduce-before-fix discipline
- To apply review findings — use `/cg-fix-triage`, which tracks each finding's status
- As a replacement for `/cg-review` — never skip review for analytical code that feeds published statistics

**Output**: Code, tests, documentation changes; updated plan frontmatter (`status: completed`).

---

### 4. Fix Bug (`/cg-fixbug`)

**When to use**:
- A specific, reproducible bug has been identified — during work, during review, or from a user report
- You need a structured reproduce-diagnose-fix-verify cycle with hard stops
- You want a verified bug document captured in `.cg-docs/solutions/bugs/`

**What happens**: The prompt walks through five stages with hard stops at reproduce and verify:
1. **Intake**: Describe the bug; search `.cg-docs/solutions/bugs/` for any prior occurrence of the same pattern.
2. **Reproduce** *(hard stop)*: Write a failing test that reproduces the bug. Does not proceed until the test confirms the bug exists.
3. **Diagnose**: State a root-cause hypothesis with evidence.
4. **Fix** *(hard stop)*: Implement the fix and verify all tests pass — both the reproduction test and the full suite. Does not proceed until tests confirm the fix.
5. **Document**: Write a verified bug report to `.cg-docs/solutions/bugs/`.

**Scenarios**:
- *Regression discovered during review*: Start with `/cg-fixbug` before applying other findings.
- *Edge case from a user report*: Intake the report, reproduce with a minimal test, fix.
- *Recurring bug pattern*: The intake step checks prior solutions — if this bug (or a related one) was fixed before, the prior solution is surfaced immediately.
- *Bug found mid-implementation*: Pause `/cg-work` and run `/cg-fixbug`; resume `/cg-work` after the fix is committed.

**When NOT to use**:
- For planned feature work — use `/cg-plan` + `/cg-work`
- For code quality issues surfaced in review (e.g., missing tests, naming violations) — use `/cg-fix-triage`
- For performance rework that requires architectural change — use `/cg-plan`
- When you haven't confirmed the bug is reproducible — `/cg-fixbug` requires a failing test before proceeding

**Output**: Fixed code + passing tests + `.cg-docs/solutions/bugs/YYYY-MM-DD-<title>.md`

---

### 5. Review (`/cg-review`)

**When to use**:
- After implementing changes — before merging to main
- Any time you want an independent quality scan of specific files
- Before publishing analytical results — P0 findings (statistical errors, data corruption) must be clear
- After applying a significant fix to verify no regressions were introduced

**What happens**: The prompt determines review depth, identifies changed files, applies any **automatic depth overrides** based on content (see table below), dispatches the appropriate agents, and consolidates findings as P0/P1/P2/P3. Each finding gets a compound ID (e.g., `P0.1`, `P1.2`) for selective fixing. The full report is saved to `.cg-docs/reviews/`.

**Depth tiers**:

| Tier | Agents run | Use when |
|------|-----------|---------|
| **Light** | `cg-code-quality` + `cg-testing` | Quick fixes, formatting, small changes, verifying fix-triage results |
| **Standard** | All 8 agents | Default for most feature work |
| **Thorough** | All 8 + `cg-learnings-researcher` + `cg-adversarial` | Major features, architectural changes, refactors |

**Automatic depth overrides** (applied on top of the configured depth):

| Trigger | Override |
|---------|----------|
| Changed files include `pipeline*.{R,py}`, `extract*.{R,py}`, `load*.{R,py}`, or any file in `scripts/` | Always adds `@cg-data-quality` (even in `light`) |
| Changed files touch authentication, secrets, or credentials | Always adds `@cg-version-control` |
| Changed files call statistical functions (`fmean`, `fsum`, `fgini`, `svymean`, `reghdfe`, `lm`, etc.) or generate summary tables | Always adds `@cg-data-quality` + `@cg-reproducibility` |
| ≥ 50 non-test lines changed | Escalates `light` → `standard` |
| ≥ 200 non-test lines changed | Suggests `thorough` (does not auto-apply — you decide) |

When any override fires, the prompt tells you: `"Auto-escalation applied: [reason]. Running [agents] in addition to the base depth."`

**Invocation**:

| Command | Effect |
|---------|--------|
| `/cg-review` | Use depth from `compound-gpid.local.md` |
| `/cg-review light` | Override to light (2 agents) |
| `/cg-review standard` | Override to standard (8 agents) |
| `/cg-review thorough` | Override to thorough (10 agents, adversarial + learnings) |
| `/cg-review mode:autofix` | Apply safe mechanical fixes automatically after collecting findings |
| `/cg-review light mode:autofix` | Light review + autofix combined |

Arguments can be combined in any order: `/cg-review thorough mode:autofix`.

**Scenarios**:
- *After implementing a feature*: Run `/cg-review` (or `/cg-review standard`) — the configured depth from `compound-gpid.local.md` applies.
- *Quick check after a typo fix*: `/cg-review light` — only code quality and tests, takes less time.
- *Before merging a statistical module*: The auto-escalation adds `@cg-data-quality` + `@cg-reproducibility` automatically if statistical functions are detected — no need to manually choose thorough.
- *After applying fix-triage results*: Run `/cg-review light` to confirm all P0/P1 issues are resolved.
- *Major architectural refactor*: `/cg-review thorough` dispatches `@cg-adversarial` to actively try to break the code.
- *CI-like use*: Run `/cg-review standard` before every PR merge as a quality gate.

Review reports are saved with per-finding status tracking in YAML frontmatter. Each finding ID is recorded as `open`, `fixed`, or `skipped`. `/cg-resume` shows a summary of open findings so unresolved P1s are never lost between sessions.

**When NOT to use**:
- In the middle of implementation — finish implementing first, then review
- As a substitute for running tests — tests must pass before review is meaningful
- On work-in-progress branches where the design is still changing — review findings become stale immediately if the design shifts
- As a first response to a known bug — use `/cg-fixbug` which is designed for reproduce-first diagnosis

**Output**: `.cg-docs/reviews/<plan-stem>-review.md`

---

### 5b. Fix Triage (`/cg-fix-triage`)

**When to use**:
- In a session after `/cg-review` has saved a review report with open findings
- When you want to address only specific priority levels (e.g., P0 and P1 only)
- When fixing a small number of findings without treating everything at once
- At the start of a session to see what review findings are still open

**What happens**: Loads the most recent review report from `.cg-docs/reviews/`, displays findings by priority, applies fixes, and updates per-finding status in the report's frontmatter. Supports selective fixing by priority level or individual finding ID.

After each fix, `/cg-fix-triage` runs a targeted partial test suite to verify the change, then runs a full-suite regression gate at the end of the session. Language-specific skills are loaded conditionally — only when in-scope findings reference `.R`, `.py`, `.do`, or `.ado` files; findings that reference only `.md`, `.json`, or `.ps1` files skip skill loading entirely.

**Invocation**:

| Command | Effect |
|---------|--------|
| `/cg-fix-triage` | Fix all open findings from the most recent review |
| `/cg-fix-triage P0` | Fix all blocking findings only |
| `/cg-fix-triage P1` | Fix all critical findings only |
| `/cg-fix-triage P0 P1` | Fix all blocking and critical findings |
| `/cg-fix-triage P1.2 P2.1` | Fix exactly those two specific findings |
| `/cg-fix-triage --migrate` | Backfill per-finding status tracking on legacy review files (pre-v0.4.3) |

**Finding status tracking**: Each finding ID is recorded as `open`, `fixed`, or `skipped` in the review file's frontmatter. Previously `fixed` findings are never re-shown. `skipped` findings appear in `/cg-resume` as pending so they are not forgotten.

**Scenarios**:
- *Normal fix cycle*: Run `/cg-review`, then `/cg-fix-triage` to apply all findings.
- *Large report*: If the review has more than 15 open findings, `/cg-fix-triage` warns you before proceeding and recommends priority batches. Respond `batch` to get the three recommended batch commands and stop, or `yes` to proceed with all findings at once.
- *Prioritized fix*: Run `/cg-fix-triage P0 P1` to address only blocking and critical issues first; fix P2/P3 later or skip them.
- *Selective fix*: Copy specific finding IDs from the review report: `/cg-fix-triage P1.2 P2.3`.
- *Legacy review file*: Run `/cg-fix-triage --migrate` once on any review file written before v0.4.3 to add the `findings:` frontmatter block.
- *Verify after fixing*: After fix-triage, run `/cg-review light` to confirm the P0/P1 issues are resolved.

**When NOT to use**:
- Before running `/cg-review` — there is no report to act on; the prompt will tell you to run `/cg-review` first
- To fix bugs found outside a review — use `/cg-fixbug` for unstructured bug fixing
- To apply changes to production code without branching — always work on a feature branch; `/cg-fix-triage` modifies files directly

**Output**: Applied code fixes + updated review frontmatter with `fixed`/`skipped` statuses + summary of what was fixed, skipped, and remaining.

---

### 6. Compound (`/cg-compound`)

**When to use**:
- After solving a non-trivial bug, build error, environment issue, or performance problem
- When you discover a pattern or technique that the team is likely to encounter again
- After completing a thorough review that surfaced important, non-obvious learnings
- Any time you think "someone else on the team will hit this"

**What happens**: Captures the problem, root cause, solution, and prevention strategy as a structured document in one of seven categories (`bugs`, `build-errors`, `performance-issues`, `testing-patterns`, `data-quality`, `environment-issues`, `git-workflows`). Checks existing solutions to avoid duplicates and adds cross-references between related documents. This feeds the `cg-learnings-researcher` agent in future thorough reviews, making past solutions discoverable.

**Scenarios**:
- *After a crash or environment break*: Document it with full root cause so future sessions don't repeat the diagnosis.
- *After a subtle statistical error*: Capture the incorrect pattern, the correct pattern, and how to prevent recurrence.
- *After a non-obvious fix*: Even simple fixes are worth capturing if the root cause would have taken hours to rediscover.
- *Cross-referencing*: The prompt checks existing solution files and adds bidirectional links when a new solution is related to a prior one.

**When NOT to use**:
- For documenting normal planned work — that's what plan files are for
- Before a solution is verified — `/cg-fixbug` has hard stop gates; do not use `/cg-compound` to document an unverified fix
- As a substitute for inline code comments — solution documents capture institutional knowledge, not implementation decisions

**Output**: `.cg-docs/solutions/<category>/YYYY-MM-DD-<title>.md`

---

### 6b. Compound Refresh (`/cg-compound-refresh`)

**When to use**:
- Periodically (e.g., monthly or after a major refactor) to keep the knowledge base from drifting
- After renaming or moving files — solution documents may reference stale paths
- After upgrading a major dependency — solution documents may describe API-obsolete patterns
- When the `cg-learnings-researcher` agent starts returning irrelevant results

**What happens**: Audits all solution documents in `.cg-docs/solutions/` across 7 categories. Detects drift (file paths moved, APIs changed, dependencies updated, solutions outdated) and classifies each as Keep / Update / Consolidate / Replace / Archive. Presents an interactive audit report and applies approved changes. Solutions that no longer apply are moved to `.cg-docs/archive/` — never hard-deleted.

**Scenarios**:
- *Post-refactor*: After renaming modules, run refresh to update path references in 20+ solution files at once.
- *Annual cleanup*: Review all solutions for accuracy; archive anything that no longer applies to the current stack.
- *Consolidation*: Merge two solutions that cover the same pattern into one canonical document.

**When NOT to use**:
- As a substitute for writing fresh solutions — run `/cg-compound` first, then refresh later when drift accumulates
- Immediately after adding a new solution — wait until there is meaningful drift to fix
- To delete solutions permanently — the archive mechanism exists to preserve history; hard deletion is not supported

**Output**: Updated solution files in `.cg-docs/solutions/`; deprecated solutions archived to `.cg-docs/archive/`.

---

### 7. Resume (`/cg-resume`)

**When to use**:
- At the start of a new session when you have interrupted or in-progress work
- After VS Code or the conversation was interrupted and you need to reload context
- To get a quick overview of what is in progress across all workflow artifacts

**What happens**: Checks whether your project schema version is current and warns if `cg-update` is needed. Scans `.cg-docs/plans/` for active plans, `.cg-docs/brainstorms/` for decided-but-unplanned brainstorms, `.cg-docs/reviews/` for open and skipped findings, and inspects `git status`/`git log` for in-progress code changes. Presents a structured summary and suggests the most logical next action. If `roadmap.json` exists, it displays milestone progress with completion counts, surfaces roadmap/plan status drift, and surfaces unstarted roadmap ideas from active milestones.

**Scenarios**:
- *Normal session start*: Run `/cg-resume` to see: active plans, open review findings, pending brainstorms, and current git state in one view.
- *Schema version warning*: If the project schema version is behind the global install, `/cg-resume` tells you exactly what migration is needed.
- *After a crash*: Run `/cg-diagnose` first to understand what caused the crash, then `/cg-resume` to pick up the work.
- *Roadmap check*: `/cg-resume` shows milestone progress — e.g., "Milestone 1: 3/5 features done (60%)".

**When NOT to use**:
- In the middle of an active session — it's an entry point, not a mid-session state snapshot
- When starting completely fresh with no prior work — just begin with `/cg-setup` or `/cg-brainstorm`
- After a crash, if you want to understand *what caused it* — use `/cg-diagnose` first

**Output**: A structured context summary and a suggested continuation path.

---

### 8. Diagnose (`/cg-diagnose`)

**When to use**:
- After VS Code crashed and you restarted — this is always the first thing to run after a crash
- When VS Code was sluggish or froze and you want to understand why
- When the AI agent was behaving erratically before a crash (running unsafe commands, getting stuck in loops)

**What happens**: Checks for uncommitted changes and stashed work. Locates and reads VS Code crash logs (`main.log`, `renderer.log`, `exthost.log`, `terminal.log`). Classifies the crash into one of five known categories based on log signatures. Presents a structured crash report with evidence, likely trigger, recovery steps, and prevention advice. Offers to hand off to `/cg-resume` for work recovery.

**Scenarios**:
- *Post-crash (Pester)*: `/cg-diagnose` finds forbidden Pester patterns in the terminal log, classifies as Category A, and reminds you of safe alternatives.
- *Post-crash (long session)*: `/cg-diagnose` finds listener LEAK entries in the renderer log, classifies as Category B, and suggests session hygiene (new chat every 2–3h, close terminals).
- *Post-crash (mid-edit)*: `/cg-diagnose` finds uncommitted changes and warns that a multi-file edit may have been interrupted. Recommends reviewing `git diff` before proceeding.
- *Post-crash (unknown)*: `/cg-diagnose` doesn't find matching log signatures, classifies as Category E, and suggests filing a VS Code issue with the log excerpts.

**When NOT to use**:
- When VS Code didn't crash — this command only inspects crash logs
- For regular session start — use `/cg-resume` instead
- To fix a bug in your code — use `/cg-fixbug`

**Output**: A structured crash report and a handoff to `/cg-resume` for work recovery.

---

### Non-linear Entry Points

The following commands can be invoked at any stage — not just sequentially.

### Roadmap (`@cg-roadmap`)

**When to use**:
- Any time you want to capture a milestone or feature idea directly
- To check the current state of roadmap progress
- To manually update a feature status (e.g., marking something `done` or `abandoned`)
- When other prompts (`/cg-plan`, `/cg-work`, `/cg-brainstorm`) have dispatched it and you want to see what changed

**What happens**: The agent reads and modifies `roadmap.json` — adding milestones, registering features, linking plans, and updating statuses. Other prompts dispatch this agent automatically for roadmap updates when `roadmap.json` exists.

**How to use** — invoke `@cg-roadmap` directly in Copilot Chat:
- `"Add a milestone for survey harmonization"`
- `"I have an idea for automated PPP validation — add it to the pipeline milestone"`
- `"Show me the roadmap progress"`
- `"Remove the feature about X, we're not doing it anymore"`
- `"Link plan '.cg-docs/plans/2026-04-08-foo.md' to the feature 'foo-feature'"`

**When NOT to use**:
- To modify plan files, brainstorm files, or any `.cg-docs/` artifact other than `roadmap.json` — `@cg-roadmap` only manages `roadmap.json`
- To update code — it is purely a roadmap state manager
- As a substitute for `/cg-plan` — `/cg-plan` creates the plan file AND links it to the roadmap via `@cg-roadmap` automatically

**Output**: Updated `roadmap.json` in the project root.

---

### Strategy (`/cg-strategy`)

**When to use**:
- Day zero: you have a vision and need to structure it into milestones and features
- Mid-project: direction has shifted and the roadmap needs a rethink
- Post-milestone: you've completed a milestone and need to plan the next phase
- Stalled project: you're not sure what to work on and want structured direction-setting

**What happens**: Reads your project charter, roadmap, and recent work. Asks focused questions one at a time to understand your ideas, surface trade-offs, and clarify priorities. Proposes a concrete roadmap structure for your approval, then dispatches `@cg-roadmap` to apply the changes. Saves a record of the session to `.cg-docs/strategy/`.

**Scenarios**:
- *New project*: Run after `/cg-setup` to structure the first roadmap from a rough vision.
- *Pivot*: Run mid-project when a major constraint changes (e.g., team size, timeline, scope).
- *Post-milestone review*: Run after completing Milestone 1 to scope Milestone 2 with updated context.

**Hard prerequisite**: `compound-gpid.md` must exist (run `/cg-setup` first). `roadmap.json` is optional — `/cg-strategy` will create it if needed.

**When NOT to use**:
- For a single specific task — use `/cg-brainstorm` or `/cg-plan` directly
- When you just want to add one feature idea to the roadmap — use `@cg-roadmap` directly
- Without a project charter — `/cg-strategy` reads `compound-gpid.md` and will error if it doesn't exist

**Output**: Updated `roadmap.json` + `.cg-docs/strategy/YYYY-MM-DD-<title>.md`

---

## Prompts vs. Agents vs. Skills

| Aspect | Prompts | Agents | Skills |
|--------|---------|--------|---------|
| **What they are** | Workflow commands | Specialized reviewers / roadmap manager | Reference knowledge |
| **How you use them** | Type `/cg-setup`, `/cg-strategy`, `/cg-brainstorm`, etc. | `@cg-roadmap` (direct); review agents dispatched by `/cg-review` | Referenced by prompts/agents |
| **Interactive?** | Yes — they ask questions and wait for your answers | No — automated | No (passive, loaded on demand) |
| **Prefix** | `cg-` | `cg-` | `cg-skill-` |
| **Location** | `.github/prompts/` | `.github/agents/` | `.github/skills/` |
| **Produce output?** | Yes (docs, code, reviews) | Yes (review findings, `roadmap.json`) | No (consumed by others) |

> **`@cg-roadmap` is the only user-invokable agent.** All review agents (`cg-code-quality`, `cg-testing`, etc.) are dispatched exclusively by `/cg-review` and do not appear in the Copilot Chat agent dropdown.

---

> **All commands in one place**: see [Reference](reference.md).
> **Something broken?** See [Troubleshooting](troubleshooting.md).

---

## Plugin Development

> The commands in this section are **developer-only**. They live at the `compound-gpid` repo root and are NOT distributed to linked user projects via junctions. Only use them when working inside the `compound-gpid` repository itself.

### Release (`/cg-release`)

**When to use**: After completing and compounding a milestone, when you are ready to publish a new version of compound-gpid to GitHub.

**What happens**: Detects the latest git tag, analyzes commits since then to suggest the next semver version, reads `.cg-docs/` entries dated after the last release to draft curated release notes, checks `SCHEMA_VERSION` for structural migration warnings, presents a confirmation summary, and runs `create-release.ps1` to publish to GitHub.

**When NOT to use**:
- On a feature branch — merge to main first
- Without reviewing and running the full test suite first
- Without checking for open P0/P1 review findings

**Output**: A published GitHub Release at https://github.com/GPID-WB/compound-gpid/releases

