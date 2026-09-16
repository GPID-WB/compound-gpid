"""Lost responses before/after each irreversible publication operation."""

import pytest
from test_publisher import invoke

from cg_release.events import ControllerError


@pytest.mark.parametrize("operation", ["tag", "draft", "asset-package.whl", "publish"])
@pytest.mark.parametrize("boundary", ["before", "after"])
def test_every_write_boundary_converges_without_duplicate_effect(
    publication, operation, boundary
):
    remote = publication[-1]
    remote.fail = (operation, boundary)
    try:
        invoke(publication)
    except ControllerError as error:
        assert error.code == "E_WRITE_UNKNOWN"
    result = invoke(publication)
    assert result.state == "published"
    assert len(remote.assets) == 1
    assert remote.writes.count(operation) == (2 if boundary == "before" else 1)
    before = list(remote.writes)
    invoke(publication)
    assert before == remote.writes
