"""Audited stranded recovery remains schedulable without an original inbox issue."""

from types import SimpleNamespace

from cg_release.controller import work_inventory


def test_audited_recovery_has_a_stable_queue_key_without_a_receipt():
    record = SimpleNamespace(
        request_id="reviewed-recovery",
        receipt=None,
        state="building",
        evidence={"publication-recovery": {"run_id": 91}},
    )
    journal = SimpleNamespace(records=lambda: [record])
    first = work_inventory(journal, [])
    assert len(first) == 1 and first[0]["sealed_request_id"] == record.request_id
    assert 2**52 <= first[0]["number"] < 2**53
    assert work_inventory(journal, []) == first
    record.state = "complete"
    assert work_inventory(journal, []) == []
