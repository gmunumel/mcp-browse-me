#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from the workspace root so relative paths work.
cd /workspace

VENV="${VENV_PATH:-/workspace/.venv}"
UVICORN_BIN="$VENV/bin/uvicorn"
PYTHON_BIN="$VENV/bin/python"

if [[ ! -x "$UVICORN_BIN" ]]; then
  echo "uvicorn not found at $UVICORN_BIN. Did postCreateCommand finish successfully?" >&2
  exit 1
fi

# Wait for Postgres to be reachable before starting the API so FastAPI import
# doesn't die on startup.
if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "Waiting for DATABASE_URL to become reachable..."
  "$PYTHON_BIN" - <<'PY'
import os
import time

import psycopg

dsn = os.environ["DATABASE_URL"]
for attempt in range(30):
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            break
    except Exception as exc:  # pragma: no cover - startup helper
        print(f"DB not ready (attempt {attempt + 1}/30): {exc}")
        time.sleep(2)
else:
    raise SystemExit("Database never became ready; aborting uvicorn start")
PY
else
  echo "DATABASE_URL not set; skipping database wait" >&2
fi

# Restart the API server.
pkill -f 'uvicorn src.api.main:app' || true
nohup "$UVICORN_BIN" src.api.main:app --host 0.0.0.0 --port 3000 >/tmp/uvicorn.log 2>&1 &
echo "uvicorn launched; logs: /tmp/uvicorn.log"
