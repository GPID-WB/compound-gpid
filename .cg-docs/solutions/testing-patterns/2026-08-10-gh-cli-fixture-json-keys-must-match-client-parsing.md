---
date: 2026-08-10
title: "gh CLI fixture JSON keys must match what the client actually parses"
category: "testing-patterns"
language: "Python"
tags: [fixtures, gh-cli, json, schema-drift, offline-testing, headRefName, mocking]
root-cause: "An offline fixture used a hand-chosen JSON key (headRef) while the production gh client parsed a different key (headRefName), so copied real gh output would silently lose data with no test catching it."
severity: "P3"
---

# gh CLI fixture JSON keys must match what the client actually parses

## Problem

The readiness validator's offline fixture (`scripts/tests/fixtures/ready_issue.json`)
supplies mocked GitHub state to `FixtureClient`. The fixture's PR items were
documented/structured with key `headRef`, but the `GhCliClient` — the real
client whose output the fixture mimics — parses `headRefName` (the actual
`gh pr list --json` key). Because `FixtureClient` used `pr.get("headRef", "")`,
a maintainer copying real `gh pr list` output into the fixture would silently
get `head_ref=""` — branch-name data lost with no test failing (the fixture
has no PR items, so no test covers the path).

## Root Cause

The fixture schema and the client parsing diverged because the two were
written independently: the fixture author chose a readable key; the gh CLI
contract uses `headRefName` (and authors as `{ "login": ... }` dicts). Nothing
enforced that the fixture is a *mirror of the real wire format*.

Additionally, `FixtureClient` read `author` as a plain string while the gh
client normalizes `author: {"login": ...}` — a second latent drift in the same
record shape.

## Solution

Make the fixture client parse the **exact keys the production client uses**:

- `headRef` → `headRefName`
- `author` handled as either a `{"login": ...}` dict (gh real output) or a
  plain string (lenient fallback), mirroring `GhCliClient`.

Document the convention in `docs/copilot-readiness.md`:
> PR items under `"openClosingPRs"` use the same JSON keys as `gh pr list`
> (e.g., `headRefName`, author as `{ "login": ... }`).

## Prevention

- **A fixture that mimics an external CLI must be a verbatim mirror of that
  CLI's wire format** — copy real output, do not hand-craft "nicer" keys.
- When two clients (live + fixture) share a record shape, add a test that
  feeds a realistic sample of the live format through the fixture path; an
  empty fixture array is a silent schema-drift trap.
- When adding a fixture field, grep the production client for the exact key
  name it reads — divergence is a P3-latent bug until copied data exposes it.
- Positive validator fixtures must avoid placeholder evidence once validation
  tightens (real contract data, not exemplars).

## Related

- [Positive validator fixtures must avoid placeholder evidence once validation tightens](.cg-docs/solutions/testing-patterns/2026-07-24-positive-validator-fixtures-must-avoid-placeholder-evidence.md)
- [Typed-invalid gh CLI JSON payloads must map to the API-error exit code](.cg-docs/solutions/bugs/2026-08-10-typed-invalid-gh-cli-payloads-crash-exit-code-contract.md)
- Contract documentation: `docs/copilot-readiness.md` (fixture paragraph)
- Review: `.cg-docs/reviews/2026-08-05-copilot-issue-implementation-pipeline-v2-review.md`
