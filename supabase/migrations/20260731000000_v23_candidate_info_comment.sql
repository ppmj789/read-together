-- ════════════════════════════════════════════════════════════════════════
-- v23 — 다음 책 후보에 책 정보(출판사·가격·표지)와 의견(댓글) 추가 (2026-07-31)
--
-- 1) next_book_candidate 에 publisher / price / cover_url 컬럼 추가
--    추천 이유(reason)는 '왜 읽고 싶은가'라는 주관이고, 출판사·가격은 고르는 데
--    필요한 객관 정보라 분리해서 담는다. price 는 '13,500원'·'무료(웹 공개)' 같은
--    표기 유연성을 위해 text. cover_url 은 정적 표지(assets/covers/)가 없는
--    후보용 폴백 — 표시는 coverFor(title) 정적 파일이 항상 우선.
--
-- 2) next_book_candidate 에 update 정책 추가 — 버그 수정.
--    v21 의 '추천 수정' 기능은 update 정책이 없어 PATCH 가 조용히 0행으로
--    끝나고 있었다(클라이언트는 에러 없이 "수정했어요" 표시). RLS update 는
--    insert/delete 와 같은 회원 셀프서비스 등급으로 개방한다.
--
-- 3) next_book_comment 신설 — 후보에 다는 의견(댓글).
--    투표(북마크)는 익명 집계지만, "이 책 절판 아니야?" "영화 먼저 볼까?" 같은
--    대화가 오갈 자리가 없었다. answer 의 comment 와 같은 구조로, 후보 삭제 시
--    cascade. RLS 는 comment 와 동일 신뢰 모델(select/insert/delete, update 없음).
-- ════════════════════════════════════════════════════════════════════════

-- 1) 책 정보 컬럼
alter table next_book_candidate
  add column if not exists publisher text not null default '' check (char_length(publisher) <= 100);
alter table next_book_candidate
  add column if not exists price     text not null default '' check (char_length(price) <= 40);
alter table next_book_candidate
  add column if not exists cover_url text not null default '' check (char_length(cover_url) <= 500);

-- 2) update 정책 (v21 수정 기능 무동작 버그 수정)
drop policy if exists next_book_candidate_update on next_book_candidate;
create policy next_book_candidate_update on next_book_candidate
  for update to anon, authenticated using (true) with check (true);

-- 3) 후보 의견(댓글)
create table if not exists next_book_comment (
  id            uuid primary key default gen_random_uuid(),
  candidate_id  uuid not null references next_book_candidate(id) on delete cascade,
  author_phone4 text not null check (author_phone4 ~ '^[0-9]{4}$' or author_phone4 = 'host'),
  body          text not null check (char_length(body) between 1 and 500),
  created_at    timestamptz not null default now()
);
create index if not exists nbcm_cand_idx on next_book_comment(candidate_id);

alter table next_book_comment enable row level security;
drop policy if exists next_book_comment_select on next_book_comment;
drop policy if exists next_book_comment_insert on next_book_comment;
drop policy if exists next_book_comment_delete on next_book_comment;
create policy next_book_comment_select on next_book_comment for select to anon, authenticated using (true);
create policy next_book_comment_insert on next_book_comment for insert to anon, authenticated with check (true);
create policy next_book_comment_delete on next_book_comment for delete to anon, authenticated using (true);
