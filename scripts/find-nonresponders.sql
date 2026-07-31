-- ════════════════════════════════════════════════════════════════════════
-- 미답변자 색출 — 특정 책에 답변을 안 단 사람의 phone4(뒷번호) 추출
-- Supabase Dashboard → SQL Editor 에 붙여넣고 Run.
-- 책 제목만 바꾸면 다른 책에도 그대로 쓸 수 있다.
-- ════════════════════════════════════════════════════════════════════════

with tgt as (                                     -- 대상 책 1권
  select b.id, b.season_id, jsonb_array_length(b.questions) as nq
    from book b
   where b.title = '프로젝트 헤일메리'
   order by b.created_at desc
   limit 1
),
roster as (                                       -- 명부 = 같은 시즌 참여자 ∪ 클럽 멤버
  select mb.phone4
    from member_book mb
    join book b on b.id = mb.book_id
    join tgt    on tgt.season_id = b.season_id
  union
  select m.phone4
    from member m
    join season s on s.club_id = m.club_id
    join tgt      on tgt.season_id = s.id
),
nick as (                                         -- 가장 최근에 쓴 닉네임
  select distinct on (mb.phone4) mb.phone4, mb.nickname
    from member_book mb
    join book b on b.id = mb.book_id
    join tgt    on tgt.season_id = b.season_id
   order by mb.phone4, mb.updated_at desc
),
done as (                                         -- 대상 책 실답변 수 (공백 본문 제외)
  select a.phone4, count(*) filter (where btrim(a.body) <> '') as answered
    from answer a
    join tgt on a.book_id = tgt.id
   group by a.phone4
)
select r.phone4                                   as "뒷번호",
       n.nickname                                 as "닉네임",
       coalesce(d.answered, 0) || '/' || t.nq     as "답변",
       coalesce(mbt.submitted, false)             as "제출",
       case when coalesce(d.answered, 0) = 0 then '미답변'
            when d.answered < t.nq            then '부분'
            else '완답' end                       as "상태"
  from roster r
  cross join tgt t
  left join nick n   on n.phone4 = r.phone4
  left join done d   on d.phone4 = r.phone4
  left join member_book mbt on mbt.phone4 = r.phone4 and mbt.book_id = t.id
 where coalesce(d.answered, 0) < t.nq             -- ← 완답자 제외
 order by coalesce(d.answered, 0), r.phone4;

-- ── 변형 1: 명부를 "직전 책 실제 참여자" 로 좁히기 (유령 계정 제외) ──────
--   roster CTE 를 아래로 교체:
--
--   roster as (
--     select distinct a.phone4
--       from answer a
--       join book b on b.id = a.book_id
--       join tgt    on tgt.season_id = b.season_id and b.id <> tgt.id
--      where btrim(a.body) <> ''
--   )

-- ── 변형 2: 누가 어떤 질문을 빼먹었는지까지 ─────────────────────────────
--   select r.phone4, g.q
--     from roster r
--     cross join tgt t
--     cross join lateral generate_series(0, t.nq - 1) as g(q)
--    where not exists (
--      select 1 from answer a
--       where a.book_id = t.id and a.phone4 = r.phone4
--         and a.q_index = g.q and btrim(a.body) <> '')
--    order by r.phone4, g.q;
