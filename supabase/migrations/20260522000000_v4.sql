-- ════════════════════════════════════════════════════════════════════════
-- untoldChapter v4 — 모임 공개여부(is_open)
-- (기존 마이그레이션 수정 금지, 새 파일. idempotent)
-- ════════════════════════════════════════════════════════════════════════
alter table meeting add column if not exists is_open boolean not null default true;
-- 데모 모임은 공개
update meeting set is_open=true where code='HUMAN-Q2';
