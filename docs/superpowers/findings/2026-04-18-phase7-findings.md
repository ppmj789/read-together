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
