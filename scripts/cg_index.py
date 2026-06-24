#!/usr/bin/env python3
"""cg-index — Compound GPID knowledge indexer.

Scans .cg-docs/ artifacts and roadmap.json, then builds a rich multi-file
brain knowledge index.

Usage:
    cg-index query --intent <intent> --query <text> [--changed-file <path>] [--budget <n>] [--format json|md] [--root <path>]
    cg-index [--brain] [--root <path>] [--version] [--help]

    # Legacy (deprecated — use --brain):
    cg-index [--index] [--digest] [--all] [--root <path>]

Modes:
    query      Return budgeted Knowledge Brain retrieval output.
    --brain    Build the full brain knowledge index: BRAIN.md, BRAIN-01.md,
               BRAIN-log.md, brain-index.json.  Also removes legacy
               DIGEST.md and search-index.json on success.
    --index    (DEPRECATED) Build search-index.json only.
    --digest   (DEPRECATED) Build DIGEST.md only.
    --all      (DEPRECATED) Alias for --brain.
    --root     Override the project root (defaults to cwd).
    --version  Print version and exit.

Exit codes:
    0  Success (even if some files were skipped due to parse warnings).
    1  Fatal error (no .cg-docs/ directory, unwritable output, etc.).

Requirements: Python 3.8+, stdlib only (no third-party packages).
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-index requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import warnings
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Version — imported from brain to avoid duplication (architecture P1.11 fix)
# ---------------------------------------------------------------------------

# __version__ defined in brain/__init__.py; imported lazily after sys.path bootstrap below.

# ---------------------------------------------------------------------------
# sys.path bootstrap — brain sub-modules live in scripts/brain/
# ---------------------------------------------------------------------------

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

try:
    from brain import __version__  # noqa: E402
    from brain.legacy import build_digest, build_index, scan_solutions  # noqa: E402
    from brain.utils import extract_summary, parse_frontmatter  # noqa: E402,F401
except ImportError as exc:  # noqa: E402
    __version__ = "unknown"
    _BRAIN_IMPORT_ERROR: ImportError | None = exc
else:
    _BRAIN_IMPORT_ERROR = None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_query_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for ``cg-index query``."""
    parser = argparse.ArgumentParser(
        prog="cg-index query",
        description="Query the local Knowledge Brain with a bounded token budget.",
    )
    parser.add_argument(
        "--intent",
        required=True,
        choices=("brainstorm", "plan", "work", "review", "compound", "resume"),
        help="Workflow intent used to rank Knowledge Brain artifacts.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search directive or question.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed or relevant file path. Repeat for multiple paths.",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=800,
        help="Maximum estimated output tokens. Minimum: 120.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "md"),
        default="md",
        help="Output format for prompts/tools or humans.",
    )
    parser.add_argument(
        "--root",
        metavar="PATH",
        default=None,
        help="Project root directory (defaults to current working directory).",
    )
    return parser

def build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser for ``cg-index``.

    Returns:
        Configured :class:`argparse.ArgumentParser` with ``--brain``,
        ``--index``, ``--digest``, ``--all``, ``--root``, and ``--version``
        flags.

    Example:
        >>> parser = build_arg_parser()
        >>> args = parser.parse_args(["--brain"])
        >>> args.brain
        True
    """
    parser = argparse.ArgumentParser(
        prog="cg-index",
        description="Compound GPID knowledge indexer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--brain",
        action="store_true",
        help="Build the full brain knowledge index (BRAIN.md, BRAIN-log.md, brain-index.json).",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="[DEPRECATED] Build search-index.json (metadata only). Use --brain instead.",
    )
    parser.add_argument(
        "--digest",
        action="store_true",
        help="[DEPRECATED] Build DIGEST.md (active entries). Use --brain instead.",
    )
    parser.add_argument(
        "--all",
        dest="all_",
        action="store_true",
        help="[DEPRECATED] Alias for --brain. Use --brain instead.",
    )
    parser.add_argument(
        "--root",
        metavar="PATH",
        default=None,
        help="Project root directory (defaults to current working directory).",
    )
    parser.add_argument(
        "--push-entry",
        metavar="PATH",
        default=None,
        help=(
            "Push a solution entry to the team brain central repo. "
            "Reads team-brain config from compound-gpid.local.md. "
            "Skips silently if team-brain is not configured."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"cg-index {__version__}",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the ``cg-index`` CLI.

    Args:
        argv: Argument list to parse.  Defaults to ``sys.argv[1:]`` when
            ``None``.

    Returns:
        Integer exit code: ``0`` on success, ``1`` on fatal error.

    Example:
        >>> import sys
        >>> sys.exit(main(["--brain"]))
    """
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "query":
        parser = build_query_arg_parser()
        args = parser.parse_args(argv[1:])
        root = Path(args.root).resolve() if args.root else Path.cwd()
        try:
            from brain.query import query_from_args

            rendered = query_from_args(
                root,
                intent=args.intent,
                query=args.query,
                changed_files=args.changed_file,
                budget_tokens=args.budget,
                output_format=args.format,
            )
        except ValueError as exc:
            print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
            return 1
        print(rendered, end="")
        return 0

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Resolve root
    root = Path(args.root).resolve() if args.root else Path.cwd()

    # -----------------------------------------------------------------------
    # --push-entry mode
    # -----------------------------------------------------------------------
    if getattr(args, "push_entry", None):
        solution_path = Path(args.push_entry)
        if not solution_path.exists():
            print(
                f"[cg-index] ERROR: solution file not found: {solution_path}",
                file=sys.stderr,
            )
            return 1
        try:
            from team_brain.push import push_entry
        except ImportError as exc:
            print(
                f"[cg-index] ERROR: team_brain package not available ({exc}).\n"
                "Reinstall compound-gpid or run: pip install -e scripts/",
                file=sys.stderr,
            )
            return 1
        try:
            result = push_entry(solution_path)
            print(f"[cg-index] {result.summary}")
            return 0
        except ValueError as exc:
            print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
            return 1
        except RuntimeError as exc:
            print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
            return 1

    # --all is deprecated; redirect to --brain
    do_brain = getattr(args, "brain", False) or args.all_
    do_index = args.index
    do_digest = args.digest

    # Emit deprecation notices for legacy flags
    for flag, condition in (("--all", args.all_), ("--index", args.index), ("--digest", args.digest)):
        if condition:
            print(
                f"[cg-index] DEPRECATED: {flag} is deprecated. Use --brain instead.",
                file=sys.stderr,
            )

    # When --all is passed, suppress the legacy index/digest runs — brain only
    if args.all_:
        do_index = False
        do_digest = False

    # -----------------------------------------------------------------------
    # Brain mode (--brain or --all redirect)
    # -----------------------------------------------------------------------
    if do_brain:
        cg_docs_dir = root / ".cg-docs"
        if not cg_docs_dir.is_dir():
            print(
                f"[cg-index] ERROR: {cg_docs_dir} does not exist.\n"
                "Run cg-index from a project root containing a .cg-docs/ directory.",
                file=sys.stderr,
            )
            return 1
        if _BRAIN_IMPORT_ERROR is not None:
            print(
                f"[cg-index] ERROR: brain package not available ({_BRAIN_IMPORT_ERROR}).\n"
                "Reinstall compound-gpid or run: pip install -e scripts/",
                file=sys.stderr,
            )
            return 1
        try:
            from brain import build_brain
            from brain.renderer import render_brain
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                data = build_brain(root)
                render_brain(data, out_dir=cg_docs_dir)
            for w in captured:
                print(f"[cg-index] WARNING: {w.message!s}", file=sys.stderr)
            print(
                f"[cg-index] Brain index written to {cg_docs_dir} "
                f"({len(data.entities)} entities, {len(data.topics)} topics, "
                f"{len(data.edges)} edges)"
            )
        except ImportError as exc:
            print(
                f"[cg-index] ERROR: brain package not available ({exc}).\n"
                "Reinstall compound-gpid or run: pip install -e scripts/",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
            return 1
        # Delete legacy files outside the brain-build try block so that a
        # locked or missing legacy file does not cause a false exit-1 after
        # a successful brain write.
        for legacy_name in ("DIGEST.md", "search-index.json"):
            legacy_path = cg_docs_dir / legacy_name
            if legacy_path.exists():
                try:
                    legacy_path.unlink()
                    print(f"[cg-index] Removed legacy {legacy_name}")
                except OSError as exc:
                    print(
                        f"[cg-index] WARNING: could not remove legacy {legacy_name}: {exc}",
                        file=sys.stderr,
                    )
        return 0

    # -----------------------------------------------------------------------
    # Legacy mode (--index / --digest / default)
    # -----------------------------------------------------------------------
    solutions_dir = root / ".cg-docs" / "solutions"
    if not solutions_dir.is_dir():
        print(
            f"[cg-index] ERROR: {solutions_dir} does not exist.\n"
            "Run cg-index from a project root containing a .cg-docs/solutions/ directory.",
            file=sys.stderr,
        )
        return 1

    # Default: --index when no mode flag is given
    if not do_index and not do_digest:
        do_index = True

    if _BRAIN_IMPORT_ERROR is not None:
        print(
            f"[cg-index] ERROR: brain package not available ({_BRAIN_IMPORT_ERROR}).\n"
            "Reinstall compound-gpid or run: pip install -e scripts/",
            file=sys.stderr,
        )
        return 1

    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            entries = scan_solutions(solutions_dir, root, want_summary=do_digest)
            if do_index:
                build_index(entries, root / ".cg-docs" / "search-index.json")
            if do_digest:
                build_digest(entries, root / ".cg-docs" / "DIGEST.md")
        for w in captured:
            print(f"[cg-index] WARNING: {w.message!s}", file=sys.stderr)
    except OSError as exc:
        print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
