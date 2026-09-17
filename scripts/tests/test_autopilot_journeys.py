"""Complete multi-batch autopilot journeys with injected failures (Phase 6, Step 15).

Every journey drives the real control transition functions under
``scripts/autopilot/``: marker acquisition, reservations, stage settlement,
expected-byte checkpoints, foreground dispatch correlation, publication
observation, CI classification, deadline extensions and interrupted-run
reconciliation. Children are a recording foreground dispatcher. Git effects
run in a temporary repository against a local bare remote. GitHub is an
exact-wire fake backend whose unscripted argv raises; no live network or
destructive operation can reach a real checkout. Test seams are injection-only:
no production module gained a fake-success or runtime bypass flag.

Run: python -B -m pytest scripts/tests/test_autopilot_journeys.py -q
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pytest

import secure_fs
from secure_fs import ExpectedFileState
from tests.autopilot_plan_fixture import plan_source_valid
from autopilot import state as st
from autopilot import ci, queries as q
from autopilot import checkpoint as ck
from autopilot import context as cx
from autopilot import evidence as ev
from autopilot import pipeline as pl
from autopilot import plan as plan_mod
from autopilot import recovery as rc
from autopilot import records as recs
from autopilot.arguments import BatchSegment
from autopilot.contracts import (
    AutopilotError,
    EvidenceError,
    PacketError,
    PlanError,
    StateError,
    sha256_hex,
)
from autopilot.packets import StageEnvelope, StageResult

FIXTURES = Path(__file__).resolve().parents[0] / "fixtures" / "autopilot"
SHA = "a" * 64
RUN = "run-journey"
NONCE = "nonce-journey"
BRANCH = "cg-autopilot"
BASE = "origin/dev"
PLAN_REL = ".cg-docs/plans/journey-plan.md"
CURSOR_REL = ".cg-docs/active-state/current.json"
CONTRACT_REL = ".github/shared/autopilot-stage.contract.md"
COMMAND_REL = ".kilo/commands/cg-autopilot.md"
REQUIRED_CONTEXTS = ("native-targets", "pester-prompt-tools")


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class JourneyError(RuntimeError):
    """A journey harness violation; tests assert typed production errors."""


# ---------------------------------------------------------------------------
# Exact-wire fake GitHub backend
# ---------------------------------------------------------------------------


class FakeGitHub:
    """Exact-wire fake GitHub: records argv, serves only scripted shapes.

    Any argv outside the served set raises ``AssertionError``, so a test can
    never reach a live network through this backend.
    """

    def __init__(
        self,
        *,
        pr: Optional[dict] = None,
        checks_pages: Sequence[object] = (),
        log_bytes: bytes = b"",
    ) -> None:
        self.pr = pr
        self.checks_pages = list(checks_pages)
        self.log_bytes = log_bytes
        self.view_calls: List[Tuple[str, ...]] = []
        self.create_calls: List[Tuple[str, ...]] = []
        self.run_calls: List[Tuple[str, ...]] = []

    def set_checks(self, *pages: object) -> None:
        self.checks_pages = list(pages)

    def set_pr(self, pr: Optional[dict]) -> None:
        self.pr = pr

    def create_pr(self, *, base: str, head: str, title: str, body_file: str) -> dict:
        argv = (
            "gh", "pr", "create", "--base", base, "--head", head,
            "--title", title, "--body-file", body_file,
        )
        self.create_calls.append(argv)
        number = 100 + len(self.create_calls)
        created = {
            "url": f"https://github.com/o/r/pull/{number}", "number": number,
            "title": title, "state": "OPEN", "baseRefName": base,
            "headRefName": head, "headRefOid": "b" * 40,
        }
        self.pr = created
        return created

    def run(self, argv: Sequence[str]) -> q.CommandOutcome:
        argv = tuple(argv)
        if argv[:3] == ("gh", "pr", "view"):
            self.view_calls.append(argv)
            if self.pr is None:
                return q.CommandOutcome(1, "", "no open pull requests found")
            return q.CommandOutcome(0, json.dumps(self.pr), "")
        if argv[:3] == ("gh", "pr", "create"):
            raise AssertionError(
                "gh pr create must go through create_pr so the wire is recorded."
            )
        if argv[:4] == ("gh", "run", "view"):
            self.run_calls.append(argv)
            return q.CommandOutcome(0, self.log_bytes.decode("utf-8", errors="replace"), "")
        raise AssertionError(f"unscripted gh argv: {list(argv)}")


# ---------------------------------------------------------------------------
# Recording foreground dispatcher
# ---------------------------------------------------------------------------


class RecordingDispatcher:
    """Recording foreground dispatcher; outcomes per operation ID.

    An outcome is ``(child_id, raw_bytes)`` or a zero-argument callable that
    performs the child's effects and returns that tuple; an exception outcome
    simulates a missing or failing native child. Dispatching an unscripted
    operation raises so no stage can silently proceed on invented output.
    """

    def __init__(self) -> None:
        self.outcomes: Dict[str, object] = {}
        self.calls: List[Tuple[str, StageEnvelope]] = []

    def script(self, operation_id: str, outcome: object) -> None:
        self.outcomes[operation_id] = outcome

    def __call__(self, command: str, envelope: StageEnvelope):
        self.calls.append((command, envelope))
        if envelope.operation_id not in self.outcomes:
            raise AssertionError(f"unscripted dispatch for {envelope.operation_id}")
        outcome = self.outcomes[envelope.operation_id]
        if isinstance(outcome, BaseException):
            raise outcome
        if callable(outcome):
            outcome = outcome()
        if not isinstance(outcome, tuple) or len(outcome) != 2:
            raise AssertionError("outcome must be (child_id, raw_result_bytes).")
        return outcome[0], outcome[1]


# ---------------------------------------------------------------------------
# Journey harness: the parent loop over the real control functions
# ---------------------------------------------------------------------------


def _scrubbed_env() -> dict:
    """Inherit nothing credential- or git-redirect-related into probe git."""
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(
            ("GH_", "GITHUB_", "GIT_AUTHOR", "GIT_COMMITTER", "GIT_ASKPASS",
             "GIT_DIR", "GIT_WORK_TREE", "SSH_", "GCM_")
        )
    }


def _real_git(repo: Path, *args: str) -> q.CommandOutcome:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True,
        check=False, timeout=60, env=_scrubbed_env(),
    )
    return q.CommandOutcome(result.returncode, result.stdout, result.stderr)


class ConfinedGit:
    """Real git confined to one repository; every argv and cwd is recorded."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.calls: List[Tuple[Tuple[str, ...], str]] = []

    def __call__(self, argv: Sequence[str]) -> q.CommandOutcome:
        argv = tuple(argv)
        assert argv and argv[0] == "git", (
            f"ConfinedGit must only ever run git, got {argv!r}"
        )
        self.calls.append((argv, str(self.repo)))
        outcome = _real_git(self.repo, *argv[1:])
        return outcome


class Journey:
    """One bounded parent-loop emulation over the real control modules."""

    def __init__(self, repo: Path, *, plan_phases: int = 6) -> None:
        self.repo = repo
        self.git = ConfinedGit(repo)
        self.backend = FakeGitHub()
        self.dispatcher = RecordingDispatcher()
        self.coordination = st.resolve_coordination_root(repo)
        self.cursor = repo / CURSOR_REL
        self.plan_phases = plan_phases
        self.plan = None
        self.marker = None
        self.branch = BRANCH
        self.base = BASE
        self.budget = cx.ParentContextBudget()
        self.previous_stage: Optional[str] = None
        self.operation_counter = 0
        self.child_counter = 0
        self.reservation_counter = 0
        self.previous_operations: frozenset = frozenset()
        self.known_approvals: frozenset = frozenset()
        self.last_op: Optional[str] = None
        self.last_child: Optional[str] = None
        self.batch_key = "batch-1"

    # -- setup -----------------------------------------------------------

    @classmethod
    def setup(cls, tmp_path: Path, *, plan_phases: int = 6,
              completed: tuple = (), current: int = 1) -> "Journey":
        remote = tmp_path / "remote.git"
        remote.mkdir(parents=True, exist_ok=True)
        _real_git(remote, "init", "-q", "--bare")
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        _real_git(repo, "init", "-q", "-b", "dev")
        _real_git(repo, "config", "user.email", "a@example.com")
        _real_git(repo, "config", "user.name", "A")
        (repo / "f.txt").write_text("base\n", encoding="utf-8")
        journey = cls(repo, plan_phases=plan_phases)
        journey._commit_all("chore: baseline")
        _real_git(repo, "remote", "add", "origin", str(remote))
        _real_git(repo, "push", "-qu", "origin", "dev")
        _real_git(repo, "checkout", "-qb", BRANCH)
        journey.write_contract_and_command()
        journey.write_plan(completed=completed, current=current)
        (repo / ".cg-docs/active-state").mkdir(parents=True, exist_ok=True)
        journey._commit_all("chore: autopilot fixtures")
        _real_git(repo, "push", "-qu", "origin", BRANCH)
        return journey

    def write_contract_and_command(self) -> None:
        contract = self.repo / CONTRACT_REL
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text("# Autopilot Stage Contract\n\nContract version: 1.\n",
                            encoding="utf-8")
        command = self.repo / COMMAND_REL
        command.parent.mkdir(parents=True, exist_ok=True)
        command.write_text("# Autopilot command\n\nProbe-only entry.\n", encoding="utf-8")

    def write_plan(self, *, completed: tuple = (), current: int = 1, extra: str = "") -> None:
        plan_file = self.repo / PLAN_REL
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        plan_file.write_text(
            plan_source_valid(
                phases=self.plan_phases, completed=completed, current=current,
                extra=extra,
            ),
            encoding="utf-8",
        )

    def _commit_all(self, message: str) -> str:
        outcome = _real_git(self.repo, "add", "-A")
        assert outcome.returncode == 0, outcome.stderr
        before = self.head()
        outcome = _real_git(self.repo, "commit", "-qm", message)
        assert outcome.returncode == 0, outcome.stderr
        return before

    def head(self) -> str:
        return _real_git(self.repo, "rev-parse", "HEAD").stdout.strip()

    # -- identity and invocation -----------------------------------------

    def installed_digests(self) -> Tuple[str, str]:
        return (
            _sha((self.repo / CONTRACT_REL).read_bytes()),
            _sha((self.repo / COMMAND_REL).read_bytes()),
        )

    def guard_installed_identity(self, envelope: StageEnvelope) -> StageEnvelope:
        contract, command = self.installed_digests()
        if envelope.contract_digest != contract or envelope.command_digest != command:
            raise pl.PipelineError(
                "installed-identity-changed: the stage envelope carries stale "
                "installed command/contract digests; re-check installed identity "
                "before effects."
            )
        return envelope

    def start(self, segments: Sequence[BatchSegment]) -> None:
        self.plan = plan_mod.read_plan(self.repo, PLAN_REL)
        union = plan_mod.validate_batches(self.plan, segments)
        assert union == tuple(range(segments[0].start, segments[-1].end + 1))
        self.marker = st.acquire_marker(
            self.repo, self.coordination, run_id=RUN, owner_nonce=NONCE,
            worktree=str(self.repo), branch=self.branch,
            plan_digest=self.plan.digest, required_base=self.base,
        )
        initial = ck.build_cursor_record(
            run_id=RUN, revision=0, worktree=str(self.repo), branch=self.branch,
            required_base=self.base, plan_digest=self.plan.digest,
            next_action=f"/cg-work phase{union[0]} review:none",
            updated_at="2026-01-01T00:00:00Z",
            batch_pointer={"phase": union[0], "segment-start": segments[0].start,
                           "segment-end": segments[-1].end},
        )
        secure_fs.secure_write_bytes(
            self.repo, PurePosixPath(CURSOR_REL), initial,
            expected_state=ExpectedFileState.absent(),
        )
        self.marker = ck.bind_initial_cursor(
            self.marker, self.coordination, owner_nonce=NONCE, cursor_bytes=initial,
        )

    def advance_plan(self, completed: tuple, current: int) -> None:
        old_source = self.plan.source
        self.write_plan(completed=completed, current=current)
        new_source = (self.repo / PLAN_REL).read_text(encoding="utf-8")
        delta = plan_mod.progress_delta(old_source, new_source)
        assert set(delta) <= set(plan_mod.PROGRESS_FIELDS)
        self.plan = plan_mod.validate_autopilot_plan(new_source, self.repo / PLAN_REL)

    # -- operations --------------------------------------------------------

    def next_operation(self) -> str:
        self.operation_counter += 1
        operation_id = f"op-{self.operation_counter}"
        pl.assert_fresh_operation(self.previous_operations, operation_id)
        self.previous_operations |= {operation_id}
        self.last_op = operation_id
        return operation_id

    def next_reservation(self) -> str:
        self.reservation_counter += 1
        return f"res-{self.reservation_counter}"

    def reserve(self, scope: str, key: str) -> str:
        reservation_id = self.next_reservation()
        self.marker = st.reserve(
            self.marker, self.coordination, owner_nonce=NONCE,
            scope=scope, key=key, reservation_id=reservation_id,
        )
        return reservation_id

    def envelope(self, stage: str, operation_id: str, *,
                 reservation_id: Optional[str] = None,
                 approval_refs: Sequence[str] = ()) -> StageEnvelope:
        contract, command = self.installed_digests()
        payload = {
            "schema-version": 1, "run-id": RUN, "operation-id": operation_id,
            "stage": stage, "root": str(self.repo), "branch": self.branch,
            "plan": PLAN_REL, "plan-execution-digest": self.plan.digest,
            "contract-digest": contract, "command-digest": command,
            "expected-revision": self.marker.revision,
            "scope": [PLAN_REL], "approval-refs": list(approval_refs),
            "reservation-id": reservation_id,
        }
        return StageEnvelope.parse(json.dumps(payload).encode("utf-8"))

    # -- stage driving ------------------------------------------------------

    def run_stage(self, stage: str, *, phase: Optional[int] = None,
                  status: str = "succeeded", effect: bool = False,
                  reservation_id: Optional[str] = None,
                  decision: Optional[dict] = None,
                  manifest: Optional[str] = None,
                  tests: Sequence[dict] = (),
                  artifact_specs: Sequence[Tuple[str, str, bytes]] = (),
                  cursor_requests: Sequence[dict] = (),
                  approval_refs: Sequence[str] = (),
                  findings: bool = False, verify_context: bool = False,
                  record: bool = True, settle: bool = True,
                  effects: Optional[Callable[[], None]] = None,
                  forced_outcome: bool = False) -> Tuple[object, pl.Transition]:
        pl.resolve_activation(stage, previous=self.previous_stage)
        command = pl.render_command(stage, phase=phase)
        operation_id = self.next_operation()
        envelope = self.envelope(stage, operation_id, reservation_id=reservation_id,
                                 approval_refs=approval_refs)
        pl.validate_approval_refs(envelope, self.known_approvals)
        envelope = self.guard_installed_identity(envelope)
        if reservation_id is not None:
            self.marker = st.begin_stage(
                self.marker, self.coordination, owner_nonce=NONCE,
                operation_id=operation_id, reservation_id=reservation_id,
            )
        if effect:
            ck.begin_effect(self.coordination, operation_id,
                            recorded_at="2026-01-01T00:00:00Z")
        artifacts = [
            self.artifact(kind, path, content, operation_id)
            for kind, path, content in artifact_specs
        ]
        raw = self.result_bytes(
            stage, status, operation_id, decision=decision, manifest=manifest,
            tests=tests, artifacts=artifacts, cursor_requests=cursor_requests,
        )
        if not forced_outcome:
            if effects is not None:

                def outcome():
                    effects()
                    return self.next_child(), raw

            else:
                outcome = (self.next_child(), raw)
            self.dispatcher.script(operation_id, outcome)
        correlated = pl.run_foreground(
            command=command, envelope=envelope, dispatcher=self.dispatcher,
            effect_started=effect, context_budget=self.budget,
        )
        self.last_child = correlated.child_id
        self.charge_frame(raw)
        if record:
            ck.record_result(self.coordination, operation_id, raw)
        if reservation_id is not None and settle:
            zero_evidence = (
                ("tests/last-run.json",)
                if status == "needs-input" and not effect and not manifest
                else ()
            )
            self.marker = pl.settle_operation(
                self.marker, self.coordination, owner_nonce=NONCE,
                operation_id=operation_id, result=correlated.result,
                zero_effect_evidence=zero_evidence,
            )
        transition = pl.select_transition(
            stage, correlated.result, has_findings=findings,
            verify_context=verify_context,
        )
        self.previous_stage = stage
        return correlated, transition

    def next_child(self) -> str:
        self.child_counter += 1
        return f"ses-journey-{self.child_counter}"

    def charge_frame(self, raw: bytes) -> None:
        frame = cx.measure_frame(raw, metadata={"child-id": self.last_child})
        decision = cx.budget_decision(frame, self.budget)
        assert decision["decision"] == "dispatch", decision
        self.budget = cx.charge(self.budget, frame.total_bytes())

    @staticmethod
    def result_bytes(stage: str, status: str, operation_id: str, *,
                     decision: Optional[dict] = None,
                     manifest: Optional[str] = None,
                     tests: Sequence[dict] = (),
                     artifacts: Sequence[dict] = (),
                     cursor_requests: Sequence[dict] = ()) -> bytes:
        payload = {
            "schema-version": 1, "stage": stage, "status": status,
            "run-id": RUN, "operation-id": operation_id,
            "artifacts": list(artifacts), "head-before": None,
            "head-after": None, "change-manifest-hash": manifest,
            "tests": list(tests), "next-stage": None,
        }
        if decision is not None:
            payload["decision"] = decision
        if cursor_requests:
            payload["cursor-update-requests"] = list(cursor_requests)
        return json.dumps(payload).encode("utf-8")

    @staticmethod
    def decision(request_id: str = "req-1", options: Sequence[str] = ("go", "stop"),
                 approval_refs: Sequence[str] = ()) -> dict:
        return {
            "request-id": request_id, "summary": "scoped decision",
            "options": list(options), "scope-digest": SHA,
            "approval-refs": list(approval_refs),
        }

    @staticmethod
    def cursor_request(event_kind: str, expected_revision: int) -> dict:
        return {
            "expected-revision": expected_revision, "event-kind": event_kind,
            "plan-ref": PLAN_REL, "report-ref": ".cg-docs/work-reports/example.md",
        }

    @staticmethod
    def artifact(kind: str, path: str, content: bytes, operation_id: str) -> dict:
        return {
            "kind": kind, "path": path, "byte-count": len(content),
            "sha256": _sha(content), "operation-id": operation_id,
            "content-identity": None,
        }

    def checkpoint_cursor(self, *, next_action: str,
                          fold_reservation_ids: Sequence[str] = (),
                          transaction_id: Optional[str] = None,
                          before_publish: object = None) -> None:
        payload = ck.build_cursor_record(
            run_id=RUN, revision=self.marker.revision + 1,
            worktree=str(self.repo), branch=self.branch, required_base=self.base,
            plan_digest=self.plan.digest, next_action=next_action,
            updated_at="2026-01-01T00:00:00Z",
            batch_pointer={"phase": 1, "segment-start": 1, "segment-end": 1},
        )
        self.marker = ck.checkpoint(
            self.marker, self.coordination, self.cursor, payload,
            owner_nonce=NONCE, fold_reservation_ids=tuple(fold_reservation_ids),
            transaction_id=transaction_id or f"tx-{self.marker.revision + 1}",
            before_publish=before_publish,
        )

    # -- work-child effects ------------------------------------------------

    def write_work_output(self, phase: int) -> bytes:
        report = self.repo / ".cg-docs/work-reports/example.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        content = f"# Work report phase {phase}\n\nExecuted phase {phase}.\n".encode("utf-8")
        report.write_bytes(content)
        return content

    # -- publication --------------------------------------------------------

    def publication_runner(self) -> Callable[[Sequence[str]], q.CommandOutcome]:
        def run(argv: Sequence[str]) -> q.CommandOutcome:
            if argv[0] == "gh":
                return self.backend.run(argv)
            return self.git(argv)
        return run

    def observe_publication(self) -> q.PublicationState:
        return q.observe_publication(
            self.publication_runner(), branch=self.branch, selected_base=self.base
        )

    def publish_child_effects(self, *, message: str = "feat(autopilot): batch payload",
                              trailers: Sequence[str] = ()) -> Tuple[str, str]:
        before = self.head()
        outcome = _real_git(self.repo, "add", "-A")
        assert outcome.returncode == 0, outcome.stderr
        commit_args = ["commit", "-q", "-m", message]
        for trailer in trailers:
            commit_args += ["-m", trailer]
        outcome = _real_git(self.repo, *commit_args)
        if outcome.returncode != 0:
            raise JourneyError(f"commit failed: {outcome.stderr}")
        after = self.head()
        push = _real_git(self.repo, "push", "-q", "origin", self.branch)
        if push.returncode != 0:
            raise JourneyError(f"push failed: {push.stderr}")
        return before, after

    def ensure_pr(self) -> Tuple[dict, str]:
        state = self.observe_publication()
        if state.state == "existing-matching-pr":
            assert state.pr is not None
            return state.pr, "reused"
        if state.state == "pushed-no-pr":
            created = self.backend.create_pr(
                base=self.base, head=self.branch,
                title="feat(autopilot): journey", body_file="pr-body.md",
            )
            return created, "created"
        raise JourneyError(f"unexpected publication state {state.state}")

    def coverage_of_reviewed_payload(self) -> q.Coverage:
        return q.coverage_of([
            q.PathIdentity("f.txt", "present",
                           _sha((self.repo / "f.txt").read_bytes()),
                           len((self.repo / "f.txt").read_bytes())),
            q.PathIdentity(".cg-docs/work-reports/example.md", "present",
                           _sha((self.repo / ".cg-docs/work-reports/example.md").read_bytes()),
                           len((self.repo / ".cg-docs/work-reports/example.md").read_bytes())),
        ])

    # -- CI observation and repairs -----------------------------------------

    def observe_ci(self) -> ci.Observation:
        checks = []
        for page in self.backend.checks_pages:
            checks.extend(q.normalize_rollup(page, "rollup"))
        merged = ci.merged_checks([checks])
        return ci.classify_observation(
            merged, required=[ci.RequiredContext(name, None)
                              for name in REQUIRED_CONTEXTS]
        )

    def repair_commit(self, pr_number: int, round_number: int,
                      operation_id: str) -> None:
        (self.repo / "fix.txt").write_text(f"repair round {round_number}\n",
                                           encoding="utf-8")
        before = self.head()
        self.publish_child_effects(
            message=f"fix(ci): repair round {round_number}",
            trailers=(f"CI-Fix-Round: {pr_number}/{round_number}",
                      f"Autopilot-Operation: {operation_id}"),
        )
        assert self.head() != before

    def count_ci_rounds(self, pr_number: int) -> int:
        outcome = _real_git(self.repo, "log", "--format=%B")
        pattern = re.compile(rf"^CI-Fix-Round: {pr_number}/(\d+)$", re.MULTILINE)
        rounds = {int(match.group(1)) for match in pattern.finditer(outcome.stdout)}
        return max(rounds, default=0)

    def project_index(self) -> q.Routing:
        outcome = self.git(("git", "ls-files", "--stage"))
        assert outcome.returncode == 0, outcome.stderr
        entries = q.parse_index_entries(outcome.stdout, "git-ls-files")
        return q.classify_routing(entries)


# ---------------------------------------------------------------------------
# Fixture safety and reconciliation helpers
# ---------------------------------------------------------------------------


def test_fake_backend_and_confined_git_reject_everything_unscripted(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    backend = FakeGitHub()
    with pytest.raises(AssertionError, match="unscripted"):
        backend.run(("gh", "repo", "view", "o/r"))
    with pytest.raises(AssertionError, match="unscripted"):
        backend.run(("gh", "api", "repos/o/r"))
    git = ConfinedGit(tmp_path)
    outcome = git(("git", "status", "--porcelain"))
    assert outcome.returncode != 0 or isinstance(outcome.stdout, str)
    assert all(cwd == str(git.repo) for _, cwd in git.calls)
    assert journey.backend is not None


def test_repeated_reconciliation_is_noop_or_same_blocker(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    first = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                         owner_nonce=NONCE)
    assert first.status == "noop-complete"
    second = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                          owner_nonce=NONCE)
    assert second.status == first.status
    assert second.marker == first.marker
    foreign = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                           owner_nonce="other-nonce")
    assert foreign.status == "blocked"
    assert foreign.reason == "foreign-owner"
    again = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                         owner_nonce="other-nonce")
    assert (again.status, again.reason) == (foreign.status, foreign.reason)
    assert rc.finish_checkpoint(
        journey.repo, journey.coordination, journey.cursor,
        owner_nonce=NONCE, transaction_id="tx-none", payload=None,
    ) == journey.marker

# ---------------------------------------------------------------------------
# Two complete batches through the real control transitions
# ---------------------------------------------------------------------------


def _batch_a(journey: Journey) -> None:
    """Batch A: phases 1-3 with findings, a lesson, a new PR and one CI repair."""
    journey.start([BatchSegment(1, 3)])
    for phase in (1, 2, 3):
        content = journey.write_work_output(phase)
        request = journey.cursor_request("phase-boundary", journey.marker.revision + 1)
        correlated, transition = journey.run_stage(
            "work", phase=phase, effect=True, manifest=_sha(content),
            artifact_specs=[("report", ".cg-docs/work-reports/example.md", content)],
            cursor_requests=[request],
        )
        assert transition.next_stage == "prepare-publication"
        next_action = (
            f"/cg-work phase{phase + 1} review:none" if phase < 3
            else "/cg-commit-push-pr"
        )
        journey.checkpoint_cursor(next_action=next_action)
    journey.run_stage("prepare-publication")
    report_path = ".cg-docs/reviews/journey-review.md"
    review_content = (
        "---\nreport-type: review\nparent-report: journey-plan\n---\n"
        "# Review\n\nFindings present.\n"
    ).encode("utf-8")
    review_dir = journey.repo / ".cg-docs/reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    (journey.repo / report_path).write_bytes(review_content)
    journey.run_stage(
        "review", effect=True, findings=True,
        artifact_specs=[("review", report_path, review_content)],
    )
    # First triage: scoped question before any effect -> zero-effect release.
    reservation = journey.reserve("review-round", "batch-1")
    correlated, transition = journey.run_stage(
        "triage", status="needs-input", reservation_id=reservation,
        decision=journey.decision(options=("fix-all", "defer")),
    )
    assert transition.kind == "needs-input"
    assert journey.marker.reservations[-1].status == "released-no-effect"
    # Answered decision: mutating fix -> charged round.
    journey.known_approvals |= {"ans-fix-all"}
    reservation = journey.reserve("review-round", "batch-1")
    content = (journey.repo / "f.txt").read_bytes() + b"fix\n"
    (journey.repo / "f.txt").write_bytes(content)
    journey.run_stage(
        "triage", effect=True, reservation_id=reservation, manifest=_sha(content),
        approval_refs=("ans-fix-all",),
    )
    assert journey.marker.reservations[-1].status == "charged"
    journey.checkpoint_cursor(next_action="/cg-review mode:verify",
                              fold_reservation_ids=[reservation])
    journey.run_stage("prepare-publication")
    verify_content = (
        "---\nreport-type: verify-review\nparent-report: journey-plan\n---\n"
        "# Verify\n\nFixes verified.\n"
    ).encode("utf-8")
    verify_path = ".cg-docs/reviews/journey-verify-review.md"
    (journey.repo / verify_path).write_bytes(verify_content)
    verified = ev.verify_review_report(
        journey.repo, verify_path, expected_type="verify-review",
        expected_parent="journey-plan", budget=ev.AcquisitionBudget(),
    )
    assert verified.sha256 == _sha(verify_content)
    journey.run_stage("verify-review", effect=True, verify_context=True)
    lesson_content = b"# Lesson\n\nReusable knowledge.\n"
    (journey.repo / ".cg-docs/solutions").mkdir(parents=True, exist_ok=True)
    (journey.repo / ".cg-docs/solutions/lesson.md").write_bytes(lesson_content)
    journey.run_stage(
        "compound", effect=True,
        artifact_specs=[("lesson", ".cg-docs/solutions/lesson.md", lesson_content)],
        tests=[{"command-id": "cmd-1", "started-at": "2026-01-01T00:00:00Z",
                "ended-at": "2026-01-01T00:01:00Z", "scope-digest": SHA,
                "exit-status": 0, "result-ref": "tests/last-run.json",
                "status": "passed"}],
    )
    # Publish: the reviewed payload is committed and pushed by the stage child.
    before = journey.head()

    def publish_effects():
        journey.publish_child_effects()

    journey.run_stage("publish", effect=True, manifest=SHA, effects=publish_effects)
    assert journey.head() != before
    pr, kind = journey.ensure_pr()
    assert kind == "created"
    # verify-pr: CI fails once, repair round 1 fixes it, then green.
    journey.backend.set_checks(_fixture("status-check-failure.json"))
    assert journey.observe_ci().status == "diagnose"
    reservation = journey.reserve("ci-round", f"pr/{pr['number']}")
    assert journey.count_ci_rounds(pr["number"]) == 0

    def repair():
        journey.repair_commit(pr["number"], 1, journey.last_op)

    journey.backend.set_checks(_fixture("status-check-green.json"))
    journey.run_stage(
        "verify-pr", reservation_id=reservation, effect=True,
        manifest=SHA, effects=repair,
    )
    assert journey.marker.reservations[-1].status == "charged"
    assert journey.count_ci_rounds(pr["number"]) == 1
    assert journey.observe_ci().status == "eligible"
    journey.checkpoint_cursor(next_action="/cg-work phase4 review:none",
                              fold_reservation_ids=[reservation])


def test_batch_a_complete_flow_with_findings_lesson_and_ci_repair(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _batch_a(journey)
    assert journey.marker is not None
    assert journey.marker.in_flight_operation is None
    for reservation in journey.marker.reservations:
        assert reservation.status in ("charged", "released-no-effect")
    assert all(
        reservation.status == "charged" for reservation in journey.marker.reservations
        if reservation.scope == "ci-round"
    )
    assert len(journey.backend.create_calls) == 1
    assert journey.backend.create_calls[0][3] == "--base"
    assert journey.backend.create_calls[0][4] == BASE


def test_batch_b_complete_flow_without_findings_reusing_pr(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _batch_a(journey)
    journey.advance_plan(completed=(1, 2, 3), current=4)
    journey.previous_stage = None
    for phase in (4, 5, 6):
        content = journey.write_work_output(phase)
        journey.run_stage("work", phase=phase, effect=True, manifest=_sha(content))
        journey.checkpoint_cursor(next_action=f"/cg-work phase{phase + 1} review:none")
    journey.run_stage("prepare-publication")
    journey.run_stage("review", findings=False)
    correlated, transition = journey.run_stage("compound")
    assert transition.kind == "phase-4"
    assert transition.next_stage == "publish"

    def publish_effects():
        journey.publish_child_effects()

    journey.run_stage("publish", effect=True, manifest=SHA, effects=publish_effects)
    pr, kind = journey.ensure_pr()
    assert kind == "reused"
    assert len(journey.backend.create_calls) == 1
    journey.backend.set_checks(_fixture("status-check-green.json"))
    assert journey.observe_ci().status == "eligible"
    correlated, transition = journey.run_stage("verify-pr")
    assert transition.kind == "batch-complete"
    assert transition.next_stage is None
    assert sum(
        1 for reservation in journey.marker.reservations if reservation.scope == "ci-round"
    ) == 1
    assert journey.marker.deadline is None

# ---------------------------------------------------------------------------
# Child failure forms and missing native dispatch
# ---------------------------------------------------------------------------


def _started(journey: Journey) -> None:
    journey.start([BatchSegment(1, 3)])
    journey.write_work_output(1)


@pytest.mark.parametrize("status", ["failed", "blocked"])
def test_batch_stops_on_each_child_failure_form(tmp_path: Path, status: str) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    correlated, transition = journey.run_stage(
        "work", phase=1, effect=True, status=status, record=False
    )
    assert transition.kind == "stop"
    assert transition.next_stage is None
    assert transition.reason == status
    assert journey.marker.in_flight_operation is None


def test_malformed_or_forged_result_stops_without_fallback(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    operation_id = f"op-{journey.operation_counter + 1}"
    journey.dispatcher.script(operation_id, ("ses-x", b"{not json"))
    with pytest.raises(PacketError):
        journey.run_stage("work", phase=1, effect=True, forced_outcome=True)


def test_missing_native_child_stops_without_invented_result(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    operation_id = f"op-{journey.operation_counter + 1}"
    journey.dispatcher.script(
        operation_id, RuntimeError("native Task dispatch unavailable")
    )
    with pytest.raises(RuntimeError, match="Task"):
        journey.run_stage("work", phase=1, effect=True, forced_outcome=True)
    assert journey.marker.in_flight_operation is None
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "noop-complete"


def test_child_disappearing_before_return_blocks_resume(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    reservation = journey.reserve("review-round", "batch-1")
    # begin the stage and its one-way effect, then the child vanishes: no result.
    operation_id = f"op-{journey.operation_counter + 1}"
    journey.marker = st.begin_stage(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        operation_id=operation_id, reservation_id=reservation,
    )
    ck.begin_effect(journey.coordination, operation_id,
                    recorded_at="2026-01-01T00:00:00Z")
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "interrupted-effect"
    with pytest.raises(StateError, match="unsettled-operation"):
        journey.checkpoint_cursor(next_action="/cg-work phase2 review:none")


# ---------------------------------------------------------------------------
# Legacy work cursor-write points and lost writes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("event_kind", ["report-created", "phase-boundary", "blocked-stop"])
def test_legacy_work_cursor_write_points_are_requests_not_bytes(
    tmp_path: Path, event_kind: str
) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    content = journey.write_work_output(1)
    request = journey.cursor_request(event_kind, journey.marker.revision + 1)
    correlated, transition = journey.run_stage(
        "work", phase=1, effect=True, manifest=_sha(content),
        cursor_requests=[request],
    )
    assert correlated.result.cursor_update_requests[0].event_kind == event_kind
    assert journey.marker.revision == 0
    journey.checkpoint_cursor(
        next_action=("/cg-work phase2 review:none" if event_kind != "blocked-stop"
                     else "/cg-autopilot --resume .cg-docs/active-state/current.json")
    )
    assert journey.marker.revision == 1
    cursor = recs.validate_cursor_record(journey.cursor.read_bytes())
    assert cursor["autopilot"]["run-id"] == RUN


def test_direct_child_cursor_write_preserves_foreign_bytes(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    journey.cursor.write_bytes(b"forged child cursor bytes")
    with pytest.raises(StateError, match="cursor-changed"):
        journey.checkpoint_cursor(next_action="/cg-work phase2 review:none")
    assert journey.cursor.read_bytes() == b"forged child cursor bytes"
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "blocked"


def test_lost_result_receipt_keeps_operation_unsettled(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    reservation = journey.reserve("review-round", "batch-1")
    operation_id = f"op-{journey.operation_counter + 1}"
    journey.marker = st.begin_stage(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        operation_id=operation_id, reservation_id=reservation,
    )
    ck.begin_effect(journey.coordination, operation_id,
                    recorded_at="2026-01-01T00:00:00Z")
    raw = journey.result_bytes("triage", "needs-input", operation_id,
                               decision=journey.decision())
    ck.record_result(journey.coordination, operation_id, raw)
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "unacknowledged-result"
    result = StageResult.parse(raw)
    journey.marker = st.settle_stage(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        operation_id=operation_id, outcome="released-no-effect",
        evidence_refs=("tests/last-run.json",),
    )
    assert journey.marker.in_flight_operation is None
    assert result.status == "needs-input"


def test_checkpoint_interruption_before_publish_then_recovery_republishes(
    tmp_path: Path,
) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    payload = ck.build_cursor_record(
        run_id=RUN, revision=1, worktree=str(journey.repo), branch=BRANCH,
        required_base=BASE, plan_digest=journey.plan.digest,
        next_action="/cg-work phase2 review:none",
        updated_at="2026-01-01T00:00:00Z",
    )

    def crash(_path: Path) -> None:
        raise OSError("injected crash before cursor publish")

    with pytest.raises(OSError, match="injected crash"):
        ck.checkpoint(
            journey.marker, journey.coordination, journey.cursor, payload,
            owner_nonce=NONCE, fold_reservation_ids=(), transaction_id="tx-1",
            before_publish=crash,
        )
    marker = st.load_marker(journey.coordination)
    assert marker.transaction is not None
    recovered = rc.finish_checkpoint(
        journey.repo, journey.coordination, journey.cursor,
        owner_nonce=NONCE, transaction_id="tx-1", payload=payload,
    )
    assert recovered.revision == 1
    assert recovered.transaction is None
    again = rc.finish_checkpoint(
        journey.repo, journey.coordination, journey.cursor,
        owner_nonce=NONCE, transaction_id="tx-1", payload=None,
    )
    assert again == recovered and again.revision == 1
    assert recs.validate_cursor_record(journey.cursor.read_bytes())["autopilot"]["revision"] == 1


def test_unknown_writer_blocks_without_takeover(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    own = st.load_marker(journey.coordination)
    from dataclasses import replace
    from autopilot import records

    foreign = replace(own, run_id="run-other", owner_nonce="nonce-other")
    secure_fs.secure_write_bytes(
        journey.coordination, PurePosixPath("marker.json"),
        records.marker_to_bytes(foreign),
        expected_state=ExpectedFileState.from_bytes(records.marker_to_bytes(own)),
    )
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "foreign-owner"
    loaded = st.load_marker(journey.coordination)
    assert loaded.owner_nonce == "nonce-other"
    with pytest.raises(StateError, match="foreign-owner"):
        st.reserve(loaded, journey.coordination, owner_nonce=NONCE,
                   scope="review-round", key="batch-1", reservation_id="res-x")
    with pytest.raises(StateError, match="foreign-owner"):
        ck.checkpoint(
            loaded, journey.coordination, journey.cursor,
            ck.build_cursor_record(
                run_id="run-other", revision=1, worktree=str(journey.repo),
                branch=BRANCH, required_base=BASE, plan_digest=_sha(b"p"),
                next_action="/cg-work phase2 review:none",
                updated_at="2026-01-01T00:00:00Z",
            ),
            owner_nonce=NONCE, fold_reservation_ids=(), transaction_id="tx-x",
        )

# ---------------------------------------------------------------------------
# Repeated zero-effect approvals versus partial-effect yield
# ---------------------------------------------------------------------------


def test_repeated_zero_effect_approvals_never_consume_repair_rounds(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    for _ in range(3):
        reservation = journey.reserve("review-round", "batch-1")
        journey.run_stage(
            "triage", status="needs-input", reservation_id=reservation,
            decision=journey.decision(request_id=f"req-{journey.reservation_counter}"),
        )
    assert journey.marker.reservations[-1].status == "released-no-effect"
    charged = [
        r for r in journey.marker.reservations
        if r.scope == "review-round" and r.status != "released-no-effect"
    ]
    assert charged == []
    # The cap counts charged attempts only: a fourth reservation still works.
    reservation = journey.reserve("review-round", "batch-1")
    assert reservation


def test_partial_effect_yield_charges_and_second_round_exhausts(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    # Round 1: a fix was written but the child then asks a question.
    reservation = journey.reserve("review-round", "batch-1")
    journey.run_stage(
        "triage", status="needs-input", effect=True, manifest=SHA,
        reservation_id=reservation,
        decision=journey.decision(request_id="req-1"),
    )
    assert journey.marker.reservations[-1].status == "charged"
    # Round 2: the answered fix fails before commit.
    journey.known_approvals |= {"ans-2"}
    reservation = journey.reserve("review-round", "batch-1")
    journey.run_stage(
        "triage", status="failed", effect=True, reservation_id=reservation,
        approval_refs=("ans-2",), record=False, settle=False,
    )
    journey.marker = st.settle_stage(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        operation_id=journey.last_op, outcome="uncertain",
    )
    assert journey.marker.reservations[-1].status == "uncertain"
    # A third charged attempt is refused: reservations are never refunded.
    with pytest.raises(StateError, match="reservation-exhausted"):
        journey.reserve("review-round", "batch-1")


# ---------------------------------------------------------------------------
# Publication: existing/new PR, wrong base, drift and re-review
# ---------------------------------------------------------------------------


def test_dirty_tree_blocks_publication_until_committed(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    content = journey.write_work_output(1)
    state = journey.observe_publication()
    assert state.state == "dirty"
    journey.publish_child_effects()
    assert journey.observe_publication().state == "pushed-no-pr"


def test_existing_matching_pr_is_reused_never_duplicated(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.backend.set_pr({
        "url": "https://github.com/o/r/pull/7", "number": 7, "title": "t",
        "state": "OPEN", "baseRefName": BASE, "headRefName": BRANCH,
        "headRefOid": "b" * 40,
    })
    journey.start([BatchSegment(1, 3)])
    journey.write_work_output(1)
    journey.publish_child_effects()
    pr, kind = journey.ensure_pr()
    assert kind == "reused"
    assert pr.number == 7
    assert journey.backend.create_calls == []


def test_wrong_base_conflict_blocks_never_silently_adopts(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.backend.set_pr({
        "url": "https://github.com/o/r/pull/9", "number": 9, "title": "t",
        "state": "OPEN", "baseRefName": "main", "headRefName": BRANCH,
        "headRefOid": "b" * 40,
    })
    journey.start([BatchSegment(1, 3)])
    journey.write_work_output(1)
    journey.publish_child_effects()
    with pytest.raises(q.QueryError, match="base-conflict"):
        journey.ensure_pr()
    assert journey.backend.create_calls == []


def test_closed_pr_blocks_duplicate_creation(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.backend.set_pr({
        "url": "https://github.com/o/r/pull/3", "number": 3, "title": "t",
        "state": "MERGED", "baseRefName": BASE, "headRefName": BRANCH,
        "headRefOid": "b" * 40,
    })
    journey.start([BatchSegment(1, 3)])
    journey.write_work_output(1)
    journey.publish_child_effects()
    with pytest.raises(q.QueryError, match="pr-closed"):
        journey.ensure_pr()


def test_generation_drift_invalidates_intent_and_forces_re_review(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    content = journey.write_work_output(1)
    journey.run_stage("work", phase=1, effect=True, manifest=_sha(content))
    journey.checkpoint_cursor(next_action="/cg-commit-push-pr")
    journey.run_stage("prepare-publication")
    reviewed = journey.coverage_of_reviewed_payload()
    journey.run_stage("review", findings=False)
    journey.run_stage("compound")
    # Regeneration produced a different inventory: drift blocks before commit.
    actual = q.coverage_of([
        q.PathIdentity("f.txt", "present", "d" * 64, 5),
        q.PathIdentity(".cg-docs/work-reports/example.md", "present",
                       _sha(content), len(content)),
    ])
    drifted = q.coverage_drift(reviewed, actual)
    assert drifted == ("f.txt",)
    head_before = journey.head()
    assert journey.observe_publication().state == "dirty"
    # Route through preparation and affected review before a new intent.
    journey.run_stage("prepare-publication")
    journey.run_stage("verify-review", effect=True, verify_context=True)
    reviewed_again = q.coverage_of([
        q.PathIdentity("f.txt", "present", "d" * 64, 5),
        q.PathIdentity(".cg-docs/work-reports/example.md", "present",
                       _sha(content), len(content)),
    ])
    assert q.idempotent(reviewed_again, actual)
    journey.run_stage("compound")
    journey.run_stage("publish", effect=True, manifest=SHA,
                      effects=journey.publish_child_effects)
    assert journey.head() != head_before
    assert journey.ensure_pr()[1] == "created"


def test_repeated_generation_drift_with_unchanged_inputs_blocks(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    journey.publish_child_effects()
    expected = q.coverage_of([q.PathIdentity("f.txt", "present", "d" * 64, 5)])
    first = q.coverage_drift(
        expected,
        q.coverage_of([q.PathIdentity("f.txt", "present", "e" * 64, 5)]),
    )
    second = q.coverage_drift(
        expected,
        q.coverage_of([q.PathIdentity("f.txt", "present", "e" * 64, 5)]),
    )
    assert first == ("f.txt",)
    assert second == first
    assert q.coverage_drift(expected, expected) == ()


# ---------------------------------------------------------------------------
# CI: pending, failure, timeout, approved extension, rerun, third round
# ---------------------------------------------------------------------------


def _pr_ready(journey: Journey, *, green: bool = True) -> dict:
    journey.start([BatchSegment(1, 3)])
    journey.write_work_output(1)
    journey.publish_child_effects()
    pr, _kind = journey.ensure_pr()
    journey.previous_stage = "publish"
    journey.backend.set_checks(
        _fixture("status-check-green.json") if green
        else _fixture("status-check-failure.json")
    )
    return pr


def test_pending_waits_and_never_counts_as_success(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _pr_ready(journey)
    journey.backend.set_checks(_fixture("status-check-pending.json"))
    observation = journey.observe_ci()
    assert observation.status == "wait"
    assert observation.reason == "pending"
    assert observation.counts["success"] == 1


def test_failure_diagnosis_yields_exact_failed_identity(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _pr_ready(journey)
    journey.backend.set_checks(_fixture("status-check-failure.json"))
    observation = journey.observe_ci()
    assert observation.status == "diagnose"
    assert observation.failing[0].name == "ci-tests"
    job = ci.parse_job_url(observation.failing[0].details_url)
    assert (job.run_id, job.job_id) == ("1001", "2001")


def test_timeout_uses_exact_identity_and_redacts_diagnostics(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _pr_ready(journey)
    journey.backend.set_checks(_fixture("status-check-timeout.json"))
    journey.backend.log_bytes = (
        b"ghp_" + b"f" * 36 + b" leaked token\nBearer abc\nnormal output\n"
        + b"x" * 9000
    )
    observation = journey.observe_ci()
    assert observation.status == "diagnose"
    assert observation.failing[0].conclusion == "TIMED_OUT"
    job = ci.parse_job_url(observation.failing[0].details_url)
    diagnostic = ci.bound_diagnostic(job, journey.backend.log_bytes)
    assert diagnostic.truncated
    assert b"ghp_" + b"f" * 36 not in diagnostic.redacted
    assert b"Bearer abc" not in diagnostic.redacted
    assert b"normal output" in diagnostic.redacted
    assert len(diagnostic.redacted) <= ci.MAX_DIAGNOSTIC_BYTES


def test_approved_extension_changes_only_the_deadline(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    pr = _pr_ready(journey)
    original = "2026-09-15T10:00:00Z"
    journey.marker = rc.record_ci_deadline(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        original_deadline=original, scope_hash=_sha(f"pr/{pr['number']}".encode()),
    )
    reservations_before = journey.marker.reservations
    journey.marker = rc.extend_ci_deadline(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        request_id="ext-1", duration_seconds=1800, approval_ref="approval-1",
        scope_hash=_sha(f"pr/{pr['number']}".encode()),
        application_time="2026-09-15T10:20:00Z",
    )
    deadline = journey.marker.deadline
    assert deadline["original-deadline"] == original
    assert deadline["effective-deadline"] == "2026-09-15T10:50:00Z"
    assert deadline["history"][0]["old-deadline"] == original
    assert journey.marker.reservations == reservations_before
    assert journey.marker.in_flight_operation is None
    replay = rc.extend_ci_deadline(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        request_id="ext-1", duration_seconds=1800, approval_ref="approval-1",
        scope_hash=_sha(f"pr/{pr['number']}".encode()),
        application_time="2026-09-15T10:20:00Z",
    )
    assert replay.deadline == deadline


def test_lost_extension_acknowledgement_replays_without_double_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = Journey.setup(tmp_path)
    pr = _pr_ready(journey)
    original = "2026-09-15T10:00:00Z"
    journey.marker = rc.record_ci_deadline(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        original_deadline=original, scope_hash=_sha(f"pr/{pr['number']}".encode()),
    )
    original_write = secure_fs.secure_write_bytes
    calls = {"count": 0}

    def fail_marker_write(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("injected crash before extension acknowledgement")
        return original_write(*args, **kwargs)

    monkeypatch.setattr(secure_fs, "secure_write_bytes", fail_marker_write)
    with pytest.raises(OSError, match="injected crash"):
        rc.extend_ci_deadline(
            journey.marker, journey.coordination, owner_nonce=NONCE,
            request_id="ext-lost", duration_seconds=1800,
            approval_ref="approval-1",
            scope_hash=_sha(f"pr/{pr['number']}".encode()),
            application_time="2026-09-15T10:20:00Z",
        )
    monkeypatch.setattr(secure_fs, "secure_write_bytes", original_write)
    loaded = st.load_marker(journey.coordination)
    assert loaded.deadline["effective-deadline"] == original
    assert loaded.deadline["request-id"] is None
    journey.marker = rc.extend_ci_deadline(
        loaded, journey.coordination, owner_nonce=NONCE,
        request_id="ext-lost", duration_seconds=1800, approval_ref="approval-1",
        scope_hash=_sha(f"pr/{pr['number']}".encode()),
        application_time="2026-09-15T10:20:00Z",
    )
    assert journey.marker.deadline["effective-deadline"] == "2026-09-15T10:50:00Z"
    assert len(journey.marker.deadline["history"]) == 1


def test_extension_requires_observation_scope_and_settled_writer(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _pr_ready(journey)
    with pytest.raises(StateError, match="no-observation"):
        rc.extend_ci_deadline(
            journey.marker, journey.coordination, owner_nonce=NONCE,
            request_id="ext-1", duration_seconds=60, approval_ref="a",
            scope_hash=SHA, application_time="2026-09-15T10:20:00Z",
        )
    journey.marker = rc.record_ci_deadline(
        journey.marker, journey.coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T10:00:00Z", scope_hash=SHA,
    )
    with pytest.raises(StateError, match="deadline-scope-changed"):
        rc.extend_ci_deadline(
            journey.marker, journey.coordination, owner_nonce=NONCE,
            request_id="ext-2", duration_seconds=60, approval_ref="a",
            scope_hash=_sha(b"other-scope"), application_time="2026-09-15T10:20:00Z",
        )
    with pytest.raises(StateError, match="clock-rollback"):
        rc.extend_ci_deadline(
            journey.marker, journey.coordination, owner_nonce=NONCE,
            request_id="ext-3", duration_seconds=1, approval_ref="a",
            scope_hash=SHA, application_time="2026-09-15T09:59:59Z",
        )


def test_cancelled_check_requires_one_approved_rerun_only(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _pr_ready(journey)
    cancelled_page = [
        {"__typename": "CheckRun", "name": name,
         "status": "COMPLETED", "conclusion": "SUCCESS", "detailsUrl": None}
        for name in REQUIRED_CONTEXTS
    ] + [{"__typename": "CheckRun", "name": "ci-tests", "status": "COMPLETED",
          "conclusion": "CANCELLED", "detailsUrl": None}]
    journey.backend.set_checks(cancelled_page)
    assert journey.observe_ci().reason == "cancelled"
    assert ci.RERUNS_PER_BATCH == 1
    reruns = 0

    def approved_rerun():
        nonlocal reruns
        reruns += 1
        assert reruns <= ci.RERUNS_PER_BATCH

    approved_rerun()
    checks = []
    for page in journey.backend.checks_pages:
        checks.extend(q.normalize_rollup(page, "rollup"))
    merged = ci.merged_checks([checks])
    observation = ci.classify_observation(
        merged, required=[ci.RequiredContext(name, None)
                          for name in REQUIRED_CONTEXTS],
        cancelled_rerun_approved=frozenset({"ci-tests"}),
    )
    # Approval alone never redeems: the observation still carries no same-name
    # SUCCESS check for ci-tests, so the cancelled check stays a blocker.
    assert observation.status == "block"
    assert observation.reason == "cancelled"

    # The approved rerun finishes green: the same-name SUCCESS in the new
    # observation redeems the earlier cancellation.
    green_page = [
        {"__typename": "CheckRun", "name": name,
         "status": "COMPLETED", "conclusion": "SUCCESS", "detailsUrl": None}
        for name in REQUIRED_CONTEXTS
    ] + [{"__typename": "CheckRun", "name": "ci-tests",
          "status": "COMPLETED", "conclusion": "SUCCESS", "detailsUrl": None}]
    journey.backend.set_checks(green_page)
    checks = []
    for page in journey.backend.checks_pages:
        checks.extend(q.normalize_rollup(page, "rollup"))
    merged = ci.merged_checks([checks])
    observation = ci.classify_observation(
        merged, required=[ci.RequiredContext(name, None)
                          for name in REQUIRED_CONTEXTS],
        cancelled_rerun_approved=frozenset({"ci-tests"}),
    )
    assert observation.status == "eligible"
    with pytest.raises(AssertionError):
        approved_rerun()


def test_third_ci_round_is_refused_across_batches(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    pr = _pr_ready(journey)
    key = f"pr/{pr['number']}"
    first = journey.reserve("ci-round", key)
    journey.run_stage("verify-pr", reservation_id=first, effect=True,
                      manifest=SHA, effects=lambda: journey.repair_commit(pr["number"], 1, journey.last_op))
    assert journey.count_ci_rounds(pr["number"]) == 1
    second = journey.reserve("ci-round", key)
    journey.previous_stage = "publish"
    journey.run_stage("verify-pr", reservation_id=second, effect=True,
                      manifest=SHA, effects=lambda: journey.repair_commit(pr["number"], 2, journey.last_op))
    assert journey.count_ci_rounds(pr["number"]) == 2
    with pytest.raises(StateError, match="reservation-exhausted"):
        journey.reserve("ci-round", key)


def test_repair_commit_without_trailer_does_not_count_as_a_round(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    pr = _pr_ready(journey)
    reservation = journey.reserve("ci-round", f"pr/{pr['number']}")

    def untrailed_repair():
        (journey.repo / "fix.txt").write_text("untrailed\n", encoding="utf-8")
        journey.publish_child_effects(message="fix(ci): untrailed repair")

    journey.run_stage("verify-pr", reservation_id=reservation, effect=True,
                      manifest=SHA, effects=untrailed_repair)
    assert journey.count_ci_rounds(pr["number"]) == 0


def test_failed_push_or_commit_still_charges_the_reserved_round(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    pr = _pr_ready(journey)
    reservation = journey.reserve("ci-round", f"pr/{pr['number']}")

    def failing_repair():
        raise JourneyError("push rejected: non-fast-forward")

    with pytest.raises(JourneyError, match="non-fast-forward"):
        journey.run_stage("verify-pr", reservation_id=reservation, effect=True,
                          manifest=SHA, effects=failing_repair)
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "interrupted-effect"


def test_pushed_remote_ahead_blocks_observation(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _pr_ready(journey)
    _real_git(journey.repo, "reset", "-q", "--hard", "HEAD~1")
    with pytest.raises(q.QueryError, match="remote-ahead"):
        journey.observe_publication()

# ---------------------------------------------------------------------------
# Consumer repair without a local scripts directory
# ---------------------------------------------------------------------------


def test_no_local_scripts_consumer_repair_uses_consumer_command_only(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    routing = journey.project_index()
    assert routing.kind == "consumer"
    assert routing.evidence == ()
    journey.write_work_output(1)
    journey.publish_child_effects()
    pr, _kind = journey.ensure_pr()
    journey.backend.set_checks(_fixture("status-check-failure.json"))
    observation = journey.observe_ci()
    assert observation.status == "diagnose"
    failing = observation.failing[0]
    job = ci.parse_job_url(failing.details_url)
    assert failing.name == "ci-tests"
    consumer_command = ("pytest", "tests/consumer/test_damage.py")
    consumed = {"runs": 0}

    def consumer_run():
        consumed["runs"] += 1
        return {
            "command-id": "consumer-cmd", "started-at": "2026-01-01T00:00:00Z",
            "ended-at": "2026-01-01T00:01:00Z", "scope-digest": SHA,
            "exit-status": 0, "result-ref": "tests/last-run.json",
            "status": "passed",
        }

    assert consumed["runs"] == 0
    consumer_run()
    assert consumed["runs"] == 1
    for command, _envelope in journey.dispatcher.calls:
        assert "scripts/" not in command
    assert job.run_id == "1001"
    assert consumer_command[0] == "pytest"


def test_consumer_repair_never_selects_source_test_inventory(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    routing = journey.project_index()
    assert routing.kind == "consumer"
    assert journey.git.calls
    assert all(
        str(cwd) == str(journey.repo) for _argv, cwd in journey.git.calls
    )
    outcome = journey.git(("git", "ls-files", "scripts/tests/"))
    assert outcome.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Whole-document input limits and changed source/commands/config
# ---------------------------------------------------------------------------


def test_oversized_plan_input_stops_before_parsing(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    plan_file = journey.repo / PLAN_REL
    plan_file.write_bytes(b"# Plan\n\n" + b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(PlanError, match="plan-too-large"):
        plan_mod.read_plan(journey.repo, PLAN_REL)


def test_aggregate_evidence_budget_exhaustion_blocks_validation(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    budget = ev.AcquisitionBudget(limit=128)
    (journey.repo / "small-a.md").write_bytes(b"a" * 100)
    (journey.repo / "small-b.md").write_bytes(b"b" * 100)
    ev.acquire_document(journey.repo, "small-a.md", kind="plan", budget=budget)
    with pytest.raises(EvidenceError, match="budget"):
        ev.acquire_document(journey.repo, "small-b.md", kind="plan", budget=budget)


def test_plan_body_change_blocks_batch_continuation(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    old_source = journey.plan.source
    journey.write_plan(completed=(1, 2, 3), current=4, extra="\n# Injected section\nBody changed.\n")
    new_source = (journey.repo / PLAN_REL).read_text(encoding="utf-8")
    with pytest.raises(PlanError, match="plan-body-changed"):
        plan_mod.progress_delta(old_source, new_source)


def test_changed_installed_contract_blocks_stale_envelope(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    stale = journey.envelope("work", "op-1")
    contract = journey.repo / CONTRACT_REL
    contract.write_bytes(b"# Autopilot Stage Contract\n\nContract version: 2.\n")
    with pytest.raises(pl.PipelineError, match="installed-identity-changed"):
        journey.guard_installed_identity(stale)


def test_changed_consumer_config_invalidates_spec_and_rerun_digest(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    spec = (journey.repo / "tests/consumer/consumer-spec.json")
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({"command": ["pytest", "tests/consumer/test_x.py"]}),
                    encoding="utf-8")
    before = _sha(spec.read_bytes())
    spec.write_text(json.dumps({"command": ["pytest", "tests/consumer/test_y.py"]}),
                    encoding="utf-8")
    after = _sha(spec.read_bytes())
    assert before != after
    outcome = _real_git(journey.repo, "add", "-A")
    assert outcome.returncode == 0


# ---------------------------------------------------------------------------
# Context exhaustion and pause recovery
# ---------------------------------------------------------------------------


def test_context_exhaustion_pauses_before_dispatch_and_resumes(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    journey.start([BatchSegment(1, 3)])
    journey.budget = cx.ParentContextBudget(used=cx.CONTEXT_ALLOWANCE_BYTES - 200)
    journey.write_work_output(1)
    with pytest.raises(pl.PipelineError, match="context-pause"):
        journey.run_stage("work", phase=1, effect=True)
    assert journey.marker.in_flight_operation is None
    frame = cx.measure_frame(b"{}", metadata={"child-id": "ses-x"})
    decision = cx.budget_decision(frame, journey.budget)
    assert decision["reason"] in ("context-budget-exhausted", "within-budget")
    fresh = cx.ParentContextBudget()
    assert fresh.used == 0
    journey.budget = fresh
    content = journey.write_work_output(1)
    correlated, transition = journey.run_stage("work", phase=1, effect=True,
                                               manifest=_sha(content))
    assert transition.next_stage == "prepare-publication"
    assert journey.marker.in_flight_operation is None
    assert journey.marker.reservations == ()


def test_context_pause_never_truncates_and_marker_state_survives(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _started(journey)
    reservation = journey.reserve("review-round", "batch-1")
    journey.budget = cx.ParentContextBudget(used=cx.CONTEXT_ALLOWANCE_BYTES - 10)
    with pytest.raises(pl.PipelineError, match="context-pause"):
        journey.run_stage("triage", reservation_id=reservation, status="needs-input",
                          decision=journey.decision())
    loaded = st.load_marker(journey.coordination)
    assert loaded.reservations[-1].status == "pending"
    assert loaded.revision == 0
    assert loaded.in_flight_operation is not None
    reconciliation = rc.reconcile(journey.repo, journey.coordination, journey.cursor,
                                  owner_nonce=NONCE)
    assert reconciliation.status == "blocked"
    journey.marker = st.settle_stage(
        loaded, journey.coordination, owner_nonce=NONCE,
        operation_id=loaded.in_flight_operation, outcome="released-no-effect",
        evidence_refs=("tests/last-run.json",),
    )
    assert journey.marker.reservations[-1].status == "released-no-effect"
    reservation = journey.reserve("review-round", "batch-1")
    journey.budget = cx.ParentContextBudget()
    journey.run_stage("triage", reservation_id=reservation, status="needs-input",
                      decision=journey.decision())
    assert journey.marker.reservations[-1].status == "released-no-effect"


# ---------------------------------------------------------------------------
# Fixture safety: no live network or destructive operation reaches a real checkout
# ---------------------------------------------------------------------------


def test_journeys_never_touch_a_real_checkout(tmp_path: Path) -> None:
    real_repo = Path(__file__).resolve().parents[2]
    head_before = _real_git(real_repo, "rev-parse", "HEAD").stdout.strip()
    status_before = _real_git(real_repo, "status", "--porcelain").stdout
    journey = Journey.setup(tmp_path)
    _batch_a(journey)
    assert _real_git(real_repo, "rev-parse", "HEAD").stdout.strip() == head_before
    assert _real_git(real_repo, "status", "--porcelain").stdout == status_before
    assert all(cwd == str(journey.repo) for _argv, cwd in journey.git.calls)
    for argv, _cwd in journey.git.calls:
        assert str(real_repo) not in str(argv)


def test_gh_effects_never_reach_a_network(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _batch_a(journey)
    assert journey.backend.view_calls
    for argv in journey.backend.view_calls:
        assert argv[0:3] == ("gh", "pr", "view")
    with pytest.raises(AssertionError, match="unscripted"):
        journey.backend.run(("gh", "api", "repos/o/r"))
    assert all(argv[0] == "gh" for argv in journey.backend.create_calls)


def test_all_control_writes_stay_inside_the_temp_repository(tmp_path: Path) -> None:
    journey = Journey.setup(tmp_path)
    _batch_a(journey)
    assert journey.coordination.is_relative_to(journey.repo / ".git")
    assert journey.cursor.is_relative_to(journey.repo)
    for artifact in (journey.coordination / "marker.json",
                     journey.coordination / "operations" / "receipts"):
        assert artifact.is_relative_to(journey.repo)
    assert str(tmp_path) not in str(Path(__file__).resolve())
