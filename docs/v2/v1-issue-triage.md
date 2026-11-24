# Version 1 roadmap issues, sorted for version 2

Task 0.3 (#213). The 44 open issues labelled `cg:roadmap`, each with a verdict. Sorted from titles and opening lines; most of these issues have no description.

No issue has been commented on or closed. That waits for the maintainer.

| Verdict | Count | Meaning |
|---|---|---|
| absorbed | 31 | a v2 issue covers it; close with a link once that issue is done |
| deferred | 8 | a possible pack feature after 2.0; keep open, relabel |
| out of scope | 3 | set aside, with the record that says why; close as not planned |
| superseded | 1 | no longer applies |
| out of scope as a default | 1 | set aside as a default, allowed as a choice |

| Issue | Title | Verdict | See | Reason |
|---|---|---|---|---|
| #47 | tidymodels addition to cg-skill-r-analytical | deferred | #221 | Content for the `lang-r` pack. Needs an observed failure first (SCOPE.md). |
| #48 | Skill description consistency audit | absorbed | #222, #238 | The skill linter and the routing evals check every description. |
| #49 | Testing skill for Python | deferred | #239 | Content for the `lang-python` pack. |
| #50 | Skill description length cap with test enforcement | absorbed | #222 | A linter rule. |
| #51 | Model-split pattern for other prompts | deferred | #249 | Model choice belongs to the human and the host; guidance could live in the audit pack. |
| #52 | Study OpenAI Codex plugin for Claude Code | out of scope | ADR 0004 | No host is built on another. |
| #53 | Evaluate GitHub Copilot hooks | deferred | ADR 0004 | Hooks are an optional adapter, after 2.0. |
| #54 | copilot-instructions.md restructuring | absorbed | #219 | v2 has no such file; setup writes one short pointer block. |
| #55 | Adding hooks to streamline process | deferred | ADR 0004 | Same as #53. |
| #56 | Include an ideate-style prompt | absorbed | #225 | The widen-then-narrow step of the brainstorm playbook. |
| #57 | Study GSD-2 and Superpowers workflow patterns | superseded | #214 | v2 is based on three other sources; a quarterly look at sources is in the plan. |
| #58 | Stage control knobs for workflow prompts | absorbed | #219, #224 | Size and tier replace per-stage flags. |
| #59 | Autonomous pipeline command /cg-autopilot | out of scope | `.out-of-scope/never-block-on-the-human.md` | The two hard stops stay. |
| #60 | Copilot CLI execution with worktrees | out of scope | ADR 0004 | Specific to one host. |
| #61 | Verification commands, configurable post-task checks | absorbed | #227 | Declared checks, `cg.py evidence`, the verification profile (P4). |
| #62 | Auto-triggered skills via expanded applyTo patterns | absorbed | #238 | Skills load from their descriptions; routing evals test it. |
| #63 | Add mattpocock/skills to review sources | absorbed | #214 | It is one of the three pinned sources. |
| #64 | Cross-model review | out of scope as a default | `.out-of-scope/review-by-several-models-by-default.md` | A human may still ask a second model. |
| #65 | Tiered model escalation | deferred | #249 | As #51. |
| #66 | ID traceability from requirements to plan tasks | absorbed | #224 | Requirements and checks carry IDs in the contract (P1). |
| #67 | Inline self-review checklist after brainstorm and plan | absorbed | #226 | Plan-stage verifiers replace a self-checklist. |
| #68 | Verification-before-completion enforcement | absorbed | #227, #230 | Evidence per check and the verification verifier (P4). |
| #69 | Append-only DECISIONS.md register | absorbed | #236 | Decision records, one file each (P8). |
| #70 | Human-in-the-loop review mode for brainstorm and plan | absorbed | #225, #226 | Grilling and the first hard stop. |
| #71 | Systematic debugging methodology in /cg-fixbug | absorbed | #235 | The bugfix playbook. |
| #72 | Automatic knowledge extraction after work | absorbed | #234 | The compound playbook (P9). |
| #73 | Brainstorm depth overhaul, grill-me mode | absorbed | #225 | The grilling primitive. |
| #74 | /cg-confidence | absorbed | #231, #233 | Labelled claims (P7) and the defend-it brief. |
| #75 | roadmap.json schema validation | absorbed | #246 | Roadmap edits are made by code in the roadmap pack. |
| #76 | Required frontmatter field checks for plans | absorbed | #224 | `cg.py validate`. |
| #77 | Evals scaffold with probe-and-check pairs | absorbed | #238 | Planted-violation tests, routing evals, pressure cases. |
| #78 | Migration path from plain Copilot instructions | absorbed | #219, #252 | Setup edits the instructions file that exists and adds one block. |
| #79 | Roadmap bootstrap from charter | deferred | #246 | A feature of the roadmap pack. |
| #80 | /cg-setup --refresh | absorbed | #219 | Setup is safe to run again. |
| #81 | Onboarding tour /cg-tour | absorbed | #237, #253 | Help in the guide and the one-page start. |
| #82 | /cg-help interactive help | absorbed | #237 | Help that routes without starting work. |
| #83 | Goal-driven execution, plan as completion contract | absorbed | #226, #227 | The contract, declared checks and evidence. |
| #84 | Outcome criteria in plans | absorbed | #226 | Requirements with checks (P1). |
| #85 | Conversation audit trail across stages | absorbed | #233, #236 | Decision records, the conformance record and the AI-use statement (P8, P12). |
| #86 | Attribution documentation | absorbed | #214, #253 | `derived-from` fields, the ledger and a generated acknowledgements page. |
| #87 | /cg-strategy --add quick-add for roadmap ideas | deferred | #246 | A feature of the roadmap pack. |
| #88 | Planning-stage test strategy and human review | absorbed | #226 | Checks agreed with the human before work (P4). |
| #89 | Agent-verified outcome definitions with acceptance evals | absorbed | #226, #228 | Checks that can fail, run by verifiers. |
| #98 | status:completed verification from /cg-work output | absorbed | #227 | Completion follows from evidence, not from a status field. |
