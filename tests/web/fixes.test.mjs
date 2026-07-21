/* 2026-07-21 UI/UX 전수 수정 회귀 테스트
 * A: 답변 유실 방지(draft 백업)·죽은 confirm 가드·더블탭 가드
 * B: 인앱 다이얼로그·잠긴 탭 피드백·동선(결과 직진입 뒤로, 서재 self-link)
 * C: 접근성(tabindex/role 자동 부여, 키보드 활성화)
 * D: pin 입력 속성·로그인 안내문·meta description */
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

/* ── A1: 온라인 미제출 답변 로컬 백업 ── */

test('draft 백업: ONLINE 에서 captureAnswersLocal 이 localStorage 에도 저장한다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  await a.w.setRating('length', 3);
  a.w.setDiscView('mine');
  a.d.getElementById('ans-0').value = '자동로그아웃 나도 살아남을 답변';
  // 온라인 모드 시뮬레이션 — bookById 가 서버 캐시(MEET_CACHE)를 보므로 시드 시즌을 미러해 준다
  a.w.ONLINE = true;
  a.w.MEET_CACHE = [{ id: 'm1', clubId: 'c1', name: '未知의 서재', kind: 'custom', isOpen: true, season: { title: '인간 본성 탐구', sub: '', books: a.w.SEASON.books } }];
  a.w.captureAnswersLocal(); // 이때 saveStore 는 no-op — draft 백업이 유일한 영속층

  const drafts = JSON.parse(a.w.localStorage.getItem('rt:draft:1234'));
  assert.equal(drafts.ihyangin[0], '자동로그아웃 나도 살아남을 답변');
});

test('draft 복원: 서버 답이 빈 칸에만 백업을 되살린다 (서버 값 우선)', (t) => {
  const a = app(t);
  a.w.ONLINE = true;
  a.w.STATE.phone4 = '1234';
  a.w.draftSave('bk1', ['쓰다 만 답', '옛날 백업', '']);
  a.w.NETSTORE['bk1'] = { answers: ['', '서버에 저장된 답', ''], submitted: false, ratings: {}, comments: {} };
  a.w.applyLocalDrafts('bk1');
  const ans = a.w.NETSTORE['bk1'].answers;
  assert.equal(ans[0], '쓰다 만 답', '빈 칸은 백업으로 복원');
  assert.equal(ans[1], '서버에 저장된 답', '서버 값이 있으면 백업이 덮지 않음');
});

test('draft 정리: 제출된 책의 백업은 폐기된다', (t) => {
  const a = app(t);
  a.w.ONLINE = true;
  a.w.STATE.phone4 = '1234';
  a.w.draftSave('bk2', ['낡은 백업', '', '']);
  a.w.NETSTORE['bk2'] = { answers: ['제출한 답', '', ''], submitted: true, ratings: {}, comments: {} };
  a.w.applyLocalDrafts('bk2');
  assert.equal(a.w.NETSTORE['bk2'].answers[0], '제출한 답');
  assert.equal(JSON.parse(a.w.localStorage.getItem('rt:draft:1234') || '{}').bk2, undefined);
});

/* ── A3: 시즌 만들기 폼 이탈 가드 (죽은 confirm 부활) ── */

test('시즌폼 이탈: 입력이 있으면 확인창이 뜨고, 취소하면 입력이 보존된다', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('create');
  a.d.getElementById('cb-stitle').value = '한참 적던 제목';
  let asked = false;
  a.w.uiConfirm = async () => { asked = true; return false; };
  await a.w.exitBuilder();
  assert.equal(asked, true, '입력이 있으면 확인창이 떠야 함');
  assert.equal(a.page(), 'create');
  assert.equal(a.d.getElementById('cb-stitle').value, '한참 적던 제목');
});

test('시즌폼 이탈: 확인을 누르면 나가고, 빈 폼은 바로 나간다', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('create');
  a.d.getElementById('cb-stitle').value = '버릴 제목';
  a.w.uiConfirm = async () => true;
  await a.w.exitBuilder();
  assert.equal(a.page(), 'meetings');
  a.w.go('create');
  let asked = false;
  a.w.uiConfirm = async () => { asked = true; return true; };
  await a.w.exitBuilder(); // 빈 폼
  assert.equal(asked, false, '빈 폼은 확인 없이 나감');
  assert.equal(a.page(), 'meetings');
});

/* ── A4: 더블탭 가드 ── */

test('더블탭 가드: 확인창이 떠 있는 동안 두 번째 제출 탭은 무시된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  await a.w.setRating('length', 3);
  a.w.setDiscView('mine');
  const b = a.w.bookById('ihyangin');
  b.questions.forEach((q, i) => { a.d.getElementById('ans-' + i).value = '답 ' + i; });
  let confirms = 0;
  a.w.uiConfirm = () => { confirms++; return new Promise((r) => setTimeout(() => r(true), 30)); };
  const p1 = a.w.submitAnswers();
  const p2 = a.w.submitAnswers(); // 더블탭
  await Promise.all([p1, p2]);
  assert.equal(confirms, 1, '두 번째 탭은 잠금으로 차단');
  assert.equal(a.w.bookState('ihyangin').submitted, true);
});

test('더블탭 가드: 잠금 중엔 댓글 등록이 재진입하지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  assert.equal(a.w._busy('comment'), false, '첫 획득은 성공');
  assert.equal(a.w._busy('comment'), true, '중복 획득은 차단');
  await a.w.addComment(0, 0); // 잠금 중 — 아무 것도 하지 않고 조용히 반환해야 함
  a.w._done('comment');
  assert.equal(a.w._busy('comment'), false, '해제 후 다시 획득 가능');
  a.w._done('comment');
});

/* ── B5: 인앱 다이얼로그 (실제 모달 동작) ── */

test('uiConfirm 모달: 확인 → true, 취소 → false, Escape → false', async (t) => {
  const a = app(t);
  const real = a.w.__realUiConfirm;
  let p = real('지울까요?', { danger: true, okLabel: '삭제' });
  assert.ok(a.d.getElementById('rt-dialog'), '모달이 떠야 함');
  assert.match(a.d.querySelector('.dlg__msg').textContent, /지울까요/);
  a.d.getElementById('dlg-ok').click();
  assert.equal(await p, true);
  assert.equal(a.d.getElementById('rt-dialog'), null, '닫힌 뒤 DOM 에서 제거');
  p = real('또 지울까요?');
  a.d.getElementById('dlg-cancel').click();
  assert.equal(await p, false);
  p = real('Escape 테스트');
  const overlay = a.d.getElementById('rt-dialog');
  overlay.dispatchEvent(new a.w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  assert.equal(await p, false);
});

test('uiPrompt 모달: 입력 후 확인 → 값, 취소 → null', async (t) => {
  const a = app(t);
  const real = a.w.__realUiPrompt;
  let p = real('비밀번호를 입력하세요', { numeric: true });
  const inp = a.d.getElementById('dlg-input');
  assert.ok(inp, '입력칸이 있어야 함');
  inp.value = ' 1234 ';
  a.d.getElementById('dlg-ok').click();
  assert.equal(await p, '1234', '앞뒤 공백은 정리');
  p = real('다시 입력');
  a.d.getElementById('dlg-cancel').click();
  assert.equal(await p, null);
});

test('네이티브 confirm/prompt 는 더 이상 쓰이지 않는다 (모임장 삭제 흐름)', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.enterMeeting('m1');
  let nativeUsed = false;
  a.w.confirm = () => { nativeUsed = true; return true; };
  a.w.prompt = () => { nativeUsed = true; return '1234'; };
  await a.w.hostCloseBook('ihyangin', '이향인', true); // uiConfirm 스텁(true) 경유
  assert.equal(a.w.bookStatus(a.w.bookById('ihyangin')), 'closed');
  assert.equal(nativeUsed, false, '네이티브 다이얼로그 호출 금지');
});

/* ── B6: 잠긴 탭 피드백 ── */

test('잠긴 탭을 누르면 왜 잠겼는지 토스트로 알려준다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await a.w.openBook('ihyangin');
  a.w.go('discussion');
  const tabs = [...a.d.querySelectorAll('.disc-tab')];
  tabs[2].click(); // ③ 다른 사람의 답변 (잠김)
  assert.match(a.lastToast() || '', /제출하면 열려요/);
  tabs[1].click(); // ② 내 답변 (잠김)
  assert.match(a.lastToast() || '', /별점을 1개 이상/);
  assert.equal(a.w.DISC.view, 'rating', '잠긴 탭 클릭으로 뷰가 바뀌면 안 됨');
});

/* ── B7: 동선 ── */

test('발표 결과 직진입 후 ← 뒤로: 온 곳(시즌)으로 돌아간다', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.enterMeeting('m1');
  await a.w.hostCloseBook('ihyangin', '이향인', true);
  await a.w.hostGenerateReport('ihyangin', '이향인');
  a.w.STATE.isHost = false; // 참가자 시점
  a.w.go('season');
  await a.w.memberGoResults('ihyangin');
  assert.equal(a.page(), 'results');
  a.w.back();
  assert.equal(a.page(), 'season', '시즌에서 왔으면 시즌으로');
  // 사전정보를 거쳐 들어가면 기존대로 사전정보로
  await a.w.openBook('ihyangin');
  a.w.go('results');
  a.w.back();
  assert.equal(a.page(), 'book');
});

/* ── 하단 주 내비게이션 (2026-07-21 UX) ── */

function activeNav(a) {
  const b = a.d.querySelector('#bottomnav button.active');
  return b ? b.dataset.nav : null;
}

test('하단 내비: 로그인 전 숨김 → 로그인 후 표시 + 서재 탭 활성', async (t) => {
  const a = app(t);
  assert.equal(a.d.getElementById('bottomnav').classList.contains('visible'), false);
  await a.loginAs('1234');
  assert.equal(a.d.getElementById('bottomnav').classList.contains('visible'), true);
  assert.equal(activeNav(a), 'shelf');
});

test('하단 내비: 화면 이동에 따라 활성 탭이 따라온다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  assert.equal(activeNav(a), 'season');
  await a.w.openBook('ihyangin');
  assert.equal(activeNav(a), 'book');
  a.w.go('discussion');
  assert.equal(activeNav(a), 'book', '답변 화면도 이번 책 탭 소속');
  await a.w.openHistory();
  assert.equal(activeNav(a), 'history');
});

test('하단 내비: 어느 화면에서든 목적지로 직행 (시즌 미선택 시 자동 보정)', async (t) => {
  const a = app(t);
  await a.loginAs('1234'); // meetings — meetingId 없음
  await a.w.navGo('book');
  assert.equal(a.page(), 'book');
  assert.equal(a.w.STATE.bookId, 'ihyangin', '열림 상태인 이번 달 책으로 직행');
  await a.w.navGo('history');
  assert.equal(a.page(), 'history');
  await a.w.navGo('season');
  assert.equal(a.page(), 'season');
  await a.w.navGo('shelf');
  assert.equal(a.page(), 'meetings');
});

test('하단 내비: 발표모드에선 숨고 종료하면 돌아온다', async (t) => {
  const a = app(t);
  await a.loginAs('9999');
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'UNTOLD';
  a.d.getElementById('mg-pw').value = '1234';
  await a.w.managerLogin();
  a.w.enterMeeting('m1');
  await a.w.hostCloseBook('ihyangin', '이향인', true);
  await a.w.hostGenerateReport('ihyangin', '이향인');
  await a.w.startShare('ihyangin');
  assert.equal(a.d.getElementById('bottomnav').classList.contains('visible'), false, '발표 중 숨김');
  a.w.exitStage();
  assert.equal(a.d.getElementById('bottomnav').classList.contains('visible'), true, '종료 후 복귀');
});

test('하단 내비: 로그아웃하면 사라진다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.logout();
  await tick();
  assert.equal(a.d.getElementById('bottomnav').classList.contains('visible'), false);
});

/* ── C: 접근성 ── */

test('클릭 가능한 div/span 에 tabindex·role 이 자동 부여된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await tick(); // MutationObserver 반영
  const card = a.d.querySelector('#page-season .book-card');
  assert.equal(card.getAttribute('tabindex'), '0');
  assert.equal(card.getAttribute('role'), 'button');
  const subbarLink = a.d.getElementById('subbar-back');
  assert.equal(subbarLink.getAttribute('tabindex'), '0');
});

test('키보드 Enter 로 책 카드를 열 수 있다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await tick();
  const card = a.d.querySelector('#page-season .book-card');
  card.dispatchEvent(new a.w.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  await tick();
  assert.equal(a.page(), 'book');
});

/* ── D: 자잘한 것 ── */

test('로그인 입력: type=tel + 본인 번호·자동 로그아웃 안내 노출', (t) => {
  const a = app(t);
  const pin = a.d.getElementById('pin');
  assert.equal(pin.getAttribute('type'), 'tel');
  assert.equal(pin.getAttribute('autocomplete'), 'off');
  const hint = a.d.getElementById('page-login').textContent;
  assert.match(hint, /본인 번호/);
  assert.match(hint, /자동 로그아웃/);
});

test('meta description 존재 + 토스트 지속시간 파라미터 동작', async (t) => {
  const a = app(t);
  assert.ok(a.d.querySelector('meta[name="description"]'));
  a.w.toast('금방 사라질 토스트', 40);
  assert.equal(a.toasts().length, 1);
  await new Promise((r) => setTimeout(r, 400));
  assert.equal(a.toasts().length, 0, 'ms 파라미터대로 사라져야 함');
});
