/* 다음 책 투표(v19) 동작 테스트 — 오프라인(localStorage) 경로로 실제 코드 구동 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { app } from './harness.mjs';

async function hostLogin(a, p4 = '9999') {
  await a.loginAs(p4);
  a.w.go('manage');
  a.d.getElementById('mg-code').value = 'UNTOLD';
  a.d.getElementById('mg-pw').value = '1234';
  await a.w.managerLogin();
}

/* 시즌 페이지에서 '+ 책 추천하기' 폼을 열고 한 권 추천 */
async function propose(a, title, author = '') {
  a.w.CANDADD.open = true;
  a.w.renderSeason();
  a.d.getElementById('cand-title').value = title;
  const au = a.d.getElementById('cand-author');
  if (au) au.value = author;
  await a.w.proposeCandidate();
}

test('회원 추천: 후보가 투표 목록에 뜬다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '개리 마커스');
  const cands = a.w.seasonCandidates('m1');
  assert.equal(cands.length, 1);
  assert.equal(cands[0].title, '클루지');
  assert.equal(cands[0].byPhone, '1234');
  assert.match(a.d.getElementById('page-season').textContent, /클루지/);
});

test('복수 추천(approval): 여러 후보에 투표하고 다시 눌러 취소', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '책A');
  await propose(a, '책B');
  const [c1, c2] = a.w.seasonCandidates('m1');
  await a.w.voteCandidate(c1.id);
  await a.w.voteCandidate(c2.id);
  let cs = a.w.seasonCandidates('m1');
  assert.equal(cs.find((c) => c.id === c1.id).voters.length, 1, '책A 1표');
  assert.equal(cs.find((c) => c.id === c2.id).voters.length, 1, '책B 1표 — 복수 추천 가능');
  // 같은 후보 다시 누르면 내 표 취소
  await a.w.voteCandidate(c1.id);
  cs = a.w.seasonCandidates('m1');
  assert.equal(cs.find((c) => c.id === c1.id).voters.length, 0, '책A 표 취소됨');
});

test('추천 상한: 회원 1인 3권까지, 4번째는 거부', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '1권');
  await propose(a, '2권');
  await propose(a, '3권');
  await propose(a, '4권');
  assert.equal(a.w.seasonCandidates('m1').length, 3, '3권까지만 등록');
  assert.match(a.lastToast() || '', /3권까지/);
});

test('빈 제목 추천은 거부', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '');
  assert.equal(a.w.seasonCandidates('m1').length, 0);
  assert.match(a.lastToast() || '', /제목을 입력/);
});

test('투표는 로그인(휴대폰 4자리) 없으면 막힌다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '책A');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.STATE.phone4 = null; // 로그아웃 상황 시뮬레이션
  await a.w.voteCandidate(cid);
  assert.equal(a.w.seasonCandidates('m1')[0].voters.length, 0);
  assert.match(a.lastToast() || '', /입장/);
});

test('모임장은 남의 후보도 삭제할 수 있다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '삭제될 책');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.STATE.isHost = true;
  await a.w.delCandidate(cid, '삭제될 책');
  assert.equal(a.w.seasonCandidates('m1').length, 0);
});

test('모임장 확정: 후보를 예정 책으로 등록하고 후보에서 제거', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('create');
  a.d.getElementById('cb-stitle').value = '투표 시즌';
  await a.w.issueMeeting();
  const m = a.w.customMeetings().find((x) => x.season.title === '투표 시즌');
  a.w.enterMeeting(m.id);
  await propose(a, '승자책', '작가');
  const cid = a.w.seasonCandidates(m.id)[0].id;
  await a.w.promoteCandidate(cid, '승자책', '작가');
  const m2 = a.w.customMeetings().find((x) => x.season.title === '투표 시즌');
  assert.ok(m2.season.books.find((b) => b.title === '승자책'), '예정 책으로 등록됨');
  assert.equal(a.w.bookStatus(m2.season.books.find((b) => b.title === '승자책')), 'upcoming');
  assert.equal(a.w.seasonCandidates(m.id).length, 0, '후보에서 제거됨');
});
