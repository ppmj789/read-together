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
  assert.equal(cubbies.length, 1, '시즌 칸만 — 별도의 다음 칸은 없다 (2026-08-27)');
  assert.match(cubbies[0].querySelector('.cubby__title').textContent, /인간 본성 탐구/);
  const spines = [...cubbies[0].querySelectorAll('.spine-book')];
  assert.equal(spines.length, 3, '칸 안엔 그 시즌 책 3권만');
  assert.match(spines[0].getAttribute('onclick'), /shelfOpenBook\('m1','ihyangin'\)/);
});

test('메인 책꽂이: 칸 제목 밑에 시즌 기간이 2026.06~08 형식으로 붙는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  await tick();
  const meta = a.d.getElementById('page-meetings').querySelector('.cubby__meta');
  /* 시드는 6월 책만 실제로 열려 있어 한 달, 실데이터(세 권)는 2026.06~08 로 나온다 */
  assert.match(meta.querySelector('.cubby__period').textContent, /^\d{4}\.\d{2}(~\d{2})?$/);
  assert.match(meta.textContent, /3권/);
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

test('메인 책꽂이: 책이 있는 칸엔 투표 UI 가 없고, 누르면 시즌으로 간다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await propose(a, '코스모스', '칼 세이건');
  a.w.go('meetings');
  await tick();
  const el = a.d.getElementById('page-meetings');
  /* 후보 제목·투표 UI 는 메인에 노출되지 않는다 */
  assert.doesNotMatch(el.textContent, /코스모스/);
  assert.equal(el.querySelector('.cand__vote'), null);
  assert.equal(el.querySelector('.cubby__votebtn'), null, '책이 있는 칸엔 투표 버튼이 없다');
  el.querySelector('.cubby__label').dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'season');
});

test('메인 책꽂이: 새 시즌 꽂기는 칸이 아니라 모임장 링크 줄에 있다', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.go('meetings');
  await tick();
  const el = a.d.getElementById('page-meetings');
  assert.equal(el.querySelector('.cubby--next'), null, '다음 칸은 사라졌다');
  const link = [...el.querySelectorAll('.host-links a')].find((x) => /새 시즌 꽂기/.test(x.textContent));
  assert.ok(link, '모임장 링크 줄의 새 시즌 꽂기');
  link.dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'create');
});

test('메인 책꽂이: 회원에겐 새 시즌 꽂기가 안 보인다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  await tick();
  const el = a.d.getElementById('page-meetings');
  assert.equal(el.querySelector('.host-links'), null);
  assert.doesNotMatch(el.textContent, /새 시즌 꽂기/);
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

/* ── 추천 회차(round, 2026-08-25): 시즌별로 회차를 나눠 새로 받는다 ── */

test('마감된 옛 추천: 지금 목록과 섞이지 않고 접힌 채로 열람만 된다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  /* 예전 판(1)에서 마감된 추천 + 지금 판은 2 — v24 마이그레이션이 만든 상태와 같다 */
  a.w.localStorage.setItem('rt:cands', JSON.stringify({
    m1: [{ id: 'old1', round: 1, title: '코스모스', author: '칼 세이건', reason: '', alias: '', byPhone: '1234', voters: ['1234'], comments: [] }],
  }));
  a.w.localStorage.setItem('rt:candround', JSON.stringify({ m1: 2 }));
  a.w.shelfGoVote('m1');
  await tick();
  const el = a.d.getElementById('page-vote');
  assert.equal(a.w.seasonCandidates('m1').length, 0, '지금 목록엔 안 섞인다');
  assert.doesNotMatch(el.querySelector('.cand-empty').textContent, /회차/);
  const toggle = el.querySelector('.cand-past__toggle');
  assert.match(toggle.textContent, /예전에 모였던 추천 보기 \(1권\)/);
  assert.equal(el.querySelector('.cand-past__item'), null, '접힌 채로 시작');
  toggle.dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  const item = a.d.getElementById('page-vote').querySelector('.cand-past__item');
  assert.match(item.textContent, /코스모스/);
  assert.match(item.querySelector('.cand-past__votes').textContent, /1표/);
  assert.equal(item.querySelector('.cand__vote'), null, '읽기 전용');
});

test('투표 페이지: 회차 배지·마감 버튼은 없다 (한 번에 다 받는다)', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.shelfGoVote('m1');
  await tick();
  const el = a.d.getElementById('page-vote');
  assert.equal(el.querySelector('.cand-round__badge'), null);
  assert.equal(el.querySelector('.cand-round__new'), null);
  assert.doesNotMatch(el.textContent, /회차/);
  assert.equal(typeof a.w.startCandRound, 'undefined', '회차 넘기기 기능 자체가 없다');
});

test('추천: 판 정보가 없는 옛 후보도 지금 목록에 그대로 뜬다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  /* v24 이전에 저장된 후보 — round 키가 아예 없다 */
  a.w.localStorage.setItem('rt:cands', JSON.stringify({
    m1: [{ id: 'old1', title: '옛날 후보', author: '', reason: '', alias: '', byPhone: '1234', voters: [], comments: [] }],
  }));
  assert.equal(a.w.seasonRound('m1'), 1);
  assert.equal(a.w.seasonCandidates('m1').length, 1);
  assert.equal(a.w.pastCandRounds('m1').length, 0);
});

/* ── 다음 시즌을 새로 만들면 추천은 그 시즌으로 (2026-08-27) ── */

test('책꽂이: 책이 없는 시즌 칸은 눌러서 곧장 그 시즌 투표로 간다', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.STATE.clubId = 'c1';
  a.w.BUILD = { name: '', stitle: '가을의 문장', ssub: '두 번째 봄' };
  await a.w.issueMeeting();
  await tick();
  const el = a.d.getElementById('page-meetings');
  const cubbies = [...el.querySelectorAll('.cubby')];
  assert.equal(cubbies.length, 2, '시즌 두 칸만');
  const autumn = cubbies[1];
  assert.match(autumn.querySelector('.cubby__title').textContent, /가을의 문장/);
  /* 칸 제목을 눌러도 시즌 페이지를 거치지 않고 투표로 직행 */
  autumn.querySelector('.cubby__label').dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'vote');
  const newId = a.w.STATE.meetingId;
  assert.notEqual(newId, 'm1', '읽는 중인 시즌이 아니라 새 시즌이 대상');
  assert.match(a.d.getElementById('page-vote').querySelector('.eyebrow').textContent, /가을의 문장/);
  /* 추천도 새 시즌에 쌓인다 */
  await propose(a, '가을의 소리');
  assert.equal(a.w.seasonCandidates(newId).length, 1);
  assert.equal(a.w.seasonCandidates('m1').length, 0, '이전 시즌엔 안 쌓인다');
});

test('책꽂이: 책이 없는 칸엔 안내문 대신 투표 버튼 하나만 (가독성)', async (t) => {
  const a = app(t);
  await hostLogin(a);
  a.w.STATE.clubId = 'c1';
  a.w.BUILD = { name: '', stitle: '가을의 문장', ssub: '' };
  await a.w.issueMeeting();
  await tick();
  const cubby = [...a.d.getElementById('page-meetings').querySelectorAll('.cubby')][1];
  assert.equal(cubby.querySelectorAll('.spine-book').length, 0);
  assert.equal(cubby.querySelector('.cubby-empty'), null, '안내문 블록은 없다');
  const btn = cubby.querySelector('.cubby__votebtn');
  assert.match(btn.textContent, /다음 책투표하기/);
  assert.equal(btn.querySelector('.n').textContent, '0');
  btn.dispatchEvent(new a.w.MouseEvent('click', { bubbles: true }));
  await tick();
  assert.equal(a.page(), 'vote');
});

/* ── 시즌 에피그래프·테마 (2026-08-27) ── */

/* 오프라인 커스텀 시즌에 여는 문장·테마를 심는다 (ONLINE 은 season 컬럼에서 옴) */
function seedThemedSeason(a, extra = {}) {
  const cs = JSON.parse(a.w.localStorage.getItem('rt:meetings') || '[]');
  cs.push({
    id: 'mAutumn', clubId: 'c1', name: '未知의 서재', kind: 'custom', isOpen: true,
    season: {
      title: '가을의 문장', sub: '모든 잎이 꽃이 되는, 두 번째 봄',
      eyebrow: '모임 · 未知의 서재', meta: '', books: [],
      epigraph: '가을은 모든 잎이 꽃이 되는 두 번째 봄이다.',
      epigraphBy: '알베르 카뮈', theme: 'autumn', ...extra,
    },
  });
  a.w.localStorage.setItem('rt:meetings', JSON.stringify(cs));
}

test('에피그래프: 시즌 페이지에 여는 문장과 출처가 뜬다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedThemedSeason(a);
  a.w.enterMeeting('mAutumn');
  await tick();
  const el = a.d.getElementById('page-season');
  const ep = el.querySelector('.epigraph');
  assert.ok(ep, '에피그래프 카드');
  assert.match(ep.querySelector('.epigraph__q').textContent, /모든 잎이 꽃이 되는 두 번째 봄/);
  assert.match(ep.querySelector('.epigraph__by').textContent, /알베르 카뮈/);
  assert.ok(el.querySelector('.season-page').className.includes('theme-autumn'), '가을 테마 스코프');
  assert.equal(ep.querySelector('.epigraph__leaf').textContent, '🍂');
});

test('에피그래프: 투표 페이지에도 같은 문장 + 추천 기준 안내', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedThemedSeason(a);
  a.w.shelfGoVote('mAutumn');
  await tick();
  const el = a.d.getElementById('page-vote');
  assert.match(el.querySelector('.epigraph--sm .epigraph__q').textContent, /두 번째 봄/);
  assert.match(el.textContent, /이 문장에 어울리는 책을 추천해 주세요/);
  assert.ok(el.querySelector('.cand-sec').className.includes('theme-autumn'));
});

test('에피그래프: 여는 문장이 없는 시즌엔 카드가 안 붙는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await tick();
  assert.equal(a.d.getElementById('page-season').querySelector('.epigraph'), null);
  a.w.go('vote');
  await tick();
  assert.equal(a.d.getElementById('page-vote').querySelector('.epigraph'), null);
});

test('테마: 책꽂이 칸도 시즌 결을 따라간다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedThemedSeason(a);
  a.w.go('meetings');
  await tick();
  const cubbies = [...a.d.getElementById('page-meetings').querySelectorAll('.cubby')];
  const autumn = cubbies.find((c) => /가을의 문장/.test(c.textContent));
  assert.ok(autumn.className.includes('theme-autumn'));
  assert.ok(autumn.className.includes('cubby--empty'));
});

test('테마: 이상한 theme 값은 클래스로 새지 않는다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedThemedSeason(a, { theme: 'autumn" onload="x' });
  a.w.enterMeeting('mAutumn');
  await tick();
  const el = a.d.getElementById('page-season');
  /* 따옴표·공백이 걸러져 속성으로 새지 않는다 — 남는 건 글자뿐인 클래스 한 덩어리 */
  assert.doesNotMatch(el.innerHTML, /onload=/);
  const cls = el.querySelector('.season-page').className.trim().split(/\s+/);
  assert.equal(cls.length, 2, 'season-page + theme-* 두 클래스뿐');
  assert.match(cls[1], /^theme-[a-z-]+$/);
});

test('시즌 페이지: 내 기록 보기 버튼은 없다 (하단 내비에 있으니 중복)', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  a.w.enterMeeting('m1');
  await tick();
  const el = a.d.getElementById('page-season');
  assert.doesNotMatch(el.textContent, /내 기록 보기/);
  /* 하단 내비의 '내 기록' 은 그대로 */
  assert.ok([...a.d.querySelectorAll('#bottomnav button')].some((b) => b.dataset.nav === 'history'));
});

test('시즌 기간: 책이 없으면 시즌에 적어둔 기간을 쓴다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  seedThemedSeason(a, { period: '2026.09~11' });
  a.w.go('meetings');
  await tick();
  const autumn = [...a.d.getElementById('page-meetings').querySelectorAll('.cubby')]
    .find((c) => /가을의 문장/.test(c.textContent));
  assert.equal(autumn.querySelector('.cubby__period').textContent, '2026.09~11');
});

/* ── 책마다 다른 별명 사전 (2026-08-27) ── */

test('별명 사전: 가면산장은 일본 추리 테마, 헤일메리는 우주 테마', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  const mask = a.w.nickSetForTitle('가면산장 살인사건');
  assert.ok(mask.adj.includes('유카타 차림의'), '일본 정경이 형용사에');
  assert.ok(mask.noun.includes('경부') && mask.noun.includes('명탐정'), '일본 미스터리 배역이 명사에');
  assert.equal(a.w.nickSetForTitle('프로젝트 헤일메리').noun.includes('우주비행사'), true);
  /* 사전이 없는 책은 서재·독서 기본값 — 우주 이름이 아무 책에나 붙지 않는다 */
  const dflt = a.w.nickSetForTitle('아직 사전 없는 책');
  assert.equal(dflt.noun.includes('우주비행사'), false);
  assert.ok(dflt.noun.includes('독서가'));
});

test('별명 사전: 자동 배정 이름이 그 책 사전에서 나온다', async (t) => {
  const a = app(t);
  await a.loginAs('1234');
  /* 오프라인 커스텀 시즌에 가면산장을 한 권 꽂는다 */
  const cs = JSON.parse(a.w.localStorage.getItem('rt:meetings') || '[]');
  cs.push({
    id: 'mMask', clubId: 'c1', name: '未知의 서재', kind: 'custom', isOpen: true,
    season: { title: '가면 시즌', sub: '', eyebrow: '', meta: '', books: [{
      id: 'bMask', title: '가면산장 살인사건', author: '히가시노 게이고', spine: '가',
      yearmonth: '', month: '', angle: '', tagline: '', intro: '', intro_note: '',
      authorBio: '', bio: [], links: [], questions: [''], others: [[]],
      opened_at: '2026-08-21T00:00:00Z', closed_at: null, closed: false, report: null,
    }] },
  });
  a.w.localStorage.setItem('rt:meetings', JSON.stringify(cs));
  const mask = a.w.nickSetForTitle('가면산장 살인사건');
  const auto = a.w.nickFor('7777', 'bMask');
  assert.ok(mask.adj.some((x) => auto.startsWith(x)), `${auto} 는 추리 테마여야 함`);
  assert.ok(mask.noun.some((x) => auto.endsWith(x)), `${auto} 는 추리 테마여야 함`);
  /* 같은 사람·같은 책이면 항상 같은 이름 (결정론 유지) */
  assert.equal(a.w.nickFor('7777', 'bMask'), auto);
  /* 픽커가 굴리는 이름도 같은 사전 */
  a.w.STATE.meetingId = 'mMask'; a.w.STATE.bookId = 'bMask';
  for (let i = 0; i < 12; i++) {
    const r = a.w.randomNick();
    assert.ok(mask.adj.some((x) => r.startsWith(x)) && mask.noun.some((x) => r.endsWith(x)), r);
  }
});
