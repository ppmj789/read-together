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

출력 JSON: `book`(질문 포함) · `stats`(답변/댓글/공감/참가자 수) ·
`ratings`(5축 평균·표본수, 결정론) · `score_distribution`(이향인 점수, 있을 때만) ·
`answers_by_question`(질문별 답변 본문) · `comments`(댓글 본문).

### 2) report 저작 — **키워드 중심**

`answers_by_question` 와 `comments` 를 직접 읽고 다음을 만든다.

- **keywords (8~10개)** — 토론에서 실제로 반복된 **주제어**. 단순 빈도 토큰이 아니라
  참가자들이 실제 쓴 개념/프레임을 뽑는다. 각 항목:
  - `w`: 키워드(짧게, 칩에 들어갈 길이)
  - `size`: `lg`(핵심 3~4개) / `md` / `sm` — 중요도
  - `c`: 대략 언급 빈도(정수, 표시용)
  - `q`: **실제 답변에서 그대로 가져온 대표 인용문 1개** (오버레이에 뜸)
  - `why`: 이 키워드를 뽑은 이유 한 줄 (오버레이 제목)
- **summary** — **여러 줄**(`\n` 포함)로. 한 줄 정서 → 지배 키워드 → 인정한 지점 →
  수렴한 결론 → 별점 요약 → 반전 포인트 → 진행 제안. 문장을 붙이지 말고
  줄바꿈·불릿으로 끊어 **읽기 쉽게**. (프론트가 `white-space:pre-line` 로 렌더)
- **ratings / stats** — 1)의 결정론 값을 그대로 복사.
- **highlights** (선택, 배열) · **score_distribution**(1)의 값) — 기록용.
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

- `report_put.py` 출력의 `keywords / 인용 / summary 줄` 수 확인.
- 발표모드 [AI 분석] 탭에서 키워드에 마우스를 올리면 `why`+`q` 오버레이가 뜬다.

## 주의

- **RLS 데모 등급** — anon 키로 직접 PATCH 된다. 사내 비공개 전용.
- 인용문 `q` 는 답변 원문을 **변형 없이** 발췌(따옴표는 렌더러가 붙임).
- 별점 축 키: `length·difficulty·fun·novelty·overall`. 난이도는 '적절할수록 높음'.
- 개인정보(phone4)는 report 에 넣지 않는다. 표시는 익명 닉네임 기준.
