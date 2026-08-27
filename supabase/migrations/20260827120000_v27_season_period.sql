-- ════════════════════════════════════════════════════════════════════════
-- v27 — 시즌 기간 표기(season.period) (2026-08-27)
--
-- 책꽂이 칸에 '2026.06~08' 처럼 시기를 띄운다. 책이 꽂힌 시즌은 책들의
-- yearmonth(없으면 실제 열린 달)에서 자동으로 뽑히지만, 아직 책이 없는
-- 시즌 — 지금 추천을 받는 중인 「가을의 문장」 같은 — 은 뽑아낼 근거가
-- 없다. 그래서 시즌이 직접 들고 있을 수 있는 자유 표기 칸을 둔다.
-- 책이 꽂히면 자동 계산이 우선이고, period 는 그 전까지의 예고.
--
-- ⚠️ season 은 컬럼 단위 select grant 테이블(v16) — 신규 컬럼은 grant 필수.
-- ════════════════════════════════════════════════════════════════════════

alter table season
  add column if not exists period text not null default '' check (char_length(period) <= 40);

grant select (period) on season to anon, authenticated;
