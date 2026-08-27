-- ════════════════════════════════════════════════════════════════════════
-- v26 — 시즌의 여는 문장(에피그래프)과 결(theme) (2026-08-27)
--
-- 배경: 시즌은 제목 + 한 줄 설명이 전부였다. 그런데 「가을의 문장」 시즌은
--   카뮈의 "가을은 모든 잎이 꽃이 되는 두 번째 봄이다" 에서 출발했고, 그
--   문장이 곧 "어떤 책을 추천할까" 의 기준이다. 추천을 받는 자리(투표 페이지)와
--   시즌 페이지 양쪽에서 같은 문장을 보여줘야 추천이 한 방향으로 모인다.
--
-- 설계:
--   - epigraph / epigraph_by — 여는 문장과 출처. 한 줄 설명(season_sub)은
--     책이 모인 뒤 엮는 '이야기 흐름'(예: 나 → 연결 → 관계의 그늘)으로 남기고,
--     그 이전 단계인 '이 시즌은 어떤 결인가' 를 인용이 맡는다.
--   - theme — 시즌 화면·책꽂이 칸의 강조색 키(예: 'autumn'). 클래스명으로 쓰여
--     서버에서도 [a-z-] 로 제한하고, 클라이언트도 같은 필터를 한 번 더 건다.
--
-- ⚠️ season 은 v16 hardening 이후 **컬럼 단위 select grant** 테이블이다.
--   새 컬럼은 grant 를 함께 주지 않으면 anon 조회가 42501 로 죽는다 (v24 →
--   v25 에서 실제로 밟은 함정). 그래서 이 마이그레이션은 grant 를 같이 넣는다.
-- ════════════════════════════════════════════════════════════════════════

alter table season
  add column if not exists epigraph text not null default '' check (char_length(epigraph) <= 300);
alter table season
  add column if not exists epigraph_by text not null default '' check (char_length(epigraph_by) <= 100);
alter table season
  add column if not exists theme text not null default '' check (theme ~ '^[a-z-]{0,20}$');

grant select (epigraph, epigraph_by, theme) on season to anon, authenticated;
