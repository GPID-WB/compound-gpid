"""Strict schema and source validators for evidence-backed command help.

This module is the shared public facade of the help package. It validates inert
JSON data only and never executes prompt, metadata, workflow, wrapper, or
documentation content. The lightweight shared contracts live in
``help.base``; validation, installer, and maintenance entry points live in
``help.validation``, ``help.installers``, and ``help.maintenance`` and are
re-exported here so existing importers keep the one ``help.catalog`` surface.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from help.base import (  # noqa: F401
    CATALOG_OUTPUT_PATH,
    CATALOG_SCHEMA_PATH,
    CATALOG_SCHEMA_VERSION,
    GENERATOR_VERSION,
    HelpCatalogIOError,
    HelpCatalogStaleError,
    HelpValidationError,
    MAX_JSON_BYTES,
    MODULE_REGISTRY_PATH,
    QUALIFIED_ID_PATTERN,
    SEMANTIC_STATES,
    SHA256_PATTERN,
    SHELL_METADATA_PATH,
    SourceMetadata,
    SUPPORTED_OS,
    SUPPORTED_PLATFORMS,
    TRANSPORT_OPERATIONS,
    TRANSPORT_SCHEMA_PATH,
    TRANSPORT_SCHEMA_VERSION,
    UUID_PATTERN,
    WORKFLOW_END,
    WORKFLOW_ID_PATTERN,
    WORKFLOW_SOURCE_PATH,
    WORKFLOW_START,
    _reject_constant,
    _reject_surrogates,
    _repository_root,
    _sorted_unique,
    _validate_relative_path,
    compute_source_digest,
    load_strict_json,
    load_strict_json_bytes,
    normalize_command_key,
)

from help.installers import (  # noqa: E402, F401
    MAX_INSTALLER_BYTES,
    POSIX_INSTALL_END,
    POSIX_INSTALL_START,
    WINDOWS_INSTALL_END,
    WINDOWS_INSTALL_START,
    parse_posix_installer_inventory,
    parse_windows_installer_inventory,
    require_exact_installer_inventory,
)
from help.maintenance import (  # noqa: E402, F401
    check_catalog,
    generate_catalog_bytes,
    merge_catalog,
    preview_definition_digest,
    repin_definition_digest,
    serialize_catalog,
    write_catalog,
)
from help.validation import (  # noqa: E402, F401
    _heading_ids,
    _module_closure,
    _read_source_bytes,
    _schema_at,
    _schema_errors,
    _source_path,
    _validate_against_schema,
    _validate_command_semantics,
    _validate_definition,
    _validate_module_registry,
    _validate_source_reference,
    _workflow_payload,
    _workflow_records,
    compute_definition_digest,
    parse_transport_envelope,
    validate_catalog,
    validate_source_metadata,
    validate_transport_envelope,
)