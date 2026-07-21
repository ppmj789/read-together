/* 시즌·책·답변·별점·마감 흐름 동작 테스트 (오프라인 데모 모드) */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app, tick } from './harness.mjs';

async function enterBook(a, bookId = 'ihyangin') {
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook(bookId);
}

test('시즌 화면: 시드 시즌 3권 카드 렌더 + 이향인만 열림', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  assert.equal(a.page(), 'season');
  const cards = a.d.querySelectorAll('#page-season .book-card');
  assert.equal(cards.length, 3);
  assert.equal(a.w.bookStatus(a.w.bookById('ihyangin')), 'open');
  assert.equal(a.w.bookStatus(a.w.bookById('hailmary')), 'upcoming');
  assert.equal(a.w.bookStatus(a.w.bookById('darkpsych')), 'upcoming');
});

test('사전정보 진입: 닉네임 자동 배정 + 헤더에 닉네임 노출', async (t) => {
  const a = app(t);
  await enterBook(a);
  assert.equal(a.page(), 'book');
  const nick = JSON.parse(a.w.localStorage.getItem('rt:nick'))['1234|ihyangin'];
  assert.ok(nick && nick.length > 0, '닉네임이 자동 배정돼야 함');
  assert.equal(a.d.getElementById('hdr-nick').textContent, nick);
});

test('답변 화면 탭 잠금: 별점 전엔 내답변 잠김, 제출 전엔 남의답변 잠김', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  const tabs = [...a.d.querySelectorAll('.disc-tab')];
  assert.equal(tabs.length, 3);
  assert.equal(tabs[1].getAttribute('aria-disabled'), 'true', '내 답변 탭은 별점 전 잠김');
  assert.equal(tabs[2].getAttribute('aria-disabled'), 'true', '남의 답변 탭은 제출 전 잠김');
});

test('별점: 즉시 저장 + 5축 모두 채우면 내 답변 탭으로 자동 이동', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of ['length', 'difficulty', 'fun', 'novelty']) await a.w.setRating(ax, 4);
  assert.equal(a.w.DISC.view, 'rating', '4축까지는 별점 탭 유지');
  await a.w.setRating('overall', 5);
  assert.equal(a.w.DISC.view, 'mine');
  const bs = a.w.bookState('ihyangin');
  assert.equal(bs.ratings.overall, 5);
  assert.equal(bs.ratings.length, 4);
});

test('제출 가드: 답변이 비어 있으면 제출되지 않는다', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 3);
  a.d.getElementById('ans-0').value = '첫 답변만 씀';
  await a.w.submitAnswers();
  assert.equal(a.w.bookState('ihyangin').submitted, false);
  assert.match(a.lastToast() || '', /모든 질문에 답한 뒤/);
});

test('제출 성공: submitted=true + 남의 답변 탭 열림', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 3);
  const b = a.w.bookById('ihyangin');
  b.questions.forEach((q, i) => { a.d.getElementById('ans-' + i).value = '답변 ' + (i + 1); });
  await a.w.submitAnswers();
  const bs = a.w.bookState('ihyangin');
  assert.equal(bs.submitted, true);
  assert.equal(a.w.DISC.view, 'others');
  const tabs = [...a.d.querySelectorAll('.disc-tab')];
  assert.notEqual(tabs[2].getAttribute('aria-disabled'), 'true', '제출 후 남의 답변 탭 잠금 해제');
});

test('임시저장: 답변 보존 + 미제출 유지', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 2);
  a.d.getElementById('ans-0').value = '쓰다 만 답변';
  await a.w.saveDraft();
  const bs = a.w.bookState('ihyangin');
  assert.equal(bs.answers[0], '쓰다 만 답변');
  assert.equal(bs.submitted, false);
});

test('별점 없이 제출 시도: confirm 취소하면 별점 탭으로 복귀', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  await a.w.setRating('length', 3); // 1축만 → mine 탭 진입 가능
  a.w.setDiscView('mine');
  a.w.uiConfirm = async () => false; // "그래도 제출?" 에 취소
  await a.w.submitAnswers();
  assert.equal(a.w.DISC.view, 'rating');
  assert.equal(a.w.bookState('ihyangin').submitted, false);
});

test('마감 가드: 닫힌 책엔 별점·임시저장·제출 모두 차단', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  await a.w.setRating('length', 3);
  a.w._setBookClosedLocal('ihyangin', true);
  await a.w.setRating('fun', 5);
  assert.equal(a.w.bookState('ihyangin').ratings.fun || 0, 0, '마감 후 별점 반영 금지');
  await a.w.saveDraft();
  await a.w.submitAnswers();
  assert.equal(a.w.bookState('ihyangin').submitted, false);
});

test('내 답변 삭제: 전부 비면 제출 상태 강등', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 3);
  const b = a.w.bookById('ihyangin');
  b.questions.forEach((q, i) => { a.d.getElementById('ans-' + i).value = '답 ' + i; });
  await a.w.submitAnswers();
  for (let i = 0; i < b.questions.length; i++) await a.w.delMyAnswer(i);
  const bs = a.w.bookState('ihyangin');
  assert.equal(bs.submitted, false);
  assert.ok(bs.answers.every((x) => !x || !x.trim()));
});

test('XSS 방어: 답변에 HTML 을 넣어도 스크립트로 렌더되지 않는다', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 3);
  const b = a.w.bookById('ihyangin');
  const payload = '<img src=x onerror="window.__pwned=1"><script>window.__pwned=2</scr' + 'ipt>';
  b.questions.forEach((q, i) => { a.d.getElementById('ans-' + i).value = payload; });
  await a.w.submitAnswers();
  await tick();
  assert.equal(a.w.__pwned, undefined);
  assert.equal(a.d.querySelector('#page-discussion img[src="x"]'), null);
});

test('내 기록: 제출한 책 수·답변 수 집계', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  for (const ax of a.w.RATING_AXES) await a.w.setRating(ax.k, 3);
  const b = a.w.bookById('ihyangin');
  b.questions.forEach((q, i) => { a.d.getElementById('ans-' + i).value = '답변 ' + i; });
  await a.w.submitAnswers();
  await a.w.openHistory();
  assert.equal(a.page(), 'history');
  const nums = [...a.d.querySelectorAll('.profile-stat__num')].map((e) => e.textContent);
  assert.deepEqual(nums, ['1', '3', '3']); // 읽은 책 1 · 제출 답변 3 · 시즌 도서 3
});

test('발표 결과 가드: 발표자료 없으면 사전정보로 튕긴다', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('results');
  await tick();
  assert.equal(a.page(), 'book');
  assert.match(a.lastToast() || '', /발표자료가 없어요/);
});

test('모임장 위임(오프라인): 백업 코드 인증 → 모임장 모드', async (t) => {
  const a = app(t);
  await a.loginAs('9999');
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'untold';
  a.d.getElementById('mg-pw').value = '1234';
  await a.w.managerLogin();
  assert.equal(a.w.STATE.isHost, true);
  assert.equal(a.page(), 'meetings');
});

test('모임장 위임 실패: 잘못된 코드/비번은 거부', async (t) => {
  const a = app(t);
  await a.loginAs('9999');
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'UNTOLD';
  a.d.getElementById('mg-pw').value = '0000';
  await a.w.managerLogin();
  assert.equal(a.w.STATE.isHost, false);
  assert.match(a.lastToast() || '', /맞지 않아요/);
});

test('호스트 열기 가드: 질문 없는 책은 열 수 없다', async (t) => {
  const a = app(t);
  await a.loginAs('9999');
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'UNTOLD';
  a.d.getElementById('mg-pw').value = '1234';
  await a.w.managerLogin();
  a.w.enterMeeting('m1');
  await a.w.hostOpenBook('darkpsych', '다크 심리학'); // questions: []
  assert.equal(a.w.bookStatus(a.w.bookById('darkpsych')), 'upcoming');
  assert.match(a.lastToast() || '', /질문이 1개 이상 필요/);
});

test('호스트 닫기 → 발표자료(mock) 생성 → 발표 결과 열람', async (t) => {
  const a = app(t);
  await a.loginAs('9999');
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'UNTOLD';
  a.d.getElementById('mg-pw').value = '1234';
  await a.w.managerLogin();
  a.w.enterMeeting('m1');
  await a.w.hostCloseBook('ihyangin', '이향인', true);
  assert.equal(a.w.bookStatus(a.w.bookById('ihyangin')), 'closed');
  await a.w.hostGenerateReport('ihyangin', '이향인');
  assert.ok(a.w.bookById('ihyangin').report, '발표자료가 생성돼야 함');
  await a.w.openBook('ihyangin');
  a.w.go('results');
  await tick();
  assert.equal(a.page(), 'results');
});

test('예정 책 진입: 답변 화면은 잠금 안내만 노출', async (t) => {
  const a = app(t);
  await enterBook(a, 'hailmary');
  a.w.go('discussion');
  assert.match(a.d.getElementById('page-discussion').textContent, /아직 열리지 않았어요/);
  assert.equal(a.d.querySelectorAll('#page-discussion .disc-tab').length, 0);
});

test('닉네임 변경: 다시 뽑기 → 확정하면 저장되고 헤더 반영', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  a.w.startNickChange();
  assert.equal(a.w.NICKMODE, true);
  a.w.rollNick();
  const pend = a.w.PENDNICK;
  await a.w.confirmNick();
  assert.equal(a.w.NICKMODE, false);
  const saved = JSON.parse(a.w.localStorage.getItem('rt:nick'))['1234|ihyangin'];
  assert.equal(saved, pend);
});

test('닉네임 직접 입력: 20자 초과 거부', async (t) => {
  const a = app(t);
  await enterBook(a);
  a.w.go('discussion');
  a.w.startNickChange();
  a.d.getElementById('nk-custom').value = '가'.repeat(21);
  await a.w.confirmNick();
  assert.match(a.lastToast() || '', /20자/);
  assert.equal(a.w.NICKMODE, true, '실패 시 변경 모드 유지');
});
