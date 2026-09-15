"""Keep the standalone controller's production modules independently reviewable."""

from pathlib import Path


def test_production_modules_remain_within_project_line_bound():
    source = Path(__file__).parents[1] / "src/cg_release"
    oversized = {}
    for path in source.glob("*.py"):
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > 300:
            oversized[path.name] = count
    assert not oversized
