---
date: 2026-05-07
title: "Cross-platform Python utility layer — Stage 1: cg-index.py"
status: decided
scope: "Deep"
chosen-approach: "Wrapper-time Python resolution + stdlib-only cg-index.py"
tags: [python, cross-platform, indexing, digest, search-index, cg-learnings-researcher, cg-compound]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Cross-platform Python utility layer — Stage 1: cg-index.py

## Context

As `.cg-docs/` accumulates plans, reviews, brainstorms, and solutions across
projects, `@cg-learnings-researcher` loses retrieval focus because it scans
all files broadly. The fix is a two-artifact system built by a new Python
script (`scripts/cg-index.py`), with platform wrappers and a cross-platform
Python resolver.

Stage 2 (shared cross-project knowledge base via a private GitHub repo) is
explicitly out of scope.

## Requirements

### Problem validated
Retrieval quality is actively degrading in projects with many `.cg-docs/`
files. The indexer must be built for scale from day one — file counts will
increase significantly.

### Two artifacts

1. **`.cg-docs/DIGEST.md`** — running compressed summary of all active
   solutions. One structured entry per solution. Read by
   `@cg-learnings-researcher` as the primary retrieval surface.

2. **`.cg-docs/search-index.json`** — lightweight metadata-only index of all
   `.cg-docs/` entries (plans, brainstorms, reviews, solutions). No summary
   field. Used by `@cg-learnings-researcher` for filtered lookup of
   non-solution entries.

### DIGEST.md entry format (locked down)

```markdown
## YYYY-MM-DD — <title>
**Path**: `.cg-docs/solutions/<category>/<filename>.md`
**Category**: <category>
**Language**: <language>
**Tags**: `tag1`, `tag2`
**Root cause**: <one sentence>
**Summary**: <2-3 sentence description of the problem, solution, and key
constraint or gotcha>
```

Key contracts:
- Only active solutions appear in DIGEST.md (no status field — archived/
  superseded solutions are omitted during rebuild).
- No other level-2 headings anywhere in DIGEST.md — only entry headers use
  `##`. Metadata uses level-1 headings or HTML comments.
- `## header count == entry count` exactly.
- One field per line — no `|` delimiters. Each line is `**Key**: value`,
  trivially parseable with `re.match(r'\*\*(.+?)\*\*:\s*(.*)', line)`.

### search-index.json schema (locked down)

```json
{
  "generated": "YYYY-MM-DDTHH:MM:SS",
  "entries": [
    {
      "path": ".cg-docs/plans/2026-04-01-my-plan.md",
      "type": "plan",
      "title": "...",
      "date": "YYYY-MM-DD",
      "status": "completed",
      "tags": ["tag1", "tag2"],
      "language": "r"
    }
  ]
}
```

No `summary` field — keeps the index lightweight (~200 chars/entry, scalable
to 1000+ entries without context window pressure). The agent reads full files
via `tools: ['read']` for entries that match.

No `root` field — paths are relative to project root, always.

### Python constraints
- stdlib only: no pip installs, no pyproject.toml, no venv.
- Modules: `json`, `re`, `pathlib`, `sys`, `datetime`, `argparse`,
  `dataclasses`.
- Python 3.8+ minimum (pathlib 3.4+, f-strings 3.6+, dataclasses 3.7+).
- No PyYAML — YAML frontmatter parsed manually with regex.
- Best-effort YAML parsing: single-line inline arrays parsed with quoted
  and unquoted value handling. Multiline arrays produce a warning and
  default to empty list. File is still indexed.

### cg-index.py modes

- `--index` (default): scan all `.cg-docs/` subdirectories, extract YAML
  frontmatter, produce `.cg-docs/search-index.json`.
- `--digest`: read all `.cg-docs/solutions/` files, build or rebuild
  `DIGEST.md` from scratch using the locked-down entry format.
- `--all`: run both `--index` and `--digest`.
- `--root <path>`: specify the project root (defaults to cwd).

### Error handling
- Malformed frontmatter in one file → warning + skip that file, not abort.
- Missing `.cg-docs/` directory → clear error message, exit 1.
- Partially written files → handle gracefully (missing closing `---` in
  frontmatter → skip with warning).
- Summary of skipped files printed at the end of every run.

### Integration triggers (4 total)

1. **`/cg-compound-refresh`** — explicit full rebuild. Final step invokes
   `cg-index --all`. Primary maintenance trigger.
2. **`/cg-compound` modulo-10 notification** — after appending a new entry
   to DIGEST.md, counts `##` headers. If `count % 10 == 0`, appends:
   "DIGEST.md now has N entries — good time to run `/cg-compound-refresh`
   to rebuild the search index." No stored counter. Live file count.
3. **`cg-link` bootstrap** — if `.cg-docs/` exists and has content, offer
   to run `cg-index --all` as a final step. Silent skip if empty/absent.
4. **Manual `cg-index`** — advanced users run from command line directly.

**Not a trigger**: `cg-update` does NOT call `cg-index`. The index is a
per-project artifact; cg-update runs from the global clone and has no
registry of linked projects. Stale registry entries, network drives, and
single-project failures are unacceptable failure modes for a global update.

### @cg-learnings-researcher changes

Tiered retrieval logic:
1. Read `.cg-docs/DIGEST.md`
2. Filter entries: tag exact match (high) → keyword match in title (medium)
   → keyword match in summary (low)
3. High-relevance: read full original file at stored path
4. Medium-relevance: return digest summary + path reference only
5. Zero matches or DIGEST.md absent: fall back to current directory scan

Fallback is permanent — ensures nothing is lost if digest is young, missing,
or predates a solution. Agent output must clearly distinguish digest findings
from fallback directory scan findings.

### shared/ stub (future-proofing)

- Empty `.github/shared/` directory with `.gitkeep` in the global clone.
- `shared/` added to `$ManagedDirs` in `link.ps1` and `MANAGED_DIRS` in
  `link.sh`.
- No behavioral change — directory is empty, no agent reads it yet.
- Safe for existing installations: the link loop handles "source exists,
  target doesn't" as the normal case. Users who don't re-run `cg-link`
  see no change. `.gitignore` update is generated dynamically from
  `$ManagedDirs`.

## Approaches Considered

### Approach 1: Install-time resolver with cached result
install.ps1 probes python3 → python → py, writes the result to
`.cg-python-cmd`. Wrappers read from that file.

**Pros**: Resolution runs once. Wrappers are fast. Easy to debug.
**Cons**: Stale if user changes Python install after running install.ps1.
Requires re-running install.ps1 to fix.
**Effort**: Small

### Approach 2: Wrapper-time resolution (probe on every call)
`bin/cg-index.cmd` itself contains the python3 → python → py probe logic.
No install-time caching. Each invocation finds Python fresh.

**Pros**: Always correct even if Python setup changes. Zero install-time
coupling. One fewer artifact.
**Cons**: 1-3 `where.exe` checks (~100ms) per invocation. Probe logic
duplicated if more Python wrappers are added (theoretical — only one now).
**Effort**: Small

### Approach 3: Hybrid — install-time + wrapper fallback
install.ps1 resolves and caches; wrappers check cache first, fall back to
probe if cache is missing or stale.

**Pros**: Fast normal case, self-healing.
**Cons**: Most complex. Fallback makes cache pointless — two code paths.
**Effort**: Medium

## Decision

**Approach 2: Wrapper-time resolution.** Correctness over speed. 100ms is
invisible. Only one Python wrapper exists today, so duplication is theoretical.
The wrapper provides discoverability and a consistent invocation surface, and
pays forward for future Python utilities.

install.ps1 still validates that Python is available (hard-fail with friendly
instructions if not found), consistent with install.sh behavior. But the
resolved command is not cached — each wrapper resolves independently.

## Devil's Advocate — Challenges Considered

1. **Could the agent be improved without an index?** — Changing agent
   instructions alone doesn't solve the scaling problem. The agent would
   still load every file to check frontmatter. The index moves that cost
   to a batch step. Correct structural fix.

2. **Do we need bin/ wrappers at all?** — Prompts could invoke the script
   directly. Decision: wrappers wanted for discoverability, consistency,
   and investment in future Python utilities.

3. **Is Phase 1 (resolver) over-invested for one script?** — Yes, if
   cg-index.py is the only Python script for 6 months. Accepted risk:
   Stage 2 (shared knowledge base) and future Python utilities will use
   the same infrastructure.

4. **Charter alignment** — No conflicts. "Fail loudly" is followed
   (hard-fail on missing Python, warnings on malformed frontmatter).
   Python 3.8 floor is conservative but safe for enterprise Windows.

## Next Steps

### Phase 1: Python resolver + install validation
- Add Python detection to `install.ps1` (probe python3 → python → py,
  hard-fail with instructions if none found)
- Create `bin/cg-index.cmd` with inline Python resolution logic
- Create `bin/cg-index` (macOS bash wrapper, calls `python3` directly)
- Verify both platforms before proceeding to Phase 2

### Phase 2: cg-index.py
- Build `scripts/cg-index.py` with `--index`, `--digest`, `--all`, `--root`
- Regex-based YAML frontmatter parser (stdlib only, best-effort)
- DIGEST.md builder with locked-down entry format
- search-index.json builder with metadata-only schema
- Error handling: skip malformed files with warnings, summary at end

### Phase 3: Integration
- Update `/cg-compound-refresh` to call `cg-index --all` as final step
- Add modulo-10 notification to `/cg-compound`
- Add bootstrap offer to `cg-link` (both platforms)
- Update `@cg-learnings-researcher` with tiered retrieval logic

### Phase 4: shared/ stub
- Create `.github/shared/.gitkeep`
- Add `shared/` to `$ManagedDirs` in `link.ps1` and `MANAGED_DIRS` in
  `link.sh`
