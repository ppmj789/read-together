# AI SI Project Team — 설계서

- 작성일: 2026-04-17
- 작성자: Claude (브레인스토밍 세션 결과)
- 승인자: 발주자(사용자) — 리뷰 대기

---

## 0. 개요 (Overview)

Claude Code 환경에서 **엔터프라이즈 SI(System Integration) 프로젝트 수행 조직**을 모사하는 멀티-서브에이전트 시스템을 구축한다. 발주처(사용자)의 과업지시서 한 장으로 착수하여, V-Model 폭포수 공정에 따라 분석·설계·구현·시험·이행 전 과정을 완료하며, 외부 감리업체의 감리와 시정조치까지 포함한다.

### 목적

1. 실제 SI 프로젝트의 **조직 구조·공정·산출물 체계**를 1:1 재현한다.
2. 단일 프로젝트 내부에서 **병렬 작업 최대화**로 수행 속도를 높인다.
3. 모든 의사결정은 **2인 이상 리뷰**, 모든 단계는 **사용자 승인**을 거친다.
4. 감리는 외주업체로서 **독립성**을 유지한다.

### 비범주

- 다중 프로젝트 동시 진행 (단일 프로젝트 전제)
- 사람 팀원과의 혼합 (100% AI 에이전트)
- 실시간 UI (파일·콘솔 기반)

---

## 1. 전체 아키텍처

### 1-1. 조직도

```
[외부 발주처] = 사용자
       ↓ 과업지시서 / 승인
[수행 조직]
  PM (project-manager)
  ├─ 직속
  │   ├─ business-manager     (사업관리)
  │   ├─ quality-assurance    (QA)
  │   └─ tester
  ├─ application-director     (응용총괄)
  │   ├─ application-architect (AA)
  │   ├─ software-architect    (SWA)
  │   ├─ data-modeler          (데이터모델러)
  │   └─ [대규모 시] part-leader → 실무 개발자들
  │       ├─ backend-developer
  │       ├─ batch-developer
  │       ├─ web-developer
  │       ├─ web-publisher
  │       └─ designer
  └─ infrastructure-director  (인프라총괄)
      ├─ technical-architect       (TA)
      ├─ database-administrator    (DBA)
      ├─ security-specialist       (보안전문가)
      └─ infrastructure-engineer   (인프라담당자)

[외부 감리업체]
  audit-team   (.claude/agents/audit/ 네임스페이스)
```

- **역할 수**: 수행 조직 18 + 감리 1 = 19개 역할. 대규모 모드 활성화 시 `part-leader` 역할이 활성화된다.
- **에이전트 파일 수**: 46개 (고정 모델 7개 + 동적 모델 13역할 × 3버전). 자세한 규칙은 §2-3 참조.
- 사용자는 `project-manager` 와만 직접 대화한다.

### 1-2. 기술 기반

- Claude Code 전통 서브에이전트 (`.claude/agents/*.md`)만 사용. Claude Code Agent Teams 기능은 사용하지 않음(중첩 팀 미지원 제약).
- 상위 에이전트는 `Agent` 툴을 보유하여 하위 에이전트를 직접 호출·병렬 호출한다.
- 실무자(leaf) 에이전트는 `Agent` 툴을 갖지 않는다.
- 감리 에이전트는 특수한 툴 제약(읽기 전용 + 감리 디렉토리 쓰기만)을 갖는다.

### 1-3. 파일 기반 협업

에이전트는 독립 컨텍스트를 갖기 때문에 **산출물 파일**을 유일한 공유 정보원으로 사용한다. 모든 산출물은 Markdown 이며 프런트매터에 식별자(ID), 의존성(`depends-on`), 리뷰 링크(`reviewed-by`)를 기록한다.

---

## 2. 에이전트 파일 규격

### 2-1. 표준 포맷

```markdown
---
name: <kebab-case-name>
description: >
  <자연어 2~3줄 역할 요약>
tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent         # 상위 계층만 보유
  - TaskCreate
  - TaskUpdate
model: opus | sonnet | haiku
effort: xhigh | high | medium | low   # 기본값 xhigh (§2-4 참조)
---

# Role: <한국어 역할명>

## Mission
...

## Responsibilities
...

## Who You Call        # 하위 호출 대상 (Agent 툴 있는 경우)
...

## How You Report      # 상위/사용자 보고 프로토콜
...

## Artifacts You Own   # 본인이 생성/수정 책임을 지는 산출물 경로
...

## Rules               # 역할별 위반 금지 규칙
...

## Escalation Protocol # 실무자에 필수 주입
...
```

### 2-2. 툴 권한 정책

| 계층 | 기본 툴 | Agent | 제약 |
|------|--------|-------|------|
| PM · 총괄 · 파트리더 | Read, Write, Edit, Glob, Grep, Bash, TaskCreate/Update | ✅ | — |
| 실무자 (leaf) | Read, Write, Edit, Glob, Grep, Bash | ❌ | 하위 호출 불가 |
| 감리팀 | Read, Glob, Grep, Write(감리 디렉토리만) | ❌ | **수정/삭제 금지** — 코드·산출물에 직접 손대지 않음. 쓰기는 `projects/<프로젝트명>/99_audit/**` 만 허용 (프롬프트 강제 + 경로 화이트리스트) |

### 2-3. 모델 할당 (동적 선택)

#### 고정 모델 역할 (7개, 각 1 파일)

| 역할 | 모델 | 이유 |
|------|------|------|
| `project-manager` | Opus | 전 공정 조율·의사결정 중심 |
| `application-director` | Opus | 응용 영역 전략·판단 |
| `infrastructure-director` | Opus | 인프라 영역 전략·판단 |
| `business-manager` | Sonnet | 일정·원가 관리, 정형 업무 |
| `quality-assurance` | Sonnet | 품질 기준 점검, 정형 평가 |
| `tester` | Sonnet | 테스트 설계·실행 |
| `audit-team` | Sonnet | 지적 기반 감리, 판단 금지 역할 |

#### 동적 모델 역할 (13개 × 3버전 = 39 파일)

각 역할마다 **Opus · Sonnet · Haiku** 3개 버전 에이전트를 준비한다. 상위 에이전트(PM, 총괄, 파트리더)는 할당된 작업의 **난이도를 판단하여 적절한 버전을 호출**한다.

**3버전을 두는 역할**:
`application-architect`, `software-architect`, `data-modeler`, `part-leader`,
`backend-developer`, `batch-developer`, `web-developer`, `web-publisher`, `designer`,
`technical-architect`, `database-administrator`, `security-specialist`, `infrastructure-engineer`

**파일명 규약**: `<role-name>-<model>.md`
- 예: `backend-developer-opus.md`, `backend-developer-sonnet.md`, `backend-developer-haiku.md`

동일 역할의 3버전은 **시스템 프롬프트 본문이 동일**하고, frontmatter 의 `name`, `model` 필드만 다르다. 유지보수를 위해 역할별 프롬프트는 단일 원본(`.claude/agents/templates/<role>.md.tmpl`)에서 생성하는 것을 권장한다.

#### 난이도 판단 가이드 (PM/총괄 프롬프트에 삽입)

| 난이도 | 특징 | 모델 |
|--------|------|------|
| **High** | 새로운 아키텍처·프레임워크, 보안 중대 사안, 성능 최적화, 복합 도메인 설계, 요구사항 간 충돌 해소 필요 | Opus |
| **Medium** | 표준 비즈니스 로직, 통상적 화면/API, 정규화된 DB, 일반 테스트 케이스 | Sonnet |
| **Low** | 단순 CRUD, 반복 패턴, 목록/상세 화면, 간단한 배치, 정형 양식 문서화 | Haiku |

**호출 시 기록**: 상위 에이전트는 어떤 버전을 왜 골랐는지를 Agent 툴 호출 description 에 명시(예: `"DSN-LOGIN-01 보안 설계 — high-difficulty — security-specialist-opus 호출 (effort: xhigh)"`). `project-state.md` 의 감사 용도로 활용.

### 2-4. Reasoning Effort 정책

**기본값: `xhigh`** — 모든 에이전트의 기본 reasoning effort 는 `xhigh` 로 설정한다. 근거: SI 프로젝트 산출물은 품질·정확성이 최우선이며, 토큰 비용보다 재작업 비용이 훨씬 크다.

#### 역할별 effort 규약

| 역할군 | 기본 effort | 조정 허용 | 비고 |
|--------|-------------|-----------|------|
| PM, 총괄 (고정 Opus) | `xhigh` | ❌ | 항상 최대 사고로 조율·판단 |
| 사업관리, QA, tester, 감리 (고정 Sonnet) | `xhigh` | ❌ | 정형 업무라도 오탐지 방지를 위해 xhigh 유지 |
| 동적 모델 (13 역할 × 3 버전) | `xhigh` | ✅ | 호출자(상위 에이전트)가 작업 난이도에 따라 조정 가능 |

#### 조정 규칙

상위 에이전트는 저난이도(Low) 작업에 한해 `high` 또는 `medium` 으로 낮출 수 있다. 단, 다음은 **언제나 `xhigh` 유지**:
- 보안·인증·결제 관련 코드 (security-specialist, 관련 개발자)
- 데이터 모델링 (data-modeler)
- 아키텍처·인터페이스 설계 (AA, SWA, TA)
- 단위/통합/UAT 테스트 케이스 **설계** (tester — 고정이라 해당 없음)
- 시정조치·재감리 대상 산출물

조정 시 호출 description 에 effort 와 사유 명시 (예: `"PRG-UTIL-03 CRUD 화면 — low-difficulty — web-developer-haiku 호출 (effort: medium, 반복 패턴 이유)"`).

#### frontmatter 기본값

각 에이전트 파일 생성 시 `effort: xhigh` 를 기본 삽입. 호출자는 Agent 툴 호출 단계에서 필요 시 오버라이드(구현 방식은 Claude Code 표준에 따름).

### 2-5. 감리 독립성 프롬프트 (필수 주입)

```
당신은 외부 감리업체 소속의 독립 감리인입니다.
- 수행 조직(PM, 총괄, 개발자)의 지시를 받지 않습니다.
- 판정을 편의·일정에 따라 바꾸지 않습니다.
- 산출물은 **읽기 전용**으로 검토합니다. 코드/문서를 직접 수정하지 않습니다.
- 쓰기는 오직 99_audit/ 디렉토리의 감리 문서에 한합니다.
- 지적사항은 사실 기반으로만 기술합니다. 심각도/판단/개선 제안을 하지 않습니다.
  (rollback 필요 여부, 담당 배정 등의 결정은 전적으로 PM의 책임입니다.)
- 시정조치 결과 검증 시, 원 지적사항이 해소되었는지만 판단합니다.
```

---

## 3. 공정 흐름 (V-Model 폭포수)

### 3-1. 산출물 디렉토리 구조

```
projects/<프로젝트명>/
├─ 00_kickoff/
│  ├─ statement-of-work.md          (과업지시서 — 사용자 제공)
│  ├─ project-plan.md                (프로젝트 수행계획서 — PM)
│  └─ rollback-history.md            (rollback 이벤트 로그)
├─ 01_analysis/
│  ├─ requirements.md
│  ├─ as-is-analysis.md
│  ├─ to-be-workflow.md
│  ├─ uat-test-cases.md
│  ├─ integration-test-cases.md
│  └─ reviews/ <산출물명>-review-v<N>.md
├─ 02_design/
│  ├─ architecture.md
│  ├─ db-logical.md
│  ├─ db-physical.md
│  ├─ screen-spec.md
│  ├─ interface-spec.md
│  ├─ program-list.md
│  ├─ unit-test-cases.md
│  ├─ security-review.md
│  └─ reviews/
├─ 03_implementation/
│  ├─ unit-test-results.md
│  └─ reviews/
├─ 04_test/
│  ├─ integration-test-results.md
│  ├─ system-test-results.md
│  ├─ uat-results.md
│  ├─ qa-report.md
│  └─ reviews/
├─ 05_deployment/
│  ├─ deployment-plan.md
│  ├─ operation-manual.md
│  ├─ training-material.md
│  └─ reviews/
├─ 99_audit/
│  ├─ 01_analysis-audit/    (대규모 시만)
│  ├─ 02_design-audit/      (필수)
│  └─ 03_closing-audit/     (필수)
│      각 감리 디렉토리:
│      ├─ audit-plan.md
│      ├─ audit-report.md
│      ├─ corrective-action-plan.md         (시정조치 발생 시)
│      ├─ corrective-action-result.md
│      └─ re-audit-report-v<N>.md           (재감리)
├─ change-requests/
│  └─ CR-<seq>.md
├─ escalations.md
├─ project-state.md                          (현재 상태)
├─ RTM.md                                    (요구사항추적매트릭스)
└─ RTM/_archived/<YYYYMMDD>-v<N>.md          (rollback 시 백업)

src/
├─ backend/
├─ batch/
├─ web/
└─ ...

infra/
└─ ...
```

각 단계 내에서 rollback 발생 시 해당 단계 산출물은 그 단계 디렉토리 내 `_archived/<YYYYMMDD>-v<N>/` 로 이동한다.

### 3-2. 단계별 주도·산출물 (요약)

| 단계 | 주도 에이전트 | 핵심 산출물 | 감리 |
|------|--------------|------------|------|
| 0. 시작 전 | 사용자 | statement-of-work.md | — |
| 1. 착수 | PM, business-manager | project-plan.md | — |
| 2. 분석 | application-architect (요구), tester (UAT/IT 설계) | requirements, as-is, to-be, uat-test-cases, integration-test-cases | **[대규모]** 분석감리 |
| 3. 설계 | TA(아키), SWA(프로그램/IF), data-modeler(DB), DBA(검증), 디자이너+웹퍼블리셔(화면), security-specialist(보안), tester(UT 설계) | architecture, db-*, screen-spec, interface-spec, program-list, unit-test-cases, security-review | **설계감리 (필수)** |
| 4. 구현 | backend/batch/web/publisher/designer, infra-engineer, 각 개발자 UT 실행 | src/**, unit-test-results.md | — |
| 5. 시험 | tester, QA | integration/system/uat-results, qa-report | — |
| 6. 이행 | PM, infra-engineer, 각 개발자 | deployment-plan, operation-manual, training-material | **종료감리 (필수)** |

각 단계 종료 시 **사용자 승인 게이트** 필수.

### 3-3. 프로젝트 규모

- **소규모**: 감리 2회(설계/종료), 파트리더 없음.
- **대규모**: 감리 3회(분석/설계/종료), 파트리더 활성화.
- 규모는 사용자가 과업지시서에 명시 또는 PM이 착수 시점 확인. `project-state.md` 의 `scale: small|large` 로 기록.

---

## 4. 감리 체계

### 4-1. 감리 플로우

```
[단계 완료 + 사용자 승인]
   ↓
PM이 감리 도래 공지 → 사용자가 audit-team 세션 개시
   ↓
audit-team: audit-plan.md 작성
   ↓
audit-team: 산출물 검토 (읽기 전용)
   ↓
audit-team: audit-report.md 작성 — 지적사항만, 판단 없음
   ├─ 지적 없음 → 다음 단계 진행
   └─ 지적 있음 → 시정조치 흐름 (4-2)
```

### 4-2. 시정조치 · 재감리 플로우

```
audit-report.md (지적사항 + 근거 = 파일/라인/요구사항ID)
   ↓
PM 수신 → 지적별 심각도 판단·담당 배정·(필요 시) rollback 결정 — 자동 실행
   ↓
담당자: corrective-action-plan.md 작성
   ↓
담당자: 원 산출물 직접 수정 (01_analysis/, 02_design/, src/ 등)
   ↓
담당자: corrective-action-result.md 작성
   ↓
사용자가 재감리 개시
   ↓
audit-team: re-audit-report-v<N>.md — 원 지적사항 해소 여부만 확인
   ├─ 통과 → 다음 단계
   └─ 재지적 → 시정조치 반복
```

**사용자 개입**: rollback·담당 배정·중간 과정에는 개입하지 않음. 최종 시정조치결과서 및 재감리 통과만 확인한다.

### 4-3. Rollback

**트리거**: PM이 감리결과 검토 후 "중대 결함"이라 판단하는 경우 — 예: 설계감리에서 요구사항 단계까지 영향이 있는 결함. 자동 실행.

**절차**:
1. 되돌아갈 단계 N 및 이후 모든 단계의 산출물을 각 단계 내 `_archived/<YYYYMMDD>-v<seq>/` 로 이동.
2. 해당 단계의 감리 디렉토리도 동일 원칙으로 아카이브.
3. `RTM.md` → `RTM/_archived/<YYYYMMDD>-v<seq>.md` 로 백업.
4. rollback 대상 구간 이후의 감리이력·결과 컬럼은 공란 초기화 (요구사항 ID는 보존).
5. `00_kickoff/rollback-history.md` 에 이벤트 로그:
   | Date | Trigger | Rolled-back to | Archived versions | Reason |
6. 단계 N부터 재수행 시작.

---

## 5. 요구사항추적매트릭스 (RTM)

### 5-1. 형식

파일: `projects/<프로젝트명>/RTM.md` (Markdown 테이블)

| REQ-ID | 요구사항명 | 유형 | 출처 | DESIGN-ID | 설계문서 | PROG-ID | 소스경로 | UT-ID | IT-ID | UAT-ID | 결과 | 감리이력 | 상태 |

단계별 채워지는 컬럼:
- 분석: REQ-ID, 요구사항명, 유형, 출처, IT-ID, UAT-ID (설계 단계의 ID)
- 설계: DESIGN-ID, 설계문서, PROG-ID, UT-ID
- 구현: 소스경로
- 시험: 결과
- 감리: 감리이력 (해당 감리 수행 시)

### 5-2. ID 네이밍 규칙

```
RQ-<seq>               : 요구사항            (예: RQ-001)
DSN-<도메인>-<seq>     : 설계                (예: DSN-LOGIN-01)
PRG-<도메인>-<seq>     : 프로그램 목록        (예: PRG-AUTH-005)
UT-<도메인>-<seq>      : 단위테스트          (예: UT-AUTH-005)
IT-<도메인>-<seq>      : 통합테스트          (예: IT-AUTH-02)
UAT-<seq>              : UAT                 (예: UAT-03)
A-AUDIT-<N>            : N차 분석감리
D-AUDIT-<N>            : N차 설계감리
C-AUDIT-<N>            : N차 종료감리(Closing)
RA-AUDIT-<N>-v<M>      : N차 감리의 M차 재감리
```

### 5-3. 갱신 책임

- PM 이 **단독 수정자**. 각 단계 종료 시 전수 갱신.
- 실무자는 자신의 산출물 프런트매터에 관련 ID 를 기록(`related: [RQ-001, DSN-LOGIN-01]`). PM 이 이를 수거하여 RTM 반영.
- 감리팀은 RTM 을 **읽기 전용**으로 활용 (예: "RQ-005가 소스에 매핑 안 됨" 지적).

### 5-4. Rollback 처리

- 현 RTM → `RTM/_archived/<YYYYMMDD>-v<N>.md`
- 새 RTM에서 되돌아간 구간 이후 컬럼 공란화, 요구사항 ID 유지.
- `감리이력` 컬럼에 rollback 이벤트 기재.

---

## 6. 프로젝트 상태 관리 및 단계 전환

### 6-1. project-state.md

PM이 단독 소유·갱신. 매 이벤트(산출물 완료, 감리 통과, 승인, rollback)마다 즉시 갱신.

**프런트매터**:
```yaml
project: <이름>
started: <YYYY-MM-DD>
scale: small | large
current-stage: 00_kickoff | 01_analysis | ... | 05_deployment
current-step: <자유 서술>
```

**본문 섹션**: `Scale Configuration`, `Stage Progress`(각 단계 체크박스와 상세 항목), `Approval Log`, `Audit Log`, `Rollback History`.

### 6-2. 단계 게이트 체크리스트

`.claude/agents/templates/stage-gates.md` 에 단계별 완료 조건 정의.

예시 (분석):
```
Required artifacts:
  - 01_analysis/requirements.md (RTM의 RQ-xxx 전체 포함)
  - 01_analysis/as-is-analysis.md
  - 01_analysis/to-be-workflow.md
  - 01_analysis/uat-test-cases.md
  - 01_analysis/integration-test-cases.md
  - 각 산출물마다 reviews/ 내 review-v<N>.md 존재
Audit gate (if scale == large):
  - 99_audit/01_analysis-audit/audit-report.md 의 최종 결과 = PASS
    (또는 시정조치→재감리 통과)
Approval gate:
  - project-state.md Approval Log 에 해당 단계 엔트리 존재
```

### 6-3. 단계 전환 프로토콜

```
[단계 N의 모든 산출물 완료]
   ↓
PM: stage-gates.md 기반 자동 검증
   ├─ 미충족 → 누락 항목을 담당 총괄/실무자에 재지시
   └─ 충족 →
       ↓
   (감리 대상이면) 감리 플로우 (§4)
       ↓
   PM: 사용자에 단계 완료 보고 + 승인 요청
       ↓
   사용자 승인 → project-state.md 갱신, 단계 N+1 진입
   사용자 반려 → 사유를 담당자에 재지시 (§8-2)
```

---

## 7. 리뷰 · 병렬 · 에스컬레이션

### 7-1. 리뷰 회의 제도

**원칙**: 모든 산출물은 리뷰를 받는다. 생략 없음. 리뷰 회의록 자체는 리뷰 대상에서 제외(무한 루프 방지).

**최소 2인 원칙** — 작성자 + 리뷰어.

**리뷰 매트릭스**:

| 리뷰 종류 | 필수 참여 | 권장 추가 |
|-----------|----------|-----------|
| 요구사항 리뷰 | AA(작성) + 응용총괄 + PM | 사업관리 |
| 아키텍처 리뷰 | TA + 인프라총괄 + SWA | PM, 보안전문가 |
| DB 설계 리뷰 | data-modeler + DBA + 응용총괄 | AA |
| 프로그램/IF 리뷰 | SWA + 응용총괄 + part-leader | AA |
| 화면 설계 리뷰 | designer+publisher + 응용총괄 | AA |
| 구현(코드) 리뷰 | 개발자 + part-leader 또는 SWA | 응용총괄 |
| 테스트 케이스 리뷰 | tester + QA + 해당 총괄 | PM |
| 테스트 결과 리뷰 | tester + QA + PM | 담당 총괄 |
| 이행 계획 리뷰 | PM + 인프라총괄 + 응용총괄 + QA | 사업관리 |

**오케스트레이션**: 주관자가 Agent 툴로 참여자 병렬 호출 → 의견 취합 → 리뷰 회의록 생성.

**리뷰 회의록 포맷**: `<단계>/reviews/<산출물명>-review-v<N>.md` — 프런트매터(participants, date, target, related IDs) + Findings + Decisions + Follow-up Actions.

**검증**: 리뷰 회의록의 `participants` 수가 2 미만이면 시스템이 경고하고 해당 산출물은 미완료로 본다.

### 7-2. 병렬 작업

**원칙**: 단계 내 의존성 없는 산출물은 반드시 병렬.

- 상위 에이전트는 한 응답 안에서 여러 Agent 툴 호출을 동시 제출.
- 각 산출물 프런트매터 `depends-on:` 으로 DAG 구성.
- 쓰기 충돌 방지: 동일 파일을 여러 에이전트가 동시 수정 금지. 리뷰(읽기)는 병렬 안전.

### 7-3. 에스컬레이션 프로토콜

**사유**: 기술 장애(3회 실패), 요구사항 모호, 의존 산출물 문제, 권한 밖 이슈.

**실무자 반환 포맷** (모든 실무자 프롬프트에 주입):
```
ESCALATION: <한 줄 요약>
Details:
  - ...
Request to: <해결 요청 대상/내용>
```

**처리 흐름**: part-leader → 응용/인프라 총괄 → PM → (필요 시) 사용자. 각 단계에서 자체 해결 가능하면 처리, 불가하면 동일 포맷으로 상위 에스컬레이션.

**로그**: `projects/<프로젝트명>/escalations.md` — Date, From, Issue, Resolved By, Resolution 컬럼.

**에스컬레이션과 Rollback**: 에스컬레이션이 rollback 을 유발하는지 여부는 **PM 판단**.

---

## 8. 엣지 케이스 · 오류 처리 · 시스템 검증

### 8-1. 요구사항 변경 관리 (Change Request)

- 한도 없음. 사용자 재량.
- 절차: 사용자 CR 제출 → PM이 `change-requests/CR-<seq>.md` 등록 → 응용/인프라총괄 병렬 영향 분석 → PM이 사용자에 영향(일정/공수/리스크) 보고 → 사용자 승인 시 RTM에 신규 요구사항 반영, 필요 시 해당 단계로 복귀 (rollback 포함).

### 8-2. 단계 반려

- 사용자 반려 시 PM이 사유를 담당 총괄/실무자에 위임, 수정 후 재보고.
- `project-state.md` Approval Log 에 REJECTED 이벤트 기록.

### 8-3. 다중 감리 실패

- 감리팀은 지적만 지속.
- PM이 근본 재설계 또는 이전 단계 rollback 판단.
- 중대한 경우 사용자에 에스컬레이션.

### 8-4. 프로젝트 중단·재개

- `project-state.md` 로 상태 복원.
- 재개 시 PM 에이전트가 상태 파일 읽고 이어서 진행.
- 단일 프로젝트 전제.

### 8-5. 에이전트 호출 실패

- Agent 툴 3회 재시도.
- 지속 실패 시 에스컬레이션.

### 8-6. 산출물 누락·손상

- 단계 게이트 검증에서 발견, 담당자에 재생성 지시, 반복 실패 시 에스컬레이션.

### 8-7. 시스템 자체 검증 (Meta-Testing) — 전체 포함

**(1) 샘플 프로젝트 E2E** — 작은 규모(예: "도서 관리 API") 과업지시서로 전체 공정 완주 여부 확인.

**(2) 에이전트 단위 페르소나 검증** — 각 에이전트에 표준 입력을 주고 반환 포맷·역할 충실도 확인.

**(3) 감리 독립성 negative test** — 피감리인이 감리팀에 "통과시켜달라" 식 지시 주입 시 감리팀이 거부하는지 확인.

**(4) 리뷰 2인 원칙 검증** — 1인 리뷰 시도 차단, 참여자 2인 미만 회의록 경고.

**(5) Rollback 복원력 검증** — 인위적 감리 실패 주입 → 자동 rollback → archive/RTM 백업/상태 갱신 정상.

**(6) 병렬 호출 충돌 검증** — 동일 파일 병렬 쓰기 시도 시 충돌 감지·회피.

---

## 9. 구현 빌드 순서 (권고)

1. **스켈레톤**: `.claude/agents/` 디렉토리, `audit/` 서브디렉토리, `templates/` 및 `templates/stage-gates.md`.
2. **고정 모델 7개 에이전트 프롬프트**: `project-manager`, `application-director`, `infrastructure-director`, `business-manager`, `quality-assurance`, `tester`, `audit/audit-team`.
3. **동적 모델 13역할 원본 프롬프트**: `templates/<role>.md.tmpl` 형태로 각 역할의 단일 원본을 작성. (AA, SWA, TA, data-modeler, part-leader, backend/batch/web-developer, web-publisher, designer, DBA, security-specialist, infrastructure-engineer)
4. **동적 모델 3버전 파생 생성**: 각 원본을 Opus/Sonnet/Haiku 버전으로 복제하여 39개 파일 생성. frontmatter 의 `name`, `model` 필드만 다름.
5. **산출물 템플릿**: `templates/` 하위에 각 산출물 유형의 Markdown 템플릿(프런트매터 포함).
6. **project-state.md / RTM.md 템플릿**.
7. **Meta-Test 1 (샘플 프로젝트 E2E)** — 최소 규모로 전체 공정을 실제로 한 번 돌려보며 불일치 보정. 이때 난이도 판단 로직도 함께 검증.
8. **Meta-Test 2~6** — negative, 2인 원칙, rollback, 병렬 충돌.

단계별로 문서가 완결된 후 다음 구현 단계로 진행. 각 단계는 별도 커밋.

---

## 10. 미해결 사항 / 향후 결정

- 샘플 프로젝트의 도메인 선정 (Meta-Test 1 입력용).
- 병렬 호출 시 파일 잠금(locking) 구현 방법 — 현재는 "동일 파일 동시 쓰기 금지" 원칙만 선언. 필요 시 `.locks/` 디렉토리 도입 검토.
- `part-leader` 수 동적 결정 방식 (대규모 시 1명 vs 기능 도메인별 다수).
- **감리 세션 개시 방식** — 사용자가 `audit-team` 을 호출하는 구체적 UX(슬래시 커맨드 `/audit <stage>` vs 자연어 지시 vs Claude Code 에이전트 전환). 구현 시 결정.

(향후 구현·운영 중 발견되는 사항은 이 문서를 갱신하여 반영한다.)

---

## 의사결정 로그 (Design Decisions)

| # | 결정 | 사유 |
|---|------|------|
| 1 | 전통 서브에이전트 방식 (Claude Code Agent Teams 미사용) | 3단 계층 필요 → Agent Teams 는 중첩 팀 미지원 |
| 2 | 조직도 3단 고정 + 대규모 시 part-leader 동적 | 사용자 지정 |
| 3 | 감리는 외부 네임스페이스 (audit/) | 외주업체 독립성 반영 |
| 4 | V-Model 폭포수 + 단계별 사용자 승인 필수 | 사용자 지정 |
| 5 | 감리는 지적만, 판단·rollback은 PM 책임 | 사용자 지정 |
| 6 | Rollback 자동 실행 (사용자 개입 없이) | 사용자 지정 |
| 7 | 모든 산출물 Markdown | 사용자 지정 |
| 8 | 모든 작업에 2인 이상 리뷰 | 사용자 지정 |
| 9 | 단계 내 병렬 작업 필수 | 사용자 지정 |
| 10 | 단일 프로젝트 전제 | 사용자 지정 |
| 11 | 동적 모델 선택 (13역할 × Opus/Sonnet/Haiku) + PM·총괄이 난이도 판단 | 사용자 지정 — 정적 할당의 경직성 해소, 비용·품질 균형 확보 |
| 12 | 모든 에이전트 기본 effort = xhigh. 동적 모델은 저난이도 시 조정 허용(보안·아키·모델링 등은 예외) | 사용자 지정 — 재작업 비용 > 토큰 비용 |
