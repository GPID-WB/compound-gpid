# Experimental Capabilities

The repository tracks possible retrieval and research capabilities in explicit
registries. Registry presence is not runtime support.

## Current active modes

- `native-brain-query` is the only active retrieval backend.
- `local-workflow` is the only active snapshot/research mode.

The active paths are local and deterministic. They do not imply vector search,
hosted retrieval, external browsing, or cross-project data transfer.

## Evaluation registries

- [Retrieval Backends](../retrieval-backends.md) records optional backend
  candidates and their gates.
- [Snapshot and External Research](../snapshot-external-research.md) records
  deferred modes and non-goals.

Candidates require explicit evaluation of privacy, offline behavior,
configuration, fallback, rollback, and measurable value before activation.
Documentation must not describe a candidate as available merely because its
name appears in a JSON registry.

## Related pages

- [Model Guide](../model-guide.md)
- [Governance and Security](../governance/index.md)
- [Complete Reference](../reference.md)
