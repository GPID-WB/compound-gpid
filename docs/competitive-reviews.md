# Competitive Reviews Guide

> **compound-gpid development only.** This feature is part of the compound-gpid
> plugin infrastructure. It is **not available** in consumer projects. If you see
> `/cg-review-repos` in your Copilot autocomplete, do not use it — it will stop
> immediately with an explanatory message. This guide is for compound-gpid
> maintainers only.

## What It Does

`/cg-review-repos` performs a structured competitive analysis of external AI-assisted
workflow repos to identify features worth incorporating into compound-gpid. It fetches
README pages and release notes, produces Feature Cards with compatibility verdicts and
effort estimates, and offers to queue the best ones into the project roadmap.

## The Two Modes

| Mode | Command | When to use |
|------|---------|-------------|
| **Full** | `/cg-review-repos --full` | Initial baseline for a new repo, or periodic deep audit |
| **Delta** | `/cg-review-repos` | Weekly/biweekly check-in for new releases |

**Full mode** fetches each repo's README and releases page, generates up to 25 Feature
Cards per repo, and saves one assessment file per repo.

**Delta mode** only checks releases newer than the last reviewed tag. Faster and
lighter — produces a single combined delta report.

## Getting Started

### Prerequisites

The registry file `.cg-docs/competitive-reviews/repos.json` must exist with at least
one repo entry. The current registry tracks three repos:

- **CE** — [Compound Engineering Plugin](https://github.com/EveryInc/compound-engineering-plugin)
- **SP** — [Superpowers](https://github.com/obra/superpowers)
- **GSD** — [GSD-2](https://github.com/gsd-build/gsd-2)

### Step 1 — Run the full baseline

```
/cg-review-repos --full
```

This will:
1. Fetch each repo's README and releases page
2. Generate up to 25 Feature Cards per repo with compatibility verdicts
3. Save per-repo assessment files in `.cg-docs/competitive-reviews/`
4. Update `repos.json` with the latest release tag and date for each repo
5. Show a summary table highlighting the top features worth pursuing
6. Ask if you want to add any to the roadmap via `@cg-roadmap`

### Step 2 — Ongoing delta reviews

After the baseline exists, run delta mode periodically:

```
/cg-review-repos
```

This only fetches releases newer than the last reviewed tag — much faster than a full
run. It produces a single combined delta report.

## What You Do With the Output

After each run, the prompt presents a summary table and asks what to do next. Your
options:

1. **Add features to the roadmap** — List the feature IDs when prompted. They will be
   queued via `@cg-roadmap` with the effort and priority from the Feature Card.

2. **Brainstorm an adaptation** — For features marked "Needs adaptation", copy the
   Feature Card description and run `/cg-brainstorm` to work out how to implement it
   in compound-gpid's architecture.

3. **Plan directly** — For features marked "Directly applicable" with a clear
   adaptation sketch, run `/cg-plan` to jump straight to an implementation plan.

4. **Skip** — Say "none" when prompted. The assessment files remain in
   `.cg-docs/competitive-reviews/` as institutional memory for future reference.

## Output Files

| File | Created by | Content |
|------|-----------|---------|
| `.cg-docs/competitive-reviews/YYYY-MM-DD-<id>-full-review.md` | `--full` | Per-repo assessment with all Feature Cards |
| `.cg-docs/competitive-reviews/YYYY-MM-DD-delta-review.md` | delta mode | Combined report of new features across all repos |
| `.cg-docs/competitive-reviews/repos.json` | both modes | Registry with last-reviewed release tags and dates |

Same-day re-runs append `-2`, `-3`, etc. to avoid overwriting prior output.

## Adding a New Repo

1. Edit `.cg-docs/competitive-reviews/repos.json` — add an entry:
   ```json
   {
     "id": "my-repo",
     "url": "https://github.com/owner/my-repo",
     "releasesUrl": "https://github.com/owner/my-repo/releases",
     "shortName": "MR",
     "lastReviewedRelease": null,
     "lastReviewDate": null
   }
   ```
   - `id`: alphanumeric + hyphens, max 50 characters
   - `shortName`: 1–10 alphanumeric characters, unique across all repos
   - URLs must start with `https://github.com/`; `releasesUrl` must end with `/releases`

2. Add a column for the new repo in the concept mapping table (Step 1.5 of
   `.github/prompts/cg-review-repos.prompt.md`).

3. Run `/cg-review-repos --full` to baseline the new repo.

## Removing a Repo

Delete the entry from `repos.json` and remove the corresponding column from the
concept mapping table. Old assessment files in `.cg-docs/competitive-reviews/` can
be kept for historical reference or deleted.

## Suggested Cadence

| Action | Frequency |
|--------|-----------|
| Delta review (`/cg-review-repos`) | Every 1–2 weeks |
| Full audit (`/cg-review-repos --full`) | Every ~2 months, or when adding a new repo |

## Recovery

If a run is interrupted partway through:
- The prompt logs a **pre-run baseline** of each repo's `lastReviewedRelease` at the
  start of the session
- To recover: reset `lastReviewedRelease` in `repos.json` to the baseline values for
  any repos that were partially updated, then re-run

If a `--full` run partially fails (some repos fetched, others didn't):
- `lastFullReview` is set to `null` in the registry root
- A `lastFullReviewNote` field records which repos failed
- Re-run `--full` to complete the baseline — the note is removed on success
