---
date: 2026-09-12
type: verification
depth: full
status: changes-required
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-verification.md
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
validation: .cg-docs/work-reports/release-controller/2026-09-12-phase6-repair2-correction3-validation-215912Z.json
phase: 6
phase-complete: false
coverage:
  requested-repairs: 23
  confirmed-repairs: 22
  remaining-open: 1
  new-findings: 0
  unverified-repairs: 0
  prior-confirmed-preserved: 19
  total-confirmed: 41
findings:
  P0.1: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P1.13: fixed
  P1.14: fixed
  P1.15: open
  P1.16: fixed
  P1.17: fixed
  P1.18: fixed
  P1.19: fixed
  P1.20: fixed
  P1.22: fixed
  P1.23: fixed
  P1.24: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P2.11: fixed
  P2.12: fixed
  P2.13: fixed
  P2.14: fixed
  P2.15: fixed
  P2.16: fixed
  P3.1: fixed
  P3.2: fixed
---

# Phase 6 Repair 2 Independent Verification

**Verdict: Changes required.** All 23 repair candidates were assessed through the requested full 10-spec route. **22 repairs are confirmed; P1.15 remains open; there are no new finding IDs.** The 19 earlier confirmations are preserved. The resulting assessment is **41 confirmed and 1 open**, with active severity **P0: 0, P1: 1, P2: 0, P3: 0**. No finding was skipped, suppressed, or accepted as an exception.

`fixed` in this separate report means that the scoped implementation repair is confirmed by the stated source and local evidence. It does not mean that a live release, supported-host qualification, committed-candidate gate, Phase 6, or V6 has passed. Original finding maps, handoff/progress files, phase state, and implementation/review counters were not changed. Draft P1.21 remains absorbed by P1.13 and is not counted. P1.8 retains its prior P2 severity; P2.12 retains its prior P1 severity.

## Remaining Finding

### P1.15: Workflow Reads Still Follow Final Human Authorization

**Open residual, P1.** The repair in `packages/cg-release/src/cg_release/profile_deploy.py:43-45` correctly repeats the current-ticket and human-authority checks after `verify_run()`. The requester, resumer, and admitted recovery-principal tests now cover revocation during that worker's run read. This is a valid partial repair.

However, the actual last workflow step still executes this order at `.github/workflows/release-controller-docs.yml:251-255`:

1. Call the real `profile_worker authorize-deploy` operation.
2. Compare the local manifest digest.
3. Read the remote `dev` branch and compare its SHA.
4. Read the remote latest Release and compare its tag.
5. Run `actions/deploy-pages` without another human-authority check.

The canonical template has the same order at `packages/cg-release/templates/gpid-docs.yml:251-255`. This is not isolated generated-file drift. A requester or resumer can lose permission while either later remote read is in progress. The dev SHA and stable tag can remain unchanged, so both shell comparisons still pass. The authority result can therefore be stale at the deployment action. Read-only App credentials and the protected Pages environment do not replace the applicable human-authority requirement.

**Fresh bounded proof:** Two independent probe cases used the existing GET-only worker fixture, real `Journal`, real registration, and real `authorize_deployment()`. The current composition result was seeded in the same way as the existing deployment-gate boundary test. Each case first obtained authorization. The probe extracted the exact trailing remote endpoints from the current workflow and executed that read sequence through `GitHubReads` with only an outer fake GET transport. During `releases/latest`, the transport revoked requester `456` or resumer `8`, while returning the expected stable tag. Both freshness values still matched. Journal bytes remained unchanged. A negative control called the real authorization function again and rejected the revoked principal in both cases.

The probe file is `C:/Users/wb384996/AppData/Local/Temp/3/kilo/test_phase6_repair2_independent.py`; its two counterexample assertions passed. It is outside the source worktree. The proof executes the real worker and trailing provider-read sequence, not the complete Bash step or a Pages action. It does not claim an actual unauthorized deployment. The current workflow and template supply the missing connection to deployment.

**Required correction:** Complete the remote freshness reads before the final `authorize-deploy` call, or include them within the trusted operation before its final ticket/authority check. Keep the manifest, current-dev, stable-selection, and protected-environment guards. Correct the canonical template and regenerate the installation. Add workflow-boundary revocation cases after the last external freshness read, not only inside the Python worker. Do not execute a live deployment to test this repair.

This is the same stale-authorization defect as P1.15 at a later connected boundary. It is not counted again as a new ID.

## Repair Coverage

Package paths in this table are relative to `packages/cg-release/src/cg_release/`; package tests are under `packages/cg-release/tests/`. **Fresh** means executed in this review. **Retained** means inspected source/tests plus the final correction-3 validation, not a test rerun by this reviewer.

| ID | Result | Current Evidence And Limits |
|---|---|---|
| P0.1 | Confirmed | `.github/workflows/release-docs.yml:11-87` places release and mutable dev execution in separate unprivileged jobs. `release-pages.yml:71-101,176-212` verifies separate archive identities, imports static data, and composes with protected code. `scripts/assemble-docs-site.js:288-295` binds combined stable bytes to the independently supplied release docs. Fresh Node execution includes the self-consistent contamination rejection at `scripts/tests/assemble-docs-site.test.js:208-226`. The old shared-workspace attack is closed; actual GitHub artifact-service and deployment qualification remain external. |
| P1.2 | Confirmed | `profile_native.py:67-119` resolves runtime plus explicit `dev`/`gpid-native` dependency closure, applies markers, and requires exact package equality. `:122-167` checks platform, Python minor, lock, and registered run. `profile_build_verify.py:38-47` connects this to approval. The installed workflow uses `--no-default-groups --group dev --group gpid-native` at `release-controller-build.yml:126`, matching the installer. Fresh missing/substitution/platform-extra tests passed; the retained clean-venv test passes its actual builder receipt to the verifier. Native Linux execution was not performed here. |
| P1.5 | Confirmed | `scripts/snapshot-data.js:10-16` now serializes fixed fields and lexical ASCII file keys directly, without JavaScript integer-key enumeration or entry-array comparison. It agrees with `profile_snapshot.py:112-126`. Fresh installed exporter -> Python verifier -> installed importer tests preserve exact bytes for `0` and for `a`/`a+b`. |
| P1.6 | Confirmed | `profile_selection.py:177-190` retains actual envelope size. `deployment_capacity()` at `:202-208` checks the whole selection; `profile_build_verify.py:70-74` adds the candidate before the check. The fresh 13-envelope count test rejects the over-limit selection without allocating half a GiB. Single-envelope and decoded deployment limits remain distinct. |
| P1.7 | Confirmed | `hook_authority.py:13-38,111-123` seals original required hooks separately and retains original ticket evidence. `build_stage.py:35-43` rejects profile removal before a replacement ticket. Fresh admitted-grant tests include interruption after tag creation but before the first receipt, then reject a generic replacement build without publication effects. |
| P1.8 | Confirmed, prior P2 residual | `scripts/release-payloads.js:17-20,32` uses fatal UTF-8 decoding and compares original buffers. Fresh complete-loader tests reject distinct malformed bytes and equal JSON with different original bytes, without rewriting payloads. Full SemVer filename support remains. |
| P1.10 | Confirmed | `create-release.ps1:672-695` retains `-RequireRecoveryRecord:$historicalDeployment` through the last authority call and compares exact default revision, branch, actor, and historical record before attestation. Retained full Pester evidence includes the withdrawal-after-artifact case at `tests/create-release.Tests.ps1:676-681`. No Pester or actual attestation effect ran in this review. |
| P1.11 | Confirmed | `bridge_client.py:47-114` checks the normalized Git/index identity separately from the declared LF/CRLF checkout transform and rejects source-defined filters/encoding/ident transforms. The fixture now copies the real `.gitattributes` at `test_bridge_client_roundtrip.py:33`. Fresh local-only qualification uses real Git, full helpers, managed refresh, and strict receipt verification. It is not delivered bridge or opposite-host qualification. |
| P1.13 | Confirmed | `profile_dispatch.py:83-85` reuses immutable absence evidence only after fresh discovery and authority validation. Fresh connected tests cover re-entry after the absence checkpoint, repeated exhausted-budget reconciliation, later dev advancement, and preservation of old record bytes. |
| P1.15 | Open, P1 | Worker-level final-run revocation is repaired, but template/installed workflow freshness reads still follow authorization. See the remaining finding and two fresh counterexamples above. |
| P1.17 | Confirmed | `release-legacy-authority.ps1:99-142` binds the exact protected default/ref, run attempt, successful deploy job and named step, and one successful deployment status with that job's log identity. `create-release.ps1:685` calls it before the final historical-grant check. Retained Pester cases reject non-default/all-skipped wrappers, skipped jobs, missing successful deployment results, and artifact substitution. Real GitHub/Pages wire qualification remains external. |
| P1.19 | Confirmed | `bridge_client.py:184-218` keeps isolated Git configuration and adds an exact-repository HTTP authorization header through the child environment, not argv; redirects are disabled. Fresh fake-token tests cover both variable names, absent/empty/malformed credentials, wrong host/repository/path, and redacted process failure. Fresh full local qualification restricts Git to file transport after intercepting only the approved clone. The real workflow token has read-only permissions. No real credential or private HTTPS operation was used. |
| P1.20 | Confirmed | `scripts/generate-whats-new.js:203-206` derives the older-history URL from the same validated repository identity as payload validation. Fresh complete-loader/render tests pass the configured `owner/repo` boundary at both 20 and 21 releases. |
| P1.22 | Confirmed | `profile_docs.py:31-36,57-73` uses the applicable admitted grant for old-policy reconciliation rather than rejecting before terminal discovery. The immutable predecessor remains. Fresh actual-admission test replaces a terminal old-policy composition with the current maintainer after revoking the old actor; publication receipt bytes remain unchanged. |
| P1.23 | Confirmed | `stranded_recovery.py:131-149` requires an explicit reviewed protected evidence base for exceptional GPID admission. `profile_evidence_inputs.py:19-71` seals a separate grant-bound attempt; `profile_evidence.py:41-48,80-148` uses its base/nonce/time and preserves prior PR/evidence. `scripts/release_profile_gpid.py:176-199` uses reviewed recovery provenance without inventing a preparation PR. Fresh tests cover deleted source, existing evidence and replay, and a fresh target journal that admits an existing tag and reaches build/publication/docs/evidence completion without an inbox receipt or preparation PR. Only immutable source/tag data is copied into that target fixture. |
| P1.24 | Confirmed | `profile_worker.py:25-55,71-100` retains one exact `Composition` through registration. `composition_journal.py:103-107` requires the registration digest to match that record's immutable ticket. Fresh storage-read interleaving rejects the old worker and leaves the successor unregistered. |
| P2.5 | Confirmed | `test_profile_evidence_lifecycle.py:16-108` provides eight independent evidence failures after valid deployed docs, with real verifiers, unchanged receipt, and no extra publication effects. All eight passed fresh. The positive lifecycle at `test_profile_lifecycle.py:157-176` compares all nine exact canonical/native/ownership outputs; it also passed in the retained 853-test package gate. |
| P2.6 | Confirmed | `scripts/tests/release_shell_fixture.py:114-123,159-161` adds the selected Bash to isolated PATH, so the actual launcher can resolve its `/usr/bin/env bash` shebang. The real launcher/argv/exit fixture remains. Retained launcher validation passes; this review does not claim native Unix execution. |
| P2.10 | Confirmed | `profile_evidence.py:22-36` documents callback arguments, trusted origin, actor provenance, pending versus verified results, writes, and failures. `profile_worker.py:204-218` documents per-operation inputs, credential channel, `EXPECTED_MANIFEST`, outputs, exits, and effects. These contracts were checked against the functions and workflow. |
| P2.12 | Confirmed, prior P1 residual | `profile_selection.py:209-235` builds the full candidate-inclusive destination graph, including stable-root duplication, and validates aliases/parents before approval. `profile_build_verify.py:70-74` uses it. The fresh `rc.A`/`rc.a` regression rejects the selection before publication; installed Node retains its pre-copy guard. |
| P2.14 | Confirmed | `scripts/update.sh:75` uses a common prefix to force string comparison, without changing lexical prefix order. Seven fresh actual Git Bash reader cases passed, including all four strict-prefix pairs and both adjacent huge-number cases. Git Bash is not native Unix evidence. |
| P2.15 | Confirmed | `.github/prompts/cg-release.prompt.md:463-465` and all four generated command copies now name the verified protected remote default revision, not assumed `main`. The separate legacy source-branch rules remain. Current source snippets and retained canonical-generation/parity evidence agree. |
| P2.16 | Confirmed with cost limit | `github_journal.py:105-139` reads the complete head tree once, reconstructs every historical tree from verified event deltas, compares each canonical OID, and checks the exact final inventory. `journal_tree.py:51-95` reports entry updates and hash bytes. `composition_journal.py:182-185` reuses its authenticated operation-local event view. Fresh 8/16/32-event cold-reader tests and real `git mktree`/hidden historical corruption tests passed. Flat-directory hashing remains cumulative, not linear; see the cost assessment below. |

## Ten-Spec Completion

All ten `.kilo/agents/` specs were read and applied in the requested order, sequentially in this independent session. No new Agent Manager session or internal reviewer session was created. Independent file reads and local test calls did not make the review analyses parallel.

| Order | Spec | Completed Scope And Result |
|---|---|---|
| 1 | cg-code-quality | Absence replay, immutable composition transitions, retry sequencing, errors, and module bounds. Repair code remains within the existing package module gate; no separate quality finding. |
| 2 | cg-testing | Eight valid-docs/evidence-failure cases, all-nine-byte success assertion, real transport boundaries, source-only fixtures, launcher Bash resolution, and host qualifications. P2.5/P2.6 confirmed. |
| 3 | cg-documentation | Evidence/worker public behavior contracts, legacy command examples, default-ref terminology, and canonical/generated copies. P2.10/P2.15 confirmed; Phase 7 documentation was excluded. |
| 4 | cg-version-control | Separate producer jobs, protected composer, Finalize authority/deployment binding, read-only Git history, ignore rules, and historical payload/attestation preservation. No new version-control finding. |
| 5 | cg-reproducibility | Exact native dependency closure, interpreter/platform binding, clean-environment test connection, source workflow provisioning, bundled resources, real checkout attributes, and immutable fixtures. P1.2 confirmed; external host evidence remains separate. |
| 6 | cg-performance | Cold history reconstruction, retained signatures/parents/tree identities, bounded operation-local reuse, envelope capacity, and absence/retry behavior. P2.16 confirmed with disclosed cumulative hashing. |
| 7 | cg-architecture | Original required-hook seal, pre-receipt recovery, admitted old-policy replacement, explicit recovered evidence attempts, generic-mode separation, and exact nine-file projection. P1.7/P1.22/P1.23 confirmed. |
| 8 | cg-data-quality | Actual export/approval/import identity, strict UTF-8 and buffer equality, marker-selected package closure, complete encoded/decoded capacity, and destination graph. P1.5/P1.6/P1.8/P2.12 confirmed. |
| 9 | cg-learnings-researcher | Exact artifact/byte authority, real boundary fixtures, complete loader/render behavior, and immutable historical knowledge. P1.20/P2.14 confirmed; no new learning-derived finding. |
| 10 | cg-adversarial | Current human authority after delayed reads, registration interleaving, local/private bridge transport contract, installed resource boundary, and connected workflow/template order. P1.15 remains open; no new ID. |

R, Stata, survey estimation, and research-method checks do not apply to this tool change. They are not omitted review specs.

## Earlier Confirmations

The following 19 prior confirmations are retained, not relabeled as 19 newly executed proofs:

| Prior IDs | Preservation And Adjacent Checks |
|---|---|
| P1.1, P1.9 | The actual provider-backed dual-tree durable-payload union remains in `profile_source.py:23-75`. Recovery/evidence changes do not remove source/default historical obligations. |
| P1.3 | `profile_process.py:19-66,79-144` retains installed RECORD, containment, finite deadline, bounded output, and credential-free fixed Node execution. Fresh connected snapshot/recovery tests use wheel-bundled resources. |
| P1.4, P1.14 | Strict retry policy and separate bounded composition records remain. Fresh absence/exhausted-budget tests and registration interleaving pass; journal delta replay does not truncate evidence or raise bounds. |
| P1.12 | Highest adopted stable and first-pre-release checks remain in `profile_selection.py:77-102,243-274`, separate from repaired candidate capacity. |
| P1.16 | `profile_attestations.py:34-143` still seals exact canonical, four native, and four ownership outputs. Recovery attempts use that same projection; valid-docs negative evidence tests pass. |
| P1.18 | Legacy authority still resolves the actual protected remote default and current actor. The fresh Node helper tests cover a default named `production`, cutover, actor revocation, and artifact identity. |
| P2.1 | Fresh unchanged module-bounds test passed. `build_stage.py` and `bridge_client.py` are each 300 lines; no bound was raised. |
| P2.2, P2.4, P2.13 | Retained final prepare evidence includes native selectors, all three real module validators, the separately owned package gate, and profile/launcher gate. Native/profile versus six-cell ownership is still explicit. |
| P2.3 | Effective workflow assertions remain in the canonical Pester suite; the final unfiltered result includes all 24 docs-automation and 10 docs-preview assertions. Old combined-producer assumptions were not restored. |
| P2.7 | `hatch_build.py:27-68` still gives complete bundled sdist resources priority and fails incomplete/unverified source layouts. Fresh connected tests build their wheel only in test scratch. |
| P2.8, P3.2 | `.gitattributes:19-21` retains frozen-reader `-text` rules. Fresh bridge qualification checks the frozen source hashes before using the complete helper fixture. These fixtures do not establish real delivery. |
| P2.9 | Explicit `LegacyOperation` examples remain in canonical/generated commands and in actual Finalize/Reserve code. |
| P2.11 | `profile_selection.py:116-173` retains one fresh tag/Release inventory per acquisition and verifies selected bytes before use. No new cross-command authority cache was introduced. |
| P3.1 | `hooks.py:32-105,130-154` retains explicit profile protocol methods and strict raw result decoding. Generic mode does not import the optional profile. |

## Local Evidence

The handoff and repair2 progress files both describe the 21:45:37Z source freeze but still say a complete rerun is required. The later **22:28:29Z correction-3 validation** supplies the completed rerun and takes precedence for test status. Earlier failures remain historical evidence; they were not deleted or renamed as passes.

| Retained Gate | Final Result | Qualification |
|---|---|---|
| Prepare | 9 selected, 9 executed, 9 passed, 0 failed, 0 unexecuted | Actual prepare mode with `--full-gate --run-native-target`; not committed-candidate mode. |
| Package | 853 passed, 0 failed/errors/skipped | Complete summary and return code also read at `2026-09-12-phase6-repair2-correction3-prepare-readable-215912Z.json:335-352`. |
| Native | 2,592 passed, 0 failed, 50 skipped, 2 deselected | Exact skip names/reasons are not available from that `-q` result. |
| Profile/Launcher | 28 passed, 0 failed/skipped | Complete command result also read at the readable prepare file, lines 353-370. |
| Ordinary Node | 106 passed, 0 failed/skipped | Windows EPERM uses the explicit portable file-link Dirent boundary, not real Windows symlink creation. |
| Plan/Parity | 56 passed, 0 failed, 8 skipped | Named skip groups are POSIX-only cases unavailable on this Windows host. |
| Pester | 2,935 passed, 0 failed, 2 skipped; `filteredFiles: null` | `tests/last-run.json` still matches 21:59:12Z. TestDrive cleanup errors remain; both skips belong to update, but individual names/reasons are absent from `skipped[]`. |
| Lint/Build | Ruff and wheel/sdist build passed | Retained gate evidence; no separate source-tree build was run by this reviewer. |

This review ran these additional bounded checks with the existing package interpreter, `-B`, `-p no:cacheprovider`, and distinct scratch directories under `C:/Users/wb384996/AppData/Local/Temp/3/kilo/`:

| Fresh Selection | Result |
|---|---|
| Native receipt negatives, cold journal work, journal tree identities/corruption, module bounds | 15 passed, 1 deselected; 1.62 seconds. The clean native-environment case was not rerun in this selection. |
| Actual Bash reader corpus | 7 passed, 24 deselected; 2.30 seconds. |
| `test_profile_security.py` plus fake credential boundary tests | 21 passed, 2 deselected; 1.93 seconds. The two distribution-dependent bridge cases were excluded from this selection only. |
| Independent trailing-workflow-read counterexamples | 2 passed; 0.91 seconds. These assert the remaining defect and its negative controls, not a safe deployment. |
| Evidence failures, admitted policy/source recovery, fresh stranded lifecycle, installed snapshot roundtrip/capacity, absence-checkpoint re-entry | 21 passed; 218.18 seconds. Tests use real controller/provider/journal code with fake outer transport and local scratch. |
| `test_bridge_qualification.py` | 14 passed; 34.80 seconds. Actual local Git/helper/qualifier and strict receipt paths; the fixture intercepts the approved HTTPS clone, then limits Git subprocesses to file transport. |
| Node `generate-whats-new.test.js`, `assemble-docs-site.test.js`, `legacy-pages.test.js` | Exit 0. Dot reporter was used; no case count is inferred from progress glyphs. Includes actual complete-loader/render and stable-contamination regression execution. |
| Protected history and whitespace | `git diff --exit-code -- releases .github/shared/skill-management/release-attestations` was empty. `git diff --check` passed with existing LF/CRLF checkout advisories. |

Counts overlap with the full retained suites and are not added as unique coverage. No Pester command was run by this reviewer. There was no real `gh` invocation, credential lookup, private clone, remote Git operation, release, PR, deployment, or settings operation. Test fixtures supplied only synthetic credentials where required.

### Cold Replay Cost

The retained before/after measurements at 8, 16, and 32 events change provider calls from **27/51/99** to **20/36/68**, processed tree entries from **108/408/1,584** to **24/48/96**, and decoded bytes from **37,578/105,338/332,834** to **23,599/46,643/92,739**. Fresh tests confirm the new provider-call bound and exact processed-entry counts, plus canonical Git tree identity and rejection of transient historical corruption.

The new hash-byte measurements are **9,388/33,944/128,560**. The fixed flat-directory Git format still requires cumulative hashing; this review does not call the whole cold replay linear or claim a measured deadline guarantee. P2.16 is confirmed for removal of repeated cumulative tree acquisition/materialization and reuse of the authenticated operation-local view. Signatures, parents, root, every event, every historical tree identity, and final full-tree equality remain required.

## Scope And Preservation

The review used current tracked changes and untracked Phase 6 implementation, tests, workflows, templates, and evidence. It did not rely on `git diff` alone: the new package and many integration files are untracked. Build outputs, virtual environments, caches, generated view bodies, and future Phase 7 scope were excluded from code review. Installed scratch resources were used only as local verification inputs. Canonical/generated interactions were checked in the release command copies, profile installation/template, optional wheel resources, and nine-file evidence projection.

Base HEAD remains `b94f585c8a485dfb03965ca9711fb83257aaa7de` on `improve-cg-release`; the reviewed candidate is uncommitted. The earlier gate's freeze is a handoff declaration, not a cryptographic identity for all dirty contents. This review also does not claim a complete before/after source fingerprint. The only manual worktree write by this reviewer is this distinct report; a small independent probe was written outside the workspace. No source/test repairs, canonical regeneration, historical rewrites, phase changes, commits, pushes, or PRs were performed.

The review loaded project instructions, applicable Python/PowerShell guidance, review/context contracts, plan documentation-provenance and recovery requirements, and all ten reviewer specs. Local Brain retrieval supplied exact-artifact, immutable-tag, and cross-platform-boundary lessons, including `.cg-docs/solutions/git-workflows/2026-08-13-verified-pages-artifact-and-release-tag-gates.md`. Its old main-only topology is superseded by the approved September 11 plan. No open-brain service tool was available; bounded local Brain and saved project context were used. No memory write was requested or performed.

## Phase Boundary

P1.15 requires a source repair and another scoped independent verification before this review can be clean. The new controller remains disabled; `.release-controller.json` still has unresolved real authority identities. This report does not close Phase 6, mark V6/external-V6-only completion, reset any counter, or start Phase 7.

Remaining external evidence is unchanged: native Unix/Python 3.8 execution, real supported-host file-symlink qualification, authorized delivered bridge and clean-client proof, exact source-bound six-cell CI and both registered producer identities, a reviewed committed-candidate gate, and real bootstrap/App/controller/journal/protected-setting authority. Local test success does not replace these requirements.

For the next repair/verification step, the appropriate capability is release-security engineering with high-effort independent boundary testing. This is capability advice only; the user controls model and effort selection.
