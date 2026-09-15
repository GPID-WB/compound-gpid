"""Current recovery authority is not the same set as historical approval exclusions."""

from types import SimpleNamespace

from cg_release.publication_approval import excluded_reviewers


def test_all_reconfirmers_are_excluded_even_when_current_ticket_has_only_new_actor():
    record = SimpleNamespace(
        evidence={
            "publication-request-1": {"reconfirmers": [8]},
            "publication-request-2": {"reconfirmers": [9]},
            "publication-recovery": {"actor_id": 10},
            "publication-exception-99": {"actor_id": 11},
        }
    )
    assert excluded_reviewers(record, {"actor": {"id": 12}}, 77) == [8, 9, 10, 11, 12]
    assert excluded_reviewers(record, {"actor": {"id": 77}}, 77) == [8, 9, 10, 11]


def test_older_ticket_authority_is_not_reused_for_new_ticket(publication, tmp_path):
    import subprocess

    from cg_release.journal import digest
    from cg_release.publication_control import store_seal
    from cg_release.publication_stage import publication_step

    journal, record, *_ = publication
    api = SimpleNamespace(
        host="github.com",
        slug="owner/repo",
        cwd=tmp_path,
        read_seconds=20,
        remaining=lambda: 120,
        runner=lambda *a, **k: subprocess.CompletedProcess(
            a, 0, "HTTP/2.0 204 No Content\n\n", ""
        ),
    )
    context = SimpleNamespace(journal=journal, api=api, default="main")
    first = publication_step(context, record, resuming_actor_id=8)
    assert first.evidence["publication-request-1"]["reconfirmers"] == [8]
    sealed = store_seal(
        journal,
        first,
        {
            "run_id": 41,
            "run_attempt": 1,
            "nonce": first.evidence["publication-request-1"]["nonce"],
            "inputs": {"ok": True},
            "digest": digest({"ok": True}),
        },
    )
    api.get = lambda endpoint: {"id": 41, "status": "completed"}
    second = publication_step(context, sealed, resuming_actor_id=9)
    assert second.evidence["publication-request-2"]["reconfirmers"] == [9]
    assert excluded_reviewers(second, {"actor": {"id": 77}}, 77) == [8, 9]
