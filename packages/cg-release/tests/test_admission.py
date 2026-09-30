"""Offline portable-locator and durable-inbox failure boundaries."""

import base64
import json
from pathlib import Path

import pytest

from cg_release.admission import Locator, discover, submit
from cg_release.events import ControllerError, emit_event
from cg_release.models import Event, Request, canonical_bytes, load_record


@pytest.fixture
def release_request() -> Request:
    """Return the strict immutable request fixture, not an admission grant."""
    return load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )


class Inbox:
    """Model remote acceptance independently of the create response."""

    def __init__(self, request: Request, *, lost: bool = False, accepted: bool = True):
        self.request = request
        self.lost, self.accepted = lost, accepted
        self.issues = []
        self.writes = 0
        self.read_failure = False

    def create(self, locator: str, body: bytes) -> None:
        self.writes += 1
        if self.accepted:
            self.issues.append(
                {
                    "number": 7,
                    "node_id": "I_fixture",
                    "body": body.decode(),
                    "author_id": self.request.requester_id,
                    "repository_id": self.request.repository_id,
                    "last_edited_at": None,
                    "edit_count": 0,
                    "url": f"https://{self.request.host}/{self.request.repository_slug}/issues/7",
                }
            )
        if self.lost:
            raise ControllerError("E_TIMEOUT", "Response lost.")

    def inventory(self, locator: Locator) -> list[dict]:
        if self.read_failure:
            raise ControllerError("E_FORBIDDEN", "Cannot establish absence.")
        return list(self.issues)


def test_locator_roundtrips_without_local_state(release_request: Request) -> None:
    request = release_request
    locator = Locator.from_request(request)
    encoded = locator.encode()
    assert encoded.startswith("rc1.")
    assert Locator.decode(encoded) == locator
    assert locator.proposal_digest == request.proposal_digest
    assert "version" not in json.loads(base64.urlsafe_b64decode(encoded[4:] + "=="))


@pytest.mark.parametrize(
    "value", ["", "rc2.e30", "rc1.e30", "rc1.!!!!", "rc1." + "a" * 4096]
)
def test_locator_rejects_invalid_encoding_and_schema(value: str) -> None:
    with pytest.raises(ControllerError, match="locator"):
        Locator.decode(value)


def test_locator_rejects_noncanonical_and_duplicate_keys(
    release_request: Request,
) -> None:
    request = release_request
    raw = canonical_bytes(Locator.from_request(request))
    for invalid in (b" " + raw, raw.replace(b"{", b'{"host":"evil.test",', 1)):
        value = "rc1." + base64.urlsafe_b64encode(invalid).decode().rstrip("=")
        with pytest.raises(ControllerError):
            Locator.decode(value)


@pytest.mark.parametrize("lost", [False, True])
def test_intent_precedes_write_and_lost_acceptance_reconciles(
    release_request: Request, lost: bool
) -> None:
    request = release_request
    inbox = Inbox(request, lost=lost)
    events = []

    def emit(event):
        if event.kind == "submission-intent":
            assert inbox.writes == 0
        events.append(event)

    receipt = submit(request, inbox, emit)
    assert inbox.writes == 1
    assert receipt.number == 7
    assert [e.kind for e in events] == ["submission-intent", "receipt"]
    assert events[-1].observed == "queued"
    assert discover(events[0].request_id, inbox) == receipt


@pytest.mark.parametrize("read_failure", [False, True])
def test_uncertain_submission_retains_locator_and_never_retries(
    release_request: Request, read_failure: bool
) -> None:
    request = release_request
    inbox = Inbox(request, lost=True, accepted=False)
    inbox.read_failure = read_failure
    events = []
    with pytest.raises(ControllerError) as caught:
        submit(request, inbox, events.append)
    assert caught.value.code == "E_SUBMISSION_UNKNOWN"
    assert inbox.writes == 1
    assert [event.kind for event in events] == ["submission-intent"]
    assert Locator.decode(events[0].request_id).nonce == request.nonce
    with pytest.raises(ControllerError):
        discover(events[0].request_id, inbox)
    assert inbox.writes == 1


@pytest.mark.parametrize(
    "mutation",
    [
        {"last_edited_at": "2026-09-11T00:00:00Z"},
        {"edit_count": 1},
        {"author_id": 999},
        {"repository_id": 999},
        {"edit_count": None},
        {"url": "https://evil.test/issue"},
        {"number": True},
        {"created_at": "not-a-date"},
    ],
)
def test_untrusted_receipts_fail_closed(
    release_request: Request, mutation: dict
) -> None:
    request = release_request
    inbox = Inbox(request)
    receipt = submit(request, inbox, lambda event: None)
    inbox.issues[0].update(mutation)
    with pytest.raises(ControllerError):
        discover(receipt.request_id, inbox)


def test_ambiguous_nonce_and_changed_digest_are_conflicts(
    release_request: Request,
) -> None:
    request = release_request
    inbox = Inbox(request)
    receipt = submit(request, inbox, lambda event: None)
    inbox.issues.append(
        {
            **inbox.issues[0],
            "number": 8,
            "node_id": "I_other",
            "url": f"https://{request.host}/{request.repository_slug}/issues/8",
        }
    )
    with pytest.raises(ControllerError) as caught:
        discover(receipt.request_id, inbox)
    assert caught.value.code == "E_REQUEST_CONFLICT"
    inbox.issues.pop()
    body = json.loads(inbox.issues[0]["body"])
    body["request"]["proposal_digest"] = "f" * 64
    inbox.issues[0]["body"] = json.dumps(body)
    with pytest.raises(ControllerError):
        discover(receipt.request_id, inbox)


def test_submit_rejects_changed_request_fields_even_with_same_locator(
    release_request: Request,
) -> None:
    inbox = Inbox(release_request)
    create = inbox.create

    def changed(locator: str, raw: bytes) -> None:
        body = json.loads(raw)
        body["request"]["source_sha"] = "f" * 40
        create(locator, json.dumps(body).encode())

    inbox.create = changed
    with pytest.raises(ControllerError) as caught:
        submit(release_request, inbox, lambda event: None)
    assert caught.value.code == "E_REQUEST_CONFLICT"


def test_human_intent_displays_portable_locator_before_write(
    release_request: Request,
    capsys: pytest.CaptureFixture,
) -> None:
    locator = Locator.from_request(release_request).encode()
    emit_event(
        Event(
            kind="submission-intent",
            request_id=locator,
            message="Provisional identity, not queued.",
        ),
        json_output=False,
    )
    assert locator in capsys.readouterr().out
