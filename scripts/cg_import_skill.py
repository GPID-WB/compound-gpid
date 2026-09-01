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
credentials, nonrecursive public GitHub tree/blob traversal, and a network-free
apply after quarantined admission.

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
import stat
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
import secure_fs
from skill_management.providers.github import (
    AcquisitionLimits,
    GitHubAcquisitionError,
    GitHubProvider,
    normalize_public_github_origin,
    normalize_source_path,
)
from skill_management import planning as lifecycle_planning
from skill_management.context import (
    discover_context,
    require_maintainer_write_context,
)
from skill_management.services import admission as common_admission
from skill_management.services import bundles as bundle_service
from skill_management.services import maintenance as maintenance_service
from skill_management.services import provenance as provenance_service

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


# ── Bounded GitHub provider fetch ───────────────────────────────────────────

def fetch_to_quarantine(
    repo_url: str,
    sha: str,
    skill_path: str,
    quarantine_dir: Path,
    policy: Dict[str, Any],
) -> Tuple[bool, str, List[str]]:
    """Fetch exact GitHub blobs under canonical limits into new quarantine."""
    limits = AcquisitionLimits(
        max_metadata_bytes=int(policy.get("maxProviderMetadataBytes", 1024 * 1024)),
        max_tree_depth=int(policy.get("maxProviderTreeDepth", 16)),
        max_entries=int(policy.get("maxFileCount", 64)),
        max_file_bytes=int(policy.get("maxFileSizeBytes", 262144)),
        max_total_bytes=int(policy.get("maxBundleSizeBytes", 1048576)),
    )
    try:
        acquired = GitHubProvider().acquire(repo_url, sha, skill_path, limits)
        quarantine_dir.mkdir(parents=True, exist_ok=False)
        metadata = os.lstat(str(quarantine_dir))
        if stat.S_ISLNK(metadata.st_mode) or bool(
            getattr(metadata, "st_file_attributes", 0) & 0x400
        ) or not stat.S_ISDIR(metadata.st_mode):
            return False, "Quarantine directory is a link or reparse point", []
        skill_name = PurePosixPath(skill_path).name
        fetched_files = []
        for item in acquired.files:
            relative = PurePosixPath(skill_name) / item.path
            secure_fs.secure_write_bytes(
                quarantine_dir,
                relative,
                item.content,
                executable=False,
                expected_state=secure_fs.ExpectedFileState.absent(),
            )
            fetched_files.append(relative.as_posix())
        return True, f"Fetched {len(fetched_files)} verified Git blobs", fetched_files
    except FileExistsError:
        return False, "Quarantine destination already exists; preserve and reconcile it", []
    except (GitHubAcquisitionError, OSError, ValueError) as error:
        return False, f"Bounded GitHub acquisition failed: {error}", []


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
    owner: str = "",
    capability: str = "",
    suites: Tuple[str, ...] = ("cg", "cr"),
    platforms: Tuple[str, ...] = (
        "copilot",
        "claude-code",
        "codex",
        "opencode",
        "kilo",
    ),
    activation_cost: str = "high",
    triggers: Tuple[str, ...] = (),
    selectors: Tuple[Dict[str, str], ...] = (),
    apply_digest: str = "",
) -> Tuple[bool, str]:
    """Plan or apply legacy vendor input through the common lifecycle service.

    The compatibility entry performs no direct source or registry writes. With
    no ``apply_digest`` it stores and returns a reviewable plan. With a digest it
    recomputes and applies that exact plan through the held-lock transaction.
    """
    del policy
    try:
        root = Path(source_checkout).resolve(strict=True)
        context = discover_context(
            root,
            root,
            invocation_path=root,
            trusted_source_root=root,
        )
        require_maintainer_write_context(context)
        normalized_origin = normalize_public_github_origin(repo_url)
        normalized_path = normalize_source_path(skill_path)
        if not owner or not capability or not triggers:
            raise ValueError(
                "Legacy vendor mode requires explicit owner, capability, and triggers"
            )
        common_policy = common_admission.load_admission_policy(root)
        if not common_admission.repository_allowed_for_plugin(
            normalized_origin, common_policy
        ):
            raise common_admission.AdmissionPolicyError(
                "Plugin repository is not on the canonical allowlist"
            )
        skill_name = PurePosixPath(normalized_path).name
        quarantine_skill = Path(quarantine_dir) / skill_name
        if not quarantine_skill.is_dir():
            candidates = [
                item
                for item in Path(quarantine_dir).iterdir()
                if item.is_dir() and item.name != "_clone_tmp"
            ]
            if len(candidates) != 1:
                raise ValueError("Cannot locate one quarantined skill bundle")
            quarantine_skill = candidates[0]
        candidate = bundle_service.inventory_bundle(
            quarantine_skill.parent,
            quarantine_skill.name,
            origin="plugin-canonical",
        )
        admitted = common_admission.admit_bundle(
            quarantine_skill, license_id, common_policy
        )
        if not admitted.ok:
            first = admitted.findings[0]
            raise common_admission.AdmissionPolicyError(
                f"Plugin admission rejected {first.path or 'bundle'}: {first.code}"
            )
        metadata = maintenance_service.CapabilityMetadata(
            capability,
            owner,
            tuple(suites),
            tuple(platforms),
            activation_cost,
            tuple(triggers),
            tuple(dict(item) for item in selectors),
        )
        evidence_digest = hashlib.sha256(admitted.evidence_bytes).hexdigest()
        record = provenance_service.provenance_record(
            candidate.identifier,
            "plugin-canonical",
            normalized_origin,
            normalized_path,
            sha,
            candidate.digest,
            "imported",
            reviewer,
            approval_ref,
            policy_digest=common_policy.digest,
            review_evidence_digest=evidence_digest,
        )
        plan = maintenance_service.plan_canonical_add(
            root,
            root,
            candidate,
            metadata,
            record,
            operation="import",
            role=context.role,
            policy_digest=common_policy.digest,
            review_evidence_digest=evidence_digest,
            license_id=license_id,
        )
        if not apply_digest:
            stored = lifecycle_planning.store_plan(root, plan)
            return True, (
                f"Planned plugin vendoring for {skill_name}; "
                f"apply with digest {stored.digest}"
            )
        result = lifecycle_planning.apply_plan(root, plan, apply_digest)
        return True, f"Plugin vendoring {result.state}: {skill_name}"
    except (OSError, ValueError, PermissionError) as error:
        return False, f"Common plugin vendoring failed: {error}"


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
    owner: str = "",
    capability: str = "",
    suites: Tuple[str, ...] = ("cg", "cr"),
    platforms: Tuple[str, ...] = (
        "copilot",
        "claude-code",
        "codex",
        "opencode",
        "kilo",
    ),
    activation_cost: str = "high",
    triggers: Tuple[str, ...] = (),
    selectors: Tuple[Dict[str, str], ...] = (),
    apply_digest: str = "",
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
    quarantine_base = Path(quarantine_base)
    if not quarantine_base.is_absolute():
        quarantine_base = root / quarantine_base
    quarantine_base = Path(os.path.abspath(str(quarantine_base)))
    try:
        quarantine_base.relative_to(root)
        secure_fs.revalidate_destination_ancestors(
            root, quarantine_base / "candidate"
        )
    except (ValueError, secure_fs.SecureMutationError) as exc:
        return False, f"Quarantine path must be confined under project root: {exc}"
    quarantine_dir = quarantine_base / f"{sha[:12]}_{PurePosixPath(skill_path).name}"

    if quarantine_dir.exists() or quarantine_dir.is_symlink():
        return False, "Quarantine destination already exists; preserve and reconcile it"

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

    if not admission.ok and mode != "vendor":
        return False, (
            f"Admission failed with {len(admission.errors)} error(s), "
            f"{len(admission.secret_findings)} secret finding(s), "
            f"{len(admission.injection_findings)} injection finding(s). "
            f"Review: {review_path}"
        )

    # Step 9: Vendor mode re-admits through the common canonical service. The
    # legacy result above remains review context and cannot approve or block the
    # common plugin-scope plan.
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
            owner=owner,
            capability=capability,
            suites=suites,
            platforms=platforms,
            activation_cost=activation_cost,
            triggers=triggers,
            selectors=selectors,
            apply_digest=apply_digest,
        )
        if not ok:
            return False, f"Vendor registration failed: {msg}"
        return True, msg

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
    parser.add_argument("--owner", type=str, default="", help="Explicit owner module.")
    parser.add_argument("--capability", type=str, default="", help="Explicit capability id.")
    parser.add_argument("--suites", default="cg,cr", help="Comma-separated suite eligibility.")
    parser.add_argument(
        "--platforms",
        default="copilot,claude-code,codex,opencode,kilo",
        help="Comma-separated platform eligibility.",
    )
    parser.add_argument(
        "--activation-cost",
        choices=["low", "medium", "high"],
        default="high",
    )
    parser.add_argument("--triggers", default="", help="Comma-separated task triggers.")
    parser.add_argument("--selectors", default="[]", help="Strict selector JSON array.")
    parser.add_argument("--apply", default="", help="Apply one reviewed plan digest.")
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

    try:
        selector_value = json.loads(args.selectors)
        if not isinstance(selector_value, list) or any(
            not isinstance(item, dict)
            or set(item) != {"field", "operator", "value"}
            or any(not isinstance(value, str) or not value for value in item.values())
            for item in selector_value
        ):
            raise ValueError("selectors must contain field/operator/value objects")
        selectors = tuple(dict(item) for item in selector_value)
    except (json.JSONDecodeError, ValueError) as error:
        print(f"Error: invalid --selectors: {error}", file=sys.stderr)
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
        owner=args.owner,
        capability=args.capability,
        suites=tuple(item.strip() for item in args.suites.split(",") if item.strip()),
        platforms=tuple(
            item.strip() for item in args.platforms.split(",") if item.strip()
        ),
        activation_cost=args.activation_cost,
        triggers=tuple(
            item.strip() for item in args.triggers.split(",") if item.strip()
        ),
        selectors=selectors,
        apply_digest=args.apply,
    )

    if ok:
        print(msg)
        sys.exit(0)
    else:
        print(msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
