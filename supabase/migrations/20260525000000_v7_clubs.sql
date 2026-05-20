-- ════════════════════════════════════════════════════════════════════════
-- v7 — 모임(club) 엔티티 신설 + 시즌(=meeting) 을 모임 하위로 묶기
--   모델:
--     club (모임)              ← 신규
--       ├── meeting (시즌)     ← 기존 테이블 그대로, club_id FK 추가
--       │      └── book        ← 기존
--       │           ├── answer / member_book / comment / reaction
--   인증:
--     - 모임장 = club.code + club.password 로 1회 인증 → 그 모임의 모든 시즌 관리
--     - meeting.code / meeting.password 컬럼은 호환을 위해 그대로 두되 사용하지 않음
--   시드:
--     - 기존 meeting('인간 본성 탐구' = HUMAN-Q2)을 시드 club '未知의 서재' (코드 UNTOLD/1234) 에 매핑
--   idempotent: 컬럼/테이블 추가는 if not exists, FK 매핑은 update where null.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists club (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  code       text not null unique,
  password   text not null,
  intro      text not null default '',
  is_open    boolean not null default true,
  created_at timestamptz not null default now()
);

alter table club enable row level security;
do $$ begin
  execute 'drop policy if exists club_rw on club';
  execute 'create policy club_rw on club for all to anon, authenticated using (true) with check (true)';
end $$;

-- meeting → club 의 FK
alter table meeting add column if not exists club_id uuid references club(id) on delete cascade;
create index if not exists meeting_club_idx on meeting(club_id);

-- 시드: 未知의 서재 (코드 UNTOLD · 비번 1234)
insert into club (id, name, code, password, intro, is_open) values
  ('00000000-0000-0000-0000-0000000000c1',
   '未知의 서재','UNTOLD','1234',
   '시드 모임 — 인간 본성 탐구 시즌(이향인 외 2권) 보유',
   true)
on conflict (code) do nothing;

-- 기존 meeting 들의 club_id 가 비어있으면 시드 club 으로 묶음
update meeting
   set club_id = '00000000-0000-0000-0000-0000000000c1'
 where club_id is null;
