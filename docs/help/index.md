# Help and Troubleshooting

Start with the smallest recovery path. Preserve user files and capture the
actual error before using repair commands that discard changes in the global
plugin clone.

## Command help

Use the [command browser](../reference/commands.md) to find slash commands,
terminal commands, and complete workflows. Its catalog is checked against the
command definitions during the documentation build.

The current source manifest binds the canonical help definitions, catalog, and
generated command assets for all five adapters. It does not certify live runtime behavior
for any host. Host-specific runtime observations are optional evidence and are
not required to distribute or use the plugin.

| Host | Source/static status | Live runtime certification |
|---|---|---|
| Claude Code | Current | Not certified |
| Codex | Current | Not certified |
| GitHub Copilot | Current | Not certified |
| Kilo | Current | Not certified |
| OpenCode | Current | Not certified |

In a linked project with the `cg-help` backend available on PATH, use these
lookups in the host's command input:

```text
/cg-help
/cg-help /cg-help
```

The first returns the command overview; the second explains `/cg-help` itself.
The host transfers the query through a prepared file and relays the backend's
answer. Running `/cg-help` does not install the backend or generate documentation.
If it reports unavailable help, check the installation and project linking before
retrying; do not replace the response with guessed commands.

The manifest records the exact source commit and Git-object digests. Its five
platform rows are source bindings, not stored test-result strings. CI separately
checks the catalog, generated targets, and platform test suites. Maintainers can
regenerate and verify the current bindings without a model or hosted agent:

```sh
python scripts/cg_generate_help_support.py
python scripts/cg_verify_help_support.py --evidence .cg-docs/work-reports/docs-help-support-current.json
```

The dated 2026-09-23 file is retained as historical Kilo probe evidence. It is
not the current cross-platform support manifest and does not set a Kilo version
floor, ceiling, provider, model, operating-system, or consumer requirement.

## Choose the problem

| Symptom | First check | Detailed path |
|---|---|---|
| `cg-link` or another command is not found | Restart the terminal and confirm the install `bin` directory is on PATH | [Installation Details](../installation.md) |
| Python is missing or resolves to the Windows Store stub | Install Python 3.8+ and confirm `python3`, `python`, or `py --version` reports Python | [Troubleshooting Reference](../troubleshooting.md#python-not-found) |
| A platform file was skipped | Determine whether it is user-owned or a modified managed copy; do not overwrite it blindly | [Configuration](../configuration/index.md#managed-and-user-owned-content) |
| `/cg-*` commands do not appear | Restart the IDE after linking and confirm setup was run in the project root | [Installation Details](../installation.md) |
| `cg-update` fails | Record the Git error; use `cg-update --fix` only when discarding global-clone changes is acceptable | [Updates and Versions](../versioning.md) |
| VS Code or Positron crashes | Stop repeated test attempts, preserve work, and run `/cg-diagnose` in a fresh session | [Troubleshooting Reference](../troubleshooting.md) |
| Pester hangs or floods output | Use the repository's canonical runner; never run the full test directory directly | [Contribute and Develop](../development/index.md#run-tests-safely) |
| GitHub issue or PR automation fails | Check `gh auth status`, repository identity, and permissions before retrying | [Troubleshooting Reference](../troubleshooting.md) |

## Safe diagnostic sequence

1. Copy the exact command, exit status, and concise error message.
2. Confirm the current project root and active installation path.
3. Check whether the affected file is user-owned, linked, generated, or
   manifest-managed.
4. Run the narrowest documented diagnostic or test.
5. Escalate to repair only after understanding what state it may discard.

## Complete recovery reference

The [Troubleshooting Reference](../troubleshooting.md) preserves detailed
procedures for Python and PATH failures, old install paths, Constrained
Language Mode, link conflicts, updates, VS Code crashes, Pester safety, logs,
GitHub CLI authentication, issue linkage, and historical recovery cases.

## Related pages

- [Getting Started](../getting-started/index.md)
- [Configuration](../configuration/index.md)
- [Updates and Versions](../versioning.md)
