#!/usr/bin/env bash
set -euo pipefail
# Wrapper around pyinstrument for pytest profiling.
# Usage: profile-test.sh <test_dir> [-k "filter"] [extra pytest args...]
# All arguments are passed through to pytest via pyinstrument.
uv run pyinstrument -r text -m pytest "$@" -q
