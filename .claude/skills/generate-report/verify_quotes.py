#!/usr/bin/env python3
"""report 인용 검증 (2026-07-31 사용자 피드백) — report 텍스트 안의 따옴표 인용이
실제 답변·댓글 원문에 존재하는지 확인한다. '달리지 않은 댓글을 달린 것처럼'
쓰는 사고를 막는 게 목적.

사용법:
    python3 verify_quotes.py <book title substring | book id> [report.json]
report.json 을 주면 그 파일을, 없으면 DB 의 book.report 를 검사한다.
공백은 양쪽 모두 접어서(연속 공백·개행 → 1칸) 부분 문자열 매칭. 하나라도
원문에 없으면 exit 1.
"""
import sys, re, json, urllib.request
from report_fetch import creds, rest

# 반응 종류 라벨 등 — 사용자 발화가 아닌 UI 용어는 검증 대상에서 제외
WHITELIST = {'밑줄', '완전 동의', '생각 못 했네요', '전 다르게', '더 듣고 싶어요',
             '이번 모임', '개인모드'}
# 같은 종류 따옴표끼리만 짝짓는다 — 종류를 섞으면 인접 인용 사이 구간을 오탐한다
QUOTE_RE = re.compile(r'“([^”]{6,}?)”|"([^"]{6,}?)"|‘([^’]{6,}?)’|\'([^\']{6,}?)\'')

def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()

def walk(o, path=''):
    """report 트리의 모든 문자열 값을 (경로, 값) 으로 순회"""
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + '.' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + '[%d]' % i)
    elif isinstance(o, str):
        yield path, o

def main():
    if len(sys.argv) < 2:
        print('usage: verify_quotes.py <book title|id> [report.json]', file=sys.stderr); sys.exit(2)
    q = sys.argv[1]
    url, key = creds()
    books, _ = rest(url, key, 'book?select=id,title,report')
    book = None
    for b in books:
        if b['id'] == q or q in (b.get('title') or ''):
            book = b; break
    if book is None:
        print('책을 찾지 못함: ' + q, file=sys.stderr); sys.exit(2)
    rep = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 else book.get('report')
    if not rep:
        print('report 가 없음', file=sys.stderr); sys.exit(2)
    bid = book['id']
    answers, _ = rest(url, key, 'answer?book_id=eq.%s&select=body' % bid)
    comments, _ = rest(url, key, 'comment?book_id=eq.%s&select=body' % bid)
    qrows, _ = rest(url, key, 'book?id=eq.%s&select=questions' % bid)
    questions = (qrows[0].get('questions') or []) if qrows else []
    corpus = norm(' ␂ '.join([a.get('body') or '' for a in answers] +
                                  [c.get('body') or '' for c in comments] + questions))
    total = miss = 0
    for path, s in walk(rep):
        for m in QUOTE_RE.finditer(s):
            frag = norm(next(g for g in m.groups() if g))
            if frag in WHITELIST or len(frag) < 6:
                continue
            total += 1
            if frag in corpus:
                print('  OK   %-40s “%s”' % (path, frag[:60]))
            else:
                miss += 1
                print('  MISS %-40s “%s”' % (path, frag[:80]))
    print('---')
    print('인용 %d개 중 원문 불일치 %d개' % (total, miss))
    sys.exit(1 if miss else 0)

if __name__ == '__main__':
    main()
