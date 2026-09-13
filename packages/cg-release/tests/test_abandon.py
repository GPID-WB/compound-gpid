"""Maintainer abandonment preserves reservations when remote effects are uncertain."""

import pytest
from journal_store import MemoryStore
from test_authority import Controls
from test_lifecycle import receipt_fixture

from cg_release.abandon import abandon_request
from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.runtime import Context


class AbandonAPI(Controls):
    def __init__(self):
        super().__init__()
        self.tags, self.releases, self.other_runs = [], [], []

    def refs(self):
        return self.tags

    def branch(self, name):
        if name.startswith("release-controller/"):
            raise ControllerError("E_NOT_FOUND", "No preparation branch.")
        return super().branch(name)

    def pages(self, endpoint):
        return self.releases if endpoint == "releases" else super().pages(endpoint)

    def get(self, endpoint, **kwargs):
        if endpoint == "actions/runs":
            rows = [{"id": 10, "status": "in_progress"}, *self.other_runs]
            return {"total_count": len(rows), "workflow_runs": rows}
        return super().get(endpoint, **kwargs)


@pytest.mark.parametrize("effect", [None, "tag", "draft", "worker"])
def test_abandon_needs_actual_absence_and_keeps_audit_history(effect):
    api = AbandonAPI()
    receipt = receipt_fixture()
    journal = Journal(MemoryStore())
    journal.admit(receipt.request, receipt=receipt)
    if effect == "tag":
        api.tags = [{"ref": "refs/tags/" + receipt.request.tag}]
    elif effect == "draft":
        api.releases = [{"tag_name": receipt.request.tag, "draft": True}]
    elif effect == "worker":
        api.other_runs = [{"id": 11, "status": "in_progress"}]
    context = Context(api, api.policy, receipt.request.policy_sha, "main", journal)
    if effect:
        with pytest.raises(ControllerError):
            abandon_request(context, receipt.request_id, 456, "Superseded", 10)
        assert len(journal.reservations()) == 1
    else:
        event = abandon_request(context, receipt.request_id, 456, "Superseded", 10)
        assert event.observed == "abandoned" and journal.reservations() == []
        assert journal.events()[-1]["audit"]["actor_id"] == 456
        assert len(journal.events()) == 2
