---
description: "Import an external skill with quarantine, security scanning, and approval workflow."
---

# Import Skill

Import an external skill into Compound GPID with full security scanning.

## Usage

```
/cg-import-skill <repo-url>@<full-sha> <path> [--mode review|vendor]
```

## Arguments

- `<repo-url>`: HTTPS URL of the source repository (must be on the allowlist)
- `<full-sha>`: Full 40-character immutable commit SHA
- `<path>`: Path to the skill root within the repository (e.g., `.github/skills/skill-name/`)
- `--mode`: `review` (default, consumer project) or `vendor` (maintainer source checkout)

## Process

1. Validate inputs against `.github/shared/vendor-policy.json`
2. Fetch pinned content into quarantine
3. Run admission checks (extensions, secrets, prompt-injection, paths, symlinks)
4. Generate deterministic review diff
5. For vendor mode: register in canonical source after approval

## Security

- Only HTTPS repositories on the allowlist
- Full 40-character SHA required (no short SHAs, branches, or tags)
- Executable files are always rejected
- Secrets are redacted in review output
- Prompt-injection patterns are detected and blocked
