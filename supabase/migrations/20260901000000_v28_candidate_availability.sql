-- ════════════════════════════════════════════════════════════════════════
-- v28 — 후보 책을 어디서 구할 수 있는지 (밀리 · 도서관) (2026-09-01)
--
-- 배경: 투표할 때 "읽고 싶다" 만큼 "구할 수 있나" 가 실제 선택을 가른다.
--   구독 중인 밀리의 서재에 있으면 부담이 0이고, 도서관에 있으면 그 다음이다.
--
-- 설계: 자동 조회는 불가능하다 — 밀리·공공도서관 모두 공개 API 가 없고,
--   정적 페이지(GitHub Pages)에서 남의 사이트를 조회하면 CORS 에 막힌다.
--   그래서 '사람이 확인해서 체크하는' 3-상태 필드로 둔다:
--     '' = 아직 모름(기본) · 'y' = 있음 · 'n' = 없음
--   화면에는 확인용 검색 링크(밀리·도서관)를 함께 띄워, 모름 상태에서도
--   누구나 한 번 눌러 확인하고 체크해 줄 수 있게 한다.
--
-- next_book_candidate 는 테이블 단위 grant 라 컬럼 grant 는 불필요
-- (season 과 달리 v16 컬럼 단위 grant 대상이 아님 — v20/v21 주석 참고).
-- ════════════════════════════════════════════════════════════════════════

alter table next_book_candidate
  add column if not exists millie  text not null default '' check (millie  in ('','y','n'));
alter table next_book_candidate
  add column if not exists library text not null default '' check (library in ('','y','n'));
