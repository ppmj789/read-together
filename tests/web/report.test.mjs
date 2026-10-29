/* 발표자료 2026-07-31 개편 — PPT 슬라이드 요약 · 답변 기준 반응 · 기준 라벨
   하이라이트 · 로드맵 실제 표지. 오프라인 경로로 실제 렌더 코드 구동 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app } from './harness.mjs';

async function withReport(a, rep) {
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  const b = a.w.bookById('ihyangin');
  b.report = Object.assign({
    source: 'test', generated_at: '2026-07-31T00:00:00Z',
    keywords: [{ w: '테스트', size: 'md' }],
    ratings: { length: { avg: 3, n: 1 }, difficulty: { avg: 3, n: 1 }, fun: { avg: 3, n: 1 }, novelty: { avg: 3, n: 1 }, overall: { avg: 3, n: 1 } },
    stats: { answers: 1, comments: 0, reactions: 0, participants: 1 },
    summary: '폴백 요약',
  }, rep);
  b.closed = true;
  return b;
}

test('summary_slides 가 있으면 발표 결과에 PPT 슬라이드 카드로 렌더', async (t) => {
  const a = app(t);
  await withReport(a, { summary_slides: [
    { icon: '🚀', t: '전원 호평', b: '한 줄 정서', hero: true },
    { icon: '🤝', t: '우정', b: '로키 이야기' }] });
  a.w.go('results');
  const slides = a.d.querySelectorAll('#page-results .sum-slide');
  assert.equal(slides.length, 2);
  assert.ok(slides[0].className.includes('sum-slide--hero'), '첫 장은 hero');
  assert.doesNotMatch(a.d.getElementById('page-results').textContent, /폴백 요약/, '슬라이드가 있으면 문단 요약은 안 그림');
});

test('summary_slides 가 없으면 기존 문단 요약 폴백', async (t) => {
  const a = app(t);
  await withReport(a, {});
  a.w.go('results');
  assert.equal(a.d.querySelectorAll('#page-results .sum-slide').length, 0);
  assert.match(a.d.getElementById('page-results').textContent, /폴백 요약/);
});

test('[AI 분석] 탭에서도 슬라이드가 문단 요약을 대체한다', async (t) => {
  const a = app(t);
  await withReport(a, { summary_slides: [{ t: '제목', b: '본문', hero: true }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.renderStageRating();
  const sm = a.d.querySelector('#scene-analysis .analysis-summary');
  assert.ok(sm.className.includes('analysis-summary--slides'));
  assert.equal(sm.querySelectorAll('.sum-slide').length, 1);
});

test('reactions.by_answer 가 있으면 답변 기준으로 렌더 (종류별 막대 없이)', async (t) => {
  const a = app(t);
  await withReport(a, { reactions: {
    total: 3, by_kind: { empathy: 2, differ: 1 }, top: [],
    by_answer: [{ q_index: 3, nick: '별을 헤는 항해자', quote: '로키네 가서 살 거예요', counts: { empathy: 2, differ: 1 }, total: 3 }] } });
  a.w.go('results');
  assert.equal(a.d.querySelectorAll('#page-results .rxa').length, 1);
  const txt = a.d.getElementById('page-results').textContent;
  assert.match(txt, /별을 헤는 항해자/);
  assert.match(txt, /Q4/, '질문 번호 뱃지');
  assert.equal(a.d.querySelectorAll('#page-results .rx-row').length, 0, 'by_answer 있으면 분포 막대는 안 그림');
});

test('highlights 객체형은 선정 기준 라벨이 함께 렌더 (구형 문자열 하위호환)', async (t) => {
  const a = app(t);
  await withReport(a, { highlights: [
    { label: '🙌 공감 최다 답변 (2표)', q: 'Q4. 결말을 바꾼다면?', body: '→ 지구 귀환파가 다수였습니다.' },
    'Q1. 구형 문자열\n→ 하위호환도 렌더'] });
  a.w.go('results');
  const txt = a.d.getElementById('page-results').textContent;
  assert.match(txt, /공감 최다 답변 \(2표\)/);
  assert.match(txt, /지구 귀환파가 다수였습니다/);
  assert.match(txt, /구형 문자열/);
});

test('키워드 클릭 → 아래 고정 패널에 선정 이유, 다른 키워드 클릭 → 교체', async (t) => {
  const a = app(t);
  await withReport(a, { keywords: [
    { w: '로키', size: 'lg', why: '최애 캐릭터', q: '로키 같은 친구' },
    { w: '우정', size: 'md', why: '전원 호응', q: '유니버셜 우정' }] });
  a.w.go('results');
  const kws = [...a.d.querySelectorAll('#res-kws .kw')];
  const detail = a.d.getElementById('res-kw-detail');
  assert.ok(!detail.className.includes('show'), '클릭 전엔 숨김');
  kws[0].click();
  assert.ok(detail.className.includes('show'));
  assert.match(detail.textContent, /최애 캐릭터/);
  kws[1].click();
  assert.match(detail.textContent, /전원 호응/, '다른 키워드를 누르면 교체');
  assert.doesNotMatch(detail.textContent, /최애 캐릭터/);
});

test('멤버 추리 씬 — member_profiles 카드 렌더 (없으면 안내)', async (t) => {
  const a = app(t);
  await withReport(a, { member_profiles: [
    { nick: '타오르는 로켓', title: '감동 담당', desc: '다섯 번 울었다', quote: '울었습니다' }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.renderStageMembers();
  const cards = a.d.querySelectorAll('#stage-members-grid .member-card');
  assert.equal(cards.length, 1);
  assert.match(cards[0].textContent, /감동 담당/);
});

test('ratings_comment 는 별점 아래 요약으로, 본문 속 닉네임은 <i.nick> 강조', async (t) => {
  const a = app(t);
  await withReport(a, {
    ratings_comment: '참신함이 가장 높았습니다.',
    member_profiles: [{ nick: '타오르는 로켓', desc: 'x' }],
    summary_slides: [{ t: '제목', b: '타오르는 로켓은 감동 담당입니다.', hero: true }] });
  a.w.go('results');
  const txt = a.d.getElementById('page-results').textContent;
  assert.match(txt, /참신함이 가장 높았습니다/);
  assert.ok(a.d.querySelector('#page-results .sum-slide__b .nick'), '슬라이드 본문 닉네임 이탤릭 강조');
  assert.ok(a.d.querySelector('#page-results .member-card'), '발표 결과에도 멤버 프로필 카드');
});

test('발표모드 하이라이트 씬 — report 하이라이트가 정본, 선정 이유가 큰 제목', async (t) => {
  const a = app(t);
  await withReport(a, { highlights: [
    { label: '🙌 유일하게 공감 2표를 모은 답변', q: 'Q4. 결말을 바꾼다면?', body: '→ 귀환파 다수.' }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.renderStageHighlights();
  const crit = a.d.querySelector('#stage-highlights-grid .highlight-card__crit');
  assert.ok(crit, '선정 이유 제목 요소');
  assert.match(crit.textContent, /공감 2표를 모은 답변/);
});

test('발표모드 카드 클릭 → 확대 오버레이, 다시 클릭하면 닫힘', async (t) => {
  const a = app(t);
  await withReport(a, { member_profiles: [
    { nick: '타오르는 로켓', title: '감동 담당', desc: '다섯 번 울었다' }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('members');
  const card = a.d.querySelector('#stage-members-grid .member-card');
  card.click();
  const ov = a.d.getElementById('zoom-ov');
  assert.ok(ov && ov.className.includes('show'), '카드 클릭 시 오버레이 표시');
  assert.match(a.d.getElementById('zoom-ov-inner').textContent, /감동 담당/);
  ov.click();
  assert.ok(!ov.className.includes('show'), '오버레이 클릭으로 닫힘');
});

test('무리 모션 — 질문별 그룹 존과 조약돌이 뜨고, 질문을 바꾸면 같은 조약돌이 이동한다', async (t) => {
  const a = app(t);
  await withReport(a, { question_groups: [
    { q_index: 0, groups: [
      { emoji: '🏃', name: '일단 도망', members: ['타오르는 로켓', '꿈꾸는 표류자'] },
      { emoji: '💬', name: '말 걸어본다', members: ['되돌아오지 않는 일식'] }] },
    { q_index: 1, groups: [
      { emoji: '💖', name: '응원파', members: ['타오르는 로켓', '되돌아오지 않는 일식', '꿈꾸는 표류자'] }] }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.STAGE.q = 0;
  a.w.renderStageGroups();
  await new Promise((r) => setTimeout(r, 60));
  const host = a.d.getElementById('sl-groups');
  assert.equal(host.style.display, 'block');
  assert.equal(host.querySelectorAll('.grp-zone').length, 2, '무리 2개');
  const pebs = host.querySelectorAll('.grp-peb');
  assert.equal(pebs.length, 3, '조약돌 3개');
  const before = pebs[0].style.left;
  a.w.STAGE.q = 1;
  a.w.renderStageGroups();
  await new Promise((r) => setTimeout(r, 60));
  assert.equal(host.querySelectorAll('.grp-peb').length, 3, '조약돌 DOM 재사용(이동 애니메이션)');
  assert.equal(host.querySelectorAll('.grp-zone').length, 1, '무리 1개로 재편');
  assert.notEqual(pebs[0].style.left, before, '위치가 바뀌어 transition 이동');
});

test('조약돌끼리 겹치지 않게 밀어낸다 (같은 무리 3명)', async (t) => {
  const a = app(t);
  await withReport(a, { question_groups: [
    { q_index: 0, groups: [
      { name: '한 무리', members: ['타오르는 로켓', '꿈꾸는 표류자', '되돌아오지 않는 일식'] }] }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.STAGE.q = 0;
  a.w.renderStageGroups();
  await new Promise((r) => setTimeout(r, 60));
  const pos = [...a.d.querySelectorAll('#sl-groups .grp-peb')].map((p) => ({
    x: parseFloat(p.style.left), y: parseFloat(p.style.top) }));
  assert.equal(pos.length, 3);
  for (let i = 0; i < pos.length; i++) for (let j = i + 1; j < pos.length; j++) {
    const overlap = Math.abs(pos[i].x - pos[j].x) < 98 && Math.abs(pos[i].y - pos[j].y) < 32;
    assert.ok(!overlap, `조약돌 ${i}·${j} 가 겹치면 안 됨 (${JSON.stringify(pos)})`);
  }
});

test('키워드 카드 확대 상태에서 키워드를 눌러도 닫히지 않고 클론 패널에 이유가 뜬다', async (t) => {
  const a = app(t);
  await withReport(a, { keywords: [{ w: '로키', size: 'lg', why: '최애 캐릭터', q: '로키 같은 친구' }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('analysis');
  const label = a.d.querySelector('#scene-analysis .analysis-card .analysis-card__label');
  label.click(); /* 카드 본문 클릭 → 확대 */
  const ov = a.d.getElementById('zoom-ov');
  assert.ok(ov.className.includes('show'));
  const kw = ov.querySelector('.kw');
  kw.click();
  assert.ok(ov.className.includes('show'), '키워드 클릭으로는 닫히지 않는다');
  assert.match(ov.querySelector('.kw-detail').textContent, /최애 캐릭터/, '클론 패널에 이유 표시');
  ov.click();
  assert.ok(!ov.className.includes('show'), '바깥 클릭으로는 닫힌다');
});

test('AI 요약 슬라이드 확대 상태에서 ‹ › 로 좌우 넘기기', async (t) => {
  const a = app(t);
  await withReport(a, { summary_slides: [
    { t: '첫 장', b: '하나', hero: true },
    { t: '둘째 장', b: '둘' },
    { t: '셋째 장', b: '셋' }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('analysis');
  a.d.querySelectorAll('#scene-analysis .sum-slide')[0].click();
  const ov = a.d.getElementById('zoom-ov');
  assert.ok(ov.className.includes('show'));
  assert.equal(a.d.getElementById('zoom-ov-cnt').textContent, '1 / 3');
  a.w.zoomNav(1);
  assert.match(a.d.getElementById('zoom-ov-inner').textContent, /둘째 장/);
  assert.equal(a.d.getElementById('zoom-ov-cnt').textContent, '2 / 3');
  a.w.zoomNav(-1);
  a.w.zoomNav(-1);
  assert.match(a.d.getElementById('zoom-ov-inner').textContent, /셋째 장/, '끝에서 순환');
  assert.ok(ov.className.includes('show'), '넘기는 동안 확대 유지');
});

test('진행탭 — 발언자 뽑기가 질문선택 오른쪽 상단바에 있고 왼쪽 패널은 없다', async (t) => {
  const a = app(t);
  await withReport(a, {});
  a.w.showStageScene('live');
  assert.equal(a.d.querySelector('#scene-live .scene-live__left'), null, '왼쪽 패널 제거');
  const bar = a.d.querySelector('#scene-live .sl-topbar .sl-pickbar');
  assert.ok(bar, '뽑기 바가 상단바 오른쪽에');
  assert.match(bar.textContent, /답변 다 보기/);
  assert.doesNotMatch(bar.textContent, /무작위/, '무작위 뽑기는 없앴다 (2026-09-30)');
  assert.ok(a.d.getElementById('stage-speaker-name'), '발언자 이름 표시는 유지');
  assert.equal(a.d.getElementById('sl-order'), null, '발언 순서 목록은 없앴다 (2026-09-30)');
});

test('조약돌 클릭 → 그 사람이 발언자로 지목되고 강조된다', async (t) => {
  const a = app(t);
  await withReport(a, { question_groups: [
    { q_index: 0, groups: [{ name: 'A', members: ['타오르는 로켓', '꿈꾸는 표류자'] }] }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.STAGE.q = 0;
  a.w.renderStageGroups();
  await new Promise((r) => setTimeout(r, 50));
  const peb = [...a.d.querySelectorAll('#sl-groups .grp-peb')]
    .find((p) => p.textContent.includes('타오르는 로켓'));
  peb.click();
  assert.equal(a.w.STAGE.pickedName, '타오르는 로켓');
  assert.equal(a.d.getElementById('stage-speaker-name').textContent, '타오르는 로켓');
  assert.ok(peb.className.includes('is-picked'), '지목된 조약돌 강조');
});

test('무리 데이터가 없는 질문에서는 무리 영역을 숨긴다', async (t) => {
  const a = app(t);
  await withReport(a, { question_groups: [
    { q_index: 0, groups: [{ name: 'A', members: ['타오르는 로켓'] }] }] });
  a.w.STAGE.bookId = 'ihyangin';
  a.w.STAGE.q = 2;
  a.w.renderStageGroups();
  assert.equal(a.d.getElementById('sl-groups').style.display, 'none');
});

test('로드맵 카드에 표지 맵의 실제 표지 이미지가 뜬다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.STAGE.bookId = 'ihyangin';
  a.w.renderStageRoadmap();
  assert.ok(a.d.querySelectorAll('#stage-roadmap .sr-book__cover').length >= 1,
    'coverFor 맵에 있는 책은 책등 글자 대신 표지 이미지');
});

/* 발표모드 진행탭 답변·댓글은 줄바꿈을 보존한다 (2026-09-04) */
test('발표모드 진행탭: 답변 본문과 댓글이 pre-line 으로 줄바꿈을 살린다', async (t) => {
  const a = app(t);
  const css = [...a.d.querySelectorAll('style')].map((s) => s.textContent).join('');
  assert.match(css, /\.sl-pick-card__ans\{[^}]*white-space:pre-line/);
  assert.match(css, /\.sl-cmt\{[^}]*white-space:pre-line/);
});

test('지정 발언자 — report.speaker_picks 의 그 질문 지정자가 뽑힌다', async (t) => {
  const a = app(t);
  const b = await withReport(a, { speaker_picks: [
    { q_index: 0, nick: '꿈꾸는 표류자' }, { q_index: 1, nick: '타오르는 로켓', why: '반응 최다' }] });
  b.others = b.questions.map(() => [{ n: '꿈꾸는 표류자', a: '답' }, { n: '타오르는 로켓', a: '답' }]);
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('live');
  a.w.STAGE.q = 1;
  a.w.stagePick({ type: 'assigned' });
  await new Promise((r) => setTimeout(r, 1200));
  assert.equal(a.w.STAGE.pickedName, '타오르는 로켓');
  assert.equal(a.w.STAGE.critText, '지정 발언자');
  assert.match(a.d.getElementById('sl-pickcard').textContent, /지정 이유 · 반응 최다/, '지정 이유 표시');
});

test('지정 발언자가 없는 질문이면 아무도 뽑지 않는다', async (t) => {
  const a = app(t);
  const b = await withReport(a, { speaker_picks: [{ q_index: 0, nick: '꿈꾸는 표류자' }] });
  b.others = b.questions.map(() => [{ n: '꿈꾸는 표류자', a: '답' }]);
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('live');
  a.w.STAGE.q = 2;
  a.w.stagePick({ type: 'assigned' });
  await new Promise((r) => setTimeout(r, 1200));
  assert.equal(a.w.STAGE.pickedName, null);
});

test('답변 보드 — 발언자가 없으면 그 질문의 답변이 전부 카드로 보이고, 누르면 그 사람이 발언자', async (t) => {
  const a = app(t);
  const b = await withReport(a, {});
  b.others = b.questions.map((_, qi) => [{ n: '꿈꾸는 표류자', a: 'Q' + qi + ' 표류자 답' }, { n: '타오르는 로켓', a: 'Q' + qi + ' 로켓 답' }]);
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('live');
  b.reactions = { q1a1: { counts: { insight: 3, empathy: 1 }, mine: {}, total: 4 } };
  a.w.stageSetQ(1);
  const cards = a.d.querySelectorAll('#sl-pickcard .sl-board__card');
  assert.match(cards[1].textContent, /반응 4/, '종류별 반응 합계');
  assert.equal(cards.length, 2, '답변자 전원 카드');
  assert.match(cards[1].textContent, /Q1 로켓 답/);
  cards[1].click();
  assert.equal(a.w.STAGE.pickedName, '타오르는 로켓');
  assert.equal(a.w.STAGE.critText, '다 같이 고른 발언자');
  assert.ok(a.d.querySelector('#sl-pickcard .sl-pick-card'), '답변 카드로 전환');
  a.d.querySelector('#sl-pickcard .sl-board-back').click();
  assert.equal(a.w.STAGE.pickedName, null);
  assert.equal(a.d.querySelectorAll('#sl-pickcard .sl-board__card').length, 2, '다시 보드로');
});

test('지정 발언자 버튼은 speaker_picks 가 있는 책에서만 보인다', async (t) => {
  const a = app(t);
  const b = await withReport(a, {});
  b.others = b.questions.map(() => [{ n: '꿈꾸는 표류자', a: '답' }]);
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('live');
  a.w.renderStageLive();
  assert.equal(a.d.getElementById('sl-assigned-btn').style.display, 'none');
  b.report.speaker_picks = [{ q_index: 0, nick: '꿈꾸는 표류자' }];
  a.w.renderStageLive();
  assert.equal(a.d.getElementById('sl-assigned-btn').style.display, '');
});

test('반 별 입력 — 왼쪽 절반을 누르면 0.5점으로 저장되고 반 별로 그려진다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  a.w.setDiscView('rating');
  const hit = a.d.querySelector('.rating-row .star__hit--l[aria-label$=" 3.5점"]');
  assert.ok(hit, '4번째 별 왼쪽 절반 = 3.5점');
  hit.click();
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(a.w.bookState('ihyangin').ratings.length, 3.5);
  const row = a.d.querySelector('.rating-row');
  assert.equal(row.querySelectorAll('.star.on').length, 3);
  assert.equal(row.querySelectorAll('.star.half').length, 1);
  assert.match(row.textContent, /3\.5/);
});

test('별점 — 축마다 몇 점에 몇 명인지 점(한 사람 = 하나)으로, 별점 카드 하나에만', async (t) => {
  const a = app(t);
  const b = await withReport(a, {});
  b.allRatings = [
    { phone4: '9876', length: 5, difficulty: 4.5, fun: 4, novelty: 3, overall: 4 },
    { phone4: '8765', length: 5, difficulty: 4, fun: 3.5, novelty: 5, overall: 4 },
    { phone4: '7654', length: 5, difficulty: 0, fun: 4, novelty: 4, overall: 3.5 }];
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('analysis');
  assert.equal(a.d.getElementById('analysis-rating-spread'), null, '키워드 카드의 흩어짐 그래프는 없앴다');
  const axes = a.d.querySelectorAll('#stage-rating-rows .rt-axis');
  assert.equal(axes.length, 5);
  const len = axes[0].querySelectorAll('.rt-cnt__g');
  assert.equal(len.length, 1, '분량은 전원 5점');
  assert.match(len[0].textContent, /5점/);
  assert.equal(len[0].querySelectorAll('.rt-cnt__dot').length, 3, '세 사람 = 점 세 개');
  const diff = [...axes[1].querySelectorAll('.rt-cnt__g')].map((g) => g.textContent);
  assert.deepEqual(diff, ['4.5점', '4점'], '높은 점수부터, 0점(미입력)은 뺀다');
  assert.doesNotMatch(a.d.getElementById('stage-rating-rows').innerHTML, /9876|8765|7654/, '번호는 절대 싣지 않는다(익명)');
});

test('홀랜드 — 검사 결과가 붙은 질문을 고르면 답변 보드 대신 팀 지도가 뜬다', async (t) => {
  const a = app(t);
  const b = await withReport(a, { question_groups: [
    { q_index: 1, groups: [{ name: 'A', members: ['꿈꾸는 표류자'] }] }] });
  const url = (r, i, ar, s, e, c) => 'https://prismatest.com/ko/tests/holland?res=realistic%3A' + r +
    '-investigative%3A' + i + '-artistic%3A' + ar + '-social%3A' + s + '-enterprising%3A' + e + '-conventional%3A' + c;
  b.others = b.questions.map((_, qi) => qi === 1
    ? [{ n: '꿈꾸는 표류자', a: url(100, 50, 40, 60, 20, 100) + '\n\n결과 설명' },
       { n: '타오르는 로켓', a: url(50, 50, 90, 70, 60, 50) },
       { n: '조용한 관찰자', a: '검사 못 했어요' }]
    : [{ n: '꿈꾸는 표류자', a: '답' }, { n: '타오르는 로켓', a: '답' }, { n: '조용한 관찰자', a: '답' }]);
  const hd = a.w.hollandData(b);
  assert.equal(hd.qi, 1);
  assert.equal(hd.people.length, 2, '주소 없는 답변은 빠진다');
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('live');
  assert.equal(a.d.getElementById('stage-holland'), null, '다른 질문엔 지도 없음');
  a.w.stageSetQ(1);
  const host = a.d.getElementById('stage-holland');
  assert.ok(host, 'Q2 아래에 지도');
  assert.equal(a.d.querySelectorAll('#sl-pickcard .sl-board__card').length, 0, '링크뿐인 답변 카드는 안 보인다');
  assert.equal(a.d.getElementById('sl-groups').style.display, 'none', '무리 지도도 숨김');
  assert.ok(host.querySelector('svg polygon'), '레이더');
  const rows = [...host.querySelectorAll('.hol-type')];
  assert.match(rows[0].textContent, /실재형 75/, '팀 평균');
  assert.match(rows[0].textContent, /꿈꾸는 표류자/, '공동 1위도 들어간다');
  assert.match(rows[5].textContent, /꿈꾸는 표류자/);
  assert.match(rows[2].textContent, /타오르는 로켓/);
  assert.match(host.textContent, /만점 100점/);
  host.querySelector('.hol-who button[data-n="타오르는 로켓"]').click();
  assert.equal(a.d.querySelectorAll('#stage-holland svg polygon[stroke="#E07A3F"]').length, 1, '고른 사람 육각형이 겹쳐진다');
});

test('홀랜드는 별도 탭이 아니다', async (t) => {
  const a = app(t);
  await withReport(a, {});
  assert.equal(a.d.querySelector('#top-nav a[data-scene="holland"]'), null);
});

test('진행탭 답변 카드 오른쪽 위 👀 → 이름표 이름(없으면 번호 뒷자리)이 화면 가운데에 뾱, 발언자 선택은 안 된다', async (t) => {
  const a = app(t);
  const b = await withReport(a, { member_profiles: [{ nick: '꿈꾸는 표류자', title: 'A', desc: '한 문장.' }] });
  b.others = b.questions.map(() => [{ n: '꿈꾸는 표류자', a: '답', phone4: '1111' }, { n: '타오르는 로켓', a: '답', phone4: '2222' }]);
  a.w.STAGE.bookId = 'ihyangin';
  a.w.showStageScene('members');
  assert.equal(a.d.querySelector('#scene-members .nm-eye'), null, '멤버 추리 탭엔 이름 보기 없음');
  a.w.showStageScene('live');
  a.w.stageSetQ(0);
  assert.doesNotMatch(a.d.getElementById('sl-pickcard').textContent, /1111|2222/, '누르기 전엔 안 보인다');
  a.d.getElementById('nm-paste-ta').value = '1111 홍길동 / 3333 다른사람(오늘 불참)';
  a.w.nameTagSave();
  assert.deepEqual(JSON.parse(a.w.localStorage.getItem('rt:names')), { 1111: '홍길동', 3333: '다른사람(오늘 불참)' });
  a.d.querySelector('.sl-board__card[data-nick="꿈꾸는 표류자"] .nm-eye').click();
  assert.equal(a.w.STAGE.pickedName, null, '👀 는 발언자 선택과 별개');
  assert.ok(a.d.getElementById('nm-pop').className.includes('show'));
  assert.equal(a.d.getElementById('nm-pop-name').textContent, '홍길동');
  assert.match(a.d.querySelector('.sl-board__card[data-nick="꿈꾸는 표류자"]').textContent, /홍길동/, '닫아도 카드에 남는다');
  a.w.namePopClose();
  a.d.querySelector('.sl-board__card[data-nick="타오르는 로켓"] .nm-eye').click();
  assert.equal(a.d.getElementById('nm-pop-name').textContent, '뒷자리 2222', '이름표 없으면 번호');
  a.w.namePopClose();
  a.d.querySelector('.sl-board__card[data-nick="타오르는 로켓"]').click();
  assert.equal(a.w.STAGE.pickedName, '타오르는 로켓', '카드 자체를 누르면 여전히 발언자 선택');
});
