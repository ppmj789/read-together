/* 내비게이션·인증·세션 동작 테스트 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app, boot, tick } from './harness.mjs';

test('초기 부팅: 로그인 화면 + 로그아웃 버튼 숨김', (t) => {
  const a = app(t);
  assert.equal(a.page(), 'login');
  assert.equal(a.logoutVisible(), false);
  assert.equal(a.w.STATE.phone4, null);
});

test('로그인 검증: 4자리 숫자가 아니면 거부', async (t) => {
  const a = app(t);
  a.d.getElementById('pin').value = '12x';
  await a.w.login();
  assert.equal(a.page(), 'login');
  assert.equal(a.w.STATE.phone4, null);
  assert.match(a.lastToast() || '', /4자리/);
});

test('정상 로그인: 未知의 서재(시즌 목록)까지 직진입 + 세션 저장 + 로그아웃 버튼 표시', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  assert.equal(a.page(), 'meetings');
  assert.equal(a.w.STATE.phone4, '1234');
  assert.equal(a.w.STATE.clubId, 'c1');
  assert.equal(a.logoutVisible(), true);
  const sess = JSON.parse(a.w.localStorage.getItem('rt:sess'));
  assert.equal(sess.p4, '1234');
  assert.equal(sess.pg, 'meetings');
});

test('[버그가드] 최상위(서재)에서 ← 뒤로: 로그인 화면으로 빠지지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.back();
  await tick();
  // 로그인 상태에서 최상위 화면의 뒤로가기가 로그인(휴대폰 입력) 화면을 띄우면 안 된다
  assert.notEqual(a.page(), 'login');
  assert.equal(a.w.STATE.phone4, '1234');
});

test('[버그가드] 로그인 화면과 로그아웃 버튼이 동시에 보이는 조합은 없다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.back(); // 최상위에서 뒤로
  await tick();
  const inconsistent = a.page() === 'login' && a.logoutVisible();
  assert.equal(inconsistent, false);
});

test('[버그가드] 브라우저 뒤로 끝까지: 세션이 살아있으면 로그아웃처럼 보이지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  // 히스토리 맨 바닥 엔트리(초기 replaceState 값)로 pop
  await a.pop({ rt: 1, pg: 'login', p4: null, cid: null, mid: null, host: false, bid: null });
  assert.notEqual(a.page(), 'login');
  assert.equal(a.w.STATE.phone4, '1234');
  assert.equal(a.logoutVisible(), true);
});

test('[버그가드] 로그아웃 후 뒤로가기로 세션이 부활하지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.logout();
  await tick();
  assert.equal(a.page(), 'login');
  // 히스토리에 남아있던 로그인 시절 엔트리로 pop — 세션 부활 금지
  await a.pop({ rt: 1, pg: 'meetings', p4: '1234', cid: 'c1', mid: null, host: false, bid: null });
  assert.equal(a.page(), 'login');
  assert.equal(a.w.STATE.phone4, null);
  assert.equal(a.logoutVisible(), false);
});

test('로그아웃: 이 기기의 rt:* 데이터 전부 삭제', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.localStorage.setItem('rt:1234', JSON.stringify({ ihyangin: { answers: ['a', '', ''] } }));
  a.w.logout();
  await tick();
  const leftover = [];
  for (let i = 0; i < a.w.localStorage.length; i++) {
    const k = a.w.localStorage.key(i);
    if (k && k.startsWith('rt:')) leftover.push(k);
  }
  assert.deepEqual(leftover, []);
  assert.equal(a.page(), 'login');
  assert.equal(a.logoutVisible(), false);
});

test('자동 로그아웃: 세션만 끊고 쓰던 데이터는 보존', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.localStorage.setItem('rt:1234', JSON.stringify({ ihyangin: { answers: ['보존될 답변', '', ''] } }));
  a.w.autoLogout();
  await tick();
  assert.equal(a.page(), 'login');
  assert.equal(a.w.localStorage.getItem('rt:sess'), null);
  const kept = JSON.parse(a.w.localStorage.getItem('rt:1234'));
  assert.equal(kept.ihyangin.answers[0], '보존될 답변');
});

test('세션 복원: 유효한 세션이면 마지막 화면으로 돌아간다', async (t) => {
  const a = app(t);
  a.w.localStorage.setItem(
    'rt:sess',
    JSON.stringify({ p4: '5678', cid: 'c1', mid: 'm1', host: false, bid: null, pg: 'season', ts: Date.now() })
  );
  const ok = await a.w.sessRestore();
  await tick();
  assert.equal(ok, true);
  assert.equal(a.page(), 'season');
  assert.equal(a.w.STATE.phone4, '5678');
  assert.equal(a.logoutVisible(), true);
});

test('세션 복원: 30분 지난 세션은 복원하지 않는다', async (t) => {
  const a = app(t);
  a.w.localStorage.setItem(
    'rt:sess',
    JSON.stringify({ p4: '5678', cid: 'c1', mid: null, host: false, bid: null, pg: 'meetings', ts: Date.now() - 31 * 60 * 1000 })
  );
  const ok = await a.w.sessRestore();
  await tick();
  assert.equal(ok, false);
  assert.equal(a.page(), 'login');
  assert.equal(a.w.localStorage.getItem('rt:sess'), null); // 만료 세션은 정리
});

test('세션 복원: 알 수 없는 페이지명은 홈으로 폴백', async (t) => {
  const a = app(t);
  a.w.localStorage.setItem(
    'rt:sess',
    JSON.stringify({ p4: '5678', cid: 'c1', mid: null, host: false, bid: null, pg: 'no-such-page', ts: Date.now() })
  );
  const ok = await a.w.sessRestore();
  await tick();
  assert.equal(ok, true);
  assert.equal(a.page(), 'meetings'); // clubs 는 단일 모임이라 서재로 forward
});

test('내부 뒤로가기 체인: 답변→사전정보→시즌→서재', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  assert.equal(a.page(), 'discussion');
  a.w.back();
  assert.equal(a.page(), 'book');
  a.w.back();
  assert.equal(a.page(), 'season');
  a.w.back();
  assert.equal(a.page(), 'meetings');
});

test('goHome: 로그인 상태면 서재, 아니면 로그인 화면', async (t) => {
  const a = app(t);
  a.w.goHome();
  await tick();
  assert.equal(a.page(), 'login');
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.goHome();
  await tick();
  assert.equal(a.page(), 'meetings');
});

test('이향인 모달: 뒤로가기(pop)는 모달만 닫고 화면 이동 없음', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  a.w.openIhyangTest();
  assert.equal(a.w.IHYANG_OPEN, true);
  await a.pop({ rt: 1, ihyang: 1, pg: 'discussion', p4: '1234' });
  assert.equal(a.w.IHYANG_OPEN, false);
  assert.equal(a.page(), 'discussion');
});

test('세션 가드: 미로그인 상태로 서재 렌더 시 로그인으로 밀어낸다', async (t) => {
  const a = app(t);
  a.w.go('meetings');
  await tick();
  assert.equal(a.page(), 'login');
});
