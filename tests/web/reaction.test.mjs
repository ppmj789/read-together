/* 답변 반응 5종(v22) 동작 테스트 — 오프라인(localStorage) 경로로 실제 코드 구동 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app } from './harness.mjs';

/* 오프라인 시드엔 '남의 답변'이 없어서 직접 한 명 심는다 */
async function othersView(a, bookId = 'ihyangin') {
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook(bookId);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 3);
  const b = a.w.bookById(bookId);
  b.questions.forEach((q, i) => { a.d.getElementById('ans-' + i).value = '내 답변 ' + (i + 1); });
  await a.w.submitAnswers();
  b.others = b.questions.map((q, i) => (i === 0 ? [{ n: '밤새 읽는 독서가', a: '주인공은 끝까지 혼자였어요', phone4: '5555' }] : []));
  a.w.DISC.view = 'others';
  a.w.renderDiscussion();
  return b;
}
const btns = (a) => [...a.d.querySelectorAll('#page-discussion .answer:not(.mine) .reaction-btn')];

test('반응 5종이 모두 버튼으로 뜬다', async (t) => {
  const a = app(t);
  await othersView(a);
  const labels = btns(a).map((x) => x.textContent);
  assert.equal(labels.length, 5);
  for (const r of a.w.REACTIONS) {
    assert.ok(labels.some((l) => l.includes(r.l)), `${r.l} 버튼이 있어야 함`);
  }
});

test('반응을 누르면 내 반응으로 켜지고 카운트가 1', async (t) => {
  const a = app(t);
  await othersView(a);
  await a.w.toggleReact(0, 0, 'differ');
  const rc = a.w.normReact(a.w.bookState('ihyangin').reactions['q0a0']);
  assert.equal(rc.counts.differ, 1);
  assert.equal(rc.mine.differ, true);
  const on = btns(a).filter((x) => x.className.includes('react-on'));
  assert.equal(on.length, 1);
  assert.match(on[0].textContent, /전 다르게 1/);
});

test('여러 종류를 동시에 달 수 있다 (공감 단일 시절과 다름)', async (t) => {
  const a = app(t);
  await othersView(a);
  await a.w.toggleReact(0, 0, 'underline');
  await a.w.toggleReact(0, 0, 'more');
  const rc = a.w.normReact(a.w.bookState('ihyangin').reactions['q0a0']);
  assert.equal(rc.counts.underline, 1);
  assert.equal(rc.counts.more, 1);
  assert.equal(rc.total, 2);
  assert.equal(btns(a).filter((x) => x.className.includes('react-on')).length, 2);
});

test('같은 종류를 다시 누르면 취소된다', async (t) => {
  const a = app(t);
  await othersView(a);
  await a.w.toggleReact(0, 0, 'insight');
  await a.w.toggleReact(0, 0, 'insight');
  const rc = a.w.normReact(a.w.bookState('ihyangin').reactions['q0a0']);
  assert.equal(rc.counts.insight, undefined);
  assert.equal(rc.mine.insight, undefined);
  assert.equal(rc.total, 0);
  assert.equal(btns(a).filter((x) => x.className.includes('react-on')).length, 0);
});

test('레거시 공감 데이터({count,mine})는 🙌 완전 동의로 승계된다', async (t) => {
  const a = app(t);
  await othersView(a);
  const bs = a.w.bookState('ihyangin');
  bs.reactions = { q0a0: { count: 3, mine: true } }; // v21 이전 로컬 상태
  a.w.setBookState('ihyangin', bs);
  a.w.renderDiscussion();
  const rc = a.w.normReact(a.w.bookState('ihyangin').reactions['q0a0']);
  assert.equal(rc.counts.empathy, 3);
  assert.equal(rc.mine.empathy, true);
  const on = btns(a).filter((x) => x.className.includes('react-on'));
  assert.equal(on.length, 1);
  assert.match(on[0].textContent, /완전 동의 3/);
});

test('마감된 책은 버튼 대신 반응 요약만 보인다', async (t) => {
  const a = app(t);
  const b = await othersView(a);
  await a.w.toggleReact(0, 0, 'underline');
  b.closed = true;
  a.w.renderDiscussion();
  assert.equal(btns(a).length, 0);
  assert.match(a.d.getElementById('page-discussion').textContent, /🔖1 · 마감/);
});

test('발표자료(mock)에 반응 종류별 집계가 들어간다', async (t) => {
  const a = app(t);
  await othersView(a);
  await a.w.toggleReact(0, 0, 'underline');
  await a.w.toggleReact(0, 0, 'differ');
  const rep = a.w.generateReportMock(a.w.bookById('ihyangin'));
  assert.equal(rep.reactions.total, 2);
  assert.equal(rep.reactions.by_kind.underline, 1);
  assert.equal(rep.reactions.by_kind.differ, 1);
  assert.equal(rep.stats.reactions, 2);
  const top = rep.reactions.top.find((x) => x.kind === 'differ');
  assert.equal(top.quote, '주인공은 끝까지 혼자였어요', '그 종류를 가장 많이 받은 답변 인용');
  assert.match(rep.summary, /밑줄 1·전 다르게 1/);
});

test('발표 결과 화면에 반응 카드(분포 폴백) + 종류별 최다 인용이 렌더된다', async (t) => {
  const a = app(t);
  const b = await othersView(a);
  await a.w.toggleReact(0, 0, 'more');
  b.report = a.w.generateReportMock(b);
  b.closed = true;
  a.w.go('results');
  const txt = a.d.getElementById('page-results').textContent;
  assert.match(txt, /반응이 몰린 답변/);
  assert.match(txt, /👂 더 듣고 싶어요/);
  assert.match(txt, /더 듣고 싶어요.*최다/);
  assert.match(txt, /반응 1개/, '상단 기록 줄에도 반응 수');
  assert.equal(a.d.querySelectorAll('#page-results .rx-row').length, 1);
});

test('반응이 없는 발표자료는 반응 카드를 아예 안 그린다', async (t) => {
  const a = app(t);
  const b = await othersView(a);
  b.report = a.w.generateReportMock(b);
  b.closed = true;
  a.w.go('results');
  assert.equal(b.report.reactions, null);
  assert.doesNotMatch(a.d.getElementById('page-results').textContent, /반응이 몰린 답변/);
});

test('[AI 분석] 탭에는 반응 카드가 없다 — 반응은 진행탭·발표 결과 담당 (2026-07-31)', async (t) => {
  const a = app(t);
  const b = await othersView(a);
  await a.w.toggleReact(0, 0, 'insight');
  b.report = a.w.generateReportMock(b);
  a.w.STAGE.bookId = 'ihyangin';
  a.w.renderStageRating();
  assert.equal(a.d.getElementById('analysis-rx-card'), null, '분석 탭 반응 카드는 삭제됨');
  assert.equal(a.d.getElementById('analysis-star-pick'), null, '별점으로 발언자 뽑기도 삭제됨');
});
