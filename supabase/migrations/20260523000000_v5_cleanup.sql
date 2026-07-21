-- ════════════════════════════════════════════════════════════════════════
-- ⚠️⚠️ 수동 재실행 절대 금지 ⚠️⚠️
--   이 파일은 데이터를 DELETE 하는 일회성 정리 마이그레이션이다.
--   SQL Editor 에 다시 붙여넣어 Run 하면 현재 운영 데이터(시드 9001~9004
--   외 모든 답변·댓글·공감·member_book)가 삭제된다. 적용은 CLI/Actions
--   마이그레이션 체인으로만. (경고 추가: 2026-07-21)
-- ════════════════════════════════════════════════════════════════════════
-- v5 — 테스트 데이터 정리 + 모임명 통합 ('未知의 서재')
--   목적:
--     1) 이향인 책이 들어 있는 시즌(=시드 HUMAN-Q2) 외의 모든 모임 제거
--        (책·답변·댓글·공감·member_book 은 ON DELETE CASCADE 로 자동 정리)
--     2) HUMAN-Q2 시즌 자체는 유지하되, 데모 시드 외 사용자가 만든
--        ad-hoc 답변/댓글/공감/member_book 만 정리(phone4 not in '9001'..'9004')
--     3) 모든 meeting.name 을 '未知의 서재'로 통일 (모임명 고정 정책)
--   idempotent: 여러 번 돌려도 안전.
-- ════════════════════════════════════════════════════════════════════════

-- 1) 이향인 책이 들어 있지 않은 모임 제거
delete from meeting
 where id not in (
   select distinct b.meeting_id
     from book b
    where b.title = '이향인'
 );

-- 2) HUMAN-Q2 시즌의 ad-hoc 사용자 데이터 정리 (시드 9001~9004 만 보존)
delete from comment
 where author_phone4 not in ('9001','9002','9003','9004','host');
delete from reaction
 where author_phone4 not in ('9001','9002','9003','9004');
delete from answer
 where phone4 not in ('9001','9002','9003','9004');
delete from member_book
 where phone4 not in ('9001','9002','9003','9004');

-- 3) 모임명 통합 — '未知의 서재'로 고정
update meeting set name = '未知의 서재';
