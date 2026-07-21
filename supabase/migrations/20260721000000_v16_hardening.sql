-- ════════════════════════════════════════════════════════════════════════
-- v16 — 데이터 보호 강화 (2026-07-21)
--
-- 배경: anon 키가 정적 페이지에 공개되는 구조에서 RLS 가 전부 all-true 라
--   콘솔 한 줄로 club 전체 삭제(cascade)까지 가능했고, 모임 비밀번호가
--   평문 컬럼 그대로 모든 방문자에게 다운로드되고 있었다.
--
-- 이 마이그레이션이 하는 것:
--   1) club/meeting/book 의 anon DELETE 차단
--      — all-true 단일 정책(for all)을 select/insert/update 3개로 분리하고
--        DELETE 정책은 만들지 않는다. 삭제는 아래 비번 검증 RPC 로만.
--      — answer/comment/reaction/member_book 은 현행 유지
--        (본인 답변·댓글 삭제, 공감 토글 기능 보존. 사내 신뢰 모델).
--   2) club.password / meeting.password 를 클라이언트에서 숨김
--      — 테이블 단위 select 권한을 회수하고 password 를 뺀 컬럼 목록으로
--        재부여. 모임장 인증은 verify_club RPC 로 서버에서만 비교.
--      ⚠️ 이후 club/meeting 에 컬럼을 추가하는 마이그레이션은
--         grant select(새컬럼) on <table> to anon, authenticated; 를 함께 넣을 것.
--   3) 삭제 RPC 3종 (delete_club / delete_meeting / delete_book)
--      — security definer. 모임(club) 비밀번호가 맞을 때만 삭제 수행.
--
-- idempotent: 정책·함수는 drop-if-exists / create-or-replace, grant 는 재실행 무해.
-- ════════════════════════════════════════════════════════════════════════

-- 1) club/meeting/book: all-true 정책을 3분할, DELETE 정책 없음
do $$
declare t text;
begin
  foreach t in array array['club','meeting','book'] loop
    execute format('drop policy if exists %1$s_rw on %1$s', t);
    execute format('drop policy if exists %1$s_select on %1$s', t);
    execute format('drop policy if exists %1$s_insert on %1$s', t);
    execute format('drop policy if exists %1$s_update on %1$s', t);
    execute format('create policy %1$s_select on %1$s for select to anon, authenticated using (true)', t);
    execute format('create policy %1$s_insert on %1$s for insert to anon, authenticated with check (true)', t);
    execute format('create policy %1$s_update on %1$s for update to anon, authenticated using (true) with check (true)', t);
  end loop;
end $$;

-- 2) password 컬럼 숨김 (컬럼 단위 grant 로 교체)
revoke select on club from anon, authenticated;
grant select (id, name, code, intro, is_open, created_at, owner_phone4, owner_phone4s, is_public)
  on club to anon, authenticated;

revoke select on meeting from anon, authenticated;
grant select (id, name, code, season_title, season_sub, created_at, is_open, club_id)
  on meeting to anon, authenticated;

-- 3) 서버측 비번 검증 RPC
--    verify_club: 모임장 인증. 코드+비번이 맞으면 club id, 아니면 null.
create or replace function verify_club(p_code text, p_pw text)
returns uuid
language sql stable security definer set search_path = public
as $$
  select id from club where upper(code) = upper(p_code) and password = p_pw limit 1;
$$;

--    delete_club: 비번이 맞을 때만 모임 삭제 (시즌·책·답변 cascade). true=삭제됨.
create or replace function delete_club(p_club_id uuid, p_pw text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  delete from club where id = p_club_id and password = p_pw;
  return found;
end;
$$;

--    delete_meeting: 소속 모임 비번이 맞을 때만 시즌 삭제.
create or replace function delete_meeting(p_meeting_id uuid, p_pw text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  delete from meeting m
  using club c
  where m.id = p_meeting_id and c.id = m.club_id and c.password = p_pw;
  return found;
end;
$$;

--    delete_book: 소속 모임 비번이 맞을 때만 책 삭제.
create or replace function delete_book(p_book_id uuid, p_pw text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  delete from book b
  using meeting m, club c
  where b.id = p_book_id and m.id = b.meeting_id and c.id = m.club_id and c.password = p_pw;
  return found;
end;
$$;

revoke all on function verify_club(text, text) from public;
revoke all on function delete_club(uuid, text) from public;
revoke all on function delete_meeting(uuid, text) from public;
revoke all on function delete_book(uuid, text) from public;
grant execute on function verify_club(text, text) to anon, authenticated;
grant execute on function delete_club(uuid, text) to anon, authenticated;
grant execute on function delete_meeting(uuid, text) to anon, authenticated;
grant execute on function delete_book(uuid, text) to anon, authenticated;
