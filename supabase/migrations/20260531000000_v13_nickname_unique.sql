-- ════════════════════════════════════════════════════════════════════════
-- v13 — 같은 책 안에서 닉네임 중복 방지
--   배경:
--     member_book 의 PK 는 (book_id, phone4) 뿐이라, 같은 책에서 서로 다른
--     두 사람이 동일한 닉네임을 가질 수 있었다(프론트에도 중복 검사 없었음).
--   판정 기준 (프론트 normNick 과 일치):
--     - 연속 공백을 하나로 축약하고 앞뒤 공백 제거
--     - 대소문자 무시(lower)
--     예) '졸린  고양이 ' == '졸린 고양이' == '졸린 고양이'(영문 대소문자 무시)
--   빈 닉네임('' / 공백뿐)은 인덱스 대상에서 제외(placeholder 충돌 방지).
--   idempotent — 기존에 정규화 기준 중복이 없을 때만 생성 성공.
-- ════════════════════════════════════════════════════════════════════════

create unique index if not exists member_book_book_nick_uq
  on member_book (
    book_id,
    (lower(btrim(regexp_replace(nickname, '\s+', ' ', 'g'))))
  )
  where btrim(nickname) <> '';
