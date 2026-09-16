"""Release notes use complete exact-commit inventories, not timestamps or AI."""

import pytest

from cg_release.events import ControllerError
from cg_release.notes import release_notes


class Commits:
    """Exact REST commit inventory fixture with paginated comparison envelopes."""

    slug = "owner/repo"

    def __init__(self, wrong: bool = False) -> None:
        self.calls = []
        self.wrong = wrong

    def _request(self, path: str, page: int) -> object:
        self.calls.append((path, page))
        commits = [
            {"sha": f"{i:040x}", "commit": {"message": f"Change {i}\n\nBody"}}
            for i in (range(100) if page == 1 else [100])
        ]
        if self.wrong:
            commits = [{"sha": "a" * 40, "commit": None}]
        if "/compare/" in path:
            return {"status": "ahead", "total_commits": 101, "commits": commits}
        return commits


def test_complete_commit_inventory_not_first_page_only() -> None:
    api = Commits()
    result = release_notes(api, "b" * 40, "a" * 40)
    assert "Change 100" in result and result.count("\n- ") == 101
    assert len(api.calls) == 2
    assert "a" * 40 + "..." + "b" * 40 in api.calls[0][0]


def test_wrong_commit_shape_is_a_typed_error() -> None:
    with pytest.raises(ControllerError):
        release_notes(Commits(wrong=True), "b" * 40, None)
