-- ════════════════════════════════════════════════════════════════════════
-- eng_* — 영어 스터디 앱(english-together) 테이블 (2026-11-16)
--
-- 같은 Supabase 프로젝트를 쓰는 별도 앱. 화면은 ppmj789/english-together
-- 저장소(GitHub Pages)에 있고, DB 마이그레이션 이력은 이 저장소 하나로
-- 모으기 위해 여기에 둔다. read-together 테이블과는 연결 없음.
--
--   eng_member : 참여자(휴대폰 뒤 4자리 + 이름 + 색)
--   eng_check  : 날짜별 체크(스픽 완료, 영상 시청) — (day, phone4) 1행
--   eng_video  : 날짜별 오늘의 영상(셋이 같은 영상) — day 1행
--
-- 신뢰 모델은 미지의 서재와 동일: anon select/insert/update 개방, delete 없음.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists eng_member (
  phone4     text primary key check (phone4 ~ '^[0-9]{4}$'),
  name       text not null check (char_length(name) between 1 and 20),
  color      text not null default '#f4a7b9' check (color ~ '^#[0-9a-fA-F]{6}$'),
  created_at timestamptz not null default now()
);

create table if not exists eng_check (
  day        date not null,
  phone4     text not null references eng_member(phone4) on delete cascade,
  speak      boolean not null default false,
  video      boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (day, phone4)
);

create table if not exists eng_video (
  day        date primary key,
  url        text not null check (char_length(url) between 1 and 500),
  title      text not null default '' check (char_length(title) <= 200),
  by_phone4  text references eng_member(phone4) on delete set null,
  updated_at timestamptz not null default now()
);

alter table eng_member enable row level security;
alter table eng_check  enable row level security;
alter table eng_video  enable row level security;

do $$
declare t text;
begin
  foreach t in array array['eng_member','eng_check','eng_video'] loop
    execute format('drop policy if exists %1$s_s on %1$s', t);
    execute format('drop policy if exists %1$s_i on %1$s', t);
    execute format('drop policy if exists %1$s_u on %1$s', t);
    execute format('create policy %1$s_s on %1$s for select using (true)', t);
    execute format('create policy %1$s_i on %1$s for insert with check (true)', t);
    execute format('create policy %1$s_u on %1$s for update using (true) with check (true)', t);
    execute format('grant select, insert, update on %1$s to anon, authenticated', t);
  end loop;
end $$;
