# 같이읽자 — v1 백엔드(Supabase) 셋업·배포 가이드

정적 `index.html`(GitHub Pages) + **Supabase**(호스티드 Postgres + 자동 REST) 구성.
서버를 따로 띄우지 않고도 진짜 멀티유저로 동작합니다.

> 핵심: `index.html` 상단의 `SB_URL`/`SB_KEY` 가 **비어 있으면 기존처럼 localStorage**(오프라인·단일 브라우저)로 동작하고, **채우면 Supabase**(멀티유저)로 자동 전환됩니다. 무회귀.

---

## 1. Supabase 프로젝트 생성

1. https://supabase.com → 로그인 → **New project**
2. 리전: `Northeast Asia (Seoul)` 권장. DB 비밀번호는 적당히(이건 Postgres 관리용, 앱과 무관).
3. 생성 완료까지 1~2분.

## 2. 스키마 적용

1. 좌측 **SQL Editor** → **New query**
2. 이 저장소의 `supabase/schema.sql` 전체를 붙여넣고 **Run**
3. "Success" 확인. (재실행해도 안전 — idempotent)
   - 좌측 **Table editor** 에 `meeting/book/member_book/answer/comment` 5개 테이블과
     데모 모임(`HUMAN-Q2 / 1234`, 책 3권, 이향인 표본 4인)이 보이면 정상.

## 3. 키 확인

좌측 **Project Settings → API**:

- **Project URL** → `SB_URL`
- **anon public** 키 → `SB_KEY`  (절대 `service_role` 키를 쓰지 마세요)

## 4. 프론트에 키 연결

`index.html` 상단 스크립트의 설정 블록을 채웁니다 (루트 + `docs/index.html` 둘 다):

```js
/* ── Supabase 설정 (비우면 localStorage 모드) ── */
var SB_URL = 'https://xxxxxxxx.supabase.co';
var SB_KEY = 'eyJhbGciOi...(anon public)';
```

저장 후 브라우저로 `index.html` 을 열면 우측 하단에 한 번 `온라인(Supabase) 모드` 토스트가 뜹니다.

## 5. 배포 (GitHub Pages)

```bash
cd ~/read-together
git add index.html docs/index.html supabase/ SUPABASE.md
git commit -m "feat: v1 Supabase 백엔드 연동"
git push
```

- Pages 게시 소스가 `/`면 루트 `index.html`, `/docs`면 `docs/index.html` 이 서비스됩니다.
  (Settings → Pages 에서 확인. 둘 다 갱신해 두면 안전)
- `anon` 키는 공개돼도 되는 키지만, 그래서 **RLS 가 유일한 방어선**입니다.
  v1 스키마는 데모 등급(anon 전체 허용)입니다 — 사내 비공개 모임 수준에서만 쓰세요.

---

## 데이터 모델 요약

| 테이블 | 의미 |
|---|---|
| `meeting` | 모임(시즌). `code`+`password` 가 모임장 공용계정 |
| `book` | 모임 안의 책. `questions` jsonb = 질문 배열 |
| `member_book` | (책, phone4) — 제출여부 · 다축 별점 · 닉네임 |
| `answer` | (책, phone4, 질문번호) 답변 1행 |
| `comment` | 어떤 사람의 답변에 달린 댓글 |

식별자 = 휴대폰 뒤 4자리(`phone4`). 인증 아님(사내 신뢰 모델). 닉네임은 책마다 자동.

## 동작 매핑 (프론트 → Supabase)

- 모임 리스트 / 입장 → `meeting`,`book` select
- 모임 만들기(시즌 빌더) → `meeting`,`book` insert
- 모임 관리(코드+비번) → `meeting` 조회 검증
- 질문 편집 → `book.questions` update
- 내 답변 제출 → `answer` upsert + `member_book.submitted=true`
- 제출 직후 타인 답변 열람 → 다른 phone4 의 `answer` select
- 책 별점 → `member_book.ratings` upsert
- 댓글 → `comment` insert/select
- 발표 모드(참가자·답변·별점분포·댓글) → `member_book`+`answer`+`comment` 집계

## 한계 / 다음 버전

- v1 RLS 는 데모 등급(누구나 read/write). 운영 시: 모임코드 스코프 정책 + Edge Function 으로 모임장 비번 검증, 답변 수정은 본인 phone4 만 등으로 강화.
- 실시간 갱신은 폴링 없음(화면 진입·새로고침 시 최신화). 필요하면 Supabase Realtime 구독 추가.
- phone4 4자리 충돌 가능(같은 모임 내). 소규모에선 수용, 운영 시 전체번호/초대코드로 확장.
