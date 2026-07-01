#!/usr/bin/env python3
"""
저작한 report JSON 을 book.report 에 저장(PATCH)한다.

사용법:
    python3 report_put.py <book_id> <report.json>
환경변수 SB_URL / SB_KEY 로 자격증명을 덮어쓸 수 있다(기본값은 index.html 에서 파싱).

report.json 필수 필드: source, generated_at, keywords[], ratings{}, summary, stats{}.
keywords 각 항목: {w, size(lg|md|sm), c, q(실제 인용문), why(선정 이유)}.
프론트 렌더러(renderStageRating)가 그대로 읽으므로 스키마를 지킬 것.
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

REQ = ['source', 'generated_at', 'keywords', 'ratings', 'summary', 'stats']

def main():
    if len(sys.argv) < 3:
        print('usage: report_put.py <book_id> <report.json>', file=sys.stderr); sys.exit(2)
    bid, path = sys.argv[1], sys.argv[2]
    rep = json.load(open(path, encoding='utf-8'))
    missing = [k for k in REQ if k not in rep]
    if missing:
        print('report 에 필수 필드 누락: ' + ', '.join(missing), file=sys.stderr); sys.exit(2)
    for k in rep.get('keywords', []):
        if 'w' not in k or 'size' not in k:
            print('keyword 항목에 w/size 필요: ' + json.dumps(k, ensure_ascii=False), file=sys.stderr); sys.exit(2)
    url, key = creds()
    payload = json.dumps({'report': rep}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url + '/rest/v1/book?id=eq.' + bid, data=payload, method='PATCH')
    req.add_header('apikey', key); req.add_header('Authorization', 'Bearer ' + key)
    req.add_header('Content-Type', 'application/json'); req.add_header('Prefer', 'return=representation')
    with urllib.request.urlopen(req) as r:
        rows = json.loads(r.read().decode('utf-8'))
    if not rows:
        print('저장 실패 — 해당 id 의 책이 없거나 권한 문제', file=sys.stderr); sys.exit(1)
    b = rows[0]; rr = b['report']
    print('저장 완료: 「%s」' % b['title'])
    print('  source=%s · keywords=%d(인용 %d) · summary %d줄' % (
        rr.get('source'), len(rr.get('keywords', [])),
        sum(1 for k in rr.get('keywords', []) if k.get('q')),
        rr.get('summary', '').count(chr(10)) + 1))

if __name__ == '__main__':
    main()
