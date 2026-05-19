-- ════════════════════════════════════════════════════════════════════════
-- 같이읽자 (read-together) — v1 백엔드 스키마 (Supabase / Postgres)
-- Supabase Dashboard → SQL Editor 에 통째로 붙여넣고 Run.
-- 재실행 안전(idempotent): 테이블/정책/시드 모두 if not exists · on conflict.
--
-- 인증 모델: 휴대폰 뒤 4자리(phone4)는 "식별자"일 뿐 인증이 아님.
--   사내 소규모 모임 신뢰 모델 → v1 은 anon 키 + 허용적 RLS(데모 등급).
--   운영 강화가 필요하면 RLS 정책을 좁히고 Edge Function 도입(다음 버전).
-- ════════════════════════════════════════════════════════════════════════

create extension if not exists pgcrypto;

-- ── 모임(시즌) ─────────────────────────────────────────────────────────────
create table if not exists meeting (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  code         text not null unique,
  password     text not null,
  season_title text not null,
  season_sub   text not null default '',
  created_at   timestamptz not null default now()
);

-- ── 책 ─────────────────────────────────────────────────────────────────────
create table if not exists book (
  id         uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references meeting(id) on delete cascade,
  ord        int  not null default 0,
  title      text not null,
  author     text not null default '',
  intro      text not null default '',
  questions  jsonb not null default '[]'::jsonb,   -- ["질문1","질문2",...]
  created_at timestamptz not null default now()
);
create index if not exists book_meeting_idx on book(meeting_id, ord);

-- ── 멤버×책 (제출여부 · 다축 별점 · 닉네임) ─────────────────────────────────
create table if not exists member_book (
  book_id    uuid not null references book(id) on delete cascade,
  phone4     text not null,
  nickname   text not null,
  submitted  boolean not null default false,
  ratings    jsonb   not null default '{}'::jsonb, -- {"length":4,"fun":3,...}
  updated_at timestamptz not null default now(),
  primary key (book_id, phone4)
);

-- ── 답변 (멤버×책×질문 1행) ───────────────────────────────────────────────
create table if not exists answer (
  id         uuid primary key default gen_random_uuid(),
  book_id    uuid not null references book(id) on delete cascade,
  phone4     text not null,
  q_index    int  not null,
  body       text not null default '',
  updated_at timestamptz not null default now(),
  unique (book_id, phone4, q_index)
);
create index if not exists answer_book_idx on answer(book_id);

-- ── 댓글 (어떤 사람의 답변에 달리는 댓글) ─────────────────────────────────
create table if not exists comment (
  id            uuid primary key default gen_random_uuid(),
  book_id       uuid not null references book(id) on delete cascade,
  q_index       int  not null,
  target_phone4 text not null,   -- 댓글이 달린 답변의 주인
  author_phone4 text not null,
  author_nick   text not null,
  body          text not null,
  created_at    timestamptz not null default now()
);
create index if not exists comment_book_idx on comment(book_id, q_index);

-- ── RLS (v1 데모: anon 허용. phone4 는 인증 아님) ─────────────────────────
alter table meeting     enable row level security;
alter table book        enable row level security;
alter table member_book enable row level security;
alter table answer      enable row level security;
alter table comment     enable row level security;

do $$
declare t text;
begin
  foreach t in array array['meeting','book','member_book','answer','comment'] loop
    execute format('drop policy if exists %1$s_rw on %1$s', t);
    execute format(
      'create policy %1$s_rw on %1$s for all to anon, authenticated using (true) with check (true)', t);
  end loop;
end $$;

-- ════════════════════════════════════════════════════════════════════════
-- SEED — 기본 시즌 "인간 본성 탐구" (데모 모임: 코드 HUMAN-Q2 / 비번 1234)
-- ════════════════════════════════════════════════════════════════════════
insert into meeting (id, name, code, password, season_title, season_sub) values
  ('00000000-0000-0000-0000-0000000000a1',
   '사내 독서모임 · 인간 본성 탐구','HUMAN-Q2','1234','인간 본성 탐구','나 → 연결 → 관계의 그늘')
on conflict (code) do nothing;

insert into book (id, meeting_id, ord, title, author, intro, questions) values
  ('00000000-0000-0000-0000-0000000000b1','00000000-0000-0000-0000-0000000000a1',1,
   '이향인','라미 카민스키',
   '열다섯에 한국을 떠나 다섯 나라를 거친 저자가 "어디에도 온전히 속하지 못하는 사람"의 자리에서 길어 올린 심리·에세이.',
   '["가장 마음에 남은 문장은? 왜 그 문장이 와닿았나요?","이방인이 된 경험이 있나요? 그때 무엇을 느꼈나요?","이 책을 읽고 바꾸고 싶은 생각이나 행동이 있나요?"]'::jsonb),
  ('00000000-0000-0000-0000-0000000000b2','00000000-0000-0000-0000-0000000000a1',2,
   '프로젝트 헤일메리','앤디 위어',
   '혼자 깨어난 우주선, 기억을 잃은 과학자, 그리고 인류의 마지막 임무. 전혀 다른 존재와 손잡는 "연결"의 SF.',
   '["가장 인상 깊었던 \"연결\"의 순간은?","낯선 존재를 신뢰하기까지, 나라면?","이타심은 어디까지 가능할까요?"]'::jsonb),
  ('00000000-0000-0000-0000-0000000000b3','00000000-0000-0000-0000-0000000000a1',3,
   '다크 심리학','(저자 미확정)',
   '타인의 조종·자기보호·관계의 그늘을 다루는 실용 심리. 8월 도서는 진행 결과를 보고 확정.',
   '[]'::jsonb)
on conflict (id) do nothing;

-- 이향인 표본 참가자 4인 (발표 모드 데모용)
insert into member_book (book_id, phone4, nickname, submitted, ratings) values
  ('00000000-0000-0000-0000-0000000000b1','9001','꿈꾸는 해파리',true,'{"length":4,"difficulty":5,"fun":3,"novelty":5,"overall":4}'::jsonb),
  ('00000000-0000-0000-0000-0000000000b1','9002','빛나는 알파카',true,'{"length":3,"difficulty":4,"fun":2,"novelty":5,"overall":3}'::jsonb),
  ('00000000-0000-0000-0000-0000000000b1','9003','배고픈 판다',true,'{"length":2,"difficulty":3,"fun":5,"novelty":3,"overall":3}'::jsonb),
  ('00000000-0000-0000-0000-0000000000b1','9004','용감한 두부',true,'{"length":5,"difficulty":4,"fun":4,"novelty":4,"overall":4}'::jsonb)
on conflict (book_id, phone4) do nothing;

insert into answer (book_id, phone4, q_index, body) values
  ('00000000-0000-0000-0000-0000000000b1','9001',0,'처음 외국에 갔을 때, 아무것도 아닌 사람이 된 느낌이었어요. 그런데 그게 자유였다는 걸 나중에야 알았죠.'),
  ('00000000-0000-0000-0000-0000000000b1','9001',1,'전학을 자주 다녀서 어느 교실에서도 늘 새 사람이었어요. 관찰자가 되는 법을 일찍 배웠죠.'),
  ('00000000-0000-0000-0000-0000000000b1','9001',2,'억지로 섞이려는 노력을 줄이려고요. 거리감을 결핍이 아니라 시야로 보기로.'),
  ('00000000-0000-0000-0000-0000000000b1','9002',0,'이방인이 아닌 사람이 있을까요? 우리는 모두 어딘가에서는 이방인이에요.'),
  ('00000000-0000-0000-0000-0000000000b1','9002',1,'타지에서 명절을 혼자 보낸 적이 있어요. 외로움이 아니라 묘한 해방감이 들어 스스로 놀랐어요.'),
  ('00000000-0000-0000-0000-0000000000b1','9002',2,'내가 어디 ''소속''인지로 나를 설명하던 습관을 바꾸고 싶어요.'),
  ('00000000-0000-0000-0000-0000000000b1','9003',0,'저는 회사에서도 이방인이고 집에서도 이방인이에요. 냉장고 앞에서만 소속감을 느낍니다 ㅋㅋ'),
  ('00000000-0000-0000-0000-0000000000b1','9003',1,'이직 첫 주, 회의에서 다들 웃는 농담을 나만 못 알아들었을 때요.'),
  ('00000000-0000-0000-0000-0000000000b1','9003',2,'남의 무리를 부러워하는 시간을 줄이고 내 리듬을 지키기.'),
  ('00000000-0000-0000-0000-0000000000b1','9004',0,'소속감을 버리니까 오히려 진짜 연결이 생기더라고요. 역설적이지만요.'),
  ('00000000-0000-0000-0000-0000000000b1','9004',1,'군대에서요. 거기선 한동안 모두가 이방인이잖아요.'),
  ('00000000-0000-0000-0000-0000000000b1','9004',2,'혼자인 시간을 결핍이 아니라 회복으로 부르기로 했어요.')
on conflict (book_id, phone4, q_index) do nothing;

insert into comment (book_id, q_index, target_phone4, author_phone4, author_nick, body) values
  ('00000000-0000-0000-0000-0000000000b1',0,'9001','9003','배고픈 판다','그 자유, 저도 뒤늦게 알았어요'),
  ('00000000-0000-0000-0000-0000000000b1',0,'9003','9004','용감한 두부','냉장고 소속감 ㅋㅋ 너무 공감'),
  ('00000000-0000-0000-0000-0000000000b1',1,'9002','9001','꿈꾸는 해파리','그 해방감, 어떤 순간이었는지 더 듣고 싶어요')
on conflict do nothing;

-- 끝. (Realtime 이 필요하면 Dashboard → Database → Replication 에서
--  answer·comment·member_book 테이블을 publication 에 추가)
