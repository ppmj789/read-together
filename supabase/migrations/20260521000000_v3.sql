-- ════════════════════════════════════════════════════════════════════════
-- untoldChapter v3 — 풍부한 사전정보(재미있는 사실 · 같이 볼 콘텐츠)
-- (기존 마이그레이션 수정 금지, 새 파일로 추가. idempotent)
-- ════════════════════════════════════════════════════════════════════════

alter table book add column if not exists author_facts jsonb not null default '[]'::jsonb; -- [{e,t,s}]
alter table book add column if not exists links        jsonb not null default '[]'::jsonb; -- [{i,t,m}]

-- ── 이향인 (라미 카민스키 · 21세기북스 2026 · 원제 THE GIFT OF NOT BELONGING)
update book set
  intro='내향인도 외향인도 아닌 제3의 유형 ''이향인(otrovert)''. 사고의 출발점이 ''우리''가 아니라 ''나''인 사람들을 위한, 뉴욕의 정신과 의사 라미 카민스키의 심리 에세이.',
  author_bio='라미 카민스키 — 임상심리학자이자 뉴욕시 통합정신의학연구소 설립자. 40년 넘게 세계 각계 인사 수천 명을 상담해 온 정신과 의사.',
  author_facts='[
    {"e":"🧠","t":"40년+ 임상","s":"세계 지도자·최고 전문가 등 수천 명의 심리를 상담했다"},
    {"e":"🔬","t":"뇌 연구자","s":"1990년대 마운트 시나이에서 퇴행성 뇌질환의 히스타민 역할 등을 발견"},
    {"e":"🏷️","t":"새 이름을 만든 사람","s":"내향/외향이 아닌 제3의 유형 ''이향인''을 제안"}
  ]'::jsonb,
  links='[
    {"i":"📘","t":"교보문고 — 이향인 책 소개","m":"product.kyobobook.co.kr"},
    {"i":"📚","t":"나무위키 — 이향인 정리","m":"namu.wiki"},
    {"i":"▶","t":"21세기북스 소개 영상","m":"youtube.com"}
  ]'::jsonb
  where id='00000000-0000-0000-0000-0000000000b1';

-- ── 프로젝트 헤일메리 (앤디 위어)
update book set
  intro='혼자 깨어난 우주선, 기억을 잃은 과학자, 그리고 인류의 마지막 임무. ''마션''의 앤디 위어가 과학적 디테일로 쌓아 올린 1인칭 생존·우정 SF.',
  author_bio='앤디 위어 — 25년차 소프트웨어 엔지니어 출신 SF 작가. 데뷔작 ''마션''으로 베스트셀러 작가가 됐다.',
  author_facts='[
    {"e":"💻","t":"원래 개발자","s":"마션이 베스트셀러가 된 뒤에도 한동안 프로그래밍 직장을 안 그만뒀다"},
    {"e":"🔭","t":"과학이 먼저","s":"\"내 이야기엔 깊은 메시지는 없다 — 그냥 재미를 위한 것\""},
    {"e":"🎬","t":"영화에도 참여","s":"라이언 고슬링 주연 영화에 프로듀서·과학자문으로 거의 전 촬영 참여"}
  ]'::jsonb,
  links='[
    {"i":"📖","t":"Wikipedia — Project Hail Mary","m":"en.wikipedia.org"},
    {"i":"🎙️","t":"Rolling Stone — Andy Weir 인터뷰","m":"rollingstone.com"},
    {"i":"🔬","t":"Astronomy.com — the science of the book","m":"astronomy.com"}
  ]'::jsonb
  where id='00000000-0000-0000-0000-0000000000b2';
