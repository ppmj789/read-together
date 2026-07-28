/* 다음 책 투표(v19) 동작 테스트 — 오프라인(localStorage) 경로로 실제 코드 구동 */
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

/* 별도 투표 페이지(page-vote)에서 '+ 책 추천하기' 폼을 열고 한 권 추천 */
async function propose(a, title, author = '', reason = '', alias = '') {
  a.w.CANDADD.open = true;
  a.w.renderVote();
  a.d.getElementById('cand-title').value = title;
  const au = a.d.getElementById('cand-author');
  if (au) au.value = author;
  const rz = a.d.getElementById('cand-reason');
  if (rz) rz.value = reason;
  const al = a.d.getElementById('cand-alias');
  if (al) al.value = alias;
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
  assert.match(a.d.getElementById('page-vote').textContent, /클루지/);
});

test('추천 이유: 후보에 저장되고 카드에 표시된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '개리 마커스', '뇌의 설계 결함 이야기가 흥미로워요');
  const c = a.w.seasonCandidates('m1')[0];
  assert.equal(c.reason, '뇌의 설계 결함 이야기가 흥미로워요');
  assert.match(a.d.getElementById('page-vote').textContent, /뇌의 설계 결함 이야기가 흥미로워요/);
});

test('추천인 별명: 직접 적으면 그 이름으로 표시된다', async (t) => {
  const a = app(t);
  await a.loginAs('7220');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '개리 마커스', '', '책덕후사서');
  const c = a.w.seasonCandidates('m1')[0];
  assert.equal(c.alias, '책덕후사서');
  const txt = a.d.getElementById('page-vote').textContent;
  assert.match(txt, /책덕후사서님 추천/);
  assert.doesNotMatch(txt, /No\.\s*7220/);
});

test('추천인 별명 미입력: 번호 대신 시즌 우주 닉네임이 뜬다', async (t) => {
  const a = app(t);
  await a.loginAs('7220');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '개리 마커스');
  const txt = a.d.getElementById('page-vote').textContent;
  assert.doesNotMatch(txt, /No\.\s*7220/);
  const auto = a.w.candNick('7220', 'm1');
  assert.ok(auto && auto !== '모임장', '자동 닉네임이 배정돼야 함');
  assert.match(txt, new RegExp(auto + '님 추천'));
  // 결정론 — 같은 사람·같은 시즌이면 항상 같은 이름, 책 닉네임과는 다른 축
  assert.equal(a.w.candNick('7220', 'm1'), auto);
  assert.notEqual(a.w.nickFor('7220', 'm1-b1'), auto);
});

test('투표 닉네임은 서재 테마 — 헤일메리 우주 테마 사전을 안 쓴다', async (t) => {
  const a = app(t);
  await a.loginAs('7220');
  a.w.enterMeeting('m1');
  const seen = new Set();
  for (const p4 of ['7220', '1234', '0001', '5555', '8080', '3141', '4242', '1111']) {
    const nm = a.w.candNick(p4, 'm1'); // 형용사·명사에 공백이 있어 split 대신 접두·접미로 판정
    assert.ok(a.w.VOTE_ADJ.some((adj) => nm.startsWith(adj + ' ')), `서재 형용사여야: ${nm}`);
    assert.ok(a.w.VOTE_NOUN.some((n) => nm.endsWith(' ' + n)), `서재 명사여야: ${nm}`);
    assert.ok(!a.w.NICK_ADJ.some((adj) => nm.startsWith(adj + ' ')), `우주 형용사면 안 됨: ${nm}`);
    seen.add(nm);
  }
  assert.ok(seen.size >= 6, '사람마다 충분히 갈려야 함');
});

test('후보 카드: 책등 + 제목 블록으로 렌더되고 최다 득표엔 왕관', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '개리 마커스');
  await propose(a, '이기적 유전자');
  const card = a.d.querySelector('#page-vote .cand');
  assert.ok(card, '후보 카드가 있어야 함');
  assert.equal(card.querySelector('.cand__spine').textContent.trim().charAt(0), '클');
  assert.equal(card.querySelector('.cand__title').textContent, '클루지');
  // 아직 아무도 투표 안 함 → 왕관 없음
  assert.equal(a.d.querySelectorAll('#page-vote .cand__crown').length, 0);
  await a.w.voteCandidate(a.w.seasonCandidates('m1').find((c) => c.title === '클루지').id);
  const lead = a.d.querySelector('#page-vote .cand--lead');
  assert.match(lead.querySelector('.cand__title').textContent, /클루지/);
  assert.equal(a.d.querySelectorAll('#page-vote .cand__crown').length, 1);
});

test('추천인 별명: 20자 초과는 잘리고 공백은 한 칸으로 정규화된다', async (t) => {
  const a = app(t);
  await a.loginAs('7220');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '', '', '  아주   긴별명입니다일이삼사오육칠팔구십백천만억  ');
  const c = a.w.seasonCandidates('m1')[0];
  assert.equal(c.alias.length, 20);
  assert.equal(c.alias, '아주 긴별명입니다일이삼사오육칠팔구십백천만억'.slice(0, 20));
});

test('책장 진입 카드 → 별도 투표 페이지로 이동 (같은 페이지 아님)', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  // 시즌 페이지엔 진입 카드만 있고 투표 UI는 없다
  const seasonHtml = a.d.getElementById('page-season').innerHTML;
  assert.match(seasonHtml, /vote-entry/);
  assert.doesNotMatch(seasonHtml, /cand-sec/);
  // 카드 클릭 → vote 페이지로 이동 + 투표 UI 렌더
  const card = a.d.querySelector('#page-season .vote-entry');
  assert.ok(card, '진입 카드가 있어야 함');
  card.click();
  await tick();
  assert.equal(a.page(), 'vote');
  assert.match(a.d.getElementById('page-vote').innerHTML, /cand-sec/);
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
