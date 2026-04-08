# Workflow

This page explains the Compound GPID workflow loop and how to use each step.

> **Not installed yet?** See [Installation](installation.md) first. For all commands and shortcuts, see [Reference](reference.md).

---

## The Loop

```
Setup -> Strategy -> Ideate -> Brainstorm -> Plan -> Work -> Review -> Compound
                ^           ^            ^                      ^          ^
       (vision/rethink)  (discover)  (one task)             Fix Bug    Refresh
Resume (re-entry at any stage)
```

All steps are invoked as `/cg-*` prompts in GitHub Copilot Chat. **Prompts are not interactive commands** - invoke a prompt, answer its questions when asked, and let it run to completion.

> **Project Charter** (`compound-gpid.md`): Before any workflow step, Copilot reads your
> project's charter to understand objective, deliverables, constraints, and current focus.
> Create or update it via `/cg-setup`. The charter has exactly four sections (Objective, Key
> Deliverables, Constraints, Current Focus) — content that doesn't fit belongs elsewhere
> (see `/cg-setup` for where each type belongs). When content is removed, it will be archived
> to `.cg-docs/archive/charter-history.md` (enabled in a future release). `/cg-resume` will
> nudge you if `last-reviewed` is missing or more than 30 days old.

---

## Steps

### 0. Ideate (`/cg-ideate`)

**When**: You want to discover what to work on next, or need fresh ideas for project improvement.

**What happens**: Launches parallel agents to scan the codebase for pain points, architecture issues, and quality gaps. Generates 8-12 improvement ideas, filters them against the roadmap and project constraints, and presents the survivors ranked by impact/effort ratio. Hands off to `/cg-brainstorm` or `/cg-plan`.

**Output**: Interactive ranked list of improvement ideas.

---

### 1. Brainstorm (`/cg-brainstorm`)

**When**: Requirements are fuzzy, you're not sure what to build, or multiple approaches are possible.

**What happens**: The prompt scans your project, asks clarifying questions one at a time, and proposes 2–3 approaches with pros/cons. Once you pick one, it saves a decision document to `.cg-docs/brainstorms/`. If `roadmap.json` exists, it also offers to register the brainstorm outcome as a feature idea in the roadmap.

**Output**: `.cg-docs/brainstorms/YYYY-MM-DD-<title>.md`

---

### 2. Plan (`/cg-plan`)

**When**: After brainstorming (or when you already know what to build).

**What happens**: The prompt reads any relevant brainstorm, researches your codebase, and creates a step-by-step implementation plan with files to create/modify, tests to write, and acceptance criteria. If `roadmap.json` exists, the prompt also offers to link the plan to a matching roadmap feature, setting its status to `planned`.

**Output**: `.cg-docs/plans/YYYY-MM-DD-<title>.md`

---

### 3. Work (`/cg-work`)

**When**: After a plan exists.

**What happens**: The prompt loads the most recent plan and implements it step by step - writing code, tests, and documentation. It checks against acceptance criteria and suggests commit messages. If the plan is linked to a roadmap feature, the prompt automatically marks it as `active` before work begins.

**Output**: Code, tests, documentation changes.

---

### 4. Fix Bug (`/cg-fixbug`)

**When**: After identifying a bug — during work, review, or standalone.

**What happens**: The prompt walks through five steps: intake (describe the bug and search past bugs), reproduce (write a failing test — hard stop until confirmed), diagnose (root-cause hypothesis), fix (implement and verify — hard stop until confirmed), and document (write a verified bug report).

**Output**: `.cg-docs/solutions/bugs/YYYY-MM-DD-<title>.md`

---

### 5. Review (`/cg-review`)

**When**: After implementing changes.

**What happens**: The prompt dispatches specialized agents based on your configured review depth, collects their findings, and presents them prioritized as P0 (blocking), P1 (critical), P2 (important), P3 (minor). Each finding gets a compound ID (e.g., `P0.1`, `P1.1`, `P2.3`) for selective fixing later. The full report is saved to `.cg-docs/reviews/`.

| Tier | Agents run | Use when |
|------|-----------|---------|
| **Light** | `cg-code-quality` + `cg-testing` | Quick fixes, small changes |
| **Standard** | All 8 agents | Default for most work |
| **Thorough** | All 8 + `cg-learnings-researcher` + `cg-adversarial` | Major features, refactors |

Review reports are saved with per-finding status tracking in YAML frontmatter. Each finding ID (e.g., `P1.2`) is recorded as `open`, `fixed`, or `skipped`. `/cg-resume` shows a summary of open findings across all review files — so unresolved P1s are never lost between sessions.

**Output**: `.cg-docs/reviews/<plan-stem>-review.md`

---

### 5b. Fix Triage (`/cg-fix-triage`)

**When**: In a follow-up session after `/cg-review` has saved a review report.

**What happens**: Loads the most recent review report from `.cg-docs/reviews/`, displays the findings, and applies fixes. Supports selective fixing by priority level or individual finding ID.

| Invocation | Effect |
|-----------|--------|
| `/cg-fix-triage` | Fix all open findings |
| `/cg-fix-triage P1` | Fix all P1 (critical) findings |
| `/cg-fix-triage P1 P3` | Fix all P1 and P3 findings |
| `/cg-fix-triage P1.2 P2.1` | Fix only those specific findings |
| `/cg-fix-triage --migrate` | Backfill per-finding status tracking on legacy review files (from before v0.4.3) |

Each finding you fix is tracked in the review file's frontmatter (`open` → `fixed`). If you decline a finding it becomes `skipped`. Previously resolved findings are counted but not re-shown in future sessions.

**Output**: Applied code fixes + updated review frontmatter + summary of what was fixed, skipped, and remaining.

---

### 6. Compound (`/cg-compound`)

**When**: After solving a non-trivial problem.

**What happens**: Captures the problem, root cause, solution, and prevention strategy as a structured document. This feeds the `cg-learnings-researcher` agent in future thorough reviews.

**Output**: `.cg-docs/solutions/<category>/YYYY-MM-DD-<title>.md`

---

### 6b. Compound Refresh (`/cg-compound-refresh`)

**When**: Periodically (e.g., monthly) or after major refactoring to keep the knowledge base current.

**What happens**: Audits all solution documents in `.cg-docs/solutions/` across 7 categories. Detects drift (file paths moved, APIs changed, dependencies updated, solutions outdated) and classifies each as Keep / Update / Consolidate / Replace / Archive. Presents an interactive audit report and applies approved changes. You can also Skip any entry to defer it for later. Solutions that no longer apply are moved to `.cg-docs/archive/` (never hard-deleted).

**Output**: Updated solution files in `.cg-docs/solutions/`; deprecated solutions archived to `.cg-docs/archive/`.

---

### 7. Resume (`/cg-resume`)

**When**: At the start of a session when you have interrupted work.

**What happens**: Checks whether your project schema version is current and warns if `cg-update` is needed. Scans `.cg-docs/plans/` for active plans, `.cg-docs/brainstorms/` for decided-but-unplanned brainstorms, and inspects `git status`/`git log` for in-progress code changes. Presents a structured summary and suggests the most logical next action. If `roadmap.json` exists, it also displays milestone progress with completion counts, surfaces roadmap/plan status drift, and suggests unstarted roadmap ideas from active milestones.

**Output**: A structured context summary and a suggested continuation path.

---

### Roadmap (`@cg-roadmap`)

**When**: Any time you want to capture a milestone, feature idea, or check project progress.

**What happens**: The agent reads and modifies `roadmap.json` -- adding milestones, registering features, linking plans, and updating statuses. Other prompts (`/cg-plan`, `/cg-work`, `/cg-brainstorm`) dispatch this agent automatically for roadmap updates (when `roadmap.json` exists at the project root).

**How to use**: Invoke `@cg-roadmap` directly in Copilot Chat. Examples:
- "Add a milestone for survey harmonization"
- "I have an idea for automated PPP validation -- add it to the pipeline milestone"
- "Show me the roadmap progress"
- "Remove the feature about X, we're not doing it anymore"

**Output**: Updated `roadmap.json` in the project root.

---

### Strategy (`/cg-strategy`)

**When**: You have a full project vision to structure into milestones and features — at any stage of the project. Use at day zero to build the initial roadmap, mid-project to rethink direction, or after a milestone to plan the next phase.

**What happens**: Reads your project charter, roadmap, and recent work. Asks focused questions one at a time to understand your ideas, surface trade-offs, and clarify priorities. Proposes a concrete roadmap structure for your approval, then dispatches `@cg-roadmap` to apply the changes. Saves a record of the session to `.cg-docs/strategy/`.

**Hard prerequisite**: `compound-gpid.md` must exist (run `/cg-setup` first). `roadmap.json` is optional — `/cg-strategy` will create it if needed.

**Output**: Updated `roadmap.json` + `.cg-docs/strategy/YYYY-MM-DD-<title>.md`

---

| Aspect | Prompts | Agents | Skills |
|--------|---------|--------|---------|
| **What they are** | Workflow commands | Specialized reviewers / roadmap manager | Reference knowledge |
| **How you use them** | Type `/cg-setup`, `/cg-strategy`, `/cg-brainstorm`, etc. | `@cg-roadmap` (direct); review agents dispatched by `/cg-review` | Referenced by prompts/agents |
| **Interactive?** | No - follow the workflow | No - automated | No (passive by design) |
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

**When**: After the Compound step, when you are ready to publish a new version of compound-gpid to GitHub.

**What happens**: Detects the latest git tag, analyzes commits since then to suggest the next semver version, reads `.cg-docs/` entries dated after the last release to draft curated release notes, checks `SCHEMA_VERSION` for structural migration warnings, presents a confirmation summary, and runs `create-release.ps1` to publish to GitHub.

**Output**: A published GitHub Release at https://github.com/GPID-WB/compound-gpid/releases

