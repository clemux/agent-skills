#!/usr/bin/env bash
set -euo pipefail
# Wrapper around pyinstrument for pytest profiling.
# Usage: [RUNNER="uv run --with pyinstrument"] profile-test.sh <test_dir> [-k "filter"] [extra pytest args...]
# All arguments are passed through to pytest via pyinstrument.
# RUNNER is the project's command prefix for running Python tools; defaults to
# "uv run --with pyinstrument" (works in uv projects without touching dependencies).
# Use RUNNER="" if pyinstrument is on PATH, RUNNER="poetry run" for poetry, etc.
read -ra runner <<<"${RUNNER-uv run --with pyinstrument}"
"${runner[@]}" pyinstrument -r text -m pytest "$@" -q
