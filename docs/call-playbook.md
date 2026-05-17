# Call Playbook — AI SI Project Team

- 버전: v1 (2026-04-18)
- 기반: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md` v2
- 오너: 본 문서는 드리프트-가드 대상. Role 파일 변경 시 본 문서 동기 갱신.

---

## 0. 개요 — 단일 호출 계약 (claude -p 폐기)

본 플랫폼은 `claude -p` subprocess 를 사용하지 않는다. "Track A" 개념은
폐기됐다. 모든 위임·저작·자문은 현 세션의 **Agent 툴 단일 primitive** 로
수행한다.

### 0-1. 저작 노드 호출

PM(유일한 오케스트레이터)이 Agent 툴로 dispatch:

- `subagent_type` = `general-purpose`
- `model` = 난이도 기반 (`opus` | `sonnet` | `haiku`)
- `prompt` = (1) `[PERSONA]` 블록에 `.claude/roles/<role>.md` 전문 inline
  주입 + self-attestation 지시, (2) 처리할 ledger 노드 파일 경로,
  (3) 출력 계약: 실산출물은 소유 경로에 직접 Write, 같은 ledger 노드의
  `## RESPONSE`/`## CHILD INDEX`/`## NEXT` 작성 + frontmatter `status`
  갱신, PM 반환은 **노드 경로 + status + NEXT 요약만**.

`effort` 는 Agent 툴 미노출 → model 티어 + 프롬프트 명시로 근사.

### 0-2. 순수 자문 호출 (읽기전용)

저작이 불필요한 분석·리뷰는 `subagent_type=<role>-<variant>`
(`.claude/agents/`, 툴셋 Read/Glob/Grep)로 dispatch. 더 저렴함.

### 0-3. PM 의 위치

PM 은 모든 hop 의 필수 버스이자 공유 파일 단독 scribe
(`project-state.md`·`RTM/**`·`escalations.md`·`agent-call-log.md`·
`rollback-history.md`). general-purpose 는 Agent 툴 미보유 → 자율 중첩
불가. PM 은 본문이 아닌 노드 경로·`NEXT:` 만 셔틀한다.

### 0-4. ledger 프로토콜

위임·통신은 `projects/<name>/ledger/` 계층 트리에 축적된다. 노드 ID =
Dewey(`A` → `A-1` → `A-1-1`). 노드 = 요청-응답 완결 단일 문서이며
실산출물(00~05 트리)·RTM-ID 를 링크하는 래퍼다. 스키마·소유 규칙은
spec `docs/superpowers/specs/2026-05-16-no-claude-p-ledger-redesign-design.md` §2.

> 📝 **산출물 경로 표기 관행 (Phase 7 Part B meta-test 2 도출, C-14-3)**: 각 역할의 산출물 경로는 **프로젝트 상대 경로** (`projects/<project>/<stage>/...` 또는 단순히 `<stage>/...`) 로 기술한다. 절대 경로 (`/home/earth/ai_team_meta/...`) 나 worktree-특정 경로는 사용하지 않는다. persona probe 응답, Role 파일 `## Artifacts You Own` 섹션, 산출물 frontmatter 의 `related:` 리스트에 동일하게 적용.
> - 근거: 동일 프로젝트가 다수 worktree 에서 실행될 수 있고(예: master, audit worktree, meta-test worktree), 절대 경로는 worktree 이동 시 유효성을 잃음. 상대 경로는 모든 worktree 에서 동일하게 해석.

본 문서는 **역할별 호출 규칙의 중앙 매트릭스 정본**이다. 각 `.claude/roles/<role>.md` 의 `## How You Invoke Sub-executions` / `## How You Consult Advisors` 섹션은 본 문서의 해당 역할 하위 표를 **발췌·복사** 한 것과 정합해야 한다.

`scripts/validate_agent.py` 의 drift-guard 가 Role 파일의 표와 본 문서 §5 의 각 역할 섹션 간 정합(행 누락·잉여·금지 사례 위반) 을 검증한다.

---

## 1. 단계별 호출 매트릭스 (V-Model)

| 단계 | 주도자 | 필수 Track A (주 산출물 저작) | 필수 Track B (자문·리뷰) |
|------|-------|-----------------------------|-------------------------|
| 00_kickoff | PM (Skill, 사용자 세션) | — (PM 직접 저작) | business-manager(예산 가이드), quality-assurance(계획 리뷰) |
| 01_analysis | application-director | application-architect, data-modeler, tester | technical-architect, quality-assurance |
| 02_design (소규모) | application-director + infrastructure-director | 개발자(backend/web/batch/web-publisher)가 파트별 설계 저작 + tester(unit-test-cases) + technical-architect(공통 아키) + security-specialist(보안) + infrastructure-engineer(인프라) | quality-assurance, software-architect(모듈 경계 자문), designer(UI/UX 자문), data-modeler(모델 자문), database-administrator(DB 자문) |
| 02_design (대규모) | application-director (**도메인 파트** 분할 — 기술 유형이 아니라 업무 도메인 기준; 예: 회원·결제·구매·카탈로그) | part-leader × N (N = 도메인 수, SOW 분석 결과) → 파트 소속 cross-functional 개발자(web+batch+backend)에게 저작 재위임 + tester + 공통 설계(technical-architect / security-specialist / infrastructure-engineer). 각 도메인 파트가 자기 도메인의 TBL-RDB·COLL-NOSQL 까지 자체 저작 (DB 쏠림 방지) | (동일) |
| 03_implementation (소규모) | application-director | backend-developer, web-developer, batch-developer | security-specialist, database-administrator, software-architect 수시 |
| 03_implementation (대규모) | part-leader | 파트별 개발자들 | (동일) + tester 수시 |
| 04_test | tester (PM 감독) | tester(통합·시스템·UAT 실행), infrastructure-engineer(테스트 환경) | quality-assurance |
| 05_deployment | infrastructure-engineer | infrastructure-engineer, technical-architect(리뷰) | security-specialist |
| 감리 (analysis, 대규모만) | 사용자 호출 | audit-team (worktree) | — |
| 감리 (design, 필수) | 사용자 호출 | audit-team (worktree) | — |
| 감리 (closing, 필수) | 사용자 호출 | audit-team (worktree) | — |

---

## 2. 상황 기반 자문 매트릭스 (Track B)

### 2-1. 보안

| 트리거 | 자문 대상 |
|-------|---------|
| 인증·세션·결제 로직 작성·리뷰 | security-specialist |
| 외부 API 연동 설계·구현 | security-specialist + software-architect |
| 감사 로그·민감정보 저장 설계 | security-specialist + database-administrator |
| 권한 모델·RBAC 설계 | security-specialist + application-architect |
| 암호화·키 관리 | security-specialist |

### 2-2. 데이터베이스

| 트리거 | 자문 대상 |
|-------|---------|
| 복잡 쿼리·인덱스 설계 | database-administrator |
| 스키마 변경·마이그레이션 계획 | database-administrator + data-modeler |
| 트랜잭션 격리 수준 판단 | database-administrator + software-architect |
| 파티셔닝·샤딩 전략 | database-administrator + technical-architect |

### 2-3. 성능·확장성

| 트리거 | 자문 대상 |
|-------|---------|
| 대용량 처리 설계 | technical-architect + database-administrator |
| 배치 최적화 | technical-architect + batch-developer |
| 캐시·큐 전략 | technical-architect + software-architect |
| 응답 시간 SLO 미달 | technical-architect |

### 2-4. 아키텍처·인터페이스

| 트리거 | 자문 대상 |
|-------|---------|
| 모듈 경계 모호 | software-architect |
| 외부 시스템 연동 아키 | technical-architect + software-architect |
| 프론트·백 인터페이스 스펙 | software-architect + backend-developer + web-developer |
| 이벤트/메시지 설계 | software-architect + technical-architect |

### 2-5. 예산·일정

| 트리거 | 자문 대상 |
|-------|---------|
| 단계 진입 (필수) | business-manager (§2-6 설계서) |
| 예산 초과 우려 | business-manager |
| 일정 지연 우려 | business-manager + PM |
| 추가 자원 요청 | business-manager |
| 모델·effort 승급 판단 | business-manager |

### 2-6. 품질·테스트

| 트리거 | 자문 대상 |
|-------|---------|
| 품질 기준 해석 모호 | quality-assurance |
| 테스트 케이스 해석 난해 | tester |
| 단계 산출물 품질 우려 | quality-assurance + 해당 단계 주도자 |
| 리뷰 회의 주관 | 해당 단계 주도자 (§7-1 리뷰 매트릭스 참조) |

---

## 3. 에스컬레이션 경로

| 발생자 | 1차 | 2차 | 3차 |
|-------|----|----|-----|
| 실무 개발자 (backend/web/batch/designer/web-publisher) | 파트리더(대규모) / 응용총괄(소규모) | PM | 사용자 |
| 자문가 (Track B 세션 중 문제 발견) | 자문 요청자 | 요청자의 직속 상위 | PM |
| AA · SWA · data-modeler · TA · DBA · security-specialist · infrastructure-engineer | 소속 총괄 (응용 or 인프라) | PM | 사용자 |
| 파트리더 | 응용총괄 | PM | 사용자 |
| 응용총괄 · 인프라총괄 | PM | 사용자 | — |
| 사업관리 · QA · tester | PM | 사용자 | — |
| PM | 사용자 | — | — |
| 감리팀 | PM (지적만 전달, 판단·처리는 PM) | — | — |

모든 에스컬레이션은 `projects/<프로젝트명>/escalations.md` 에 append (설계서 §7-3).

### 에스컬레이션 포맷 (모든 Track A 실행 세션 종료 시)

```
ESCALATION: <한 줄 요약>
Details:
  - ...
Request to: <해결 요청 대상/내용>
```

---

## 4. 금지된 호출 (위임 체인 위반)

| 금지 사례 | 사유 |
|---------|------|
| PM 이 개발자·파트리더를 직접 저작 노드로 호출 (총괄 건너뜀) | 두 단계 이상 건너뛴 지정 — 설계서 §2-3 위임 체인 위반 |
| 응용총괄이 개발자의 모델을 파트리더 경유 없이 직접 지정 (대규모 시) | 동일 |
| 실무자가 다른 실무자를 저작 노드로 호출 | 실무자는 저작 노드 호출 권한 없음 (순수 자문만) |
| 사업관리가 직접 하위 에이전트 호출 | 예산 프레임·모니터링만 담당 (설계서 §2-6) |
| 감리팀이 코드·산출물 직접 수정 | 감리는 읽기 전용 지적만 (설계서 §2-5) |
| 자문 Skill 을 Opus·xhigh 외 값으로 호출 | Skill frontmatter 고정 (의사결정 #19) |
| 순수 자문 노드에게 Write/Edit/Bash 가 필요한 작업 지시 | 서브에이전트 실제 툴셋 = Read/Glob/Grep (의사결정 #21). 저작 노드로 대체 |
| `claude -p` subprocess 를 발생시키는 모든 호출 | 무과금·무claude-p 제약 (spec 2026-05-16) |
| general-purpose 노드가 공유 파일(§7-2)을 직접 수정 | 공유 파일은 PM 단독 scribe |
| 저작 노드가 본문을 PM 에 반환 (경로 아닌 본문 셔틀) | PM 컨텍스트 보호 — 경로·NEXT 만 |

---

## 5. 역할별 호출 규칙 정본

각 역할에서 Role 파일의 `## How You Invoke Sub-executions` 및 `## How You Consult Advisors` 섹션은 본 §5 의 해당 역할 하위 표를 복사한다. 역할이 해당 호출 주체가 아닐 경우 해당 섹션 자체를 생략한다.

### 5-1. project-manager (Skill 전용, 사용자 세션)

#### 5-1-1. NEXT 디스패치 선언 규칙

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| 01_analysis 진입 (사용자 승인 후) | application-director | 요구사항·AS-IS·TO-BE·테스트케이스 주도 | 확정 project-plan, 예산 가이드, SOW |
| 01_analysis 진입 | infrastructure-director | 기술 제약·운영 요건 식별 | 동일 |
| 02_design 진입 | application-director | 응용 설계 주도 | 분석 산출물 전체 |
| 02_design 진입 | infrastructure-director | 인프라 설계 주도 | 동일 |
| 03_implementation 진입 | application-director | 구현 주도 | 설계 산출물 |
| 03_implementation 진입 | infrastructure-director | 인프라 환경 구성 | 동일 |
| 04_test 진입 | tester | 통합·시스템·UAT 실행 | test-cases 전체 |
| 05_deployment 진입 | infrastructure-director | 배포 계획·실행 | 검증된 산출물 |
| 감리 단계 도래 | (사용자에게 안내) | 사용자가 worktree 에서 audit-team Track A 실행 | 감리 범위 |

#### 5-1-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 매 단계 진입 (필수) | business-manager | 해당 단계 모델·effort 예산 정책 확정 |
| 계획·단계별 주요 산출물 완료 후 | quality-assurance | 품질·완결성 리뷰 |
| 요구사항 충돌·판단 난해 | application-director 또는 infrastructure-director | 총괄 판단 자문 |
| 예산 초과 우려 | business-manager | 재할당·승급 권고 |
| 감리 지적 처리 판단 | 해당 총괄 | 시정조치 전략 자문 |
| 테스트 결과 품질 판단 | quality-assurance + tester | 합격 여부 권고 |

---

### 5-2. application-director

#### 5-2-1. NEXT 디스패치 선언 규칙

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| 01_analysis 진입 | application-architect | requirements·as-is·to-be 저작 | SOW, project-plan, 예산 |
| 01_analysis 진입 | data-modeler | 논리 데이터 모델 초안 (분석 단계 한정) | 동일 |
| 01_analysis 진입 | tester | UAT · 통합 테스트 케이스 저작 | 동일 |
| 02_design 진입 (소규모) | backend-developer | 서버측 PRG(type:API/daemon) / IF-REST / IF-KAFKA / 물리 DB 저작 | 분석 산출물 + 공통 설계(ARCH-*, INF-*, SEC-*) |
| 02_design 진입 (소규모) | web-developer | web PRG(type:web) / SCN 저작 | 동일 |
| 02_design 진입 (소규모) | batch-developer | batch PRG(type:batch) / BATCH 저작 | 동일 |
| 02_design 진입 (소규모) | web-publisher | 퍼블리싱 가이드 저작 | 동일 |
| 02_design 진입 | tester (Track B 자문) | unit-test-cases 는 각 파트/도메인 개발자가 저작; tester 는 케이스 설계·커버리지 자문 | 동일 |
| 02_design 진입 (대규모) | part-leader (파트 수만큼) | 파트별 설계·구현 주도 위임 (파트리더가 파트 개발자에게 저작 재위임) | project-plan 의 파트 정의 |
| 03_implementation 진입 (소규모) | backend-developer | 백엔드 구현 | 설계 산출물 |
| 03_implementation 진입 (소규모) | web-developer | 프론트 구현 | 동일 |
| 03_implementation 진입 (소규모) | batch-developer | 배치 구현 (있을 시) | 동일 |
| 리뷰 회의 오케스트레이션 | 관련 역할 2인 이상 (아키텍트 자문 포함) | 2인 원칙 리뷰 | 리뷰 대상 산출물 |

#### 5-2-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 단계 진입 시 (PM 으로부터 정책 수신) | business-manager | 예산·모델 정책 명확화 |
| 아키 경계 모호 | technical-architect | 기술 아키 자문 |
| 요구사항 품질 우려 | quality-assurance | 품질 검토 요청 |
| 예산 초과 우려 | business-manager | 재할당·승급 권고 |
| 보안·성능 트레이드오프 | security-specialist + database-administrator | 의사결정 자문 |
| 인터페이스 설계 확인 | software-architect | 모듈 경계 자문 |

---

### 5-3. infrastructure-director

#### 5-3-1. NEXT 디스패치 선언 규칙

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| 01_analysis 진입 | technical-architect | 기술 아키 초안·제약 식별 | SOW, project-plan |
| 01_analysis 진입 | infrastructure-engineer | 운영 요건·제약 식별 | 동일 |
| 02_design 진입 | technical-architect | architecture.md 저작 (공통 토폴로지·Kafka·Stream 아키) | 분석 산출물 |
| 02_design 진입 | security-specialist | security-review 저작 (공통) | 설계 산출물 |
| 02_design 진입 | infrastructure-engineer | 인프라 구성도 (공통 INF-*, 스케줄러·모니터링) | 동일 |
| 03_implementation 진입 | infrastructure-engineer | 환경 구성·배포 준비 | 설계 산출물 |
| 04_test 진입 | infrastructure-engineer | 테스트 환경 준비 | 테스트 계획 |
| 05_deployment 진입 | infrastructure-engineer | deployment-plan·operation-manual·training-material 저작 | 검증된 산출물 |

#### 5-3-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 단계 진입 시 | business-manager | 예산·모델 정책 명확화 |
| 보안 의사결정 | security-specialist | 보안 자문 |
| 아키 경계 모호 | technical-architect | 기술 아키 자문 |
| DB 설계 이슈 | database-administrator | DB 자문 |
| 예산 초과 우려 | business-manager | 재할당·승급 권고 |

---

### 5-4. business-manager (자문 중심, Track A 호출 주체 아님)

사업관리는 **하위를 직접 호출하지 않는다** (설계서 §2-6 경계). 자문·보고만 수행.

#### 5-4-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-4-2. 순수 자문(읽기전용) 호출 규칙 (필요 시 상위 보고용)

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 감리 지적이 예산·일정 영향 큼 | PM (에스컬레이션) | 승급·재할당 의사결정 요청 |
| 자원 한도 임박 | PM (에스컬레이션) | 중대 의사결정 요청 |

---

### 5-5. quality-assurance (자문 중심)

QA 는 주로 Track B 자문 대상. 스스로 Track A 호출 불가.

#### 5-5-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-5-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 품질 기준 해석 모호 | PM (에스컬레이션) | 기준 재정의 요청 |
| 테스트 결과 판단 난해 | tester | 결과 상세 확인 |

---

### 5-6. tester

#### 5-6-1. NEXT 디스패치 선언 규칙

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| 04_test 실행 | infrastructure-engineer | 테스트 환경 가동 확인 | 테스트 계획 |

(tester 는 주로 테스트 설계·실행의 실무자. 하위 호출 최소.)

#### 5-6-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 품질 기준 해석 모호 | quality-assurance | 기준 확인 |
| 테스트 설계 아키 의문 | software-architect | 설계 확인 |
| 테스트 데이터·환경 이슈 | infrastructure-engineer | 인프라 자문 |
| 예산·시간 초과 우려 | business-manager | 일정 자문 |

---

### 5-7. audit-team (감리팀, 별도 worktree 에서 실행)

#### 5-7-1. NEXT 디스패치 선언 규칙

해당 없음. 감리팀은 자기 worktree 내부에서 감리 산출물만 저작.

#### 5-7-2. 순수 자문(읽기전용) 호출 규칙

해당 없음. 감리 독립성 원칙상 수행 조직 어떤 에이전트와도 자문 교류 금지 (설계서 §2-5).

---

### 5-8. application-architect (AA)

#### 5-8-1. NEXT 디스패치 선언 규칙

해당 없음 (실무자).

#### 5-8-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 아키 판단 난해 | technical-architect | 기술 아키 자문 |
| 데이터 구조 판단 | data-modeler | 모델 자문 |
| 요구사항 품질 우려 | quality-assurance | 품질 자문 |
| 보안 관련 요구 | security-specialist | 보안 자문 |

---

### 5-9. software-architect (SWA)

#### 5-9-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-9-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 모듈 경계 확정 | application-architect | 요구 맥락 확인 |
| DB 연계 설계 | database-administrator | 쿼리·트랜잭션 자문 |
| 보안 인터페이스 | security-specialist | 인증·권한 자문 |
| 성능 관련 설계 | technical-architect | 성능 자문 |

---

### 5-10. data-modeler

#### 5-10-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-10-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 물리 구현 제약 | database-administrator | 물리 스키마 자문 |
| 비즈니스 규칙 해석 | application-architect | 요구 맥락 확인 |
| 성능·샤딩 판단 | technical-architect + database-administrator | 아키 자문 |

---

### 5-11. part-leader (대규모 모드만)

#### 5-11-1. NEXT 디스패치 선언 규칙

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| 02_design 진입 (파트별 설계) | 파트 소속 backend-developer / web-developer / batch-developer / web-publisher | 파트 내 설계 산출물 저작 (아키텍트는 Track B 자문 전용) | 응용총괄의 파트 분담 + 공통 설계(ARCH-*, INF-*, SEC-*) 참조 |
| 03_implementation 진입 | 파트 소속 backend-developer / web-developer / batch-developer / web-publisher | 파트 구현 | 파트 설계 산출물 |
| 파트 내 리뷰 오케스트레이션 (설계·코드) | 파트 관련 역할 2인 이상 (저자 + 파트리더 또는 아키텍트) | 2인 원칙 리뷰 | 리뷰 대상 |

#### 5-11-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 파트 간 경계 이슈 | application-director | 조정 자문 |
| 모듈 경계·인터페이스 호환성 | software-architect | 설계 자문 |
| 데이터 모델·정합성 | data-modeler | 모델링 자문 |
| UI/UX·접근성 | designer | UX 자문 |
| 보안·DB·아키 자문 (파트 내 판단 난해) | security-specialist / database-administrator / technical-architect | 전문 자문 |
| 예산 초과 우려 | business-manager | 재할당 요청 |
| 테스트 케이스 이슈 | tester | 테스트 확인 |

---

### 5-12. backend-developer

#### 5-12-1. NEXT 디스패치 선언 규칙

해당 없음 (실무자).

#### 5-12-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 인증·세션·결제 로직 | security-specialist | 보안 리뷰 |
| 복잡 쿼리·인덱스 설계 | database-administrator | DB 자문 |
| 아키 경계·인터페이스 모호 | software-architect | 설계 확인 |
| 성능 설계 | technical-architect | 아키 자문 |
| 테스트 케이스 해석 난해 | tester | 케이스 확인 |
| 추가 자원·시간 필요 | business-manager | 일정·자원 자문 |

---

### 5-13. batch-developer

#### 5-13-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-13-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 대용량 처리·최적화 | technical-architect + database-administrator | 성능 자문 |
| 스케줄링·운영 환경 | infrastructure-engineer | 인프라 자문 |
| 데이터 정합성 | data-modeler | 모델 확인 |
| 테스트 데이터 | tester | 케이스 확인 |

---

### 5-14. web-developer

#### 5-14-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-14-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 백엔드 API 스펙 해석 | backend-developer (파트 내 경우) / software-architect | 인터페이스 확인 |
| 화면·디자인 해석 | designer / web-publisher | 레이아웃·스타일 자문 |
| 보안 (XSS/CSRF 등) | security-specialist | 보안 자문 |
| 성능 (번들·로딩) | technical-architect | 아키 자문 |

---

### 5-15. web-publisher

#### 5-15-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-15-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 화면 설계 해석 | designer / application-architect | 요구·디자인 맥락 |
| 접근성 이슈 | quality-assurance | 기준 확인 |
| 프론트 통합 | web-developer | 통합 자문 |

---

### 5-16. designer

#### 5-16-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-16-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 요구사항 해석 | application-architect | 맥락 확인 |
| 기술 제약 확인 | web-publisher / web-developer | 구현 가능성 |
| 접근성·품질 | quality-assurance | 기준 확인 |

---

### 5-17. technical-architect (TA)

#### 5-17-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-17-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| DB 물리 설계 상호작용 | database-administrator | DB 자문 |
| 보안 아키 | security-specialist | 보안 자문 |
| 운영·배포 제약 | infrastructure-engineer | 인프라 자문 |
| 요구 맥락 | application-architect | 요구 확인 |

---

### 5-18. database-administrator (DBA)

#### 5-18-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-18-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 논리 모델 재확인 | data-modeler | 모델 자문 |
| 성능 요구 | technical-architect | 아키 자문 |
| 백업·재해복구 | infrastructure-engineer | 운영 자문 |
| 보안 (암호화·감사 로그) | security-specialist | 보안 자문 |

---

### 5-19. security-specialist

#### 5-19-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-19-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 요구 맥락 확인 | application-architect | 비즈니스 맥락 |
| 아키 제약 | technical-architect | 기술 아키 자문 |
| DB 민감정보 | database-administrator | 저장·암호화 자문 |
| 운영 보안 | infrastructure-engineer | 인프라 자문 |

---

### 5-20. infrastructure-engineer

#### 5-20-1. NEXT 디스패치 선언 규칙

해당 없음.

#### 5-20-2. 순수 자문(읽기전용) 호출 규칙

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| 아키 전략 | technical-architect | 아키 자문 |
| 보안 | security-specialist | 보안 자문 |
| DB 운영 | database-administrator | DB 운영 자문 |
| 배포 요구 | (해당 인프라총괄 에스컬레이션) | 전략 판단 |

---

## 6. Drift-guard 규약

`scripts/validate_agent.py` 는 다음을 검증:

1. 각 `.claude/roles/<role>.md` 의 `## How You Invoke Sub-executions` 표가 본 문서 §5-X-1 과 행 단위 정합 (행 누락·잉여 탐지).
2. 각 `.claude/roles/<role>.md` 의 `## How You Consult Advisors` 표가 본 문서 §5-X-2 와 행 단위 정합.
3. 본 문서 §4 의 금지 사례에 해당하는 조합이 Role 파일 호출 규칙 표에 **등장하지 않음** 확인.
4. 본 문서 §1 의 단계별 주도자·필수 호출 대상이 Role 파일 호출 규칙에 빠짐없이 반영됨.
5. 본 문서 §3 의 에스컬레이션 경로가 각 Role 파일 `## Escalation Protocol` 섹션과 정합.

정합 위반 시 drift-guard 는 **실패 종료**. 설계서 §9 Phase 6.5 스텝 10 의 작업 범위.

---

## 7. 개정 이력

- 2026-04-18 v1: 초기 작성. Amendment #1 v2 §2-12 매트릭스 기반 확장.
