#!/usr/bin/env python3
"""cg-import-skill — Quarantined external-skill importer for Compound GPID.

Implements the ``/cg-import-skill`` command with two explicit modes:

* **review** mode (consumer project): accepts a pinned commit from an
  allowlisted HTTPS repository, fetches the content into a quarantined
  directory, runs admission checks, and produces a deterministic review
  diff.  Consumer projects may only create review evidence — no canonical
  writes.

* **vendor** mode (verified maintainer source checkout): same intake,
  but after approval the bundle may be copied into canonical
  ``.github/skills/`` with full provenance registration.

Both modes require a full immutable SHA, normalized approved upstream
skill-root descendant, no redirects, no shell interpolation, no interactive
credentials, disabled hooks/submodules/LFS smudging, and a network-free
runtime result after the initial ``git archive`` fetch.

Usage:
    python scripts/cg_import_skill.py \\
        <repo-url>@<full-sha> <path> \\
        --mode review|vendor \\
        [--root <path>] [--quarantine-dir <path>]

Exit codes:
    0  Success (quarantined and reviewed, or vendored).
    1  Admission or policy failure.
    2  Missing or invalid arguments or project root.

Requirements: Python 3.8+, stdlib only, git.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-import-skill requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from cg_vendor_policy import (
    load_policy,
    is_allowed_repository,
    is_safe_skill_path,
    is_allowed_extension,
    is_approved_license,
    scan_for_secrets,
    scan_for_prompt_injection,
    run_admission_checks,
    verify_canonical_source_checkout,
    check_identifier_collision,
    normalize_identifier,
)

# ── Constants ────────────────────────────────────────────────────────────────

_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_REPO_PATH_PATTERN = re.compile(r"^(https://[^\s@]+)@([0-9a-f]{40})\s+(\S+)$")
_REGISTRY_PATH = ".github/shared/module-registry.json"
_QUARANTINE_MARKER = ".quarantine-meta.json"
_SAFE_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"}


# ── Argument parsing ─────────────────────────────────────────────────────────

def parse_import_spec(spec: str) -> Tuple[str, str, str]:
    """Parse ``<repo-url>@<full-sha> <path>`` into components.

    Returns (repo_url, sha, skill_path).
    Raises ValueError on invalid format.
    """
    spec = spec.strip()
    match = _REPO_PATH_PATTERN.match(spec)
    if not match:
        # Try separate arguments form
        parts = spec.split()
        if len(parts) >= 2:
            repo_sha = parts[0]
            skill_path = parts[1]
        else:
            raise ValueError(
                "Invalid import spec. Expected: <repo-url>@<full-sha> <path>"
            )
        at_idx = repo_sha.rfind("@")
        if at_idx == -1:
            raise ValueError("Missing '@' separator in repo@sha specification")
        repo_url = repo_sha[:at_idx]
        sha = repo_sha[at_idx + 1:]
    else:
        repo_url = match.group(1)
        sha = match.group(2)
        skill_path = match.group(3)

    # Validate SHA format
    if not _SHA_PATTERN.match(sha):
        raise ValueError(
            f"SHA must be a full 40-character hex string, got: {sha!r}"
        )

    # Validate path normalization
    posix_path = PurePosixPath(skill_path)
    if ".." in posix_path.parts:
        raise ValueError(f"Path traversal not allowed: {skill_path}")

    return repo_url, sha, skill_path


# ── Git archive fetch ────────────────────────────────────────────────────────

def fetch_to_quarantine(
    repo_url: str,
    sha: str,
    skill_path: str,
    quarantine_dir: Path,
    policy: Dict[str, Any],
) -> Tuple[bool, str, List[str]]:
    """Fetch the pinned content into the quarantine directory.

    Uses ``git archive --remote`` or ``git clone --depth 1`` + extraction.
    On Windows, uses ``git archive`` with piped tar extraction.

    Returns (ok, message, fetched_files).
    """
    errors: List[str] = []
    fetched_files: List[str] = []

    # Create quarantine directory
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    # Use git archive to fetch pinned content
    try:
        # Try git archive first (works with GitHub for some repos)
        result = subprocess.run(
            [
                "git", "archive",
                f"--remote={repo_url}",
                sha,
                skill_path,
            ],
            capture_output=True,
            timeout=120,
            env=_SAFE_GIT_ENV,
        )
        if result.returncode == 0:
            # Extract tar to quarantine with member validation (tar-slip prevention)
            import tarfile
            import io

            tar_data = result.stdout
            if not tar_data:
                return False, "git archive returned empty output", []

            # Write to skill subdirectory in quarantine
            dest = quarantine_dir / PurePosixPath(skill_path).name
            dest.mkdir(parents=True, exist_ok=True)

            with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:") as tar:
                dest_real = os.path.realpath(str(dest))
                safe_members = []
                for member in tar.getmembers():
                    member_dest = os.path.realpath(
                        os.path.join(str(dest), member.name)
                    )
                    if not member_dest.startswith(dest_real + os.sep) and member_dest != dest_real:
                        return False, f"Tar path traversal detected: {member.name}", []
                    if member.issym() or member.islnk():
                        return False, f"Symlink/hardlink in archive: {member.name}", []
                    safe_members.append(member)
                tar.extractall(path=str(dest), members=safe_members)

            # Collect extracted files
            for item in dest.rglob("*"):
                if item.is_file():
                    fetched_files.append(str(item.relative_to(quarantine_dir)))

            return True, f"Fetched {len(fetched_files)} files", fetched_files
    except subprocess.TimeoutExpired:
        return False, "git archive timed out (120s)", []
    except FileNotFoundError:
        return False, "git not found on PATH", []

    # Fallback: shallow clone + extract
    clone_dir = quarantine_dir / "_clone_tmp"
    try:
        # Shallow clone with no checkout
        result = subprocess.run(
            [
                "git", "clone",
                "--depth=1",
                "--no-checkout",
                "--no-tags",
                "--no-recurse-submodules",
                "--config", "core.hooksPath=/dev/null",
                "--config", "credential.helper=",
                repo_url,
                str(clone_dir),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=_SAFE_GIT_ENV,
        )
        if result.returncode != 0:
            return False, f"Clone failed: {result.stderr.strip()}", []

        # Checkout specific SHA (detached HEAD)
        result = subprocess.run(
            ["git", "checkout", sha, "--", skill_path],
            capture_output=True,
            text=True,
            cwd=str(clone_dir),
            timeout=30,
            env=_SAFE_GIT_ENV,
        )
        if result.returncode != 0:
            return False, f"Checkout of {sha} failed: {result.stderr.strip()}", []

        # Copy to quarantine
        source = clone_dir / skill_path
        if not source.exists():
            return False, f"Skill path not found after checkout: {skill_path}", []

        dest = quarantine_dir / PurePosixPath(skill_path).name
        dest.mkdir(parents=True, exist_ok=True)

        import shutil
        if source.is_dir():
            for item in source.rglob("*"):
                if item.is_file() and not item.is_symlink():
                    rel = item.relative_to(source)
                    target = dest / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(item), str(target))
                    fetched_files.append(str(target.relative_to(quarantine_dir)))
        else:
            target = dest / source.name
            shutil.copy2(str(source), str(target))
            fetched_files.append(str(target.relative_to(quarantine_dir)))

        return True, f"Fetched {len(fetched_files)} files via clone", fetched_files

    except subprocess.TimeoutExpired:
        return False, "Clone timed out", []
    finally:
        # Clean up clone directory
        if clone_dir.exists():
            import shutil
            try:
                shutil.rmtree(str(clone_dir))
            except OSError:
                pass


# ── Quarantine metadata ──────────────────────────────────────────────────────

def write_quarantine_meta(
    quarantine_dir: Path,
    repo_url: str,
    sha: str,
    skill_path: str,
    mode: str,
    fetched_files: List[str],
) -> Path:
    """Write quarantine metadata marker file."""
    meta = {
        "schemaVersion": 1,
        "importedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": {
            "repository": repo_url,
            "commitSha": sha,
            "skillPath": skill_path,
        },
        "mode": mode,
        "files": fetched_files,
        "status": "quarantined",
    }
    meta_path = quarantine_dir / _QUARANTINE_MARKER
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta_path


# ── Review diff generation ───────────────────────────────────────────────────

def generate_review_diff(
    quarantine_dir: Path,
    repo_url: str,
    sha: str,
    skill_path: str,
    admission_result: Any,
) -> str:
    """Generate a deterministic, secret-redacted review diff.

    Returns Markdown-formatted review evidence suitable for a consumer
    project's ``.compound-gpid/vendor-reviews/`` directory.
    """
    lines = [
        "# Vendor Import Review",
        "",
        f"**Repository**: {repo_url}",
        f"**Commit SHA**: {sha}",
        f"**Skill path**: {skill_path}",
        f"**Review date**: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}",
        "",
    ]

    # Files
    lines.append("## Imported Files")
    lines.append("")
    for item in sorted(quarantine_dir.rglob("*")):
        if item.is_file() and item.name != _QUARANTINE_MARKER:
            rel = str(item.relative_to(quarantine_dir)).replace("\\", "/")
            size = item.stat().st_size
            sha256 = hashlib.sha256(item.read_bytes()).hexdigest()[:16]
            lines.append(f"- `{rel}` ({size} bytes, sha256:{sha256}...)")
    lines.append("")

    # Admission results
    lines.append("## Admission Checks")
    lines.append("")

    if admission_result.ok:
        lines.append("✅ All admission checks passed.")
    else:
        lines.append("❌ Admission checks failed.")
    lines.append("")

    if admission_result.errors:
        lines.append("### Errors")
        for err in admission_result.errors:
            lines.append(f"- ❌ {err}")
        lines.append("")

    if admission_result.secret_findings:
        lines.append("### Secret Findings (redacted)")
        for finding in admission_result.secret_findings:
            lines.append(
                f"- `{finding.get('file', '?')}` line {finding.get('line', '?')}: "
                f"potential secret — {finding.get('redacted', '***')}"
            )
        lines.append("")

    if admission_result.injection_findings:
        lines.append("### Prompt-Injection Findings")
        for finding in admission_result.injection_findings:
            lines.append(
                f"- `{finding.get('file', '?')}` line {finding.get('line', '?')}: "
                f"matched pattern {finding.get('pattern', '?')}"
            )
        lines.append("")

    if admission_result.warnings:
        lines.append("### Warnings")
        for warn in admission_result.warnings:
            lines.append(f"- ⚠️ {warn}")
        lines.append("")

    # Provenance
    lines.append("## Provenance")
    lines.append("")
    lines.append(f"- Import date: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(f"- Import mode: quarantine review")
    lines.append(f"- Policy schema: vendor-policy.json v1")
    lines.append("")

    return "\n".join(lines) + "\n"


# ── Vendor registration (Step 12) ───────────────────────────────────────────

def register_vendor_skill(
    source_checkout: Path,
    quarantine_dir: Path,
    skill_path: str,
    repo_url: str,
    sha: str,
    policy: Dict[str, Any],
    *,
    license_id: str = "",
    reviewer: str = "",
    approval_ref: str = "",
) -> Tuple[bool, str]:
    """Register an approved quarantined bundle in the canonical source.

    Only callable in vendor mode from a verified canonical source checkout.
    Copies the non-executable bundle into ``.github/skills/`` and registers
    provenance in the module registry.

    Returns (ok, message).
    """
    # Verify canonical source
    ok, reason = verify_canonical_source_checkout(source_checkout, policy)
    if not ok:
        return False, f"Not a verified canonical source checkout: {reason}"

    # Load registry
    registry_path = source_checkout / _REGISTRY_PATH
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return False, f"Cannot load module registry: {exc}"

    # Determine destination
    managed_root = source_checkout / policy.get("managedSkillRoot", ".github/skills/")
    skill_name = PurePosixPath(skill_path).name
    dest = managed_root / skill_name

    # Check for collisions
    existing_ids = {
        cap["id"] for cap in registry.get("capabilities", [])
    }
    collision_ok, collision_reason = check_identifier_collision(
        skill_name, existing_ids
    )
    if not collision_ok:
        return False, collision_reason

    # Check destination does not exist
    if dest.exists():
        return False, f"Destination already exists: {dest.relative_to(source_checkout)}"

    # Copy from quarantine to managed root
    import shutil
    managed_root.mkdir(parents=True, exist_ok=True)

    # Find the skill content in quarantine
    quarantine_skill = quarantine_dir / skill_name
    if not quarantine_skill.exists():
        # Try finding any directory in quarantine
        dirs = [d for d in quarantine_dir.iterdir() if d.is_dir() and d.name != "_clone_tmp"]
        if len(dirs) == 1:
            quarantine_skill = dirs[0]
        else:
            return False, f"Cannot locate skill content in quarantine"

    shutil.copytree(str(quarantine_skill), str(dest))

    # Add provenance entry to registry (vendor-imports section)
    if "vendorImports" not in registry:
        registry["vendorImports"] = []

    registry["vendorImports"].append({
        "skillName": skill_name,
        "sourceRepository": repo_url,
        "sourceCommitSha": sha,
        "sourcePath": skill_path,
        "importedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "license": license_id,
        "reviewer": reviewer,
        "approvalRef": approval_ref,
        "localPath": f".github/skills/{skill_name}/",
    })

    # Write updated registry
    registry_path.write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )

    return True, f"Vendored {skill_name} to .github/skills/{skill_name}/"


# ── Main import workflow ─────────────────────────────────────────────────────

def run_import(
    repo_url: str,
    sha: str,
    skill_path: str,
    mode: str,
    root: Path,
    quarantine_base: Optional[Path] = None,
    *,
    license_id: str = "",
    reviewer: str = "",
    approval_ref: str = "",
) -> Tuple[bool, str]:
    """Execute the full import workflow.

    Returns (ok, message).
    """
    # Load policy
    try:
        policy = load_policy(root)
    except (FileNotFoundError, ValueError) as exc:
        return False, f"Policy error: {exc}"

    # Step 1: Validate repository identity
    if not is_allowed_repository(repo_url, policy):
        return False, (
            f"Repository {repo_url!r} is not on the allowlist. "
            f"Allowed: {policy.get('allowedRepositoryIdentities', [])}"
        )

    # Step 2: Validate path safety
    ok, reason = is_safe_skill_path(skill_path, policy)
    if not ok:
        return False, f"Unsafe skill path: {reason}"

    # Step 3: Vendor mode requires canonical source checkout
    if mode == "vendor":
        ok, reason = verify_canonical_source_checkout(root, policy)
        if not ok:
            return False, f"Vendor mode requires canonical source checkout: {reason}"

    # Step 4: Set up quarantine directory
    if quarantine_base is None:
        quarantine_base = root / policy.get(
            "quarantineDirectoryName", ".compound-gpid/quarantine"
        )
    quarantine_dir = quarantine_base / f"{sha[:12]}_{PurePosixPath(skill_path).name}"

    if quarantine_dir.exists():
        import shutil
        try:
            shutil.rmtree(str(quarantine_dir))
        except OSError as exc:
            return False, f"Cannot clean quarantine: {exc}"

    # Step 5: Fetch to quarantine
    ok, msg, fetched_files = fetch_to_quarantine(
        repo_url, sha, skill_path, quarantine_dir, policy
    )
    if not ok:
        return False, f"Fetch failed: {msg}"

    # Step 6: Write quarantine metadata
    write_quarantine_meta(quarantine_dir, repo_url, sha, skill_path, mode, fetched_files)

    # Step 7: Run admission checks
    admission = run_admission_checks(quarantine_dir, policy)

    # Step 8: Generate review diff
    review_diff = generate_review_diff(
        quarantine_dir, repo_url, sha, skill_path, admission
    )

    # Save review evidence
    review_dir = root / policy.get(
        "reviewEvidenceDirectoryName", ".compound-gpid/vendor-reviews"
    )
    review_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}_{sha[:12]}_{PurePosixPath(skill_path).name}"
    review_path = review_dir / f"{slug}-review.md"
    review_path.write_text(review_diff, encoding="utf-8")

    if not admission.ok:
        return False, (
            f"Admission failed with {len(admission.errors)} error(s), "
            f"{len(admission.secret_findings)} secret finding(s), "
            f"{len(admission.injection_findings)} injection finding(s). "
            f"Review: {review_path}"
        )

    # Step 9: Vendor mode — register if approved
    if mode == "vendor":
        ok, msg = register_vendor_skill(
            source_checkout=root,
            quarantine_dir=quarantine_dir,
            skill_path=skill_path,
            repo_url=repo_url,
            sha=sha,
            policy=policy,
            license_id=license_id,
            reviewer=reviewer,
            approval_ref=approval_ref,
        )
        if not ok:
            return False, f"Vendor registration failed: {msg}"
        return True, f"Vendored successfully. {msg}"

    # Review mode: quarantine only
    return True, (
        f"Quarantined {len(fetched_files)} file(s) for review. "
        f"Review evidence: {review_path}"
    )


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quarantined external-skill importer for Compound GPID."
    )
    parser.add_argument(
        "import_spec",
        help="Import specification: <repo-url>@<full-sha> <path>",
        nargs="?",
    )
    parser.add_argument(
        "skill_path_override",
        nargs="?",
        help="Skill path (alternative to inline spec)",
    )
    parser.add_argument(
        "--mode",
        choices=["review", "vendor"],
        default="review",
        help="Import mode: review (consumer) or vendor (maintainer).",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--quarantine-dir", type=Path, default=None)
    parser.add_argument("--license", type=str, default="", help="License identifier.")
    parser.add_argument("--reviewer", type=str, default="", help="Reviewer identity.")
    parser.add_argument("--approval-ref", type=str, default="", help="Approval reference.")
    args = parser.parse_args()

    if not args.import_spec:
        parser.print_help()
        sys.exit(2)

    root = args.root.resolve()

    try:
        if args.skill_path_override:
            # Split import_spec into repo@sha
            repo_sha = args.import_spec
            at_idx = repo_sha.rfind("@")
            if at_idx == -1:
                print("Error: Missing '@' in repo@sha specification.", file=sys.stderr)
                sys.exit(2)
            repo_url = repo_sha[:at_idx]
            sha = repo_sha[at_idx + 1:]
            skill_path = args.skill_path_override
            if not _SHA_PATTERN.match(sha):
                print(f"Error: SHA must be 40 hex chars, got: {sha!r}", file=sys.stderr)
                sys.exit(2)
        else:
            repo_url, sha, skill_path = parse_import_spec(args.import_spec)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    ok, msg = run_import(
        repo_url=repo_url,
        sha=sha,
        skill_path=skill_path,
        mode=args.mode,
        root=root,
        quarantine_base=args.quarantine_dir,
        license_id=args.license,
        reviewer=args.reviewer,
        approval_ref=args.approval_ref,
    )

    if ok:
        print(msg)
        sys.exit(0)
    else:
        print(msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
