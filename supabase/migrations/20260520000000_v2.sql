-- ════════════════════════════════════════════════════════════════════════
-- untoldChapter v2 — 작가정보·회차 연월·공감(reaction) 추가
-- (기존 init 마이그레이션은 수정하지 않고 이 파일을 새로 추가)
-- ════════════════════════════════════════════════════════════════════════

-- 책: 작가 소개 + 회차 연월(YYYYMM)
alter table book add column if not exists author_bio text not null default '';
alter table book add column if not exists yearmonth  text not null default '';

-- 공감 (한 사람이 한 답변에 1회 — 토글)
create table if not exists reaction (
  id            uuid primary key default gen_random_uuid(),
  book_id       uuid not null references book(id) on delete cascade,
  q_index       int  not null,
  target_phone4 text not null,
  author_phone4 text not null,
  created_at    timestamptz not null default now(),
  unique (book_id, q_index, target_phone4, author_phone4)
);
create index if not exists reaction_book_idx on reaction(book_id, q_index);

alter table reaction enable row level security;
drop policy if exists reaction_rw on reaction;
create policy reaction_rw on reaction for all to anon, authenticated using (true) with check (true);

-- 데모 시즌 책에 회차 연월·작가 소개 채워두기
update book set yearmonth='202606',
  author_bio='라미 카민스키 — 5개국에서 살았고, 소설을 쓰기 전 10년간 문학 번역을 했다. 글 쓸 때 늘 재즈를 듣는다.'
  where id='00000000-0000-0000-0000-0000000000b1';
update book set yearmonth='202607',
  author_bio='앤디 위어 — ''마션''의 작가. 공학·과학 디테일을 직접 계산해 검증하는 편.'
  where id='00000000-0000-0000-0000-0000000000b2';
update book set yearmonth='202608',
  author_bio='(저자 미확정 — 진행 결과를 보고 8월 도서 확정)'
  where id='00000000-0000-0000-0000-0000000000b3';
