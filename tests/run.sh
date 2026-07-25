#!/usr/bin/env bash
# Run the PAIDEIA-Hermes test suite. Stdlib only — no install step, no venv.
#   ./tests/run.sh          # quiet
#   ./tests/run.sh -v       # per-test names
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${PYTHON:-python3}" -m unittest discover -s tests "$@"
