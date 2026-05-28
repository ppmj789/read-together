-- ════════════════════════════════════════════════════════════════════════
-- v14 — 이향인 테스트 점수 회원별 저장 (실제 모임 분석용)
--   ihyang_score: 0~280 (내향성 원점수, 188 이상 = 이향인)
--   ihyang_pct  : 0~100 (내향성 %)
--   프론트는 best-effort upsert — 컬럼이 없어도 답변 본문에 점수 라인이
--   남으므로 동작은 하지만, 분석 편의를 위해 본 컬럼 적용을 권장.
--   idempotent.
-- ════════════════════════════════════════════════════════════════════════

alter table member_book add column if not exists ihyang_score int;
alter table member_book add column if not exists ihyang_pct   int;
