#!/bin/bash
# scripts/run_audit.sh — PM helper: isolated git worktree 생성 + PM dispatch 안내 출력.
#
# 신 계약 (Track A 직접 호출 폐기 이후):
#   감리는 PM 이 Agent 툴로 general-purpose + audit-team 페르소나로 dispatch.
#   run_audit.sh 는 (1) worktree 격리·프로젝트 복사, (2) PM 안내 출력,
#   (3) 복사 결과 안내만 담당. claude 직접 실행은 하지 않는다.
#
# Usage:
#   scripts/run_audit.sh <project> <cycle-id> <prompt-file>
#
#   <project>     — project name under projects/, e.g., my-project
#   <cycle-id>    — audit cycle dir name, e.g., 02_design or 03_closing
#   <prompt-file> — absolute path to a text file with the audit prompt
#
# Behavior:
#   1. Locate main worktree root (the one this script lives in).
#   2. Locate master repo path (first line of `git worktree list`).
#   3. Create a dedicated audit worktree:
#        path:   <parent>/<main-name>_audit_<cycle>
#        branch: <current-branch>-audit-<cycle>-<timestamp>
#   4. Copy <main>/projects/<project>/ into the audit worktree.
#   5. Print PM dispatch guidance: Agent 툴로 general-purpose + audit-team 페르소나 호출.
#   6. (선택) 감리 완료 후 결과를 main 트리로 복사하는 안내 출력.
#
# Exit codes:
#   0   success (worktree 준비 완료, PM 안내 출력)
#   2   bad args / paths

set -euo pipefail

if [ $# -lt 3 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'USAGE'
Usage: scripts/run_audit.sh <project> <cycle-id> <prompt-file>

  <project>     project under projects/ (e.g., my-project)
  <cycle-id>    audit cycle dir name (e.g., 02_design, 03_closing)
  <prompt-file> path to text file containing the audit prompt

Creates an isolated git worktree and copies the project into it, then
prints PM dispatch guidance. Audit execution is done by the PM via
Agent tool (general-purpose + audit-team persona) — this script does
NOT invoke claude directly.
USAGE
  [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] && exit 0 || exit 2
fi

PROJECT="$1"
CYCLE="$2"
PROMPT_FILE="$3"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MAIN_NAME="$(basename "$MAIN_ROOT")"
PARENT_DIR="$(dirname "$MAIN_ROOT")"

PROJECT_DIR="$MAIN_ROOT/projects/$PROJECT"
ROLE_FILE="$MAIN_ROOT/.claude/roles/audit-team.md"

[ -d "$PROJECT_DIR" ] || { echo "ERROR: project not found: $PROJECT_DIR" >&2; exit 2; }
[ -f "$PROMPT_FILE" ] || { echo "ERROR: prompt file not found: $PROMPT_FILE" >&2; exit 2; }
[ -f "$ROLE_FILE" ]    || { echo "ERROR: audit-team role file not found: $ROLE_FILE" >&2; exit 2; }

MASTER_PATH="$(git -C "$MAIN_ROOT" worktree list | head -1 | awk '{print $1}')"
CUR_BRANCH="$(git -C "$MAIN_ROOT" branch --show-current)"

WT_PATH="$PARENT_DIR/${MAIN_NAME}_audit_${CYCLE}"
WT_BRANCH="${CUR_BRANCH}-audit-${CYCLE}-$(date +%Y%m%d-%H%M%S)"

if [ -d "$WT_PATH" ]; then
  echo "ERROR: audit worktree path already exists: $WT_PATH" >&2
  echo "Remove with:  git -C $MASTER_PATH worktree remove --force $WT_PATH" >&2
  exit 2
fi

LOG="/tmp/run_audit_${CYCLE}_$(date +%Y%m%d-%H%M%S).log"
echo "audit worktree: $WT_PATH (branch $WT_BRANCH)"

git -C "$MASTER_PATH" worktree add "$WT_PATH" -b "$WT_BRANCH" "$CUR_BRANCH" >"$LOG" 2>&1

cp -r "$MAIN_ROOT/projects" "$WT_PATH/"

cat <<EOF
[run_audit] worktree 준비 완료: $WT_PATH

다음을 PM 세션에서 수행하라:
  Agent 툴  subagent_type=general-purpose, model=sonnet
  system    .claude/roles/audit-team.md 전문을 system prompt 로 전달
  prompt    내용:
    - 감리 대상 worktree 경로: $WT_PATH/projects/$PROJECT
    - 산출물 경로: $WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit/
    - 감리 prompt 파일: $PROMPT_FILE

감리 완료 후 결과를 main 트리로 복사:
  SRC: $WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit/
  DST: $MAIN_ROOT/projects/$PROJECT/99_audit/${CYCLE}-audit/
  명령: cp -r "$WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit" \\
             "$MAIN_ROOT/projects/$PROJECT/99_audit/"

  (worktree root 에 작성된 경우 fallback):
  SRC_FALLBACK: $WT_PATH/99_audit/${CYCLE}-audit/
EOF

SRC="$WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit"
SRC_FALLBACK="$WT_PATH/99_audit/${CYCLE}-audit"
DST="$MAIN_ROOT/projects/$PROJECT/99_audit/${CYCLE}-audit"

# 감리 실행 전이므로 결과가 아직 없을 수 있다 — 있으면 복사, 없으면 안내만.
copied_from=""
if [ -d "$SRC" ] && [ -n "$(ls -A "$SRC" 2>/dev/null | grep -v '^index.md$' || true)" ]; then
  mkdir -p "$DST"
  cp -r "$SRC"/. "$DST"/
  copied_from="$SRC"
elif [ -d "$SRC_FALLBACK" ]; then
  # Fallback path (Phase 7 Task 10 finding #18): audit output found at worktree root.
  echo "WARNING: audit output found at fallback path $SRC_FALLBACK" >&2
  echo "         expected $SRC. run_audit.sh will copy from fallback — please confirm." >&2
  mkdir -p "$DST"
  cp -r "$SRC_FALLBACK"/. "$DST"/
  if [ -d "$SRC" ]; then
    cp -rn "$SRC"/. "$DST"/ 2>/dev/null || true
  fi
  copied_from="$SRC_FALLBACK"
elif [ -d "$SRC" ]; then
  mkdir -p "$DST"
  cp -r "$SRC"/. "$DST"/
  echo "WARNING: audit output at $SRC appears to be only seed files — audit may not have run yet" >&2
  copied_from="$SRC (seed-only)"
fi

if [ -n "$copied_from" ]; then
  echo "audit results copied to: $DST"
  echo "  (source: $copied_from)"
else
  echo "audit output not yet present — run Agent dispatch first, then copy manually."
fi

exit 0
