# Incorporating graphify principles into compound-gpid

## A roadmap-ready implementation guide

This document turns the four salvageable graphify ideas into concrete, sequenced work for compound-gpid. It is written to be pasted into your roadmap and worked on in your own Copilot sessions. Every step respects your hard constraints: GitHub Copilot in VS Code/Positron only, Windows with PowerShell and junction architecture, `cg-index.py` stdlib only, R and Stata as the analytical languages, and the rule that computational checks are harness work, never model calls.

---

## 0. The one adaptation that makes all four principles safe

graphify builds its graph by asking Claude to read each document and guess concepts and relationships. You cannot copy that, for two reasons that are both load bearing for you:

1. It is a model call, so it belongs in inference, which violates your harness engineering rule (deterministic checks live in hooks, not in the model).
2. Model-inferred edges between methodological concepts are exactly the artifact that becomes dangerous the moment someone trusts it. In a corpus about FGT indices and PPP vintages, a confidently wrong link is an institutional risk.

**The adaptation:** compound-gpid's index must be built from structure that is already explicit in the documents, not inferred. The graph edges come from things a deterministic stdlib script can read without judgment: YAML front matter, tags, explicit cross links between documents, headings, and filenames. The author of a `.cg-docs/` artifact declares the relationships during the Compound step. `cg-index.py` only reads what is declared.

This flips graphify's confidence model in your favor. In graphify, `EXTRACTED` versus `INFERRED` describes how confident the model was. In compound-gpid, `EXTRACTED` means the link is literally present in a document, and `INFERRED` or `AMBIGUOUS` is a label the human or agent author chose to attach to a claim they are less sure about. The index stays deterministic and auditable; the uncertainty lives in the authored content where it belongs.

Hold this distinction in mind for the rest of the document. It is what keeps you from rebuilding graphify's biggest weakness.

---

## 1. Principle one: the brain as a navigable markdown wiki

### What it is

graphify's `--wiki` output renders an `index.md` entry point plus one markdown article per topic, specifically so an agent can navigate by reading files instead of parsing JSON. For you this is the highest value idea, because Copilot reads markdown natively and you can scope what it loads through a context contract.

Today your `.cg-docs/` is a folder of artifacts. The brain exists, but Copilot has to crawl it. The wiki turns it into a small, structured front door.

### Why it matters for token efficiency

This is your real token win, and it is the defensible version of graphify's discarded 71x claim. Instead of Copilot crawling the whole `.cg-docs/` tree or you pasting whole files, a prompt loads one file, `.cg-docs/index.md`, which is a compact map. From there Copilot follows links only to the articles a task actually needs. Loading a 60 line index plus two relevant articles is far cheaper than letting the model re-derive structure from the raw tree every session.

### Where it slots in the roadmap

This is the rendering half of Stage 1 (local knowledge index). Build it immediately after the index data structure in principle two exists, because the wiki is a view over that index.

### Step by step

1. **Decide the generated layout.** Nothing here is hand authored. Everything under `.cg-docs/_index/` is output of `cg-index.py` and is regenerated, never edited.

   ```
   .cg-docs/
   ├── solutions/              # hand-authored knowledge artifacts (source of truth)
   ├── bugs/                   # hand-authored
   ├── _index/                 # GENERATED, do not edit
   │   ├── index.md            # entry point: the map of the brain
   │   ├── topics/             # one article per tag/topic
   │   │   ├── ppp-alignment.md
   │   │   └── survey-weights.md
   │   └── index.json          # machine index (principle two)
   ```

2. **Define what `index.md` contains.** Keep it scannable and stable. A short header explaining it is generated, then a list of topics with article counts, then a list of the highest connection artifacts (your equivalent of graphify god nodes, computed deterministically as the artifacts with the most inbound links). Each entry is a relative markdown link Copilot can follow.

3. **Define a topic article.** One per tag. It lists every artifact carrying that tag, with the artifact title, a one line summary pulled from the artifact front matter, the relative link, and the declared related links with their confidence labels. The article is a junction, not new prose.

4. **Render deterministically.** Sort everything (topics alphabetical, artifacts by id) so that regenerating the wiki on an unchanged corpus produces a byte identical result. This keeps git diffs meaningful and lets your Pester tests assert on output.

5. **Generate, never hand edit.** Add a one line banner to every generated file: `<!-- GENERATED by cg-index.py. Do not edit. Edit the source artifact instead. -->`. Add `.cg-docs/_index/` handling to your `.gitignore` decision (see failure modes for the commit-or-ignore tradeoff).

6. **Wire it into context contracts.** Update the relevant prompts so their context contract names `.cg-docs/_index/index.md` as the knowledge entry point, instead of pointing Copilot at the whole `.cg-docs/` tree. This is the change that actually saves tokens. Remember the prompt versus agent rule: this is a context declaration in the prompt body, not a `tools:` entry.

### Definition of done

Running the indexer on `.cg-docs/` produces `index.md` and topic articles, a Copilot session pointed only at `index.md` can reach any artifact in two hops, and rerunning on an unchanged corpus changes nothing.

---

## 2. Principle two: a persistent structural index built once, queried cheaply

### What it is

graphify writes `graph.json` so you can query the structure weeks later without re-reading the source. Your version is `index.json`, a small deterministic map of your `.cg-docs/` corpus that both the wiki renderer and any future tooling read instead of rescanning every file.

### Why it matters

It separates the expensive scan from the cheap query. Build the structure once in a hook; every consumer after that reads a compact JSON instead of walking the tree. It is also the substrate the wiki is rendered from, so principles one and two are one piece of work split into data then view.

### Where it slots in the roadmap

This is the core of Stage 1 and the prerequisite for principle one. It also becomes the unit that Stage 2 (shared cross-project knowledge base) distributes through the junction architecture: each project has its own `index.json`, and a future merge step can union them.

### The data model

Every `.cg-docs/` artifact carries YAML front matter. The indexer reads only this plus explicit links. Author this front matter during the Compound step.

```yaml
---
id: ppp-2017-vintage-alignment        # stable, unique, kebab case
title: Aligning welfare to the 2017 PPP vintage
type: solution                        # solution | bug | decision | convention
tags: [ppp-alignment, welfare-aggregation, deflators]
summary: One sentence shown in the wiki and index.
related:
  - id: fgt-poverty-line-construction
    confidence: EXTRACTED             # see principle four
  - id: survey-weight-taylor-linearization
    confidence: INFERRED
status: verified                      # verified | draft  (enforces your "document only after verification" rule)
---
```

`index.json` is then a straightforward aggregation:

```json
{
  "generated_at": "ISO-8601",
  "schema_version": 1,
  "artifacts": [
    {
      "id": "ppp-2017-vintage-alignment",
      "title": "...",
      "path": "solutions/ppp-2017-vintage-alignment.md",
      "tags": ["ppp-alignment", "..."],
      "summary": "...",
      "status": "verified",
      "inbound": ["fgt-poverty-line-construction"],
      "outbound": [
        {"id": "fgt-poverty-line-construction", "confidence": "EXTRACTED"}
      ]
    }
  ],
  "topics": {"ppp-alignment": ["ppp-2017-vintage-alignment", "..."]}
}
```

### Step by step

1. **Write the front matter parser in stdlib only.** Do not add PyYAML. Your front matter is a constrained subset (scalars, flat lists, and the `related` list of two key maps), which you can parse with a small hand written reader. If you ever need full YAML, prefer enforcing the simple subset over taking a dependency, because the dependency breaks your stdlib rule and the Windows install story.

2. **Walk `.cg-docs/` sources** (`solutions/`, `bugs/`, and any other authored folders), skipping `_index/`. Use `pathlib`. Open files as UTF-8 explicitly and normalize newlines, because Windows will otherwise hand you CRLF and BOM surprises.

3. **Validate and fail loudly.** Missing `id`, duplicate `id`, unknown `type`, a `related` target that does not exist, or a `confidence` value outside the allowed set must stop the build with a clear message naming the file and the problem. Silent degradation is the failure mode you most want to avoid here. This validation is deterministic, so it correctly lives in the harness, not in a model.

4. **Build the graph in memory** as plain dicts. Inbound links are computed by inverting the authored outbound `related` links. No third party graph library; an adjacency dict is enough at your corpus size.

5. **Compute the deterministic analytics** the wiki needs: connection counts for the god node list, and orphan detection (artifacts with no inbound and no outbound links, which usually means missing cross links). These are counts, not inferences.

6. **Write `index.json` with sorted keys** and a trailing newline so output is reproducible.

### A note on scale, stated honestly

At a few dozen artifacts an adjacency dict and a tag map are plenty. You do not need NetworkX, Leiden community detection, or anything graphify ships. Reach for real graph algorithms only if `.cg-docs/` grows into the hundreds and you find yourself wanting automatic clustering. Until then, that machinery is complexity you would be maintaining for no benefit. Do not import the graph stack just because graphify did.

### Definition of done

`index.json` is generated deterministically, validation rejects a malformed artifact with a clear error, and inbound links are correctly inverted from authored outbound links.

---

## 3. Principle three: content hash caching for incremental updates

### What it is

graphify keeps a SHA256 cache so reruns only process changed files. You want the same, and it is pure stdlib (`hashlib`), so it costs you nothing in dependencies.

### Why it matters

Two reasons. First, speed: as `.cg-docs/` grows you do not want to reparse everything on every commit. Second, and more important for you, it is what makes it safe to run the indexer automatically in a hook. A cheap incremental rebuild can run on every commit without anyone noticing; an expensive full rebuild cannot.

### Where it slots in the roadmap

A refinement layer on Stage 1, added once principles one and two work. Do not build the cache first. Correct full rebuild comes before fast incremental rebuild, or you will be debugging cache invalidation before you have a baseline to trust.

### Step by step

1. **Define the cache file.** `.cg-docs/_index/.cache.json`, mapping each source path to the SHA256 of its raw bytes plus the parsed result for that file.

2. **Hash raw bytes, not parsed content,** with `hashlib.sha256`. Read the file in binary mode so the hash is stable regardless of newline handling, then decode for parsing separately.

3. **On each run:** for every source file, compare its current hash to the cached hash. Unchanged means reuse the cached parse. Changed or new means reparse. A cached path that no longer exists means a deletion, so drop it and remember to recompute inbound links for anything that pointed at it.

4. **Always rebuild the derived layer.** The cache short circuits parsing of individual files only. Inbound links, the topic map, the god node counts, and the rendered wiki are global, so recompute them every run from the merged parse results. This is the cache invalidation trap graphify users hit: caching the per file parse is safe, caching the cross file analytics is not.

5. **Version the cache.** Store a `schema_version`. When you change the front matter schema or the parser, bump it and invalidate the whole cache. A stale cache that silently feeds an old parse into a new schema is exactly the silent degradation you forbid.

### Definition of done

Editing one artifact and rerunning reparses only that file, deleting an artifact correctly updates the inbound links of artifacts that referenced it, and bumping the schema version forces a clean full rebuild.

---

## 4. Principle four: EXTRACTED / INFERRED / AMBIGUOUS confidence tags

### What it is

graphify tags every edge so you always know what was found versus guessed. You adopt the labels as a `.cg-docs/` authoring convention, applied to the `related` links and, optionally, to individual claims inside an artifact.

### Why it matters

It is a precise fit for your stated principles: honest about what was found versus guessed, fail loudly, and auditability over convenience. It gives a reader, human or Copilot, a calibrated signal about how much weight a cross reference carries. For a team producing official statistics, a knowledge base that distinguishes a verified methodological link from a plausible hunch is worth more than one that flattens both into the same confident prose.

### The semantics, fixed for your context

Write these definitions into your `.cg-docs/` authoring guide so they are applied consistently.

| Label | Meaning in compound-gpid | Example |
|-------|--------------------------|---------|
| `EXTRACTED` | The relationship is explicitly established in code, a spec, an official methodology, or a verified result. Not a judgment call. | This solution uses the FGT function defined in that artifact. |
| `INFERRED` | A reasonable, defensible connection the author drew, but not explicitly documented anywhere. | This deflator issue is probably related to that PPP vintage change. |
| `AMBIGUOUS` | A connection the author suspects but cannot stand behind. Flagged for human review. | These two discrepancies might share a root cause. |

### Step by step

1. **Add `confidence` as a required field** on every `related` link in the front matter schema, and have `cg-index.py` reject any value outside the three labels. Required, not optional, so the author cannot dodge the calibration.

2. **Render the label in the wiki.** In topic articles and on each artifact entry, show the label next to the link, for example `related: fgt-poverty-line-construction (EXTRACTED)`. Copilot then sees the calibration when it follows the map.

3. **Surface AMBIGUOUS links for review.** In `index.md`, generate a short section listing every AMBIGUOUS link across the corpus. This is your review queue, the same role graphify gives the label in `GRAPH_REPORT.md`. An AMBIGUOUS link is a question waiting to be resolved into EXTRACTED, downgraded, or deleted.

4. **Optionally extend to inline claims.** If you want calibration below the link level, adopt a lightweight inline marker in artifact prose, for example a trailing `[INFERRED]` on a sentence. Keep it optional to avoid burdening authors; the link level labels are the part that earns its keep.

5. **Make it stick through review.** Add a check to `/cg-review` or your Compound step that any new `.cg-docs/` artifact has confidence labels on all its `related` links. This is the change management lever: the convention only survives if the workflow enforces it, especially as the analytical group starts authoring artifacts.

### Definition of done

Every cross link in `.cg-docs/` carries a confidence label, the indexer rejects artifacts that omit one, and `index.md` shows a live list of AMBIGUOUS links awaiting review.

---

## 5. How this runs without becoming a model call

The whole point is that `cg-index.py` is harness, not inference. Run it deterministically:

- **Primary trigger:** a git post-commit hook, the same mechanism graphify offers with `graphify hook install`. It runs once per commit, needs no background process, and works regardless of editor. This keeps the brain current as a side effect of normal work.
- **Manual trigger:** a `/cg-index` command for on demand rebuilds, useful during the Compound step before committing.
- **Never inside a prompt or agent as a model action.** Copilot consumes the generated `index.md`; it does not build it. Building is Python in a hook.

This placement is what lets you claim a token efficiency benefit honestly. The expensive structural work is paid once, deterministically, off the inference path. Copilot only ever pays to read a compact, prebuilt map.

---

## 6. Sequencing and dependencies

Build in this order. Each step depends on the one before it.

1. **Prerequisite, already on your radar: reliable Python detection on Windows.** None of this ships until `cg-index.py` can be invoked dependably across your team's Windows install methods. This is the existing Stage 1 blocker and it gates everything here.
2. **Front matter schema plus authoring convention** (principles two and four data model). Decide the schema, write the authoring guide, including the confidence label definitions.
3. **`index.json` builder with fail loud validation** (principle two). Full rebuild, no cache yet.
4. **Wiki renderer** (principle one). The view over `index.json`.
5. **Context contract update** so prompts load `index.md`. This is when the token benefit becomes real.
6. **Content hash cache** (principle three). The optimization, added only once the full rebuild is trusted.
7. **Review enforcement of confidence labels** (principle four step five). The change management lever, added as the analytical group begins authoring.

A reasonable first slice that delivers value on its own is steps two through five: schema, index, wiki, context contract. The cache and the review gate are refinements you can defer.

---

## 7. Pester and test implications

Your suite asserts on prompt and agent structure, so the structural changes here need coordinated test updates. Plan for:

- Tests asserting the front matter schema is enforced: a fixture artifact missing a required field must fail the build.
- A determinism test: build twice on a fixed fixture corpus and assert byte identical `index.json` and `index.md`.
- A cache correctness test: edit one fixture, rebuild, assert only that file was reparsed and that inbound links updated.
- A context contract test: assert the relevant prompts reference `.cg-docs/_index/index.md` and do not point at the raw tree.
- Validation tests for each failure mode: duplicate id, dangling `related` target, illegal confidence value.

Write these as the spec before implementing, consistent with your test first integrity principle. The validation rules are deterministic, so they are genuinely unit testable, which is the right place for that rigor.

---

## 8. Failure modes and honest risks

- **The wiki drifting from the source.** If anyone hand edits `_index/`, the brain now has two truths. Mitigate with the generated banner, the regenerate on commit hook, and ideally a check that fails if `_index/` was edited by hand. Treat generated files as build output.
- **Commit the wiki, or gitignore it.** Committing makes the brain browsable on GitHub and diffable in review, which suits an auditable team, but it adds regeneration noise to diffs. Gitignoring keeps diffs clean but means the wiki must be rebuilt locally and is absent from the remote. For your auditability priorities, committing is probably right, but only if the build is deterministic enough that diffs stay meaningful. Decide deliberately.
- **Windows text handling.** UTF-8, BOM, and CRLF will bite a naive parser. Read bytes for hashing, decode UTF-8 explicitly for parsing, and normalize newlines. Add a fixture with a BOM and CRLF to lock this down.
- **Junction architecture interaction.** `cg-index.py` operates per project on that project's `.cg-docs/`. Confirm the hook and the command resolve paths correctly through the directory junctions rather than following them into the global clone and indexing the wrong tree. Test this explicitly on a junctioned project.
- **Adoption tax on the analytical group.** Required front matter and confidence labels add friction for sixteen economists who are still migrating to R and GitHub. If the convention is too heavy it will be skipped or faked. Keep the required surface minimal (id, title, tags, summary, status, and confidence on links), provide a snippet or template, and let `/cg-compound` scaffold the front matter so authors fill blanks rather than remember a schema.
- **Resist the graph stack.** The temptation will be to pull in NetworkX and community detection to match graphify feature for feature. At your corpus size that is maintenance burden with no payoff and a dependency that breaks the stdlib rule. Add it only when the corpus and a concrete need both demand it.

---

## 9. Paste-ready roadmap insert

> **Stage 1 (Local knowledge index), expanded.** Build `cg-index.py` (stdlib only, deterministic, runs in a post-commit hook and via `/cg-index`, never as a model call) that turns `.cg-docs/` into a navigable brain:
>
> 1. **Authoring convention.** Required YAML front matter on every artifact (`id`, `title`, `type`, `tags`, `summary`, `status`) plus `related` links each carrying a confidence label (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`). Definitions written into the `.cg-docs/` authoring guide.
> 2. **`index.json`.** Deterministic aggregation of front matter plus explicit links, with fail loud validation (duplicate id, dangling link, illegal confidence). Inbound links inverted from authored outbound links.
> 3. **Navigable wiki.** Generated `.cg-docs/_index/index.md` entry point plus per topic articles, sorted for reproducible output, marked generated, with a live AMBIGUOUS-links review queue.
> 4. **Context contract.** Prompts load `.cg-docs/_index/index.md` as the knowledge entry point instead of crawling the tree. This is the token efficiency mechanism.
> 5. **Incremental cache.** SHA256 per file cache (`hashlib`) so commits trigger cheap incremental rebuilds; global analytics always recomputed; cache versioned and invalidated on schema change.
> 6. **Review enforcement.** `/cg-review` (or the Compound step) requires confidence labels on all new `related` links.
>
> **Prerequisite:** reliable Windows Python detection (existing Stage 1 blocker).
> **Tests:** schema enforcement, build determinism, cache correctness, context contract references, validation failure modes. Spec first, per test first integrity.
> **Stage 2 link:** each project's `index.json` is the unit the shared cross-project knowledge base later unions through the junction architecture.

---

### Sources
- graphify README: https://github.com/safishamsi/graphify
- graphify ARCHITECTURE.md: https://raw.githubusercontent.com/safishamsi/graphify/main/ARCHITECTURE.md
- GitHub Copilot agent mode plus MCP, GA in VS Code: https://github.blog/news-insights/product-news/github-copilot-agent-mode-activated/
