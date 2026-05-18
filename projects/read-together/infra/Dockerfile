# read-together Dockerfile
# 기반: python:3.11-slim (ADR-TA-02, RQ-NFR-OPS-01)
# 배포 단위: 단일 컨테이너, Uvicorn ASGI 서버

FROM python:3.11-slim

# 보안: 비루트 사용자로 실행
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# 의존성 레이어 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY src/ ./src/
COPY templates/ ./templates/

# SQLite 데이터 디렉토리 생성 (볼륨 마운트 전 빈 디렉토리 보장)
RUN mkdir -p /data && chown app:app /data

# 정적 파일 디렉토리 (없으면 생성)
RUN mkdir -p /app/src/web/static

USER app

# 헬스체크 (ARCH-TECH-DEPLOYMENT-TOPOLOGY §헬스체크)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Uvicorn 단일 워커 (동접 20명, ADR-TA-02)
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
