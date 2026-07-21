/* 엣지 케이스·운영(호스트) 흐름·데이터 격리 테스트 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app, tick } from './harness.mjs';

async function hostLogin(a, p4 = '9999') {
  await a.loginAs(p4);
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'UNTOLD';
  a.d.getElementById('mg-pw').value = '1234';
  await a.w.managerLogin();
}

test('히스토리 스택: 로그인 직후 [로그인, 서재] 2개만 — 유령 clubs 엔트리 없음', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  assert.equal(a.w.history.length, 2);
  assert.equal(a.w.history.state.pg, 'meetings');
  assert.equal(a.w.history.state.p4, '1234');
});

test('히스토리 스택: 같은 페이지 반복 이동은 엔트리를 쌓지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  const len = a.w.history.length;
  a.w.goHome();
  a.w.goHome();
  await tick();
  assert.equal(a.w.history.length, len);
});

test('서브바 뒤로 링크: 서재(최상위)에선 숨김, 안쪽 화면에선 노출', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  assert.equal(a.d.getElementById('subbar-back').style.display, 'none');
  a.w.enterMeeting('m1');
  assert.notEqual(a.d.getElementById('subbar-back').style.display, 'none');
});

test('로그인 입력: 앞뒤 공백은 허용(trim)', async (t) => {
  const a = app(t);
  a.d.getElementById('pin').value = ' 1234 ';
  await a.w.login();
  await tick();
  assert.equal(a.w.STATE.phone4, '1234');
});

test('로그아웃 상태에선 세션을 기록하지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.logout();
  await tick();
  a.w.go('login');
  assert.equal(a.w.localStorage.getItem('rt:sess'), null);
});

test('시즌 생성(오프라인 호스트): 제목만으로 발급 → 책장에 꽂힘', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('create');
  assert.equal(a.page(), 'create');
  a.d.getElementById('cb-stitle').value = '테스트 시즌';
  a.d.getElementById('cb-ssub').value = '한 줄 설명';
  await a.w.issueMeeting();
  assert.equal(a.page(), 'meetings');
  const created = a.w.customMeetings().find((m) => m.season && m.season.title === '테스트 시즌');
  assert.ok(created, '커스텀 시즌이 저장돼야 함');
  assert.match(a.d.getElementById('page-meetings').textContent, /테스트 시즌/);
});

test('시즌 생성 검증: 제목 없으면 발급 거부', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('create');
  a.d.getElementById('cb-stitle').value = '';
  await a.w.issueMeeting();
  assert.equal(a.page(), 'create');
  assert.match(a.lastToast() || '', /제목을 입력/);
});

test('커스텀 시즌: 책 추가 → 질문 채우면 열기 가능', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('create');
  a.d.getElementById('cb-stitle').value = '책 추가 시즌';
  await a.w.issueMeeting();
  const m = a.w.customMeetings().find((x) => x.season.title === '책 추가 시즌');
  a.w.enterMeeting(m.id);
  a.w.SADD.adding = true;
  a.w.renderSeason();
  a.d.getElementById('sadd-title').value = '새 책';
  a.d.getElementById('sadd-author').value = '저자';
  await a.w.addBookHostSubmit();
  const m2 = a.w.customMeetings().find((x) => x.season.title === '책 추가 시즌');
  assert.equal(m2.season.books.length, 1);
  const bid = m2.season.books[0].id;
  // 질문 없는 새 책(빈 문자열 1칸)은 열기 거부
  await a.w.hostOpenBook(bid, '새 책');
  assert.equal(a.w.bookStatus(a.w.bookById(bid)), 'upcoming');
  // 질문 저장 후 열기 성공
  a.w.saveBookQuestions(bid, ['첫 질문?']);
  await a.w.hostOpenBook(bid, '새 책');
  assert.equal(a.w.bookStatus(a.w.bookById(bid)), 'open');
});

test('기본 시즌(m1)엔 오프라인 책 추가 불가 안내', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.enterMeeting('m1');
  a.w.SADD.adding = true;
  a.w.renderSeason();
  a.d.getElementById('sadd-title').value = '아무 책';
  await a.w.addBookHostSubmit();
  assert.match(a.lastToast() || '', /온라인 전용/);
});

test('운영자 관리: 4자리 검증·중복 등록 거부', async (t) => {
  const a = app(t);
  await hostLogin(a);
  // 오프라인에선 SEED_CLUB 이 customClubs 에 없어 저장이 안 되므로 커스텀 모임으로 검증
  const cs = a.w.customClubs();
  cs.push({ id: 'cx', name: '테스트 모임', code: 'TESTX', pw: '1111', ownerPhones: ['9999'], isPublic: true });
  a.w.saveCustomClubs(cs);
  a.w.STATE.clubId = 'cx';
  a.w.go('owners');
  assert.equal(a.page(), 'owners');
  a.d.getElementById('add-owner-p4').value = '12';
  await a.w.addOwner();
  assert.match(a.lastToast() || '', /4자리/);
  a.d.getElementById('add-owner-p4').value = '9999';
  await a.w.addOwner();
  assert.match(a.lastToast() || '', /이미 등록된/);
  a.d.getElementById('add-owner-p4').value = '8888';
  await a.w.addOwner();
  // jsdom 창의 Array 는 노드 Array 와 프로토타입이 달라 JSON 으로 비교
  assert.deepEqual(JSON.parse(JSON.stringify(a.w.clubOwners(a.w.clubById('cx')))), ['9999', '8888']);
});

test('운영자 제거: 마지막 한 명은 제거 불가, 나를 제거하면 권한 상실', async (t) => {
  const a = app(t);
  await hostLogin(a);
  const cs = a.w.customClubs();
  cs.push({ id: 'cy', name: '모임2', code: 'TESTY', pw: '1111', ownerPhones: ['9999'], isPublic: true });
  a.w.saveCustomClubs(cs);
  a.w.STATE.clubId = 'cy';
  a.w.go('owners');
  await a.w.removeOwner('9999'); // 한 명뿐 → 거부
  assert.deepEqual(JSON.parse(JSON.stringify(a.w.clubOwners(a.w.clubById('cy')))), ['9999']);
  a.d.getElementById('add-owner-p4').value = '7777';
  await a.w.addOwner();
  await a.w.removeOwner('9999'); // 나를 제거 → 권한 상실
  assert.equal(a.w.STATE.isHost, false);
  assert.deepEqual(JSON.parse(JSON.stringify(a.w.clubOwners(a.w.clubById('cy')))), ['7777']);
});

test('이향인 점수(오프라인): postMessage 결과가 내 기록에 저장된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  await a.w.onIhyangResult({ type: 'ihyang-result', score: 200, pct: 80, isIhyang: true });
  const bs = a.w.bookState('ihyangin');
  assert.equal(bs.ihyangScore, 200);
  assert.equal(bs.ihyangIs, true);
  assert.match(a.lastToast() || '', /점수 기록 완료/);
});

test('자동 로그아웃 직전 작성 중이던 답변은 로컬에 보존된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  await a.w.setRating('length', 3);
  a.w.setDiscView('mine'); // 별점 1개 이상이면 내 답변 탭 진입 가능 — 입력칸이 여기 있음
  a.d.getElementById('ans-0').value = '아직 저장 안 한 답변';
  a.w.autoLogout();
  await tick();
  const kept = JSON.parse(a.w.localStorage.getItem('rt:1234'));
  assert.equal(kept.ihyangin.answers[0], '아직 저장 안 한 답변');
});

test('사용자별 저장 격리: 다른 4자리로 들어오면 남의 답변이 안 보인다', async (t) => {
  const a = app(t);
  await a.loginAs('1111');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  await a.w.setRating('length', 5);
  a.w.autoLogout(); // 데이터 보존형 로그아웃
  await tick();
  await a.loginAs('2222');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  const bs2222 = a.w.bookState('ihyangin');
  assert.equal(bs2222.ratings.length || 0, 0, '2222 는 1111 의 별점을 보면 안 됨');
  a.w.autoLogout();
  await tick();
  await a.loginAs('1111');
  assert.equal(a.w.bookState('ihyangin').ratings.length, 5, '1111 재로그인 시 자기 별점 복원');
});

test('발표모드 진입 가드: 발표자료 없으면 시작 거부', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.enterMeeting('m1');
  await a.w.startShare('ihyangin');
  assert.equal(a.w.isStage, false);
  assert.match(a.lastToast() || '', /발표자료를 생성/);
});

test('발표모드: 시작·종료 시 화면 전환과 popstate 시 자동 종료', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.enterMeeting('m1');
  await a.w.hostCloseBook('ihyangin', '이향인', true);
  await a.w.hostGenerateReport('ihyangin', '이향인');
  await a.w.startShare('ihyangin');
  assert.equal(a.w.isStage, true);
  assert.ok(a.d.getElementById('stage-wrap').classList.contains('visible'));
  // 뒤로가기(pop) → 발표모드 자동 종료
  await a.pop({ rt: 1, pg: 'season', p4: '9999', cid: 'c1', mid: 'm1', host: true, bid: null });
  assert.equal(a.w.isStage, false);
  assert.equal(a.page(), 'season');
});

test('세션 만료 경계: 30분 미만이면 유지, 초과하면 만료', (t) => {
  const a = app(t);
  const mk = (ageMin) => ({ p4: '1234', ts: Date.now() - ageMin * 60 * 1000 });
  assert.equal(a.w.sessExpired(mk(29)), false);
  assert.equal(a.w.sessExpired(mk(31)), true);
});

test('esc(): 특수문자 이스케이프 + 악센트 문자는 보존', (t) => {
  const a = app(t);
  assert.equal(a.w.esc('<a b="c">&\'</a>'), '&lt;a b=&quot;c&quot;&gt;&amp;&#39;&lt;/a&gt;');
  assert.equal(a.w.esc('café Zürich 未知'), 'café Zürich 未知');
});

test('extractUrl(): URL·도메인 추출과 꼬리 문장부호 제거', (t) => {
  const a = app(t);
  assert.equal(a.w.extractUrl('보기: https://example.com/a,b).'), 'https://example.com/a,b'.replace(',b', '')); // 쉼표에서 절단
  assert.equal(a.w.extractUrl('notion.so/page 자료'), 'https://notion.so/page');
  assert.equal(a.w.extractUrl('링크 없음'), null);
});
