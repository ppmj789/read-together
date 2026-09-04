---
name: generate-report
description: |
  read-together(未知의 서재) 앱에서 한 권의 책 토론이 끝난 뒤, 실제 Supabase
  데이터(답변·댓글·공감·별점·이향인 점수)를 바탕으로 발표모드 [AI 분석] 탭에
  뜨는 발표자료(book.report)를 '키워드 중심'으로 생성해 저장한다.
  새 책이 마감될 때마다 실행한다. "발표자료 만들어줘 / 생성해줘 / report" 요청 시 사용.
---

# 발표자료(report) 생성 스킬

책 한 권의 토론 데이터를 분석해 **키워드 중심 발표자료**를 만들고 `book.report`
(jsonb)에 저장한다. 프론트 `renderStageRating()` 이 이 데이터를 그대로 읽어
발표모드 **[AI 분석]** 탭(키워드·별점 분포·한줄 요약)에 렌더한다.

## 언제

- 책이 **마감(closed)** 되어 답변·별점이 고정된 뒤.
- 사용자가 "발표자료 생성/재생성" 을 요청할 때. **앞으로 새 책이 생길 때마다 반복.**

## 절차

작업 디렉토리: 이 스킬 폴더(`.claude/skills/generate-report/`). 스크립트는
`index.html` 상단의 공개 anon 키를 자동으로 읽는다(별도 설정 불필요).

### 1) 원천 데이터 수집

```bash
python3 report_fetch.py "이향인"      # 제목 부분일치 (또는 book UUID)
```

출력 JSON: `book`(질문 포함) · `stats`(답변/댓글/반응/참가자 수) ·
`ratings`(5축 평균·표본수, 결정론) · `reactions`(종류별 집계 + **`by_answer`
답변 기준 집계**, 결정론) · `reaction_labels`(종류 키→라벨) ·
`score_distribution`(이향인 점수, 있을 때만) ·
`answers_by_question`(질문별 답변 본문) ·
`answers_detail`(**집단 분석용** — 질문별 `{nick, body, reactions, comments[]}`,
닉네임·답변별 반응·대상 답변에 연결된 댓글) · `comments`(댓글 본문).

### 2) report 저작 — **키워드 중심**

`answers_by_question` 와 `comments` 를 직접 읽고 다음을 만든다.

- **keywords (8~10개)** — 토론에서 실제로 반복된 **주제어**. 단순 빈도 토큰이 아니라
  참가자들이 실제 쓴 개념/프레임을 뽑는다. 각 항목:
  - `w`: 키워드(짧게, 칩에 들어갈 길이)
  - `size`: `lg`(핵심 3~4개) / `md` / `sm` — 중요도
  - `c`: 대략 언급 빈도(정수, 표시용)
  - `q`: **실제 답변에서 그대로 가져온 대표 인용문 1개** (오버레이에 뜸)
  - `why`: 이 키워드를 뽑은 이유 한 줄 (오버레이 제목)
- **summary_slides (2026-07-31, 발표 정본)** — PPT 슬라이드 배열 6~9장,
  각 항목 `{icon(이모지 1개), t(슬라이드 제목, 짧고 굵게), b(본문 2~4문장),
  hero(첫 장만 true)}`. 첫 장(hero)은 '이번 책 한 줄 정서'. 이후 장 구성
  권장: 핵심 발견 → 논쟁 지점 → 별점 읽기 → **집단 분석 1~2장(아래)** →
  반전/웃음 포인트 → 진행 제안. 프로젝터에서 읽히도록 제목은 7단어 이내,
  본문은 완성 문장. 프론트([AI 분석]탭·발표 결과)가 카드 그리드로 렌더.
- **집단 분석 (2026-07-31 사용자 피드백: "우리 집단에 대해 상세하게")** —
  `answers_detail` 의 닉네임으로 참가자별 캐릭터·역할(감동 담당, 드립 담당,
  학구파, 반론가…)과 상호작용(누가 누구에게 댓글/반응을 보내는지)을 분석해
  summary_slides 1~2장 + highlights 에 녹인다. **닉네임은 앱에 공개된 값이라
  써도 되지만, 별점은 익명이므로 닉네임과 별점을 연결 짓는 서술 금지.**
- **member_profiles (2026-07-31, 멤버 추리 씬)** — 답변한 멤버 전원 각
  1개 `{nick, title(캐치프레이즈 한 줄), desc(답변·댓글 스타일 근거 2~3문장),
  quote(그 사람 답변/댓글 원문 발췌 1개)}`. 발표모드 **[멤버 추리]** 탭이
  '닉네임만 보고 실물이 누구인지 맞히기' 게임용으로 카드 렌더한다. desc 는
  실제 데이터 근거(예: 댓글 10개 츳코미 담당)를 담되 실명 추정은 금지.
- **ratings_comment (2026-07-31)** — 별점 카드 아래에 붙는 '팀원들은
  이렇게 생각했다' 해석 2~3문장. 축 간 대비(참신함은 높고 분량은 갈림 등)를
  완성 문장으로. 별점을 특정 닉네임과 연결 짓지 않는다.
- **question_groups (2026-07-31, 진행탭 무리 모션)** — 질문마다 비슷한
  답변끼리 무리 짓는 데이터: `[{q_index, groups:[{emoji, name, members:[닉네임]}]}]`.
  질문당 무리 2~4개, **답변자 전원을 어느 무리엔가 배치** (실제 답변 내용
  근거로 분류 — 예: 도망파/말걸기파). 진행탭에서 조약돌(닉네임 칩)이 무리
  사이를 이동하는 애니메이션으로 렌더된다. 질문 간 무리 이동이 재미 포인트라
  같은 사람이 질문마다 다른 무리에 가도록 실제 답변대로 정직하게 나눈다.
- **인용 규칙 (2026-07-31 사용자 피드백)** — report 의 모든 따옴표 인용은
  답변·댓글·질문 원문의 **연속 발췌**여야 한다. 중간 생략(...)·어순 재배열·
  축약·맞춤법 교정 금지. 짧게 쓰려면 연속 부분 문자열만 잘라 쓴다.
  AI 자신의 표현(요약·명명)에는 따옴표를 쓰지 않는다 (달리지 않은 댓글이
  달린 것처럼 보이는 사고 방지).
- **summary** — 폴백·아카이브용 텍스트(필수 유지). **여러 줄**(`\n` 포함),
  4~6개 문단. 흐름: 전체 정서 → 인정한 지점 → 수렴한 결론 → 별점 요약 →
  반전 포인트 → 진행 제안.
  **(2026-07-21 사용자 피드백) 전신·불릿·대시 압축체 금지 — 완성된 문장으로
  풀어 쓴다.** "· 지배 키워드 — A · B · C" 식이 아니라 "많은 분이 ~라고
  읽었고, 자주 나온 표현은 A, B 였습니다" 처럼. 문단 사이는 `\n` 1개.
  (프론트가 `\n` 기준 문단으로 렌더 — summary_slides 가 있으면 슬라이드가
  우선이고 summary 는 구버전 프론트 폴백)
- **ratings / stats / reactions** — 1)의 결정론 값을 **그대로 복사**(재계산·추정 금지).
  `reactions` = `{total, by_kind:{종류키:개수}, top:[{kind,count,q_index,quote}],
  by_answer:[{q_index,nick,quote,counts,total}]}`. **(2026-07-31 사용자 피드백)
  반응은 답변에 달리는 것이므로 `by_answer`(반응이 몰린 답변)가 정본이고,
  프론트도 이것을 우선 렌더한다** (구 report 는 by_kind 분포 폴백).
  종류는 5가지 — `underline`(🔖 밑줄) · `empathy`(🙌 완전 동의) ·
  `insight`(👀 생각 못 했네요) · `differ`(🌀 전 다르게) · `more`(👂 더 듣고 싶어요).
  **슬라이드에도 반응이 몰린 답변을 한 장 녹일 것** — 특히 `differ`(전 다르게)가
  몰린 답변은 모임 당일 토론 불씨라 짚어 주고, `more`(더 듣고 싶어요)가 붙은
  답변은 진행 제안에 넣는다. `kind` 컬럼 적용 전 데이터는 전부 `empathy` 로
  잡히므로 그 경우 종류 분석은 생략한다.
- **highlights** (선택, 배열) — **신형 (2026-07-31 사용자 피드백: 명확한
  선정 기준): 각 항목 = `{label, q, body}` 객체.** `label` 은 **'왜 이게
  하이라이트인지'를 제목 문장으로** 쓴다 — 프론트가 label 을 굵은 제목,
  q 를 보조 줄로 렌더 (예: `🙌 유일하게 공감 2표를 모은 귀환파 대표 답변` ·
  `🌀 반박 댓글까지 부른 이번 토론 최대 쟁점`). 기준은
  `by_answer`/`answers_detail` 의 실제 수치에 근거하고 수치를 병기한다.
  `q` 는 질문 첫 줄(`Q1. …`), `body` 는 답변 발췌 + AI 의견 완성 문장.
  (구형 `"질문\n→ 의견"` 문자열도 프론트가 렌더는 하지만 신규 생성은
  객체형으로.)
- **score_distribution**(1)의 값) — 기록용.
- `source`: 생성 모델명(예: `claude-opus-4.8`), `generated_at`: ISO8601.

키워드 스키마 예시는 `example-report.json` 참고.

### 3) 저장

저작한 report 를 파일로 쓴 뒤:

```bash
python3 report_put.py <book_id> /path/to/report.json
```

`report_put.py` 가 필수 필드(source·generated_at·keywords·ratings·summary·stats)와
keyword 의 `w`/`size` 를 검증한 뒤 PATCH 한다.

### 4) 검증

- **저장 전 필수**: `python3 verify_quotes.py <책> /path/to/report.json` —
  report 안의 모든 따옴표 인용이 답변·댓글·질문 원문의 연속 발췌인지 검사.
  **불일치 0 이어야 report_put 진행** (비0 exit → 인용을 원문 그대로 고칠 것).
- `report_put.py` 출력의 `keywords / 인용 / summary 줄 / 멤버 프로필` 수 확인.
- 발표모드 [AI 분석] 탭에서 키워드를 누르면 `why`+`q` 고정 패널이 뜬다.

## 주의

- **RLS 데모 등급** — anon 키로 직접 PATCH 된다. 사내 비공개 전용.
- 인용문 `q` 는 답변 원문을 **변형 없이** 발췌(따옴표는 렌더러가 붙임).
- 별점 축 키: `length·difficulty·fun·novelty·overall`. 난이도는 '적절할수록 높음'.
- 개인정보(phone4)는 report 에 넣지 않는다. 표시는 익명 닉네임 기준.

## 시즌 결산 리포트 (season.report, v31 · 2026-09-04)

시즌의 책이 **전부 마감**된 뒤 한 번, 3권을 관통하는 결산호를 만들어 `season.report`
(jsonb)에 저장한다. 책장 칸의 책들 옆에 접은 신문(📰 결산호)이 놓이고, 누르면
시즌 결산 페이지(`renderSeasonReport`)가 열린다. 발표모드에서는 마지막 탭
[📰 시즌 결산] 으로도 같은 지면이 뜬다.

절차: 시즌의 책마다 `report_fetch.py` 로 원천을 모은 뒤(`member_book.phone4` 로
같은 사람을 책 사이에서 잇는다) 아래 스키마로 저작 → `python3 season_put.py "<시즌 제목>" season_report.json`.

스키마 (프론트 `seasonReportHtml` 이 읽는 키):
- `thesis` 시즌 한 줄 · `eyebrow`(`SEASON 1`) · `period`
- `books:[{title,author,ym}]` 순서대로 — 나머지 필드의 `book` 은 이 배열 인덱스
- `totals:{answers:[권별],comments:[],reactions:[],participants,participants_note}` · `score_title`
- `ratings:{overall|fun|novelty|length|difficulty:[권별 평균]}` · `ratings_reads:{축:'한 줄'}` · `ratings_note`
- `thread:[{book,q,body,quote:{text,by:phone4,src}}]` · `thread_lede` · `verdict`(`**굵게**` 허용)
- `roster:[{phone4,nicks:[권별 닉네임]}]` — 닉네임은 이 칸에서만 보여 준다
- `members:[{phone4,title(칭호 문장),award(짧은 상 이름),desc,quotes:[{book,text,src}]}]` · `members_title` · `members_lede`
- `graph:{order:[phone4],counts:{쓴:{받은:n}}}` · `graph_lede` · `graph_note`

규칙 (사용자 결정 2026-09-04): **사람은 전화번호 뒷자리(phone4)로만 식별** — 카드는
번호를 숨기고 눌러야 보인다(맞히기용). **별점은 익명이라 어떤 카드·번호와도 연결 금지.**
동료 실명이 들어간 답변은 인용하지 않는다. 인용은 book.report 와 같이 원문 연속 발췌.
