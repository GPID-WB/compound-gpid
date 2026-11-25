#!/usr/bin/env bash
# Kept so earlier instructions still work. The checks live in run_cli_checks.py,
# which runs on macOS and Windows and reads ONLY, KILO_MODEL and LAYOUT.
exec python3 "$(dirname "$0")/run_cli_checks.py" "$@"
