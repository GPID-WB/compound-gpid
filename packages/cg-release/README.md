# cg-release

A standalone Python release controller for GitHub repositories. It has four
commands: `plan`, `start`, `status`, and `resume`. Generic operation does not need
Compound GPID, a charter, Node, PowerShell, or an AI session in the target project.
Git and the authenticated GitHub CLI (`gh`) are required. Python 3.11 or later is
required for this package only; the existing GPID tools keep their own minimum.

## Delivery Status

The publisher remains disabled in the supplied installation. Local fixtures test
the protocol; they do not prove remote setup, approval, publication, or latency.
Bridge delivery, native clean-client qualification, registered release-mode CI,
sandbox security trials and live performance proof are **deferred, not passed**.
Ordinary PR CI and the later authorized committed-input gate remain required.
No package registry publication or global installation is part of this delivery.

## Install Locally

From the controller source checkout, with `uv` installed:

```text
uv sync --project packages/cg-release --locked --python 3.12
uv run --project packages/cg-release cg-release --help
uv build --project packages/cg-release
```

For a source-free installation, use a new virtual environment. Replace `PYTHON`
with its actual interpreter (`.venv/Scripts/python.exe` on Windows or
`.venv/bin/python` on Unix). Replace `WHEEL` with the reviewed wheel path. These
uppercase values are placeholders, not commands to run unchanged.

```text
uv venv --python 3.12 .venv
uv export --project packages/cg-release --locked --no-dev --no-emit-project --output-file requirements.txt
uv pip install --python PYTHON --link-mode copy --require-hashes -r requirements.txt
uv pip install --python PYTHON --link-mode copy --no-deps WHEEL
```

The export and wheel come from the same reviewed controller revision. Retain and
check the wheel SHA-256. Use `--link-mode copy`: the optional GPID profile verifies
installed resource digests and rejects mutable hardlink aliases. The installed
CLI can run from a different generic checkout without this source tree. Package
tests build an sdist and wheel, install locked dependencies, and test that case.
Do not run the source checkout's editable install as a privileged production pin.

## Four Commands

These syntax examples require a separately reviewed target setup before remote
use. `REQUEST_ID` means the complete retained `rc1.` locator, not this literal
word. Tests parse all four examples and execute preview against an offline fixture.

<!-- cg-release:examples -->
```text
cg-release plan --version 1.0.0 --branch main --line current --json
cg-release start --version 1.0.0 --branch main --line current --yes --json
cg-release status REQUEST_ID --json
cg-release resume REQUEST_ID --json
```

`plan` is read-only and does not reserve a version. `start` needs no prior plan:
it recomputes, displays, confirms and rechecks the exact proposal. `--yes` replaces
CLI confirmation only, never remote approval. `--bump` and `--version` are mutually
exclusive. Use `--channel rc` only with an automatic bump; explicit versions must
already contain their suffix. Use `--sign` to require an allowlisted signing key.

JSON output is JSON Lines, not one JSON document. Retain `submission-intent` and
its provisional locator before the first write. Only the read-back verified
`receipt` means durable queued submission, not admission or publication. Exit 0
means the command completed, not that a release is complete. Controller errors
return exit 2 with a structured code and safe next action. Logs use stderr.

On a second machine, use `status` with the same locator; a local checkout or issue
number is not needed for locator discovery. `resume` checks fresh authority and
dispatches reconciliation after discovery. An unresolved locator stays unknown;
do not repeat `start`. `status --watch --timeout 10m` stops observing on timeout or
Ctrl+C without cancelling the request.

## Setup and Recovery

The [operator guide](../../docs/release-controller.md) describes the reviewed
setup PR, exact policy and controller pins, App/environment/ruleset requirements,
version lines, metadata projections, backup/restore, and deferred trial procedure.
`templates/policy.example.json` contains synthetic IDs and digests; it is not
usable authority. Workflow examples have explicit false guards. They must not
be enabled by a copy-and-run installation recipe.

Published tag objects and asset bytes are immutable. A missing Release after a
matching tag is a recovery case, not permission to delete or retag. Expired
pre-publication assets need a new exact-input build and fresh approval. Preserve
the journal and all evidence; a missing journal is not restored from chat.

## Local Checks

```text
uv run --project packages/cg-release pytest packages/cg-release/tests -q
uv run --project packages/cg-release ruff check packages/cg-release
uv run --project packages/cg-release python scripts/benchmark_release.py --offline
```

The last command measures local Git preparation only. It performs no remote
trial and reports missing remote stage timings as null. The operator guide lists
offline sandbox planning and supplied-measurement checks. Neither path can
establish the ten-sample p95 <=120-second live handoff target or a speedup.
