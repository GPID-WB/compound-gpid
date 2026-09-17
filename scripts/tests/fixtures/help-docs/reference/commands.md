# Commands

Find a command by the result you need. Start with the [eight task recipes](../workflows/index.md#task-recipes),
then use the entries below for prerequisites, output, approval, failure, and the
next step. Examples are illustrative; paths, IDs, versions, and source data must
match your project. They are not instructions to publish this documentation.

Use prompts for guided project workflows and shell commands for installation,
local indexing, and bounded summaries. Skills are loaded by workflows and are
not slash commands.

## Task-to-command cheat sheet

Print this page with your browser's Print command. The printed page keeps suite
labels and build identity, but removes navigation and copy controls. A local or
unverified build does not identify a published version. Review the linked recipes
and approval gates before you run a command; this table is not authority to apply,
commit, or publish changes.

| Task | Suite and context | Starting command | Verify or approve |
| --- | --- | --- | --- |
| Configure a project | Technical (CG), AI chat | `/cg-setup` | Check the project root and suite selection |
| Fix a software error | Technical (CG), AI chat | `/cg-fixbug The launcher fails when the project path contains spaces` | Reproduce the error and verify the repair |
| Complete a small technical task | Technical (CG), AI chat | `/cg-light-work <task>` | Approve the saved plan and review the result |
| Deliver an approved larger change | Technical (CG), AI chat | `/cg-work phase1` | Use the approved plan and required phase tests |
| Resolve technical review findings | Technical (CG), AI chat | `/cg-fix-triage` | Re-review the recorded findings with evidence |
| Scope research | Research (CR), AI chat | `/cr-brainstorm Compare poverty estimates across survey rounds` | Resolve comparability assumptions before planning |
| Execute approved research | Research (CR), AI chat | `/cr-work phase1` | Check evidence, methods and researcher decisions |
| Resume technical work | Technical (CG), AI chat | `/cg-resume` | Confirm the current state and next approved action |

Use [task recipes](../workflows/index.md#task-recipes) for the complete technical
procedures and the [Research Handbook](../research/index.md) for research work.
Search uses only the current channel's section index. If search is unavailable,
continue with navigation or use Retry search. Copy failures offer Select code for
manual copying. Output and prompted transcripts are not copyable invocations.

## Workflow prompts

> [!TECHNICAL] These are slash prompts for AI chat, not terminal commands. Technical workflow prompts need `cg` in the active suite selection. The canonical module registry, not a prefix heuristic, controls ownership and eligibility.

Before a mutating workflow, check the project root, charter/configuration, active
suite, and relevant saved artifacts. Read the proposed scope and approve the
required gates. A workflow result is not permission to commit, publish, or skip
verification. Exact syntax and generated summaries stay in the
[Complete Reference](../reference.md#copilot-chat-prompts); this page owns editorial
recipes, not a second generated facts catalog.

| Goal | Command |
|---|---|
| Configure a project | `/cg-setup` |
| Set or rethink project direction | `/cg-strategy` |
| Discover possible next work | `/cg-ideate` |
| Clarify a fuzzy task | `/cg-brainstorm` |
| Create an implementation plan | `/cg-plan` |
| Critique a plan | `/cg-plan-review` |
| Execute a qualified small technical task | `/cg-light-work <task>` |
| Execute an approved saved Plan or phase | `/cg-work [phaseX]` |
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
| Manage the complete skill lifecycle | `/cg-skill <operation>` |
| Manage a project wiki | `/cg-wiki` |
| Link optional GitHub Issues | `/cg-issues` |
| Commit, push, and open a PR | `/cg-commit-push-pr` |
| Diagnose or repair PR checks | `/cg-verify-pr` |

## Research workflow prompts

> [!RESEARCH] These chat prompts require `suites: [cr]` or `[cg, cr]`. They do not require the CG suite. The researcher owns normative choices and publication decisions; review is not certification of a claim.

Use `/cr-*` for research, statistical, and publication work. Use the standard
technical `/cg-brainstorm` -> `/cg-plan` -> `/cg-work` cycle for larger,
ambiguous, security-sensitive, schema, dependency, or destructive technical
work.

| Goal | Command |
|---|---|
| Scope a research question and surface normative choices | `/cr-brainstorm` |
| Create a research plan with evidence and integrity gates | `/cr-plan` |
| Execute a research plan or phase | `/cr-work [phaseX]` |
| Run task-aware research and engineering review | `/cr-review` |
| Capture a verified research lesson | `/cr-compound` |

The [Research Handbook](../research/index.md) explains when to use these
commands and what a newcomer should expect from each handoff.

Developer-only commands include `/cg-devtag` and `/cg-compound-gpid-rd`.
Generic `/cg-release plan|start|status|resume` delegates unchanged arguments to
the separately installed controller without requiring a GPID charter. Only its
explicit legacy bridge/recovery path is GPID-only and needs specific maintainer
authority. The supplied publisher is disabled; no live release support is implied.
`/cg-compound-gpid-rd` has four forms: delta
(`/cg-compound-gpid-rd`), full (`/cg-compound-gpid-rd --full`), add
(`/cg-compound-gpid-rd --add <URL>`), and remove
(`/cg-compound-gpid-rd --remove <id>`). `rd` means `research-development`, and
its current scope is public GitHub repository research for Compound GPID
maintainers. Its development-repository guardrail stops it before registry,
network, utility, or write operations in consumer projects.

## Shell commands

Shell commands run in a terminal after installation. Core `.cmd` launchers work
in Windows PowerShell; POSIX wrappers run in bash/zsh. The five summary wrappers
are POSIX-only: on Windows use `python scripts/cg_summary.py <kind>` from the
source checkout, with the same options. Do not add a leading slash.

| Command | Purpose |
|---|---|
| `cg-link [--platforms <list>]` | Link managed platform units into a project |
| `cg-unlink` | Remove managed units while preserving user-owned content |
| `cg-update [<version>|latest|--list|--fix]` | Update, pin, list, or repair the global installation |
| `cg-kilo [<kilo arguments>]` | Launch Kilo through the certified containment preflight; required for Kilo with Codex/Claude roots |
| `cg-brain-init` | Initialize optional Team Brain integration |
| `cg-index` | Build or query the local Knowledge Brain index |
| `cg-index --brain` | Rebuild generated Brain artifacts |
| `cg-render-artifact <source>` | Explicitly validate and render one Brainstorm or Plan |
| `cg-render-artifact --automatic <source>` | Validate and render only when automatic HTML is enabled |
| `cg-render-artifact --validate-only <source>` | Validate one artifact without writing HTML |
| `cg-render-artifact --check <source>` | Report its derived view as missing, stale, or current |
| `cg-token-audit` | Generate context, model-governance, and token artifacts |
| `cg-skill <operation>` | Run deterministic skill discovery and lifecycle operations |
| `cg-test-summary` | Summarize an existing `tests/last-run.json`; does not run tests |
| `cg-diff-summary` | Summarize changed files, hunks, and risk tags |
| `cg-log-summary` | Summarize branch-local first-parent commits |
| `cg-tree-summary` | Summarize a bounded repository tree |
| `cg-problems-summary` | Summarize optional diagnostics input |
| `cg-publish-markdown <source>` | Publish generic Markdown through the separate contained publisher |
| `cg-release plan|start|status|resume` | Use the separately installed asynchronous release controller; supplied publisher disabled |

The summary wrappers retain redacted source artifacts under `.cg-docs/token/`.
They do not replace required validation commands.

## Technical Entry Checklist

Each row gives one exact example invocation. Combine it with the common chat
prerequisites above. The last column distinguishes a common failure from the
next useful action; it is not an automatic command chain.

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `/cg-setup` | Configure a technical project / not to force an inactive suite | Installed and linked host; eligible CG project | Confirmed settings and `.cg-docs/`; approve configuration choices | Wrong project or suite / check configuration, then choose a task |
| `/cg-strategy` | Set project direction / not for one bounded bug | Existing `compound-gpid.md`; resolved `project-type` from local settings or clarification | Strategic decisions and roadmap proposals; approve charter changes; roadmap agent owns writes | Missing charter / run `/cg-setup`; resolve a missing or blank project type before proceeding, then `/cg-ideate` |
| `/cg-ideate` | Find useful next work / not to start implementation | Current goals and constraints | Filtered ideas; selection remains human | Ideas repeat existing work / check roadmap, then `/cg-brainstorm` |
| `/cg-brainstorm Add offline validation to the importer` | Clarify uncertain requirements / not to execute a plan | A technical question and constraints | Saved brainstorm after approach confirmation; no implementation approval implied | Scope exceeds one task / split decisions, then `/cg-plan` |
| `/cg-plan` | Turn a clear task into a saved plan / not to implement | Approved direction and current source | Plan with completion contract; review and approve before work | Missing acceptance evidence / revise, then `/cg-plan-review` |
| `/cg-plan-review` | Critique a saved plan / not to certify implemented behavior | Saved plan | Findings and proposed corrections; approve consequential changes | Wrong plan selected / select the intended plan, then `/cg-work phase1` |
| `/cg-light-work Add a missing explanatory label to the settings page` | One qualified low-risk task / not bugs, research, security, schemas, dependencies, or destructive work | Bounded technical scope and available tests | Approved saved Plan, Work Report, mandatory light Review Report; separate compounding opt-in | Qualification fails / use brainstorm and plan rather than bypassing it |
| `/cg-work phase1` | Implement an approved saved phase / not unmatched inline tasks | Approved Plan; previous phase complete | Source changes and Work Report; executed completion evidence and phase gate | Missing evidence or predecessor / resolve blocker, then rerun the phase |
| `/cg-fixbug The launcher fails when the project path contains spaces` | Fix reproducible wrong behavior / not vague feature requests | Expected-behavior source and reproduction | Diagnosed fix with red-green evidence; verification before knowledge capture | Cannot reproduce / record conditions rather than claim fixed, then review |
| `/cg-review standard` | Review changed technical work / not replace research review | Checkable diff and appropriate risk route | Prioritized review report; default review immediately applies `safe_auto` fixes and can edit files; manual fixes require approval. Use `--report-only` and decline interactive Fix offers to select findings before triage | Missing test evidence / obtain evidence, then `/cg-fix-triage` |
| `/cg-fix-triage P0 P1` | Resolve saved findings / not invent an unsaved review | Review artifact and selected priorities | Tracked finding status and tested fixes; accepted risk needs approval | Stale finding or unresolved test / retain it, then re-review |
| `/cg-fix-problems` | Repair editor diagnostics / not diagnose a failing logical test | Available Problems diagnostics | Selected diagnostic fixes; respect offered scope/severity choices | Diagnostics unavailable / obtain them or use the failing test workflow |
| `/cg-compound` | Capture a verified solution / not write success before proof | Confirmed fix and passing evidence | Reusable solution with boundaries; canonical source changes are proposed, not silently applied | Missing verification / verify first, then refresh Brain if needed |
| `/cg-compound-refresh` | Audit stale solution knowledge / not rewrite historical evidence | Existing `.cg-docs/solutions/` | Staleness findings and reviewed maintenance | Conflicting lessons / resolve against current source, then rebuild Brain |
| `/cg-brain-rebuild` | Rebuild generated local knowledge / not edit source lessons indirectly | Valid knowledge sources and Python wrapper | Brain/index artifacts; inspect errors and warnings | Invalid frontmatter / repair source metadata, then rerun |
| `/cg-resume` | Recover interrupted work / not approve pending work automatically | Saved plan/report/history; state pointer if present | Context and exact next-command handoff; verify it against current files | Stale state pointer / reconcile artifacts before running its command |
| `/cg-diagnose` | Diagnose an IDE crash / not use unsafe test reruns | Available logs and working-tree state | Bounded diagnosis and recovery advice; preserve uncommitted work | Missing logs / state uncertainty, then follow the safe recovery path |
| `/cg-roadmap-view --status active` | Inspect roadmap work / not mutate roadmap | Valid `roadmap.json` | Read-only view | Invalid or absent roadmap / use approved roadmap-agent maintenance |
| `/cg-token-audit` | Inspect context cost / not claim measured savings from estimates | Workflow/context inputs | Token/context artifacts and bounded recommendations; distinguish estimates | Missing telemetry / label it unavailable, then review recommendations |
| `/cg-wiki status` | Inspect or maintain project wiki / not overwrite manual prose | Wiki configuration and ownership markers | Status; use `init`/`rebuild` only for the intended operation and ownership | Missing configuration / initialize deliberately, then inspect generated diff |
| `/cg-issues status` | Inspect optional roadmap-linked issues / not create remote issues by default | Roadmap and authenticated GitHub access when needed | Status; mutating link/backfill/adopt/setup modes have their own gates | Missing credentials or ambiguous link / resolve before mutation |
| `/cg-commit-push-pr --base dev` | Publish reviewed commits and a PR / not bypass tests or leak secrets | Authorized git publication, correct base, passing gates | Commits, push, PR URL after review of intended files | Failed hook/CI or unrelated files / fix or exclude, then verify PR |
| `/cg-verify-pr --propose` | Diagnose current PR checks / not repair without scope | Existing PR and GitHub access | Observe-only diagnosis with proposed repairs; normal mode has bounded repair | Wrong/missing PR / identify it, then approve and verify fixes |
| `/cg-skill find --suite cg --platform kilo` | Discover skills / not infer activation from eligibility | Eligible CG prompt, installed dispatcher, local registry; current skill-management capability supports `cg` only | Deterministic findings; reads first, exact digest and explicit approval for mutations | Stale manifest / prospective is not active; follow [Skill Management](../skills/management/index.md) |

## Research Entry Checklist

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `/cr-brainstorm Compare poverty estimates across survey rounds` | Frame a research question / not assume comparability | Active CR, population and evidence description | Scoped alternatives and normative choices; human approval before selecting a method | Missing welfare/PPP/design facts / obtain them before `/cr-plan` |
| `/cr-plan` | Plan research evidence and checks / not implement an unapproved question | Approved research direction and available sources | Saved research plan with integrity and evidence gates | Unsupported assumptions / revise or bound them, then `/cr-work phase1` |
| `/cr-work phase1` | Execute approved research / not bypass missing data or P0 gates | Saved plan, required inputs, reproducible environment | Research outputs, provenance, specification and run records; verified completion | Missing input, seed, or integrity evidence / stop that step, then `/cr-review` after resolution |
| `/cr-review` | Review checkable research / not certify causal truth | Methods, code, outputs, provenance, task classification | Task-aware research and engineering findings; P0 blocks release | Missing derivation or source / supply evidence and re-review |
| `/cr-compound` | Capture verified research learning / not preserve an unchecked claim as fact | Resolved serious findings and verified result | Research lesson with evidence, limitations, and rejected alternatives | Unresolved integrity issue / fix before knowledge capture |

## Shared Capability Entries

> [!SHARED] Shared describes capability support metadata, not automatic prompt activation. The current registry owns `cg-*` prompt files in the Technical suite; a shared capability or website badge does not activate an otherwise ineligible chat prompt. Check the resolved project configuration and use documented shell entry points where applicable.

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `/cg-render-doc docs/manual.md` | Render a document / not change its canonical decisions | Eligible prompt, contained source, renderer | Derived HTML or validation result; typed Plan/Brainstorm routes stay strict; theme selection is explicit | Invalid source or ownership collision / correct source, then check freshness |

## Maintainer Entries

The merged help assets are present, but host runtime certification is a separate
gate. A listed command does not establish that an installed host supports it.

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `/cg-help` | Find catalog-backed command information / not execute the described task | Installed backend, fresh catalog, and verified host transport | Bounded lookup or recovery text; host support remains unverified until source-bound evidence passes | Missing backend or unsupported transport / stop and use the command reference |
| `/cg-autopilot` | Inspect the approved Kilo bootstrap-probe workflow / not run production autopilot | Kilo contract and explicit probe authorization; unsupported on other hosts | Probe evidence only; production execution remains disabled | Unsupported host or missing authorization / use ordinary workflow commands |

These operations are distinct from ordinary project delivery. Maintainer-only
and Development labels describe role/risk, not another suite. No example below
authorizes a release, tag, or repository mutation.

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `/cg-devtag` | Authorized plugin development install test / not a normal consumer release | Plugin checkout, correct branch, tag authority | Confirmed development tag and push; inspect version and git state first | Unauthorized branch or existing tag / stop, never move the tag |
| `/cg-compound-gpid-rd --full` | Research public repository features / not research in a consumer project | Exact Compound GPID charter, valid registry and network access | Repository assessments; add/remove modes need their distinct confirmations | Guardrail or registry failure / repair approved input, then select a feature |
| `/cg-release plan --version 1.5.0-rc.1 --json` | Preview a generic release request / not use legacy recovery implicitly | Separately installed controller and its repository policy; no GPID charter required in generic mode | Read-only non-reserving plan; start needs confirmation; submitted/published is not complete | Missing CLI or disabled publisher / report blocker; see [Release Controller](../release-controller.md) |

## Shell Entry Checklist

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `cg-help --help` | Inspect backend CLI syntax / not send query text through the shell | Installed wrapper and Python 3.8+ | Usage text only; prepared-file transport and host certification are separate | Missing wrapper / check installation; do not invent a query invocation |
| `cg-autopilot-control inspect` | Read control eligibility / not start autonomous execution | Installed helper, explicit root, plan, batches and base arguments | Read-only eligible/blocked report; no production execution | Missing required arguments / inspect CLI usage and the autopilot contract |

Examples below run in a terminal at the project root unless noted. Installation
must put the wrapper on PATH. For Windows summary examples, replace the wrapper
with `python scripts/cg_summary.py test|diff|log|tree|problems` as applicable;
the vertical bars denote alternatives, not literal shell syntax.

| Command and example | Use when / do not use when | Prerequisites | Expected output and verification or approval boundary | Common failure / next useful step |
| --- | --- | --- | --- | --- |
| `cg-link --platforms copilot` | Link a project / not overwrite user-owned units | Installed source, project root, chosen host | Managed links/copies and ownership record; review reported conflicts | Conflicting user file / preserve it and follow [installation recovery](../installation.md) |
| `cg-unlink` | Remove managed install units / not delete project content | Linked project and ownership state | Managed units removed with confirmation; user content preserved | Modified or unowned path / inspect rather than force deletion |
| `cg-update --list` | List versions before updating / not infer root docs identity | Installed source and release access | Version list; update/pin/fix forms change installation only when selected | Network or local-change blocker / resolve, then follow [versioning](../versioning.md) |
| `cg-kilo --version` | Launch through containment checks / not bypass unsupported host state | Installed Kilo and supported minimum/capabilities | Preflight result and child Kilo output; failure blocks launch | Failed containment or projection / use reported remedy, not direct launch |
| `cg-brain-init --repo example/team-brain --manager example-manager` | Configure optional team knowledge / not send private project data automatically | Reviewed repository, manager, GitHub authority | Team Brain configuration/scaffolding; confirm sharing scope | Missing authority or repository / resolve before setup |
| `cg-index query --intent work --query "navigation" --budget 700 --format md` | Retrieve local lessons / not treat stale lessons as authority | Valid `.cg-docs/` sources and Python | Bounded source-linked retrieval; warnings are not test proof | Invalid metadata / repair sources; use `cg-index --brain` for rebuild |
| `cg-render-artifact --validate-only .cg-docs/plans/example.md` | Validate a saved typed artifact / not render generic prose as a Plan | Existing project-contained Plan or Brainstorm; replace example path | Validation only; explicit render creates derived view; `--check` tests freshness | Schema error / fix canonical Markdown, never execute HTML |
| `cg-publish-markdown --validate-only docs/manual.md` | Validate generic Markdown / not bypass typed-artifact checks | Contained Markdown/resources, valid destination ownership | Validation; explicit publication writes a derived document view | Unsafe resource or ownership collision / repair source or approved destination |
| `cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations` | Produce context-cost artifacts / not run correctness tests | Project source and wrapper dependencies | JSON/Markdown cost reports and recommendations; review estimates | Missing telemetry / label limitations, then inspect recommendations |
| `cg-skill --format json help` | Inspect lifecycle operations / not treat read output as apply permission | Installed dispatcher and local descriptors | Stable result envelope; [full operation checklist](../skills/management/index.md#operation-reference) covers all 12 operations | Nonzero exit / follow exact remediation; never treat as partial success |
| `cg-test-summary --root . --format json` | Summarize an existing test run / not run tests | Fresh `tests/last-run.json`; POSIX wrapper or Python form | Bounded summary and redacted source artifact; check timestamp/completeness | Missing/stale run / execute the actual safe tests first |
| `cg-diff-summary --root . --format md` | Inspect a bounded git diff / not approve changes | Git repository; POSIX wrapper or Python form | Changed files/risk summary and redacted source artifact | Missing baseline / select a valid scope, then inspect actual diff |
| `cg-log-summary --root . --format json` | Summarize branch commits / not infer uncommitted changes | Git history; POSIX wrapper or Python form | First-parent summary; verify relevant commits before publication | Missing history / obtain the correct history, then review diff |
| `cg-tree-summary --root . --max-entries 120 --format md` | Inspect a bounded tree / not claim omitted files are absent | Readable project; POSIX wrapper or Python form | Bounded inventory with exclusions; use focused inspection next | Entry limit / narrow the requested scope |
| `cg-problems-summary --root . --input problems.json --format json` | Summarize supplied diagnostics / not claim editor state without input | Actual diagnostics JSON/text; POSIX wrapper or Python form | Summary or explicit unavailable result; verify input freshness | Missing/malformed input / obtain diagnostics, then fix selected errors |
| `cg-release plan --version 1.5.0-rc.1 --json` | Preview a release / not enable the disabled publisher | Installed standalone controller and validated policy | Non-reserving plan; `start`, `status`, `resume` have separate effects and checks | Policy/installation blocker / use [controller guidance](../release-controller.md), not an implicit legacy fallback |

## Complete contracts

See [Complete Reference](../reference.md) for flags, models, output schemas,
warnings, routing, configuration fields, and command behavior. See
[Workflow Overview](../workflows/index.md) to choose a command by situation.
See the [Modular Guide](../modular-guide.md) for suite activation and boundaries.
See [Skill Management](../skills/management/index.md) for operation grammar,
roles, plan/apply behavior, security controls, and migration.
