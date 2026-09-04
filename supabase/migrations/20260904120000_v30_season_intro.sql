-- ════════════════════════════════════════════════════════════════════════
-- v30 — 시즌 서문 + 책마다 엮는 말 (2026-09-04)
--
-- 시즌 페이지 상단이 '이번 시즌 소개'가 된다. 여는 문장(v26 epigraph)만으론
-- "왜 이 세 권인가"가 안 보인다 — 모임장이 쓰는 서문(season.intro)과, 책마다
-- 시즌 문장의 어느 토막에 해당하는지(book.motif: '잎이 진다')와 한 줄 엮는 말
-- (book.angle)을 둔다. 셋 다 비어 있으면 화면은 예전 그대로다.
--
-- ⚠️ season 은 컬럼 단위 select grant 테이블(v16) — 신규 컬럼은 grant 필수.
--    book 은 테이블 단위 grant 라 별도 grant 불필요.
-- ════════════════════════════════════════════════════════════════════════

alter table season
  add column if not exists intro text not null default '' check (char_length(intro) <= 3000);

alter table book
  add column if not exists motif text not null default '' check (char_length(motif) <= 40),
  add column if not exists angle text not null default '' check (char_length(angle) <= 300);

grant select (intro) on season to anon, authenticated;
