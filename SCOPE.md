# Scope

Compound GPID 2.0 is built for analysts: economists, researchers and data scientists, and the people who build their packages, pipelines and dashboards. It keeps the human in charge of work done with a coding agent, and it is held to its own principles.

Version 1 grew until it was hard to install, hard to debug and hard to trust. This page is how version 2 stays small. Its rules are checked by code where code can check them.

Policy adapted from mattpocock/skills (`SCOPE.md`).

## The bar for a change

A proposed change to core stays open only if it clears both parts.

1. **Observed failure.** It describes something that went wrong in real use: what the human asked, what the agent did, what should have happened. "It would be better if" does not clear this part.
2. **It fits.** It serves the twelve principles, it is not already recorded under `.out-of-scope/`, and it cannot be had by combining what exists. A setting for one person's taste, or a branch for one host, does not fit.

The size of the change does not matter. One word and a rewrite face the same bar.

## Where a change goes

| It is | It goes to |
|---|---|
| Knowledge about a language, a method or a field | a pack |
| A feature only some people want | a pack |
| Something one host needs | an adapter (ADR 0004) |
| A rule code can check | a check in `tools/`, before any text |
| A change to how the loop works for everyone | core, through the bar above |
| A new principle, or a change to what one means | the maintainer's decision; see "How a principle changes" in the principles index |
| Clearer wording of a principle, same meaning | an ordinary commit |

## Budgets

Checked in CI. Going over fails the build.

| What | Limit |
|---|---|
| The guide's `SKILL.md` | 100 lines |
| A playbook | 120 lines |
| A principle file | 120 lines |
| A lens | 60 lines |
| Any other skill's `SKILL.md` | 500 lines, with longer material in files beside it |
| Core tooling, excluding tests | 2,500 lines |
| One pack's tooling, excluding tests | 1,500 lines |
| Hub tooling (`tools/`, `install.py`), excluding tests | 2,000 lines |
| Tests | at most 1.5 times the code they cover |
| `pack.json` | six keys |
| User-invoked skills in core | one: the guide |

Raising a limit needs a decision record and an equal deletion elsewhere.

## Rules for the tooling

- One implementation, in Python, for every operating system.
- Standard library first. A single vendored pure-Python file is allowed where it replaces a parser we would otherwise write.
- Inputs are constrained instead of parsed leniently: flat frontmatter, a declared subset of Markdown.
- Core never imports from a pack.
- A check that guards a rule is shown to fail on the mistake it guards against.

## Removing things

Something that goes unused is deleted. The changelog entry names what replaces it, or says that nothing does.

## Already decided

Each file in [`.out-of-scope/`](.out-of-scope/) records one idea that was considered and set aside, and why. Read them before proposing a change.

## Who decides

The maintainer. A proposal that cannot be judged against the bar gets one round of questions and is then closed if no answer comes.
