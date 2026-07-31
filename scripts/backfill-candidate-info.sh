#!/usr/bin/env bash
# v23 백필 — 기존 다음 책 후보 6권에 출판사·가격 채우기 (2026-07-31, 알라딘 조회값)
# 실행 시점: v23 마이그레이션이 DB 에 적용된 뒤 (update 정책이 v23 에서 생기므로
#            그 전에 돌리면 조용히 0행 — 적용 여부는 출력 JSON 이 비어있지 않은지로 확인).
# 사용법: bash scripts/backfill-candidate-info.sh
set -euo pipefail
SB_URL='https://kkkmsnyiwliovitsmsmw.supabase.co'
SB_KEY=$(grep -oP "(?<=^var SB_KEY = ')[^']+" "$(dirname "$0")/../index.html")

patch(){ # $1=candidate id, $2=publisher, $3=price
  curl -s -X PATCH "$SB_URL/rest/v1/next_book_candidate?id=eq.$1" \
    -H "apikey: $SB_KEY" -H "Authorization: Bearer $SB_KEY" \
    -H "Content-Type: application/json" -H "Prefer: return=representation" \
    -d "{\"publisher\":\"$2\",\"price\":\"$3\"}" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("OK" if d else "NO-OP(update 정책 미적용?)", d[0]["title"] if d else "")'
}

patch 1d01cba8-1388-4cd3-a884-f34746c1c766 '민음사'       '9,000원'   # 체호프 단편선
patch 8310e598-f7f0-4c15-a95f-3c0393bb2004 '황금가지'     '22,000원'  # 눈물을 마시는 새 1
patch 9255d54c-2bc1-4254-bf10-cc6eeafd636b '재인'         '16,800원'  # 가면산장 살인사건
patch 6f50e9bf-0e2c-4f71-a5f9-70bb9b5eaaaa '오픈하우스'   '20,000원'  # 아이기스
patch 40d3d0eb-3ffe-4538-aae9-7c1a2675f590 '사이언스북스' '22,000원'  # 코스모스 (100만 부 기념판)
patch 51930e85-4230-46d7-a554-cee062a8ef3e '문학사상'     '13,500원'  # 바람의 노래를 들어라
