# AI SI Project Team

Claude Code 멀티 서브에이전트 시스템으로 엔터프라이즈 SI(System Integration)
프로젝트 실행 조직을 모사한다.

- **현행 설계서**: `docs/superpowers/specs/2026-05-16-no-claude-p-ledger-redesign-design.md`
  (Agent 단일 프리미티브 + ledger 재설계; `2026-04-17-ai-si-team-design.md`
  + Amendment `2026-04-18-amendment-01-claude-p-invocation.md` 를 대체 — 2026-05-16 재설계로 superseded)
- **현행 플랜**: `docs/superpowers/plans/2026-05-16-no-claude-p-ledger-redesign.md`
- 빌드 플랜 (이력): `docs/superpowers/plans/2026-04-17-ai-si-team-build.md`
- Phase 7 E2E (이력): `docs/superpowers/plans/2026-04-18-phase7-e2e.md`
- 호출 매트릭스: `docs/call-playbook.md` — 역할별 호출 규약 §0 (drift-guard 대상)

## Quick Start

1. 프로젝트 디렉토리를 bootstrap 한다 (다음 절 참고).
2. 작업 범위 기술서를 `projects/<name>/00_kickoff/statement-of-work.md` 에 작성한다.
3. 저장소 루트에서 Claude Code 세션을 시작한다 — `SessionStart` hook 이
   `project-manager` Skill 을 자동 로드하며, 해당 세션 자체가 PM 역할을 맡는다.
4. PM 에게 요청한다. PM 은 단일 창구로서 **Agent 툴** — 저작 노드
   (`subagent_type=general-purpose` + 페르소나 주입 + 모델 티어)와
   읽기전용 자문 서브에이전트 (`subagent_type=<role>-<variant>`) — 를
   통해 모든 것을 조율한다.
   모든 위임은 `projects/<name>/ledger/` 에 기록된다.
5. 각 stage gate 에서 PM 이 결과를 보고하고 승인을 기다린다.
6. 감리가 필요한 시점에 PM 이 `scripts/run_audit.sh` 를 실행하면
   격리된 git worktree 를 생성하고 프로젝트를 복사한 뒤 `audit-team`
   general-purpose 노드에 대한 PM dispatch 안내를 출력한다 (`claude -p` 제거됨).

## 신규 프로젝트 bootstrap

```bash
python3 scripts/bootstrap_project.py <project-name> --scale small|large
```

`projects/<project-name>/` 을 v2 계층 트리 전체 구조로 생성한다:

- 단계별 디렉토리: `index.md` + `<ID>.md` 자식 파일
- `project-plan/` 디렉토리 (index + overview/scope/organization/schedule/budget/wbs 자식)
- `RTM/` 디렉토리 (`index.md` + `by-stage/*.md` + `_archived/`; `scale == large` 이면 `by-part/` 추가)
- 최상위 로그: `project-state.md`, `agent-call-log.md`, `escalations.md`,
  `00_kickoff/statement-of-work.md`, `00_kickoff/rollback-history.md`
- `99_audit/` 스켈레톤 (design-audit + closing-audit; `large` 이면 analysis-audit 추가)
- `ledger/` — `index.md` + Dewey 트리 위임 노드 (`A`, `A-1`, `A-1-1`, …)
- `index.md` 의 `child-count` 필드는 실제 내용에 자동 동기화

**프로젝트 산출물은 gitignore 대상** (`.gitignore` 의 `projects/*/`).
이 저장소가 버전 관리하는 것은 플랫폼이며, 특정 프로젝트의 산출물은
버전 관리 대상이 아니다. 스켈레톤 재생성이 필요하면 새 체크아웃에서
제너레이터를 실행한다.

### 프로젝트별 별도 git 저장소 사용 (선택)

PM 이 프로젝트를 `closed` 로 선언한 후, 중첩 `git init` 으로 클라이언트
저장소에 산출물을 push 할 수 있다. 부모 `.gitignore` 가 두 이력을 독립
상태로 유지한다:

```bash
cd projects/<name>
git init && git add -A && git commit -m "initial delivery"
git remote add origin <client-repo-url>
git push -u origin master
```

## 호출 규약 (call-playbook §0)

`claude -p` subprocess 는 **폐기** (2026-05-16). 모든 위임은 현재 세션의
**Agent 툴** 을 단일 프리미티브로 사용한다:

| 노드 유형 | 호출 방법 | 목적 | 툴셋 |
|-----------|-----------|------|------|
| **저작 노드** | `Agent` 툴, `subagent_type=general-purpose` + `.claude/roles/<role>.md` 에서 페르소나 프롬프트 인라인 주입 + `model` 티어 | 주 저작, 자신의 산출물 및 자신의 ledger 노드 직접 작성 | Full (Read/Write/Edit/Glob/Grep/Bash) — 중첩 Agent 없음 |
| **자문 (읽기전용)** | `Agent` 툴, `subagent_type=<role>-<variant>` (`.claude/agents/` shells) | 자문 / 리뷰 / 분석 전용 | `Read, Glob, Grep` (읽기전용, 런타임 고정) |
| **PM Skill** | SessionStart hook 으로 로드되는 `project-manager` Skill | PM 페르소나 — 모든 hop 의 필수 버스; 공유 파일의 단독 기록자 | 세션 툴 계승 (Opus · xhigh 고정) |

`general-purpose` 노드는 Agent 툴을 보유하지 않아 설계상 자기 중첩이
불가능하다 (call-playbook §0-3).

## Ledger 위임 시스템 (spec 2026-05-16 / call-playbook §0-4)

PM 에서 노드로의 모든 위임은 `projects/<name>/ledger/` 에 Dewey 번호
트리(`A` → `A-1` → `A-1-1`)로 기록된다. 각 노드는 `## REQUEST` /
`## RESPONSE` / `## CHILD INDEX` / `## NEXT` 섹션 및 실제 산출물과 RTM ID
링크를 포함하는 자기완결 문서다. `python3 scripts/validate_ledger.py <project>` 가
exit 0 을 반환해야 모든 stage 를 완료로 선언할 수 있다.

## 에이전트 카탈로그

**모델 고정 역할 (8종)**
- `project-manager` — Opus · xhigh · **Skill 전용** (sessionstart 로드, `claude -p` 미사용)
- `application-director` · `infrastructure-director` · `policy-engineer` — Opus · xhigh
- `business-manager` · `quality-assurance` · `tester` — Sonnet · xhigh
- `audit-team` — Sonnet · xhigh · `scripts/run_audit.sh` 경유로만 호출

**동적 모델 역할 (13 × opus/sonnet/haiku = 39 shells)**
- `application-architect` (AA), `software-architect` (SWA),
  `technical-architect` (TA), `data-modeler`
- `part-leader` (`scale == large` 일 때만 활성화)
- `backend-developer`, `batch-developer`, `web-developer`,
  `web-publisher`, `designer`
- `database-administrator` (DBA), `security-specialist`,
  `infrastructure-engineer`

상위 호출자가 작업 난이도에 따라 변형을 선택한다 (spec §2-3 난이도 가이드).
위임 체인에서 한 단계 이상 낮은 모델을 강제로 지정하지 말 것.

소스 트리:
- `.claude/roles/<role>.md` — 단일 소스 페르소나 (역할당 1개, 모델 접미사 없음)
- `.claude/agents/<role>-<variant>.md` — 역할에서 파생된 자문 (읽기전용) shells
- `.claude/skills/project-manager/SKILL.md` — PM skill shell

## 산출물 템플릿

단계별·역할별 산출물 스켈레톤은 `templates/artifacts/` 를 참고:

- `_common/` — `index.md.tmpl` + `child.md.tmpl` (모든 계층 영역 공통)
- `change-requests/` — `cr-request` / `cr-impact-analysis` / `cr-decision` / `cr-action-result` / `index`
- `audit/` — `audit-plan` + `finding` (`pm-classification` A/B/C/D 필드 포함)
- `rtm/` — `index` + `by-stage` 템플릿
- `ledger/` — `node.md.tmpl` (REQUEST/RESPONSE/CHILD INDEX/NEXT 스켈레톤) + `index.md.tmpl`
- 최상위 로그 — `project-state` / `agent-call-log` / `escalations` / `review-meeting` / `rollback-history` / `statement-of-work`

모든 템플릿은 필수 frontmatter 스키마를 포함하며, 위반은 아래 validator 가 검출한다.

## Stage Gates

`templates/stage-gates.md` 는 단계별로 필수 산출물, 리뷰, 자문 게이트
(`business-manager` + `quality-assurance` 협의 기록을 `agent-call-log.md` 에
남길 것), RTM 입력, 감리, 계층 게이트, 승인 게이트를 열거한다.

"Hierarchy gate" 항목은 `validate_artifact_hierarchy.py` 가 exit 0 을
반환하고, 역참조가 변경된 경우 `sync_back_references.py` 가 clean 을
보고해야 통과된다.

"Ledger-completeness gate" 는 `python3 scripts/validate_ledger.py <project>`
가 exit 0 을 반환해야 하며, RESPONSE 가 없는 open REQUEST 노드가 있으면
stage 완료가 차단된다.

## 검증·헬퍼 스크립트

```bash
# Agent frontmatter 스키마 + 역할/플레이북 drift-guard
python3 scripts/validate_agent.py --all

# v2 계층: index.md 존재, 양방향 의존성, 3-hop 깊이,
# group-ID 참조, orphan 자문, audit-advisory 완화
python3 scripts/validate_artifact_hierarchy.py <project>

# Frontmatter 완전성 (id/title/owner/depends-on/referenced-by + version 정규식 + 중복 키 탐지)
python3 scripts/check_frontmatter.py <project>

# 변경 요청 사이클 완전성 (CR-<seq>/ 5개 파일, 템플릿별 스키마)
python3 scripts/validate_cr.py <project>

# depends-on 선언에서 referenced-by 역참조 동기화
python3 scripts/sync_back_references.py <project>

# index.md child-count 필드를 실제 내용에 동기화 (bootstrap 시 자동 실행)
python3 scripts/sync_child_count.py <project>            # write
python3 scripts/sync_child_count.py <project> --check    # dry-run, 드리프트 시 exit 1

# Type-A 분류 FIND-*.md 상태를 raised → resolved 로 전환
python3 scripts/close_audit_findings.py <project> <cycle-id>

# 신규 프로젝트 bootstrap (종료 시 child-count 자동 동기화)
python3 scripts/bootstrap_project.py <name> --scale small|large

# 역할 템플릿에서 동적 변형 agent shell 39개 재생성
python3 scripts/derive_dynamic_agents.py

# 감리 실행기 (worktree 생성 + 프로젝트 복사 + PM dispatch 안내 출력;
# claude -p 제거됨 — PM 이 audit-team 을 general-purpose 노드로 dispatch)
scripts/run_audit.sh <project> <cycle-id> <prompt-file>

# Ledger 완전성: 모든 REQUEST 노드에 RESPONSE 필요 (stage gate)
python3 scripts/validate_ledger.py <project>

# 롤백 헬퍼 (MOVE vs SNAPSHOT 모드 — §4-3)
scripts/execute_rollback.sh <project> <stage> <mode>

# 전체 테스트 스위트 실행
python3 -m pytest -q
```

작성 시점 기준: **169개 테스트 통과 · `validate_agent --all` 68/68 clean**.

## Phase 7 E2E 결과 (2026-04-19)

Phase 7 에서는 이 시스템으로 `book-mgmt-api` 샘플 프로젝트를 처음부터
끝까지 실행하고, 감리를 두 차례 진행(D-AUDIT-1 통과, C-AUDIT-1 통과)한
뒤 다섯 가지 메타테스트(Task 14–18)를 수행했다. 3차례 파동에 걸쳐
42개의 구조 개선이 master 에 반영되었다:

- Phase 7 잔여 발견 목록(`#1`–`#19`)에서 14개
- 원시 로그 / 리뷰 / 산출물 메타데이터 스캔(`N1`–`N20`)에서 20개
- Part B 메타테스트(`C-18-1/2`, `C-17-1/2`, `C-14-1/2/3`, `C-18-3`)에서 8개

주요 구조 추가 사항:
- **공유 파일 단독 수정 규칙** (spec §7-2) — `project-state.md`,
  `RTM/`, `agent-call-log.md`, `escalations.md`, 디렉토리 index 파일은
  PM 전용 기록 대상이며, subprocess 는 직접 수정 대신 에스컬레이션.
- **`--add-dir` 범위 한정** (call-playbook §0) — subprocess 는 자신이
  저작하는 디렉토리만 부여받아 병렬 쓰기 경합 제거.
  (2026-05-16 `claude -p` 폐기로 대체 — 현행 아님)
- **롤백 MOVE/SNAPSHOT 모드** (`scripts/execute_rollback.sh`).
- **감리 발견 분류** `pm-classification` frontmatter 필드의 A/B/C/D 값;
  Type-A 는 `scripts/close_audit_findings.py` 로 `resolved` 전환.
- **중첩 Track A 깊이 가드** — 4-레벨 체인 권장; 더 깊은 체인은
  `condensed-brief.md` 를 통과해야 함 (95 % 캐시 히트만으로는 4레벨
  이후 컨텍스트 보존 불충분).
  (2026-05-16 `claude -p` 폐기로 대체 — 현행 아님)

전체 보고서: `docs/superpowers/findings/2026-04-18-phase7-findings.md`
및 `docs/superpowers/findings/2026-04-19-phase7-part-b-findings.md`.

## Role realignment (2026-05-02)

한국 SI 통념 정합을 위해 두 차례 페르소나·디렉토리·dispatch 재정비를 진행
(2 × 5-commit 시리즈). 현재 master 는 다음 흐름이 반영된 상태:

**아키텍트 3종 분담** (`02_design/architecture/`) — application-architect 가
`application/` (overview·domain-model·business-flow·components/CMP-* + ADR)
을, software-architect 가 같은 application/ 안에 code-architecture·module-
patterns·interface-policy + ADR 을, technical-architect 가 좁은 `technology/`
(overview·middleware·deployment-topology·nfr-technology + ADR) 을 저작.
data-modeler 는 `data/`, security-specialist 는 `security/`. Clean
Architecture 기본 채택 ADR 은 SWA 단독 책임. validate_artifact_hierarchy.py
가 subdomain 별 owner 정합을 검증한다.

**웹 직군 흐름** (`02_design/design-system/`, screens, src/web/) —
designer 가 `design-system/` (overview·colors·typography·layout·logo-brand)
단독 저작, web-developer 가 `screens/SCN-*.md` 단독 저작 (한국 SI 통념),
web-publisher 는 02_design 저작 책임 없이 03_implementation 단계에서
SCN+design-system 을 입력받아 `src/web/` HTML 마크업·CSS 껍데기를 단독
저작 (web-developer 의 동적 기능·API 연동 추가 전 선행). validator 가
design-system owner=designer 정합을 검증한다.

상세는 `git log --oneline 3c23e5e..HEAD` 의 `feat(roles)` /
`feat(architecture)` / `feat(design-system)` / `feat(directors)` /
`feat(validator)` 커밋 시리즈를 참고.

## Exception-handling ratio policy (2:8 법칙, 2026-05-02)

단위기능 차원에서 **정상 ≤ 2 : 비정상 예외 처리 ≥ 8** 비율을 자연스럽게
도출하도록, 단계별 산출물 형태에 맞춰 강제하는 통합 정책을 신설.
SSOT: `docs/exception-handling-ratio-policy.md`.

| 단계 | 강제 강도 | 핵심 메커니즘 |
|------|---------|----------|
| 요구사항 | 약 (발견) | 7 Failure Categories 카테고리 커버리지 (AA RQ enumerate) |
| 설계 | 중 (메커니즘) | PRG/IF/SCN/BATCH 본문 FMEA 표 의무 + 3 불변식 (Tree·One-handler·Guard chain) |
| 단위테스트 | **강 (숫자)** | UT-*.md frontmatter `variant-happy-count / variant-count ≤ 0.3`, `variant-exception-count / variant-count ≥ 0.7`, `validate_artifact_hierarchy.py` 가 자동 검증 |
| 구현 | 간접 | TDD 자연 도출 + One RPC = one handler + precondition guard chain + 코드 헤더 카테고리 명시 |
| 통합테스트 | 기존 | Variant Multiplication |

비율 강제의 진앙지는 단위테스트 설계 — 요구사항 단계에 숫자를 들이대면
"가짜 예외" 양산. parent-variant 트리 구조 (1 UT = 1 PRG = N variants)
로 산출물 폭증을 차단하면서 enumeration 은 보존.

## Project-fit hook generation (2026-05-02)

하네스의 통제력은 자연어 가이드보다 코드(validator)가 강력하다는
원칙에 따라, **WBS 승인 시점에 프로젝트 fit 한 검증 hook 을 자동 생성**
하는 메커니즘을 도입. 단계:

1. PM 이 SOW·WBS·project-plan 을 분석해 후보 hook 5–8 건을 추천
2. PM 이 사용자에게 후보 제시 → 사용자 선택·추가·제외 합의
3. PM 이 합의 명세를 `policy-engineer-opus` 에 general-purpose 노드 dispatch (call-playbook §0-1)
4. policy-engineer 가 `projects/<name>/scripts/` 에 디스패처 + 개별
   hook + manifest 저작 (Python 표준 라이브러리만, 결정론, 읽기 전용,
   exit 0/1/2 규약)
5. PM 이 매 stage 종결 보고 직전 `bash projects/<name>/scripts/
   run_project_hooks.sh <stage>` 자동 호출 — 비0 exit 시 PASS 보고 보류

신규 페르소나 `policy-engineer` 는 fixed Opus·xhigh — 검증 hook 은 한
번 잘못 만들면 stage-gate 전체가 망가지는 통제 장치라 모델 변동성을
제거. bootstrap 은 placeholder 디스패처(INFO + exit 0) 와 빈 매니페스트를
시드하므로, hook 미생성 상태에서도 stage-gate 가 동작 (Hook Generation
gate 미완 시는 stage 종결 자체 금지).
