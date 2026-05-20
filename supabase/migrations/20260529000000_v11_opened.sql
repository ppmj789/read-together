-- ⚠️ 이 마이그레이션은 데이터 활동이 없는 책도 '열림'으로 채우는
--    부작용이 있습니다. v12(20260530000000_v12_upcoming.sql) 를 함께 적용해
--    답변·멤버 이력 없는 책은 '예정' 으로 복원하세요.
-- ════════════════════════════════════════════════════════════════════════
-- v11 — 책 3상태: 예정 / 열림 / 닫힘
--   상태 판정 규칙:
--     opened_at == null  AND  closed_at == null  →  예정 (upcoming)
--     opened_at != null  AND  closed_at == null  →  열림 (open)
--     closed_at != null                          →  닫힘 (closed)
--   변경:
--     - book.opened_at timestamptz 추가
--     - 기존 책: 닫힘이 아니면 opened_at=now() 로 채워서 '열림' 유지
--     - 새 책: opened_at=null → '예정'으로 시작 (모임장이 명시적으로 열기)
--   idempotent.
-- ════════════════════════════════════════════════════════════════════════

alter table book add column if not exists opened_at timestamptz;

-- 기존 데이터 호환: 닫힘이 아닌 책은 모두 '열림' 으로 간주 (opened_at 채움)
update book set opened_at = coalesce(opened_at, now()) where closed_at is null;
-- 닫힌 책은 그 이전에 열렸던 걸로 가정 (opened_at = closed_at)
update book set opened_at = coalesce(opened_at, closed_at) where closed_at is not null;

create index if not exists book_opened_idx on book(opened_at);
