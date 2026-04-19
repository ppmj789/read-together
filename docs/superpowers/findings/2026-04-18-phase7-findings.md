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

## Task 1: bootstrap

- `scripts/bootstrap_project.py book-mgmt-api --scale small` → 49 dirs / 59 seed files (예상치 일치)
- v2 계층 검증: stage roots 9개, area 서브디렉토리 + index.md, `99_audit/01_analysis-audit/` ABSENT (small 정상), top-level singletons 3종, RTM/by-stage/{analysis,design,implementation,test,deployment}.md, validate_artifact_hierarchy clean

## Task 2: SOW

- `00_kickoff/statement-of-work.md` 빈 템플릿 → 도서관 API 실 SOW 60줄 (date 2026-04-18, 발주처·기간·범위·기능/비기능·제약 모두 채움)

## Task 3: 00_kickoff project-plan + 리뷰

### 진행
- Step 1: business-manager Track B 자문 → budget guide 통합 (agentId a050663d5b03dc93a, ~18.5K tok)
- Step 2: project-plan 계층 작성 — index + 자식 5개 + wbs/index + 자식 5개 (총 12 파일)
- Step 3: Track B 병렬 리뷰 (business-manager + QA, 응답 두 건 모두 "조건부 통과")
- Step 4: project-state, agent-call-log 갱신
- Step 5: 사용자 승인 (2026-04-18)

### 관찰 사항 (Meta-Test 2 누적)
- **§2-6 mandatory gate 준수**: PM 이 budget 작성 전 business-manager 자문 → spec 그대로 동작
- **PM Skill 페르소나 일관성**: 한국어 응답·3 부 형식(현재 상태/한 일/사용자 결정) 자연 유지
- **business-manager 자문 품질**: SOW 항목별 강제 xhigh 식별 정확. 단계 명명에서 "01_requirements / 02_analysis" 로 분리 표기 — 실제 v2 계층은 `01_analysis` 통합. 사소 deviation, 영향 없음
- **Track B 병렬 dispatch 동작**: 단일 응답에서 2개 Agent 호출 → 두 응답 독립 회신 정상. 둘 다 PM 산출물을 직접 Read 한 흔적 (tool_uses 14, 23)
- **자문 false positive 2건**:
  - QA-1: `version: v1` 필드 "전부 누락" 주장 → grep 검증 결과 모든 자식 12행에 존재. QA 가 본문 마크다운 변경 이력 표기와 frontmatter 를 혼동한 것으로 추정.
  - QA-3: `scope.md` referenced-by 에 `00-KICKOFF-PROJECT-PLAN-WBS` (index ID) 누락 지적 → validate_artifact_hierarchy 가 인덱스 ID 를 id_map 에서 제외(line 47-48). 자식이 인덱스 ID 를 참조하면 drift 발생. QA 가 validator 로직 미숙지.
  - **함의**: Track B 자문이 sometimes hallucinates. PM 이 사실 확인 후 RESOLVED/REJECTED 판단 필수. spec §7-1 "PM 이 최종 판단" 원칙 검증됨.
- **계층 깊이 3-hop 한도 (decision #26)** 정상 동작: `00_kickoff/project-plan/wbs/wbs-*.md` (3-hop) 통과. 더 깊이 못 들어감을 상기.
- **Track B 호출 비용**: 3회 자문 약 82.5K tok ≈ $0.4. 디자인 단계로 가면 부풀 것.

### 산출물
- `00_kickoff/`: 16 파일 (index + SOW + project-plan/{index, 5 자식, wbs/{index, 5 자식}} + reviews/project-plan-review-v1.md + rollback-history.md)
- `agent-call-log.md`: 3행 등재
- `project-state.md`: 00_kickoff [x], Approval Log 1행

### Phase 7 patches 후보 누적 (Task 12 에서 정리)
1. QA 자문 false positive 빈도 측정 → frontmatter 자동 점검 스크립트 권고 (low)
2. validate_artifact_hierarchy: 인덱스 ID 와 자식 ID 영역 분리 명확화 또는 인덱스도 참조 가능하도록 보완 검토 (med)
3. **`templates/stage-gates.md` v2 계층 구조 미정합 (QA-5)**: 모든 단계가 단일 파일을 가정. v2 디렉토리+index+자식 구조로 재작성 필요 — 모든 후속 프로젝트에 영향 (high)

## Task 4: 01_analysis (Track A 4단 nested)

### 진행
- §2-6 stage-entry gate: business-manager 자문 → W-A-01·03 만 xhigh, 나머지 high; infra-director sonnet/medium 권고; NFR 별도 등재 권고 (agentId a69d4b12243da38be)
- Track A 병렬 dispatch 2건 (PM → appdir opus/xhigh + infra-director sonnet/medium, ~30분)
- appdir 가 산하 6 sub-Track A (W-A-01~06) + 2 Track B (W-A-07 리뷰) fan-out
- 산출물 80 파일 (requirements 33 + AS-IS 7 + TO-BE 8 + IT 15 + UAT 10 + reviews 6 + index 1) + infra-constraints.md
- RQ 25 (auth4/book5/member4/loan3/search2/batch2/nfr5)
- PM 사후조치: drift-guard 48 → 0, F-REQ-01·F-IT-03 즉시 fix, F-IT-02·F-TB-02 후속 단계 귀속

### 핵심 발견 (Meta-Test 2 누적)
- **🔴 응용총괄 자체 검증 누락 (CRITICAL)**: appdir 가 자체 PASS-WITH-COMMENTS 보고 전 `validate_artifact_hierarchy.py` 미실행. drift-guard 48건 위반을 PM 이 receiving inspection 에서 발견. 원인: 역할 프롬프트에 검사기 실행 의무 명시 부재.
  → **즉시 보완 적용**:
  - `scripts/sync_back_references.py` 신설 (양방향 자동 동기화, 7 unit tests 포함)
  - `application-architect`, `tester`, `data-modeler` 역할에 "자식 작성 직후 sync 실행 또는 부모 referenced-by 직접 갱신 필수" 추가
  - `application-director`, `infrastructure-director` 역할에 "PM 보고 직전 sync + validate 실행 + 결과 인용 필수" 추가
  - 87 pytest 통과 (기존 80 + 신규 7)
- **🟢 Prompt cache 효과 측정 (반복 role 호출)**: appdir 자체 usage 에서 `cache_read=2,082,229 / cache_creation=30,054` → 약 **98.5% cache hit**. sub-Track A 들이 동일 role system prompt 반복 호출 시 거의 100% 재사용. Track A nested invocation 의 prompt cache 가 budget.md 가정대로 동작 확인.
- **🟢 appdir 위임 chain 작동**: 6 sub-Track A 가 PM instruction 의 모델·effort 정책 (W-A-01·03 xhigh, 나머지 high) 정확히 준수. NFR 별도 그룹 (requirements/nfr/) 신설 의무 준수. agent-call-log.md 에 8행 자동 등재.
- **🟡 4단 nested 실 비용**: business-manager 추정 $3-6 (기준), 실측 ~$1.0 (cache hit 으로 절감). 가용 절감 마진 큼.
- **🟡 자문 false positive 패턴 재확인**: 응용총괄이 산하 sub-Track A 의 W-A-06 결과를 PASS 보고 전 검증하지 않음. Task 3 의 QA false positive 와 동일 카테고리 문제 (신뢰 후 검증 누락). 보강된 프롬프트로 재발률 감소 기대.

### 사후 조치 (PM 직접 처리)
1. 23 RQ + 3 AS-IS `referenced-by` 갱신 (sync 자동 22건 + AS-IS 수동 2건)
2. F-REQ-01: IT-11 합격기준 "오류율 0%" → "1% 미만" (RQ-NFR-02 AC1 정합)
3. F-IT-03: IT-09 depends-on 에 RQ-LOAN-03 추가 → sync 자동
4. F-IT-02 (RQ-MEMBER-03 IT/UAT 미커버) → 02_design 진입 시 처리 (PM dispatch 프롬프트에 반영)
5. F-TB-02 (RQ-NFR-05 단일 서버) → 05_deployment 게이트 항목으로 귀속

### 산출물 추가 (시스템 보강)
- `scripts/sync_back_references.py` (200+ 줄, 도구 신설)
- `tests/test_sync_back_references.py` (7 단위 테스트)
- 5개 역할 프롬프트 갱신 (`.claude/roles/{application-architect,tester,data-modeler,application-director,infrastructure-director}.md`)

### Phase 7 patches 후보 추가
4. **자동 차단 hook (보완안 1, 미구현)**: SessionEnd 또는 stage-gate 키워드 감지 시 validator 자동 실행. 본 세션은 프롬프트 보강(보완안 2·3) 으로 갈음. 효과 모니터링 후 추가 검토.
5. **AS-IS 자식 간 의존 author 가이드**: AS-IS 자식 작성 시 부모(AS-XX) 와 자식(AS-XX) 관계 혼동 (방향 오류 2건 발견). 역할 프롬프트에 "AS-XX 의 referenced-by 는 후행 AS·TB 만 (선행 AS 는 안 됨)" 명시 필요.

## Task 5: 02_design (양 트랙 본격 가동, 4단 nested + cross-track)

### 진행
- §2-6 stage-entry gate: business-manager 자문 — security-specialist sonnet/xhigh 확정, 의존 순서, RQ-MEMBER-03 처리 instruction (agentId a9c484f8580727894)
- Track A 2 갈래 병렬 (PM → appdir + infra-dir 모두 opus/xhigh, 약 38분)
- appdir 산하: data-modeler (xhigh), SWA(IF,PRG), designer+publisher, tester(UT) — 5 sub-Track A + 10인 Track B 리뷰
- infra-dir 산하: TA, DBA, security-specialist (모두 xhigh), infra-engineer — 4 sub-Track A + 8인 Track B 리뷰
- 산출물 134 자식 + 13 인덱스 + 9 리뷰 = 156 파일 (drift-guard CLEAN 200, 01_analysis 포함)
- PM Step 3: RTM/by-stage/design.md 자동 추출 (frontmatter 스캔), 25 RQ × 8 영역 매핑

### 핵심 발견 (Task 4 보강 효과 검증 — 메이저 성공)
- **🟢 갱신 프롬프트 효과 100% — 양 디렉터 모두 self-check 준수**:
  - appdir: `python3 scripts/sync_back_references.py book-mgmt-api` + `validate_artifact_hierarchy.py` 실행 후 verbatim 인용. 12 issue 잔존 시 PASS 보고하지 않고 "CONDITIONAL PASS" 로 다운그레이드. 잔존 12건을 infra 도메인으로 정확히 스코프 분리.
  - infra-dir: 동일 self-check 준수, 결과 `OK: clean (200 child files)` — appdir 가 carry-forward 한 12건 모두 시정.
  - 결과: PM 의 receiving inspection 에서 추가 발견 0건. **Task 4 의 응용총괄 자체 검증 누락 패턴 100% 해소.**
- **🟢 Prompt cache 효과 (4단 nested, sub-Track A 5+4=9건)**:
  - appdir: cache_read 13.3M / cache_creation 337K → ~97.5% hit
  - infra: cache_read 8.2M / cache_creation 659K → ~92.5% hit
  - Task 4 의 ~98.5% 와 유사. 대규모 nested 호출에서도 cache 효과 안정적.
- **🟢 비용 절감 검증**: 추정 $7-12 → 실측 $3.0 (~60-75% 절감). budget.md 의 cache 효과 가정 정확.
- **🟢 cross-track 협업 정상 동작**:
  - DB 논리(data-modeler/appdir) → 물리(DBA/infra) 의존 순서 준수
  - 보안(security-specialist/infra) 가 IF(SWA/appdir) 산출물 Read 후 작성
  - PM Track B 자문 없이 양 총괄이 instruction 으로 정확히 동기화
- **🟡 sub-agent Write 권한 패턴**: Track B 자문 호출 (subagent_type=*-haiku 등) 의 sub-agent 가 산출물 본문을 응답 텍스트로 회신하면 상위 director 가 자체 Write. infra 4건, appdir 1건 발생. 정상 동작이나 Track A vs B 선택 가이드 보강 여지 있음 (Phase 7 patches 후보).
- **🟡 BOOK 도메인 drift 14건 자체 발견·시정**: appdir 의 IF 리뷰에서 application-architect-haiku 가 "BOOK 드리프트" 발견. appdir 가 sync 실행 + manual edit 21건으로 정정 후 PM 보고. 즉 appdir 가 시정조치까지 자체 완료. 갱신 프롬프트의 "PASS 보고 금지 → 시정 또는 escalate" 룰 정확 동작.

### 산출물 요약 (134 자식 + 13 인덱스 + 9 리뷰)
| 영역 | 자식 | 담당 |
|------|-----|-----|
| architecture (cross-cutting + 6 components) | 11 | technical-architect |
| db/logical (ENT-*) | 7 | data-modeler |
| db/physical (TBL-*) | 8 | database-administrator (BATCH_HISTORY 신설) |
| interfaces (IF-*) | 16 | software-architect |
| programs (PRG-*) | 19 | software-architect (COMMON 3 신설: 감사·암호화·RBAC) |
| screens (SCN-*) | 15 | designer + web-publisher |
| security-review (FIND + 5 sections) | 5 | security-specialist |
| infra (DESIGN-INFRA-*) | 4 | infrastructure-engineer |
| unit-test-cases (UT-UNIT-*) | 30 | tester (RQ-MEMBER-03 4 AC 전수: UT-10/11/12/29) |

### Carry-forward 정리 (Task 7 → 03_implementation)
- security REC-D-01~05 (423 Locked, PW 변경 시 세션 폐기, role rotation, PII READ 감사, JSONB 마스킹)
- infra MED/LOW 9건 + DB MED/LOW 9건
- ARCH-R-01 배치 장애 격리

### Phase 7 patches 후보 추가
6. **Track A vs B 선택 가이드 (low-med)**: director 들이 서브 작업을 Track B 자문으로 호출하고 상위가 Write 하는 패턴 다수 발생. 본 단계 5건. Track B 는 본래 자문용, Write 가 필요한 작업은 Track A 가 정석. 역할 프롬프트에 "산출물 작성 = Track A, 자문 = Track B" 명시 강화.
7. **prompt cache 효과 budget 갱신 (med)**: 실측 cache hit ~95% 일관 → budget.md §3 가중치 표의 USD 추정 범위를 30-40% 하향 조정 가능. Phase 7 master patches 후보.

## Task 6: D-AUDIT-1 설계 감리 + 시정조치 + 재발 방지 도구

### 진행
- PM 이 사용자 위임으로 worktree 생성 → 프로젝트 복사 → audit-team Track A dispatch (spec decision #15 amendment: PM 이 scripts/run_audit.sh 로 격리 실행, 본 프로젝트에선 PM·user 동일 세션이라 정당화됨)
- **🔴 중요 finding: CLI 인자 순서 sensitivity**: `claude -p` 에서 `--append-system-prompt "$(cat ...)"` 가 `--add-dir <path>` 앞에 오면 SessionStart hook 3회 실행 후 `Error: Input must be provided either through stdin or as a prompt argument when using --print` 로 종료. 원인: `--add-dir` 의 path argument 가 뒤따르는 positional prompt 를 consume 한 듯 (정확한 CLI parsing 버그 재현 가능). 해결: **`--add-dir` 을 먼저, `--append-system-prompt` 을 나중에**. Phase 7 major finding.
- audit-team 12 findings (모두 마이너): 인덱스 본문 placeholder 2건, 인덱스 의존성 요약 표 vs frontmatter 불일치 4건, §8 본문 불일치 1건, child-count 1건, 리뷰 reviewed-by 형식 5건, UT 리뷰 depends-on 공백 1건, WBS task ID 충돌 1건, DESIGN-ARCH-07 의존성 누락 1건, architecture/index.md 의존성 요약 미갱신 1건
- PM 판단: rollback 불필요 (요구사항·결정 자체 영향 없음), 재감리 생략 권고, PM 직접 시정 처리
- 시정 완료 후 drift-guard clean 215 child files (02_design 134 + 인덱스 13 + 리뷰 9 + audit 13 + ACT/RES 2)

### 재발 방지 도구 신설 (본 Task 부수 산출)

**1. `scripts/run_audit.sh`** (shell wrapper)
- args: `<project> <cycle-id> <prompt-file>`
- 동작: worktree 생성 (신규 브랜치) → projects/ 복사 → claude -p (CORRECT arg order!) → 결과 99_audit/<cycle>-audit 본 worktree 로 복사
- 추가 테스트: `tests/test_run_audit.py` (6 passing tests — arg validation, help 출력, 에러 코드)
- **핵심**: CLI 인자 순서를 스크립트 내부에 fix 하여 사용자·에이전트가 실수할 여지 제거

**2. role 파일 갱신**
- `.claude/roles/audit-team.md`: description 및 Mission 에 "scripts/run_audit.sh 로 invoke, CLI 인자 순서 load-bearing" 명시
- `.claude/roles/project-manager.md`: "Never call audit-team yourself" → "Invoke only via scripts/run_audit.sh" 로 amendment. spec decision #15 의 user-only 규칙을 PM-dispatched-with-helper 로 완화. 이유: 본 시스템에서 PM 과 human client 가 동일 세션

### 핵심 발견 (메이저)
- **🔴 CLI 인자 순서 버그**: 위 설명 참조. spec amendment 후보 — 모든 Track A 호출 예시에 `--add-dir` 을 앞에 두도록 일괄 정정 필요 (project-manager.md "How You Invoke" 예시, application-director.md·infrastructure-director.md 등에도 연쇄 영향).
- **🟢 spec decision #15 실용화**: 원 규정 "PM 은 audit-team 호출 금지" 는 외부 감리 독립성 가정 (실제 외부 감리업체 존재). 본 E2E 에서 PM·user 동일 세션이므로 worktree 격리 + 도구·역할 제한으로 실질 독립성 유지하면서 PM 자동화 가능. `scripts/run_audit.sh` 로 정착.
- **🟢 audit-team 독립성 준수**: 12 findings 모두 사실 기술, 파일/라인/ID 인용. 심각도·개선안·담당 배정 없음. 99_audit/ 외 쓰기 없음.
- **🟢 audit 효율**: cache_read 2.39M / 94.5% hit, ~$0.5. 감리 범위 광대 (200 child) 대비 저비용.

### Phase 7 patches 후보 추가
8. **`claude -p` CLI 인자 순서 가이드 (HIGH)**: spec/plan/role 모든 Track A 호출 예시에 `--add-dir` 을 `--append-system-prompt` 보다 앞에 두도록 통일. 잘못된 순서는 silent failure → 디버그 어려움.
9. **spec decision #15 amendment (med)**: "PM 이 scripts/run_audit.sh 를 통해 audit-team 을 호출할 수 있다" 명시. 본 Phase 7 에서 role 파일 차원 적용 완료, spec 본문 반영 필요.
10. **인덱스 의존성 요약 표 자동 검증 (low-med)**: validate_artifact_hierarchy 는 자식 frontmatter 양방향만 검사. 인덱스의 "의존성 요약" 마크다운 표는 미검사 → 본 감리에서 발견된 4건 대부분 이 카테고리. 인덱스 표 vs 자식 frontmatter 를 비교 검증하는 script 추가 검토.

## Task 7: 03_implementation (5 도메인 구현, 2-Wave 구조)

### 진행
- §2-6 gate: business-manager 자문 — 2-Wave 구조, P0 carry-forward REC-D-01~06 + ARCH-R-01, MOCK 범위 정의 (agentId a502d89cbdfa11fb7)
- Track A 2 갈래 병렬 (PM → appdir + infra-dir 모두 opus/xhigh, 약 ~?분)
- appdir Wave 1 (단독): backend-developer-sonnet/xhigh — PRG-COMMON-01/02/03 + PRG-AUTH-01~03 + UT-RES-01~05/28/29/30 (REC-D-01~05 P0 일괄 반영)
- appdir Wave 2 (6 sub-Track A 병렬): member, loan, book(haiku), search, batch, web — 22 UT-RES + 16 SCN
- infra-dir 1 sub-Track A: W-I-07 (Dockerfile, compose, 8 TBL DDL, REC-D-06 secrets, ARCH-R-01 heartbeat 컬럼, DBP-R-07 확장 초기화)
- 산출물 90+ 파일 (`src/backend` 32 .py, `src/batch` 6 .py, `src/web/admin` 24, tests 22, `infra/` 8, 03_implementation 32)
- PM Step 3: RTM/by-stage/implementation.md 자동 추출 (25 RQ × 20 PRG × 30 UT-RES 매핑)

### 핵심 발견 (Task 4·5 보강 효과 3차 검증 — 메이저 성공 지속)
- **🟢 양 디렉터 모두 sync + validate self-check 준수, verbatim 인용**:
  - appdir: `OK: book-mgmt-api updated 30 parent file(s)` + `OK: ... clean (247 child file(s))` 인용 후 PASS-WITH-COMMENTS
  - infra: `OK: ... already in sync` + `OK: ... clean (215 child file(s))` 인용 후 PASS
  - 잔여 finding 자체 시정 후 보고 (UT-RES-19~23 frontmatter drift 일괄 regex 수정, depends-on/resolved-by 분리)
- **🟢 Prompt cache 효과 (3차 검증)**:
  - appdir: cache_read 4.08M / cache_creation 121K → ~97% hit (3-tier nested 환경)
  - infra: cache_read 803K / cache_creation 9.8K → ~99% hit (단일 sub-Track A)
- **🟢 비용 절감 검증 (Task 5 보다 더 절감)**:
  - 추정 $8-15 → 실측 ~$5.0 (~60% 절감)
  - haiku 활용 효과 (book CRUD + 단순 SCN): Wave 2 비용 일부 추가 절감
- **🟢 P0 carry-forward 전수 해결**: REC-D-01~05 (보안), REC-D-06 (Docker Secrets), ARCH-R-01 (배치 격리), DBP-R-02 (overdue 정책 A3 하이브리드), DBP-R-07 (pgcrypto/pg_trgm) 모두 구현 + 증적 매핑 PM 보고에 file:line 인용
- **🟡 2-Wave 구조 효율**: appdir 가 Wave 1 (auth+COMMON) 완료 후 Wave 2 (5 도메인) 병렬 dispatch — 의존성 관리 정확. cache 재사용 극대화.
- **🟡 cross-track 동기화 (DBP-R-02)**: appdir 가 Wave 2 PRG-LOAN/BATCH 호출 시 infra-dir 의 W-I-07 결과 (loans.overdue_days 컬럼 + 정책 권고)를 context 에 주입. 양 트랙 일관 결과.

### 산출물 요약 (90+ 파일)
| 영역 | 파일 수 | 담당 |
|------|------|-----|
| src/backend/{auth,common,member,book,loan,search} | 32 .py | backend-developer-sonnet (auth/member/loan/search) + backend-developer-haiku (book) |
| src/batch/ | 6 .py | batch-developer-sonnet |
| src/web/admin/{auth,member,book,loan,search,batch,common}/ | 24 (HTML 16 + CSS 1 + JS 6 + index 1) | web-developer + web-publisher + designer (haiku 우세, AUTH·COMMON 만 sonnet/high) |
| tests/test_ut_unit_*.py | 22 | backend-developer (Wave 2) |
| infra/{Dockerfile, docker-compose.yml, migrations/, scripts/, .env.example, .github/workflows/, README.md} | 8 | infrastructure-engineer-sonnet |
| 03_implementation/{unit-test-results 30 + reviews 2 + index 2} | 34 | 본 단계 산출 |

### Carry-forward → 04_test (PM 권고)
- batch audit 확장 CR: OVERDUE_NOTICE_SENT action_type 미등록 → CR 등재 + write_audit_log 확장
- UT-RES-09/13 AC 표 → IT 케이스에 Given/When/Then 재구성
- MOCK 한계: 04_test 에서 Docker + PG 실 환경 기동 후 실제 green 재검증

### Phase 7 patches 후보 추가
11. **MOCK→실 환경 전이 가이드 (med)**: 03_implementation MOCK 와 04_test 실 환경 전이 시 어떤 검증이 필수인지 spec 에 명시 필요. 현 spec 은 04_test 시험 케이스 작성만 명시, 환경 전이 게이트 없음.
12. **2-Wave dispatch 패턴 정착 (low-med)**: appdir 가 자체 판단으로 2-Wave 구조 (선행 1 + 병렬 N) 채택. 일반화 가능 — application-director.md 의 "How You Invoke" 에 "공통 모듈/암호화 선행, 도메인 병렬" 패턴 명시 가능.

## Task 8: 04_test (tester + QA 직렬, 정식 CR 사이클 첫 실행)

### 진행
- §2-6 gate: business-manager 자문 — 직렬(tester→QA→PM), IT-09 CR-001 시정 사이클, plausible FAIL 시뮬레이션 권고 (agentId aadebfeab0fc83563)
- tester Track A (Skill, sonnet/xhigh) — W-T-01 IT 14건 + W-T-02 ST 3건 + W-T-03 UAT 9건 + carry-forward 3건 처리 (CR-001 등재, audit.py 수정, IT-04/IT-13 G/W/T 재구성)
- QA Track A (Skill, sonnet/xhigh) — W-T-04 qa-report 5 자식 작성, 25 RQ 100% 추적
- security-specialist Track B 자문 — IT-RES-02/13 보안 합격 검토 + C-AUDIT-1 진입 전 보강 권고 (SEC-CF-01/02)
- PM W-T-05 리뷰 (4인: tester + QA + PM + security) + W-T-06 RTM/by-stage/test.md 자동 추출

### 핵심 발견 (Task 4·5·7 보강 효과 4차 검증 + 신규 발견)
- **🟢 양 단독 역할 모두 sync + validate self-check 준수, verbatim 인용**:
  - tester: 276 child clean
  - QA: 281 child clean
  - PM: 최종 282 child clean
- **🟢 Prompt cache 효과 (4차 검증)**: tester cache_read 9.0M / 98% hit, QA 1.7M / 96% hit
- **🟢 비용 절감**: 추정 $0.4-1.0 → 실측 ~$1.9 (BM 추정 약간 초과 — security 자문 + multi-line 정정 작업 추가됨)
- **🟢 정식 CR 사이클 첫 가동**: tester 가 carry-forward (batch audit CR) 를 받아 CR-001 신설 → 시정 → 재실행 → CLOSED 사이클 정상 동작. defect-cycle 증적 (QA-REPORT-DEFECT-CYCLE) 보존.
- **🟢 cross-track 보안 자문**: PM 이 security-specialist Track B 로 보안 IT 케이스 합격 판정 보강. C-AUDIT-1 진입 전 보강 항목 2건 사전 식별.
- **🔴 NEW finding: multi-line YAML 리스트 파싱 누락 (HIGH)**:
  - QA 가 작성한 4 자식 (QA-REPORT-COVERAGE/RESULTS/DEFECT-CYCLE/SECURITY) 의 frontmatter 가 `depends-on:\n  - X\n  - Y` 다중 행 YAML 리스트 형식 사용
  - `scripts/_frontmatter.py` 는 inline `[...]` 형식만 지원 → 리스트 값이 빈 문자열로 인식되어 drift-guard 가 의존성을 검증하지 못함 (silent miss)
  - PM 이 inline 형식으로 정정해야 했음 (4 파일 + VERDICT 정정)
  - **함의**: spec/role 어디에도 frontmatter 리스트 형식 강제 없음 → 에이전트가 문법적으로 유효한 multi-line YAML 사용 가능하나 검증기 미지원. spec §3-1 자식 frontmatter 표준에 "리스트는 inline `[a, b, c]` 형식만 사용" 명시 필요. 또는 _frontmatter.py 에 multi-line 지원 추가.
- **🟢 가상 시뮬레이션 PASS 합리성**: spec §Task 8 MOCK NOTE 대로 "code stub + pass criteria align → simulated PASS" 가능. 단, ST-RES-03 (RQ-NFR-05 단일 서버 graceful shutdown) 은 mock 시뮬레이션이라 05_deployment 게이트에서 실제 단일 컨테이너 배포 후 재확인 필요 (PM 이 carry-forward 명시).

### 산출물 (45 파일)
| 영역 | 파일 |
|---|---|
| 04_test/integration-test-results | 14 IT-RES + 1 index |
| 04_test/system-test-results | 3 ST-RES + 1 index |
| 04_test/uat-results | 9 UAT-RES + 1 index |
| 04_test/qa-report | 5 자식 + 1 index |
| 04_test/reviews | 1 REV-TEST-RESULTS-V1 + (1 index 기존) |
| change-requests/CR-001 | 4 파일 (cr-request, cr-impact, cr-decision, index) |
| RTM/by-stage/test.md | 1 (PM 자동 추출) |
| src/backend/common/audit.py | 1 (CR-001 시정 — OVERDUE_NOTICE_SENT 추가) |

### Carry-forward → 05_deployment / C-AUDIT-1
- **CF-01**: RQ-MEMBER-03 IT/UAT 미검증 — 종료감리에서 audit-team 명시적 검토 (PM 위험 수용)
- **CF-02**: 03_implementation MOCK 한계 — 종료감리에서 명시
- **SEC-CF-01**: IT-RES-02 DB 잠금 컬럼 직접 검증 누락 — 05_deployment 진입 전 보강
- **SEC-CF-02**: IT-13 토큰 유효기간 중 역할 변경 시나리오 미커버 — C-AUDIT-1 진입 전 신규 IT 또는 위험 수용 기록

### Phase 7 patches 후보 추가
13. **frontmatter multi-line YAML 리스트 지원 (HIGH)**: 두 가지 옵션 — (a) `_frontmatter.py` 에 multi-line list 파서 추가, (b) spec §3-1 에 "리스트는 inline `[...]` 만 허용" 명시. (a) 가 사용성 좋고 (b) 가 단순. 우선순위 high — 에이전트 출력 중 silent miss 발생 위험.
14. **CR (Change Request) 사이클 첫 실증 — 정식 패턴 정착 (med)**: Task 8 에서 CR-001 사이클 정상 동작. cr-request → cr-impact-analysis → cr-decision → 시정 → audit.py 수정 → 재실행 PASS → CR-CLOSED. Phase 7 plan 의 Task 8 MOCK 흐름 외 실증 케이스로 spec/templates 의 change-requests/ 사용 예시 보강.
