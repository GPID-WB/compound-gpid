# Help and Troubleshooting

Start with the smallest recovery path. Preserve user files and capture the
actual error before using repair commands that discard changes in the global
plugin clone.

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
