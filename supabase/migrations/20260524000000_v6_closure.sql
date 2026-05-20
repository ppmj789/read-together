-- ════════════════════════════════════════════════════════════════════════
-- v6 — 책(=월 1회 모임) 마감 프로세스 + 발표자료(보고서) 영속
--   목적:
--     1) 책 단위 마감 — closed_at 가 not null 이면 그 책은 잠김
--        (답변/별점/댓글/공감 입력은 클라이언트 가드. RLS는 v1 데모 정책 유지)
--     2) 발표자료(보고서) 1회 생성·영속 — report jsonb
--        report 스키마(샘플): {
--          "source":"mock|openai|...",
--          "generated_at":"2026-05-20T12:00:00Z",
--          "keywords":[{"w":"이방인","size":"lg"}, ...],
--          "ratings":{"length":{"avg":3.5,"n":5}, ...},
--          "summary":"…",
--          "stats":{"answers":12,"comments":4,"participants":5}
--        }
--   외부 AI 연동은 후속 PR — 본 마이그레이션은 데이터 자리만 확보.
--   idempotent: 컬럼 추가는 if not exists.
-- ════════════════════════════════════════════════════════════════════════

alter table book add column if not exists closed_at timestamptz;
alter table book add column if not exists report    jsonb;

create index if not exists book_closed_idx on book(closed_at);
