-- ════════════════════════════════════════════════════════════════════════
-- v17 — 모임원 발표자료(material) 공유 (2026-07-21)
--
-- 배경: 모임에서 각자 발표한 자료(슬라이드·노션·영상 등)를 서로 볼 수 있는
--   자리가 없었다. 1단계는 "링크"만 — 사내 자료는 대부분 링크로 충분.
--   파일 업로드(Supabase Storage)는 실수요 확인 후 2단계로.
--
-- 설계:
--   - book 단위 부착 (answer/comment/reaction 과 동일 스코프 문법,
--     book 삭제 시 cascade 로 함께 정리)
--   - phone4 텍스트 식별 유지 ('host' = 모임장. member 테이블 도입 시 함께 이관)
--   - 마감(closed) 후에도 등록 가능 — 발표자료는 보통 모임 당일·직후에 올라옴
--   - RLS 는 회원 셀프서비스 등급(answer/comment 와 동일 신뢰 모델):
--     select/insert/delete 개방, update 없음(수정 = 삭제 후 재등록)
--   - 새 테이블은 Supabase 기본 default privileges 로 테이블 단위 grant 가
--     자동 부여됨 (v16 의 컬럼 단위 grant 주의사항은 club/meeting 한정)
-- ════════════════════════════════════════════════════════════════════════

create table if not exists material (
  id         uuid primary key default gen_random_uuid(),
  book_id    uuid not null references book(id) on delete cascade,
  phone4     text not null check (phone4 ~ '^[0-9]{4}$' or phone4 = 'host'),
  title      text not null check (char_length(title) between 1 and 200),
  url        text not null check (char_length(url) between 1 and 2000),
  created_at timestamptz not null default now()
);

create index if not exists material_book_idx on material(book_id, created_at);

alter table material enable row level security;
drop policy if exists material_select on material;
drop policy if exists material_insert on material;
drop policy if exists material_delete on material;
create policy material_select on material for select to anon, authenticated using (true);
create policy material_insert on material for insert to anon, authenticated with check (true);
create policy material_delete on material for delete to anon, authenticated using (true);
