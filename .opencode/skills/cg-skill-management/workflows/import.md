# Import Workflow

1. Normalize one credential-free public GitHub HTTPS origin, bundle path, and full commit SHA.
2. Traverse nonrecursive Git trees under canonical metadata, depth, entry, file, and total-byte ceilings.
3. Fetch only declared blobs, reject redirects and unsupported Git modes, and verify each Git blob object ID.
4. Write only confined quarantine and deterministic redacted review evidence during planning.
5. Run strict shared admission. Project approval is exact-origin only; it does not grant plugin allowlist authority.
6. For project scope, store an inactive project record and append-only provenance in a digest-bound plan.
7. For plugin scope, require maintainer context, a repository allowlist match, explicit owner and capability metadata, approver audit metadata, and a new plugin-scope plan.
8. Keep project and plugin review evidence scope-bound so one plan digest cannot grant the other authority.
9. Apply source, provenance, registry, manifest, generated output, projection, and ownership bytes through one held-lock journal.

Planning never writes active lifecycle state. Apply requires `--apply <plan-digest>` with the same operation arguments.
