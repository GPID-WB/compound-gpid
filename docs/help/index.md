# Help and Troubleshooting

Start with the smallest recovery path. Preserve user files and capture the
actual error before using repair commands that discard changes in the global
plugin clone.

## Command help

Use the [command browser](../reference/commands.md) to find slash commands,
terminal commands, and complete workflows. Its catalog is checked against the
command definitions during the documentation build.

The examples below are supported only for the verified Kilo configuration
listed here. Static adapter checks pass for all five hosts; runtime status is separate.

| Host | Runtime status | Tested configuration |
|---|---|---|
| Claude Code | Unverified | No certified runtime probe |
| Codex | Unverified | No certified runtime probe |
| GitHub Copilot | Unverified | No certified runtime probe |
| Kilo | Verified | macOS, Kilo 7.4.20, `openai/gpt-5.6-terra`, high reasoning effort |
| OpenCode | Unverified | No certified runtime probe |

In the verified Kilo configuration, open a project linked to the development
installation, with the `cg-help` backend available on PATH. Use these lookups in
the host's command input:

```text
/cg-help
/cg-help /cg-help
```

The first returns the command overview; the second explains `/cg-help` itself.
The host transfers the query through a prepared file and relays the backend's
answer. Running `/cg-help` does not install the backend or generate documentation.
If it reports unavailable help, check the installation and project linking before
retrying; do not replace the response with guessed commands.

Evidence was collected on 2026-09-17 for source commit
`9e2ed0008c46a210e0381ab55b337009ea33a996`, using a process-only model selection.
Overview, exact lookup, punctuation preservation, and unchanged result delivery
passed. This evidence does not certify other models, host versions, or operating
systems. Maintainers can recheck the stored source bindings with:

```sh
python3 scripts/cg_verify_help_support.py --evidence .cg-docs/work-reports/2026-09-17-docs-help-support.json
```

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
