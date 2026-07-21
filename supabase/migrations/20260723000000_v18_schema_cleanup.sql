-- ════════════════════════════════════════════════════════════════════════
-- v18 — 스키마 정리 (2026-07-21, 레드팀 DB 리뷰 반영)
--
-- 1) meeting → season 리네임
--    테이블명이 실제 의미(시즌)와 달라 계속 혼란을 만들었다. UI·문서 전역이
--    '시즌'이라 부르므로 데이터가 적은 지금 맞춘다. book.meeting_id 도
--    season_id 로 함께 리네임. (프론트 from('season') / season_id 로 동시 반영)
-- 2) 유령·중복 컬럼 정리
--    - club.is_open       → v10 에서 is_public 로 대체된 잔재
--    - club.owner_phone4  → v9 에서 owner_phone4s[] 로 대체된 읽기 미러
--    - season.code/password → v7 부터 미사용 (인증은 club 코드/비번)
--    - comment.author_nick → 표시는 항상 displayNick(결정론 해시)이라 죽은 데이터
-- 3) 삭제 RPC 를 season 기준으로 재정의 (delete_meeting → delete_season)
-- 4) member 테이블 신설 — '사람' 엔티티의 시작.
--    당장 answer 등의 phone4 를 갈아엎지 않고, 입장 시 (club, phone4) 매핑만
--    축적한다. 이후 4자리 충돌 해소·번호 변경·시즌 간 연속성의 기반.
-- 5) 데이터 무결성 check 제약 (신규 행부터 적용 — not valid)
--
-- idempotent: rename 은 if-exists 가드, drop column/constraint 는 if exists.
-- ════════════════════════════════════════════════════════════════════════

-- 1) meeting → season
alter table if exists meeting rename to season;
do $$ begin
  if exists (select 1 from information_schema.columns
             where table_schema='public' and table_name='book' and column_name='meeting_id') then
    alter table book rename column meeting_id to season_id;
  end if;
end $$;

-- 2) 유령·중복 컬럼 정리
alter table club   drop column if exists is_open;
alter table club   drop column if exists owner_phone4;
alter table season drop column if exists code;
alter table season drop column if exists password;
alter table comment drop column if exists author_nick;

-- 3) 삭제 RPC 재정의 (v16 의 meeting 참조 본문 교체)
drop function if exists delete_meeting(uuid, text);

create or replace function delete_season(p_season_id uuid, p_pw text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  delete from season s
  using club c
  where s.id = p_season_id and c.id = s.club_id and c.password = p_pw;
  return found;
end;
$$;

create or replace function delete_book(p_book_id uuid, p_pw text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  delete from book b
  using season s, club c
  where b.id = p_book_id and s.id = b.season_id and c.id = s.club_id and c.password = p_pw;
  return found;
end;
$$;

revoke all on function delete_season(uuid, text) from public;
revoke all on function delete_book(uuid, text) from public;
grant execute on function delete_season(uuid, text) to anon, authenticated;
grant execute on function delete_book(uuid, text) to anon, authenticated;

-- 4) member — 사람 엔티티 (매핑 축적용, FK 전환은 후속)
create table if not exists member (
  id           uuid primary key default gen_random_uuid(),
  club_id      uuid not null references club(id) on delete cascade,
  phone4       text not null check (phone4 ~ '^[0-9]{4}$'),
  display_name text not null default '',
  created_at   timestamptz not null default now(),
  unique (club_id, phone4)
);
alter table member enable row level security;
drop policy if exists member_select on member;
drop policy if exists member_insert on member;
drop policy if exists member_update on member;
create policy member_select on member for select to anon, authenticated using (true);
create policy member_insert on member for insert to anon, authenticated with check (true);
create policy member_update on member for update to anon, authenticated using (true) with check (true);
-- delete 정책 없음 (v16 방침과 동일)

-- 5) 무결성 check — 기존 행은 건드리지 않음(not valid), 신규 행부터 강제
alter table answer  drop constraint if exists answer_body_len;
alter table answer  add  constraint answer_body_len  check (char_length(body) <= 20000) not valid;
alter table comment drop constraint if exists comment_body_len;
alter table comment add  constraint comment_body_len check (char_length(body) <= 2000) not valid;
alter table answer  drop constraint if exists answer_qidx;
alter table answer  add  constraint answer_qidx      check (q_index between 0 and 50) not valid;
alter table member_book drop constraint if exists mb_phone4_fmt;
alter table member_book add  constraint mb_phone4_fmt check (phone4 ~ '^[0-9]{4}$') not valid;
alter table comment drop constraint if exists cm_author_fmt;
alter table comment add  constraint cm_author_fmt    check (author_phone4 ~ '^[0-9]{4}$' or author_phone4 = 'host') not valid;
