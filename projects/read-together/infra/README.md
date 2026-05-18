# read-together — 빠른 시작 가이드

독서토론 보조 플랫폼 · MVP · Python 3.11 / FastAPI / SQLite / HTMX

---

## 사전 요구사항

| 도구 | 최소 버전 |
|------|---------|
| Docker | 24.x+ |
| Docker Compose | v2.x (`docker compose` 명령) |
| (개발 전용) Python | 3.11+ |

---

## Docker로 시작하기 (권장)

### 1. 환경변수 파일 준비

```bash
cp infra/.env.example infra/.env
# SECRET_KEY 생성 후 .env 에 붙여넣기
openssl rand -hex 32
```

`.env` 파일 최소 설정:
```
SECRET_KEY=<위에서 생성한 값>
```

### 2. 컨테이너 빌드 & 실행

```bash
# 프로젝트 루트에서 실행
docker compose -f infra/docker-compose.yml up -d --build
```

### 3. 동작 확인

```bash
curl http://localhost:8000/health
# 정상: {"status": "ok", "db": "ok"}
```

브라우저에서 `http://localhost:8000` 접속.

### 4. 로그 확인

```bash
docker compose -f infra/docker-compose.yml logs -f
```

### 5. 중지

```bash
docker compose -f infra/docker-compose.yml down
# 데이터 유지: 볼륨 read-together-data 는 삭제되지 않음
# 데이터까지 삭제: docker compose ... down -v
```

---

## 로컬 개발 서버 (Python 직접 실행)

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 준비 (Docker와 동일)
cp infra/.env.example infra/.env
# SECRET_KEY 설정 후

# 개발 서버 시작 (--reload 자동 포함)
bash infra/scripts/start.sh
```

서버 주소: `http://localhost:8000`

> `DB_PATH` 미설정 시 프로젝트 루트의 `dev.db` 를 사용합니다.

---

## 환경변수 참조

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `SECRET_KEY` | **필수** | — | 세션 쿠키 서명 키 (`openssl rand -hex 32`) |
| `DB_PATH` | 선택 | `/data/read_together.db` | SQLite 파일 경로 |
| `PORT` | 선택 | `8000` | Uvicorn 포트 |
| `LOG_LEVEL` | 선택 | `info` | 로그 레벨 (`debug`/`info`/`warning`) |
| `ALLOWED_ORIGINS` | 선택 | `*` | CORS 허용 출처 (운영 시 명시 권장) |

---

## 데이터 백업

SQLite 파일 단순 복사로 백업 가능:

```bash
# Docker 볼륨에서 파일 복사
docker cp read-together-app:/data/read_together.db ./backup_$(date +%Y%m%d).db
```

---

## 운영 배포 (nginx TLS)

nginx 리버스 프록시 설정은 `infra/` 디렉토리의 `deployment-topology.md` (설계 문서) 를 참조하세요.
