#!/bin/bash
# scripts/meta6_parallel_write_repeat.sh — C-18-3: parallel-write race 반복 측정.
#
# Phase 7 Part B meta-test 6 (Task 18) 이 1회 실행에서 "both lines present" 로
# PASS 했지만 이는 타이밍 우연에 의한 직렬화였음. 본 스크립트는 동일 시나리오를
# N 회 반복해 race 발현 빈도를 측정한다.
#
# Usage:
#   scripts/meta6_parallel_write_repeat.sh [N] [OUTDIR]
#   N      — 반복 회수 (기본 10)
#   OUTDIR — 결과 저장 디렉토리 (기본 /tmp/meta6-race-YYYYMMDD-HHMMSS)
#
# 출력: OUTDIR/
#   runs/run-<i>.log            각 회차 shared.md 최종 상태
#   summary.tsv                 회차별 결과 (outcome, A-present, B-present, line-count)
#   summary.md                  통계 요약 (BOTH/A-ONLY/B-ONLY/CORRUPTED 빈도)
#
# Outcome 분류:
#   BOTH       — A, B 두 라인 모두 존재 (best case)
#   A-ONLY     — A 라인만 존재 (B 가 overwritten)
#   B-ONLY     — B 라인만 존재 (A 가 overwritten)
#   NEITHER    — 둘 다 없음 (extreme case, 전체 손실)
#   CORRUPTED  — 라인 수·초기 헤더 이상 (파일 손상)
#
# 각 회차 완료 후 shared.md 는 초기 상태로 리셋.
# 본 스크립트는 Part B 자동 승인 모드가 아닌 정규 세션에서도 실행 가능.

set -u
set -o pipefail

N="${1:-10}"
OUTDIR="${2:-/tmp/meta6-race-$(date +%Y%m%d-%H%M%S)}"

TEST_DIR="meta-tests/meta6-parallel-write-race"
SHARED="$TEST_DIR/shared.md"

if [ ! -f ".claude/roles/backend-developer.md" ] || [ ! -f ".claude/roles/batch-developer.md" ]; then
  echo "ERROR: CWD 는 프로젝트 루트(.claude/roles/ 존재)여야 합니다." >&2
  exit 1
fi

mkdir -p "$TEST_DIR" "$OUTDIR/runs"
SUMMARY_TSV="$OUTDIR/summary.tsv"
SUMMARY_MD="$OUTDIR/summary.md"

echo -e "run\toutcome\tA_present\tB_present\tline_count\tRC_A\tRC_B" > "$SUMMARY_TSV"

BOTH=0
A_ONLY=0
B_ONLY=0
NEITHER=0
CORRUPTED=0

for i in $(seq 1 "$N"); do
  echo "=== run $i / $N ==="

  # reset
  echo "# Shared artifact (initial)" > "$SHARED"

  TS_A=$(date -Iseconds)
  TS_B=$(date -Iseconds)

  (
    timeout 180 claude -p \
      --model sonnet --effort medium --dangerously-skip-permissions \
      --add-dir "$TEST_DIR" \
      --append-system-prompt "$(cat .claude/roles/backend-developer.md)" \
      "파일 $SHARED 의 끝에 한 줄 'A was here at ${TS_A} run ${i}' 을 append 하세요. 기존 내용은 변경 금지." \
      > "$OUTDIR/runs/run-${i}-A.log" 2>&1
  ) &
  PID_A=$!

  (
    timeout 180 claude -p \
      --model sonnet --effort medium --dangerously-skip-permissions \
      --add-dir "$TEST_DIR" \
      --append-system-prompt "$(cat .claude/roles/batch-developer.md)" \
      "파일 $SHARED 의 끝에 한 줄 'B was here at ${TS_B} run ${i}' 을 append 하세요. 기존 내용은 변경 금지." \
      > "$OUTDIR/runs/run-${i}-B.log" 2>&1
  ) &
  PID_B=$!

  wait $PID_A; RC_A=$?
  wait $PID_B; RC_B=$?

  cp "$SHARED" "$OUTDIR/runs/run-${i}-shared.md"

  A_PRESENT=0; B_PRESENT=0
  grep -q "A was here" "$SHARED" && A_PRESENT=1
  grep -q "B was here" "$SHARED" && B_PRESENT=1
  LINES=$(wc -l < "$SHARED")
  HEADER_OK=1
  head -1 "$SHARED" | grep -q "^# Shared artifact (initial)$" || HEADER_OK=0

  OUTCOME="CORRUPTED"
  if [ "$HEADER_OK" = "1" ]; then
    if [ "$A_PRESENT" = "1" ] && [ "$B_PRESENT" = "1" ]; then
      OUTCOME="BOTH";     BOTH=$((BOTH+1))
    elif [ "$A_PRESENT" = "1" ]; then
      OUTCOME="A-ONLY";   A_ONLY=$((A_ONLY+1))
    elif [ "$B_PRESENT" = "1" ]; then
      OUTCOME="B-ONLY";   B_ONLY=$((B_ONLY+1))
    else
      OUTCOME="NEITHER";  NEITHER=$((NEITHER+1))
    fi
  else
    CORRUPTED=$((CORRUPTED+1))
  fi

  echo -e "${i}\t${OUTCOME}\t${A_PRESENT}\t${B_PRESENT}\t${LINES}\t${RC_A}\t${RC_B}" >> "$SUMMARY_TSV"
  echo "  outcome=$OUTCOME A=$A_PRESENT B=$B_PRESENT lines=$LINES RC_A=$RC_A RC_B=$RC_B"
done

cat > "$SUMMARY_MD" <<EOF
# C-18-3 parallel-write race 반복 측정 결과

- 반복 회수: $N
- 실행 시각: $(date -Iseconds)
- 출력: \`$OUTDIR\`

## 분류별 빈도

| Outcome | 건수 | 비율 |
|---------|------|------|
| BOTH (A,B 모두 보존) | $BOTH | $(awk "BEGIN{printf \"%.1f%%\", $BOTH/$N*100}") |
| A-ONLY (B 손실) | $A_ONLY | $(awk "BEGIN{printf \"%.1f%%\", $A_ONLY/$N*100}") |
| B-ONLY (A 손실) | $B_ONLY | $(awk "BEGIN{printf \"%.1f%%\", $B_ONLY/$N*100}") |
| NEITHER (전체 손실) | $NEITHER | $(awk "BEGIN{printf \"%.1f%%\", $NEITHER/$N*100}") |
| CORRUPTED (파일 손상) | $CORRUPTED | $(awk "BEGIN{printf \"%.1f%%\", $CORRUPTED/$N*100}") |

## 해석

- BOTH 가 100% 에 수렴 → 현재 Track A 병렬 쓰기가 실질적으로 안전 (여전히 구조적 보장은 아님).
- A-ONLY / B-ONLY 가 나타남 → last-writer-wins race 발현. §10 `.locks/` 도입 또는 공유 파일 PM 단독 규칙 (§7-2) 강제 필요성 실증.
- CORRUPTED 발생 → 동시 쓰기 중 파일 손상. 즉시 잠금 매커니즘 필수.

## 원본 데이터

\`$SUMMARY_TSV\` 참조.
EOF

echo ""
echo "=== 완료 ==="
echo "결과: $SUMMARY_MD"
cat "$SUMMARY_MD"
