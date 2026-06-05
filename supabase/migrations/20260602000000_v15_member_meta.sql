-- ════════════════════════════════════════════════════════════════════════
-- v15 — member_book.meta jsonb (책별 부가 데이터 범용 컬럼)
--   책 한 권 전용 컬럼(v14 ihyang_score/ihyang_pct)은 재사용성이 없어
--   범용 meta jsonb 하나로 통합한다. 다른 책의 테스트·부가데이터는
--   meta 의 다른 키로 누적하면 되고, 스키마 변경이 필요 없다.
--
--   meta = {"ihyang": {"score": 188, "pct": 67, "is": true}}
--   (다른 책 예) meta = {"mbti": {"type": "INFP"}}
--
--   분석 시에도 (meta->'ihyang'->>'pct')::int 로 집계·정렬 가능.
--   프론트는 best-effort — meta 컬럼이 없어도(마이그레이션 전) 앱은 동작.
--   idempotent (여러 번 실행해도 안전).
-- ════════════════════════════════════════════════════════════════════════

alter table member_book add column if not exists meta jsonb not null default '{}'::jsonb;

-- v14 전용 컬럼이 남아있으면 meta.ihyang 으로 백필 후 컬럼 제거.
-- 컬럼 존재 여부로 가드 → 마이그레이션 재실행에도 안전.
do $$
begin
  if exists (
    select 1 from information_schema.columns
     where table_name = 'member_book' and column_name = 'ihyang_score'
  ) then
    update member_book
       set meta = jsonb_set(
             coalesce(meta, '{}'::jsonb), '{ihyang}',
             jsonb_build_object(
               'score', ihyang_score,
               'pct',   ihyang_pct,
               'is',    (ihyang_score >= 188)))
     where ihyang_score is not null
       and not (meta ? 'ihyang');

    alter table member_book drop column ihyang_score;
    alter table member_book drop column ihyang_pct;
  end if;
end $$;
