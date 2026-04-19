#!/bin/bash
# scripts/execute_rollback.sh — PM helper to execute §4-3 rollback for a project.
#
# Usage:
#   scripts/execute_rollback.sh <project> <target-stage> [--mode=move|snapshot] [--date=YYYYMMDD]
#
# Arguments:
#   <project>        프로젝트 이름 (projects/<project>/ 경로와 일치).
#   <target-stage>   회귀 목표 단계 (예: 01_analysis). 해당 단계 이후 모든 단계가 archive 대상.
#
# Options:
#   --mode=move      기본값. 원본을 _archived/<date>-v<seq>/ 로 mv. stage 디렉토리 비움.
#   --mode=snapshot  cp -r 로 스냅샷 후 원본 유지 (rework 이 소폭일 때).
#   --date=YYYYMMDD  archive 디렉토리 날짜 부분 고정 (기본: 오늘). seq 는 자동 증분.
#
# Behavior:
#   1. projects/<project>/ 기준으로 target-stage 이후의 모든 stage 디렉토리(01_analysis, 02_design, 03_implementation, 04_test, 05_deployment)
#      중 존재하는 것을 archive.
#   2. 99_audit/ 하위에서 target-stage 또는 그 이후 단계의 감리 디렉토리(NN_<stage>-audit)도 동일 방식으로 archive.
#   3. RTM/ 은 항상 SNAPSHOT 모드 (rework 중 읽기 빈번). RTM/_archived/<date>-vN/ 에 index.md + by-stage/* 복사.
#   4. 00_kickoff/rollback-history.md 에 행 추가 (mode 컬럼 포함).
#   5. 출력: 생성된 archive 경로 목록과 수정해야 할 project-state.md 의 current-stage 권고값.
#
# Not done by this script (PM 직접 수행):
#   - project-state.md frontmatter current-stage 갱신 (PM 단독 수정 파일).
#   - Approval Log 에 auto-rollback 행 추가.
#   - rollback 사유 (Reason 컬럼 본문) 의 상세 서술.
#
# Exit codes:
#   0  정상 완료
#   1  인자 오류
#   2  프로젝트 경로 없음
#   3  target-stage 가 유효하지 않음
#   4  archive 중 파일 시스템 오류

set -u
set -o pipefail

PROJECT=""
TARGET_STAGE=""
MODE="move"
DATE=$(date +%Y%m%d)

while [ $# -gt 0 ]; do
  case "$1" in
    --mode=*)
      MODE="${1#--mode=}"
      ;;
    --date=*)
      DATE="${1#--date=}"
      ;;
    --help|-h)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      if [ -z "$PROJECT" ]; then
        PROJECT="$1"
      elif [ -z "$TARGET_STAGE" ]; then
        TARGET_STAGE="$1"
      else
        echo "ERROR: 인자 과다: $1" >&2
        exit 1
      fi
      ;;
  esac
  shift
done

if [ -z "$PROJECT" ] || [ -z "$TARGET_STAGE" ]; then
  echo "Usage: $0 <project> <target-stage> [--mode=move|snapshot] [--date=YYYYMMDD]" >&2
  exit 1
fi

case "$MODE" in
  move|snapshot) ;;
  *) echo "ERROR: --mode 는 move 또는 snapshot" >&2; exit 1 ;;
esac

PROJ_ROOT="projects/$PROJECT"
if [ ! -d "$PROJ_ROOT" ]; then
  echo "ERROR: $PROJ_ROOT 디렉토리 없음" >&2
  exit 2
fi

ALL_STAGES=(01_analysis 02_design 03_implementation 04_test 05_deployment)
if [[ ! " ${ALL_STAGES[*]} " =~ " ${TARGET_STAGE} " ]]; then
  echo "ERROR: target-stage 는 다음 중 하나: ${ALL_STAGES[*]}" >&2
  exit 3
fi

# target-stage 부터 끝까지 archive 대상 단계 수집
TARGET_IDX=0
for i in "${!ALL_STAGES[@]}"; do
  if [ "${ALL_STAGES[$i]}" = "$TARGET_STAGE" ]; then
    TARGET_IDX=$i
    break
  fi
done

ARCHIVE_STAGES=("${ALL_STAGES[@]:$TARGET_IDX}")
echo "=== Rollback plan ==="
echo "project:       $PROJECT"
echo "target-stage:  $TARGET_STAGE"
echo "mode:          $MODE"
echo "date:          $DATE"
echo "archive stages: ${ARCHIVE_STAGES[*]}"
echo ""

# archive 함수 — seq 는 기존 _archived/<date>-v<N>/ 를 보고 자동 증분
next_seq() {
  local archive_parent="$1"
  local seq=1
  if [ -d "$archive_parent" ]; then
    while [ -d "$archive_parent/${DATE}-v${seq}" ]; do
      seq=$((seq + 1))
    done
  fi
  echo "$seq"
}

do_archive() {
  local src="$1"          # ex: projects/foo/01_analysis
  local mode="$2"         # move | snapshot
  local archive_parent="$src/_archived"
  local seq
  seq=$(next_seq "$archive_parent")
  local dst="$archive_parent/${DATE}-v${seq}"

  if [ ! -d "$src" ]; then
    echo "  skip $src (없음)"
    return 0
  fi

  mkdir -p "$dst" || return 4

  if [ "$mode" = "move" ]; then
    # move 모드: _archived 자신을 제외한 모든 하위를 dst 로 mv
    find "$src" -mindepth 1 -maxdepth 1 ! -name "_archived" -exec mv -t "$dst" {} + || return 4
  else
    # snapshot 모드: cp -r 후 _archived 자신은 복사에서 제외
    find "$src" -mindepth 1 -maxdepth 1 ! -name "_archived" -exec cp -r -t "$dst" {} + || return 4
  fi

  echo "  archived $src → $dst"
  CREATED_ARCHIVES+=("$dst")
}

CREATED_ARCHIVES=()
echo "=== Archive stages ==="
for st in "${ARCHIVE_STAGES[@]}"; do
  if [ -d "$PROJ_ROOT/$st" ]; then
    do_archive "$PROJ_ROOT/$st" "$MODE"
  fi
done

echo ""
echo "=== Archive audit directories ==="
if [ -d "$PROJ_ROOT/99_audit" ]; then
  for st in "${ARCHIVE_STAGES[@]}"; do
    # NN 대응: 01_analysis→01, 02_design→02 etc. 감리 디렉토리 명명 = <NN>_<stage>-audit
    AUDIT_DIR="$PROJ_ROOT/99_audit/${st}-audit"
    if [ -d "$AUDIT_DIR" ]; then
      do_archive "$AUDIT_DIR" "$MODE"
    fi
  done
  # closing audit 도 target-stage 이후 수행된 경우 archive
  CLOSING="$PROJ_ROOT/99_audit/03_closing-audit"
  if [ -d "$CLOSING" ] && [[ "$TARGET_STAGE" < "03_implementation" || "$TARGET_STAGE" == "03_implementation" ]]; then
    do_archive "$CLOSING" "$MODE"
  fi
fi

echo ""
echo "=== Archive RTM (always snapshot) ==="
if [ -d "$PROJ_ROOT/RTM" ]; then
  do_archive "$PROJ_ROOT/RTM" snapshot
fi

echo ""
echo "=== Update rollback-history.md ==="
HIST="$PROJ_ROOT/00_kickoff/rollback-history.md"
if [ ! -f "$HIST" ]; then
  echo "WARN: $HIST 없음 — 먼저 생성 후 재실행" >&2
else
  # 기존 스키마에 Mode 컬럼이 있는지 확인. 없으면 header 갱신 권고만.
  if ! grep -q "| Mode |" "$HIST"; then
    echo "INFO: rollback-history.md header 에 Mode 컬럼이 없습니다. 첫 추가 시 다음 header 로 갱신하세요:" >&2
    echo "| Date | Trigger | Rolled-back to | Archived versions | Mode | Reason |" >&2
    echo "|------|---------|----------------|-------------------|------|--------|" >&2
  fi
  ARCHIVE_LIST=$(printf '`%s`, ' "${CREATED_ARCHIVES[@]}" | sed 's/, $//')
  TODAY=$(echo "$DATE" | sed 's/\(....\)\(..\)\(..\)/\1-\2-\3/')
  NEW_ROW="| $TODAY | (PM 지정 감리 지적 ID) | $TARGET_STAGE | $ARCHIVE_LIST | $MODE | (PM 작성 사유) |"
  echo "" >> "$HIST"
  echo "$NEW_ROW" >> "$HIST"
  echo "  appended row to $HIST"
fi

echo ""
echo "=== 완료 ==="
echo "생성 archive: ${#CREATED_ARCHIVES[@]} 개"
echo ""
echo "다음 작업 (PM 직접):"
echo "  1) $PROJ_ROOT/project-state.md frontmatter current-stage 를 $TARGET_STAGE 로 변경"
echo "  2) Approval Log 에 auto-rollback 행 추가 (Reviewers (count, 정족수): 0, auto-rollback §4-3 예외)"
echo "  3) $HIST 의 Trigger / Reason 컬럼을 구체 사유로 갱신"
