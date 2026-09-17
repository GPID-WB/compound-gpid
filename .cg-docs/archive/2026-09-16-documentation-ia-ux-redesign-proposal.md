# Documentation Information Architecture and UX Redesign

## Goal and Decisions

Make it easy to choose the correct suite, find a command by task, follow a complete procedure, and identify the documentation build being read. Preserve the current static site, its Markdown sources, and its editorial visual style.

Decisions confirmed with the user:

- Keep exactly two documentation channels: the published root and `/dev/`. Do not add archived documentation versions.
- Combine Skill Management guidance into one page. Retain detailed operation references outside the primary sidebar.
- Release the core redesign independently of `/cg-help`. Gate catalog integration and runtime-support claims separately.
- Retain the HTML/CSS/JavaScript foundation, existing typography, and publishing pipeline. No documentation-framework migration.

This plan changes documentation and its presentation/build tooling. It does not change command behavior, suite dependencies, installation eligibility, release branch policy, or protected-tag rules.

## Evidence and Boundaries

Inspection date: 2026-09-15. The planning worktree was clean before this plan was written. Both public channel shells responded to HTTP reads; browser interactions were not tested.

| Current evidence | Design consequence |
| --- | --- |
| `docs/navigation.json` registers 76 pages, including 29 Skill Management entries. | Separate page registration from sidebar visibility; do not delete routes to shorten navigation. |
| `docs/assets/site.js` renders Markdown in the browser and supports `#page=<id>&section=<slug>`. | Preserve this URL contract. Add TOC and migration aliases to the existing router. |
| Search, Ctrl/Cmd+K, code-copy buttons, light/dark themes, and mobile navigation already exist. | Improve these features rather than describe them as new. |
| Browser and validator heading-slug rules differ; duplicate headings are not disambiguated. | Establish one heading contract before adding section search and TOC links. |
| `scripts/assemble-docs-site.js` composes root and `/dev/`; `release-pages.yml` protects publication. | Preserve complete paired deployments, source identity, artifact digests, and trusted-controller separation. |
| Tagged-release publication can put a prerelease at root; dev publication currently takes root content from `main`. | Call root **Published**, not unconditionally **Stable** or **Latest release**. Show actual source identity. |
| Operation descriptors bind `docs/skills/management/commands/*.md`. | Preserve those reference paths and their command contracts. |
| `scripts/rebuild-docs.js` owns generated reference tables through `docs/_wiki.yml`. | Transfer ownership atomically when the help catalog becomes authoritative. Never leave two generators for one section. |

The `wealthy-salmonberry` worktree contains `/cg-help` schema, sidecars, catalog, query service, transport, and generated adapters. Its saved state reports Phases 1-4 complete and Phase 5 current; documentation generation is still planned in Phase 6. Its inspected catalog has 49 command records but lacks this branch's `/cg-light-work`. The newest saved regression artifact contains one failure, so historical passing results are not a launch gate. Recheck actual source, status, and test evidence at integration; sibling worktree notes are not release proof.

Relevant source boundaries: `docs/index.html`, `docs/assets/site.{js,css}`, `docs/navigation.json`, `docs/_wiki.yml`, `scripts/{rebuild-docs,check-docs-site,assemble-docs-site,legacy-pages}.js`, `scripts/tests/`, `package.json`, and the documentation workflows under `.github/workflows/`. Help integration additionally depends on the sibling's canonical `.github/prompts/*.help.json`, `.github/shared/{help-catalog,shell-commands,module-registry}.json`, `docs/workflow.md`, and `scripts/help/` contracts.

## 1. Information Architecture

Use seven task-oriented primary groups. Keep no more than two sidebar levels. Put advanced details on landing pages and in search, not in an always-expanded list.

| Group | Primary destinations | Secondary destinations |
| --- | --- | --- |
| Start Here | Getting Started; CG or CR: Choose a Workflow; Working with AI Responsibly; What's New | Why Compound GPID; installation details |
| Technical Workflows | Choose a Task; Design the Work; Deliver and Resume; Review and Assure; Knowledge and Coordination | Detailed workflow contracts |
| Research Workflows | Start Here; First CR Workflow; Worked Example; Lifecycle and Task Types; Evidence and Boundaries | Research philosophy and detailed method references |
| Skills | Skills Catalog; Skill Management | Analysis, research, development, and institutional skill catalogs; operation references |
| Operate | Configuration; Updates and Versions; Help and Troubleshooting; Governance and Security | Strict config schema; installation and recovery reference |
| Reference | Find a Command; Agents; Files and Artifacts; Complete Reference | Context/model/Brain schemas; evaluation-only capabilities; compatibility manual |
| Contribute | Contribute and Develop | Maintainer tools, release controller documentation, issue dispatch, documentation maintenance |

Implementation rules:

- Keep existing page IDs and source paths unless there is a documented migration need. Update labels without renaming routes.
- Extend the current manifest additively with validated sidebar visibility and redirect metadata. Existing records remain visible by default. Hidden references remain registered, linked, and searchable.
- Use optional redirect metadata containing a target page ID, default section, and an explicit old-section-to-new-section map. Reject missing targets, redirect cycles, duplicate IDs, and unsafe paths. Exclude redirect stubs from search.
- Retain complete Markdown coverage checks. Every file must be a registered primary page, secondary reference, or compatibility stub; hiding a page must not disable validation.
- Make groups collapsible with real buttons, `aria-expanded`, and an automatically opened active group. Remove numeric prefixes and literal backticks from navigation labels.
- Add a breadcrumb, suite/type badges where relevant, and a contextual next step. Do not apply arbitrary previous/next ordering across unrelated reference pages.
- Replace the homepage's CG-only "Core workflow / Verified steps" panel with equally visible Technical and Research entry paths. Keep shared responsible-AI principles and installation guidance.

## 2. Two-Channel Version Architecture

| Channel | URL | Label and behavior |
| --- | --- | --- |
| Published | `https://gpid-wb.github.io/compound-gpid/` | `Published: <verified tag>` or `Published: <ref>@<short SHA>`. Add a prerelease label when the exact tagged source is a prerelease. |
| Development | `https://gpid-wb.github.io/compound-gpid/dev/` | `Development: dev@<short SHA>`, with a persistent notice that content can change before release. |

Do not infer the root version from `latest.json`, the current GitHub default branch, or the URL alone. A release payload is not proof that the page was built from its tag. Explain in `docs/versioning.md` that these are two moving documentation channels, not documentation for every historical installation. Link to GitHub release notes and tagged source for older versions, without promising archived sites.

Add an accessible channel selector in the header and a compact source/ref link in the page footer. Preserve the page and section when the destination channel has them. If only the page exists, open its top with a notice. If the page is unavailable, show an explicit destination-channel fallback with a link back; never silently switch content under the same page title.

### Build Identity Contract

1. Have the trusted composer emit one public `channels.json` at the combined site's root from its already verified source identities. Include a schema version, the two fixed channel paths, full source SHA, branch/ref, an optional validated release tag, and per-channel content digests for navigation, Markdown, and generated indexes. Derive each short label from these fields. Compute content digests before writing this metadata; do not include the file in its own digest inputs.
2. Reserve this exact output path and reject source collisions. Do not put deployment-specific identity files into source Markdown or documentation bot commits.
3. Include `channels.json` in final artifact digests. Extend verification to recompute its expected content and compare source-derived files byte-for-byte, with only the existing dev-banner transform and this explicit metadata addition allowed. Do not broadly exempt JSON or generated paths from verification.
4. Include the generation/validation code in build fingerprints. Generate all assets before final verification; upload the verified artifact without later edits. Mutable dev code must not execute with publication credentials.
5. Read channel metadata and destination manifests with base-path-aware URLs. Keep normal assets, Markdown, search, and command data within the current channel. Only explicit channel switching crosses channels.
6. Bind browser content to the loaded metadata: verify fetched navigation, document, and index bytes against their declared digests before using them under a verified build label. Namespace in-memory caches by channel and manifest identity. On mismatch, retain any already verified view, show a build-change/reload notice, and reject mismatched command/search data. Refresh metadata and clear affected caches on explicit reload; do not loop or silently relabel stale content. Test a deployment change in an open tab and mixed cached responses.
7. Missing/malformed metadata blocks production artifact validation. A local preview can display `Local preview: version unavailable` and disable unverified switching without blocking document reading. Never substitute a guessed stable label.

Keep the existing root-source selection policy. Do not enable the disabled release controller or its `/releases/<tag>/` snapshot feature. Deploy compatible trusted validation/composition changes through the normal reviewed path before publishing artifacts that require the new contract. Test old root content with new dev content during rollout.

## 3. CG and CR Philosophy and Visual Taxonomy

Rework `docs/modular-guide.md`, preserving its `modular-guide` route, into the dedicated **CG or CR: Choose the Right Workflow** guide. Keep existing architecture/configuration anchors working, or map them explicitly.

| Dimension | Technical workflow: CG | Research workflow: CR |
| --- | --- | --- |
| Primary question | Does this implementation satisfy its engineering requirements? | Is this research claim supported by evidence, assumptions, and valid methods? |
| Typical work | Software design, infrastructure, reproducible bugs, tests, delivery | Research scope, measurement, identification, estimation, interpretation, publication |
| Review focus | Behavior, tests, security, maintainability, reproducibility | Research integrity, provenance, code-math agreement, identification, uncertainty, plus engineering quality |
| Practical example | Repair a package-loading error with `/cg-fixbug` | Audit a poverty estimator or interpret a result with the CR workflow |
| Mixed work | Supports software components | Keeps research responsibility when the research task includes code and tests |

Explain that both suites require human judgment and verified lessons. They are not "coding versus no coding," different programming languages, or novice versus expert modes. CR composes shared technical capabilities; it does not require a dependency on the CG suite. Include `suites: [cg]`, `[cr]`, and `[cg, cr]` examples and links to configuration.

Use the task's correctness risk to choose the route: fixing a launcher belongs to CG; changing a statistical specification or validating a published indicator belongs to CR. Show a bounded handoff between research and infrastructure work without implying that `/cg-review` substitutes for `/cr-review`.

Visual rules:

- Retain the existing paper/navy, Fraunces/Manrope/DM Mono design. Add semantic suite tokens: deep teal for **Technical (CG)**, plum for **Research (CR)**, and a neutral **Shared** treatment. Define separate light/dark values and test contrast.
- Apply labelled badges to entry paths, command summaries, workflow steps, search results, and callouts. Color is supplementary, never the only distinction.
- Keep suite badges separate from **Slash prompt**, **Shell command**, **Maintainer only**, and **Development** labels. Do not reuse danger/success styling as suite identity.
- Read suite membership from canonical ownership and support metadata, not from the name prefix. Shared `/cg-skill` and, after integration, `/cg-help` are explicit exceptions to "all cg-prefixed commands are technical-only."
- Add only a small allowlisted Markdown callout convention, rendered safely by the existing parser. Keep ordinary blockquote text useful in raw Markdown; do not enable arbitrary embedded HTML.

## 4. Navigation and In-Page TOC

Desktop layout: primary navigation on the left, readable content in the center, and a distinct **On this page** navigation on the right.

- At approximately 1200 CSS pixels and above, use a 240-256px left rail, a flexible article near 65-80 characters per line, and a 200-220px right rail. Adjust gaps so the article does not become too narrow.
- Make the right TOC sticky below the actual header/banner height, independently scrollable within the viewport, and generated from the current article's H2/H3 headings only. Hide it when there are fewer than two relevant headings.
- At intermediate widths, retain the left rail and move the TOC to a collapsible **On this page** control above the article. At mobile widths, use the existing left navigation drawer and the separate inline TOC. Never combine both navigation systems in one drawer.
- Use `nav aria-label="On this page"`, visible focus, heading permalinks, and active-section indication with `aria-current="location"`. Do not move keyboard focus merely because the reader scrolls.
- Reuse one tested heading extractor/slug contract for rendering, link validation, TOC, and search. Ignore fenced-code headings; handle inline code, punctuation, Unicode, and repeated headings with deterministic suffixes. Record aliases where old browser/validator slugs differ; reject ambiguous aliases rather than guess.
- Clicking a TOC item updates the section URL and scrolls without re-fetching/re-rendering the page. Browser Back/Forward and direct reload must preserve the requested section. Passive scroll tracking must not fill browser history.
- Distinguish shell actions from document routes. The existing `#content` skip link must focus the current main content without navigating to the homepage or replacing the document's page/section route. Test it from a deep link and through Back/Forward.
- Scope heading lookup to the article so it cannot select sidebar or shell elements. Disconnect scroll observers on page changes. Preserve the existing stale-navigation request guard.
- Compute scroll offsets from the real header/banner layout. Honor reduced motion and 200% zoom. Clear the TOC on the homepage, loading/error states, and unknown routes.

## 5. Consolidated Skill Management Guide

Make `docs/skills/management/index.md` the one primary, self-contained guide, not another directory of links. Use the following H2/H3 structure to keep the right TOC useful:

| H2 | Required H3 topics and content |
| --- | --- |
| Start Here | Consumer versus maintainer responsibilities; `/cg-skill` versus shell `cg-skill`; skills are not slash commands |
| Lifecycle and Safety | State transitions; discover before change; plan, review, digest-bound apply, verify; authority boundaries |
| Use Skills in a Project | Find and inspect; import at an exact SHA; activate/deactivate; understand availability |
| Maintain Plugin Skills | Create/vendor; registry and capabilities; update; deprecate/remove; release gates |
| Security and Provenance | Quarantine; approval; provenance; path protection; destructive-action safeguards |
| Diagnose and Recover | Stable finding codes; exit codes; stale plans; manifest/projection failures; safe remediation |
| Migrate Existing Workflows | Retired-command replacements; old-to-new examples; changes that require a new plan |
| Operation Reference | Compact operation/role/effect table and links to the 12 detailed operation contracts |

Migration requirements:

1. Inventory headings, examples, warnings, and inbound references in the current guide/lifecycle/consumer/maintainer/security/migration pages and `docs/skills/importing.md`.
2. Move and edit that content into the unified narrative. Remove repeated explanations, but preserve every unique safety condition and meaningful example. Do not only hide the old pages.
3. Retain `commands/*.md` as the detailed reference authority, including descriptor-bound paths, flags, result contracts, and tests. Each page links back to the relevant guide section and stays searchable.
4. Convert superseded narrative files to short compatibility pages with explicit links and preserved old heading anchors. Route their old website IDs/sections to the unified guide. Keep these stubs hidden and out of search; do not maintain duplicate full guides.
5. Update internal links to the new canonical guide anchors. Check module, descriptor, help-evidence, and schema references before removing any old heading. Preserve valid evidence anchors until their consumers migrate.
6. Validate a content-preservation checklist covering all 29 existing entries and the separate importing page. A reader must be able to complete a consumer or maintainer procedure without repeatedly opening tiny explanatory pages.

## 6. Task-Oriented Command Documentation

Turn `docs/reference/commands.md` into **Find a Command**, with goal-first sections and clear Technical, Research, Shared, and Shell groupings. Reuse `docs/workflows/*.md` and the Research Handbook for full procedures; do not create one thin page for every command. Keep the complete reference available for exact syntax.

Every public command must have a reviewed entry covering: **use when**, **do not use when**, prerequisites and suite/role requirements, exact invocation, one concrete example, expected output/artifact, verification or approval boundary, common failure, and next useful step. Use progressive disclosure for long flag lists, but keep safety conditions visible.

Prioritize these complete recipes in the first content pass:

| Reader's task | Guide and illustrative invocation |
| --- | --- |
| Start a project | Getting Started: installation/linking, suite selection, then `/cg-setup` where eligible |
| Fix a reproducible software error | Deliver and Resume: `/cg-fixbug The launcher fails when the project path contains spaces` |
| Complete a small technical task | Explain `/cg-light-work <task>` qualification, saved-plan approval, review, and opt-in compounding |
| Deliver a larger change | Design/Deliver: clarify, save and review a plan, then `/cg-work phase1`; verify before publication |
| Review and resolve findings | Review and Assure: `/cg-review`, `/cg-fix-triage`, and re-review with evidence |
| Run a research task | CR worked example: `/cr-brainstorm Compare poverty estimates across survey rounds`; surface comparability assumptions before `/cr-plan` and `/cr-work` |
| Resume or recover | `/cg-resume` and troubleshooting, with explicit artifact/state prerequisites |
| Manage skills safely | Unified guide: discovery, plan, explicit apply, verification |

Treat these as editorial scenario seeds, not new command specifications. Verify invocation grammar and every claimed artifact against the current canonical prompt, wrapper, or descriptor before publication. Label where commands run: chat versus terminal, and PowerShell versus POSIX when syntax differs. Use synthetic examples, mark placeholders, show representative output as illustrative, and never imply that a review certifies the truth of a research claim.

Before help integration, preserve the current generator's ownership of syntax/summary tables and review manual recipes against the canonical source. Do not build a competing metadata catalog. Add a compact, printable cheat-sheet section to the command hub; after integration derive its command facts from the help catalog.

## 7. `/cg-help` Integration and Parity

### Data Flow and Ownership

```text
Canonical prompts / shell definitions / module registry
        + reviewed help sidecars and explicit workflow records
        -> help source validation and digest checks
        -> canonical help-catalog.json
        -> native adapter copies + generated documentation facts
        -> website command index + section search
        -> verified channel-specific site artifact

Reviewed Markdown recipes + command-to-document route map
        -> narrative, page/section links, and parity checks
```

- Keep command identity kind-qualified: `slash:cg-help` differs from `shell:cg-help`. Preserve stable workflow IDs and repeated steps. Do not derive IDs from titles or URLs.
- Add a small reviewed website route map, proposed at `docs/reference/command-routes.json`, keyed by command/workflow ID and pointing to an existing page/section. It contains presentation links only, not copied usage, constraints, or availability facts. Do not assume `documentationTargets` is populated.
- Generate a safe browser projection, proposed at `docs/assets/command-index.json`, from the complete validated catalog, not the bounded help overview response. Include catalog schema/generator versions and `sourceDigest`; bind it to the same source revision as its channel's docs.
- Technical/research eligibility uses `supportedSuites` and `ownerModule`. Website filters are reader-selected filters, not proof that a command is active in the visitor's project.
- Catalog facts include usage, examples, prerequisites, outputs, constraints, related commands, and explicit workflows. Editors own explanations and worked scenarios. Changes to either side require review of linked recipes; automatic checks cannot establish semantic accuracy by themselves.
- At adoption, reconcile the help Phase 6 implementation with `rebuild-docs.js`, `_wiki.yml`, and wiki regeneration. Transfer each generated section to one owner in one change; preserve manual text outside markers. Reuse the help documentation writer/checker when it exists, rather than implementing a parallel writer.
- Add new sidecar JSON, registry/shell metadata, workflow records, route mapping, and generators to canonical fingerprint inputs. Treat derived indexes as outputs, not their own inputs, while retaining every output in artifact digest verification.

### Independent Release Gates

| Gate | Required evidence | What can publish |
| --- | --- | --- |
| A: Core redesign | Current-source content review, URL migration, UI/accessibility tests, paired-channel deployment validation | New navigation, philosophy guide, TOC, unified Skill Management, improved existing search/copy, and task guides. No claim that `/cg-help` is released. |
| B: Catalog-backed discovery | Help integration merged; source inventory reconciled, including `/cg-light-work`; fresh catalog; single documentation owner; target parity and relevant regressions passing | Catalog-generated command facts, shared workflow links, command filters, and copyable help lookups supported by the merged contract |
| C: Runtime claims | Current source-bound host evidence from the help support verifier; failed/unverified hosts labelled correctly | Verified `/cg-help` runtime instructions for evidenced hosts, not blanket five-host certification |

Coordinate by artifacts and gates, not calendar estimates. The website owner can complete Gate A while the help owner completes freshness and documentation-generation work. Do not copy unmerged sibling catalog files into production. After integration, source changes that make a pin stale must fail loudly; named-record repins require explicit review, and must not update other pins. There is no silent fallback to stale manual command facts in a catalog-enabled build.

The four inspected help workflows are linear records. A richer tutorial can discuss alternatives, but must label them as editorial guidance; do not imply that help supports branches, optional steps, or a `workflow:<id>` invocation that its contract does not provide. `/cg-help` candidate responses remain limited to three; a website inventory/search is a separate surface and can show more results.

Keep browser search deterministic and local. No browser execution of the CLI, project scan, natural-language assistant service, or remote query logging is in scope. Treat catalog text as untrusted display data; escape content and validate links. Documentation anchor changes may invalidate help evidence or host certification even when `sourceDigest` is unchanged; run both checks where applicable.

## 8. Additional Discovery and Accessibility Improvements

| Priority | Improvement | Acceptance condition |
| --- | --- | --- |
| Core | Better search | Build a deterministic section-level index from registered canonical pages; exact command/title matches rank above body text. Show heading, snippet, suite/type, and current channel. Exclude compatibility stubs and prevent duplicate guide/reference hits from dominating. |
| Core | Search reliability | Load one lazy local index instead of fetching every page on first search. Show explicit load failure/retry and no-results guidance; never cache missing content as an apparently complete search. Keep document reading usable if search fails. |
| Core | Search keyboard behavior | Preserve Ctrl/Cmd+K, arrows, Enter, Escape, focus return, and visible selection. Show the correct platform hint. Do not intercept ordinary typing or add unmodified single-letter shortcuts by default. |
| Core | Quick copy | Keep code-block buttons; add accessible success/error feedback and a manual-selection fallback when clipboard access fails. Preserve exact code bytes and exclude prompts, line numbers, and output from copyable invocation blocks. |
| Core | Reading/accessibility | WCAG 2.2 AA contrast, visible focus, semantic landmarks, descriptive link labels, responsive tables, reduced motion, and no full-page horizontal scroll. Do not announce the entire article for every TOC movement. |
| Core | Storage resilience | Guard browser-storage reads and writes so denied storage cannot prevent navigation initialization. Keep theme choice usable in memory when persistence fails. |
| Core | Source and feedback | Add version-correct source links and a "Report a documentation issue" link containing page/channel/SHA but no search query or project data. Resolve repository files outside the manifest to allowed GitHub source URLs instead of inert text. |
| Core | Cheat sheet and print | Provide compact task-to-command tables and print styles that remove navigation and copy controls. Keep suite labels and the channel/build identity in print. |
| Follow-up | Theme and polish | Use system theme unless explicitly overridden. Add limited syntax highlighting only with safe rendering, a measured benefit, and tests. Do not add a runtime CDN dependency for it. |

Generate the search index through the existing deterministic docs build, with an explicit output path and no self-referential fingerprint. Preserve support for raw Markdown and the no-JavaScript fallback. Full static HTML pre-rendering, separate SEO URLs for every hash route, translation, external hosted search, and usage analytics are outside this redesign.

## 9. Ordered Implementation and Validation

1. **Freeze the migration contract.** Inventory all routes/headings and the 29 Skill Management entries; record old-to-new mappings and unique-content preservation checks. Confirm current help/release state. Add fixtures for old root/new dev content and define manifest/heading/channel metadata validation before UI changes.
2. **Build the navigation and reading shell.** Update `docs/index.html`, `site.js`, `site.css`, navigation metadata, and focused helpers only where shared by runtime/build tests. Add sidebar visibility, redirects, suite badges, breadcrumbs, right TOC, responsive controls, and section-only routing. Preserve escaping and request-race protection.
3. **Restructure content.** Rewrite the suite guide, consolidate Skill Management, revise homepage/task guides/command hub, and update links. Keep operation references and generated-section ownership intact. Review technical and research examples with the appropriate subject reviewers.
4. **Improve discovery.** Generate the section index; add ranked results, copy feedback, cheat sheet/print, and source/issue links. Wire new generator inputs and exact output ownership into `rebuild-docs.js`, fingerprint tests, and `--check` mode. Do not change canonical command behavior.
5. **Add channel identity and validate Gate A.** Update composer/verification tests and the protected workflow contract without widening permissions. Include `docs/**/*.css`, new helpers, manifests, and relevant test files in CI triggers. Preview under both repository base paths, then release through the existing reviewed path after the trusted controller supports the contract.
6. **Integrate help at Gate B.** Reconcile inventories and reviewed metadata; adopt the merged documentation writer; generate command routes/index; run catalog freshness, native target parity, managed-output preservation, and source-bound link tests. Do not let Gate B block Gate A.
7. **Enable supported help guidance at Gate C.** Validate current certification evidence, publish only justified host claims, and add verified copyable `/cg-help` follow-ups. If evidence changes, remove/mark only unsupported claims rather than invent a compatibility guarantee.

### Validation Matrix

| Area | Required checks |
| --- | --- |
| Existing gates | `node --check docs/assets/site.js`; `node scripts/check-docs-site.js`; `node scripts/rebuild-docs.js --check --all`; `npm run test:docs-automation`. Update expected contracts, not just static token assertions. |
| Runtime/browser | Add a dedicated Playwright docs suite using the existing dependency, with an isolated preview server and axe-core. Wire the existing `docs-preview-runtime.test.js` into the docs test script. Test root and `/dev/`, light/dark, 320/390/768/1024/1440px widths, 200% zoom, reduced motion, keyboard-only navigation, mobile focus return, and storage access that throws. |
| TOC/router | Repeated/punctuated/Unicode headings; headings inside code; old fragments; direct deep links; skip-to-content without losing the document route; Back/Forward; same-page movement without fetch; rapid page changes; unknown page/section; TOC teardown; header/banner offsets. |
| Migration | Every former Skill Management route and heading resolves; raw Markdown stubs remain useful; no operation descriptor target changes; all unique warnings survive; hidden references remain reachable and searchable. |
| Search/copy/security | Exact slash/shell disambiguation; CR/CG/shared labels; section result links; no-results; failed index fetch; stale response races; clipboard denied; script-like Markdown/catalog text; unsafe/traversal URLs; error messages without silent success. |
| Publishing | Main-sourced root and tagged prerelease root labels; old root/new dev; absent page/section on channel switch; channel metadata collisions/tampering/missing fields; stale source/artifact rejection; unrelated root/dev bytes preserved; no cross-channel search or asset leakage; mixed cached responses and deployments changed during an open session. |
| Generation/help | Repeat builds are byte-identical; manual prose survives; stale/missing/extra metadata fails; slash/shell IDs do not collide; repeated workflow steps survive; catalog-enabled builds cannot fall back; support-evidence invalidation is detected. |

Python help/skill tests are an integration gate, not a requirement to run the whole repository suite for CSS changes. At Gate B, run the merged help catalog/query/transport/support, target-drift, and relevant skill-documentation tests. If Pester is required, first load the project's Pester safety skill and use its canonical safe runner/subagent process.

Acceptance is task-based: a new reader can choose CG versus CR from one comparison page; find a command by goal or name; identify the current build on every document; navigate a long page without losing the left navigation context; and complete Skill Management guidance on one page. All existing public routes remain valid or lead explicitly to their replacement. Gate A does not advertise unfinished `/cg-help` behavior.

### Rollback and Ownership

The website maintainer owns navigation, presentation, route aliases, and editorial guides. The help maintainer owns catalog schema, source validation, repins, and runtime certification. The release maintainer owns protected composition and deployment changes. Shared generated-section changes require both website and help review.

Keep gate changes reviewable and separately reversible. Roll back through a reviewed corrective commit and a new validated paired artifact, not by editing a deployed site or moving a tag. Preserve URL aliases during rollback where published links depend on them. If catalog integration fails, hold Gate B; do not silently publish stale catalog data or remove the validated Gate A site.

No implementation files have been changed and no builds or tests have been run as part of this planning task. Important product choices are resolved; current help status and exact evidence remain explicit implementation-time checks, not unanswered design choices.
