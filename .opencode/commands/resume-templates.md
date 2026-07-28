# Resume Templates Reference

Templates used by `/cg-resume`. Loaded on-demand — do not bulk-load at prompt start.

---

## Session Context Header

If `compound-gpid.md` exists:

```markdown
## Session Context

**<project-name>**: <objective> | Focus: <current-focus>

Language: <language> | Type: <project-type> | Review depth: <review-depth>
```

If `compound-gpid.md` does NOT exist:

```markdown
## Session Context

> no-charter No project charter found. Run `/cg-setup` to create one.

Language: <language> | Type: <project-type> | Review depth: <review-depth>
```

---

## Pending Work Sections

```markdown
### Active State Snapshot
Workflow: `<workflow>` | Status: `<status>` | Branch: `<branch>`
Plan: `<plan path or none>`
Execution report: `<execution report path or none>`
Current phase: `<currentPhase or none>`
Evidence: `<compact evidenceStatus counts or IDs>`
Artifacts: `<artifactRefs paths only>`
Unresolved decisions: `<count and one-line summaries>`
Exact next command: `<nextCommand>`

### 🔄 In-Progress Plans (<count>)
1. `<date>` — **<title>** [scope: <scope>] [effort: <estimated-effort>]
   Tags: <tags>
2. ...

### 📋 Pending Review Findings (<count>)
1. `<filename>` — <open-P0-count> blocking, <open-P1-count> critical, <open-P2-count> important, <open-P3-count> minor open findings
   → Apply with `/cg-fix-triage`
2. ...

### 💡 Decided Brainstorms Without a Plan (<count>)
1. `<date>` — **<title>**
   → Ready for `/cg-plan`
2. ...

### 🕐 Recent Git Activity
Branch: `<branch-name>`
Last commits:
- <hash> <message>
- <hash> <message>
...

Uncommitted changes: <count files changed, or "none">

---

### 📊 Milestone Progress (<milestone count>)

> Only include this section if `roadmap.json` exists.

**<milestone title>** -- <done>/<total> features [<status>]
  _<objective>_
  ✅ <done feature title>
  🔄 <active feature title>
  📋 <planned feature title>
  💡 <idea feature title>

**<next milestone>** -- ...

> If any cross-check discrepancies were found:
> ⚠️ Feature '<title>' is marked active but its plan is completed.
>   Run `@cg-roadmap` to update its status.
> ⚠️ Feature '<title>' has a stale plan reference ('<path>' not found).

> Scope health nudge <!-- SCOPE_THRESHOLD: 60% --> -- include only when more than 60% of all features
> across milestones are `idea` or `planned`:
> ⚠️ **Roadmap scope check**: <N> of <total> features haven't been started.
> Consider reviewing your roadmap with `@cg-roadmap` to archive or
> deprioritize items that aren't near-term. Or run `/cg-strategy` to
> rethink the roadmap scope.

### ⚠️ Maintenance Nudges

> Only include this section if a nudge was collected in Step 2e or Step 2f.

- <nudge text collected from Step 2e or Step 2f>

---
```

---

## Next Action Suggestions

```markdown
> What would you like to do?
> 1. Continue: **<title of most recent in-progress plan>** — `/cg-work`
> 2. Apply review findings: **<review filename>** — `/cg-fix-triage`
> 3. Plan: **<title of decided brainstorm>** — `/cg-plan`
> 4. Review uncommitted changes — `/cg-review`
> 5. Start something new — `/cg-brainstorm`
```

Adapt the options to what's actually available. If only one option applies, just suggest it directly.

If `roadmap.json` exists and any `in-progress` milestone has features with `status: "idea"`, add:

> N. Plan a roadmap idea: **<feature title>** (in <milestone title>) -- `/cg-plan`

If **scope-check condition** holds (>60% unstarted features AND no recent strategy document), add:

> N. Rethink the roadmap scope — `/cg-strategy`
