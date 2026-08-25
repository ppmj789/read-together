-- ════════════════════════════════════════════════════════════════════════
-- v25 — season.cand_round 에 컬럼 단위 select grant (2026-08-25)
--
-- v24 로 season.cand_round 를 추가했지만, season 은 v16 hardening 에서
-- `revoke select on meeting` + `grant select (컬럼 나열)` 로 **컬럼 단위**
-- grant 를 쓰는 테이블이다(비번 컬럼 숨김 목적, meeting→season 리네임으로
-- 그대로 승계). 그래서 새 컬럼은 grant 목록에 없어 anon 이 읽지 못하고
-- `42501 permission denied for table season` 이 났다.
--
-- v16 주석의 경고("새 컬럼 추가 시 grant select(새컬럼) 을 함께 넣을 것")를
-- v24 에서 빠뜨린 것에 대한 후속 수정. club/season 두 테이블에만 해당하며
-- next_book_candidate.round 는 테이블 단위 grant 라 영향 없다.
-- ════════════════════════════════════════════════════════════════════════

grant select (cand_round) on season to anon, authenticated;
