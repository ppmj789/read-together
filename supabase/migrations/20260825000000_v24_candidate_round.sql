-- ════════════════════════════════════════════════════════════════════════
-- v24 — 다음 책 추천을 '회차(round)' 단위로 (2026-08-25)
--
-- 배경: 후보가 시즌에 계속 쌓이기만 했다. 한 권을 골라 [책으로 등록] 해도
--   나머지 후보와 표가 그대로 남아, 다음 책을 정할 때 "이번에 새로 받은 추천"
--   과 "지난번에 밀린 추천" 이 한 목록에 섞였다. 그렇다고 지우면 그때 어떤
--   책이 왜 올라왔는지가 통째로 사라진다.
--
-- 설계: 후보에 회차 번호를 달고, 시즌은 '지금 받는 회차' 를 들고 있는다.
--   - next_book_candidate.round — 이 후보가 올라온 회차 (기본 1)
--   - season.cand_round        — 이 시즌이 지금 받는 회차 (기본 1)
--   화면은 cand_round 와 같은 회차만 보여주고(투표·수정·삭제도 그 회차만),
--   그보다 낮은 회차는 [지난 회차 추천 보기] 로 읽기 전용 열람.
--   모임장이 [이번 추천 마감하고 새로 받기] 를 누르면 cand_round 가 +1 되고
--   목록이 빈 채로 새 회차가 열린다 — 삭제가 아니라 보관이라 되돌아볼 수 있다.
--
-- 일회성 정리: 이미 후보가 쌓인 시즌은 그 후보를 1회차로 묶고 2회차를 새로
--   연다. 적용 직후 투표 화면은 '2회차 추천 · 후보 없음' 에서 시작하고,
--   기존 추천은 [지난 회차 추천 보기] 안에 그대로 남는다.
--
-- RLS: 컬럼 추가뿐이라 정책 변경 없음. season 은 이미 update 정책 보유
--   (v18 이후 모임장이 is_open 등을 갱신) — cand_round 도 같은 정책을 탄다.
-- ════════════════════════════════════════════════════════════════════════

alter table next_book_candidate
  add column if not exists round int not null default 1 check (round >= 1);
alter table season
  add column if not exists cand_round int not null default 1 check (cand_round >= 1);

create index if not exists nbc_season_round_idx on next_book_candidate(season_id, round);

-- 일회성: 후보가 이미 있는 시즌은 지금까지의 추천을 1회차로 닫고 2회차를 연다
update season s
   set cand_round = 2
 where s.cand_round = 1
   and exists (select 1 from next_book_candidate c where c.season_id = s.id);
