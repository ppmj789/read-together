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

test('후보 수정: [수정] 버튼으로 폼이 값 채워 열리고 표는 유지된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지', '개리 마커스', '뇌 이야기', '책덕후사서');
  const cid = a.w.seasonCandidates('m1')[0].id;
  await a.w.voteCandidate(cid); // 표 1개 모인 상태에서 수정
  a.w.editCandidate(cid);
  assert.equal(a.d.getElementById('cand-title').value, '클루지');
  assert.equal(a.d.getElementById('cand-reason').value, '뇌 이야기');
  assert.equal(a.d.getElementById('cand-alias').value, '책덕후사서');
  a.d.getElementById('cand-title').value = '클루지(개정판)';
  a.d.getElementById('cand-reason').value = '뇌의 설계 결함 이야기';
  await a.w.proposeCandidate();
  const cs = a.w.seasonCandidates('m1');
  assert.equal(cs.length, 1, '수정은 새 후보를 만들지 않는다');
  assert.equal(cs[0].title, '클루지(개정판)');
  assert.equal(cs[0].reason, '뇌의 설계 결함 이야기');
  assert.equal(cs[0].voters.length, 1, '모인 표는 그대로');
  assert.equal(a.w.CANDADD.editId, null, '저장 후 수정 모드 해제');
});

test('후보 수정: 남의 추천은 회원이 수정할 수 없다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '남의 책');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.STATE.phone4 = '9999'; // 다른 회원으로 전환
  a.w.editCandidate(cid);
  assert.equal(a.w.CANDADD.open, false);
  assert.match(a.lastToast() || '', /내가 추천한 책만/);
});

test('후보 카드에 [수정]·[삭제] 버튼이 분리돼 있다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지');
  const acts = [...a.d.querySelectorAll('#page-vote .cand__act')].map((x) => x.textContent);
  assert.deepEqual(acts, ['수정', '삭제']);
  assert.equal(a.d.querySelectorAll('#page-vote .cand__x').length, 0, '× 버튼은 없어져야 함');
});

test('투표 버튼은 하트가 아니라 북마크 SVG', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지');
  const btn = a.d.querySelector('#page-vote .cand__vote');
  assert.ok(btn.querySelector('svg'), 'SVG 아이콘이어야 함');
  assert.doesNotMatch(btn.innerHTML, /💛|🤍/);
  assert.equal(btn.querySelector('svg').getAttribute('fill'), 'none', '안 찍었으면 외곽선');
  await a.w.voteCandidate(a.w.seasonCandidates('m1')[0].id);
  const on = a.d.querySelector('#page-vote .cand__vote svg');
  assert.equal(on.getAttribute('fill'), 'currentColor', '찍으면 꽉 채움');
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

/* ═══ v23 — 책 정보(출판사·가격·표지) + 후보 의견(댓글) ═══ */

async function proposeFull(a, title, pub = '', price = '') {
  a.w.CANDADD.open = true;
  a.w.renderVote();
  a.d.getElementById('cand-title').value = title;
  const pb = a.d.getElementById('cand-publisher');
  if (pb) pb.value = pub;
  const pr = a.d.getElementById('cand-price');
  if (pr) pr.value = price;
  await a.w.proposeCandidate();
}

test('책 정보: 출판사·가격이 저장되고 이유와 분리된 meta 줄로 표시된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await proposeFull(a, '클루지', '갤리온', '13,500원');
  const c = a.w.seasonCandidates('m1')[0];
  assert.equal(c.publisher, '갤리온');
  assert.equal(c.price, '13,500원');
  const meta = a.d.querySelector('#page-vote .cand__meta');
  assert.ok(meta, 'meta 줄이 있어야 함');
  assert.match(meta.textContent, /^갤리온 · 13,500원/);
  assert.ok(!meta.closest('.cand__reason'), '추천 이유 블록과 분리');
});

test('책 정보: 출판사만 있으면 가격 구분점 없이 출판사 + 서점 링크만', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await proposeFull(a, '클루지', '갤리온');
  assert.match(a.d.querySelector('#page-vote .cand__meta').textContent, /^갤리온 · 책 정보 ↗$/);
});

test('서점 링크: 아는 책은 알라딘 상품 페이지, 모르는 책은 제목+저자 검색으로 폴백', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '코스모스', '칼 세이건');
  await propose(a, '미지의 신간', '무명 작가');
  const cards = [...a.d.querySelectorAll('#page-vote .cand')];
  const cosmos = cards.find((x) => x.querySelector('.cand__title').textContent === '코스모스');
  // 표지(책등)와 meta 줄 양쪽에 같은 링크, 새 탭
  const spineA = cosmos.querySelector('.cand__spinelink');
  assert.match(spineA.getAttribute('href'), /wproduct\.aspx\?ItemId=396765073/);
  assert.equal(spineA.getAttribute('target'), '_blank');
  assert.equal(spineA.getAttribute('rel'), 'noopener');
  assert.equal(cosmos.querySelector('.cand__storelink').getAttribute('href'), spineA.getAttribute('href'));
  const unknown = cards.find((x) => x.querySelector('.cand__title').textContent === '미지의 신간');
  const href = unknown.querySelector('.cand__storelink').getAttribute('href');
  assert.match(href, /wsearchresult\.aspx\?SearchTarget=Book&SearchWord=/);
  assert.match(decodeURIComponent(href), /미지의 신간 무명 작가/);
});

test('후보 수정: 출판사·가격도 폼에 채워지고 수정된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await proposeFull(a, '클루지', '갤리온', '13,500원');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.editCandidate(cid);
  assert.equal(a.d.getElementById('cand-publisher').value, '갤리온');
  assert.equal(a.d.getElementById('cand-price').value, '13,500원');
  a.d.getElementById('cand-price').value = '11,000원';
  await a.w.proposeCandidate();
  assert.equal(a.w.seasonCandidates('m1')[0].price, '11,000원');
});

test('표지: BOOK_COVERS 에 있는 제목이면 책등 글자 대신 표지 이미지', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '코스모스', '칼 세이건');
  await propose(a, '표지없는 미지의 책');
  const cards = [...a.d.querySelectorAll('#page-vote .cand')];
  const cosmos = cards.find((x) => x.querySelector('.cand__title').textContent === '코스모스');
  const img = cosmos.querySelector('.cand__cover');
  assert.ok(img, '코스모스는 표지 이미지');
  assert.match(img.getAttribute('src'), /assets\/covers\/cosmos\.jpg/);
  const plain = cards.find((x) => x.querySelector('.cand__title').textContent === '표지없는 미지의 책');
  assert.ok(!plain.querySelector('.cand__cover'), '표지 없으면 이미지 없음');
  assert.equal(plain.querySelector('.cand__spine').textContent.trim().charAt(0), '표');
});

test('의견: 접힌 토글(💬 의견 0)로 시작, 펼쳐서 등록하면 목록·카운트 갱신', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지');
  const cid = a.w.seasonCandidates('m1')[0].id;
  const tog = a.d.querySelector('#page-vote .cand-cmt__toggle');
  assert.match(tog.textContent, /의견 0/);
  assert.ok(!a.d.querySelector('#page-vote .cand-cmt__list'), '접힘 상태에선 목록 없음');
  a.w.toggleCandCmt(cid);
  a.d.getElementById('ccmt-in-' + cid).value = '이 책 절판 아닌가요?';
  await a.w.addCandCmt(cid);
  const c = a.w.seasonCandidates('m1')[0];
  assert.equal(c.comments.length, 1);
  assert.equal(c.comments[0].body, '이 책 절판 아닌가요?');
  assert.equal(c.comments[0].byPhone, '1234');
  const txt = a.d.getElementById('page-vote').textContent;
  assert.match(txt, /이 책 절판 아닌가요\?/);
  assert.match(a.d.querySelector('#page-vote .cand-cmt__toggle').textContent, /의견 1/);
});

test('의견: 작성자 이름은 번호가 아니라 서재 닉네임(모임장은 모임장)', async (t) => {
  const a = app(t);
  await a.loginAs('7220');
  a.w.enterMeeting('m1');
  await propose(a, '클루지');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.toggleCandCmt(cid);
  a.d.getElementById('ccmt-in-' + cid).value = '재밌어 보여요';
  await a.w.addCandCmt(cid);
  const item = a.d.querySelector('#page-vote .cand-cmt__item');
  assert.match(item.textContent, new RegExp(a.w.candNick('7220', 'm1')));
  assert.doesNotMatch(item.textContent, /7220/);
});

test('의견 삭제: 내 의견만 × 가 보이고, 삭제하면 목록에서 빠진다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.toggleCandCmt(cid);
  a.d.getElementById('ccmt-in-' + cid).value = '첫 의견';
  await a.w.addCandCmt(cid);
  // 남의 의견엔 × 없음
  a.w.STATE.phone4 = '9999';
  a.w.renderVote();
  assert.ok(!a.d.querySelector('#page-vote .cand-cmt__item .cmt-x'), '남의 의견엔 삭제 버튼 없음');
  // 본인은 삭제 가능
  a.w.STATE.phone4 = '1234';
  a.w.renderVote();
  const x = a.d.querySelector('#page-vote .cand-cmt__item .cmt-x');
  assert.ok(x, '내 의견엔 삭제 버튼');
  const cmtId = a.w.seasonCandidates('m1')[0].comments[0].id;
  await a.w.delCandCmt(cmtId, cid);
  assert.equal(a.w.seasonCandidates('m1')[0].comments.length, 0);
});

test('의견: 로그인 없이 등록하면 막힌다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '클루지');
  const cid = a.w.seasonCandidates('m1')[0].id;
  a.w.toggleCandCmt(cid);
  a.d.getElementById('ccmt-in-' + cid).value = '몰래 쓰기';
  a.w.STATE.phone4 = null;
  await a.w.addCandCmt(cid);
  assert.equal((a.w.seasonCandidates('m1')[0].comments || []).length, 0);
  assert.match(a.lastToast() || '', /입장/);
});

/* ── 메인 책꽂이 개편(2026-08-21): 칸 나눠진 책꽂이, 한 칸 = 시즌 ── */

test('메인 책꽂이: 한 칸이 시즌 하나, 칸 안에 그 시즌 책이 책등으로 꽂힌다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  await tick();
  const el = a.d.getElementById('page-meetings');
  const bc = el.querySelector('.bookcase');
  assert.ok(bc, '책꽂이 프레임(.bookcase)');
  const cubbies = [...bc.querySelectorAll('.cubby')];
  assert.equal(cubbies.length, 2, '시즌 칸 1개 + 다음 칸 1개');
  assert.match(cubbies[0].querySelector('.cubby__title').textContent, /인간 본성 탐구/);
  assert.equal(cubbies[0].querySelector('.cubby__btn'), null, '시즌 칸엔 투표 버튼이 없다');
  const spines = [...cubbies[0].querySelectorAll('.spine-book')];
  assert.equal(spines.length, 3, '칸 안엔 그 시즌 책 3권만 (투표 슬롯 없음)');
  assert.match(spines[0].getAttribute('onclick'), /shelfOpenBook\('m1','ihyangin'\)/);
});

test('메인 책꽂이: 책등을 누르면 시즌을 거치지 않고 그 책 페이지로 간다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  await tick();
  /* 실제 클릭 — 칸 빈자리 클릭(시즌 입장)에 먹히지 않고 책으로 가야 한다 */
  const spine = a.d.getElementById('page-meetings').querySelector('.spine-book');
  spine.dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'book');
  assert.equal(a.w.STATE.meetingId, 'm1');
  assert.equal(a.w.STATE.bookId, 'ihyangin');
});

test('메인 책꽂이: 투표 내용은 펼쳐지지 않고, 버튼을 눌러야 투표 페이지로 들어간다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '코스모스', '칼 세이건');
  a.w.go('meetings');
  await tick();
  const el = a.d.getElementById('page-meetings');
  /* 후보 제목·투표 버튼은 메인에 노출되지 않는다 */
  assert.doesNotMatch(el.textContent, /코스모스/);
  assert.equal(el.querySelector('.vote-strip'), null);
  assert.equal(el.querySelector('.cand__vote'), null);
  /* '다음' 칸의 투표 버튼 — 후보 수만 배지로 */
  const btn = el.querySelector('.cubby--next .cubby__btn--vote');
  assert.ok(btn, '다음 칸에 다음 책 투표 버튼');
  assert.match(btn.textContent, /다음 책 투표/);
  assert.equal(btn.querySelector('.n').textContent, '1');
  btn.dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'vote');
  assert.match(a.d.getElementById('page-vote').textContent, /코스모스/);
});

test('메인 책꽂이: 다음 칸엔 모임장만 새 시즌 꽂기, 투표 버튼은 그 아래', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('meetings');
  await tick();
  const next = a.d.getElementById('page-meetings').querySelector('.cubby--next');
  const btns = [...next.querySelectorAll('.cubby__btn')];
  assert.equal(btns.length, 2, '새 시즌 꽂기 + 다음 책 투표');
  assert.match(btns[0].textContent, /새 시즌 꽂기/);
  assert.match(btns[1].textContent, /다음 책 투표/);
  btns[0].dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'create');
});

test('메인 책꽂이: 회원에겐 다음 칸에 투표 버튼만 (새 시즌 꽂기 없음)', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  await tick();
  const next = a.d.getElementById('page-meetings').querySelector('.cubby--next');
  const btns = [...next.querySelectorAll('.cubby__btn')];
  assert.equal(btns.length, 1);
  assert.match(btns[0].textContent, /다음 책 투표/);
  assert.doesNotMatch(next.textContent, /새 시즌 꽂기/);
});

test('메인 책꽂이 표지: 읽는 중인 책은 표지 면진열, 표지 있는 예정 책은 책등 질감', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  await tick();
  const spines = [...a.d.getElementById('page-meetings').querySelectorAll('.spine-book')];
  /* 이향인(열림·표지 있음) → 면진열 */
  assert.ok(spines[0].className.includes('spine-book--face'));
  const img = spines[0].querySelector('.spine-book__face');
  assert.match(img.getAttribute('src'), /covers\/ihyangin\.jpg/);
  /* 프로젝트 헤일메리(예정·표지 있음) → 표지를 책등 배경으로 + 제목 유지 */
  assert.ok(spines[1].className.includes('spine-book--cover'));
  assert.match(spines[1].getAttribute('style'), /--sp-img:url\('assets\/covers\/hailmary\.jpg'\)/);
  assert.match(spines[1].querySelector('.spine-book__title').textContent, /프로젝트 헤일메리/);
  /* 다크 심리학(표지 없음) → 색 책등 그대로 */
  assert.ok(!spines[2].className.includes('spine-book--cover'));
  assert.match(spines[2].getAttribute('style'), /--sp-bg:#2E5D52/);
});
