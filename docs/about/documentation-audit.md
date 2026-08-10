# Documentation audit and migration record

This record captures the documentation baseline reviewed on 2026-07-24 before
the public information architecture was changed. Repository files are the
authority for product behavior. The audit also reviewed the current upstream
[Compound Engineering plugin](https://github.com/EveryInc/compound-engineering-plugin)
at commit
[`a9f6d53`](https://github.com/EveryInc/compound-engineering-plugin/commit/a9f6d530d4446d805a3100387dedd86268d7e695).

## Baseline inventory

| Source | Audience and contents | Audit finding | Destination |
|---|---|---|---|
| `README.md` | Prospective users; positioning, capabilities, and links | Useful repository entry point; its documentation table was incomplete | Retained as the repository entry point and linked to the public Getting Started path |
| `docs/manual.md` | Users; 12-page table of contents | Duplicated the homepage, sidebar, JavaScript registry, and wiki manifest | Retained as a compatibility index; replaced as the primary entry point by site navigation |
| `docs/installation.md` | New users and administrators; install, link, configure, update, repair, uninstall | Large; repeated versioning; Windows uninstall appeared inside the macOS section; two fragments were broken | Condensed into Getting Started; detailed lifecycle procedures remain in Installation and Versioning |
| `docs/workflow.md` | Users and maintainers; all prompts and end-to-end scenarios | Oversized and mixed task, concept, and maintainer guidance | Split into a workflow overview and focused Design, Deliver, Assure, and Knowledge pages; retained as the complete detailed workflow reference |
| `docs/reference.md` | Power users and maintainers; commands, prompts, agents, skills, configuration, schemas, files | Oversized; duplicated other guides; level-four headings were not rendered as headings | Split into reference indexes for commands, agents, configuration, files, and skills; retained for complete low-level contracts |
| `docs/context-files.md` | Users and administrators; context files and platform architecture | Mixed current native targets with superseded root-adapter advice; one commit instruction contradicted gitignore guidance | Current context/configuration guidance moved to Configuration; legacy adapters are explicitly labeled |
| `docs/model-guide.md` | Power users and maintainers; model and token policy | Useful policy mixed with dated rollout evidence | Retained as policy/reference and linked from Governance |
| `docs/team-brain-schema.md` | Team administrators and developers; Team Brain configuration and schemas | Detailed reference was not on a clear user journey | Linked from Knowledge workflows and Reference |
| `docs/retrieval-backends.md` | Evaluators; optional backend registry | Correctly evaluation-only but absent from persistent navigation | Listed under Experimental Reference with status preserved |
| `docs/snapshot-external-research.md` | Evaluators; deferred modes | Correctly evaluation-only but absent from persistent navigation | Listed under Experimental Reference with status preserved |
| `docs/versioning.md` | Users and maintainers; update and pin behavior | Useful detail duplicated Installation and used old example versions | Retained as lifecycle reference; Getting Started links to it after first use |
| `docs/troubleshooting.md` | Users, support staff, and maintainers; install, link, Pester, VS Code, and GitHub recovery | Oversized and mixed routine support with historical incidents | Fronted by a concise Help index; retained as the complete recovery reference |
| `docs/competitive-reviews.md` | Compound GPID maintainers | Maintainer-only page was absent from the visible sidebar | Moved into the visible Maintainer navigation group |
| `CONTRIBUTING.md` | Contributors | Strong contributor guide; incorrectly named `docs/manual.md` as the command contract | Linked from Development; command documentation points to Reference |
| `RELEASE_NOTES.md` | Upgraders and maintainers | Current release narrative has no version/date heading | Retained as release evidence; flagged for maintainer review |
| `ROADMAP.md` and `roadmap.json` | Project stakeholders | Their status disagreed with implemented capabilities and with each other | Not rewritten as product documentation; flagged for owner reconciliation |
| `compound-gpid.md` | Project maintainers and agents | Charter wording and current focus lagged native multi-platform delivery | Kept as the protected project charter; flagged for owner review |
| `compound-gpid.context.md` | Maintainers and agents; durable implementation conventions | Very large but operationally authoritative; not a public manual | Kept outside public navigation rather than silently condensed |
| `adapters/README.md` | Legacy consumers | Correctly says adapters are superseded but still presents an active install path | Kept for backward compatibility and labeled legacy in public architecture guidance |

## Site architecture findings

- GitHub Pages uploads `docs/` directly and uses `.nojekyll`.
- `docs/index.html` is the shell. `docs/assets/site.js` fetches and renders
  Markdown at runtime.
- Navigation was duplicated in `index.html`, `site.js`, `manual.md`,
  `_wiki.yml`, and `README.md`. These lists already disagreed.
- The renderer supported only level-one through level-three headings and flat
  lists. Existing level-four headings and nested list semantics were lost.
- Unknown routes silently displayed the homepage.
- The site check verified file presence but not route uniqueness, navigation
  coverage, internal links, fragments, or accessibility landmarks.

## Content preservation decisions

- No substantive manual was deleted. Detailed pages remain available as
  progressive-disclosure reference while concise task pages provide the main
  journey.
- Experimental retrieval and research modes retain their evaluation-only
  labels. The site does not present them as active capabilities.
- Legacy root adapters remain documented only as superseded compatibility
  material. Native generated runtime trees are the normal path.
- Product roadmap, charter, and release-history discrepancies are reported,
  not silently rewritten as settled facts.
- The public skills catalog counts canonical `.github/skills/cg-skill-*/SKILL.md`
   directories once. Generated `.claude/`, `.agents/`, `.opencode/`, and `.kilo/` copies
  are mirrors, not additional skills.

## Stale material requiring owner review

1. `compound-gpid.md` still describes a GitHub Copilot-centered deliverable and
   a future cross-agent evaluation, while committed release evidence describes
   native Copilot, Claude Code, Codex, OpenCode, and Kilo targets.
2. `ROADMAP.md` marks Phase 1 in progress although all listed Phase 1 items are
   checked, and it conflicts with `roadmap.json` on Team Brain and later work.
3. `RELEASE_NOTES.md` should identify its release and date at the heading level.
4. Time-bound rollout notes in `docs/model-guide.md` should eventually move to
   release or validation history.
5. Canonical skill directories include supporting references and workflows,
   but generated runtime mirrors currently contain only each `SKILL.md`. This
   packaging gap is outside the documentation-only scope of this migration.

## Migration rule

`docs/navigation.json` is the public site's navigation and search manifest.
Every published Markdown page must be present there. `.github/skills/` remains
the product source of truth for skill identity and purpose; the documentation
catalog adds only audience, category, and availability labels and is validated
against that source.
