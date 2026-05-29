"""team_brain.init — One-time setup command for the team brain manager.

Creates a new GitHub repository with the standard team brain directory
structure (``TEAM-BRAIN.yml``, ``entries/``, ``patterns/``,
``.github/workflows/``), copies the curation action templates from the
compound-gpid installation, pushes an initial commit, and optionally
configures the local project's ``compound-gpid.local.md``.

Usage::

    cg-brain-init --repo GPID-WB/team-brain --manager wb384996

    # Or directly:
    python scripts/team_brain/init.py --repo GPID-WB/team-brain --manager wb384996

This is a one-time operation for the team brain manager.  Contributors do not
need to run this command — they configure their local projects with
``compound-gpid.local.md`` pointing to the existing team brain repo.

Authentication:
    All GitHub operations go through ``gh`` CLI (``gh repo create``,
    ``gh api``, ``git push``).  Run ``gh auth login`` before use.

Requirements: Python 3.8+, stdlib only.  ``gh`` CLI on PATH.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default initial TEAM-BRAIN.yml content (manager placeholder replaced at runtime).
_TEAM_BRAIN_YML_TEMPLATE = """\
---
# TEAM-BRAIN.yml — Central team brain configuration
# Managed by the team brain manager. Contributors should not edit this file.

schema-version: "1.0"

# GitHub username of the team brain manager (reviews curation issues, approves PRs)
manager: "{manager}"

# Who can contribute to this team brain
contributors:
  - org: ""    # Replace with your GitHub org, e.g. "GPID-WB"
  # OR use a specific team:
  # - team: "GPID-WB/poverty-stats"

# Curation settings
curation:
  schedule: "weekly"       # cron preset: "daily", "weekly", "monthly"
  auto-supersede: false    # set true to auto-apply supersession for high-confidence matches
"""

#: Placeholder README for the team brain repo root.
_TEAM_BRAIN_README = """\
# 🧠 Team Brain

Cross-project knowledge base for the Compound GPID plugin.

## Structure

```
team-brain/
├── TEAM-BRAIN.yml          # Configuration: manager, contributors, curation schedule
├── TEAM-BRAIN.md           # Unified index (rebuilt automatically by CI)
├── entries/
│   └── <project-name>/    # One folder per project namespace
│       └── *.md            # Solution entries pushed via /cg-compound
├── patterns/
│   └── <project-name>.jsonl  # Distilled pattern one-liners
└── .github/
    └── workflows/
        ├── rebuild-index.yml    # Rebuilds TEAM-BRAIN.md on push
        └── curation-bot.yml     # Weekly contradiction detection
```

## Adding a Project

1. Set the `team-brain:` section in your project's `compound-gpid.local.md`:
   ```yaml
   team-brain:
     repo: "<owner>/<this-repo>"
     project-name: "<your-project-name>"
     enabled: true
   ```
2. Push a solution via `/cg-compound` in Copilot Chat.

## Curation

The weekly curation bot scans for contradicting patterns across projects
and opens GitHub Issues for the manager to review.  See `TEAM-BRAIN.yml`
for configuration options.
"""

#: Placeholder TEAM-BRAIN.md (rebuilt by CI after first push).
_TEAM_BRAIN_MD_PLACEHOLDER = """\
# 🧠 Team Brain

_No entries yet. Push your first solution via `/cg-compound`._

This file is automatically rebuilt when entries or patterns are updated.
"""

#: Gitignore for the team brain repo.
_GITIGNORE = """\
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# OS
.DS_Store
Thumbs.db
"""


# ---------------------------------------------------------------------------
# CLI helpers
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


def _repo_exists(repo: str) -> bool:
    """Return True if *repo* already exists on GitHub.

    Args:
        repo: ``owner/repo`` string.

    Returns:
        ``True`` if the repo exists and is accessible, ``False`` otherwise.
    """
    try:
        proc = subprocess.run(
            ["gh", "repo", "view", repo, "--json", "name"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# Scaffold helpers
# ---------------------------------------------------------------------------


def _write_scaffold(work_dir: Path, manager: str) -> None:
    """Write the initial team brain directory structure to *work_dir*.

    Creates:
    - ``TEAM-BRAIN.yml``
    - ``TEAM-BRAIN.md``
    - ``README.md``
    - ``.gitignore``
    - ``entries/.gitkeep``
    - ``patterns/.gitkeep``
    - ``.github/workflows/rebuild-index.yml``
    - ``.github/workflows/curation-bot.yml``

    The action template files are sourced from the compound-gpid installation
    (``scripts/team_brain/actions/``).  If they are not found, inline
    placeholder content is written and a warning is emitted.

    Args:
        work_dir: Directory in which to create the scaffold.
        manager: GitHub username for the TEAM-BRAIN.yml ``manager`` field.
    """
    # --- Root files ---
    (work_dir / "TEAM-BRAIN.yml").write_text(
        _TEAM_BRAIN_YML_TEMPLATE.format(manager=manager), encoding="utf-8"
    )
    (work_dir / "TEAM-BRAIN.md").write_text(_TEAM_BRAIN_MD_PLACEHOLDER, encoding="utf-8")
    (work_dir / "README.md").write_text(_TEAM_BRAIN_README, encoding="utf-8")
    (work_dir / ".gitignore").write_text(_GITIGNORE, encoding="utf-8")

    # --- entries/ and patterns/ placeholder files ---
    (work_dir / "entries").mkdir(exist_ok=True)
    (work_dir / "entries" / ".gitkeep").write_text("", encoding="utf-8")
    (work_dir / "patterns").mkdir(exist_ok=True)
    (work_dir / "patterns" / ".gitkeep").write_text("", encoding="utf-8")

    # --- .github/workflows/ action templates ---
    workflows_dir = work_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Try to source templates from the compound-gpid installation
    actions_source = Path(__file__).parent / "actions"
    for template_name in ("rebuild-index.yml", "curation-bot.yml"):
        src = actions_source / template_name
        dst = workflows_dir / template_name
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            warnings.warn(
                f"Action template not found: {src}. "
                f"Writing placeholder to {dst}. "
                "Copy the template manually from compound-gpid/scripts/team_brain/actions/.",
                UserWarning,
                stacklevel=3,
            )
            dst.write_text(f"# Placeholder: copy {template_name} from compound-gpid\n", encoding="utf-8")


def _git_init_and_push(work_dir: Path, repo: str, manager: str) -> bool:
    """Initialise a git repo in *work_dir* and push to *repo*.

    Args:
        work_dir: Directory containing the scaffold.
        repo: ``owner/repo`` on GitHub.
        manager: Author name for the initial commit.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    git_email = f"{manager}@users.noreply.github.com"

    commands: List[List[str]] = [
        ["git", "init"],
        ["git", "config", "user.name", manager],
        ["git", "config", "user.email", git_email],
        ["git", "add", "."],
        ["git", "commit", "-m", "feat(brain): initial team brain scaffold"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", f"https://github.com/{repo}.git"],
        ["git", "push", "-u", "origin", "main"],
    ]

    for cmd in commands:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(work_dir),
            timeout=60,
            check=False,
        )
        if proc.returncode != 0:
            warnings.warn(
                f"Command failed: {' '.join(cmd)}\n{proc.stderr.strip()}",
                UserWarning,
                stacklevel=3,
            )
            return False

    return True


def _update_local_config(project_root: Path, repo: str, project_name: str) -> bool:
    """Append the ``team-brain:`` section to ``compound-gpid.local.md``.

    If the section already exists, the file is left unchanged and the function
    returns ``True``.

    Args:
        project_root: Root directory of the local project.
        repo: ``owner/repo`` string.
        project_name: Namespace under ``entries/`` and ``patterns/``.

    Returns:
        ``True`` on success (including if already configured), ``False`` on error.
    """
    config_path = project_root / "compound-gpid.local.md"
    if not config_path.exists():
        warnings.warn(
            f"compound-gpid.local.md not found at {config_path}. "
            "Add the team-brain section manually.",
            UserWarning,
            stacklevel=2,
        )
        return False

    content = config_path.read_text(encoding="utf-8")
    if "team-brain:" in content:
        return True  # already configured

    section = (
        f"\n## Team Brain\n\n"
        f"team-brain:\n"
        f"  repo: \"{repo}\"\n"
        f"  project-name: \"{project_name}\"\n"
        f"  enabled: true\n"
        f"  llm-filter: true\n"
    )

    try:
        config_path.write_text(content.rstrip() + section, encoding="utf-8")
        return True
    except OSError as exc:
        warnings.warn(f"Could not update compound-gpid.local.md: {exc}", UserWarning, stacklevel=2)
        return False


# ---------------------------------------------------------------------------
# Main init logic
# ---------------------------------------------------------------------------


def init_team_brain(
    repo: str,
    manager: str,
    project_root: Optional[Path] = None,
    configure_local: bool = True,
) -> int:
    """Create and scaffold a new team brain repository on GitHub.

    Workflow:
        1. Check that ``gh`` CLI is available.
        2. Check if *repo* already exists — if so, offer to configure local project.
        3. Create the repo via ``gh repo create``.
        4. Clone a temporary working directory, write the scaffold, push the
           initial commit.
        5. Optionally update ``compound-gpid.local.md`` with the new config.

    Args:
        repo: ``owner/repo`` string, e.g. ``"GPID-WB/team-brain"``.
        manager: GitHub username of the team brain manager.
        project_root: Root directory of the local project.  Defaults to
            ``Path.cwd()``.
        configure_local: Whether to update ``compound-gpid.local.md``.

    Returns:
        Exit code: 0 = success, 1 = error.

    Example::

        code = init_team_brain("GPID-WB/team-brain", "wb384996")
    """
    if project_root is None:
        project_root = Path.cwd()

    # --- Check gh CLI ---
    if not _gh_available():
        print(
            "ERROR: gh CLI is not available. Install from: https://cli.github.com",
            file=sys.stderr,
        )
        return 1

    # --- Check if repo already exists ---
    if _repo_exists(repo):
        print(f"Repo {repo} already exists on GitHub.")
        print("Configuring local project to use it...")
        project_name = repo.split("/")[-1]
        if configure_local:
            ok = _update_local_config(project_root, repo, project_name)
            if ok:
                print(f"  Updated compound-gpid.local.md with team-brain repo: {repo}")
            else:
                print("  WARNING: Could not update compound-gpid.local.md automatically.")
                print("  Add this section manually:")
                print("    team-brain:")
                print(f'      repo: "{repo}"')
                print(f'      project-name: "{project_name}"')
                print("      enabled: true")
        return 0

    # --- Create the repo ---
    print(f"Creating team brain repo: {repo}")
    try:
        proc = subprocess.run(
            ["gh", "repo", "create", repo, "--public", "--description", "Team brain — cross-project knowledge base (Compound GPID)"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: gh repo create failed: {exc}", file=sys.stderr)
        return 1

    if proc.returncode != 0:
        print(f"ERROR: gh repo create failed (exit {proc.returncode}):", file=sys.stderr)
        print(proc.stderr.strip(), file=sys.stderr)
        return 1

    print(f"  Created: https://github.com/{repo}")

    # --- Scaffold and push ---
    print("Writing initial scaffold...")
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp) / "team-brain"
        work_dir.mkdir()

        _write_scaffold(work_dir, manager)

        print("Pushing initial commit...")
        ok = _git_init_and_push(work_dir, repo, manager)
        if not ok:
            print(
                "ERROR: Failed to push initial commit. "
                "Check your gh auth token has repo write access.",
                file=sys.stderr,
            )
            return 1

    print(f"  Scaffold pushed to https://github.com/{repo}")

    # --- Configure local project ---
    if configure_local:
        project_name = repo.split("/")[-1]
        ok = _update_local_config(project_root, repo, project_name)
        if ok:
            print(f"  Updated compound-gpid.local.md → team-brain: {repo}")
        else:
            print("  NOTE: Add the team-brain section to compound-gpid.local.md manually.")

    # --- Success ---
    print("")
    print(f"Team brain repo ready: https://github.com/{repo}")
    print("")
    print("Next steps:")
    print("  1. Invite team members to contribute (add them to TEAM-BRAIN.yml)")
    print("  2. Push your first solution: run /cg-compound in Copilot Chat")
    print("  3. Share the repo URL with other projects so they can configure their")
    print("     compound-gpid.local.md team-brain section.")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="cg-brain-init",
        description=(
            "One-time setup for the team brain central repository. "
            "Run this as the team brain manager to create and scaffold the repo."
        ),
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in owner/repo format (e.g. GPID-WB/team-brain).",
    )
    parser.add_argument(
        "--manager",
        required=True,
        help="GitHub username of the team brain manager.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to the local project root (default: current directory).",
    )
    parser.add_argument(
        "--no-configure",
        action="store_true",
        default=False,
        help="Skip updating compound-gpid.local.md with the new repo.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code.
    """
    args = _parse_args(argv)
    return init_team_brain(
        repo=args.repo,
        manager=args.manager,
        project_root=args.project_root,
        configure_local=not args.no_configure,
    )


if __name__ == "__main__":
    sys.exit(main())
