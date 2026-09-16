"""Irreversible publication effects are reconciled rather than overwritten."""

import hashlib
from copy import deepcopy
from pathlib import Path

import pytest
from journal_store import MemoryStore

from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.models import Request, load_record
from cg_release.prepare_stage import checkpoint
from cg_release.publisher import publish, should_be_latest
from cg_release.signing import create_tag


class PublicationRemote:
    def __init__(self):
        self.tag = None
        self.release = None
        self.assets = {}
        self.writes = []
        self.fail = None
        self.latest = None

    def _write(self, operation, effect):
        self.writes.append(operation)
        if self.fail == (operation, "before"):
            self.fail = None
            raise ControllerError("E_WRITE_UNKNOWN", "Injected lost write response.")
        effect()
        if self.fail == (operation, "after"):
            self.fail = None
            raise ControllerError("E_WRITE_UNKNOWN", "Injected lost write response.")

    def observe_tag(self, tag):
        return deepcopy(self.tag)

    def push_tag(self, tag, value, sha):
        assert self.tag is None
        self._write(
            "tag",
            lambda: setattr(
                self, "tag", {"oid": value["oid"], "commit": sha, "type": "tag"}
            ),
        )

    def observe_release(self, tag):
        return deepcopy(self.release)

    def create_draft(self, tag, sha, notes, prerelease):
        assert self.release is None
        self._write(
            "draft",
            lambda: setattr(
                self,
                "release",
                {
                    "id": 71,
                    "tag_name": tag,
                    "target_commitish": sha,
                    "body": notes,
                    "draft": True,
                    "prerelease": prerelease,
                },
            ),
        )

    def inventory(self, release_id):
        return deepcopy(list(self.assets.values()))

    def download(self, asset):
        return asset["bytes"]

    def upload(self, release_id, item, raw):
        assert item["name"] not in self.assets
        self._write(
            "asset-" + item["name"],
            lambda: self.assets.update(
                {
                    item["name"]: {
                        "id": len(self.assets) + 81,
                        "name": item["name"],
                        "size": len(raw),
                        "content_type": item["media_type"],
                        "state": "uploaded",
                        "bytes": raw,
                    }
                }
            ),
        )

    def publish(self, release_id, latest):
        def effect():
            self.release["draft"] = False
            if latest:
                self.latest = release_id

        self._write("publish", effect)

    def latest_id(self):
        return self.latest


@pytest.fixture
def publication():
    request = load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )
    journal = Journal(MemoryStore())
    record = journal.admit(request)
    for operation, state in [
        ("prepare", "awaiting-review"),
        ("review", "building"),
        ("build", "awaiting-approval"),
    ]:
        record = checkpoint(journal, record, operation, {"ok": True}, state)
    raw = b"verified build bytes"
    item = {
        "name": "package.whl",
        "path": "dist/package.whl",
        "media_type": "application/zip",
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    inputs = {
        "tag": request.tag,
        "version": request.version,
        "release_sha": "a" * 40,
        "notes": "Reviewed release notes",
        "projections": {},
        "inventory": [item],
    }
    tag = create_tag(request.tag, "a" * 40, "Bot", "bot@example.invalid", 1720000000)
    return journal, record, inputs, tag, {item["name"]: raw}, PublicationRemote()


def invoke(publication, **kwargs):
    journal, record, inputs, tag, data, remote = publication
    return publish(
        journal,
        journal.get(record.request_id),
        inputs,
        tag,
        remote,
        data=data,
        recheck=lambda: None,
        make_latest=False,
        expected_latest=None,
        run_id=41,
        **kwargs,
    )


def test_exact_publication_and_repeat_are_idempotent(publication):
    result = invoke(publication)
    assert result.state == "published" and result.published
    remote = publication[-1]
    assert remote.writes == ["tag", "draft", "asset-package.whl", "publish"]
    assert invoke(publication) == result
    assert len(remote.writes) == 4


@pytest.mark.parametrize(
    "bad", ["lightweight", "wrong-tag", "wrong-asset", "extra-asset", "wrong-draft"]
)
def test_mismatches_never_clobber(publication, bad):
    journal, record, inputs, tag, data, remote = publication
    if bad in {"lightweight", "wrong-tag"}:
        remote.tag = {
            "oid": "f" * 40,
            "commit": inputs["release_sha"],
            "type": "commit" if bad == "lightweight" else "tag",
        }
    else:
        invoke(publication)
        remote.release["draft"] = True
        if bad == "wrong-asset":
            remote.assets["package.whl"]["bytes"] = b"tampered"
        if bad == "extra-asset":
            remote.assets["extra"] = {"id": 999, "name": "extra"}
        if bad == "wrong-draft":
            remote.release["body"] = "changed"
    before = list(remote.writes)
    with pytest.raises(ControllerError):
        invoke(publication)
    assert remote.writes == before


@pytest.mark.parametrize(
    "version,history,expected",
    [
        ("1.5.0-rc.10", ["1.4.2"], False),
        ("1.4.3", ["2.0.0"], False),
        ("2.0.1", ["2.0.0", "1.9.0"], True),
        ("1.5.0", ["1.5.0-rc.10"], True),
    ],
)
def test_latest_uses_semver_not_time(version, history, expected):
    assert should_be_latest(version, history) is expected


def test_recheck_failure_prevents_first_write(publication):
    journal, record, inputs, tag, data, remote = publication

    def revoked():
        raise ControllerError("E_AUTHORITY", "Revoked")

    with pytest.raises(ControllerError):
        publish(
            journal,
            record,
            inputs,
            tag,
            remote,
            data=data,
            recheck=revoked,
            make_latest=False,
            expected_latest=None,
            run_id=41,
        )
    assert not remote.writes
