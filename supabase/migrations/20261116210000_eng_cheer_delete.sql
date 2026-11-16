-- eng_cheer — 리액션 취소(다시 누르면 지움)를 위해 delete 허용 (2026-11-16)
-- 신뢰 모델은 기존 eng_* 와 동일(anon 개방). 화면은 내가 보낸 것만 지움.
drop policy if exists eng_cheer_d on eng_cheer;
create policy eng_cheer_d on eng_cheer for delete using (true);
grant delete on eng_cheer to anon, authenticated;
