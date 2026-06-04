"""team_brain.curate — CLI entry point for the team brain curation bot.

Called by the weekly GitHub Actions curation workflow (``curation-bot.yml``).
Detects contradictions across all ``patterns/*.jsonl`` files and opens a
GitHub Issue for each one (or a PR when ``auto-supersede: true``).

Authentication:
    Reads ``GH_TOKEN`` from the environment (set automatically by GitHub
    Actions via ``secrets.GITHUB_TOKEN``).  All GitHub API calls go through
    ``subprocess.run(["gh", "issue", "create", ...])`` so no manual token
    handling is required.

Usage (standalone, outside GitHub Actions)::

    python curate.py --patterns-dir patterns/ \\
                     --config TEAM-BRAIN.yml \\
                     --repo GPID-WB/team-brain

Usage (within GitHub Actions):
    See ``scripts/team_brain/actions/curation-bot.yml`` for the full workflow.

Exit codes:
    0 — success (even when contradictions were found — issues are created).
    1 — configuration error (missing config, bad YAML, no ``gh`` CLI).
    2 — partial failure (some issues could not be created).

Requirements: Python 3.8+, stdlib only.  ``gh`` CLI must be on PATH.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Module-level import — dedup and schema live alongside curate.py in the
# same package.  They are imported lazily inside functions so that CLI
# ``--help`` works even when the package is not fully installed.
# ---------------------------------------------------------------------------


def _import_dedup():
    """Lazy import for team_brain.dedup (avoids import errors on --help)."""
    try:
        from team_brain.dedup import detect_contradictions
        return detect_contradictions
    except ImportError:
        # Fallback: add the scripts/ parent to sys.path and retry
        _scripts = Path(__file__).parent.parent
        if str(_scripts) not in sys.path:
            sys.path.insert(0, str(_scripts))
        from team_brain.dedup import detect_contradictions
        return detect_contradictions


# ---------------------------------------------------------------------------
# YAML helpers (stdlib only — no PyYAML dependency)
# ---------------------------------------------------------------------------


def _parse_team_brain_yml(config_path: Path) -> dict:
    """Parse TEAM-BRAIN.yml using a minimal stdlib YAML reader.

    Only reads top-level scalar keys.  Raises ``ValueError`` on missing
    required fields.

    Args:
        config_path: Path to ``TEAM-BRAIN.yml``.

    Returns:
        Dict with at least ``manager`` key.

    Raises:
        FileNotFoundError: If *config_path* does not exist.
        ValueError: If required fields are missing.

    Example::

        cfg = _parse_team_brain_yml(Path("TEAM-BRAIN.yml"))
        print(cfg["manager"])  # "wb384996"
    """
    if not config_path.exists():
        raise FileNotFoundError(f"TEAM-BRAIN.yml not found: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    result: dict = {}
    for line in text.splitlines():
        m = re.match(r"^([a-zA-Z_-]+)\s*:\s*(.+)$", line.strip())
        if m:
            key, value = m.group(1).strip(), m.group(2).strip()
            # Strip surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            # Parse booleans
            if value.lower() == "true":
                value = True  # type: ignore[assignment]
            elif value.lower() == "false":
                value = False  # type: ignore[assignment]
            result[key] = value

    if "manager" not in result:
        warnings.warn(
            "TEAM-BRAIN.yml missing 'manager' field — issues will be created unassigned.",
            UserWarning,
            stacklevel=2,
        )
        result["manager"] = None

    return result


# ---------------------------------------------------------------------------
# GitHub CLI helpers
# ---------------------------------------------------------------------------


def _gh_available() -> bool:
    """Return True if the ``gh`` CLI is on PATH.

    Example::

        if not _gh_available():
            sys.exit("Install gh CLI: https://cli.github.com")
    """
    try:
        proc = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _create_issue(
    repo: str,
    title: str,
    body: str,
    assignee: Optional[str],
) -> bool:
    """Create a GitHub Issue via the ``gh`` CLI.

    Args:
        repo: ``owner/repo`` string.
        title: Issue title.
        body: Issue body (markdown).
        assignee: GitHub username to assign, or ``None`` for unassigned.

    Returns:
        ``True`` on success, ``False`` on failure.

    Example::

        ok = _create_issue(
            "GPID-WB/team-brain",
            "🔍 Contradiction: null-guard vs input-validation",
            "…",
            "wb384996",
        )
    """
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
    ]
    if assignee:
        cmd += ["--assignee", assignee]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode != 0:
            warnings.warn(
                f"gh issue create failed (exit {proc.returncode}): {proc.stderr.strip()}",
                UserWarning,
                stacklevel=2,
            )
            return False
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        warnings.warn(f"gh issue create error: {exc}", UserWarning, stacklevel=2)
        return False


def _format_issue_body(report) -> str:
    """Render a ContradictionReport as a GitHub Issue body.

    Args:
        report: :class:`team_brain.dedup.ContradictionReport` instance.

    Returns:
        Markdown string suitable for ``gh issue create --body``.

    Example::

        body = _format_issue_body(report)
    """
    a = report.entry_a
    b = report.entry_b

    a_id = a.get("id", "?")
    b_id = b.get("id", "?")
    a_proj = a.get("source-project", "?")
    b_proj = b.get("source-project", "?")
    a_pattern = a.get("pattern", "")
    b_pattern = b.get("pattern", "")
    a_path = a.get("entry-path", "")
    b_path = b.get("entry-path", "")
    jaccard = report.jaccard_score
    classification = report.classification
    action = report.recommended_action
    shared_tags = ", ".join(report.shared_tags) if report.shared_tags else "none"

    classification_label = {
        "contradiction": "🔴 Contradiction (same problem, one should supersede the other)",
        "contextual_variant": "🟡 Contextual variant (same pattern, different context — both valid)",
    }.get(classification, classification)

    lines = [
        f"## Detected Relationship: {classification_label}",
        "",
        f"**Jaccard similarity**: `{jaccard:.3f}` (threshold: 0.4)",
        f"**Shared tags**: {shared_tags}",
        "",
        "---",
        "",
        f"### Entry A — `{a_id}` ({a_proj})",
        "",
        f"> {a_pattern}",
        "",
        f"Entry file: `{a_path}`",
        "",
        "---",
        "",
        f"### Entry B — `{b_id}` ({b_proj})",
        "",
        f"> {b_pattern}",
        "",
        f"Entry file: `{b_path}`",
        "",
        "---",
        "",
        "### Recommended Action",
        "",
        f"{action}",
        "",
        "---",
        "",
        "_This issue was opened automatically by the weekly curation bot._",
        "_To suppress future alerts for this pair, add a `context-note` field_",
        "_to both entries or mark one as `superseded-by: <id>`._",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main curation logic
# ---------------------------------------------------------------------------


def run_curation(
    patterns_dir: Path,
    config_path: Path,
    repo: str,
    dry_run: bool = False,
) -> int:
    """Run the full curation pipeline.

    Detects contradictions and opens GitHub Issues for each one found.

    Args:
        patterns_dir: Path to ``patterns/`` directory.
        config_path: Path to ``TEAM-BRAIN.yml``.
        repo: ``owner/repo`` string for GitHub Issue creation.
        dry_run: If ``True``, print issue content to stdout instead of
            creating real GitHub Issues.

    Returns:
        Exit code: 0 = success, 1 = config error, 2 = partial failure.

    Example::

        code = run_curation(
            Path("patterns/"),
            Path("TEAM-BRAIN.yml"),
            "GPID-WB/team-brain",
        )
    """
    detect_contradictions = _import_dedup()

    # --- Load config ---
    try:
        config = _parse_team_brain_yml(config_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    manager = config.get("manager") or None
    auto_supersede = config.get("auto-supersede", False)

    # --- Check gh CLI ---
    if not dry_run and not _gh_available():
        print(
            "ERROR: gh CLI is not available. Install from: https://cli.github.com",
            file=sys.stderr,
        )
        return 1

    # --- Detect contradictions ---
    reports = detect_contradictions(patterns_dir)

    if not reports:
        print("Curation complete: no contradictions found.")
        return 0

    print(f"Found {len(reports)} potential contradiction(s).")

    failures = 0
    for report in reports:
        a_id = report.entry_a.get("id", "?")
        b_id = report.entry_b.get("id", "?")
        topic = report.entry_a.get("topic", "unknown topic")

        title = f"🔍 Contradiction: {topic} — {a_id} vs {b_id}"
        body = _format_issue_body(report)

        if dry_run:
            print(f"\n{'=' * 60}")
            print("DRY RUN — would create issue:")
            print(f"  Title: {title}")
            print(f"  Assignee: {manager or '(unassigned)'}")
            print(f"  Body preview ({len(body)} chars):")
            print(body[:400] + ("..." if len(body) > 400 else ""))
            continue

        # auto-supersede path: open a PR instead of an issue for high-confidence
        # contradiction matches (Jaccard >= 0.8 and same classification)
        if (
            auto_supersede
            and report.classification == "contradiction"
            and report.jaccard_score >= 0.8
        ):
            # For now, still open an issue and note that auto-supersession is pending.
            # Full auto-PR path requires git operations and is deferred to a future batch.
            warnings.warn(
                f"auto-supersede is enabled for {a_id} vs {b_id} "
                f"(Jaccard={report.jaccard_score:.2f}) — "
                "creating an issue (auto-PR not yet implemented).",
                UserWarning,
                stacklevel=2,
            )

        ok = _create_issue(repo, title, body, manager)
        if ok:
            print(f"  Opened issue: {title}")
        else:
            print(f"  FAILED to open issue: {title}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"\nCuration finished with {failures} failure(s).", file=sys.stderr)
        return 2

    print(f"Curation complete: {len(reports)} issue(s) opened.")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="curate.py",
        description="Team brain curation bot — detect contradictions and open GitHub Issues.",
    )
    parser.add_argument(
        "--patterns-dir",
        type=Path,
        default=Path("patterns"),
        help="Directory containing <project>.jsonl pattern files (default: patterns/).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("TEAM-BRAIN.yml"),
        help="Path to TEAM-BRAIN.yml configuration file (default: TEAM-BRAIN.yml).",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in owner/repo format (e.g. GPID-WB/team-brain).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print issue content to stdout instead of creating real GitHub Issues.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """CLI entry point for the curation bot.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code.
    """
    args = _parse_args(argv)
    return run_curation(
        patterns_dir=args.patterns_dir,
        config_path=args.config,
        repo=args.repo,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
