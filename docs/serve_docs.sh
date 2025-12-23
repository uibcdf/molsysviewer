#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${DOCS_DIR}/_build/html"
PORT="${1:-8000}"

if [ ! -d "${BUILD_DIR}" ]; then
  echo "Build directory not found: ${BUILD_DIR}"
  echo "Run 'make html' inside docs/ first."
  exit 1
fi

echo "Serving docs from ${BUILD_DIR} on http://localhost:${PORT}"
echo "Press Ctrl+C to stop."

python -m http.server "${PORT}" --directory "${BUILD_DIR}" &
SERVER_PID=$!

cleanup() {
  kill "${SERVER_PID}" 2>/dev/null || true
}
trap cleanup EXIT

sleep 0.5
python -m webbrowser "http://localhost:${PORT}/" >/dev/null 2>&1 || true

wait "${SERVER_PID}"
