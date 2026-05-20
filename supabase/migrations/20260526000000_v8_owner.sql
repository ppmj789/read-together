-- ════════════════════════════════════════════════════════════════════════
-- v8 — 모임장 자동 인식: club.owner_phone4
--   목적:
--     - 모임을 만든 사람의 휴대폰 뒤 4자리를 club 행에 저장
--     - 회원이 같은 phone4 로 로그인하면 자동으로 그 모임의 모임장 권한 부여
--       (별도 코드/비번 인증 화면 없이도 발표 모드/마감/시즌 추가 가능)
--   호환:
--     - 기존 club.code/password 컬럼은 유지 (백업 인증 키 · 다른 디바이스에서 위임용)
--     - 시드 club '未知의 서재' 는 owner_phone4=null 로 둠 (특정 운영자 없음, 공용 데모)
--   idempotent.
-- ════════════════════════════════════════════════════════════════════════

alter table club add column if not exists owner_phone4 text;
create index if not exists club_owner_idx on club(owner_phone4);
