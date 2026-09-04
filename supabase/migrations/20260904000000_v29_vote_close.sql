-- ════════════════════════════════════════════════════════════════════════
-- v29 — 다음 책 투표 마감 (2026-09-04)
--
-- 후보를 다 모으고 표까지 나뉘면 어느 시점엔 문을 닫아야 한다. 닫힌 뒤에도
-- 목록·표는 그대로 보여야 하고(무엇이 왜 뽑혔는지가 시즌의 기록이다), 추천·
-- 투표·상태 변경만 막힌다.
--
-- vote_closed_at: 마감 시각. null 이면 열려 있음. 시각을 남겨 두면 "언제 닫혔나"
-- 가 기록으로 남고, 다시 열 때는 null 로 되돌리면 된다.
--
-- ⚠️ season 은 컬럼 단위 select grant 테이블(v16) — 신규 컬럼은 grant 필수.
-- ════════════════════════════════════════════════════════════════════════

alter table season add column if not exists vote_closed_at timestamptz;

grant select (vote_closed_at) on season to anon, authenticated;
