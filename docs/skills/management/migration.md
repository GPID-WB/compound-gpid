# Migrate to `cg-skill`

The public migration is an immediate replacement with no compatibility aliases.
Use this map only after the release notes confirm that the staged final-tree gate
passed.

| Previous command | Replacement |
| --- | --- |
| `/cg-find-skill [filters]` | `/cg-skill find [filters]` |
| `/cg-import-skill <repository> <path> <full-sha> --license <id>` | `/cg-skill import <repository> <path> <full-sha> --license <id>` |

Shell automation must replace the old launcher name with `cg-skill` and keep the
operation as the first command argument. Put common options before the operation.
Mutation scripts must preserve the two-step plan and apply flow; do not reuse a
plan after changing arguments or inputs.

Use [find](commands/find.md), [import](commands/import.md), and the
[consumer guide](consumers/index.md) for executable examples. Historical release
and project evidence remains immutable and is not rewritten.
