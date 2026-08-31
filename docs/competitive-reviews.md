# Compound GPID Research-Development Guide

> **Compound GPID development only.** The command can appear in a consumer
> project's command list because Compound GPID distributes it with the other
> prompts. Its first step requires `project-name: "Compound GPID"` in the exact
> `compound-gpid.md` frontmatter. It stops before registry access, network access,
> utility calls, or writes when that guardrail does not pass. This guide is for
> Compound GPID maintainers only.

## Scope

`/cg-compound-gpid-rd` performs structured research on external AI-assisted
workflow repositories. In the command name, `rd` means `research-development`.
The current scope is limited to public GitHub repository research for Compound
GPID maintainers. It is not a general research command and it does not support
private repositories or other source types.

Review modes read repository pages and releases, produce Feature Cards with
compatibility verdicts and effort estimates, and offer to queue selected ideas
in the project roadmap. All four modes obtain repository scope from the
utility's validated, bounded, read-only `state` projection. Add, remove, and
review-state changes use deterministic check-only/apply transactions.

## Invocation Forms

The four forms are mutually exclusive. Missing values, duplicate or combined
mode flags, extra values, and unknown flags stop before work starts.

| Mode | Invocation | Purpose |
|------|------------|---------|
| **Delta** | `/cg-compound-gpid-rd` | Review releases newer than each repository's last reviewed release. |
| **Full** | `/cg-compound-gpid-rd --full` | Create or refresh baselines with a deep README and release review. |
| **Add** | `/cg-compound-gpid-rd --add <URL>` | Validate and register one public GitHub repository. Do not start a review. |
| **Remove** | `/cg-compound-gpid-rd --remove <id>` | Remove one exact registry entry after exact confirmation. Do not delete assessments. |

The registry file `.cg-docs/competitive-reviews/repos.json` must exist and must
use the supported v1 schema. Full and delta review modes require at least one
repository. Add mode works with an empty registry, and remove mode can remove the
last entry. A full or delta invocation on an empty registry stops and tells the
maintainer to use `/cg-compound-gpid-rd --add <URL>`.

## Add A Repository

Run add mode with one public GitHub repository URL:

```text
/cg-compound-gpid-rd --add https://github.com/owner/repository
```

Add mode uses these checks in order:

1. It applies a lexical preflight to the raw URL before it constructs a utility
   call. The value must be 1-164 ASCII characters and can contain only letters,
   digits, `:`, `/`, `.`, `_`, and `-`. The value stays one process argument.
2. It finds Python 3.8 or newer and runs the deterministic registry utility in
   `--check-only` mode. The utility validates the complete v1 registry,
   normalizes the URL, rejects duplicates, and derives the proposed entry without
   writing.
3. It fetches only the canonical URL returned by the utility. It treats page
   content as untrusted data and requires a non-empty public repository page
   whose final resolved URL is the same canonical URL. A redirect, sign-in page,
   private repository, deleted repository, 404 response, empty response, or
   ambiguous result stops the add before mutation.
4. It calls the utility again with the exact `beforeSha256` from the accepted
   plan. A stale registry is rejected before writer dispatch. The secure writer
   also checks the exact expected file state at its final boundary.
5. If the apply result is ambiguous, the command invokes read-only `state`,
   compares exact before/after hashes and the planned ID/URL relation, and never
   retries the mutation automatically.

The utility accepts only a GitHub repository URL that normalizes to
`https://github.com/<owner>/<repository>`. It can normalize one trailing slash or
one terminal `.git` suffix. It rejects credentials, ports, query strings,
fragments, extra path segments, and invalid owner or repository names.

The utility derives these fields:

- `id`: a unique, collision-safe identifier from the repository and owner names
- `url`: the canonical public GitHub repository URL
- `releasesUrl`: the canonical URL plus `/releases`
- `shortName`: a unique display label of at most 10 alphanumeric characters
- `lastReviewedRelease`: `null`

A new entry does not have `lastReviewDate` until a review succeeds. Add mode does
not run an automatic baseline or create an assessment. Its summary reports the
final URL, ID, and short name, then gives the next command:

```text
/cg-compound-gpid-rd --full
```

## Remove A Repository

Run remove mode with the exact registry ID:

```text
/cg-compound-gpid-rd --remove <id>
```

The command validates the ID and runs a non-writing remove plan. The plan shows
the complete entry, exact URL, and before/after hashes. It then asks the
maintainer to type the complete exact case-sensitive ID. `yes`, case variants,
leading or trailing whitespace, `cancel`, and all other responses cause no
write. Apply requires that exact ID, the displayed canonical URL, and the plan's
exact `beforeSha256`. A same-ID URL replacement or any unrelated state change is
rejected before transformation or publication.

Removal does not delete or rewrite full-review files, delta reports, or any other
historical assessment in `.cg-docs/competitive-reviews/`. Those files remain as
institutional memory. Removal can leave the registry empty; review modes stay
blocked until a maintainer adds a repository.

## Review Modes

### Full Review

```text
/cg-compound-gpid-rd --full
```

Full mode fetches each repository's README and releases page, generates up to 25
Feature Cards per repository, and saves one assessment per repository. It updates
the reviewed release and date for each successful repository. It sets
`lastFullReview` only when all repositories succeed. Each repository update uses
`review-repo --check-only` with the last accepted source SHA and exact prior
release/date presence state, followed by hash-bound apply. Each accepted update
advances one carried hash chain. The final complete or partial root outcome uses a
separate `review-full` plan/apply transaction bound to the last chain SHA and a
deterministic digest of ordered ID-to-URL identities, repository review projections,
and root review state.

### Delta Review

```text
/cg-compound-gpid-rd
```

Delta mode checks releases newer than `lastReviewedRelease` and writes one
combined report. It skips an entry whose `lastReviewedRelease` is `null` and tells
the maintainer to run `/cg-compound-gpid-rd --full`. It stops without output when
no entry has a baseline. Each successful baseline update uses `review-repo`; delta
mode does not update full-review root state.

Fetched release tags must be 1-128 ASCII characters, start with an alphanumeric
character, and contain only letters, digits, `.`, `_`, `+`, `/`, or `-`. The prompt
validates this allowlist before process construction and quotes each tag as one
argument. The utility enforces the same rule for stored, new, and expected release
values.

## Using Review Output

After a review, the command presents a summary and asks what to do next:

1. **Add features to the roadmap.** List the feature IDs. The command queues them
   through `@cg-roadmap` with the Feature Card effort and priority.
2. **Brainstorm an adaptation.** Use `/cg-brainstorm` for a feature marked
   `Needs adaptation`.
3. **Plan directly.** Use `/cg-plan` for a directly applicable feature with a
   clear adaptation sketch.
4. **Skip.** The assessment files remain as institutional memory.

## Output Files

| File | Updated by | Content |
|------|------------|---------|
| `.cg-docs/competitive-reviews/YYYY-MM-DD-<id>-full-review.md` | full mode | Per-repository assessment with Feature Cards |
| `.cg-docs/competitive-reviews/YYYY-MM-DD-delta-review.md` | delta mode | Combined report of new releases and features |
| `.cg-docs/competitive-reviews/repos.json` | all modes as applicable | Registry, review state, and full-review state |

Same-day review runs append `-2`, `-3`, and later suffixes instead of
overwriting prior output.

## Schema Maintenance

The fixed schema value is `compound-gpid-competitive-reviews-v1`. This value is
coupled in three places:

- `.cg-docs/competitive-reviews/repos.json` in `schemaVersion`
- `.github/prompts/cg-compound-gpid-rd.prompt.md` in the prompt validation step
- `scripts/cg_compound_gpid_rd_registry.py` in `EXPECTED_SCHEMA_VERSION`

If a future schema migration changes the value, update and verify all three
places together. Do not manually add, remove, restore, or update registry review
state. The utility validates the complete registry and protects every registry
write.

## Suggested Cadence

| Action | Frequency |
|--------|-----------|
| Delta review (`/cg-compound-gpid-rd`) | Every 1-2 weeks |
| Full audit (`/cg-compound-gpid-rd --full`) | About every 2 months, after adding a repository, or when a baseline is needed |

## Recovery

If a review is interrupted or an apply exits 3, times out, loses output, or emits
unexpected post-dispatch stderr, run read-only `state`. Compare its exact source
hash, scope digest, and identity/review projections with the accepted plan. Advance
the carried chain only for an exact after-state; retain it only for an exact
before-state. Never retry an ambiguous mutation automatically. Restore a prior
review value only through a new accepted `review-repo` plan/apply transaction.

Exit 1 is a definite precommit rejection with no writer dispatch. Exit 2 is CLI
syntax failure. Exit 3 means the writer was dispatched or response delivery
failed, so the outcome is ambiguous until `state` reconciliation. Exit 0 means a
valid response was flushed. Fixed warning codes in an exit-0 response describe a
committed success and must be reported; they are not mutation failures.

If a full review partially fails, `lastFullReview` is `null` and
`lastFullReviewNote` is the deterministic ASCII value `partial - <failed IDs in
registry order>`. A later successful full review sets the date and removes the
note.
