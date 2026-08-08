#!/usr/bin/env bash
# Invoke-YamlLint.sh — YAML frontmatter validator for macOS / Linux.
#
# Unix companion to Invoke-YamlLint.ps1. Both entries run the same five rules
# and report identical results. This wrapper shells out to
# validate_yaml_frontmatter.py (Python 3, stdlib only), which is already a
# Compound GPID dependency on Unix (scripts/link.sh resolves Python the same
# way). On Windows, use the native Invoke-YamlLint.ps1 entry instead.
#
# Usage:
#   ./Invoke-YamlLint.sh                  # validate .kilo/
#   ./Invoke-YamlLint.sh -Path .kilo      # validate a specific platform tree
#   ./Invoke-YamlLint.sh -Path .kilo -Fix # validate and auto-fix R1/R2
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATOR="$SCRIPT_DIR/validate_yaml_frontmatter.py"

resolve_python() {
    local candidate version
    for candidate in python3 python py; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        case "$version" in
            Python\ [0-9]*) printf '%s\n' "$candidate"; return 0 ;;
        esac
    done
    return 1
}

PYTHON_CMD="$(resolve_python || true)"
if [ -z "$PYTHON_CMD" ]; then
    printf '\033[0;31mERROR: Python is required to run the YAML frontmatter validator (checked: python3, python, py).\033[0m\n' >&2
    printf 'Install Xcode Command Line Tools or Python from https://www.python.org/downloads/\n' >&2
    exit 1
fi

exec "$PYTHON_CMD" "$VALIDATOR" "$@"