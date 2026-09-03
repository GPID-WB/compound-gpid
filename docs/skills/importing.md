# Importing External Skills

Compound GPID supports importing external skills through a controlled,
quarantined workflow. This ensures all imported content is security-scanned,
reviewed, and registered with full provenance before entering the canonical
source.

## Overview

The `/cg-skill import` operation provides two scopes:

| Scope | Who uses it | What it does |
|------|-------------|--------------|
| `project` | Consumer projects | Quarantines content, produces evidence, and plans an inactive project record |
| `plugin` | Maintainers (canonical source checkout) | Quarantines, reviews, and plans approved canonical vendoring |

## Usage

```
/cg-skill import <repo-url> <path> <full-sha> --license <id> [--scope project|plugin]
```

### Arguments

- **repo-url**: HTTPS URL of the source repository (must be on the allowlist)
- **full-sha**: Full 40-character immutable commit SHA (no short SHAs, branches, or tags)
- **path**: Path to the skill root within the repository (e.g., `.github/skills/skill-name/`)
- **scope**: `project` (default) or maintainer-only `plugin`

### Examples

Consumer project — quarantine for review:
```
/cg-skill import https://github.com/Kilo-Org/kilocode .github/skills/cg-skill-example abc123def456abc123def456abc123def456abcd --license MIT
```

Maintainer — vendor after approval:
```
/cg-skill import https://github.com/Kilo-Org/kilocode .github/skills/cg-skill-example abc123def456abc123def456abc123def456abcd --license MIT --scope plugin --owner cap-example --capability example --suites cg --platforms copilot,kilo --activation-cost low --triggers example --selectors "[]" --approver maintainer --review-reference review=1111111111111111111111111111111111111111
```

## Workflow

### 1. Consumer Review

1. Run `/cg-skill import <repository> <path> <full-sha> --license <id>` in your consumer project.
2. The importer fetches pinned content into `.compound-gpid/quarantine/`.
3. Admission checks run: file extensions, path safety, symlinks, secrets, prompt-injection, frontmatter, binary content.
4. A deterministic review diff is saved to `.compound-gpid/vendor-reviews/`.
5. Review the diff and decide whether to approve.

### 2. Maintainer Vendor

1. Switch to the Compound GPID canonical source checkout.
2. Run `/cg-skill import <arguments> --scope plugin` with all required canonical metadata.
3. Same quarantine and admission as review mode.
4. After approval, the bundle is copied to `.github/skills/` with provenance registration.
5. The module registry is updated with vendor import metadata.

## Security Checks

Every imported bundle passes through default-deny admission:

| Check | What it catches |
|-------|-----------------|
| Repository allowlist | Only approved HTTPS repositories |
| Full SHA requirement | Prevents mutable reference attacks |
| Path safety | Traversal, hidden files, Unicode confusables, Windows reserved names |
| File extension allowlist | Only `.md`, `.json`, `.yml`, `.yaml`, `.txt` |
| Executable rejection | `.exe`, `.sh`, `.py`, `.ps1`, etc. |
| Symlink/junction rejection | Prevents link-following attacks |
| Secret scanning | API keys, tokens, passwords, AWS credentials |
| Prompt-injection scanning | Instruction override attempts, shell execution patterns |
| Binary content detection | Null bytes, non-UTF-8 content |
| Bundle size limits | Max 1MB total, 64 files, 256KB per file |
| Frontmatter validation | Valid YAML frontmatter on `.md` files |

## Configuration

The vendor policy is defined in `.github/shared/vendor-policy.json`:

- **allowedRepositoryIdentities**: HTTPS URLs of approved source repositories
- **allowedUpstreamSkillRoots**: Path prefixes that skills must be under
- **maxBundleSizeBytes**: Maximum total quarantine size
- **blockedSecretPatterns**: Regex patterns for secret detection
- **blockedMarkdownInstructions**: Regex patterns for prompt-injection detection
- **approvedLicenses**: SPDX identifiers of acceptable licenses

## Quarantine and Review Evidence

- Quarantine directory: `.compound-gpid/quarantine/`
- Review evidence: `.compound-gpid/vendor-reviews/`
- Both directories are gitignored (quarantine is ephemeral, reviews are local evidence)

## Vendor Registration

Approved plugin imports receive canonical provenance and a capability record:

```json
{
  "id": "example",
  "owningModule": "cap-example",
  "sourceProvenance": "vendor/https://github.com/example/skills@<full-sha>"
}
```

## Limitations

- No automatic installation from arbitrary repositories
- No remote runtime fetching or network execution
- No semantic rewrites of imported skills (mechanical namespace/path rewrites only)
- No public marketplace — only approved allowlisted repositories
- Plugin scope requires a verified canonical feature-branch checkout

See the complete [import operation](management/commands/import.md),
[security controls](management/security.md), and [migration guide](management/migration.md).
