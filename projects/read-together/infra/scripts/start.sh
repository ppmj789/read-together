#!/usr/bin/env bash
# read-together 개발 서버 시작 스크립트
# 사용법: bash infra/scripts/start.sh [--reload]
#
# 개발 환경: uvicorn --reload (로컬 Python 직접 실행)
# 운영 환경: docker-compose up (infra/docker-compose.yml 사용)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# .env 파일 로드 (있으면)
ENV_FILE="${PROJECT_ROOT}/infra/.env"
if [[ -f "${ENV_FILE}" ]]; then
  echo "[start.sh] .env 로드: ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
else
  echo "[start.sh] .env 없음 — infra/.env.example 을 infra/.env 로 복사 후 값을 채워주세요."
fi

# 필수 환경변수 확인
if [[ -z "${SECRET_KEY:-}" ]]; then
  echo "[start.sh] 오류: SECRET_KEY 환경변수가 설정되지 않았습니다."
  echo "  힌트: openssl rand -hex 32"
  exit 1
fi

# 개발용 SQLite 경로 (로컬 실행 시)
export DB_PATH="${DB_PATH:-${PROJECT_ROOT}/dev.db}"
export PORT="${PORT:-8000}"
export LOG_LEVEL="${LOG_LEVEL:-debug}"

echo "[start.sh] 개발 서버 시작 (host=0.0.0.0, port=${PORT}, reload=on)"
echo "[start.sh] DB_PATH=${DB_PATH}"

cd "${PROJECT_ROOT}"

# --reload 옵션 처리
RELOAD_FLAG=""
if [[ "${1:-}" == "--reload" || "${1:-}" == "" ]]; then
  RELOAD_FLAG="--reload"
fi

exec uvicorn src.main:app \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --log-level "${LOG_LEVEL}" \
  ${RELOAD_FLAG}
