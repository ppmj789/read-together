#!/usr/bin/env python3
"""
발표자료(report) 생성용 — 한 권의 책에 대한 Supabase 원천 데이터를 모아
결정론 집계(별점 평균·통계·이향인 점수 분포)와 함께 JSON 으로 출력한다.

Claude 는 이 출력의 answers/comments 를 읽고 '키워드 중심' report 를 저작한 뒤
report_put.py 로 book.report 에 저장한다.

사용법:
    python3 report_fetch.py "이향인"          # 제목 부분일치
    python3 report_fetch.py <book_uuid>        # id 직접
환경변수 SB_URL / SB_KEY 로 자격증명을 덮어쓸 수 있다(기본값은 index.html 에서 파싱).
"""
import sys, re, json, os, urllib.request

def find_repo_root():
    d = os.path.abspath(os.path.dirname(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'index.html')) and os.path.isdir(os.path.join(d, 'supabase')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def creds():
    url = os.environ.get('SB_URL'); key = os.environ.get('SB_KEY')
    if url and key:
        return url, key
    html = open(os.path.join(find_repo_root(), 'index.html'), encoding='utf-8').read()
    url = re.search(r"var SB_URL\s*=\s*'([^']+)'", html).group(1)
    key = re.search(r"var SB_KEY\s*=\s*'([^']+)'", html).group(1)
    return url, key

def rest(url, key, path, count=False):
    req = urllib.request.Request(url + '/rest/v1/' + path)
    req.add_header('apikey', key); req.add_header('Authorization', 'Bearer ' + key)
    if count:
        req.add_header('Prefer', 'count=exact')
    with urllib.request.urlopen(req) as r:
        body = r.read().decode('utf-8')
        cr = r.headers.get('content-range')
    data = json.loads(body) if body.strip() else []
    total = None
    if cr and '/' in cr:
        try: total = int(cr.split('/')[-1])
        except: pass
    return data, total

AXES = ['length', 'difficulty', 'fun', 'novelty', 'overall']

def main():
    if len(sys.argv) < 2:
        print('usage: report_fetch.py <book title substring | book id>', file=sys.stderr); sys.exit(2)
    q = sys.argv[1]
    url, key = creds()
    books, _ = rest(url, key, 'book?select=id,title,author,yearmonth,questions')
    book = None
    for b in books:
        if b['id'] == q:
            book = b; break
    if book is None:
        cands = [b for b in books if q in (b.get('title') or '')]
        if len(cands) == 1:
            book = cands[0]
        elif len(cands) > 1:
            print('여러 책이 매칭됨 — id 로 지정하세요:', file=sys.stderr)
            for b in cands: print(' ', b['id'], b['title'], file=sys.stderr)
            sys.exit(2)
    if book is None:
        print('책을 찾지 못함: ' + q, file=sys.stderr); sys.exit(1)
    bid = book['id']
    members, _ = rest(url, key, 'member_book?book_id=eq.%s&select=phone4,nickname,submitted,ratings,meta' % bid)
    answers, nA = rest(url, key, 'answer?book_id=eq.%s&select=phone4,q_index,body' % bid, count=True)
    comments, nC = rest(url, key, 'comment?book_id=eq.%s&select=q_index,target_phone4,author_phone4,body' % bid, count=True)
    reactions, nR = rest(url, key, 'reaction?book_id=eq.%s&select=q_index,target_phone4' % bid, count=True)

    # 별점 평균
    ratings = {}
    for ax in AXES:
        vals = [ (m.get('ratings') or {}).get(ax) for m in members ]
        vals = [v for v in vals if isinstance(v, (int, float)) and v]
        ratings[ax] = {'avg': round(sum(vals)/len(vals), 1) if vals else 0, 'n': len(vals)}

    # 이향인 점수 분포 (meta.ihyang 이 있을 때만)
    dist = []
    for m in members:
        iy = ((m.get('meta') or {}).get('ihyang')) or None
        if iy and iy.get('score') is not None:
            dist.append({'score': iy.get('score'), 'pct': iy.get('pct'), 'is_ihyang': bool(iy.get('is'))})
    dist.sort(key=lambda x: -(x['score'] or 0))

    # 질문별 답변 (분석용 · 익명)
    by_q = {}
    for a in answers:
        by_q.setdefault(a['q_index'], []).append(a.get('body') or '')

    out = {
        'book': {'id': bid, 'title': book['title'], 'author': book.get('author'),
                 'yearmonth': book.get('yearmonth'), 'questions': book.get('questions') or []},
        'stats': {'answers': nA if nA is not None else len(answers),
                  'comments': nC if nC is not None else len(comments),
                  'reactions': nR if nR is not None else len(reactions),
                  'participants': len(members)},
        'ratings': ratings,
        'score_distribution': ({'threshold': 188, 'max': 280,
                                'passed': sum(1 for d in dist if d['is_ihyang']),
                                'scores': dist} if dist else None),
        'answers_by_question': by_q,
        'comments': [c.get('body') or '' for c in comments],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
