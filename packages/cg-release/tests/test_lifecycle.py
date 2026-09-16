"""Admission must revalidate full confirmed inputs before reserving any identity."""

from pathlib import Path

import pytest
from journal_store import MemoryStore

from cg_release.admission import Locator, Receipt
from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.lifecycle import seal
from cg_release.models import Request, load_record


def receipt_fixture():
    request = load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )
    return Receipt(
        request_id=Locator.from_request(request).encode(),
        number=1,
        node_id="I_1",
        url="https://github.com/example/generic/issues/1",
        request=request,
    )


def test_seal_rechecks_before_atomic_admission_and_duplicate_wakeup_is_idempotent():
    journal = Journal(MemoryStore())
    receipt = receipt_fixture()
    reads = []
    seal(receipt, journal, lambda request: reads.append(request))
    seal(receipt, journal, lambda request: reads.append(request))
    assert len(journal.records()) == 1 and len(reads) == 1


def test_stale_inputs_or_actor_role_do_not_reserve():
    journal = Journal(MemoryStore())

    def stale(request):
        raise ControllerError("E_STALE_PROPOSAL", "Source changed.")

    with pytest.raises(ControllerError):
        seal(receipt_fixture(), journal, stale)
    assert journal.reservations() == []
