/* 시즌 결산 리포트(v31) — 책장 신문 · 결산 페이지 · 발표 씬. 오프라인 경로로 실제 코드 구동 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app } from './harness.mjs';

const REPORT = {
  source: 'test', generated_at: '2026-09-04T00:00:00Z', eyebrow: 'SEASON 1',
  thesis: '인간에게는 회의적이고, 관계에는 낭만적인 모임',
  books: [{ title: '이향인', author: '라미 카민스키', ym: '202606' }, { title: '프로젝트 헤일메리', author: '앤디 위어', ym: '202607' }, { title: '가면산장 살인사건', author: '히가시노 게이고', ym: '202608' }],
  totals: { answers: [35, 42, 35], comments: [23, 23, 29], reactions: [12, 31, 23], participants: 7 },
  ratings: { overall: [2.9, 4.1, 3.4], fun: [2.6, 4.4, 4.0], novelty: [3.1, 4.6, 3.3], length: [4.7, 3.3, 4.6], difficulty: [4.3, 4.0, 4.4] },
  thread: [{ book: 0, q: '집단 밖에 서는 사람은 특별한가?', body: '여섯 명이 아니라고 답했다.', quote: { text: '완벽한 이향인은 드물것 같다.', by: '9353', src: 'Q3' } }],
  verdict: '우리는 **개인의 특별함**을 의심한다.',
  roster: [{ phone4: '9353', nicks: ['졸린 고양이', '되돌아오지 않는 일식', '마에다 시오리'] }],
  members: [{ phone4: '9353', title: '간결왕', award: '간결왕 · 22자', desc: '댓글 0개.', quotes: [{ book: 2, text: '경찰에 신고해야하는거 아닌가?', src: '심판' }] }],
  graph: { order: ['5331', '9353'], counts: { '5331': { '9353': 4 } } },
};

/* 오프라인 기본 시즌(SEASON)에 리포트를 꽂고 책을 전부 마감 */
function seedSeason(a, { allClosed = true, report = REPORT } = {}) {
  a.w.SEASON.report = report;
  a.w.SEASON.books.forEach((b, i) => { b.closed = allClosed || i > 0; });
}

test('책장: 시즌 책이 전부 마감되고 리포트가 있으면 접은 신문이 놓인다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a);
  a.w.go('meetings');
  const paper = a.d.querySelector('#page-meetings .shelf-paper');
  assert.ok(paper, '신문이 책장 칸에 있어야 한다');
  assert.match(paper.getAttribute('aria-label'), /인간 본성 탐구 결산호/);
});

test('책장: 리포트가 없으면 신문이 없다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a, { report: null });
  a.w.go('meetings');
  assert.equal(a.d.querySelector('#page-meetings .shelf-paper'), null);
});

test('책장: 아직 안 닫힌 책이 있으면 리포트가 있어도 신문을 안 놓는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a, { allClosed: false });
  a.w.go('meetings');
  assert.equal(a.d.querySelector('#page-meetings .shelf-paper'), null);
});

test('신문을 누르면 결산 페이지 — 다섯 칸이 렌더되고 카드 번호는 눌러야 보인다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a);
  a.w.go('meetings');
  a.d.querySelector('#page-meetings .shelf-paper').click();
  assert.equal(a.page(), 'season-report');
  const pg = a.d.getElementById('page-season-report');
  const txt = pg.textContent;
  assert.match(txt, /인간에게는 회의적이고/, '제호 아래 시즌 한 줄');
  assert.match(txt, /112/, '답변 합계 35+42+35');
  assert.match(txt, /집단 밖에 서는 사람은 특별한가/);
  assert.match(txt, /되돌아오지 않는 일식/, '닉네임 명부');
  assert.match(txt, /누가 누구에게 말을 걸었나/);
  assert.equal(pg.querySelectorAll('.srp-axis').length, 5, '별점 5축');
  assert.ok(pg.querySelector('.srp-verdict b'), '**굵게** 는 b 로');
  const btn = pg.querySelector('.srp-reveal');
  assert.equal(btn.getAttribute('aria-expanded'), 'false');
  btn.click();
  assert.equal(btn.getAttribute('aria-expanded'), 'true');
  assert.ok(btn.classList.contains('on'));
  assert.equal(btn.querySelector('.num').textContent, '9353');
  assert.equal(a.d.getElementById('subbar-crumb').textContent.includes('시즌 결산'), true);
});

test('결산 페이지 뒤로 = 책장', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a);
  a.w.go('meetings');
  a.d.querySelector('#page-meetings .shelf-paper').click();
  a.w.back();
  assert.equal(a.page(), 'meetings');
});

test('시즌 페이지 상단에 결산호 진입 줄', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a);
  a.w.enterMeeting('m1');
  a.w.go('season');
  const entry = a.d.querySelector('#page-season .season-report-entry');
  assert.ok(entry);
  entry.click();
  assert.equal(a.page(), 'season-report');
});

test('발표모드: 시즌 리포트가 있으면 [시즌 결산] 탭이 보이고 씬이 렌더된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a);
  a.w.enterMeeting('m1');
  const b = a.w.bookById('ihyangin');
  b.report = { source: 't', generated_at: 'x', keywords: [], ratings: {}, stats: {}, summary: 's' };
  await a.w.startShare('ihyangin');
  const nav = a.d.getElementById('stage-nav-season');
  assert.equal(nav.style.display, '');
  a.w.showStageScene('season');
  assert.ok(a.d.getElementById('scene-season').classList.contains('active'));
  assert.match(a.d.getElementById('stage-season').textContent, /인간에게는 회의적이고/);
});

test('발표모드: 시즌 리포트가 없으면 [시즌 결산] 탭을 숨긴다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedSeason(a, { report: null });
  a.w.enterMeeting('m1');
  const b = a.w.bookById('ihyangin');
  b.report = { source: 't', generated_at: 'x', keywords: [], ratings: {}, stats: {}, summary: 's' };
  await a.w.startShare('ihyangin');
  assert.equal(a.d.getElementById('stage-nav-season').style.display, 'none');
});
