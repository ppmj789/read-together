-- ════════════════════════════════════════════════════════════════════════
-- v31 — 시즌 결산 리포트 (2026-09-04)
--
-- 책마다 book.report(발표자료)가 있듯 시즌에는 season.report 하나.
-- 시즌의 책이 전부 마감되고 리포트가 저장되면 책장 칸 안 책들 옆에
-- 접은 신문(결산호)이 놓이고, 누르면 시즌 결산 페이지가 열린다.
-- 생성은 앱 밖(Claude generate-report 스킬 season_put.py)에서 PATCH.
--
-- ⚠️ season 은 컬럼 단위 select grant 테이블(v16) — 신규 컬럼은 grant 필수.
--    update 는 테이블 단위 grant 라 별도 grant 불필요.
-- ════════════════════════════════════════════════════════════════════════

alter table season
  add column if not exists report jsonb;

grant select (report) on season to anon, authenticated;
