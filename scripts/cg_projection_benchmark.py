#!/usr/bin/env python3
"""cg-projection-benchmark — Before-state profile baseline matrix for projection.

Defines deterministic profile fixtures (CG-only, CR-only, mixed, and
capability-specific) and records, for each profile: a minimal requested
command/capability, the expected selected route, the expected hard-stop or
catalog result, the expected emitted inventory digest, and a supported-host
procedure. It captures source inventory, generated (selected) inventory,
advertised skill metadata, context-audit measures, and one executable
routed-task assertion per profile.

Measurement rules (R2/R14):
- Token estimates are heuristic (chars/4); this artifact never claims savings.
- Unavailable *required* host evidence is a blocking ``unavailable`` result,
  never a successful zero or an accepted baseline.
- Inventory/context reduction is tracked separately from workflow success, so
  smaller output cannot be reported as success when a selected workflow breaks.

Usage:
    python scripts/cg_projection_benchmark.py [--root <path>]
        [--output <skill-loading-baseline.json>]
        [--output-md <skill-loading-baseline.md>]
        [--profiles cg-only,cr-only,mixed,capability-python]
        [--validate]

Exit codes:
    0  Success.
    1  Validation or oracle failure.
    2  Missing or invalid project root.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-projection-benchmark requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Optional, Sequence

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import cg_audit_context as audit  # noqa: E402
import cg_context_budget as budget  # noqa: E402

DISCLAIMER = (
    "Token estimates are heuristic (chars/4) and intended for directional "
    "baseline use; they are not evidence of token savings. Unavailable required "
    "host evidence is a blocking 'unavailable' result, never a zero."
)

MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
LOCAL_CONFIG_PATH = "compound-gpid.local.md"

# ---------------------------------------------------------------------------
# Profile fixtures
# ---------------------------------------------------------------------------

PROFILES: list[dict[str, Any]] = [
    {
        "id": "cg-only",
        "description": "Technical-only project: only the /cg-* suite is selected.",
        "suites": ["cg"],
        "capabilities": [],
        "config": {"language": "both"},
        "requestedCommand": "/cg-work",
        "expectedRoute": "cg-work",
        "expectedCatalogSummary": "cg-* workflows active; cr-* inactive",
        "expectedHardStop": "cr-* capability inactive: add suite cr (or run cg-link/cg-update to regenerate)",
        "expectedInventoryIncludes": ["kernel", "suite-cg"],
        "expectedInventoryExcludes": ["suite-cr", "cap-research-output", "cap-language-research"],
        "hostProcedure": "python scripts/cg_projection_benchmark.py --profiles cg-only --validate",
    },
    {
        "id": "cr-only",
        "description": "Research-only project: only the /cr-* suite is selected.",
        "suites": ["cr"],
        "capabilities": [],
        "config": {"language": "both"},
        "requestedCommand": "/cr-work",
        "expectedRoute": "cr-work",
        "expectedCatalogSummary": "cr-* workflows active; cg-* inactive",
        "expectedHardStop": "cg-* capability inactive: add suite cg (or run cg-link/cg-update to regenerate)",
        "expectedInventoryIncludes": ["kernel", "suite-cr", "cap-research-output", "cap-language-research"],
        "expectedInventoryExcludes": ["suite-cg"],
        "hostProcedure": "python scripts/cg_projection_benchmark.py --profiles cr-only --validate",
    },
    {
        "id": "mixed",
        "description": "Mixed project: both the /cg-* and /cr-* suites are selected.",
        "suites": ["cg", "cr"],
        "capabilities": [],
        "config": {"language": "both"},
        "requestedCommand": "/cg-work",
        "expectedRoute": "cg-work",
        "expectedCatalogSummary": "cg-* and cr-* workflows active; no inactive suite",
        "expectedHardStop": None,
        "expectedInventoryIncludes": ["kernel", "suite-cg", "suite-cr"],
        "expectedInventoryExcludes": [],
        "hostProcedure": "python scripts/cg_projection_benchmark.py --profiles mixed --validate",
    },
    {
        "id": "capability-python",
        "description": "Technical project with an explicit additive python capability and an R language selector.",
        "suites": ["cg"],
        "capabilities": ["python"],
        "config": {"language": "r"},
        "requestedCommand": "/cg-skill find",
        "expectedRoute": "cg-skill find",
        "expectedCatalogSummary": "python capability active; stata/powershell inactive",
        "expectedHardStop": "stata capability inactive: remove intent or add capability (run cg-link/cg-update to regenerate)",
        "expectedInventoryIncludes": ["kernel", "suite-cg", "cap-language-python", "cap-language-r"],
        "expectedInventoryExcludes": ["cap-language-stata", "cap-language-powershell", "suite-cr"],
        "hostProcedure": "python scripts/cg_projection_benchmark.py --profiles capability-python --validate",
    },
]

PROFILE_BY_ID = {profile["id"]: profile for profile in PROFILES}


def _git_revision(root: Path) -> str:
    """Return ``<commit-time>@<short-sha>`` or the deterministic sentinel.

    A non-git root records ``"unknown-revision"`` (never wall-clock time) so
    baseline artifacts remain byte-comparable.
    """
    head_sha = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    head_time = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%cI", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if head_sha.returncode == 0 and head_time.returncode == 0:
        sha = head_sha.stdout.strip()
        stamp = head_time.stdout.strip()
        if sha and stamp:
            return f"{stamp}@{sha[:12]}"
    return "unknown-revision"


def _platform_versions() -> dict[str, str]:
    """Return python and platform version evidence for the baseline record."""
    from platform import python_version, platform

    return {"python": python_version(), "platform": platform()}


def _load_registry(root: Path) -> dict:
    path = root / MODULE_REGISTRY_PATH
    if not path.exists():
        raise FileNotFoundError(f"{MODULE_REGISTRY_PATH} not found at {root}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("module registry must be a JSON object")
    return data


def _config_text(root: Path) -> str:
    path = root / LOCAL_CONFIG_PATH
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ---------------------------------------------------------------------------
# Inventory collection
# ---------------------------------------------------------------------------


def _generated_selected_inventory(root: Path, profile: dict[str, Any]) -> dict[str, Any]:
    """Return the selected (generated) inventory for a profile's suites."""
    registry = _load_registry(root)
    ids = budget.loadable_module_ids(
        registry,
        profile["suites"],
        config=profile.get("config"),
        capabilities=profile.get("capabilities"),
    )
    globs = budget.loadable_asset_globs(registry, ids)
    return {
        "suites": list(profile["suites"]),
        "config": profile.get("config"),
        "capabilities": list(profile.get("capabilities", [])),
        "loadableModuleIds": sorted(ids),
        "loadableAssetGlobs": sorted(globs),
        "digest": budget.inventory_digest(
            registry,
            profile["suites"],
            config=profile.get("config"),
            capabilities=profile.get("capabilities"),
        ),
    }


def _source_inventory(
    files: Optional[Sequence[dict[str, Any]]] = None,
    by_category: Optional[dict[str, Any]] = None,
    root: Optional[Path] = None,
) -> dict[str, Any]:
    """Source inventory via the context-audit scanner (char/token measures)."""
    if files is None or by_category is None:
        assert root is not None
        files, by_category = audit.scan_files(root)
    total_chars = 0
    total_tokens = 0
    for file_record in files:
        total_chars += int(file_record["characters"])
        total_tokens += int(file_record["estimated_tokens"])
    return {
        "totalFiles": len(files),
        "totalCharacters": total_chars,
        "totalEstimatedTokens": total_tokens,
        "byCategory": by_category,
    }


def _advertised_skill_metadata(
    skill_rows: Sequence[dict[str, Any]],
    selected_globs: Sequence[str],
) -> list[dict[str, Any]]:
    """Advertised skill metadata restricted to the selected inventory globs."""
    if not selected_globs or not skill_rows:
        return []
    import cg_validate_modules as validator

    selected: list[dict[str, Any]] = []
    for row in skill_rows:
        candidate = f".github/skills/{row['id']}/SKILL.md"
        matched = any(validator.glob_match(pattern, candidate) for pattern in selected_globs)
        if matched:
            selected.append({
                "id": row["id"],
                "path": row["path"],
                "description": row["description"][:240],
            })
    return selected


def _context_audit_measures(root: Path, profile: dict[str, Any], report: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Selected context-audit measures for the requested command."""
    report = report or audit.build_report(root)
    workflow_rows = {
        row.get("workflow"): row
        for row in report.get("benchmark", {}).get("workflows", [])
    }
    requested = workflow_rows.get(profile["requestedCommand"])
    return {
        "requestedCommand": profile["requestedCommand"],
        "workflowAvailable": bool(requested),
        "workflowEstimatedTokens": requested.get("estimated_tokens") if requested else None,
        "workflowTotalRefs": requested.get("total_refs") if requested else None,
        "totalSourceFiles": report.get("summary", {}).get("total_files"),
        "totalSourceEstimatedTokens": report.get("summary", {}).get("total_estimated_tokens"),
        "guardrailFailureCount": len(report.get("guardrails", {}).get("failures", [])),
    }


def _baseline_context(root: Path) -> dict[str, Any]:
    """Shared, profile-independent scans used by every profile record."""
    files, by_category = audit.scan_files(root)
    return {
        "files": files,
        "by_category": by_category,
        "report": audit.build_report(root),
        "skill_rows": audit.scan_skill_metadata(root),
    }


def _skill_owner(registry: dict, skill_path: str) -> Optional[str]:
    """Owning module of a canonical skill path (or None)."""
    import cg_validate_modules as validator

    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        if any(
            isinstance(pattern, str) and validator.glob_match(pattern, skill_path)
            for pattern in module.get("ownedAssets", [])
        ):
            return module.get("id")
    return None


# ---------------------------------------------------------------------------
# Executable task oracle
# ---------------------------------------------------------------------------


def run_task_oracle(
    root: Path,
    profile: dict[str, Any],
    skill_rows: Optional[Sequence[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Execute the profile's routed-task assertion against the current source.

    Returns a dict with ``passed``, ``checks`` (list of {name, ok, detail}),
    and ``error`` when the oracle cannot be executed (``available=false``).
    """
    checks: list[dict[str, Any]] = []
    try:
        registry = _load_registry(root)
        ids = budget.loadable_module_ids(
            registry,
            profile["suites"],
            config=profile.get("config"),
            capabilities=profile.get("capabilities"),
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        return {
            "passed": False,
            "available": False,
            "checks": [],
            "error": f"oracle cannot execute: {exc}",
        }

    id_set: set[str] = set(ids)
    for module_id in profile.get("expectedInventoryIncludes", []):
        ok = module_id in id_set
        checks.append({
            "name": f"includes {module_id}",
            "ok": ok,
            "detail": "" if ok else f"{module_id} missing from loadable closure",
        })
    for module_id in profile.get("expectedInventoryExcludes", []):
        ok = module_id not in id_set
        checks.append({
            "name": f"excludes {module_id}",
            "ok": ok,
            "detail": "" if ok else f"{module_id} unexpectedly loadable",
        })

    route = profile.get("expectedRoute")
    route_file = f".github/prompts/{profile['requestedCommand'].lstrip('/')}.prompt.md"
    import cg_validate_modules as validator

    route_ok = False
    for module in registry.get("modules", []):
        if not isinstance(module, dict) or module.get("id") not in id_set:
            continue
        for pattern in module.get("ownedAssets", []):
            if isinstance(pattern, str) and validator.glob_match(pattern, route_file):
                route_ok = True
    checks.append({
        "name": f"route {route}",
        "ok": route_ok,
        "detail": "" if route_ok else "requested command not owned by selected closure",
    })

    selected_globs = budget.loadable_asset_globs(registry, id_set)
    if skill_rows is None:
        skill_rows = audit.scan_skill_metadata(root)
    advertised = _advertised_skill_metadata(skill_rows, selected_globs)
    advertised_ids = {row["id"] for row in advertised}
    leak = False
    detail = f"{len(advertised_ids)} selected skills advertised"
    for row in advertised:
        owner = _skill_owner(registry, row["path"])
        if owner not in id_set:
            leak = True
            detail = f"inactive skill {row['id']} advertised (owner {owner})"
    if not leak:
        excluded_ids: set[str] = set()
        for module_id in profile.get("expectedInventoryExcludes", []):
            for module in registry.get("modules", []):
                if not isinstance(module, dict) or module.get("id") != module_id:
                    continue
                for candidate_row in skill_rows:
                    candidate = f".github/skills/{candidate_row['id']}/SKILL.md"
                    if any(
                        isinstance(pattern, str) and validator.glob_match(pattern, candidate)
                        for pattern in module.get("ownedAssets", [])
                    ):
                        excluded_ids.add(candidate_row["id"])
        leaked = advertised_ids & excluded_ids
        if leaked:
            leak = True
            detail = f"inactive skill(s) advertised: {sorted(leaked)}"
    checks.append({
        "name": "catalog does not advertise inactive skill bodies",
        "ok": not leak,
        "detail": detail,
    })

    passed = all(check["ok"] for check in checks)
    return {"passed": passed, "available": True, "checks": checks, "error": None}


# ---------------------------------------------------------------------------
# Baseline payload
# ---------------------------------------------------------------------------


def collect_profile_baseline(
    root: Path,
    profile: dict[str, Any],
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Collect one profile's before-state baseline record.

    Registry/inventory failures are reported as a blocking ``unavailable``
    record (R2/R14), never a silent success or a crash.
    """
    ctx = context or _baseline_context(root)
    try:
        generated = _generated_selected_inventory(root, profile)
        inventory_ok = True
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        generated = {
            "suites": list(profile["suites"]),
            "loadableModuleIds": [],
            "loadableAssetGlobs": [],
            "digest": None,
            "error": str(exc),
        }
        inventory_ok = False
    selected_globs = generated.get("loadableAssetGlobs", [])
    oracle = run_task_oracle(root, profile, skill_rows=ctx["skill_rows"])
    record: dict[str, Any] = {
        "id": profile["id"],
        "description": profile.get("description", ""),
        "suites": list(profile["suites"]),
        "capabilities": list(profile.get("capabilities", [])),
        "config": profile.get("config"),
        "requestedCommand": profile["requestedCommand"],
        "expectedRoute": profile["expectedRoute"],
        "expectedCatalogSummary": profile["expectedCatalogSummary"],
        "expectedHardStop": profile.get("expectedHardStop"),
        "hostProcedure": profile["hostProcedure"],
        "generatedInventory": generated,
        "advertisedSkillCount": len(_advertised_skill_metadata(ctx["skill_rows"], selected_globs)),
        "sourceInventory": _source_inventory(files=ctx["files"], by_category=ctx["by_category"]),
        "contextAudit": _context_audit_measures(root, profile, report=ctx["report"]),
    }
    if oracle.get("available"):
        record["taskOracle"] = {
            "passed": oracle["passed"],
            "checks": oracle["checks"],
        }
        record["oracleStatus"] = "passed" if oracle["passed"] else "failed"
    else:
        record["taskOracle"] = None
        record["oracleStatus"] = "unavailable"

    if not inventory_ok:
        record["hostEvidence"] = {
            "status": "unavailable",
            "note": f"inventory could not be collected: {generated.get('error')}",
        }
    else:
        record["hostEvidence"] = {
            "status": "available",
            "note": "static inventory and oracle executed against repository source",
        }
    return record


def run_benchmark(root: Path, profile_ids: Optional[Sequence[str]] = None) -> dict[str, Any]:
    """Build the full before-state baseline payload for the selected profiles."""
    if profile_ids is None:
        selected_ids = list(PROFILES)
    else:
        known = {profile["id"] for profile in PROFILES}
        unknown = [pid for pid in profile_ids if pid not in known]
        if unknown:
            raise ValueError(f"unknown profile id(s): {', '.join(sorted(unknown))}")
        selected_ids = [profile for profile in PROFILES if profile["id"] in profile_ids]
    # Profile-independent scans run once and are shared by every record.
    context = _baseline_context(root)
    profiles = [collect_profile_baseline(root, pid, context=context) for pid in selected_ids]
    return {
        "schemaVersion": 1,
        "kind": "skill-loading-baseline",
        "generated": audit._deterministic_generated_stamp(root),
        "sourceRevision": _git_revision(root),
        "platformVersions": _platform_versions(),
        "disclaimer": DISCLAIMER,
        "collectionCommands": [
            "python scripts/cg_projection_benchmark.py --validate",
            "python scripts/cg_audit_context.py --format both",
        ],
        "measurementPolicy": {
            "tokenEstimate": "chars/4 heuristic",
            "workflowSuccessTrackedSeparately": True,
            "unavailableHostIsBlocking": True,
        },
        "profiles": profiles,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    """Validate a baseline payload. Returns a list of error messages (empty = valid)."""
    errors: list[str] = []
    if payload.get("kind") != "skill-loading-baseline":
        errors.append("payload kind must be 'skill-loading-baseline'")
    if not payload.get("disclaimer"):
        errors.append("payload missing heuristic/disclaimer statement")
    if not isinstance(payload.get("profiles"), list) or not payload["profiles"]:
        errors.append("payload must define at least one profile")
        return errors
    for record in payload["profiles"]:
        for field in (
            "id", "suites", "config", "requestedCommand", "expectedRoute",
            "expectedCatalogSummary", "hostProcedure", "generatedInventory",
            "sourceInventory", "contextAudit", "hostEvidence",
        ):
            if field not in record:
                errors.append(f"profile {record.get('id')} missing required field: {field}")
        if "digest" not in record.get("generatedInventory", {}):
            errors.append(f"profile {record.get('id')} generated inventory missing digest")
        oracle_status = record.get("oracleStatus")
        if oracle_status not in ("passed", "failed", "unavailable"):
            errors.append(f"profile {record.get('id')} has invalid oracleStatus")
        if oracle_status == "unavailable":
            errors.append(
                f"profile {record.get('id')} task oracle is unavailable; "
                "unavailable required host evidence is blocking"
            )
        host_status = record.get("hostEvidence", {}).get("status")
        requires_host = bool(record.get("generatedInventory", {}).get("loadableModuleIds"))
        if host_status != "available" and requires_host:
            errors.append(
                f"profile {record.get('id')} requires host evidence but reports {host_status}"
            )
        if oracle_status == "failed":
            errors.append(f"profile {record.get('id')} task oracle failed")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the baseline payload as a compact Markdown artifact."""
    lines = [
        "# Skill-Loading Baseline (Before State)",
        "",
        f"_Generated: {payload.get('generated')}_",
        f"_Source revision: {payload.get('sourceRevision')}_",
        "",
        f"> {payload.get('disclaimer', DISCLAIMER)}",
        "",
        "## Profiles",
        "",
        "| Profile | Suites | Requested Command | Route | Oracle | Host",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in payload.get("profiles", []):
        lines.append(
            "| {id} | {suites} | {cmd} | {route} | {oracle} | {host} |".format(
                id=record["id"],
                suites=", ".join(record.get("suites", [])),
                cmd=record.get("requestedCommand", ""),
                route=record.get("expectedRoute", ""),
                oracle=record.get("oracleStatus", ""),
                host=record.get("hostEvidence", {}).get("status", ""),
            )
        )
    digest_rows = [
        [r["id"], r.get("generatedInventory", {}).get("digest", ""), r.get("advertisedSkillCount")]
        for r in payload.get("profiles", [])
    ]
    if digest_rows:
        lines.extend(["", "## Inventory Digests", "", "| Profile | Digest | Advertised Skills |", "| --- | --- | --- |"])
        for row in digest_rows:
            lines.append(f"| {row[0]} | `{row[1]}` | {row[2]} |")
    return "\n".join(lines) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compute the skill-loading baseline matrix.")
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument("--output", default=".cg-docs/cost/skill-loading-baseline.json", help="JSON output path")
    parser.add_argument("--output-md", default=".cg-docs/cost/skill-loading-baseline.md", help="Markdown output path")
    parser.add_argument("--profiles", default=None, help="Comma-separated profile ids (default: all)")
    parser.add_argument("--validate", action="store_true", help="Validate the payload instead of writing")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    profile_ids = None
    if args.profiles:
        profile_ids = [item.strip() for item in args.profiles.split(",") if item.strip()]
        unknown = [pid for pid in profile_ids if pid not in PROFILE_BY_ID]
        if unknown:
            print(f"Error: unknown profile id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1

    payload = run_benchmark(root, profile_ids)
    errors = validate_payload(payload)
    if errors:
        print("Projection benchmark validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.validate:
        print(json.dumps({"valid": True, "profiles": len(payload["profiles"])}, indent=2))
        return 0

    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[cg-projection-benchmark] Wrote {output}")

    if args.output_md:
        md_path = root / args.output_md
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        print(f"[cg-projection-benchmark] Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
