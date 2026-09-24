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

<!-- cg:auto:help-commands -->
| Command | Suites | Purpose |
| --- | --- | --- |
| /cg-autopilot &lt;authorized read-only bootstrap request&gt; | CG | Coordinate Kilo autopilot bootstrap probes; production execution is not enabled. |
| /cg-brain-rebuild | CG | Rebuild the project knowledge brain &#40;BRAIN.md + indexes&#41;. |
| /cg-brainstorm | CG | Brainstorm answers about what to build and how. Use when requirements are fuzzy. |
| /cg-commit-push-pr | CG | Stage changes into logical commits, push, and open a PR with plan-driven description. |
| /cg-compound | CG | Capture a solved problem as reusable knowledge. Offers canonical .github/ updates; the user applies them manually after fixing a non-trivial issue. |
| /cg-compound-gpid-rd &#91;--full&#124;--add &lt;URL&gt;&#124;--remove &lt;id&gt;&#93; | CG | Research public GitHub repos for features to integrate into Compound GPID and manage the review registry. Developer-only. |
| /cg-compound-refresh | CG | Audit and refresh .cg-docs/solutions/ for staleness, drift, and consolidation opportunities. |
| /cg-devtag | CG | Create a dev tag &#40;v&lt;MAJOR&gt;.&lt;MINOR&gt;.&lt;PATCH&gt;.9000+&#41; on the current branch and push it to origin. Enables end-to-end installation testing via cg-update before an official release. Developer-only. |
| /cg-diagnose | CG | Diagnose VS Code crashes. Inspects logs, classifies the crash category, checks for uncommitted work, and recommends recovery steps. |
| /cg-fix-problems | CG | Interactive VS Code diagnostics fixer. Scans all workspace files for errors, warnings, and info diagnostics, lets the user select scope and severity, then applies fixes. Dispatches @cg-fix-problems agent. |
| /cg-fix-triage &#91;P0&#124;P1&#124;finding-id&#124;--migrate&#93; | CG | Apply review findings from a saved review report. Fixes all findings or a subset by ID/priority. |
| /cg-fixbug | CG | Structured bug-fix workflow: establish the expected-behavior source in Step 1.5, perform test-gap classification in Step 2.5, and require red-green proof. |
| /cg-help &#91;command or query&#93; | CG, CR | Find evidence-backed Compound GPID slash and shell command help. |
| /cg-ideate | CG | Generate, critique, and filter improvement ideas for the project. Use before /cg-brainstorm when you want to discover what to work on next. |
| /cg-issues &#91;status&#124;backfill&#124;link&#124;adopt&#124;setup&#93; | CG | Manage GitHub Issues linked to roadmap work items. Modes: status &#40;default, read-only&#41;, backfill, link, adopt, setup. |
| /cg-light-work &#91;--no-branch&#124;--no-brain&#124;--no-html&#93; &lt;task&gt; | CG | Qualify and execute one small technical task with bounded discovery, light review, and explicit compounding consent. |
| /cg-plan | CG | Create a structured implementation plan with research. Use after brainstorming or when requirements are clear. |
| /cg-plan-review | CG | Review an implementation plan for risks, over-engineering, missing edge cases, and flawed assumptions. Use after /cg-plan or on any existing plan. |
| /cg-release vX.Y.Z.&lt;build&gt; &#91;--source-branch branch&#93; | CG | Run generic controller commands unchanged or publish a GPID four-part prerelease through the existing PowerShell release flow. |
| /cg-render-doc &lt;source&gt; &#91;--theme reference&#124;editorial&#93; | CG | Render a workflow artifact or generic Markdown document to curated HTML. Routes typed artifacts to cg-render-artifact and generic documents to cg-publish-markdown. Supports --theme selection &#40;reference or editorial&#41;. |
| /cg-resume | CG | Load context and resume interrupted work. Use at the start of a session to pick up where you left off. |
| /cg-review &#91;light&#124;standard&#124;data-risk&#124;architecture&#124;full&#93; &#91;mode:autofix&#124;mode:verify&#93; | CG | Run multi-agent code review on recent changes. Produces prioritized P0/P1/P2/P3 findings. |
| /cg-roadmap-view &#91;--milestone&#124;--tasks&#124;--detail&#124;--status&#124;--wip&#124;--plan&#124;--help&#93; | CG | Visualize the project roadmap in chat. Supports flags: --milestone, --tasks, --detail, --status, --wip, --plan, --help. Dispatches @cg-roadmap-view agent for rendering. |
| /cg-setup | CG | Configure Compound GPID for this project and load context for returning projects. |
| /cg-skill &lt;operation&gt; &#91;arguments&#93; | CG | Discover, import, validate, activate, update, audit, deprecate, and remove skills through one lifecycle command. |
| /cg-strategy | CG | Strategic project visioning and direction-setting. Use when you have a full project in mind to structure, or when you need to rethink direction mid-project. Dispatches @cg-roadmap for all roadmap writes. |
| /cg-token-audit | CG | Analyze Compound GPID token/context usage and suggest cost-efficient workflow choices. |
| /cg-verify-pr &#91;--propose&#93; | CG | Check CI status on current PR, classify failures, and auto-fix with review agents. Use --propose for observe-only diagnosis. |
| /cg-wiki &#91;status&#124;init&#124;rebuild&#124;restructure&#124;convert&#124;help&#93; | CG | Manage the project wiki: initialize, rebuild pages, restructure sections, check status, or convert to GitHub Wiki format. |
| /cg-work &#91;phaseX&#93; &#91;review&#93; &#91;deviate:&lt;policy&gt;&#93; | CG | Implement a /cg-plan plan. Supports /cg-work &#91;phaseX&#93;, review, and deviate controls. |
<!-- cg:auto:end -->

## Research workflow prompts

> [!RESEARCH] These chat prompts require `suites: [cr]` or `[cg, cr]`. They do not require the CG suite. The researcher owns normative choices and publication decisions; review is not certification of a claim.

Use `/cr-*` for research, statistical, and publication work. Use the standard
technical `/cg-brainstorm` -> `/cg-plan` -> `/cg-work` cycle for larger,
ambiguous, security-sensitive, schema, dependency, or destructive technical
work.

<!-- cg:auto:help-research-commands -->
| Command | Suites | Purpose |
| --- | --- | --- |
| /cg-help &#91;command or query&#93; | CG, CR | Find evidence-backed Compound GPID slash and shell command help. |
| /cr-brainstorm | CR | Research brainstorm — clarify fuzzy research requirements. Classifies task type &#40;theory, EDA, implementation, ML, writing, etc.&#41; and guides methodology decisions. Use for economics and econometrics research tasks. |
| /cr-compound | CR | Research compound — capture a solved research problem for future reuse. Extends /cg-compound with research-specific categories: identification, specification, derivation, ml-methodology, reproducibility. |
| /cr-plan | CR | Research plan — structured implementation plan for research tasks. Use after /cr-brainstorm to create concrete steps. |
| /cr-review | CR | Research review — multi-agent code and methodology review. Orchestrates cg-&#42; agents &#40;code quality, testing, reproducibility&#41; and cr-&#42; agents &#40;research integrity, mathematical verification, identification audit, econometric reasoning&#41;. Produces prioritized P0/P1/P2/P3 findings. |
| /cr-work &#91;phaseX&#93; | CR | Research work — implement a research plan step by step. Supports /cr-work &#91;phaseX&#93;. Enforces P0 seed, provenance, and specification logging requirements. |
<!-- cg:auto:end -->

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

<!-- cg:auto:help-shell-commands -->
| Command | Suites | Purpose |
| --- | --- | --- |
| cg-autopilot-control inspect --root &lt;repo&gt; --plan &lt;path&gt; --batches &lt;segments&gt; --base &lt;branch&gt; &#91;--ci-timeout 30m&#93; | CG | Inspect Kilo autopilot eligibility and prior control state without writing. |
| cg-brain-init --repo &lt;owner/name&gt; --manager &lt;github-user&gt; | CG, CR | Create and scaffold a public team Brain repository, or configure a project to use an existing repository. |
| cg-diff-summary &#91;arguments&#93; | CG, CR | Create a bounded summary of the current Git diff. |
| cg-help &#40;--prepare-request&#124;--consume-request &lt;uuid&gt;&#124;--render-selection &lt;uuid&gt;&#41; &#91;--root &lt;path&gt;&#93; &#91;--platform &lt;copilot&#124;claude-code&#124;codex&#124;opencode&#124;kilo&gt;&#93; &#91;--catalog &lt;path&gt; --source-root &lt;path&gt;&#93; | CG, CR | Query evidence-backed command help through confined single-use request and selection files. |
| cg-index query --intent &lt;intent&gt; --query &lt;text&gt; --budget &lt;tokens&gt; --format &lt;json&#124;md&gt; | CG, CR | Build or query the bounded local Knowledge Brain index. |
| cg-kilo &#91;&lt;Kilo arguments&gt;&#93; | CG, CR | Run the certified contained Kilo launch preflight and launch Kilo when it passes. |
| cg-link &#91;--platforms &lt;comma-separated-platforms&gt;&#93; | CG, CR | Link selected Compound GPID platform assets into a project. |
| cg-log-summary &#91;arguments&#93; | CG, CR | Create a bounded summary of recent branch commits. |
| cg-problems-summary --input &lt;diagnostics-file&gt; &#91;arguments&#93; | CG, CR | Create a bounded summary of editor or diagnostics problem output. |
| cg-publish-markdown &#91;--automatic&#124;--validate-only&#124;--check&#93; &#91;--theme &lt;theme&gt;&#93; &lt;source&gt; | CG, CR | Publish one generic Markdown document to deterministic curated HTML. |
| cg-release plan&#124;start&#124;status&#124;resume &#91;args&#93; &#124; cg-release --legacy-routine &#91;prepared args&#93; | CG | Run generic release controller commands or a prepared GPID PowerShell publication. |
| cg-render-artifact &#91;--automatic&#124;--validate-only&#124;--check&#93; &lt;source&gt; | CG, CR | Validate, render, or check one typed workflow artifact. |
| cg-skill --project-root . --format &lt;human&#124;json&gt; &lt;operation&gt; &#91;arguments&#93; | CG, CR | Run the descriptor-driven skill lifecycle dispatcher. |
| cg-test-summary &#91;arguments&#93; | CG, CR | Create a bounded summary of existing test-runner output. |
| cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations | CG, CR | Run the deterministic context and model-governance audit. |
| cg-tree-summary &#91;arguments&#93; | CG, CR | Create a bounded summary of project tree structure. |
| cg-unlink &#91;--yes&#93; | CG, CR | Remove only Compound GPID-managed project links and projections. |
| cg-update &#91;&lt;version&gt;&#124;latest&#124;--list&#124;--fix&#93; | CG, CR | Update, pin, list, or repair the Compound GPID installation. |
<!-- cg:auto:end -->

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
