#!/usr/bin/env python3
"""시즌 결산 리포트(season.report, v31) 저장.

usage: python3 season_put.py <season title substring | season id> <season_report.json>

book.report 의 report_put.py 와 같은 방식 — index.html 의 anon 키로 REST PATCH.
필수 필드(source·generated_at·thesis·books·members·roster) 와 members[].phone4 를 검증한다.
"""
import sys, re, json, os, urllib.request, urllib.error

def find_repo_root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != '/':
        if os.path.exists(os.path.join(d, 'index.html')): return d
        d = os.path.dirname(d)
    raise SystemExit('index.html 을 찾지 못했습니다')

def creds():
    url = os.environ.get('SB_URL'); key = os.environ.get('SB_KEY')
    if url and key: return url, key
    html = open(os.path.join(find_repo_root(), 'index.html'), encoding='utf-8').read()
    url = re.search(r"var SB_URL\s*=\s*'([^']+)'", html).group(1)
    key = re.search(r"var SB_KEY\s*=\s*'([^']+)'", html).group(1)
    return url, key

def rest(url, key, path, data=None, method='GET'):
    req = urllib.request.Request(url + '/rest/v1/' + path, data=data, method=method)
    req.add_header('apikey', key); req.add_header('Authorization', 'Bearer ' + key)
    req.add_header('Content-Type', 'application/json'); req.add_header('Prefer', 'return=representation')
    with urllib.request.urlopen(req) as r: return json.loads(r.read().decode('utf-8') or 'null')

def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr); sys.exit(2)
    key_, path = sys.argv[1], sys.argv[2]
    rep = json.load(open(path, encoding='utf-8'))
    for f in ('source', 'generated_at', 'thesis', 'books', 'members', 'roster'):
        if f not in rep: raise SystemExit('필수 필드 누락: ' + f)
    for m in rep['members']:
        if not re.fullmatch(r'\d{4}', str(m.get('phone4', ''))): raise SystemExit('members[].phone4 는 4자리: %r' % m.get('phone4'))
    url, key = creds()
    seasons = rest(url, key, 'season?select=id,season_title')
    hit = [s for s in seasons if s['id'] == key_ or key_ in (s.get('season_title') or '')]
    if len(hit) != 1: raise SystemExit('시즌 매칭 %d개: %s' % (len(hit), [s['season_title'] for s in hit]))
    sid = hit[0]['id']
    try:
        out = rest(url, key, 'season?id=eq.' + sid, data=json.dumps({'report': rep}, ensure_ascii=False).encode('utf-8'), method='PATCH')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        if 'PGRST204' in body or 'report' in body:
            raise SystemExit('season.report 컬럼이 아직 없습니다 — v31 마이그레이션 적용/스키마 캐시 갱신 후 재시도.\n' + body)
        raise
    print('저장 완료: 「%s」 (%s)' % (hit[0]['season_title'], sid))
    print('  members=%d · roster=%d · thread=%d · books=%s' % (len(rep['members']), len(rep['roster']), len(rep.get('thread', [])), [b['title'] for b in rep['books']]))

if __name__ == '__main__':
    main()
