-- ════════════════════════════════════════════════════════════════════════
-- v10 — club 의 공개/비공개 의미를 명확한 컬럼으로 분리
--   배경:
--     v7 에서 club.is_open 을 "공개 여부" 의미로 도입했으나, 같은 이름
--     컬럼이 meeting.is_open(시즌의 활성/마감 여부)에도 존재해서 의미가
--     모호. 사용자가 "is_open 은 마감 아니냐"고 지적하여 컬럼명을
--     `is_public` 으로 분리.
--   변경:
--     - club.is_public boolean default true 추가
--     - 기존 club.is_open 값을 is_public 으로 동기화
--     - club.is_open 컬럼은 호환을 위해 잠시 유지(다음 PR 에서 drop 권장)
--   idempotent.
-- ════════════════════════════════════════════════════════════════════════

alter table club add column if not exists is_public boolean not null default true;

-- 기존 is_open 의 값을 is_public 으로 옮김 (idempotent — 매번 동일 상태로 수렴)
update club set is_public = coalesce(is_open, true) where is_public is distinct from coalesce(is_open, true);

-- (선택) 사용 안 하는 호환 컬럼 주석 — 다음 PR 에서 drop 검토
-- comment on column club.is_open is 'DEPRECATED v10: use is_public';
