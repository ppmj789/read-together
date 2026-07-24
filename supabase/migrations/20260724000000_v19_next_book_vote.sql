-- ════════════════════════════════════════════════════════════════════════
-- v19 — 다음 책 투표(next_book_candidate / next_book_vote) (2026-07-24)
--
-- 배경: "예정(upcoming)" 다음 책을 고를 때 회원 의견을 모을 자리가 없었다.
--   시드의 8월 책 "다크 심리학(저자 미확정)"처럼, 진행 결과를 보고 다음 책을
--   정하는 실수요가 이미 있었다.
--
-- 설계:
--   - season 단위 부착. book(실제 읽는 책)과 분리 — 후보는 가벼운 투표풀이고,
--     승자는 모임장이 [책으로 등록]하면 그때 book 으로 승격(human-in-loop).
--   - 복수추천(approval): 한 사람이 여러 후보에 표 가능. 표는 (후보, 투표자)
--     1행, reaction 과 동일한 토글(insert/delete) 패턴. 익명 집계(표수만).
--   - 회원도 후보 제안 가능(by_phone4). 'host' = 모임장. 1인 추천 상한(3권)은
--     클라이언트 가드(운영 편의), 서버는 신뢰 모델 유지.
--   - season 삭제 시 후보 cascade, 후보 삭제 시 표 cascade.
--   - RLS 는 회원 셀프서비스 등급(answer/comment/material 과 동일 신뢰 모델):
--     select/insert/delete 개방, update 없음.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists next_book_candidate (
  id         uuid primary key default gen_random_uuid(),
  season_id  uuid not null references season(id) on delete cascade,
  title      text not null check (char_length(title) between 1 and 200),
  author     text not null default '' check (char_length(author) <= 200),
  by_phone4  text not null check (by_phone4 ~ '^[0-9]{4}$' or by_phone4 = 'host'),
  created_at timestamptz not null default now()
);
create index if not exists nbc_season_idx on next_book_candidate(season_id);

create table if not exists next_book_vote (
  candidate_id uuid not null references next_book_candidate(id) on delete cascade,
  voter_phone4 text not null check (voter_phone4 ~ '^[0-9]{4}$'),
  created_at   timestamptz not null default now(),
  primary key (candidate_id, voter_phone4)
);

alter table next_book_candidate enable row level security;
alter table next_book_vote      enable row level security;

do $$
declare t text;
begin
  foreach t in array array['next_book_candidate','next_book_vote'] loop
    execute format('drop policy if exists %1$s_select on %1$s', t);
    execute format('drop policy if exists %1$s_insert on %1$s', t);
    execute format('drop policy if exists %1$s_delete on %1$s', t);
    execute format('create policy %1$s_select on %1$s for select to anon, authenticated using (true)', t);
    execute format('create policy %1$s_insert on %1$s for insert to anon, authenticated with check (true)', t);
    execute format('create policy %1$s_delete on %1$s for delete to anon, authenticated using (true)', t);
  end loop;
end $$;
