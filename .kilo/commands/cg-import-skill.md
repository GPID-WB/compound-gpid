---
description: "Import an external skill into Compound GPID with quarantine, security scanning, and approval workflow."
---

# Import Skill

You are a security-aware skill importer for Compound GPID.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` for project context.
2. Read `compound-gpid.local.md` for language and project type.
3. Parse the invocation arguments: `<repo-url>@<full-sha> <path>` with `--mode review|vendor`.

### Step 1: Validate Inputs

1. Parse the import specification into repository URL, full 40-character SHA, and skill path.
2. Validate the repository is on the allowlist in `.kilo/shared/vendor-policy.json`.
3. Validate the skill path is a normalized descendant of an approved upstream skill root.
4. Validate the SHA is a full 40-character hex string (not a short SHA or branch name).

If any validation fails, stop with the exact error and remediation.

### Step 2: Determine Mode

**review** mode (default, consumer project):
- Fetches the pinned content into a quarantined directory.
- Runs full admission checks.
- Produces a deterministic review diff.
- Cannot write to canonical `.github/skills/`.

**vendor** mode (maintainer source checkout):
- Same quarantine and admission as review.
- Requires the working directory to be a verified Compound GPID canonical source checkout.
- After approval, copies the bundle into `.github/skills/` with full provenance registration.
- Must be on an approved branch with matching git origin.

### Step 3: Fetch to Quarantine

Run `python scripts/cg_import_skill.py <spec> --mode <mode> --root <path>`.

The script:
1. Fetches the pinned content using `git archive` or shallow clone.
2. Writes quarantine metadata.
3. Runs admission checks (extensions, path safety, symlinks, secrets, prompt-injection, frontmatter, binary content).
4. Generates a deterministic, secret-redacted review diff.
5. Saves review evidence to `.compound-gpid/vendor-reviews/`.

### Step 4: Report Results

If admission passes:
- Show the review diff location and file summary.
- For review mode: "Quarantined for review. Run `/cg-import-skill <spec> --mode vendor` from the canonical source checkout to vendor after approval."
- For vendor mode: show the registration result.

If admission fails:
- Show each error, secret finding, and injection finding.
- "Import rejected. Review the findings and fix the source before re-importing."

### Step 5: Cleanup

If the import was rejected, leave the quarantine directory for inspection.
If the import was vendored, clean up the quarantine directory.

## Invocation Arguments

```
/cg-import-skill <repo-url>@<full-sha> <path> [--mode review|vendor]
```

## Security Rules

- Never fetch from non-HTTPS repositories.
- Never accept a short SHA — always a full 40-character immutable commit.
- Never follow redirects, submodules, or LFS pointers.
- Never execute fetched content — all checks are static.
- Never auto-approve — vendor mode requires explicit maintainer action.
- Redact all detected secret values in review output.
- Reject executable files regardless of mode.

## Invocation Arguments

User-provided slash-command arguments:

```text
$ARGUMENTS
```
