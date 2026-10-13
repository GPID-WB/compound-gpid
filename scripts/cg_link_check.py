#!/usr/bin/env python3
"""Report cg-link actions against local source bytes, without update or writes.

The shell entrypoints run this worker with Python -B. Desired selection and
projection bytes are resolved in memory, including when no manifest exists.
The report is not an authorization to delete or overwrite a path.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import cg_project_manifest as manifest_module
import cg_project_projection as projection
import cg_retire_native_evidence as retirement
from cg_link_check_global import global_kilo_information
from cg_link_check_paths import (
    COPY_MARKER, file_row, inspect_path, inventory, legacy_rows, mirror_rows,
)
import secure_fs

DEFAULT_CONFIG = "---\nsuites: [cg]\n---\n"
LEGACY_MAPPINGS = (
    ".claude/model-mapping.claude.json", ".agents/model-mapping.codex.json",
    ".opencode/model-mapping.opencode.json", ".kilo/model-mapping.kilo.json",
)


def check_project(root: Path, source: Path, platforms: list[str],
                  force: bool = False) -> dict[str, Any]:
    """Build the read-only current-project report.

    Args:
        root: Consumer project to inspect.
        source: Current local Compound GPID source, never updated here.
        platforms: Selected canonical platform ids.
        force: Whether ordinary cg-link would replace foreign directory links.
    Returns:
        Path records, current verification findings and separate manual actions.
    Example:
        ``check_project(Path("project"), Path("source"), ["kilo"])``.
    """
    mapping = projection.load_target_mapping(source)
    targets = [t for t in mapping["targets"] if t["id"] in platforms]
    selected_roots = [
        name for target in targets
        for name in target.get("projectRoots", {}).get("managed", [])
    ]
    rows: dict[str, dict] = {}
    manual = []
    config_state, _, config_error = inspect_path(
        root, manifest_module.LOCAL_CONFIG_PATH
    )
    if config_error:
        raise ValueError(f"unsafe project config: {config_error}")
    manifest_driven = config_state != "missing"
    config_text = DEFAULT_CONFIG
    if manifest_driven:
        config_text = secure_fs.secure_read_bytes(
            root, manifest_module.LOCAL_CONFIG_PATH
        ).decode("utf-8")
    desired = manifest_module.resolve_active_manifest(
        root, config_text=config_text, platforms=platforms, source_root=source
    )
    plan = projection.build_projection_plan(
        source, desired, mapping=mapping, project_root=root, config_text=config_text
    )
    previous = projection._previous_ownership(root)
    scalar = projection._read_managed_json(
        root, ".compound-gpid/managed-files.json"
    ).get("files", {})
    if not isinstance(scalar, dict):
        raise ValueError("managed-files.json files must be an object")
    for target in targets:
        for unit in target["installUnits"]:
            if not (source / unit["source"]).exists():
                manual.append(f"Missing source unit: {unit['source']}")
    for row in legacy_rows(root, source, targets, scalar, manifest_driven, force):
        rows[row["path"]] = row
    for row in mirror_rows(root, source, mapping["targets"]):
        rows[row["path"]] = row
    mirror_links = [row["path"] for row in rows.values()
                    if row["reason"] == "recognized managed compatibility mirror link"]
    if manifest_driven:
        legacy_copilot = projection._managed_copilot_link(root, source)
        for entry in plan.entries:
            if any(projection._is_within_relative(entry.destination, link)
                   for link in mirror_links):
                continue  # Physical mirror files are checked above without following the link.
            record = previous.get(entry.destination, {})
            checksum = record.get("sha256", "") or scalar.get(
                entry.destination, {}
            ).get("checksum", "")
            row = file_row(root, entry.destination, entry.sha256, checksum)
            if entry.platform == "copilot" and legacy_copilot:
                row.update(
                    owner="managed", action="migrate/project", manual=False,
                    reason="exact legacy Copilot skill link is migrated before publication",
                )
            rows[entry.destination] = row
        for relative, record in sorted(previous.items()):
            if relative not in rows and not any(
                projection._is_within_relative(relative, link) for link in mirror_links
            ) and any(
                projection._is_within_relative(relative, name)
                for name in selected_roots
            ):
                rows[relative] = file_row(
                    root, relative, "", record.get("sha256", ""), stale=True
                )
        for bundle, expected in projection._planned_bundle_files(plan).items():
            path = root / bundle
            if (path.is_dir() and not projection._is_link_or_reparse_path(path)
                    and not legacy_copilot):
                for relative in sorted(set(inventory(root, bundle)) - expected):
                    row = rows.get(relative) or file_row(root, relative, "", "")
                    row.update(
                        action="preserve/block", manual=True,
                        reason="unexpected file in selected managed bundle",
                    )
                    rows[relative] = row
    for managed_root in selected_roots:
        for relative in inventory(root, managed_root):
            if relative in rows or relative in retirement.NATIVE_PATHS:
                continue
            receipt = relative.endswith((
                "/" + COPY_MARKER, "/.compound-gpid-generated.json"
            ))
            row = file_row(root, relative, "", "")
            row.update(
                action="preserve", manual=not receipt,
                reason="ownership receipt retained; not a deletion target" if receipt
                else "old/unrecorded managed-root leftover; no deletion proof",
            )
            rows[relative] = row
    manifest_state, _, manifest_error = inspect_path(
        root, manifest_module.ACTIVE_MANIFEST_PATH
    )
    stale_reason = "desired manifest resolved in memory; no saved manifest"
    if manifest_state == "file":
        try:
            committed = projection._read_managed_json(
                root, manifest_module.ACTIVE_MANIFEST_PATH
            )
            if manifest_module.validate_manifest(committed):
                stale_reason = "old/invalid manifest; desired selection resolved in memory"
            else:
                stale = manifest_module.manifest_stale(committed, desired)
                stale_reason = "stale selection: " + ", ".join(stale) if stale else "current selection"
        except ValueError:
            stale_reason = "old/invalid manifest; desired selection resolved in memory"
    rows[manifest_module.ACTIVE_MANIFEST_PATH] = dict(
        path=manifest_module.ACTIVE_MANIFEST_PATH,
        owner="managed" if manifest_state != "missing" else "unowned",
        state=manifest_state, action="refresh" if manifest_driven else "none",
        reason=manifest_error or stale_reason, manual=bool(manifest_error),
    )
    if not manifest_driven and manifest_state != "missing":
        manual.append(
            "Saved active manifest without local config: ordinary projection cannot "
            "resolve selection. Restore the project config before linking."
        )
    for relative in LEGACY_MAPPINGS:
        if relative in scalar:
            rows[relative] = file_row(
                root, relative, "", scalar[relative].get("checksum", ""), stale=True
            )
    native_rows = []
    claims_error = ""
    try:
        claims = retirement._claims(retirement._snapshot(root))
    except (OSError, ValueError, UnicodeError) as error:
        claims, claims_error = {}, str(error)
    for relative in retirement.NATIVE_PATHS:
        state, _, _ = inspect_path(root, relative)
        if state != "missing":
            row = file_row(root, relative, "", claims.get(relative, ""), stale=True)
            row["reason"] = (
                "9020/9021 native-plugin residue: " + (claims_error or row["reason"])
            )
            if claims_error:
                row.update(action="preserve/block", manual=True)
            native_rows.append(row)
    if any(row["manual"] for row in native_rows):
        for row in native_rows:
            row.update(action="preserve/block", manual=True)
            row["reason"] += "; retirement is all-or-nothing"
    rows.update((row["path"], row) for row in native_rows)
    for relative in (
        manifest_module.OWNERSHIP_STATE_PATH, manifest_module.TRANSACTION_JOURNAL_PATH,
        ".compound-gpid/managed-files.json", ".gitignore",
    ):
        state, _, error = inspect_path(root, relative)
        rows[relative] = dict(
            path=relative, owner="managed" if relative != ".gitignore" else "unowned",
            state=state, action="refresh" if state != "missing" else "create",
            reason=error or "normal link maintains managed state/block; check does not write it",
            manual=bool(error),
        )
    journal = projection._read_managed_json(
        root, manifest_module.TRANSACTION_JOURNAL_PATH
    )
    if journal and (
        manifest_module.validate_transaction_journal(journal)
        or journal.get("state") not in ("empty", "committed", "rolled-back")
    ):
        rows[manifest_module.TRANSACTION_JOURNAL_PATH].update(
            action="recover/block", manual=True,
            reason="publication journal requires recovery or reconciliation; check never recovers",
        )
    verification = projection.verify_projection(root, plan)
    for row in rows.values():
        if row["manual"]:
            manual.append(f"{row['path']}: {row['reason']}")
    return dict(
        paths=sorted(rows.values(), key=lambda row: row["path"]),
        manual=sorted(set(manual)), verification=verification,
        manifestDriven=manifest_driven,
    )


def main(argv: list[str] | None = None) -> int:
    """Write the report to stdout; return 0 nonblocking, 1 blocked, 2 usage.

    Args:
        argv: Worker arguments, or process arguments when omitted.
    Returns:
        The report exit code. No update, publish, recovery or host runs occur.
    Example:
        ``main(["--root", ".", "--source-root", "source", "--platforms", "kilo"])``.
    """
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--platforms", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = check_project(
            args.root.absolute(), args.source_root.resolve(),
            args.platforms.split(","), args.force,
        )
    except (OSError, ValueError, UnicodeError, TypeError, AttributeError) as error:
        sys.stdout.write(
            f"Compound GPID - Link Check (read-only)\nManual action required:\n  {error}\n"
        )
        return 1
    sys.stdout.write(
        "Compound GPID - Link Check (read-only)\n"
        "Local source only; no update, project/state/gitignore/HOME/cache writes.\n"
        "PATH | OWNER | CURRENT STATE | cg-link WOULD | REASON\n"
    )
    if not report["manifestDriven"]:
        sys.stdout.write(
            "Mode: legacy install units (no local config); desired comparison "
            "uses the resolver's default CG selection in memory.\n"
        )
    for row in report["paths"]:
        state = row["state"]
        if row.get("sha256"):
            state += " sha256=" + row["sha256"]
        sys.stdout.write(
            f"{row['path']} | {row['owner']} | {state} | "
            f"{row['action']} | {row['reason']}\n"
        )
    sys.stdout.write(
        f"Current projection verification: {len(report['verification'])} finding(s). "
        "Missing/old desired output is not itself a blocker.\n"
    )
    sys.stdout.write("Global Kilo settings (INFORMATION ONLY; never block or write):\n")
    for item in global_kilo_information(args.source_root.resolve()):
        sys.stdout.write("  " + item + "\n")
    sys.stdout.write("Manual action required:\n")
    for item in report["manual"] or ["none"]:
        sys.stdout.write("  " + item + "\n")
    return 1 if report["manual"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
