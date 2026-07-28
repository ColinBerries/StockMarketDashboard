#!/usr/bin/env bash
# Launch the diagnostic dashboard on http://localhost:5050.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "Warning: $BACKEND_DIR/.env not found. Set POLYGON_TOKEN there first," >&2
  echo "or price lookups will require cached price_data_*.pkl files." >&2
fi

if command -v python3 >/dev/null 2>&1 \
  && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' \
    >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1 \
  && python -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' \
    >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: Python 3.10 or newer is not available on PATH." >&2
  exit 1
fi

cd "$BACKEND_DIR"
exec "$PYTHON_BIN" dev_dashboard.py
