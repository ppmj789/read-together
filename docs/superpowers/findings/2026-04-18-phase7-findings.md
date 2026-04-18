# Phase 7 Findings (v2) — 2026-04-18

## Task 0: Pre-flight

- Worktree: OK (`/home/earth/ai_team_e2e`, branch `phase7-e2e`, working tree clean)
- pytest: 80/80 passed
- File inventory: roles 20, agents 45, PM Skill OK, settings.json OK, `templates/artifacts/_common/*.tmpl` 2개
- `python3 scripts/validate_agent.py --all`: `OK: 66 file(s) validated`
- SessionStart hook: INJECTED — 현 PM 세션이 SessionStart hook 의 `project-manager` SKILL 로드를 통해 시작되었음을 시스템 리마인더로 직접 확인
- Track A Agent-tool probe: YES
  - 명령: `claude -p --append-system-prompt "$(cat .claude/roles/application-director.md)" --model sonnet --effort medium --dangerously-skip-permissions ...`
  - stream-json 파싱 결과 `tool_use_names=['Agent']` (application-director 가 software-architect-sonnet 을 Agent 툴로 호출)
  - 응답 원문: `ADV_RESPONSE: 2`
  - 결론: v2 Track A 경로에서 서브프로세스 세션이 Agent 툴을 보유함 — decision #20 가 현 Claude Code 빌드에서 유효
- Prompt cache probe: HIT
  - 동일 role(`backend-developer.md`)로 `claude -p` 두 회 호출, 5초 간격
  - 첫 호출: `input_tokens=10, cache_creation=61515, cache_read=0, output=179`
  - 두 번째 호출: `input_tokens=10, cache_creation=7510, cache_read=54004, output=245`
  - 결론: 시스템 프롬프트 약 5.4만 토큰이 캐시 재사용됨 — Anthropic prompt cache 가 Track A subprocess 경로에서도 동작 (spec §10 미해결 항목 중 하나 해결)
