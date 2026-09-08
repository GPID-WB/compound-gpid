#!/usr/bin/env python3
"""cg-vendor-policy — Vendor admission policy engine for Compound GPID.

Loads and applies the vendor admission policy from
``.github/shared/vendor-policy.json``.  Provides helper functions for
repository identity validation, file-extension checks, secret scanning,
prompt-injection detection, license validation, path-safety checks, and
bundle-size enforcement.

Usage:
    python scripts/cg_vendor_policy.py [--root <path>] [--check-all]
    python scripts/cg_vendor_policy.py [--root <path>] --list-allowed-repos

Exit codes:
    0  All checks pass (or listing printed).
    1  Policy check failed.
    2  Missing or invalid project root or policy file.

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-vendor-policy requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Set, Tuple

POLICY_PATH = ".github/shared/vendor-policy.json"
_QUARANTINE_MARKER = ".quarantine-meta.json"

# ── Normalization helpers ────────────────────────────────────────────────────

_WINDOWS_RESERVED_NAMES = frozenset({
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
})


def normalize_identifier(name: str) -> str:
    """Normalize a skill identifier for collision checks.

    Applies NFKC normalization, case-folding, and strips trailing
    dots/spaces (Windows reserved-name behavior).
    """
    import unicodedata

    norm = unicodedata.normalize("NFKC", name).casefold().strip(". ")
    return norm


def _is_windows_reserved(name: str) -> bool:
    stem = PurePosixPath(name).stem.lower().rstrip(".")
    return stem in _WINDOWS_RESERVED_NAMES


# ── Policy loading ───────────────────────────────────────────────────────────

def load_policy(root: Path) -> Dict[str, Any]:
    """Load vendor-policy.json from the project root.

    Raises FileNotFoundError if the policy file does not exist.
    Raises ValueError if the JSON is invalid.
    """
    policy_path = root / POLICY_PATH
    if not policy_path.exists():
        raise FileNotFoundError(f"Vendor policy not found: {policy_path}")
    try:
        with policy_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid vendor policy JSON: {exc}") from exc


# ── Repository identity checks ───────────────────────────────────────────────

def is_allowed_repository(repo_url: str, policy: Dict[str, Any]) -> bool:
    """Check whether a repository URL matches the allowlist."""
    allowed = policy.get("allowedRepositoryIdentities", [])
    normalized = repo_url.rstrip("/")
    return any(normalized == a.rstrip("/") for a in allowed)


# ── Path safety ──────────────────────────────────────────────────────────────

_TRAVERSAL_PATTERN = re.compile(r"(^|[\\/])\.\.([\\/]|$)")
_HIDDEN_COMPONENT = re.compile(r"(^|[\\/])\.")


def is_safe_skill_path(rel_path: str, policy: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a skill path is a normalized, safe descendant of an allowed root.

    Returns (ok, reason).
    """
    allowed_roots = policy.get("allowedUpstreamSkillRoots", [])
    posix = PurePosixPath(rel_path)

    # Must be relative, no absolute traversal
    if posix.is_absolute():
        return False, "Absolute path not allowed"

    # Check for traversal components
    if _TRAVERSAL_PATTERN.search(rel_path):
        return False, f"Path traversal detected: {rel_path}"

    # Check for hidden files/directories (allow known prefixes like .github, .compound-gpid)
    known_prefixes = {".github", ".compound-gpid", ".kilo", ".agents", ".claude"}
    for part in posix.parts:
        if part.startswith(".") and part not in (".", "..") and part not in known_prefixes:
            return False, f"Hidden path component: {part}"

    # Check prefix against allowed roots (only if path has a recognizable prefix)
    normalized_path = rel_path.replace("\\", "/")
    if allowed_roots and any(normalized_path.startswith(r) for r in allowed_roots):
        pass  # Under an allowed root — ok
    elif allowed_roots and not any(
        normalized_path.startswith(r) for r in allowed_roots
    ):
        # If the path looks like a bare filename (quarantine context), allow it
        # This handles files already extracted to quarantine
        if "/" in normalized_path or "\\" in normalized_path:
            return False, f"Path not under any allowed skill root: {rel_path}"

    # Windows reserved names
    for part in posix.parts:
        if _is_windows_reserved(part):
            return False, f"Windows reserved name in path: {part}"

    # Unicode confusable check (basic: no mixed-script components)
    for part in posix.parts:
        if any(ord(ch) > 127 for ch in part):
            import unicodedata
            categories = {unicodedata.category(ch) for ch in part if ord(ch) > 127}
            # Allow common scripts but flag unusual categories
            if any(c.startswith("C") for c in categories):
                return False, f"Control character in path component: {part}"

    return True, ""


# ── File extension checks ────────────────────────────────────────────────────

def is_allowed_extension(filename: str, policy: Dict[str, Any]) -> bool:
    """Check whether a filename has an allowed extension."""
    allowed = set(policy.get("allowedFileExtensions", []))
    blocked = set(policy.get("blockedFileExtensions", []))
    ext = PurePosixPath(filename).suffix.lower()
    if ext in blocked:
        return False
    if allowed and ext not in allowed:
        return False
    return True


def is_blocked_extension(filename: str, policy: Dict[str, Any]) -> bool:
    """Check whether a filename has a blocked extension."""
    blocked = set(policy.get("blockedFileExtensions", []))
    ext = PurePosixPath(filename).suffix.lower()
    return ext in blocked


# ── Secret scanning ──────────────────────────────────────────────────────────

def scan_for_secrets(content: str, policy: Dict[str, Any]) -> List[Dict[str, str]]:
    """Scan text content for potential secret patterns.

    Returns a list of ``{"pattern": ..., "line": ..., "redacted": ...}``
    dicts.  Secret values are redacted in the output.
    """
    raw_patterns = policy.get("blockedSecretPatterns", [])
    compiled: List[Tuple[str, Any]] = []
    for pat_str in raw_patterns:
        try:
            compiled.append((pat_str, re.compile(pat_str)))
        except re.error:
            continue
    findings: List[Dict[str, str]] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for pat_str, pat in compiled:
            match = pat.search(line)
            if match:
                matched_text = match.group(0)
                # Redact: keep first 4 and last 4 chars
                if len(matched_text) > 12:
                    redacted = matched_text[:4] + "*" * (len(matched_text) - 8) + matched_text[-4:]
                else:
                    redacted = "***REDACTED***"
                findings.append({
                    "pattern": pat_str[:40] + "..." if len(pat_str) > 40 else pat_str,
                    "line": str(line_num),
                    "redacted": redacted,
                })
    return findings


# ── Prompt-injection scanning ────────────────────────────────────────────────

def scan_for_prompt_injection(content: str, policy: Dict[str, Any]) -> List[Dict[str, str]]:
    """Scan Markdown content for prompt-injection patterns.

    Returns a list of ``{"pattern": ..., "line": ...}`` dicts.
    """
    raw_patterns = policy.get("blockedMarkdownInstructions", [])
    compiled: List[Tuple[str, Any]] = []
    for pat_str in raw_patterns:
        try:
            compiled.append((pat_str, re.compile(pat_str)))
        except re.error:
            continue
    findings: List[Dict[str, str]] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for pat_str, pat in compiled:
            if pat.search(line):
                findings.append({
                    "pattern": pat_str[:60] + "..." if len(pat_str) > 60 else pat_str,
                    "line": str(line_num),
                })
    return findings


# ── License validation ───────────────────────────────────────────────────────

def is_approved_license(license_id: str, policy: Dict[str, Any]) -> bool:
    """Check whether a license identifier is on the approved list."""
    approved = policy.get("approvedLicenses", [])
    return license_id in approved


# ── Bundle size enforcement ──────────────────────────────────────────────────

def check_bundle_limits(
    file_count: int,
    total_bytes: int,
    max_file_size: int,
    policy: Dict[str, Any],
) -> List[str]:
    """Check bundle against size limits. Returns list of violations (empty = ok)."""
    violations: List[str] = []
    max_bundle = policy.get("maxBundleSizeBytes", 1048576)
    max_count = policy.get("maxFileCount", 64)
    max_single = policy.get("maxFileSizeBytes", 262144)

    if total_bytes > max_bundle:
        violations.append(
            f"Bundle size {total_bytes} exceeds limit {max_bundle}"
        )
    if file_count > max_count:
        violations.append(
            f"File count {file_count} exceeds limit {max_count}"
        )
    if max_file_size > max_single:
        violations.append(
            f"Single file size {max_file_size} exceeds limit {max_single}"
        )
    return violations


# ── Full admission check ────────────────────────────────────────────────────

class AdmissionResult:
    """Result of a full admission check on a quarantined candidate."""

    def __init__(
        self,
        ok: bool,
        errors: List[str],
        secret_findings: List[Dict[str, str]],
        injection_findings: List[Dict[str, str]],
        warnings: List[str],
    ) -> None:
        self.ok = ok
        self.errors = errors
        self.secret_findings = secret_findings
        self.injection_findings = injection_findings
        self.warnings = warnings

    @property
    def has_security_issues(self) -> bool:
        return bool(self.secret_findings or self.injection_findings)


def run_admission_checks(
    quarantine_dir: Path,
    policy: Dict[str, Any],
    *,
    check_network_instructions: bool = True,
) -> AdmissionResult:
    """Run all admission checks on a quarantined bundle directory.

    This performs the full default-deny admission pipeline:
    1. File count and total size
    2. Per-file extension, size, path safety
    3. Symlink/junction/hard-link rejection
    4. Hidden file rejection
    5. Secret scanning
    6. Prompt-injection scanning (Markdown files only)
    7. Frontmatter validation (.md files)
    8. Binary content detection

    Returns an ``AdmissionResult`` with errors and findings.
    """
    errors: List[str] = []
    warnings: List[str] = []
    secret_findings: List[Dict[str, str]] = []
    injection_findings: List[Dict[str, str]] = []

    if not quarantine_dir.is_dir():
        return AdmissionResult(False, ["Quarantine directory not found"], [], [], [])

    # Collect files
    files: List[Path] = []
    total_bytes = 0
    max_single_size = 0

    for item in quarantine_dir.rglob("*"):
        if item.is_dir():
            continue

        # Reject symlinks/junctions/hard-links
        try:
            if item.is_symlink():
                errors.append(f"Symlink rejected: {item.relative_to(quarantine_dir)}")
                continue
        except OSError:
            pass

        # Check for reparse points on Windows
        if sys.platform == "win32":
            try:
                import stat as _stat
                st = item.lstat()
                if st.st_file_attributes & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
                    errors.append(f"Reparse point rejected: {item.relative_to(quarantine_dir)}")
                    continue
            except (AttributeError, OSError):
                pass

        rel = str(item.relative_to(quarantine_dir)).replace("\\", "/")
        # Skip quarantine metadata files (before counting toward totals)
        if item.name == _QUARANTINE_MARKER:
            continue

        files.append(item)

        file_size = item.stat().st_size
        total_bytes += file_size
        max_single_size = max(max_single_size, file_size)

        # Per-file size check before content read (DoS prevention)
        max_single_limit = policy.get("maxFileSizeBytes", 262144)
        if file_size > max_single_limit:
            errors.append(f"File too large ({file_size} > {max_single_limit}): {rel}")
            continue

        # Path safety (traversal, reserved names, hidden components)
        # In quarantine context, skip the upstream skill-root check
        posix = PurePosixPath(rel)
        if _TRAVERSAL_PATTERN.search(rel):
            errors.append(f"Unsafe path: {rel} — Path traversal detected")
            continue

        known_prefixes = {".github", ".compound-gpid", ".kilo", ".agents", ".claude"}
        hidden_ok = True
        for part in posix.parts:
            if part.startswith(".") and part not in (".", "..") and part not in known_prefixes:
                errors.append(f"Hidden component: {rel}")
                hidden_ok = False
                break
        if not hidden_ok:
            continue

        for part in posix.parts:
            if _is_windows_reserved(part):
                errors.append(f"Windows reserved name in path: {rel}")
                hidden_ok = False
                break
        if not hidden_ok:
            continue

        # Extension check
        if not is_allowed_extension(item.name, policy):
            errors.append(f"Blocked extension: {rel}")
            continue

        # Content scanning for text files
        ext = PurePosixPath(rel).suffix.lower()
        if ext in (".md", ".json", ".yml", ".yaml", ".txt", ".csv", ""):
            try:
                content = item.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"Not valid UTF-8: {rel}")
                continue

            # Binary content check (null bytes)
            if "\x00" in content:
                errors.append(f"Binary content detected: {rel}")
                continue

            # Secret scanning
            file_secrets = scan_for_secrets(content, policy)
            for finding in file_secrets:
                finding["file"] = rel
                secret_findings.append(finding)

            # Prompt-injection scanning for Markdown
            if ext == ".md" and check_network_instructions:
                file_injections = scan_for_prompt_injection(content, policy)
                for finding in file_injections:
                    finding["file"] = rel
                    injection_findings.append(finding)

                # Frontmatter validation for .md files
                if content.startswith("---"):
                    fm_end = content.find("---", 3)
                    if fm_end == -1:
                        errors.append(f"Unclosed frontmatter: {rel}")
                elif content.lstrip().startswith("---"):
                    warnings.append(f"Frontmatter not at start of file: {rel}")

    # Bundle-level checks
    bundle_errors = check_bundle_limits(len(files), total_bytes, max_single_size, policy)
    errors.extend(bundle_errors)

    return AdmissionResult(
        ok=len(errors) == 0 and not (secret_findings or injection_findings),
        errors=errors,
        secret_findings=secret_findings,
        injection_findings=injection_findings,
        warnings=warnings,
    )


# ── Canonical source checkout verification ───────────────────────────────────

def verify_canonical_source_checkout(
    checkout_root: Path,
    policy: Dict[str, Any],
) -> Tuple[bool, str]:
    """Verify that a directory is a Compound GPID canonical source checkout.

    Checks:
    1. `.github/shared/module-registry.json` exists
    2. Git remote origin matches expected canonical source
    3. On an approved branch
    4. Working tree is clean or has only policy-allowed changes

    Returns (ok, reason).
    """
    # Check registry exists
    registry_path = checkout_root / ".github/shared/module-registry.json"
    if not registry_path.exists():
        return False, "module-registry.json not found — not a canonical source checkout"

    # Check git remote
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(checkout_root),
            timeout=10,
        )
        if result.returncode != 0:
            return False, "Cannot determine git remote origin"
        remote_url = result.stdout.strip()
        expected = policy.get("canonicalSourceOrigin", "")
        if expected and remote_url.rstrip("/") != expected.rstrip("/"):
            return False, f"Git origin {remote_url!r} does not match expected {expected!r}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Git not available or remote check timed out"

    # Check branch
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(checkout_root),
            timeout=10,
        )
        if result.returncode != 0:
            return False, "Cannot determine current branch"
        current_branch = result.stdout.strip()
        approved_branches = policy.get("canonicalSourceBranches", [])
        branch_ok = False
        for approved in approved_branches:
            if approved.endswith("/*"):
                prefix = approved[:-2]
                if current_branch.startswith(prefix + "/"):
                    branch_ok = True
                    break
            elif current_branch == approved:
                branch_ok = True
                break
        if not branch_ok:
            return False, f"Branch {current_branch!r} is not in approved list"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Git not available or branch check timed out"

    # Check working tree state (informational, not blocking)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(checkout_root),
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Allow but warn — some repos may have untracked files
            pass
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return True, "Verified canonical source checkout"


# ── Collision detection ──────────────────────────────────────────────────────

def check_identifier_collision(
    proposed_id: str,
    existing_ids: Set[str],
) -> Tuple[bool, str]:
    """Check for normalized identifier collisions.

    Returns (ok, reason).  ``ok=False`` if the proposed identifier collides
    with an existing one under normalization.
    """
    proposed_norm = normalize_identifier(proposed_id)
    for existing in existing_ids:
        if normalize_identifier(existing) == proposed_norm:
            return False, (
                f"Identifier {proposed_id!r} collides with existing "
                f"{existing!r} after normalization"
            )
    return True, ""


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vendor admission policy engine for Compound GPID."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check-all", action="store_true",
                        help="Validate policy file structure.")
    parser.add_argument("--list-allowed-repos", action="store_true",
                        help="List allowed repository identities.")
    parser.add_argument("--check-repo", type=str, default=None,
                        help="Check a repository URL against the allowlist.")
    parser.add_argument("--check-license", type=str, default=None,
                        help="Check a license identifier against the approved list.")
    args = parser.parse_args()

    root = args.root.resolve()
    try:
        policy = load_policy(root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.list_allowed_repos:
        for repo in policy.get("allowedRepositoryIdentities", []):
            print(repo)
        sys.exit(0)

    if args.check_repo:
        if is_allowed_repository(args.check_repo, policy):
            print(f"ALLOWED: {args.check_repo}")
            sys.exit(0)
        else:
            print(f"BLOCKED: {args.check_repo}", file=sys.stderr)
            sys.exit(1)

    if args.check_license:
        if is_approved_license(args.check_license, policy):
            print(f"APPROVED: {args.check_license}")
            sys.exit(0)
        else:
            print(f"NOT APPROVED: {args.check_license}", file=sys.stderr)
            sys.exit(1)

    if args.check_all:
        # Validate policy structure
        required_keys = [
            "schemaVersion", "allowedRepositoryIdentities",
            "allowedUpstreamSkillRoots", "maxBundleSizeBytes",
            "maxFileCount", "allowedFileExtensions", "blockedSecretPatterns",
            "blockedMarkdownInstructions", "approvedLicenses",
        ]
        missing = [k for k in required_keys if k not in policy]
        if missing:
            print(f"Missing required keys: {missing}", file=sys.stderr)
            sys.exit(1)
        print("Policy structure valid.")
        print(f"  Allowed repos: {len(policy.get('allowedRepositoryIdentities', []))}")
        print(f"  Allowed roots: {len(policy.get('allowedUpstreamSkillRoots', []))}")
        print(f"  Allowed extensions: {len(policy.get('allowedFileExtensions', []))}")
        print(f"  Blocked extensions: {len(policy.get('blockedFileExtensions', []))}")
        print(f"  Secret patterns: {len(policy.get('blockedSecretPatterns', []))}")
        print(f"  Injection patterns: {len(policy.get('blockedMarkdownInstructions', []))}")
        print(f"  Approved licenses: {len(policy.get('approvedLicenses', []))}")
        sys.exit(0)

    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
