-- ════════════════════════════════════════════════════════════════════════
-- v22 — 답변 반응을 5종으로 확장 (2026-07-28)
--
-- 배경: reaction 이 '💛 공감' 단일 종류라 "좋다"는 말밖에 못 했다. 반대 의견을
--   '싫어요' 로 받으면 8~10명 서로 아는 모임에선 글쓰기가 위축되므로,
--   '전 다르게 읽었어요' 같은 결로 5종을 둔다.
--   underline(🔖 밑줄) / empathy(🙌 완전 동의) / insight(👀 생각 못 했네요)
--   / differ(🌀 전 다르게) / more(👂 더 듣고 싶어요)
--
-- 설계: kind 컬럼 default 'empathy' → 기존 공감 행이 백필 없이 🙌 로 승계된다.
--   유니크 제약을 (book_id,q_index,target,author) → +kind 로 넓혀 한 사람이
--   같은 답변에 여러 종류를 달 수 있게 한다(같은 종류 중복만 차단).
--   check 제약은 두지 않는다 — 종류 추가/삭제가 앱 배포만으로 되도록.
-- ════════════════════════════════════════════════════════════════════════

alter table reaction
  add column if not exists kind text not null default 'empathy';

-- v2 에서 인라인 unique(...) 로 만들어진 제약 (이름은 postgres 자동 생성 규칙)
alter table reaction
  drop constraint if exists reaction_book_id_q_index_target_phone4_author_phone4_key;

create unique index if not exists reaction_uniq
  on reaction(book_id, q_index, target_phone4, author_phone4, kind);
