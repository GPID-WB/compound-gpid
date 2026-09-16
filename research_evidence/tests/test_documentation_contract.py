"""Created 2026-08-12. AST checks for documented public Phase 1 APIs."""
from __future__ import annotations

import ast
from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[1] / "src" / "research_evidence"


def test_public_functions_and_classes_have_complete_docstrings() -> None:
    """Require Args, Returns, and Example sections on public APIs."""
    missing: list[str] = []
    source_files = sorted(SOURCE_ROOT.rglob("*.py"))
    assert source_files, "The dedicated package has no Python source files."
    for source_file in source_files:
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name.startswith("_"):
                continue
            docstring = ast.get_docstring(node) or ""
            has_args = "Args:" in docstring or "Parameters:" in docstring
            has_returns = "Returns:" in docstring or "Yields:" in docstring
            if not docstring or not has_args or not has_returns or "Example:" not in docstring:
                missing.append(f"{source_file.relative_to(SOURCE_ROOT)}::{node.name}")
    assert not missing, "Incomplete public API docstrings: " + ", ".join(missing)
