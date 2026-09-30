---
date: 2026-09-12
type: verification
depth: full
status: changes-required
parent-review: .cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-review.md
plan: .cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md
evidence: .cg-docs/work-reports/release-controller/2026-09-12-phase6-verification-evidence.json
phase: 6
phase-complete: false
findings:
  P0.1: open
  P1.1: fixed
  P1.2: open
  P1.3: fixed
  P1.4: fixed
  P1.5: open
  P1.6: open
  P1.7: open
  P1.8: open
  P1.9: fixed
  P1.10: open
  P1.11: open
  P1.12: fixed
  P1.13: open
  P1.14: fixed
  P1.15: open
  P1.16: fixed
  P1.17: open
  P1.18: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: open
  P2.6: open
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: open
  P2.11: fixed
  P2.12: open
  P2.13: fixed
  P3.1: fixed
  P3.2: fixed
  P1.19: open
  P1.20: open
  P1.22: open
  P1.23: open
  P1.24: open
  P2.14: open
  P2.15: open
  P2.16: open
---

# Phase 6 Independent Verification

**Verdict: Changes required.** All ten independent review analyses and evidence handoffs are complete. Of the 34 original findings, **19 are verified, 15 are reopened, and 0 are unverified**. There are **8 additional findings**. Active severity counts are **P0: 1, P1: 15, P2: 7, P3: 0**, for **23 open findings**. No finding was skipped or suppressed, and no exception was accepted. Verification completion is not Phase 6, V6, or external-V6-only completion.

The draft ID P1.21 was merged into reopened P1.13 after two reviewers reproduced the same absence-replay defect. It is not counted twice. Architecture/performance policy-recovery evidence and data/performance aggregate-capacity evidence are also counted once each. The original report and its labels remain unchanged as required.

The review used the source frozen after the supplemental Bash correction and actual canonical generation. Base HEAD is `b94f585c8a485dfb03965ca9711fb83257aaa7de`; the candidate remains uncommitted. All original `fixed` labels were treated as implementation and offline-evidence claims, not verification proof.

This is the explicitly requested **full 10-spec route**, not the light-only verification shortcut. No repair, accepted exception, suppressed finding, live operation, or Phase 7 work was performed. Only this report and its companion JSON are authorized review writes. Original review, work report, plan, active state, source and tests remain outside the write scope.

## Findings

Package-source references below use `packages/cg-release/src/cg_release/`. Test names and exact proof inputs are also indexed in the companion JSON. Current severity is stated independently of the preserved original ID: P1.8 has a P2 residual; P2.12 has a P1 residual.

### P0.1: Mutable Dev Can Change Stable Output

**Reopened, P0.** `.github/workflows/release-docs.yml:48-75` still runs tagged and mutable `dev` builders in one runner/workspace. Dev code can change stable output or the combined artifact after source checks. The privileged path at `.github/workflows/release-pages.yml:158-181` uploads that combined `site`.

`scripts/assemble-docs-site.js:244-290` compares output with its own digest inventory and compares source fingerprints separately. It does not bind stable output bytes to a producer isolated from mutable dev code. A bounded in-memory probe used the real fingerprint and verifier functions: unchanged stable source said `REVIEWED STABLE`, output said `ATTACKER STABLE CONTENT`, and the complete self-consistent artifact was accepted with result `0`.

**Required correction:** Isolate stable/release production from mutable dev execution. Compose separately verified artifacts with trusted code. Test stable-output contamination through the actual producer/verifier boundary. Removing direct Pages/OIDC authority from `pages.yml` is a valid partial repair, not closure of this other path. No live deployment or credential compromise was attempted.

### P1.2: Native Receipt Accepts Incomplete Dependencies

**Reopened, P1.** The separate source interpreter is connected at `.github/workflows/release-controller-build.yml:114-133` and `scripts/release_profile_build.py:31-35,59-69`. However, `profile_native.py:64-77` accepts a subset of registry entries from the lock, provided it includes `pytest` and `pyyaml`.

The current production verifier accepted a complete 20-package Linux/Python 3.12 inventory, an inventory containing only those two packages, and a 22-package inventory with Windows-only extras. The expected 20-package closure was derived from the current lock and markers; no new environment was installed. `profile_build_verify.py:37-46` connects this weak check to approval. The lifecycle transport at `packages/cg-release/tests/profile_transport.py:251-268` supplies only two packages.

**Required correction:** Compare the complete source-selected environment, including runtime/default/native groups and platform/interpreter markers, with the sealed receipt. Connect a real clean producer receipt to the trusted approval verifier. This is not merely missing CI evidence.

### P1.5: Snapshot Inventory Ordering Differs

**Reopened, P1.** `profile_snapshot.py:124-126` uses Python lexical dictionary order. `scripts/snapshot-data.js:106-108` uses JavaScript property enumeration and default entry-array sorting. Integer-index keys and comma-joined entry comparisons change the serialized identity.

The five required files plus `0`, or plus `a` and `a+b`, produce different inventory digests across languages. Python envelopes passed Python and failed installed Node; reverse envelopes failed Python. Actual installed `buildSnapshot()` and `exportSnapshot()`, with only filesystem I/O supplied in memory, produced an 850-byte envelope containing `0` that Python approval rejected with `E_PROFILE_SNAPSHOT`.

**Required correction:** Define one canonical serialization algorithm and test the same native export bytes through Python approval and installed import. Single-snapshot path-graph repairs remain valid. The separate cross-version directory alias is counted under P2.12 only.

### P1.6: Candidate Omitted From Aggregate Envelope Limit

**Reopened, P1.** The original single-envelope mismatch is fixed: export, approval, single-asset acquisition and installed Node agree on 64 MiB. But `profile_selection.py:176-220` drops envelope length from capacity summaries, and `profile_build_verify.py:69-73` adds only the candidate's decoded summary.

A bounded count proof used 12 existing snapshots at 30 MiB decoded each. Their envelopes are just over 480 MiB and can pass acquisition. A thirteenth snapshot passes the production approval capacity check at 452 MiB decoded deployment size, including stable duplication and dev reserve. Its complete envelope selection is over 520 MiB and must later fail the 512 MiB acquisition limit at `profile_selection.py:150-155`. No large files were created.

**Required correction:** Retain verified envelope sizes and check the entire existing-plus-candidate selection against every downstream capacity before approval/publication.

### P1.7: Recovery Can Drop Original Hooks

**Reopened, P1.** `hook_authority.py:62-83` derives requirements from the build selected by the publication receipt. A policy recovery before the first receipt can rebuild using `gpid_profile=None`, then bind publication to those newer generic tickets.

The connected path is `publication_stage.py:33-53`, `publication_rebuild.py:68-88`, `build_stage.py:35-53,80-96`, `publication_inputs.py:35-57,259-273`, and `published_history.py:15-26`. A bounded probe used real ticket creation, grant-reader checks and requirement decoding and returned `old_ticket_profile=v1`, `new_ticket_profile=null`, and `hooks_from_recovery_receipt=[]`. The strict grant, build-validation, seal and receipt data were manually seeded; the probe did not admit a grant or establish an original approved GPID seal. The connected production source, not those synthetic success records, is the basis for this reopening.

**Required correction:** Seal original required hooks independently of replacement build tickets and preserve them through policy recovery. The already-published, no-grant policy-removal case is fixed. No full GPID recovery-to-complete bypass or live publication was executed; the remaining finding is a connected source path with a ticket/decoder proof.

### P1.10: Finalize Drops The Recovery Grant Requirement

**Reopened, P1.** `create-release.ps1:673` requires the reviewed historical recovery record. After later remote reads, line 687 omits `-RequireRecoveryRecord`. With an existing remote tag, `scripts/release-legacy-authority.ps1:68-90` can then accept general current maintainer authority without the withdrawn record.

A bounded PowerShell probe executed the actual Finalize region and authority helper with only I/O and attestation output replaced. Withdrawal after the first record check still produced `recordReads=1` and `stubAttestations=1`. A final-boundary negative control requiring the record rejected withdrawal.

**Required correction:** Retain the operation-specific record requirement and exact grant/evidence binding through the final attestation effect. No Pester or actual attestation write ran in this review. This withdrawal issue also affects P1.17 but is counted once here.

The downstream writer was also inspected: `create-release.ps1:339-347` calls `scripts/cg_release_attestation.py`, whose real service at `scripts/skill_management/services/release_attestation.py:211-330` validates tag/payload/provenance and immutable output bytes, not the current historical grant or Pages deployment. The attestation stub does not conceal a later check that closes P1.10 or P1.17.

### P1.11: Bridge Check Rejects Required Checkout Bytes

**Reopened, P1.** `bridge_client.py:59-66` hashes raw installed bytes as Git blobs and compares them with normalized index objects. `.gitattributes:17` requires `bin/*.cmd text eol=crlf`.

Actual read-only Git output for `bin/cg-link.cmd` was `i/lf w/crlf attr/text eol=crlf`. Its HEAD blob was `8d564d28f9b5caf766c7971425b6b35496d1b1ec`; its raw working-file blob was `e06b8b2b80f9b9bf80014f88eacf005a42b8819c`. The round-trip test distribution substitutes `* -text` at `packages/cg-release/tests/test_bridge_client_roundtrip.py:31`, so it does not exercise the delivered attribute contract.

**Required correction:** Verify canonical Git identity and declared checkout transformations separately, without executing source-defined filters. Preserve real distribution attributes in the qualification fixture. Distinct real qualification and strict remote receipt decoding now exist, but a real delivered checkout cannot satisfy this byte comparison. Private clone authentication is a separate new finding, P1.19.

### P1.15: Final Deployment Read Can Outlast Authority

**Reopened, P1.** `profile_deploy.py:25-44` checks authority before a later remote run read, then can return authorization without another requester/resumer/recovery-principal check.

The existing outer GET fixture revoked the requester during the final run read. Real registration, Journal, `GitHubReads` and deployment authorization returned `deployment_authorized_after_requester_revocation=True`, with the requester now `read` and journal unchanged. Composition evidence was seeded as in the existing gate test; this was not a full release or live deployment.

**Required correction:** After run/composition validation, check the current ticket and applicable authority immediately before returning authorization. Add final-read revocation cases for each applicable principal. Registration already repeats a check at `profile_worker.py:87`.

### P1.17: Finalize Does Not Prove Deployment

**Reopened, P1.** `create-release.ps1:662-682` accepts a successful manual workflow wrapper without verifying its default ref, successful protected deploy job/attempt, or actual deployment result. The producer at `.github/workflows/release-pages.yml:29` excludes manual dispatches outside the default ref, so run SHA alone is insufficient.

An actual Finalize-region probe accepted a supplied successful wrapper with `head_branch=non-default-at-same-sha` and the current default SHA, without any jobs or deployment API read. The proof establishes the predicate's acceptance gap, not an observed live all-skipped run. No additional assumption about GitHub's `name`/`display_title` semantics is counted as a finding.

**Required correction:** Bind the selected artifact to the intended controller ref, exact successful protected job/attempt and deployment evidence. Retain the final historical-grant check described in P1.10.

### P2.12: Candidate Version Directory Aliases

**Reopened, current severity P1.** `profile_selection.py:95-101` checks existing selections, but its capacity summary at `:190-220` omits candidate destination identities. Existing `v1.0.0` and `v1.1.0-rc.A`, followed by higher-precedence `v1.1.0-rc.a`, pass the approval capacity function. Installed Node rejects the resulting 25-file deployment graph with `Snapshot directory alias or file parent conflict`.

**Required correction:** Validate the full candidate-inclusive destination graph before approval. Retain Node's now-correct pre-copy guard. The risk is publication before an inevitable completion failure, so this residual is P1. The envelope-capacity defect is counted separately under P1.6, not duplicated here.

### P1.19: Private Bridge Clone Has No Authentication

**New, P1.** `bridge_client.py:137-153` removes `GH_*`, `GITHUB_*` and inherited Git configuration, uses a private home, disables global/system configuration and prompts, then clones by HTTPS without an authentication channel. The workflow uses `persist-credentials:false` and passes `GH_TOKEN` only to the qualifier step.

A probe intercepted the first spawn before execution and suppressed directory creation. The clone had no token, credential helper or authorization header; `GIT_CONFIG_NOSYSTEM=1` and `GIT_TERMINAL_PROMPT=0`. API validation can therefore succeed while private Git access cannot. Local clone redirection in tests does not prove private HTTPS access.

**Required correction:** Supply a repository-scoped read-only Git credential channel for the approved remote and later fetches, without URLs/logs/receipts exposing credentials. Test the transport contract. No actual private clone or network authentication request was run.

### P1.20: Configured Repository Fails At 21 Releases

**New, P1.** `scripts/generate-whats-new.js:197-205` still hard-codes `GPID-WB/compound-gpid` when building the older-history link. The validator accepts `CG_RELEASE_REPOSITORY`, supplied from the real source job at `scripts/release_profile_build.py:54`.

With `owner/repo`, the actual complete loader accepted 21 SemVer payloads. Rendering 20 succeeded; rendering 21 reached `cannot derive GitHub Releases URL from sourceUrl 'https://github.com/owner/repo/tree/v1.0.21-rc.1'`. Filesystem reads were supplied in memory; `process.exit(1)` was intercepted, not treated as the shell exit status.

**Required correction:** Use the same validated repository identity for URL validation and history-link construction, with 20/21 boundary tests. This affects opted-in GPID-profile repositories; it is not a failure of generic mode with no profile.

### P1.13: Saved Absence Cannot Be Replayed

**Reopened, P1; absorbs draft P1.21.** `profile_dispatch.py:82-92` saves an immutable `absence` result with the current timestamp. Interruption after that checkpoint and before replacement ticket creation causes the next reconciliation to save a different timestamp under the same key. `composition_journal.py:153-157` correctly rejects replacement.

The real recovery, provider, Journal and composition store over outer GET/clock and MemoryStore inputs returned `replacement_safe=True` after the second observation, then `E_HOOK Composition result cannot be replaced.` on re-entry one second later. Stored bytes remained unchanged. The code-quality probe used a validated generic fixture policy and did not run `docs_step()` or a full GPID lifecycle. Performance independently reproduced the same failure at times 1121, 1242 and 1243 for a ticket created at 1000, retaining one composition after three discovery reads.

**Required correction:** After fresh run discovery and authority validation, reuse the immutable absence proof rather than rewrite it. Cover interruption after the checkpoint, budget exhaustion there, and later dev advancement.

### P1.22: Reviewed Policy Recovery Cannot Replace Composition

**New, P1.** `profile_docs.py:52-58` rejects an old-policy composition before terminal reconciliation even when `authorize_hooks()` accepts the exact current recovery grant. Old ticket mutation is correctly prohibited at `composition_journal.py:64-70`, but no granted replacement transition exists.

A bounded probe changed only `composition_retries`, manually seeded a strict applicable recovery grant and retained terminal old-policy evidence. Fresh authorization returned actor `999`, then docs reconciliation returned `E_HOOK_POLICY: Composition policy binding changed.` with zero outer mutations. The journal read view was synthetic, not authenticated journal replay; grant admission and a full lifecycle were not executed. Performance independently confirmed the conflicting production branches. Core source-exception admission preserves the record state at `stranded_recovery.py:227-243`; it does not remove the immutable composition predecessor.

**Required correction:** Under the exact grant, reconcile the old run or bounded absence, preserve its immutable ticket, and seal a new ticket. Include replacement of a revoked old actor. Do not remove policy/actor checks or rewrite old evidence.

### P1.23: Evidence Hook Assumes Ordinary Recovery Shape

**New, P1; static connected-path finding.** Core source exceptions admit a deleted source branch at `stranded_recovery.py:101-105`, but `profile_evidence.py:32-35` reads that branch directly and uses ordinary lineage checks. Core stranded-publication admission at `stranded_recovery.py:191-203` also creates records without an inbox receipt or preparation PR number; `scripts/release_profile_gpid.py:196` and `profile_evidence.py:126,145` require those fields.

**Required correction:** Define an explicit reviewed evidence-PR base and provenance contract for recovered GPID records. Use the admitted recovery authority rather than inventing an original PR, receipt, or fallback branch. Keep release identities immutable. The generic deleted-source recovery test is not GPID evidence-hook coverage; no full recovered GPID lifecycle was executed here.

### P1.24: Late Registration Can Attach To A Successor

**New, P1.** `profile_worker.py:65-67` reads the old sealed ticket and the latest composition separately. If a successor is created between these reads, but has no dispatch intent yet, lines 88-94 can append the old registration to the successor. `composition_journal.py:79-104` does not require the registration digest to identify that record's ticket. Expected-head CAS therefore does not reject this internally mismatched write.

An in-memory one-shot storage-read interleaving used an old nonce of `1` repeated 32 times, a new nonce of `2` repeated 32 times, completed old absence proof and late old run 55. Actual registration returned current composition number 2 with the new ticket, but registration run 55 and a digest matching the old ticket rather than the current one.

**Required correction:** Keep one exact composition object through lookup and append; concurrent replacement must make the old worker stale. Validate `registration.request_digest == digest(current.ticket)` in the record boundary. The existing late-registration test begins after replacement and misses this interleaving. This is a registration availability/integrity failure, not a demonstrated live publication-authority bypass.

### P1.8: Exact Bytes Still Use Lossy Text Comparison

**Reopened residual, current severity P2.** SemVer filenames are now accepted by the full loader at `scripts/release-payloads.js:23-25`. However, lines 17 and 32 compare UTF-8-decoded strings. Distinct bytes `0x80` and `0x81` inside `name` both decode to a replacement character and are accepted as matching immutable/latest payloads.

Eight full-loader version cases passed, and filename/extra-newline differences were rejected. This remaining byte-equality issue is inherited behavior, not a new filename regression. No publication bypass is claimed: Python source acquisition rejects invalid UTF-8 at `metadata.py:28-41`.

**Required correction:** Reject invalid UTF-8 and compare captured original buffers. Preserve historical bytes; do not normalize or rewrite them.

### P2.5: Lifecycle Does Not Isolate Evidence Failure

**Reopened, P2.** The positive outer-I/O lifecycle is real and materially better. But `packages/cg-release/tests/test_profile_lifecycle.py:123-158` merges the evidence PR before docs succeeds. No case has valid deployed docs while the evidence PR is open, incorrectly reviewed, or contains altered/missing canonical/native/ownership output. The success assertion counts nine edits instead of comparing all nine committed outputs.

**Required correction:** Keep the production verification adapters active. Add independent negative evidence cases with valid docs; require pending/failure, immutable publication identities and no extra publication effects. Compare all nine committed bytes on success. Architecture confirms the positive addition; it does not contradict this remaining test gap. No production bypass or verifier-removal mutation was claimed.

### P2.6: Native Unix Fixture Removes Bash

**Reopened, P2.** `scripts/tests/release_shell_fixture.py:155-157,171-175` supplies an isolated PATH with no `bash`, then directly executes the real `bin/cg-release`. That launcher's `#!/usr/bin/env bash` must resolve Bash again through PATH on native Unix.

**Required correction:** Make the selected Bash available in the isolated fixture while retaining interpreter fallbacks, shadow-command recursion protection, real launcher execution, argv and exit assertions. Windows/Git Bash success is not native Unix evidence. This deterministic fixture defect is an eligible offline correction, not simply an unavailable-host gate.

### P2.10: Public Behavior Contracts Remain Incomplete

**Reopened, P2.** `profile_evidence.py:21-26` does not specify the attestation callback, actor provenance, pending `None` versus verified dictionary, or relevant effects/errors. `profile_worker.py:198-242` has a corrected example but lacks operation-specific arguments/environment, output/exit and side-effect contracts, including `EXPECTED_MANIFEST` for deployment authorization.

**Required correction:** Document those behavior contracts at the functions. Other API documentation improvements are valid. No Phase 7 README or handoff omission is counted.

### P2.14: Bash Sentinel Reverses Prefix Ordering

**New, P2.** `scripts/update.sh:75,93,100,302` forces string comparison by appending `x`. That fixes numeric coercion but changes lexical prefix order: `alphax` compares above `alpha1x`.

The actual frozen Bash reader returned newest-first `[v1.0.0-alpha, v1.0.0-alpha1]`; correct order is the reverse. A cross-reader probe found four failed pairs: `alpha/alpha1`, `rc/rca`, `a/aa`, and `a/a-`. Numeric `rc.2/rc.10`, the two adjacent huge-number cases, and `a/az` passed. All eight actual Bash processes exited normally. These are direct probes, not eight pytest tests.

**Required correction:** Force string comparison without altering lexical prefix order and add cross-reader prefix cases. The supplemental equality correction is independently verified for both huge numeric cases; this separate defect is not attributed to that final equality edit. Probe host was Git for Windows Bash 5.2.37, not native Unix.

### P2.15: Legacy Instructions Name The Wrong Controller Ref

**New, P2.** `.github/prompts/cg-release.prompt.md:458-465` and four generated command copies still say the deployment controller must exist on protected `main`. The actual authority path at `scripts/legacy-pages.js:57-62` uses the protected remote default, which can have another name.

**Required correction:** State the verified protected remote default revision. Preserve separate legacy stable/four-part source-branch rules and regenerate through the canonical generator only when repairs are authorized.

### P2.16: Cold Journal Replay Has Quadratic Work

**New, P2; static complexity evidence.** `github_journal.py:83-132` walks each retained commit, loads its complete cumulative tree and compares that tree with the derived state. For E retained events, cumulative tree-entry work grows as `1 + 2 + ... + E`, or O(E squared). Mutable composition operations call verified history repeatedly at `composition_journal.py:115-122,172-209`. The command-local 1,024-entry/32-MiB cache at `read_session.py:18-24,48-65` does not remove cold-read growth and still decodes returned values.

**Required correction:** Add fresh-reader provider-call, processed-entry and decoded-byte measurements at increasing event counts, then reuse an authenticated operation-local history view or verified delta processing where appropriate. Preserve signatures, parent linkage, complete history and tree integrity; do not truncate or compact evidence. This is a confirmed structural workload finding, not an observed timing/deadline failure. The warm-reader 48-refresh test does not test cold scheduled starts. P2.11 concerns different publication/snapshot inventory reuse and remains verified.

## Original Findings

`Verified` means the scoped implementation correction was independently inspected, with the stated offline proof. It does not mean external delivery or committed-candidate qualification passed.

| ID | Disposition | Concrete Current Evidence |
|---|---|---|
| P0.1 | Reopened | Legacy combined producer/verifier contamination proof above. |
| P1.1 | Verified | `profile_source.py:23-37`, `github_profile_reads.py:14-61`, `profile_docs_verify.py:42-48`; actual-provider outer-transport test at `test_profile_adapter_reads.py:90-115`. |
| P1.2 | Reopened | Incomplete/incorrect platform dependency inventories accepted. |
| P1.3 | Verified | Fixed `run_snapshot` connected at `profile_worker.py:138-182`; RECORD/containment, args, environment, deadline/output guards at `profile_process.py:27-64,79-144`; installed-resource tests inspected and byte identity checked. |
| P1.4 | Verified | Strict retry default/bounds at `profile_models.py:60-70`, use at `profile_docs.py:65-101`; fresh policy-bound test passed. Replay defect is counted under P1.13. |
| P1.5 | Reopened | Real producer/approval/import inventory digest disagreement. |
| P1.6 | Reopened | Candidate-inclusive aggregate envelope capacity omitted. |
| P1.7 | Reopened | Reviewed pre-receipt recovery can select generic replacement hook requirements. |
| P1.8 | Reopened, P2 residual | Full SemVer filename loading works; exact-byte claim still uses lossy strings. |
| P1.9 | Verified | Exact dual-tree union in `profile_source.py:23-75`, acquisition `source.py:118-128,194-222`, preparation reacquisition `prepare_stage.py:115-159` and `replay.py:66-80`; ten provider cases and real CLI no-write rejection probes. |
| P1.10 | Reopened | Historical grant requirement dropped at final attestation boundary. |
| P1.11 | Reopened | Required LF/CRLF distribution identity cannot pass current installed-tree comparison. |
| P1.12 | Verified | `source.py:213-225` calls `profile_selection.py:28-102,224-255` before effects; preparation reacquires. First-pre-release positive and missing/highest-stable/older-maintenance negatives inspected. |
| P1.13 | Reopened | Two independent real dispatcher/provider/journal probes reproduce immutable absence timestamp conflict on re-entry. Absorbs draft P1.21. |
| P1.14 | Verified | Independent bounded records/CAS at `composition_journal.py:19-29,38-68,172-209`, atomic event/file transactions at `git_journal.py:38-42`, compact parent link at `profile_docs.py:88-100`; 48/49 test inspected. Separate race/scaling findings remain. |
| P1.15 | Reopened | Applicable human authority can be revoked during the final deployment run read. |
| P1.16 | Verified | Exact nine-file projection at `profile_attestations.py:34-143`; pre-PR sealing and post-merge byte checks at `profile_evidence.py:88-163`; canonical native/ownership serialization matches generator lines 1505-1568; two projection probes passed. |
| P1.17 | Reopened | Successful wrapper is not exact successful protected deployment evidence. |
| P1.18 | Verified | Real remote default/current authority at `legacy-pages.js:57-74,108`; exact controller SHA and repeated pre-effect checks; six selected helper tests passed. Actual protection installation remains external. |
| P2.1 | Verified | Unchanged 300-line gate at `test_module_bounds.py:6-13`; `models.py` 296 and `build_stage.py` 289; fresh original test passed. |
| P2.2 | Verified | Narrow standalone exemption at `scripts/cg_validate_modules.py:554-582,932`; negative relocation cases remain at `test_module_registry.py:485-519`; parent executed real-repository positive assertion without writes. |
| P2.3 | Verified | Three Pester cases retained and behavior-based at `tests/docs-automation.Tests.ps1:90-124`; related lineage/privilege/byte guards remain; two actual Node helper tests passed. |
| P2.4 | Verified | Native selectors at `cg_pr_preflight.py:114-116,899-908`, ordinary Node `package.json:14`, three-host/Python 3.8 jobs at `.github/workflows/tests.yml:225-280,335-358`; real host results remain separate. |
| P2.5 | Reopened | Missing independent lifecycle evidence-failure and all-nine-byte assertions. |
| P2.6 | Reopened | Native Unix isolated fixture cannot resolve launcher Bash shebang. |
| P2.7 | Verified | `hatch_build.py:27-68` prioritizes complete bundled resources and fails incomplete sdists; constrained exact-repository fallback; owned-copy/source-free tests inspected, not rebuilt here. |
| P2.8 | Verified | `.gitattributes:19-21`; both fresh SHA-256 checks and exact original Git-byte comparisons match recorded fixture provenance. |
| P2.9 | Verified | `LegacyOperation` in actual help/examples and canonical/generated Reserve/Finalize commands; authority/recovery prose cross-checked. Separate default-ref prose defect is P2.15. |
| P2.10 | Reopened | Remaining public callback/pending-result/CLI behavior contracts. |
| P2.11 | Verified | Actual provider/acquisition probe: one tag inventory, one Release inventory, two asset inventories and two downloads; each unchanged recheck repeats inventories with zero downloads. Mutated selected bytes rejected. Repository tests assert download count, not equivalent full inventory counts. |
| P2.12 | Reopened, P1 residual | Candidate-inclusive release-directory graph absent at approval; Node's pre-copy guard is now present. |
| P2.13 | Verified | Real native-owner routing selects five commands versus nine local commands, retaining three validators and both producer requirements; mocked spawn success is not gate evidence. |
| P3.1 | Verified | Explicit protocol methods and raw completion dictionaries at `hooks.py:58-100,143-153`; all seven source signatures match in fresh introspection; explicit RECORD-verified resource accessor. |
| P3.2 | Verified | `test_release_version_readers.py:155-167` identifies frozen hashed historical bytes and disclaims delivered bridge proof; fresh provenance comparison supports it. |

## Review Completion

All ten specs were read and all ten analyses completed. Exact native task IDs, shared-finding decisions and individual proof limits are in the JSON. Evidence-retrieval continuations did not execute more tests or write source.

| Spec | State | Scope |
|---|---|---|
| cg-code-quality | Complete | Retry policy, module bounds, actual protocol, replay idempotency. |
| cg-testing | Complete | Assertion repair, ordinary selectors, true lifecycle, installed resources, 48-refresh test meaning, Unix fixture. |
| cg-documentation | Complete | Public API contracts, all command examples, frozen-reader provenance, authority/recovery documentation. |
| cg-version-control | Complete | Legacy entries/Finalize, Pages/source trust, current remote-default authority, secrets/ignore/history boundaries. |
| cg-reproducibility | Complete | Actual source/native environment, complete receipt boundary, bundled sdists, owned copies, historical bytes, producer ownership and generic imports. |
| cg-performance | Complete | Unregistered dispatch/absence replay, bounded records, actual inventory reuse, registration interleaving, policy-recovery conflict and cold journal workload. |
| cg-architecture | Complete | Immutable original hooks, adopted stable selection, exact nine-file evidence PR, generic mode and recovery connections. |
| cg-data-quality | Complete | Provider API, installed snapshot decoder/exporter, cross-language identities, complete resource and destination envelopes. |
| cg-learnings-researcher | Complete | Real boundary and immutable-byte lessons, complete loader/render route, exact dual-tree obligations, CLI pre-effect rejection. |
| cg-adversarial | Complete | Pinned process/resources, real/private bridge qualification, late applicable authority and bootstrap feasibility. |

R, Stata, survey/statistical and research-method checks do not apply to this tool implementation. This is an applicability decision, not a skipped finding. No spec is reported as clean merely because its original IDs were marked fixed.

## Evidence Assessment

**Current freeze:** `.cg-docs/work-reports/release-controller/2026-09-12-phase6-final-validation.json` was read after the last Bash edit. Its actual full invocation, not the earlier gate, supplies these results. The reviewer did not duplicate the full suites or builds.

| Gate | Current Result | Qualification |
|---|---|---|
| Complete prepare preflight | 9 selected, 9 completed, 9 passed, 0 failed | Coordinator's actual `--phase prepare --full-gate --run-native-target --format json` result; uncommitted working tree. |
| Native selection | 2,587 passed, 0 failed, 50 skipped, 2 deselected | Skips/deselections are not passes. |
| Full package | 807 passed, 0 failed, 0 skipped | Main gate owned package build/installed-wheel fixtures. |
| Profile/launcher selection | 28 passed, 0 failed | Not real native Unix evidence. |
| Full Pester | 2,931 passed, 0 failed, 2 skipped | `tests/last-run.json`, `2026-09-12T17:26:55Z`, no filter; read directly and matched coordinator evidence. Named executor alone ran Pester. |
| Ordinary Node | 101 passed, 1 failed, 0 skipped | Required unchanged file-symlink `EPERM` at `scripts/tests/assemble-docs-site.test.js:154`; still failed, not waived. |
| Plan/parity regressions | 56 passed, 0 failed, 8 skipped | Existing POSIX cases unavailable on this Windows host. |
| Other current checks | Validators, package/native lint, package build, docs/fingerprint and disabled installation check passed | Exact commands and qualifications remain in coordinator artifact. |
| Canonical generation | Actual `cg_generate_targets.py --all`, 1,486 adapter writes | Main-owned generation after the last edit; no manual adapter edits by review. |

Pester cleanup diagnostics remain disclosed in the coordinator artifact. Its `bash-scripts` Windows placeholder is not Bash integration evidence. The earlier repair gate and its counts are historical evidence only, not relabeled as this freeze. Counts from overlapping selections and direct probes are not summed as unique test coverage.

**Real connections:** The normal lifecycle uses real CLI/controller/provider/journal paths with only outer transport/time fixtures. It builds and uses installed wheel resources in retained full-suite evidence. However, its snapshot transport supplies Python-constructed envelopes rather than exercising native export for every accepted filename. The data reviewer verified installed RECORD/containment checks and equality of all three installed Node resources with canonical source, then exposed the exporter/approval mismatch. Generic no-profile imports remain isolated.

**48 refreshes / 49 records:** `packages/cg-release/tests/test_profile_dispatch.py:95-114` performs 48 real reconciliation refreshes after synthetic cancelled runs. It requires 49 retained records, aggregate bytes above 64 KiB, each record below 64 KiB, unchanged parent bytes and unchanged reservation. It is not evidence of 48 successful deployments. The separate 64-record store test is at `test_composition_journal.py:25-56`. These tests were inspected; this reviewer did not rerun their wheel-building lifecycle fixture.

**Decoder limits:** Both valid-envelope paths use 64 MiB encoded, 32 MiB decoded, 5-10,000 files, at most 10,000 directories including root, 33 path components and 255 characters. Dev reserves are 1,000 files/child directories, 32 MiB, 32 components and 251 characters. Generic API JSON retains 4 MiB. Node has a JSON depth limit of 40; Python has no explicit matching protocol depth limit. Valid snapshots are shallow (maximum depth 3), so the demonstrated depth-41 raw array is not a valid-snapshot rejection and is not counted as another finding. Neither decoder has a separate hidden node/string-count budget. Complete acquisition and destination failures are detailed above.

**Probe limits:** Fresh probes used the actual production functions with outer I/O/clock supplied in memory, except explicitly identified boundary/count/static checks. Architecture's recovery probes manually seed strict grant/seal/receipt data, and P1.22 uses a synthetic journal read view; they are not authenticated recovery-lifecycle evidence. One of the two projection probes is a negative foreign-target test, not a second successful generation. No helper mock's supplied success was counted as a production pass. Setup-only quote/import failures and the unavailable memory-context lookup are retained as unusable attempts, not product failures. Two public reference reads checked workflow-run field semantics; no target-repository API call or live operation followed, and no uncertain extra field-semantics finding was asserted.

## Bridge Bootstrap

No unavoidable circular prerequisite is established. `profile_bridge.py:69-83` requires published previous, bridge and new-format successor distributions, but does not require that this controller created the successor. `published_history.py:40-45` permits explicit bootstrap adoption. A separately reviewed and authorized external bootstrap publication/adoption can satisfy the condition while the controller is disabled.

That is a logical route, not supplied authority or completed delivery. The legacy publisher rejects a new-format RC successor, the qualifier creates no release, and this task authorizes neither publication nor real qualification. Exact external successor authority/procedure, immutable identities, and actual native Windows/Unix installation/link/update/run/job/artifact/digest proof remain required. P1.11 and P1.19 are eligible offline qualifier defects, distinct from those external requirements.

## Context And Preservation

The review read `.kilo/commands/cg-review.md` first, project instructions, full-route/context/model-advisory contracts, all ten reviewer specs, plan design and Steps 11-12, and `.github/shared/release-controller.contract.md`. It used the requested current work-report section from line 3224, compact batch evidence and supplemental Bash proof, not the entire execution history.

The project-memory/Brain checks supplied exact-artifact, real-I/O, wire-format and immutable-anchor lessons. Relevant sources include the 2026-08-13 verified Pages/tag solution, 2026-07-28 real-boundary tests, 2026-08-10 gh fixture keys, 2026-08-28 exact JSON boundaries and 2026-08-31 captured-byte trust anchors. Older main-only advice was superseded by the approved September 11 controller design. No open-brain service tool was available; local Brain and saved project memory were used. No memory write was requested or performed.

The new controller writer and activation workflows remain disabled and real authority placeholders remain unresolved. This is not a claim that all legacy workflows are disabled. No source/test mutation, new full suite, Pester invocation, source-tree package/dist build, install, secret/settings change, live bridge/release/Pages operation, commit/push/PR, historical rewrite or Phase 7 work was performed by this review. All six named raw source/protected-artifact identities match the start of review. A separate current 2,512-file scoped fingerprint is recorded for the handoff; it is not a before/after full-tree proof or a reviewed committed candidate. No original tracking status or implementation/review budget was changed.

## Remaining Handoff

The coordinator must address the 23 open findings, beginning with P0.1. Keep source writers sequential, preserve authority and immutable evidence requirements, generate through the canonical path, freeze again and rerun applicable verification. Original phase/tracking artifacts remain unchanged for the coordinator's authorized handoff. This verification does not reset implementation counts or begin another repair stage.

Even after offline repairs, the required supported-host file-symlink result, actual native Unix/Python 3.8 execution, delivered bridge and clean-client qualification, exact-source six-cell CI and both producer IDs, committed-candidate gate, bootstrap authority and protected settings remain unmet and unwaived. No Phase 6, V6 or external-V6-only completion is justified. High-effort release/security engineering and independent verification remain the appropriate handoff capability; model/effort selection remains with the user.
