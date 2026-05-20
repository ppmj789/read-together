-- ════════════════════════════════════════════════════════════════════════
-- v12 — v11 의 과적용 보정: 데이터가 전혀 없는 책은 '예정' 으로 복원
--   배경:
--     v11 이 "닫힘이 아닌 모든 책의 opened_at=now()" 로 채워서, 시드의
--     프로젝트 헤일메리·다크 심리학 같은 '아직 안 열린' 책들도 '열림'
--     상태로 잘못 들어감.
--   판정:
--     answer / member_book 행이 전혀 없는 책 = 사용자 활동 이력 없음
--     = 사실은 '예정' 이었던 책 → opened_at 을 null 로 되돌림
--   영향 없는 케이스:
--     - 답변 한 개라도 있는 책: opened_at 유지 (열림)
--     - 닫힌 책: closed_at 있으므로 조건에 안 걸림
--   idempotent.
-- ════════════════════════════════════════════════════════════════════════

update book set opened_at = null
 where closed_at is null
   and opened_at is not null
   and not exists (select 1 from answer       a where a.book_id = book.id)
   and not exists (select 1 from member_book mb where mb.book_id = book.id);
