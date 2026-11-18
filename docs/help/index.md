# Help and Troubleshooting

Start with the smallest recovery path. Preserve user files and capture the
actual error before using repair commands that discard changes in the global
plugin clone.

## Choose the problem

For source-cited guidance, ask `/cg-help` in chat, for example
`/cg-help compare planning and work`. Help is advisory: it does not activate
suites, repair installations, or execute the recommended commands. It asks for
clarification when needed and reports unsupported requests instead of inventing
an answer. Ask in your preferred language; command identifiers remain unchanged.

From a terminal on Windows or macOS, use the installed wrapper:

```text
cg-help query "How do I configure this project?" --root "/path/to/project" --format json
```

On Windows use a Windows path, such as `--root "E:\my project"`. The catalog
and cited sources belong to the plugin installation, so consumers need no local
`docs/` or `scripts/`. Help distinguishes active commands from inactive suites;
before setup or with invalid configuration, it labels general setup guidance
without claiming verified command availability. Inactive commands receive
metadata and a remedy, not their workflow instructions.

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

If help reports a missing or malformed installation catalog, preserve local
changes and follow the normal [update path](../versioning.md). Maintainers
refresh the catalog through `python scripts/cg_generate_targets.py --all`;
queries never rebuild it or mutate the consumer. Citations name installation
source paths, headings, and line ranges. If the catalog has no eligible evidence,
help states that limitation rather than falling back to an unsourced answer.

The [Troubleshooting Reference](../troubleshooting.md) preserves detailed
procedures for Python and PATH failures, old install paths, Constrained
Language Mode, link conflicts, updates, VS Code crashes, Pester safety, logs,
GitHub CLI authentication, issue linkage, and historical recovery cases.

## Related pages

- [Getting Started](../getting-started/index.md)
- [Configuration](../configuration/index.md)
- [Updates and Versions](../versioning.md)
