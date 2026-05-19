# 같이읽자 — v1 백엔드(Supabase) 셋업·자동화 가이드

정적 `index.html`(GitHub Pages) + **Supabase**(호스티드 Postgres). 서버를 따로 띄우지 않고 멀티유저.

- `index.html` 상단 `SB_URL`/`SB_KEY` 가 **비면 localStorage**(단일 브라우저), **채우면 Supabase**(멀티유저). 무회귀.
- DB 스키마는 **`supabase/migrations/`** 가 단일 소스. push 하면 자동 적용(아래 자동화).

---

## 0. 한눈에

| 대상 | 자동화 | 1회 준비 |
|---|---|---|
| 화면(Pages) | push → Pages 자동 재배포 | Settings→Pages 1회 활성화 |
| DB 스키마 | push(`supabase/migrations/**`) → Actions 가 `db push` | GitHub Secrets 3개 |
| 키(anon) | 파일에 커밋(공개 가능 키) | 키 2줄 입력 후 1회 push |

## 1. Supabase 프로젝트 생성

1. https://supabase.com → **New project** (리전 `Northeast Asia (Seoul)`)
2. 생성 시 정한 **Database password** 를 메모(자동화 Secret 에 씀)

## 2. 첫 스키마 적용 (택1)

- **간단(1회)**: SQL Editor → `supabase/migrations/20260519120000_init.sql` 내용 붙여넣고 Run
- **또는** 아래 3번 자동화를 먼저 켜고 빈 커밋/재실행으로 적용

> 둘 다 idempotent — 여러 번 돌려도 안전.

## 3. DB 마이그레이션 자동화 (GitHub Actions)

`.github/workflows/supabase-migrate.yml` 가 이미 있습니다.
**GitHub → 저장소 → Settings → Secrets and variables → Actions** 에 3개 추가:

| Secret | 값 위치 |
|---|---|
| `SUPABASE_PROJECT_REF` | Supabase → Settings → General → **Reference ID** |
| `SUPABASE_ACCESS_TOKEN` | https://supabase.com/dashboard/account/tokens 에서 발급 |
| `SUPABASE_DB_PASSWORD` | 1번에서 정한 DB password |

→ 이후 `supabase/migrations/**` 변경을 push 하면 **자동으로 해당 프로젝트에 반영**.
Secrets 미설정이면 워크플로는 조용히 스킵(빨간 X 안 뜸).

> 스키마 바꾸려면 `supabase/migrations/` 에 새 파일
> (`<YYYYMMDDHHMMSS>_변경.sql`) 추가 후 push. 기존 파일은 수정하지 말 것(이력 보존).

대안 — Supabase 대시보드의 **GitHub 연동(Branching)** 을 쓰면 Actions 없이도
같은 폴더를 자동 적용하지만, 유료/프리뷰 제약이 있어 위 Actions 방식을 권장합니다.

## 4. 프론트에 키 연결 (파일 커밋)

Supabase → **Settings → API**: **Project URL** + **anon public** 키.
`index.html` **과** `docs/index.html` 상단 두 줄을 채웁니다:

```js
var SB_URL = 'https://xxxx.supabase.co';
var SB_KEY = 'eyJ...(anon public)';
```

> `service_role` 키는 절대 넣지 마세요. anon 키는 공개돼도 되는 키지만,
> 그래서 **RLS 가 유일한 방어선**입니다(아래 보안).

## 5. GitHub Pages 활성화 (1회)

저장소 **Settings → Pages → Source: Deploy from a branch → `master` / `/ (root)`** → Save.
이후 **모든 push 마다 Pages 가 자동 재배포**됩니다.

URL: **https://ppmj789.github.io/read-together/**

## 6. 검증

Pages URL → 회원: 휴대폰 4자리 입장 / 모임장: `모임 관리` 코드 `HUMAN-Q2` 비번 `1234`.
다른 기기·브라우저에서 같은 데이터가 보이면 멀티유저 성공.

---

## 데이터 모델

| 테이블 | 의미 |
|---|---|
| `meeting` | 모임(시즌). `code`+`password`=모임장 공용계정 |
| `book` | 책. `questions` jsonb |
| `member_book` | (책,phone4) 제출여부·다축 별점·닉네임 |
| `answer` | (책,phone4,질문) 답변 |
| `comment` | 답변에 달린 댓글 |

식별자 = 휴대폰 뒤 4자리. 인증 아님(사내 신뢰 모델).

## 보안 / 한계 (공개 전 확인)

- github.io 는 공개 URL. anon 키가 정적 파일에 박히고 v1 RLS 는 **데모 등급
  (anon 전체 read/write)** → URL+키를 본 사람은 데이터 조작 가능. **사내 비공개
  소규모 전용.** 외부 공개하려면 RLS 강화(모임 스코프·모임장 비번 검증 Edge
  Function) 선행 필요.
- 공감(💛) 미영속, 실시간 갱신 없음(화면 진입 시 최신화), phone4 4자리 충돌 가능.
