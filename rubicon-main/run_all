#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export VITE_PUBLIC_PATH="${VITE_PUBLIC_PATH:-/rvpr/dev/}"
export VITE_API_SERVER_URL="${VITE_API_SERVER_URL:-http://localhost:8000}"
export FRONTEND_DEV_URL="${FRONTEND_DEV_URL:-http://localhost:8080}"
export VITE_OP_TYPE="${VITE_OP_TYPE:-DEV}"
export VITE_COUNTRY="${VITE_COUNTRY:-KR}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-local-secret}"

export POSTGRESQL_IP="${POSTGRESQL_IP:-127.0.0.1}"
export POSTGRESQL_DB="${POSTGRESQL_DB:-your_db}"
export POSTGRESQL_PORT="${POSTGRESQL_PORT:-5432}"
export POSTGRESQL_ID="${POSTGRESQL_ID:-your_user}"
export POSTGRESQL_PWD="${POSTGRESQL_PWD:-your_password}"

export REDIS_MAIN_IP="${REDIS_MAIN_IP:-127.0.0.1}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT

cd "${ROOT_DIR}"
DJANGO_SETTINGS_MODULE=alpha.settings python -m django runserver 0.0.0.0:8000 &
BACKEND_PID=$!

cd "${ROOT_DIR}/frontend"
yarn install
yarn dev &
FRONTEND_PID=$!

wait
