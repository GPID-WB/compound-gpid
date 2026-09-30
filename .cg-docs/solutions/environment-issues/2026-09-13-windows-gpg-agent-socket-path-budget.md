---
date: 2026-09-13
title: "Windows bundled GPG tests need a short private agent socket path"
category: "environment-issues"
language: "Python"
tags: [windows, gnupg, msys, tempfile, release-gates]
root-cause: "A nested test TEMP root made the controller's private GPG agent extra socket path too long for the bundled MSYS GPG"
severity: "P1"
plan: ".cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md"
---

# Windows GPG Agent Socket Path Budget

## Problem

The Phase 7 full package gate reported 993 passes and one failure in
`test_signing.py::test_signed_object_and_wrong_key_are_verified`. Secret-key
import in the controller's private signing home failed with GPG exit 2.
The original quiet traceback did not retain raw GPG stderr. It did not establish
a signing-code defect or the underlying cause.

## Root Cause

Fresh controlled reproductions used Git for Windows' bundled MSYS GnuPG
`2.4.7-unknown`. The fixture home uses `cg-key-<random>`, but the controller creates
a longer `cg-release-sign-<random>/gnupg` home. Public-key import could succeed
while the agent could not create its extra socket for secret-key operations.

The daemon reported `socket name .../gnupg/S.gpg-agent.extra is too long` for a
110-byte MSYS socket path under the nested test root. A browser-socket length of
112 bytes was calculated, not separately observed to fail. This is evidence for
this host and bundled GPG, not a universal Windows path threshold.

## Solution

Allocate one fresh private root directly under the approved short temporary
parent. Set only the test child's `TEMP` and `TMP` to that root, before the child
starts. Do not append a `package` directory. A short pytest `--basetemp` alone
does not set the controller's separate temporary GPG home.

The verified allocation pattern was:

```python
short_root = tempfile.mkdtemp(prefix="", dir=approved_kilo_temp_parent)
child_env["TEMP"] = short_root
child_env["TMP"] = short_root
```

Here `approved_kilo_temp_parent` means an existing, explicitly approved parent,
not an arbitrary shared keyring. The successful roots were 52 native path bytes;
the corresponding extra/browser socket lengths were calculated as 101/103 bytes.
The saved repair record contains exact paths and commands. Do not reuse old roots
or infer that a fixed length is sufficient on another GPG build or host.

No product file, test assertion, cryptographic check, global environment setting,
or host protection changed. The existing test still verifies the signature and
rejects the wrong fingerprint. Shared keyrings and prior roots were not deleted.

### Verified Evidence

The [GPG repair record](../../work-reports/release-controller/2026-09-13-phase7-gpg-repair-evidence.json)
preserves two deliberate long-path failures, one short-path diagnostic pass,
and two uninstrumented signing-suite passes of eight cases each. These are eight
unique cases, not seventeen unique passes. The observer was absent from both
final targeted runs.

The initial `gpg-agent --server` probe exited 0 but did not exercise daemon socket
creation. The later `--daemon --no-detach` probe established the socket error.
The cause was reproduced; it was not recovered from missing original stderr.

The [Phase 7 final record](../../work-reports/release-controller/2026-09-13-phase7-final-evidence.json)
then records a replacement complete package pass of 994 cases on unchanged
product content, combined with seven unchanged passing gates. The earlier 7/8
run remains failed history. The later
[step 9 gate](../../work-reports/release-controller/2026-09-13-step9-validation-180003Z-86e3cad4/handoff.json)
used a fresh direct short root and passed all 995 cases in a clean default
environment. The targeted diagnosis alone was not full-package acceptance.

## Prevention

- Budget the complete private-home plus socket path, not only the pytest root.
- Diagnose with fixture-owned stderr and the operation that creates the failing
  resource. A successful server-mode probe is not daemon-socket proof.
- Retain failed runs, controlled reproductions, exact environment treatment and
  source identity. Rerun the unchanged cryptographic assertions without observers.
- Isolate keys, Git configuration, token variables and temporary roots in child
  processes. Do not log key bytes, use shared keyrings, or relax production error
  redaction to diagnose a fixture.
- Treat cleanup as a separate result. Passing signing tests do not prove old-root
  cleanup, descendant-process completion, native Unix support, or live signing.

## Related

- [Clean default dependencies and fixture controls](../testing-patterns/2026-09-13-clean-default-release-gates-and-executable-fixtures.md)
- [Controller evidence limits and deferred rollout](../git-workflows/2026-09-13-release-controller-authority-and-evidence-boundaries.md)
