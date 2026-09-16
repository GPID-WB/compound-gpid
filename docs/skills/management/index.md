# Skill Management

This guide documents the public descriptor-driven skill lifecycle available
through `/cg-skill` and the `cg-skill` shell command.

The [operation descriptors](../../../.github/shared/skill-management/operations/help.json)
define operation identity, role, phase, workflow, contract, tests, and command
page. The [dispatcher](../../../scripts/cg_skill.py) loads only complete
active descriptors.

## Start Here

> [!TECHNICAL] The current `cap-skill-management` capability declares support for `cg` only, and the registry owns `cg-*` prompt files in the Technical suite. Check the resolved project configuration before chat dispatch. Skills supply instructions; they are not slash commands. A capability-layer module is not automatically shared across suites.

Use `/cg-skill <operation>` in AI chat for guided work. Use shell `cg-skill
<operation>` in a terminal for deterministic results. Both use the operation
contracts below. Do not enter slash prompts in a terminal. The Python form is
for a checkout with `scripts/cg_skill.py`; consumer projects use the installed
wrapper. Put common options before the operation in either terminal form.

### Choose a Path

- [Consumer guide](#use-skills-in-a-project)
- [Maintainer guide](#maintain-plugin-skills)
- [Lifecycle and roles](#lifecycle-and-safety)
- [Security controls](#security-and-provenance)
- [Migration guide](#migrate-existing-workflows)

### Common Grammar

Common options must appear before the operation:

```text
python scripts/cg_skill.py [--project-root <path>] [--source-root <path>] [--format human|json] <operation> [operation arguments]
```

Consumer is the default role. The dispatcher derives maintainer authority from
the checkout context; a command-line role value cannot grant authority. Mutating
operations plan first and apply only the same digest-bound arguments with
`--apply <64-character-plan-digest>`.

## Lifecycle and Safety

Skill management separates source origin, admission, lifecycle, availability,
and manifest health so one status cannot imply another.

### State Model

| Dimension | Values | Meaning |
| --- | --- | --- |
| Origin | `plugin-canonical`, `project-imported` | The authority and store that own the bundle. |
| Admission | `quarantined`, `approved`, `rejected` | The bounded source-review state. |
| Lifecycle | `current`, `deprecated`, `removed` | Immutable identity progression. |
| Availability | `inactive`, `active` | Whether an explicit selected capability is usable. |
| Manifest health | `fresh`, `missing`, `stale`, `invalid` | Whether runtime availability is proven. |

An imported or created skill starts inactive. Activation is a separate explicit
plan. Deprecation blocks new activation but does not silently deactivate current
use. Removal requires inactive deprecated state, a valid successor, grace
evidence, completed migrations, zero active references, and checksum ownership.

### Roles

Consumers can discover, inspect, validate, audit, import project skills, and
manage explicit project selections. Maintainers can also change canonical plugin
assets, but only when invocation root, project root, and canonical source root
are the same approved feature-branch checkout.

Approver labels and review references are audit metadata. They do not grant
authority and do not replace repository review or branch protection.

### Plan and Apply

Every mutation creates a deterministic plan by default. Its digest binds
normalized arguments, resolved role, source and project roots, registries,
configuration, manifest, provenance, references, and bundle inventory.

Apply repeats the same operation arguments with `--apply <digest>`. A held lock,
durable journal, compare-before-replace publication, and exact final verification
make the operation crash-consistent and forward-recoverable. A changed input or
byte invalidates the plan rather than being overwritten.

### Lifecycle Paths

- Project: [import](#import-at-an-exact-sha) -> [activate](#activate-and-deactivate) -> [update](#update-an-imported-skill) -> [deprecate and remove](#deprecate-and-remove)
- Plugin: [create](#create-a-permanent-skill) or [vendor](#vendor-an-imported-skill) -> [registry review](#registry-and-capabilities) -> [release](#release-gates)

See [security controls](#security-and-provenance) before any source acquisition or destructive
operation.

## Use Skills in a Project

Consumers use read operations first, then review an exact plan before any project
change.

1. [Discover and inspect](#find-and-inspect) a skill and confirm its origin, lifecycle,
   capability, supported suites, and supported platforms.
2. [Import a project skill](#import-at-an-exact-sha) only from one exact public GitHub
   origin, path, and full commit SHA.
3. [Activate](#activate-and-deactivate) the explicit capability after review.
4. [Check availability](#availability) with a fresh manifest.
5. [Remediate findings](#safe-remediation) without bypassing a failed gate.

The [lifecycle model](#lifecycle-and-safety) explains why import and activation are
separate operations.

### Consumer Topics

- [Discover and inspect](#find-and-inspect)
- [Import a project skill](#import-at-an-exact-sha)
- [Activate and deactivate](#activate-and-deactivate)
- [Understand availability](#availability)
- [Remediate findings](#safe-remediation)

### Find and Inspect

Start with [help](commands/help.md), use [find](commands/find.md) for
deterministic filtering, and use [info](commands/info.md) for one immutable
identifier. Run [validate](commands/validate.md) before activation or after a
local change.

A missing or stale manifest permits clearly labeled prospective discovery. It
does not prove active or projected state, and availability filters remain blocked
until the manifest is fresh. Discovery never falls back to global, generated,
external, or network locations.

Terminal (PowerShell or POSIX), read-only discovery:

```text
cg-skill help
cg-skill find
cg-skill info cg-skill-management
```

The result identifies local metadata and findings; it is not proof that a skill
is active. Continue to [project import](#import-at-an-exact-sha) only when no approved local skill
meets the task.

### Import at an Exact SHA

[Import](commands/import.md) acquires one exact public GitHub bundle into
confined quarantine, verifies bounded metadata and content, runs admission, and
writes redacted review evidence. Planning does not change active lifecycle state.

Review the source identity, license, bundle inventory, resource classes,
findings, actions, and plan digest. Apply the same exact arguments only when the
evidence is complete. The committed project record remains inactive and gets one
reserved explicit-only capability.

Project approval cannot grant plugin vendoring authority. See [security](#security-and-provenance)
and then [activation](#activate-and-deactivate).

The `/cg-skill import` operation provides two scopes:

| Scope | Who uses it | What it does |
|------|-------------|--------------|
| `project` | Consumer projects | Quarantines content, produces evidence, and plans an inactive project record |
| `plugin` | Maintainers (canonical source checkout) | Quarantines, reviews, and plans approved canonical vendoring |

Chat grammar (replace every angle-bracket placeholder):

```text
/cg-skill import <repo-url> <path> <full-sha> --license <id> [--scope project|plugin]
```

- **repo-url**: Credential-free public GitHub HTTPS origin; plugin scope requires the allowlist, and project scope requires reviewed exact-origin admission.
- **full-sha**: Full 40-character immutable commit SHA (no short SHAs, branches, or tags)
- **path**: Path to the skill root within the repository (e.g., `.github/skills/skill-name/`)
- **scope**: `project` (default) or maintainer-only `plugin`

### Import Examples

These are illustrative source identities and digests, not known existing bundles
or approval evidence. Replace them with reviewed values; do not copy the apply
example until its plan is reviewed.

Consumer project, chat planning example:

```text
/cg-skill import https://github.com/Kilo-Org/kilocode .github/skills/cg-skill-example abc123def456abc123def456abc123def456abcd --license MIT
```

The importer places pinned content in `.compound-gpid/quarantine/`. Admission
checks cover extensions, paths, links, secrets, prompt injection, frontmatter,
binary content and resource classes. Review evidence is stored in
`.compound-gpid/vendor-reviews/`. Review it before approving and repeating the
same arguments with the returned `--apply <plan-digest>`. A blocked finding is
not partial success.

### Activate and Deactivate

[Activate](commands/activate.md) adds one explicit capability through a
byte-preserving configuration plan. [Deactivate](commands/deactivate.md)
removes only an explicit selection; it cannot subtract selector-derived or
dependency-required capabilities.

Both operations re-resolve the manifest, generate selected targets, publish
selected host projections, and verify exact desired paths and managed-bundle
inventories. Modified or user-owned projection files block unsafe deletion.

Terminal example, using a synthetic capability and digest:

```text
cg-skill activate project-skill-example
cg-skill activate project-skill-example --apply aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

After apply, use [availability](#availability) and [audit](commands/audit.md)
to confirm the final state. Run `cg-skill deactivate project-skill-example` to
plan deactivation, then review a new digest before applying it.

### Availability

Availability is reliable only when manifest health is `fresh`.

- `active` means the capability is selected and the current manifest proves it.
- `inactive` means the skill is known but is not selected.
- `prospective` means discovery used current registry data because the committed
  manifest is missing or stale.
- `invalid` means a contract failed and no runtime claim is safe.

Supported suite and platform metadata is eligibility, not activation. For a
project skill, only its one-to-one `selectedProjectSkills` entry selects the
bundle. Use [find](commands/find.md), [info](commands/info.md), and
[remediation](#safe-remediation) to distinguish these cases.

## Maintain Plugin Skills

Maintainer operations require one canonical development checkout on a
nondefault, nonprotected feature branch. Free-text role, origin, approver, or
review values cannot elevate a consumer context.

1. [Create](#create-a-permanent-skill) a new permanent skill or [vendor](#vendor-an-imported-skill) an
   imported bundle.
2. Review [registry and capability](#registry-and-capabilities) ownership.
3. [Update](#update-an-imported-skill) only from a new immutable full SHA.
4. [Deprecate and remove](#deprecate-and-remove) with successor and grace proof.
5. Run the separate [release gates](#release-gates).

Read [security controls](#security-and-provenance) before any canonical mutation.

### Maintainer Topics

- [Create permanent skills](#create-a-permanent-skill)
- [Vendor imported skills](#vendor-an-imported-skill)
- [Manage registry and capabilities](#registry-and-capabilities)
- [Update imported skills](#update-an-imported-skill)
- [Deprecate and remove](#deprecate-and-remove)
- [Release changes](#release-gates)

### Create a Permanent Skill

[Create](commands/create.md) scaffolds one canonical bundle with quoted
ASCII-safe frontmatter, explicit ownership, one capability, eligibility,
activation cost, triggers, selectors, provenance, and an atomic inventory.

Add only focused references, workflows, examples, and approved non-data
resources. Data-bearing, executable, linked, oversized, colliding, or undeclared
resources fail admission. Creation leaves the capability inactive.

Review [registry and capability rules](#registry-and-capabilities) before apply.
Use the [complete creation example](commands/create.md#examples) to supply all
required metadata; do not infer ownership or eligibility from the skill name.

### Vendor an Imported Skill

Plugin-scope [import](commands/import.md) reuses bounded acquisition,
quarantine, admission, and review evidence. It also requires maintainer context,
an allowlisted repository, explicit owner and capability metadata, approver audit
metadata, and an immutable review reference.

Project exact-origin approval is not reusable for plugin scope. Create and apply
a separate plugin plan. The vendor transaction publishes canonical source,
provenance, registry, manifests, generated targets, and projections together.

Use [security controls](#security-and-provenance) as the review checklist.
In the canonical checkout, plan with all metadata, review the quarantine and
evidence, then explicitly apply the returned digest. The following chat example
is illustrative, with synthetic SHA, owner, capability, and review reference:

```text
/cg-skill import https://github.com/Kilo-Org/kilocode .github/skills/cg-skill-example abc123def456abc123def456abc123def456abcd --license MIT --scope plugin --owner cap-example --capability example --suites cg --platforms copilot,kilo --activation-cost low --triggers example --selectors "[]" --approver maintainer --review-reference review=1111111111111111111111111111111111111111
```

### Registry and Capabilities

Every canonical asset has exactly one module owner. A capability identifies its
owning module, supported suites and platforms, source provenance, activation
cost, task triggers, and selectors. Dependencies can add required capabilities;
configuration cannot subtract them.

Project records use reserved owner `project-local`, capability
`project-skill-<id>`, explicit-only activation, and one-to-one selected-bundle
mapping. Project records cannot shadow canonical identifiers, owners, or
capabilities.

Run module ownership, dependency, and cross-suite checks before [release](#release-gates).

### Update an Imported Skill

[Update](commands/update.md) accepts one existing imported skill and one new
full commit SHA. It reuses the original immutable repository, path, origin,
identifier, and metadata authority.

Review the deterministic path, change-kind, size, and SHA-256 diff. Apply appends
source, approval, policy, evidence, diff, and content digests to provenance. It
does not replace prior provenance history.

Generic mutable update discovery is not available. A specific exact SHA is
required for every comparison. Follow the [update example](commands/update.md#examples),
review its diff, apply the exact digest, then validate and audit the new state.

### Deprecate and Remove

[Deprecate](commands/deprecate.md) preserves the immutable identifier and
records a valid same-origin successor. Existing active use receives a migration
warning, while new activation is blocked.

[Remove](commands/remove.md) requires deprecated inactive state, a successor,
immutable grace evidence, digest-bound migration edits, and a final zero-reference
rescan. It deletes only exact source bytes and checksum-owned projections, then
writes a permanent tombstone. User-owned or modified files are never deleted.

Plugin grace uses pinned release attestation data. Project grace uses a later
descendant project revision. See [release](#release-gates) and [migration](#migrate-existing-workflows).

### Release Gates

Release uses two separate complete gates.

1. While the current public commands remain active, run all operation evidence,
   authoritative native preflight, full unfiltered safe-runner Pester, docs,
   modules, target dry-run, and Windows/macOS/Linux plus Python 3.8 CI.
2. Record exact-tree evidence, then stage public registration and old-surface
   removal as one changeset generated from canonical source.
3. Run the complete final-tree gate and exact-tree CI again. A failure keeps the
   prior released tree active.

Future releases that cover plugin deprecations also create a reviewed
post-release attestation bound to the annotated tag object, peeled commit,
immutable release payload, and deprecation-record digests.

The new [release controller](../../release-controller.md) preserves these
evidence requirements. Payloads are reviewed before the release tag; the
post-tag attestation is a separate reviewed evidence PR that never moves that
tag. `published` is not `complete` until required documentation and evidence
hooks are remotely verified. Historical payloads and attestations remain unchanged.

The supplied publisher stays disabled. Bridge delivery, native clean-client
qualification, registered release-mode CI and sandbox/performance proof are
deferred, not passed. This does not defer ordinary PR CI or the authorized final
committed-input gate. Legacy bridge/recovery requires explicit maintainer
authorization and retains the old permission, branch, payload and tag checks.

## Security and Provenance

Skill management treats source acquisition, authority, lifecycle writes, and
destructive cleanup as separate fail-closed controls.

### Acquisition and Quarantine

Imports accept one credential-free public GitHub HTTPS repository, normalized
bundle path, and full commit SHA. Bounded tree and blob traversal verifies sizes,
Git object identities, paths, modes, links, content limits, license, secrets, and
the non-data resource policy before lifecycle state can change.

Every imported bundle passes through default-deny admission:

| Check | What it catches |
|-------|-----------------|
| Origin approval | Plugin allowlist or reviewed project exact-origin admission; neither grants the other scope |
| Full SHA requirement | Prevents mutable reference attacks |
| Path safety | Traversal, hidden files, Unicode confusables, Windows reserved names |
| File extension allowlist | `.md`, `.json`, `.yml`, `.yaml`, `.txt`; `.svg` is opaque and needs an approved non-data resource class |
| Executable rejection | `.exe`, `.sh`, `.py`, `.ps1`, etc. |
| Symlink/junction rejection | Prevents link-following attacks |
| Secret scanning | API keys, tokens, passwords, AWS credentials |
| Prompt-injection scanning | Instruction override attempts, shell execution patterns |
| Binary content detection | Null bytes, non-UTF-8 content |
| Bundle size limits | Max 1MB total, 64 files, 256KB per file |
| Frontmatter validation | Strict frontmatter validation for `SKILL.md` |

These are admission checks, not proof that instructions are safe or correct.
Review the actual source and evidence before apply.

### Authority and Approval

Consumer is the default role. Canonical mutation requires equal invocation,
project, and source roots in one approved feature-branch checkout. Approver and
review fields are audit metadata, not authorization proof. Project exact-origin
approval cannot grant plugin allowlist authority.

### Provenance and Supply Chain

Provenance is append-only and binds immutable source identity, policy, evidence,
inventory, and content digests. Plans and review evidence are redacted. Imported
content is never executed during admission, generation, validation, or projection.

### Destructive Controls

Apply uses one held lifecycle lock, durable expected-byte journal, and exact
desired-state verification. Removal requires complete references, successor and
grace proof, digest-bound migrations, zero active references, and checksum-owned
paths. Modified and user-owned files are preserved.

Use [audit](commands/audit.md), [remediation](#safe-remediation), and the
[lifecycle model](#lifecycle-and-safety) for operational checks.

### Vendor Policy

The vendor policy is defined in `.github/shared/vendor-policy.json`:

- **allowedRepositoryIdentities**: HTTPS URLs of approved source repositories
- **allowedUpstreamSkillRoots**: Path prefixes that skills must be under
- **maxBundleSizeBytes**: Maximum total quarantine size
- **blockedSecretPatterns**: Regex patterns for secret detection
- **blockedMarkdownInstructions**: Regex patterns for prompt-injection detection
- **approvedLicenses**: SPDX identifiers of acceptable licenses

Do not relax policy to force admission. Its resource classes and scope-specific
approval controls are part of the current import contract.

### Quarantine and Review Evidence

- Quarantine directory: `.compound-gpid/quarantine/`
- Review evidence: `.compound-gpid/vendor-reviews/`
- Both directories are gitignored (quarantine is ephemeral, reviews are local evidence)

### Vendor Registration

Approved plugin imports receive canonical provenance and a capability record:

```json
{
  "id": "example",
  "owningModule": "cap-example",
  "sourceProvenance": "vendor/https://github.com/example/skills@<full-sha>"
}
```

This is an illustrative record, not a complete registry schema.

### Limitations

- No automatic installation from arbitrary repositories
- No remote runtime fetching or network execution
- No semantic rewrites of imported skills (mechanical namespace/path rewrites only)
- No public marketplace; plugin origins require allowlisting and project origins require explicit reviewed admission
- Plugin scope requires a verified canonical feature-branch checkout

See the complete [import operation](commands/import.md),
[security controls](#security-and-provenance), and [migration guide](#migrate-existing-workflows).

## Diagnose and Recover

### Safe Remediation

Read the stable exit code, then process deterministic findings in their returned
order. Each finding includes an exact path and remediation.

Do not apply a stale plan, edit a generated tree, relax an admission ceiling, or
delete a modified projection. Repair the canonical source or project input, run
[validate](commands/validate.md), use [audit](commands/audit.md) when the
problem spans lifecycle state, and create a new plan.

The [result contract](#result-contract) defines all exit codes. The
[security guide](#security-and-provenance) defines findings that must remain fail-closed.

### Result Contract

Human and JSON output use the same deterministic result envelope. Every finding
has a stable code, severity, path, message, and remediation. Exit codes are:

| Result | Code | Meaning |
| --- | ---: | --- |
| `success` | 0 | The read, plan, or apply completed safely. |
| `internal` | 1 | Trusted dispatch or output failed unexpectedly. |
| `usage` | 2 | Operation grammar or typed arguments are invalid. |
| `contract` | 3 | A descriptor, schema, manifest, or result contract failed. |
| `role-context` | 4 | The validated checkout role cannot perform the operation. |
| `security` | 5 | Admission, path, source, or content security blocked the operation. |
| `lifecycle-conflict` | 6 | Current lifecycle state does not permit the requested transition. |
| `stale-plan` | 7 | Inputs or expected bytes changed after planning. |
| `verification` | 8 | Final desired-state verification failed. |

Do not reinterpret a nonzero code as partial success. Follow the returned
remediation and create a new plan after any relevant input changes.

## Migrate Existing Workflows

The public migration is complete and has no compatibility aliases. Replace old
invocations immediately; the retired prompt and wrappers are not shipped.

| Previous command | Replacement |
| --- | --- |
| `/cg-find-skill [filters]` | `/cg-skill find [filters]` |
| `/cg-import-skill <repository> <path> <full-sha> --license <id>` | `/cg-skill import <repository> <path> <full-sha> --license <id>` |

Shell automation must replace the old launcher name with `cg-skill` and keep the
operation as the first command argument. Put common options before the operation.
Mutation scripts must preserve the two-step plan and apply flow; do not reuse a
plan after changing arguments or inputs.

Use [find](commands/find.md), [import](commands/import.md), and the
[consumer guide](#use-skills-in-a-project) for executable examples. Historical release
and project evidence remains immutable and is not rewritten.

Documentation route compatibility is separate: old guide pages keep raw links
and old headings. The website maps those routes to this guide. An unknown section
shows an explicit notice; it does not silently select an unrelated section.

## Operation Reference

### Operations

| Operation | Role/context | Effect and next check |
| --- | --- | --- |
| `help` | Consumer or maintainer | Read descriptors; choose one operation |
| `find` | Consumer or maintainer | Discover metadata; inspect with `info` |
| `info` | Consumer or maintainer | Inspect one ID; validate before change |
| `validate` | Consumer or maintainer | Check contracts; remediate findings |
| `audit` | Consumer or maintainer | Check lifecycle/provenance/projections; remediate |
| `import` | Consumer; plugin scope needs maintainer context | Plan/apply an inactive record; activate separately |
| `activate` | Consumer or maintainer | Plan/apply one explicit selection; audit final state |
| `deactivate` | Consumer or maintainer | Plan/apply explicit deselection; verify projections |
| `create` | Maintainer only | Plan/apply inactive canonical scaffold; validate |
| `update` | Consumer or maintainer within origin authority | Plan/apply exact-SHA diff; validate and audit |
| `deprecate` | Consumer or maintainer within origin authority | Plan/apply successor record; migrate references |
| `remove` | Consumer or maintainer within origin authority | Plan/apply guarded retirement; verify tombstone |

The 12 detailed operation contracts remain authoritative for flags, examples,
result envelopes, and evidence anchors:

- [activate](commands/activate.md)
- [audit](commands/audit.md)
- [create](commands/create.md)
- [deactivate](commands/deactivate.md)
- [deprecate](commands/deprecate.md)
- [find](commands/find.md)
- [help](commands/help.md)
- [import](commands/import.md)
- [info](commands/info.md)
- [remove](commands/remove.md)
- [update](commands/update.md)
- [validate](commands/validate.md)
