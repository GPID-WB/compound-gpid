# Update Imported Skill

Use `update <id> <new-full-sha>` only for a project or plugin skill with valid
pinned imported provenance. The repository, source path, origin scope, and skill
identifier are immutable. Plugin updates additionally require canonical
maintainer context and an allowlisted repository.

The candidate uses the same bounded acquisition, quarantine, and admission path
as import. Review output contains only deterministic paths, change kinds, sizes,
and SHA-256 digests. Apply appends source, approval, policy, evidence, diff, and
content digests to provenance before exact runtime convergence.
