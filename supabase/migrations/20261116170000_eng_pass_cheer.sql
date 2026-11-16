-- ════════════════════════════════════════════════════════════════════════
-- eng_* — 패스권 + 응원·콕 찌르기 (2026-11-16)
--
--   eng_check.pass : 그날 패스권 사용(완료로 침). 한 주(월~일) 1장 제한은 화면에서 계산.
--   eng_cheer      : 응원(cheer, 👏) / 콕 찌르기(poke, 👉).
--                    같은 날 같은 사람에게 같은 종류는 한 번만(기본키로 막음).
--
-- 신뢰 모델은 기존 eng_* 와 동일: anon select/insert 개방, update·delete 없음.
-- ※ index.html 을 올리기 전에 이 파일을 먼저 실행해야 함
--   (새 화면이 eng_check.pass 칸을 읽기 때문).
-- ════════════════════════════════════════════════════════════════════════

alter table eng_check add column if not exists pass boolean not null default false;

create table if not exists eng_cheer (
  day         date not null,
  from_phone4 text not null references eng_member(phone4) on delete cascade,
  to_phone4   text not null references eng_member(phone4) on delete cascade,
  kind        text not null check (kind in ('cheer','poke')),
  created_at  timestamptz not null default now(),
  primary key (day, from_phone4, to_phone4, kind),
  check (from_phone4 <> to_phone4)
);

alter table eng_cheer enable row level security;

drop policy if exists eng_cheer_s on eng_cheer;
drop policy if exists eng_cheer_i on eng_cheer;
create policy eng_cheer_s on eng_cheer for select using (true);
create policy eng_cheer_i on eng_cheer for insert with check (true);
grant select, insert on eng_cheer to anon, authenticated;
