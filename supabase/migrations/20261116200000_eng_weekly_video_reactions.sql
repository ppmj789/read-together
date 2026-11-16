-- ════════════════════════════════════════════════════════════════════════
-- eng_* — 영상 주 3편 + 리액션 3종 + 공유 전 테스트 데이터 초기화 (2026-11-16)
--
--   eng_watch : 누가 그 주(월요일 날짜)에 어떤 영상(vid = 유튜브 id)을 봤는지 1행.
--               볼 영상 목록은 index.html 의 VIDEO_SETS 에 고정. 체크 해제 = 삭제.
--   eng_cheer.kind : cheer(👏 박수) · laugh(😂 웃음) · love(❤️ 하트) · poke(👉 콕)
--   eng_check.video, eng_video 는 더 이상 화면에서 안 씀(테이블은 남겨 둠).
--
-- 신뢰 모델은 기존 eng_* 와 동일.
-- ※ 이 파일은 아래 초기화(delete)를 포함함 — 실제 공유 시작 전 1회용.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists eng_watch (
  week       date not null,
  phone4     text not null references eng_member(phone4) on delete cascade,
  vid        text not null,
  created_at timestamptz not null default now(),
  primary key (week, phone4, vid)
);

alter table eng_watch enable row level security;
drop policy if exists eng_watch_s on eng_watch;
drop policy if exists eng_watch_i on eng_watch;
drop policy if exists eng_watch_d on eng_watch;
create policy eng_watch_s on eng_watch for select using (true);
create policy eng_watch_i on eng_watch for insert with check (true);
create policy eng_watch_d on eng_watch for delete using (true);
grant select, insert, delete on eng_watch to anon, authenticated;

alter table eng_cheer drop constraint if exists eng_cheer_kind_check;
alter table eng_cheer add constraint eng_cheer_kind_check check (kind in ('cheer','laugh','love','poke'));

-- 공유 전 초기화: 테스트로 쌓인 체크·응원·영상·시청 기록과 옛 테스트 멤버(7220) 삭제
delete from eng_watch;
delete from eng_cheer;
delete from eng_check;
delete from eng_video;
delete from eng_member where phone4 not in ('0001','0002','0003');
