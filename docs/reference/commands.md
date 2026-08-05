# Commands

Use prompts for guided project workflows and shell commands for installation,
local indexing, and bounded summaries. Skills are loaded by workflows and are
not slash commands.

## Workflow prompts

| Goal | Command |
|---|---|
| Configure a project | `/cg-setup` |
| Set or rethink project direction | `/cg-strategy` |
| Discover possible next work | `/cg-ideate` |
| Clarify a fuzzy task | `/cg-brainstorm` |
| Create an implementation plan | `/cg-plan` |
| Critique a plan | `/cg-plan-review` |
| Implement a plan or phase | `/cg-work [phaseX]` |
| Reproduce and fix a bug | `/cg-fixbug` |
| Review changes | `/cg-review [light|standard|data-risk|architecture|full]` |
| Resolve saved review findings | `/cg-fix-triage [priorities or finding IDs]` |
| Fix editor diagnostics | `/cg-fix-problems` |
| Capture a verified solution | `/cg-compound` |
| Refresh solution knowledge | `/cg-compound-refresh` |
| Rebuild the project Brain | `/cg-brain-rebuild` |
| Resume interrupted work | `/cg-resume` |
| Diagnose an IDE crash | `/cg-diagnose` |
| View roadmap progress | `/cg-roadmap-view` |
| Audit token and context usage | `/cg-token-audit` |
| Manage a project wiki | `/cg-wiki` |
| Link optional GitHub Issues | `/cg-issues` |
| Commit, push, and open a PR | `/cg-commit-push-pr` |
| Diagnose or repair PR checks | `/cg-verify-pr` |

Developer-only commands include `/cg-devtag`, `/cg-review-repos`, and the
compound-gpid-only `/cg-release` workflow. They are not normal consumer-project
steps.

## Shell commands

| Command | Purpose |
|---|---|
| `cg-link [--platforms <list>]` | Link managed platform units into a project |
| `cg-unlink` | Remove managed units while preserving user-owned content |
| `cg-update [<version>|latest|--list|--fix]` | Update, pin, list, or repair the global installation |
| `cg-brain-init` | Initialize optional Team Brain integration |
| `cg-index` | Build or query the local Knowledge Brain index |
| `cg-index --brain` | Rebuild generated Brain artifacts |
| `cg-render-artifact <source>` | Explicitly validate and render one Brainstorm or Plan |
| `cg-render-artifact --automatic <source>` | Validate and render only when automatic HTML is enabled |
| `cg-render-artifact --validate-only <source>` | Validate one artifact without writing HTML |
| `cg-render-artifact --check <source>` | Report its derived view as missing, stale, or current |
| `cg-token-audit` | Generate context, model-governance, and token artifacts |
| `cg-test-summary` | Summarize an existing `tests/last-run.json`; does not run tests |
| `cg-diff-summary` | Summarize changed files, hunks, and risk tags |
| `cg-log-summary` | Summarize branch-local first-parent commits |
| `cg-tree-summary` | Summarize a bounded repository tree |
| `cg-problems-summary` | Summarize optional diagnostics input |

The summary wrappers retain redacted source artifacts under `.cg-docs/token/`.
They do not replace required validation commands.

## Complete contracts

See [Complete Reference](../reference.md) for flags, models, output schemas,
warnings, routing, configuration fields, and command behavior. See
[Workflow Overview](../workflows/index.md) to choose a command by situation.
