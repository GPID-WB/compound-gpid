"""Validated canonical registry snapshots and public owner matching APIs."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import secure_fs

from skill_management import contracts
from skill_management import paths as path_policy
from skill_management.paths import glob_match
from skill_management.services import bundles
from skill_management.services import provenance


MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
PROJECT_REGISTRY_PATH = ".compound-gpid/project-skill-registry.json"
PROVENANCE_ROOT = provenance.PROVENANCE_ROOT


class RegistryValidationError(ValueError):
    """Raised when the canonical registry cannot form a valid snapshot."""


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def matching_asset_owners(registry: Mapping[str, Any], asset: str) -> Tuple[str, ...]:
    """Return every module whose owned-assets patterns match one asset.

    Args:
        registry: Parsed canonical module registry.
        asset: Portable repository-relative canonical asset path.

    Returns:
        Sorted unique module identifiers.

    Example:
        ``matching_asset_owners(registry, ".github/skills/x/SKILL.md")``
        returns the owner tuple for that skill.
    """
    owners = set()
    for module in registry.get("modules", []):
        if not isinstance(module, Mapping) or not isinstance(module.get("id"), str):
            continue
        if any(
            isinstance(pattern, str) and glob_match(pattern, asset)
            for pattern in module.get("ownedAssets", [])
        ):
            owners.add(module["id"])
    return tuple(sorted(owners))


@dataclass(frozen=True)
class RegistrySnapshot:
    """One deterministic validated canonical registry snapshot.

    Args:
        source_root: Canonical Compound GPID source root.
        digest: SHA-256 of the source registry bytes or canonical fixture data.
        registry: Detached parsed registry data.
        modules: Module records in declared order.
        capabilities: Capability records in declared order.

    Example:
        ``snapshot = RegistrySnapshot.from_data(root, registry)``
    """

    source_root: Path
    digest: str
    registry: Mapping[str, Any]
    modules: Tuple[Mapping[str, Any], ...]
    capabilities: Tuple[Mapping[str, Any], ...]

    @classmethod
    def from_data(
        cls,
        source_root: Path,
        registry: Mapping[str, Any],
        *,
        digest: Optional[str] = None,
        validate: bool = True,
    ) -> "RegistrySnapshot":
        """Build a detached snapshot from parsed registry data.

        Args:
            source_root: Canonical source root associated with the data.
            registry: Parsed registry object.
            digest: Optional exact source digest.
            validate: Whether to run canonical schema and layer validation.

        Returns:
            Validated immutable snapshot wrapper.

        Raises:
            RegistryValidationError: If registry structure or dependencies fail.

        Example:
            ``RegistrySnapshot.from_data(root, fixture_registry)``
        """
        if not isinstance(registry, Mapping):
            raise RegistryValidationError("Module registry must be a JSON object.")
        detached = json.loads(json.dumps(registry, ensure_ascii=False))
        if validate:
            import cg_validate_modules as validator

            errors = list(validator.validate_registry_schema(detached))
            errors.extend(validator.check_layer_rules(detached))
            if errors:
                raise RegistryValidationError(
                    "Module registry is invalid: " + "; ".join(sorted(set(errors)))
                )
        canonical = contracts.canonical_json_bytes(detached)
        snapshot_digest = digest or hashlib.sha256(canonical).hexdigest()
        frozen_registry = _freeze(detached)
        modules = tuple(frozen_registry.get("modules", ()))
        capabilities = tuple(frozen_registry.get("capabilities", ()))
        return cls(
            Path(source_root).resolve(),
            snapshot_digest,
            frozen_registry,
            modules,
            capabilities,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a detached mutable copy for existing resolver APIs.

        Returns:
            Deep JSON-compatible copy of the registry.

        Example:
            ``resolver(snapshot.to_dict())``
        """
        return _thaw(self.registry)

    def owners_for_asset(self, asset: str) -> Tuple[str, ...]:
        """Return all canonical owners for one asset path.

        Args:
            asset: Repository-relative canonical asset path.

        Returns:
            Sorted owner identifiers.

        Example:
            ``snapshot.owners_for_asset(skill_path)``
        """
        return matching_asset_owners(self.registry, asset)

    def owner_for_asset(self, asset: str) -> Optional[str]:
        """Return one owner, or fail when an asset has multiple owners.

        Args:
            asset: Repository-relative canonical asset path.

        Returns:
            One owner identifier, or ``None`` when unowned.

        Raises:
            RegistryValidationError: If more than one owner matches.

        Example:
            ``snapshot.owner_for_asset(skill_path)``
        """
        owners = self.owners_for_asset(asset)
        if len(owners) > 1:
            raise RegistryValidationError(
                f"Canonical asset has multiple owners: {asset} -> {list(owners)!r}"
            )
        return owners[0] if owners else None

    def capability_for_owner(self, owner: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return the one capability record assigned to an owner module.

        Args:
            owner: Owning module identifier, if known.

        Returns:
            Detached capability record or ``None``.

        Raises:
            RegistryValidationError: If duplicate records name one owner.

        Example:
            ``snapshot.capability_for_owner("cap-language-python")``
        """
        if owner is None:
            return None
        matches = [item for item in self.capabilities if item.get("owningModule") == owner]
        if len(matches) > 1:
            raise RegistryValidationError(
                f"Module {owner!r} has multiple capability records."
            )
        return _thaw(matches[0]) if matches else None

    def capability_by_id(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """Return one capability record by stable identifier.

        Args:
            capability_id: Capability identifier.

        Returns:
            Detached capability record or ``None``.

        Example:
            ``snapshot.capability_by_id("python")``
        """
        for capability in self.capabilities:
            if capability.get("id") == capability_id:
                return _thaw(capability)
        return None


@dataclass(frozen=True)
class CombinedRegistrySnapshot:
    """Validated canonical registry plus an isolated project overlay.

    Args:
        canonical: Canonical module registry snapshot.
        project_root: Consumer project root.
        project_registry_digest: Digest of exact committed project registry bytes.
        provenance_digest: Digest of the complete project provenance inventory.
        project_records: Strict project records ordered by identifier.
        project_bundles: Exact project bundle inventories ordered by identifier.
        provenance_records: Strict provenance records ordered by identifier.

    Example:
        ``snapshot.project_capability_by_id("project-skill-example")``
    """

    canonical: RegistrySnapshot
    project_root: Path
    project_registry_digest: str
    provenance_digest: str
    project_records: Tuple[Mapping[str, Any], ...]
    project_bundles: Tuple[bundles.BundleInventory, ...]
    provenance_records: Tuple[Mapping[str, Any], ...]
    canonical_bundles: Tuple[bundles.BundleInventory, ...]
    canonical_provenance_records: Tuple[Mapping[str, Any], ...]

    @property
    def canonical_digest(self) -> str:
        """Return the canonical registry source digest."""
        return self.canonical.digest

    def project_record_by_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Return a detached project record by immutable skill identifier."""
        for record in self.project_records:
            if record.get("id") == identifier:
                return _thaw(record)
        return None

    def project_capability_by_id(
        self, capability_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return the one explicit-only project capability record."""
        for record in self.project_records:
            if record.get("capability") == capability_id:
                return _thaw(record)
        return None

    def project_bundle_by_id(
        self, identifier: str
    ) -> Optional[bundles.BundleInventory]:
        """Return one validated project bundle inventory by identifier."""
        for inventory in self.project_bundles:
            if inventory.identifier == identifier:
                return inventory
        return None

    def provenance_by_id(self, identifier: str) -> Dict[str, Any]:
        """Return detached provenance for one project skill."""
        for record in self.provenance_records:
            if record.get("skillId") == identifier:
                return _thaw(record)
        raise KeyError(identifier)

    def canonical_bundle_by_id(
        self, identifier: str
    ) -> Optional[bundles.BundleInventory]:
        """Return one validated canonical bundle inventory by identifier."""
        for inventory in self.canonical_bundles:
            if inventory.identifier == identifier:
                return inventory
        return None

    def canonical_provenance_by_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Return optional detached canonical provenance by skill identifier."""
        for record in self.canonical_provenance_records:
            if record.get("skillId") == identifier:
                return _thaw(record)
        return None

    def provenance_record_by_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Return project or canonical provenance, including removed tombstones."""
        for record in tuple(self.provenance_records) + tuple(
            self.canonical_provenance_records
        ):
            if record.get("skillId") == identifier:
                return _thaw(record)
        return None

    def identifier_reserved(self, identifier: str) -> bool:
        """Return whether a current bundle or tombstone reserves an identifier."""
        portable = path_policy.portable_path_key(identifier)
        identifiers = [item.identifier for item in self.canonical_bundles]
        identifiers.extend(str(item.get("id")) for item in self.project_records)
        identifiers.extend(
            str(item.get("skillId"))
            for item in tuple(self.provenance_records)
            + tuple(self.canonical_provenance_records)
        )
        return any(path_policy.portable_path_key(item) == portable for item in identifiers)

    def combined_digest(self) -> str:
        """Return a stable digest of the three independent registry inputs."""
        return hashlib.sha256(
            contracts.canonical_json_bytes(
                {
                    "canonicalRegistryDigest": self.canonical_digest,
                    "projectRegistryDigest": self.project_registry_digest,
                    "provenanceDigest": self.provenance_digest,
                }
            )
        ).hexdigest()

    def select_project_skills(
        self,
        explicit_capabilities: Tuple[str, ...],
        suites: Tuple[str, ...],
        platforms: Tuple[str, ...],
    ) -> Dict[str, str]:
        """Resolve explicit project capabilities to one eligible bundle each.

        Args:
            explicit_capabilities: Explicit capability ids from strict config.
            suites: Selected user-facing suites.
            platforms: Selected platform ids.

        Returns:
            Capability-to-bundle identifier map in lexical capability order.

        Raises:
            RegistryValidationError: If a selected record is not current,
                approved, or eligible.

        Example:
            ``snapshot.select_project_skills(("project-skill-x",), ("cg",), ("kilo",))``
        """
        by_capability = {
            str(record["capability"]): record for record in self.project_records
        }
        selected = {}
        for capability_id in sorted(explicit_capabilities):
            record = by_capability.get(capability_id)
            if record is None:
                continue
            if record.get("admission") != "approved" or record.get(
                "lifecycle"
            ) == "removed":
                raise RegistryValidationError(
                    f"Project capability {capability_id!r} is not approved or usable."
                )
            if not set(record["supportedSuites"]) & set(suites):
                raise RegistryValidationError(
                    f"Project capability {capability_id!r} is not eligible for selected suites."
                )
            if not set(record["supportedPlatforms"]) & set(platforms):
                raise RegistryValidationError(
                    f"Project capability {capability_id!r} is not eligible for selected platforms."
                )
            selected[capability_id] = str(record["id"])
        return selected


def load_registry_snapshot(source_root: Path) -> RegistrySnapshot:
    """Load one bounded, strict canonical registry snapshot.

    Args:
        source_root: Canonical Compound GPID source root.

    Returns:
        Validated registry snapshot.

    Raises:
        RegistryValidationError: If the registry is absent, unsafe, or invalid.

    Example:
        ``snapshot = load_registry_snapshot(Path("."))``
    """
    root = Path(source_root).resolve()
    try:
        content = secure_fs.secure_read_bytes(
            root,
            Path(MODULE_REGISTRY_PATH),
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
        data = contracts.load_contract_bytes(content, source=MODULE_REGISTRY_PATH)
    except (OSError, UnicodeError, ValueError) as error:
        raise RegistryValidationError(
            f"Cannot load {MODULE_REGISTRY_PATH} safely: {error}"
        ) from error
    return RegistrySnapshot.from_data(
        root,
        data,
        digest=hashlib.sha256(content).hexdigest(),
    )


def _canonical_skill_ids(source_root: Path) -> Tuple[str, ...]:
    try:
        return tuple(
            path.rsplit("/", 1)[-1]
            for path in bundles.list_canonical_bundle_paths(source_root)
        )
    except bundles.BundleValidationError as error:
        raise RegistryValidationError(str(error)) from error


def _canonical_bundle_inventories(
    source_root: Path,
) -> Tuple[bundles.BundleInventory, ...]:
    inventories = []
    try:
        for source_path in bundles.list_canonical_bundle_paths(source_root):
            inventory = bundles.inventory_bundle(
                source_root, source_path, origin="plugin-canonical"
            )
            issues = bundles.validate_markdown_references(inventory)
            if issues:
                raise RegistryValidationError(
                    f"Canonical skill bundle reference is invalid: {issues[0].message}"
                )
            inventories.append(inventory)
    except (OSError, bundles.BundleValidationError) as error:
        raise RegistryValidationError(str(error)) from error
    return tuple(inventories)


def _combined_provenance_digest(
    canonical_digest: str,
    project_digest: str,
    *,
    has_canonical_records: bool,
) -> str:
    if not has_canonical_records:
        return project_digest
    return hashlib.sha256(
        contracts.canonical_json_bytes(
            {
                "canonicalProvenanceDigest": canonical_digest,
                "projectProvenanceDigest": project_digest,
            }
        )
    ).hexdigest()


def _empty_project_registry() -> Dict[str, Any]:
    return {
        "schema": "cg-project-skill-registry-v1",
        "schemaVersion": 1,
        "records": [],
    }


def load_combined_registry_snapshot(
    project_root: Path,
    source_root: Path,
) -> CombinedRegistrySnapshot:
    """Load canonical and project registry/provenance as one immutable snapshot.

    Args:
        project_root: Consumer project root containing the optional overlay.
        source_root: Canonical Compound GPID source root.

    Returns:
        Validated immutable combined snapshot with separate source digests.

    Raises:
        RegistryValidationError: If any input is unsafe, invalid, or shadows
            another input.

    Example:
        ``load_combined_registry_snapshot(project, source)``
    """
    project = Path(project_root).resolve()
    source = Path(source_root).resolve()
    canonical = load_registry_snapshot(source)
    relative = Path(PROJECT_REGISTRY_PATH)
    try:
        content = secure_fs.secure_read_bytes(
            project,
            relative,
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
    except FileNotFoundError:
        data = _empty_project_registry()
        content = contracts.canonical_json_bytes(data)
    except (OSError, ValueError) as error:
        raise RegistryValidationError(
            f"Cannot load {PROJECT_REGISTRY_PATH} safely: {error}"
        ) from error
    else:
        try:
            data = contracts.load_contract_bytes(content, source=PROJECT_REGISTRY_PATH)
        except ValueError as error:
            raise RegistryValidationError(str(error)) from error

    preliminary_canonical_ids = _canonical_skill_ids(source)
    preliminary_capabilities = tuple(
        str(item.get("id"))
        for item in canonical.capabilities
        if isinstance(item.get("id"), str)
    )
    preliminary_findings = contracts.validate_project_registry(
        data,
        canonical_ids=preliminary_canonical_ids,
        canonical_capabilities=preliminary_capabilities,
    )
    if preliminary_findings:
        details = "; ".join(
            f"{item.path}: {item.code}: {item.message}"
            for item in preliminary_findings
        )
        raise RegistryValidationError(f"Project registry is invalid: {details}")
    canonical_inventories = _canonical_bundle_inventories(source)
    try:
        canonical_provenance = provenance.load_canonical_provenance_snapshot(
            source, canonical_inventories
        )
    except provenance.ProvenanceValidationError as error:
        raise RegistryValidationError(str(error)) from error
    canonical_ids = tuple(
        sorted(
            {item.identifier for item in canonical_inventories}
            | {
                str(item.get("skillId"))
                for item in canonical_provenance.records
                if isinstance(item.get("skillId"), str)
            }
        )
    )
    canonical_capabilities = tuple(
        str(item.get("id"))
        for item in canonical.capabilities
        if isinstance(item.get("id"), str)
    )
    findings = contracts.validate_project_registry(
        data,
        canonical_ids=canonical_ids,
        canonical_capabilities=canonical_capabilities,
    )
    if findings:
        details = "; ".join(
            f"{item.path}: {item.code}: {item.message}" for item in findings
        )
        raise RegistryValidationError(f"Project registry is invalid: {details}")

    records = tuple(data.get("records", ()))
    canonical_portable = {
        path_policy.portable_path_key(identifier): identifier
        for identifier in canonical_ids
    }
    for record in records:
        identifier = str(record["id"])
        if path_policy.portable_path_key(identifier) in canonical_portable:
            raise RegistryValidationError(
                f"Project skill identifier shadows canonical bundle: {identifier}"
            )
    inventories = []
    for record in records:
        identifier = str(record["id"])
        try:
            inventory = bundles.inventory_bundle(
                project,
                str(record["sourcePath"]),
                origin="project-imported",
            )
            reference_issues = bundles.validate_markdown_references(inventory)
        except (OSError, bundles.BundleValidationError) as error:
            raise RegistryValidationError(
                f"Project skill bundle is invalid: {identifier}: {error}"
            ) from error
        if reference_issues:
            raise RegistryValidationError(
                f"Project skill bundle reference is invalid: {identifier}: "
                f"{reference_issues[0].message}"
            )
        if inventory.digest != record.get("bundleDigest"):
            raise RegistryValidationError(
                f"Project skill bundle digest mismatch: {identifier}"
            )
        inventories.append(inventory)
    try:
        provenance_snapshot = provenance.load_provenance_snapshot(project, records)
    except provenance.ProvenanceValidationError as error:
        raise RegistryValidationError(str(error)) from error
    frozen_records = tuple(_freeze(item) for item in records)
    return CombinedRegistrySnapshot(
        canonical,
        project,
        hashlib.sha256(content).hexdigest(),
        _combined_provenance_digest(
            canonical_provenance.digest,
            provenance_snapshot.digest,
            has_canonical_records=bool(canonical_provenance.records),
        ),
        frozen_records,
        tuple(inventories),
        provenance_snapshot.records,
        canonical_inventories,
        canonical_provenance.records,
    )


def build_combined_registry_snapshot(
    project_root: Path,
    canonical: RegistrySnapshot,
    project_registry: Mapping[str, Any],
    project_registry_bytes: bytes,
    project_bundles: Sequence[bundles.BundleInventory],
    provenance_records: Sequence[Mapping[str, Any]],
    provenance_bytes: Mapping[str, bytes],
    *,
    canonical_bundles: Optional[Sequence[bundles.BundleInventory]] = None,
    canonical_provenance_records: Optional[Sequence[Mapping[str, Any]]] = None,
    canonical_provenance_bytes: Optional[Mapping[str, bytes]] = None,
) -> CombinedRegistrySnapshot:
    """Build and validate a future project overlay without live writes.

    This API lets lifecycle planning resolve the complete desired manifest and
    projections from staged values in memory. Publication still occurs only in
    the common expected-byte transaction.
    """
    project = Path(project_root).resolve(strict=True)
    detached_registry = json.loads(json.dumps(project_registry))
    future_canonical = (
        tuple(canonical_bundles)
        if canonical_bundles is not None
        else _canonical_bundle_inventories(canonical.source_root)
    )
    canonical_ids = tuple(item.identifier for item in future_canonical)
    canonical_capabilities = tuple(
        str(item.get("id"))
        for item in canonical.capabilities
        if isinstance(item.get("id"), str)
    )
    findings = contracts.validate_project_registry(
        detached_registry,
        canonical_ids=canonical_ids,
        canonical_capabilities=canonical_capabilities,
    )
    if findings:
        detail = "; ".join(
            f"{item.path}: {item.code}: {item.message}" for item in findings
        )
        raise RegistryValidationError(f"Project registry is invalid: {detail}")
    records = tuple(detached_registry.get("records", ()))
    inventory_by_id = {item.identifier: item for item in project_bundles}
    provenance_by_id = {
        str(item.get("skillId")): _thaw(item)
        for item in provenance_records
    }
    if len(inventory_by_id) != len(project_bundles):
        raise RegistryValidationError("Future project bundle identifiers are duplicated")
    if len(provenance_by_id) != len(provenance_records):
        raise RegistryValidationError("Future provenance identifiers are duplicated")
    provenance_schema = contracts.load_contract(
        Path(__file__).resolve().parents[3],
        contracts.CONTRACTS_ROOT / "provenance-v1.schema.json",
    )
    canonical_portable = {
        path_policy.portable_path_key(identifier): identifier
        for identifier in canonical_ids
    }
    for record in records:
        identifier = str(record["id"])
        if path_policy.portable_path_key(identifier) in canonical_portable:
            raise RegistryValidationError(
                f"Project skill identifier shadows canonical bundle: {identifier}"
            )
        inventory = inventory_by_id.get(identifier)
        if inventory is None or inventory.digest != record.get("bundleDigest"):
            raise RegistryValidationError(
                f"Future project bundle is missing or has the wrong digest: {identifier}"
            )
        provenance_record = provenance_by_id.get(identifier)
        if provenance_record is None:
            raise RegistryValidationError(f"Future provenance is missing: {identifier}")
        provenance_findings = contracts.validate_instance(
            provenance_record, provenance_schema
        )
        if provenance_findings:
            raise RegistryValidationError(
                f"Future provenance is invalid: {identifier}: "
                f"{provenance_findings[0].code}"
            )
        source = provenance_record.get("source", {})
        if (
            provenance_record.get("origin") != record.get("origin")
            or provenance_record.get("admission") != record.get("admission")
            or provenance_record.get("lifecycle") != record.get("lifecycle")
            or source.get("bundleDigest") != record.get("bundleDigest")
        ):
            raise RegistryValidationError(
                f"Future provenance disagrees with registry: {identifier}"
            )
    expected_ids = {str(record["id"]) for record in records}
    if set(inventory_by_id) != expected_ids:
        raise RegistryValidationError("Future project overlay contains orphan bundles")
    for identifier in sorted(set(provenance_by_id) - expected_ids):
        orphan = provenance_by_id[identifier]
        if orphan.get("lifecycle") != "removed" or not isinstance(
            orphan.get("tombstone"), dict
        ):
            raise RegistryValidationError(
                f"Future provenance has no active registry record: {identifier}"
            )
    digest_rows = []
    for identifier in sorted(provenance_by_id):
        content = provenance_bytes.get(identifier)
        if content is None:
            raise RegistryValidationError(
                f"Future provenance bytes are missing: {identifier}"
            )
        if contracts.load_contract_bytes(
            content, source=f"{PROVENANCE_ROOT}/{identifier}.json"
        ) != provenance_by_id[identifier]:
            raise RegistryValidationError(
                f"Future provenance bytes disagree with record: {identifier}"
            )
        digest_rows.append(
            {
                "path": f"{PROVENANCE_ROOT}/{identifier}.json",
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    project_snapshot = provenance.ProvenanceSnapshot(
        hashlib.sha256(contracts.canonical_json_bytes(digest_rows)).hexdigest(),
        tuple(
            _freeze(provenance_by_id[identifier])
            for identifier in sorted(provenance_by_id)
        ),
    )
    if canonical_provenance_records is None:
        try:
            canonical_provenance = provenance.load_canonical_provenance_snapshot(
                canonical.source_root, future_canonical
            )
        except provenance.ProvenanceValidationError as error:
            raise RegistryValidationError(str(error)) from error
    else:
        try:
            canonical_provenance = provenance.build_provenance_snapshot(
                canonical_provenance_records,
                canonical_provenance_bytes or {},
                future_canonical,
                origin="plugin-canonical",
                root_name=provenance.CANONICAL_PROVENANCE_ROOT,
            )
        except provenance.ProvenanceValidationError as error:
            raise RegistryValidationError(str(error)) from error
    if canonical_bundles is not None:
        _validate_future_canonical(canonical, future_canonical)
    return CombinedRegistrySnapshot(
        canonical,
        project,
        hashlib.sha256(project_registry_bytes).hexdigest(),
        _combined_provenance_digest(
            canonical_provenance.digest,
            project_snapshot.digest,
            has_canonical_records=bool(canonical_provenance.records),
        ),
        tuple(_freeze(item) for item in records),
        tuple(inventory_by_id[identifier] for identifier in sorted(expected_ids)),
        tuple(
            _freeze(provenance_by_id[identifier])
            for identifier in sorted(provenance_by_id)
        ),
        tuple(sorted(future_canonical, key=lambda item: item.identifier)),
        canonical_provenance.records,
    )


def _validate_future_canonical(
    canonical: RegistrySnapshot,
    inventories: Sequence[bundles.BundleInventory],
) -> None:
    """Validate future canonical ownership against exact staged bundle paths."""
    import cg_validate_modules as validator

    try:
        assets = [
            path
            for path in validator.canonical_assets(canonical.source_root)
            if not path.startswith(".github/skills/")
        ]
    except (OSError, ValueError) as error:
        raise RegistryValidationError(str(error)) from error
    for inventory in inventories:
        assets.extend(item.source_path for item in inventory.files)
        skill_path = f"{inventory.source_path}/SKILL.md"
        owners = canonical.owners_for_asset(skill_path)
        if len(owners) != 1:
            raise RegistryValidationError(
                f"Future canonical skill must have one explicit owner: {skill_path}"
            )
        declared_owner = inventory.frontmatter.get("owner")
        if declared_owner is not None and declared_owner != owners[0]:
            raise RegistryValidationError(
                f"Skill frontmatter owner mismatch: {inventory.identifier}"
            )
        declared_capability = inventory.frontmatter.get("capability")
        capability = canonical.capability_for_owner(owners[0])
        if declared_capability is not None and (
            capability is None or declared_capability != capability.get("id")
        ):
            raise RegistryValidationError(
                f"Skill frontmatter capability mismatch: {inventory.identifier}"
            )
    errors = validator.check_owned_assets_exist(canonical.to_dict(), assets)
    errors.extend(validator.check_ownership_closure(canonical.to_dict(), assets))
    if errors:
        raise RegistryValidationError(
            "Future canonical ownership is invalid: " + "; ".join(sorted(set(errors)))
        )
