# ADR 0002: Sources Compound GPID 2.0 is based on

Date: 2026-11-24. Status: accepted.

## Decision

Compound GPID 2.0 adapts ideas from three open-source projects. We write our own versions for World Bank work; we do not copy their skills. Each derived file names its source so that credit is exact.

## Pinned sources

| Project | Author | Version | Commit | License |
|---|---|---|---|---|
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | Addy Osmani | 0.6.18 | `e997ac5b9a74eab332d5e9793bb38a38c8cfdd74` | MIT |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock | 1.3.2 | `d65391149dbb5fe76478e76fa8d5122b2aa5a70e` | MIT |
| [cursor/plugins](https://github.com/cursor/plugins), `pstack/` | Lauren Tan | 0.15.48 | `ca782ed8b3c2c521cead8e1720d55c3a5dbf2347` | MIT (`pstack/LICENSE`) |

Compound GPID also continues to build on Every's Compound Engineering, credited in `docs/why-compound-gpid.md`.

The maintainer keeps a local clone of each project beside this repository, under `projects_WBG/contributions/` (`agent-skills`, `skills`, `plugins`).

## Rules

1. **Read before adapting.** Read the source file in full, at the pinned commit, before writing the file derived from it.
2. **Name the source.** Every derived file carries a `derived-from` field: `owner/repo@commit:path`, several separated by `; `.
3. **Generate the credits.** `CREDITS.md` and the site's acknowledgements page are built from the `derived-from` fields (task 7.2), so they cannot drift from the files.
4. **Keep the notices.** `THIRD_PARTY_NOTICES` reproduces the three license texts. It is built by copying the license files, never typed.
5. **Moving the pin.** Each quarter, diff each source from its pinned commit, decide through the adoption ledger what to adopt, then update this table.

## What is adopted

The working ledger is section 5 of `.cg-docs/plans/2026-11-24-compound-gpid-v2.md`: one row per source component with a verdict (adapt, pattern, skip), the target in this repository, and what changes. Task 0.4 turns it into `docs/adoption-ledger.md` with a status column.

## Check

Every `derived-from` path in `skills/cg/principles/` was checked against the local clones on 2026-11-24: 48 sources, all present.
