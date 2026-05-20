-- ════════════════════════════════════════════════════════════════════════
-- v9 — 모임장 다명(멀티 오너) 지원
--   변경:
--     - club.owner_phone4s text[] 추가 (default '{}')
--     - 기존 owner_phone4 의 값을 owner_phone4s 로 마이그레이션
--     - owner_phone4 컬럼은 호환을 위해 유지(첫 운영자 미러용, 읽기 전용)
--   idempotent.
-- ════════════════════════════════════════════════════════════════════════

alter table club add column if not exists owner_phone4s text[] not null default '{}';

-- 기존 owner_phone4 단일값을 owner_phone4s 배열로 옮김 (이미 있으면 보존)
update club
   set owner_phone4s = array[owner_phone4]
 where owner_phone4 is not null
   and (owner_phone4s is null or array_length(owner_phone4s, 1) is null);

create index if not exists club_owners_idx on club using gin (owner_phone4s);
