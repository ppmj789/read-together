#!/bin/bash
# scripts/run_audit.sh — PM helper to dispatch audit-team in an isolated git worktree.
#
# Solves Phase 7 ergonomics issue: original spec required the human user to
# manually create the audit worktree, copy artifacts, and invoke claude -p with
# the audit-team role. With this helper, the PM Skill session can do the entire
# flow inside a single Bash call.
#
# Usage:
#   scripts/run_audit.sh <project> <cycle-id> <prompt-file>
#
#   <project>     — project name under projects/, e.g., book-mgmt-api
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
#   5. Invoke `claude -p` with the audit-team role and CORRECT argument order:
#         --add-dir <path>  ← MUST come before --append-system-prompt (Phase 7 finding).
#   6. Copy 99_audit/<cycle>-audit/ back to the main worktree.
#   7. Print the absolute path of the audit-report directory.
#
# Exit codes:
#   0   success
#   2   bad args / paths
#   *   propagated from `claude -p`

set -euo pipefail

if [ $# -lt 3 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'USAGE'
Usage: scripts/run_audit.sh <project> <cycle-id> <prompt-file>

  <project>     project under projects/ (e.g., book-mgmt-api)
  <cycle-id>    audit cycle dir name (e.g., 02_design, 03_closing)
  <prompt-file> path to text file containing the audit prompt

Creates an isolated git worktree, runs audit-team Track A inside it
(with --add-dir before --append-system-prompt to avoid argument parsing
issues), and copies 99_audit/<cycle>-audit/ back to the main worktree.
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
echo "audit-team log: $LOG"
echo "audit worktree: $WT_PATH (branch $WT_BRANCH)"

git -C "$MASTER_PATH" worktree add "$WT_PATH" -b "$WT_BRANCH" "$CUR_BRANCH" >"$LOG" 2>&1

cp -r "$MAIN_ROOT/projects" "$WT_PATH/"

PROMPT="$(cat "$PROMPT_FILE")"
ROLE="$(cat "$ROLE_FILE")"

cd "$WT_PATH"
set +e
claude -p \
  --output-format stream-json --verbose \
  --model sonnet --effort xhigh \
  --dangerously-skip-permissions \
  --add-dir "$WT_PATH/projects/$PROJECT" \
  --append-system-prompt "$ROLE" \
  "$PROMPT" >>"$LOG" 2>&1
RC=$?
set -e

SRC="$WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit"
DST="$MAIN_ROOT/projects/$PROJECT/99_audit/${CYCLE}-audit"

if [ -d "$SRC" ]; then
  mkdir -p "$DST"
  cp -r "$SRC"/. "$DST"/
  echo "audit results copied to: $DST"
else
  echo "WARNING: no audit results at $SRC — audit may have failed (exit $RC)" >&2
fi

echo "audit-team exit code: $RC"
exit $RC
