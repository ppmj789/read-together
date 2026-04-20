# WBS — 대규모 복합(웹·배치·데몬·스트리밍·복합 DB) 프로젝트 샘플

본 문서는 사용자가 **전체 파이프라인 완전성 · 담당자 배치 적정성 · 담당자↔input/output 매핑 · 작업 순서**를 종합 점검하기 위한 검토용 WBS 이다. 실제 프로젝트에서는 이 표를 해당 `projects/<name>/00_kickoff/project-plan/wbs/` 로 옮겨 세분·조정한다.

## 가정 (Scope)

- **규모**: `large` — 파트리더 필수 (spec §2-2)
- **애플리케이션**: web(REST API + SPA) + batch + daemon(항시 상주)
- **스트리밍**: Kafka (producer·consumer 양방향, 이벤트 토픽 다수)
- **데이터 저장소**: RDB(OLTP) + NoSQL(이벤트 스토어·조회 전용 캐시)
- **환경**: dev/stg/prd 3-tier, IaC 기반 프로비저닝
- **감리**: 분석 감리(대규모 필수) + 설계 감리 + 종료 감리 (총 3회)

## 파트 분할 원칙 (사용자 정책)

- **파트는 기술 유형(web/batch/daemon) 이 아니라 업무 도메인(회원·결제·구매·카탈로그 등) 기준**으로 분할한다. SOW 분석 결과에 따라 도메인 규모가 크면 한 도메인이 여러 파트로 세분될 수 있고, 규모가 작으면 여러 도메인이 묶일 수 있다 (파트 수 N 가변).
- **각 도메인 파트는 cross-functional 팀** — 해당 도메인의 web 화면 · batch 잡 · daemon/Kafka 컨슈머 · 자기 도메인의 RDB 테이블 · NoSQL 컬렉션을 **모두 자체 저작**. "Data Part" 같은 기술 중심 수평 파트는 두지 않는다 (DB 설계 쏠림 방지).
- **공유 엔티티(여러 도메인이 참조)** 는 소유 파트가 주 저자, 소비 파트들은 `depends-on` 으로 참조 + 교차 파트 합의에서 최종 승인.
- 분석 단계에서 `application-architect` 가 **도메인 분할 매트릭스**를 저작 (`01_analysis/to-be-workflow/part-allocation-matrix.md`) — RQ · 엔티티 · BATCH · 토픽의 파트 소유권 결정.

## 조직 구성 (본 샘플)

- **PM** — 사용자 단일 접점
- **총괄**: `application-director`, `infrastructure-director`
- **상시 자문**: `business-manager`(예산·일정), `quality-assurance`(품질)
- **도메인 파트리더 4 명** (`application-director` 산하, N = 분석 결과 도메인 수; 본 샘플은 4):
  - **P-MEM** — 회원관리 파트
  - **P-PAY** — 결제관리 파트
  - **P-ORD** — 구매관리 파트
  - **P-CAT** — 카탈로그관리 파트
- **인프라 팀** (`infrastructure-director` 산하): `technical-architect`, `database-administrator`, `security-specialist`, `infrastructure-engineer`
- **검증**: `tester`, `audit-team` (분석·설계·종료 3 회)
- **도메인 파트 cross-functional 구성** (사용자 정책: 개발자 저작, 아키텍트·디자이너·DBA·data-modeler 는 Track B 자문 전용):
  - 저작(Track A): `web-developer` + `batch-developer` + `backend-developer`(API · Kafka · DB 마이그레이션) + `web-publisher`(마크업 공동 저작). 해당 도메인에 배치/daemon 이 없으면 해당 역할 생략.
  - 자문(Track B): `software-architect`, `designer`, `data-modeler`, `database-administrator`, `technical-architect`, `security-specialist`, `application-architect`, `tester`
- **공통 설계 저작 (인프라·아키텍처 트랙, 파트 착수 선행)**: `technical-architect`(ARCH — 토폴로지·Kafka·Stream 기반), `security-specialist`(SEC), `infrastructure-engineer`(INF — 스케줄러·모니터링·Kafka 브로커)

## 컬럼 정의

| 컬럼 | 의미 |
|------|------|
| **단계** | V-Model 단계 코드 (00~05) |
| **작업 ID** | `W-<단계>-<seq>` 또는 파트 코드 내포 (예: `W-I-MEM-02` = 구현·회원파트·작업2) |
| **해야할 작업** | 단일 실행 단위 |
| **담당자(주)** | Track A 저작 주체 (1 인) |
| **담당자(자문·검토)** | Track B 자문 또는 리뷰 참여자 |
| **Input 산출물** | 선행 산출물 ID 또는 경로 |
| **Output 산출물** | 생성 산출물 ID 또는 경로 |
| **선행** | 완료 대기할 작업 ID (순서 검증용) |

---

## 00_kickoff

> **WBS 저작·검증 게이트**: 본 샘플 문서의 "00~05 단계 WBS 표 + 사용자 점검 체크리스트 6 섹션" 자체가 W-K-05 의 저작 형식 예시이며, W-K-06 사용자 검증에서 그 체크리스트를 그대로 사용한다. WBS 가 **사용자 ok** 를 받지 못하면 `01_analysis` 로 진입할 수 없다.

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-K-01 | SOW 수령·검토 | PM | — | 사용자 제공 SOW | `00_kickoff/statement-of-work.md` | — |
| W-K-02 | 규모·파트 구성 결정 (large, 도메인 파트 수 N) | PM | application-director, infrastructure-director (Track B) | SOW | `project-state.md` (scale: large) | W-K-01 |
| W-K-03 | 프로젝트 계획 저작 (overview·scope·organization·schedule 만; budget/WBS 는 후속) | PM | — | SOW, 조직안 | `00_kickoff/project-plan/{index,overview,scope,organization,schedule}.md` | W-K-02 |
| W-K-04 | 예산·일정 자문 (모델·effort 가이드 확정) | business-manager (Track B) | — | project-plan 초안 | `agent-call-log.md` + `00_kickoff/project-plan/budget.md` 확정 | W-K-03 |
| W-K-05 | **WBS 저작** (단계·작업 ID·해야할 작업·담당자(주)·담당자(자문)·Input·Output·선행 8 컬럼 + 본 샘플 형식 적용) | PM | application-director, infrastructure-director, 파트리더 후보, QA (Track B) | SOW, project-plan, budget, 도메인 파트 초안, part-allocation 후보 | `00_kickoff/project-plan/wbs/index.md` + `wbs/W-<단계>-<seq>.md` children (전 단계 00~05 망라) | W-K-04 |
| W-K-06 | **WBS 사용자 검증 (ok 게이트)** — 본 문서 "사용자 점검 체크리스트" 6 섹션(파이프라인 완전성·담당자 배치·I/O 매핑·순서·도메인 파트 분할·large 필수) 전 항목 PASS 확인 | user | PM, QA, 총괄 2 명, 파트리더 후보 | WBS 전체 + 체크리스트 | `project-state.md` **WBS-Validation Log** 항목 (결과: ok / 수정요청 + 사유 + 타임스탬프). 수정요청 시 W-K-05 재저작 → W-K-06 재검증 루프 | W-K-05 |
| W-K-07 | 계획 리뷰 (≥2 참여, **검증 완료 WBS 포함 전체 plan**) | PM | QA, 총괄 2 명 | project-plan + ok 받은 WBS | `00_kickoff/reviews/project-plan-review-v1.md` | W-K-06 |
| W-K-08 | 착수 승인 (전 단계 전환 Approval Log) | user | PM | review 결과 + WBS 검증 완료 | `project-state.md` Approval Log (`00_kickoff → 01_analysis`) | W-K-07 |

> **게이트 의미 분리**: W-K-06 = WBS **내용 건전성** (파이프라인·담당자·매핑·순서) 에 대한 사용자 ok. W-K-08 = 프로젝트 착수에 대한 사용자 최종 승인. 둘이 분리되어야 WBS 결함을 review 이전에 잡아 재작성 비용을 최소화한다.

---

## 01_analysis

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-A-01 | 요구사항 수집·분해 (**도메인 기준**) | application-architect | 파트리더 후보들 (Track B) | SOW, 현업 인터뷰 | `01_analysis/requirements/RQ-{MEM,PAY,ORD,CAT,NFR}-*` | W-K-08 |
| W-A-02 | AS-IS 분석 | application-architect | technical-architect (인프라 현황) | 현행 시스템 조사 | `01_analysis/as-is-analysis/AS-*` | W-A-01 |
| W-A-03 | TO-BE 워크플로우 | application-architect | 파트리더 후보들 | RQ-*, AS-* | `01_analysis/to-be-workflow/TB-*` | W-A-02 |
| W-A-03b | **도메인 분할 매트릭스 저작** (도메인 → 파트·엔티티·BATCH·토픽 소유권 매핑, 공유 엔티티 식별) | application-architect | data-modeler, technical-architect, application-director | RQ-\<DOM\>, TB-*, ENT-*(초안) | `01_analysis/to-be-workflow/part-allocation-matrix.md` | W-A-03 |
| W-A-04 | 논리 데이터 모델 초안 (도메인별 엔티티) | data-modeler | DBA (Track B), 파트리더 후보 | RQ-\<DOM\>, TB-*, part-allocation-matrix | `02_design/db/logical/ENT-{MEM,PAY,ORD,CAT}-*` (소유 파트 필드 포함) | W-A-03b |
| W-A-05 | 이벤트·스트림 요구 도출 (Kafka 토픽 맵) | application-architect | software-architect, technical-architect, 관련 파트리더 | RQ-\<DOM\>, TB-*, part-allocation-matrix | `01_analysis/to-be-workflow/TB-STREAM-events.md` (토픽별 생산 소유 파트·소비 파트 명시) | W-A-03b |
| W-A-06 | 비기능 요구 정리 | application-architect | technical-architect, security-specialist | RQ-NFR-* | `01_analysis/requirements/RQ-NFR-*` 세부화 | W-A-01 |
| W-A-07 | UAT 케이스 저작 | tester | QA (Track B) | RQ-* 전체 | `01_analysis/uat-test-cases/UAT-*` | W-A-03 |
| W-A-08 | 통합 테스트 케이스 저작 (BATCH·Stream 시나리오 포함) | tester | QA, software-architect | RQ-*, TB-* | `01_analysis/integration-test-cases/IT-*` | W-A-03 |
| W-A-09 | 영역별 리뷰 (≥2 인) | 각 저자 | QA + director | 각 영역 산출물 | `01_analysis/reviews/<area>-review-v1.md` | W-A-04~08 |
| W-A-10 | 분석 감리 (large 필수) | audit-team (worktree) | — | 01_analysis/* 전체 + RTM analysis | `99_audit/01_analysis-audit/audit-report/*` | W-A-09 |
| W-A-11 | 감리 시정조치 | PM (분배) | 해당 저자 | FIND-* | `corrective-action-{plan,result}/*` + re-audit PASS | W-A-10 |
| W-A-12 | RTM 갱신 | PM | — | 모든 RQ-*, UAT-*, IT-* | `RTM/by-stage/01_analysis.md`, `RTM/index.md` | W-A-11 |
| W-A-13 | 분석 승인 | user | PM | 감리 PASS + RTM | Approval Log | W-A-12 |

---

## 02_design

**재편 원칙 (사용자 정책)**: 아키텍트·디자이너·DBA·data-modeler 는 **Track B 자문 전용**. 파트별 세부 설계(프로그램·인터페이스·화면·배치잡·물리 DB) 는 **각 파트의 개발자가 Track A 로 저작**. 공통 설계(ARCH·SEC·INF) 만 technical-architect / security-specialist / infrastructure-engineer 가 Track A 저작.

### (A) 공통 설계 트랙 (P0 — 인프라·아키텍처, 파트 착수 선행 조건)

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-D-01 | 시스템 아키텍처 (토폴로지) | technical-architect | application-director, security-specialist, software-architect | RQ-NFR, AS-*, TB-* | `02_design/architecture/ARCH-TOPO-*` | W-A-13 |
| W-D-02 | Kafka·Stream 아키텍처 | technical-architect | infrastructure-engineer, software-architect, security-specialist | TB-STREAM-events, ARCH-TOPO | `02_design/architecture/ARCH-STREAM-*` + `02_design/infra/INF-KAFKA-*` | W-D-01 |
| W-D-03 | 보안 리뷰 (공통) | security-specialist | technical-architect, application-director | ARCH-*, RQ-NFR | `02_design/security-review/SEC-*` | W-D-01 |
| W-D-04 | 인프라 상세 (공통: 스케줄러·모니터링·알림 골격) | infrastructure-engineer | technical-architect, DBA, security-specialist | ARCH-*, RQ-NFR | `02_design/infra/INF-*` | W-D-01 |

### (B) 도메인 파트별 세부 설계 트랙 (P-MEM / P-PAY / P-ORD / P-CAT, W-D-04 완료 후 병렬 착수)

각 **도메인 파트**는 cross-functional 로 자기 도메인의 web + batch + daemon **및 자기 도메인의 RDB/NoSQL 테이블**까지 자체 저작. 아키텍트·디자이너·DBA·data-modeler 는 Track B 자문 참여자.

#### 도메인 파트 공통 설계 작업 템플릿 (파트 = `<P>`, 도메인 코드 = `<DOM>`)

각 도메인 파트에 대해 아래 작업 세트를 해당 도메인 기능 유무에 따라 취사 실행. 파트리더(`<P>`) 가 자기 파트 개발자들을 Track A 로 소환해 저작시킨다.

| 작업 ID (패턴) | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|---------------|------|-----------|-------------|-------|--------|------|
| W-D-\<DOM\>-01 | 도메인 화면 PRG 설계 (web) | web-developer(\<P\>) | software-architect, designer, application-architect | RQ-\<DOM\>, ARCH-*, TB-* | `02_design/programs/PRG-\<DOM\>-WEB-*.md` (type: web) | W-D-04 |
| W-D-\<DOM\>-02 | 도메인 API PRG 설계 (서버측) | backend-developer(\<P\>) | software-architect, security-specialist, DBA | RQ-\<DOM\>, ARCH-*, TBL-RDB-\<DOM\>(draft) | `02_design/programs/PRG-\<DOM\>-API-*.md` | W-D-04 |
| W-D-\<DOM\>-03 | 도메인 REST IF 설계 | backend-developer(\<P\>) | software-architect, security-specialist | PRG-\<DOM\>-API | `02_design/interfaces/IF-REST-\<DOM\>-*.md` | W-D-\<DOM\>-02 |
| W-D-\<DOM\>-04 | 도메인 화면설계서 (SCN) | web-developer(\<P\>) | designer (UI/UX·접근성), application-architect | RQ-\<DOM\>, PRG-\<DOM\>-WEB | `02_design/screens/SCN-\<DOM\>-*.md` | W-D-\<DOM\>-01 |
| W-D-\<DOM\>-05 | 화면 마크업·접근성 공동 저작 | web-publisher(\<P\>) | designer | SCN-\<DOM\>-* | SCN-\<DOM\>-* 마크업·접근성 섹션 co-author | W-D-\<DOM\>-04 |
| W-D-\<DOM\>-06 | 도메인 batch PRG 설계 | batch-developer(\<P\>) | software-architect, technical-architect, data-modeler | RQ-\<DOM\>, ARCH-* | `02_design/programs/PRG-\<DOM\>-BAT-*.md` (type: batch) | W-D-04 |
| W-D-\<DOM\>-07 | 도메인 배치잡 설계 (스케줄·재처리·run-window) | batch-developer(\<P\>) | infrastructure-engineer, DBA, data-modeler | PRG-\<DOM\>-BAT, TBL-RDB-\<DOM\>/COLL-NOSQL-\<DOM\>(draft) | `02_design/batch-jobs/BATCH-\<DOM\>-*.md` | W-D-\<DOM\>-06 |
| W-D-\<DOM\>-08 | 도메인 daemon PRG 설계 (Kafka 컨슈머/프로듀서) | backend-developer(\<P\>) | technical-architect, software-architect, DBA, security-specialist | RQ-\<DOM\>, ARCH-STREAM | `02_design/programs/PRG-\<DOM\>-DMN-*.md` (type: daemon) | W-D-04 |
| W-D-\<DOM\>-09 | 도메인 Kafka 토픽 스키마·계약 | backend-developer(\<P\>) | software-architect, security-specialist | PRG-\<DOM\>-DMN, ARCH-STREAM | `02_design/interfaces/IF-KAFKA-\<DOM\>-*.md` | W-D-\<DOM\>-08 |
| W-D-\<DOM\>-10 | 도메인 엔티티 세밀화 (공유 엔티티 조정) | backend-developer(\<P\>) | data-modeler, DBA, application-architect | ENT-\<DOM\>-* (W-A-04 초안) | `02_design/db/logical/ENT-\<DOM\>-*.md` 확장 | W-D-04 |
| W-D-\<DOM\>-11 | 도메인 RDB 물리 설계 (인덱스·파티션) | backend-developer(\<P\>) | DBA (운영·튜닝), data-modeler | ENT-\<DOM\>-* | `02_design/db/physical/TBL-RDB-\<DOM\>-*.md` | W-D-\<DOM\>-10 |
| W-D-\<DOM\>-12 | 도메인 NoSQL 물리 설계 (샤드키·인덱스) | backend-developer(\<P\>) | DBA, technical-architect, data-modeler | ENT-\<DOM\>-* | `02_design/db/physical/COLL-NOSQL-\<DOM\>-*.md` | W-D-\<DOM\>-10 |
| W-D-\<DOM\>-13 | **도메인 단위 테스트 케이스 저작** (자기 저작 산출물 매핑) | 각 개발자(\<P\>): web-developer→SCN/PRG-WEB, backend-developer→PRG-API·DMN·IF·TBL·COLL, batch-developer→BATCH·PRG-BAT | tester (케이스 설계·커버리지·엣지 Track B 자문), QA | PRG-\<DOM\>-*, SCN-\<DOM\>-*, BATCH-\<DOM\>-*, IF-\<DOM\>-*, TBL-RDB-\<DOM\>, COLL-NOSQL-\<DOM\> | `02_design/unit-test-cases/UT-\<DOM\>-*.md` (저작자별 산출물에 `depends-on` 매핑) | W-D-\<DOM\>-01~12 (저작자 완료분부터 부분 착수) |
| W-D-\<DOM\>-14 | **도메인 파트 설계 리뷰 (≥2 인)** | 파트리더(\<P\>) 주관, 개발자 참여 | software-architect / designer / data-modeler / DBA / security-specialist / application-director / 인접 도메인 파트리더 | 해당 파트 전 설계 산출물 (01~13) | `02_design/reviews/design-\<DOM\>-v1.md` | W-D-\<DOM\>-01~13 |

> 도메인별로 모든 14 작업이 필요한 건 아니다. 해당 도메인에 배치가 없으면 06·07 생략, daemon/Kafka 가 없으면 08·09 생략, NoSQL 을 쓰지 않으면 12 생략. 13·14 는 모든 도메인 파트 필수.

#### 본 샘플 4 도메인 파트 특이사항

- **P-MEM (회원관리)**: 01~05(화면·API·IF·SCN), 10~11(ENT-MEM, TBL-RDB-MEM·USER·ROLE), 06·07(PWD 만료 알림 배치). **공유 엔티티 소유**: `ENT-USER` (결제·구매·카탈로그가 `depends-on` 참조). 대규모 daemon 없음.
- **P-PAY (결제관리)**: 01~05(결제 화면), 02·03(결제 API·Webhook), 06·07(정산 batch·미수 처리), 08·09(결제 이벤트 produce → 구매/알림 파트 consume), 10~12(ENT-PAY, TBL-RDB-PAY, COLL-NOSQL-PAY-EVENT). **공유 엔티티 참조**: `ENT-USER(P-MEM 소유)`, `ENT-ORDER(P-ORD 소유)`.
- **P-ORD (구매관리)**: 01~05(장바구니·주문·주문조회), 02·03, 06·07(장바구니 만료·정기주문 배치), 08·09(주문 이벤트 produce + 결제·카탈로그 이벤트 consume), 10~12(ENT-ORDER, TBL-RDB-ORDER, COLL-NOSQL-ORDER-EVENT). **공유 엔티티 소유**: `ENT-ORDER`.
- **P-CAT (카탈로그관리)**: 01~05(상품·검색 화면), 02·03(상품 API), 06·07(재고·검색 인덱스 배치), 08·09(상품 변경 이벤트 produce), 10~12(ENT-PRODUCT, TBL-RDB-PRODUCT, COLL-NOSQL-PRODUCT-SEARCH). **공유 엔티티 소유**: `ENT-PRODUCT`.

### (C) 공통 후행 작업 (파트 산출물 수렴)

> 단위 테스트 케이스 저작(W-D-\<DOM\>-13) 과 파트 설계 리뷰(W-D-\<DOM\>-14) 는 도메인 파트 내부 작업 (B) 로 편입. (C) 에는 교차 합의·감리·RTM·승인만 남는다.

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-D-05 | 교차 파트 합의 (IF-REST 소비자·IF-KAFKA 토픽 계약·**공유 엔티티 소유권·depends-on 매트릭스**) | 생산자/소유 측 파트리더 주관 | software-architect, data-modeler (공유 엔티티), 소비자/참조 측 파트리더, technical-architect | IF-REST-*, IF-KAFKA-*, ENT-* (공유 엔티티 후보) | `02_design/reviews/cross-part-interface-v1.md` + `01_analysis/to-be-workflow/part-allocation-matrix.md` 갱신 | W-D-\<DOM\>-14 (모든 파트 리뷰 완료) |
| W-D-06 | 설계 감리 | audit-team (worktree) | — | 02_design 전체 + RTM design | `99_audit/02_design-audit/audit-report/*` | W-D-05 |
| W-D-07 | 감리 시정조치 | PM (분배) → 해당 저자 (개발자) | 파트리더 | FIND-* | corrective-action-* + re-audit PASS | W-D-06 |
| W-D-08 | RTM 갱신 (REQ↔PRG·SCN·BATCH·IF·UT + by-artifact 역색인) | PM | 각 저자, 파트리더 | 모든 설계 산출물 | `RTM/by-stage/02_design.md`, `RTM/by-artifact/*` | W-D-07 |
| W-D-09 | 설계 승인 | user | PM | 감리 PASS + RTM | Approval Log | W-D-08 |

---

## 03_implementation (도메인 파트 병렬)

각 도메인 파트가 자기 파트의 web·API·batch·daemon·DB 마이그레이션·단위 테스트 실행까지 자체 구현. 공통 인프라만 `infrastructure-engineer` 담당.

### 도메인 파트 공통 구현 작업 템플릿 (파트 = `<P>`, 도메인 코드 = `<DOM>`)

| 작업 ID (패턴) | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|---------------|------|-----------|-------------|-------|--------|------|
| W-I-\<DOM\>-01 | 화면 프런트 구현 | web-developer(\<P\>) | designer, web-publisher | PRG-\<DOM\>-WEB, SCN-\<DOM\>-*, IF-REST-\<DOM\> | `src/\<dom\>/web/*` | W-D-09 |
| W-I-\<DOM\>-02 | API 백엔드 구현 | backend-developer(\<P\>) | 파트리더(\<P\>), software-architect, security-specialist | PRG-\<DOM\>-API, IF-REST-\<DOM\>, TBL-RDB-\<DOM\> | `src/\<dom\>/api/*` (헤더 PRG-*·RQ-*) | W-D-09 |
| W-I-\<DOM\>-03 | 마크업·스타일 | web-publisher(\<P\>) | designer | SCN-\<DOM\>-* | `src/\<dom\>/web/styles/*`, components | W-I-\<DOM\>-01 (동시 가능) |
| W-I-\<DOM\>-04 | 배치잡 구현 | batch-developer(\<P\>) | 파트리더(\<P\>), DBA, infrastructure-engineer | PRG-\<DOM\>-BAT, BATCH-\<DOM\>-*, TBL-RDB-\<DOM\>/COLL-NOSQL-\<DOM\> | `src/\<dom\>/batch/*` (**헤더 PRG-* + BATCH-* + RQ-* 3 종**) | W-D-09 |
| W-I-\<DOM\>-05 | Kafka producer 구현 | backend-developer(\<P\>) | technical-architect, security-specialist | PRG-\<DOM\>-DMN, IF-KAFKA-\<DOM\> (produce) | `src/\<dom\>/stream/producer/*` | W-D-09 |
| W-I-\<DOM\>-06 | Kafka consumer 구현 (오프셋·DLQ·백프레셔) | backend-developer(\<P\>) | technical-architect, DBA | PRG-\<DOM\>-DMN, IF-KAFKA-\<소비대상\>, COLL-NOSQL-\<DOM\> | `src/\<dom\>/stream/consumer/*` | W-D-09 |
| W-I-\<DOM\>-07 | 데몬 헬스체크·메트릭 | backend-developer(\<P\>) | infrastructure-engineer | PRG-\<DOM\>-DMN | `src/\<dom\>/stream/health/*` | W-I-\<DOM\>-05~06 |
| W-I-\<DOM\>-08 | 도메인 RDB 마이그레이션 | backend-developer(\<P\>) | DBA | TBL-RDB-\<DOM\>-* | `src/\<dom\>/migrations/*` (+ 롤백) | W-D-09 |
| W-I-\<DOM\>-09 | 도메인 NoSQL 초기화·인덱스 | backend-developer(\<P\>) | DBA | COLL-NOSQL-\<DOM\>-* | `src/\<dom\>/nosql-init/*` | W-D-09 |
| W-I-\<DOM\>-10 | 도메인 정합성 검증 스크립트 | backend-developer(\<P\>) | data-modeler, DBA | ENT-\<DOM\>-*, TBL-\<DOM\>-*, COLL-\<DOM\>-* | `src/\<dom\>/data-checks/*` | W-I-\<DOM\>-08~09 |
| W-I-\<DOM\>-11 | 파트 단위 테스트 실행 | 각 개발자(\<P\>) | tester (케이스 해석 자문) | UT-\<DOM\>-* | `03_implementation/unit-test-results/UT-RES-\<DOM\>-*` (batch 는 BATCH-* `depends-on` 필수) | W-I-\<DOM\>-01~10 |

> 도메인별로 모든 11 작업이 필요한 건 아니다. 해당 도메인에 화면이 없으면 01·03 생략, 배치 없으면 04, daemon/Kafka 없으면 05~07, NoSQL 없으면 09 생략. 02(API) 와 08(RDB 마이그레이션) 은 사실상 전 도메인 필수.

#### 본 샘플 4 도메인 파트 구현 특이사항

- **P-MEM**: 01·02·03·08·11 + 소규모 W-I-MEM-04 (PWD 만료 알림), daemon 없음.
- **P-PAY**: 01~11 전부. Webhook 보안 W-I-PAY-02 는 `security-specialist` 필수 자문. 정산 배치 W-I-PAY-04 는 `DBA` + `technical-architect` 대용량 자문.
- **P-ORD**: 01~11 전부. 주문 생성 → 결제 요청 IF 호출 W-I-ORD-02 에서 P-PAY `IF-REST-PAY` 소비자 측 구현.
- **P-CAT**: 01·02·03·04(재고·인덱싱)·05(상품 변경 produce)·08·09(검색 NoSQL)·11. daemon consumer 없음 (produce 전용).

### 공통 인프라·수렴

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-I-C-01 | 컨테이너·IaC | infrastructure-engineer | technical-architect | INF-* | `infra/{Dockerfile,compose,IaC}` | W-D-09 |
| W-I-C-02 | Kafka 브로커 운영 구성 | infrastructure-engineer | technical-architect | INF-KAFKA, IF-KAFKA | `infra/kafka/*` (IF-KAFKA-* `depends-on`) | W-I-C-01 |
| W-I-C-03 | 스케줄러 (cron/timer/cloud scheduler) | infrastructure-engineer | — | BATCH-*, INF-* | `infra/schedulers/*` (**BATCH-* `depends-on` 필수**) | W-I-C-01 |
| W-I-C-04 | 모니터링·알림 | infrastructure-engineer | security-specialist | ARCH-*, INF-* | `infra/monitoring/*`, `infra/alerts/*` | W-I-C-01 |
| W-I-C-05 | CI/CD 파이프라인 | infrastructure-engineer | part-leader 전원 | 전 src | `.github/workflows/*` | W-I-C-01 |
| W-I-C-06 | 도메인 파트별 코드 리뷰 (≥2) | 각 파트리더 + SWA (자문) | — | 각 파트 src | `03_implementation/reviews/<DOM>-review-v1.md` | W-I-\<DOM\>-11 |
| W-I-C-07 | MOCK → real transition checklist | PM | infrastructure-engineer | 전 src | `03_implementation/mock-to-real-transition.md` | W-I-C-01~05 |
| W-I-C-08 | RTM 구현 컬럼 채움 | PM | 각 저자 | 전 UT-RES, 전 src | `RTM/by-stage/03_implementation.md` | W-I-C-06 |
| W-I-Z-01 | 구현 승인 | user | PM | 전체 리뷰 + RTM | Approval Log | W-I-C-07, W-I-C-08 |

---

## 04_test

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-T-01 | 테스트 환경 구축 | infrastructure-engineer | technical-architect | `infra/*`, mock-to-real checklist | 테스트 환경 가동 | W-I-Z-01 |
| W-T-02 | 통합 테스트 실행 (**모든 BATCH-ID 커버**) | tester | QA, part-leader 전원 | IT-*, 전 UT-RES | `04_test/integration-test-results/IT-RES-*` | W-T-01 |
| W-T-03 | 시스템 테스트 (성능·장애복구·Kafka lag) | tester | technical-architect, DBA | ARCH-*, IT-* | `04_test/system-test-results/ST-RES-*` | W-T-02 |
| W-T-04 | UAT 실행 | tester | QA, 사용자 | UAT-* | `04_test/uat-results/UAT-RES-*` | W-T-03 |
| W-T-05 | QA 리포트 | quality-assurance | tester | 모든 RES | `04_test/qa-report/*` | W-T-04 |
| W-T-06 | CR 처리 (FAIL 발생 시) | PM | director, 저자 | 실패 결과 + 영향분석 | `change-requests/CR-*/{request,impact-analysis,decision}.md` | W-T-02~04 (필요 시) |
| W-T-07 | 결과 리뷰 (≥2) | QA + tester + director | — | RES + qa-report | `04_test/reviews/test-review-v1.md` | W-T-05 |
| W-T-08 | RTM 시험 컬럼 채움 | PM | tester | 전 RES | `RTM/by-stage/04_test.md` | W-T-07 |
| W-T-09 | 시험 승인 (CONDITIONAL PASS 포함) | user | PM | 리뷰 + carry-forward 명세 | Approval Log | W-T-08 |

---

## 05_deployment

| 작업 ID | 해야할 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-R-01 | 배포 계획 (단계·롤백·배치 스케줄러 활성화) | PM | infrastructure-engineer, DBA | ARCH-*, INF-*, BATCH-* | `05_deployment/deployment-plan/DEPLOY-*` (BATCH-* `depends-on`) | W-T-09 |
| W-R-02 | 운영 매뉴얼 (도메인 파트별 + **모든 BATCH-ID**) | 각 파트리더 | infrastructure-engineer | PRG-\<DOM\>, BATCH-\<DOM\>, IF-KAFKA-\<DOM\>, SEC-* | `05_deployment/operation-manual/OPS-\<DOM\>-*` (**BATCH-ID 1:1 커버 + daemon/consumer 모니터링 포인트**) | W-R-01 |
| W-R-03 | 교육 자료 (배치 운영 섹션 포함) | application-director | 각 파트리더 | OPS-*, 사용자 가이드 초안 | `05_deployment/training-material/TRAIN-*` | W-R-02 |
| W-R-04 | 보안 최종 검토 (secrets·감사로그·알림) | security-specialist | technical-architect | DEPLOY-*, SEC-* | `agent-call-log.md` 보안 자문 + SEC-* v2 | W-R-01 |
| W-R-05 | 이행 리뷰 (≥2) | director + QA | 각 파트리더 | 위 모두 | `05_deployment/reviews/deployment-review-v1.md` | W-R-02~04 |
| W-R-06 | 종료 감리 | audit-team | — | 전 프로젝트 + 전 RTM | `99_audit/03_closing-audit/audit-report/*` | W-R-05 |
| W-R-07 | 감리 시정조치 | PM (분배) | 해당 저자 | FIND-* | corrective-action-* + re-audit PASS | W-R-06 |
| W-R-08 | 배포 실행 (환경별 순차 dev→stg→prd) | infrastructure-engineer | DBA, security-specialist | DEPLOY-* | 배포 실행 로그 + `rollback-history.md` | W-R-07 |
| W-R-09 | 배포 후 검증 (smoke · batch 첫 실행 · stream lag) | tester + infrastructure-engineer | part-leader 전원 | 운영 모니터링 | 검증 결과 기록 | W-R-08 |
| W-R-10 | RTM deployment 컬럼 채움 | PM | — | 배포 단위 매핑 | `RTM/by-stage/05_deployment.md` | W-R-09 |
| W-R-11 | 최종 승인 | user | PM | 종결 감리 + 배포 검증 | Approval Log → `current-stage: closed` | W-R-10 |

---

## 사용자 점검 체크리스트

각 항목을 위 표 위에서 스캔하여 누락·오배치를 찾는 용도.

### 1. 파이프라인 완전성
- [ ] 분석 → 설계 → 구현 → 시험 → 이행 각 단계에 승인 게이트(Approval Log) 존재?
- [ ] 감리 3 회(분석·설계·종료) 모두 선행 산출물·시정조치 사이클 포함?
- [ ] Kafka·NoSQL·RDB 각각의 설계 산출물(ARCH-STREAM, COLL-NOSQL, TBL-RDB) 이 분리돼 있는가?
- [ ] 데몬·배치·웹 각 유형이 프로그램 목록(PRG type)·UT·IT·OPS 까지 일관되게 흘러가는가?

### 2. 담당자 배치 적정성
- [ ] 파트리더 4 명이 각 파트의 **설계·구현·리뷰·운영매뉴얼·CR 대응**을 모두 커버?
- [ ] **파트별 설계 산출물(PRG / SCN / BATCH / IF / 파트별 TBL·COLL)의 주 저자가 모두 개발자 역할**이고, 아키텍트(`software-architect`, `technical-architect`)·`designer`·`database-administrator`·`data-modeler` 는 **담당자(자문) 컬럼에만** 등장?
- [ ] 공통 설계(ARCH / SEC / INF) 만 `technical-architect`·`security-specialist`·`infrastructure-engineer` 가 주 저자?
- [ ] 인프라(스케줄러·Kafka·모니터링) 는 `infrastructure-engineer` 단독 저자, `technical-architect`·`security-specialist`·DBA 는 자문?
- [ ] **단위 테스트 케이스(02_design UT) 는 각 도메인 파트 개발자가 자기 저작 산출물에 매핑하여 저작**, tester 는 Track B 자문으로만 참여? 상위 테스트(통합·시스템·UAT) 저작·실행만 `tester` 담당?
- [ ] 감리(audit-team) 는 별도 worktree 에서만 작동, 프로젝트 산출물 직접 수정 없음?

### 3. 산출물 매핑 (I/O)
- [ ] 모든 PRG-* frontmatter `type` 이 web/batch/daemon 중 하나?
- [ ] web PRG → SCN 양방향, batch PRG → BATCH 양방향 연결이 설계 단계에 담겨있음?
- [ ] BATCH-* 가 UT → UT-RES → IT-RES → OPS → DEPLOY 까지 downstream 으로 모두 참조됨?
- [ ] Kafka IF (IF-KAFKA-*) 가 Stream 구현·consumer·producer 코드 헤더·IT 시나리오에 모두 매핑?
- [ ] RTM: RQ → PRG → 유형별(SCN/BATCH/IF) → UT → UT-RES → IT-RES → UAT-RES → OPS 체인이 각 by-stage 에 채워짐?

### 4. 순서 (Precedence)
- [ ] 논리 DB(ENT-*) 는 분석 단계에서 시작(W-A-04), 물리 DB(TBL-RDB/COLL-NOSQL) 는 설계 단계에서만 시작?
- [ ] 각 도메인 파트의 배치잡 설계(BATCH-\<DOM\>-*) 는 그 파트의 batch PRG 설계(W-D-\<DOM\>-06) 이후에만 시작?
- [ ] 파트별 세부 설계(W-D-\<DOM\>-*) 는 공통 설계(W-D-04 완료) 이후에만 착수?
- [ ] 파트별 설계 저작은 모두 개발자(backend/web/batch/web-publisher) 가 수행, 아키텍트·디자이너·DBA·data-modeler 는 "담당자(자문)" 컬럼에만 등장?
- [ ] 단위 테스트 케이스(W-D-\<DOM\>-13) 와 파트 설계 리뷰(W-D-\<DOM\>-14) 가 각 도메인 파트 내부 작업으로 들어가 있고, tester 는 "담당자(자문)" 컬럼에만 등장?
- [ ] 교차 파트 합의(W-D-05) 가 **모든 파트 설계 리뷰(W-D-\<DOM\>-14) 완료 후**, 설계 감리(W-D-06) 앞에 배치됨?
- [ ] 구현 착수(W-I-\<DOM\>-01~10) 는 설계 승인(W-D-09) 이후에만 허용? (도메인 파트 동시 착수 가능)
- [ ] 테스트 환경(W-T-01) 은 MOCK → real checklist(W-I-C-07) 이후?
- [ ] 배포(W-R-08) 는 종료 감리 PASS(W-R-07) 이후?

### 5. 도메인 파트 분할 적정성 (사용자 정책 핵심)
- [ ] **파트가 기술 유형(web/batch/daemon) 이 아니라 도메인(업무) 기준**으로 분할됨? 파트 이름이 `MEM/PAY/ORD/CAT` 같은 도메인 명?
- [ ] **DB 설계(TBL/COLL) 가 한 파트로 쏠리지 않음** — 각 도메인 파트가 자기 도메인의 TBL-RDB-\<DOM\>-* / COLL-NOSQL-\<DOM\>-* 를 자체 저작?
- [ ] 각 도메인 파트가 **cross-functional**(web + batch + backend(API·Kafka·DB)) 로 구성되어 모든 계층을 자체 커버?
- [ ] **공유 엔티티 소유·참조** 가 `part-allocation-matrix.md` 에 명시, 소비 파트는 `depends-on` 으로만 참조?
- [ ] 도메인 규모 차이에 따라 파트 개수·파트리더 구성이 조정된 흔적? (예: 결제 규모 크면 P-PAY 를 P-PAY-CHECKOUT / P-PAY-SETTLEMENT 로 분할)

### 6. 대규모(large) 필수 요소
- [ ] 도메인 파트리더 전원이 실제 작업(W-D-\<DOM\>-* + W-I-\<DOM\>-* + W-R-02) 에 등장?
- [ ] `99_audit/01_analysis-audit` (분석 감리, 대규모 전용) 포함?
- [ ] `RTM/by-part/<DOM>.md` 가 **도메인 파트별** RTM 관리에 사용되도록 계획에 명시? (현 WBS 표엔 compact 표기, 실제 프로젝트에서 추가)

---

## 실 프로젝트 이관 시 주의

1. 이 표의 `W-<단계>-<seq>` ID 는 그대로 `projects/<name>/00_kickoff/project-plan/wbs/W-*.md` 의 child ID 로 사용 가능.
2. 각 작업 행을 하나의 `W-*.md` 파일로 분해하면 drift-guard(`validate_artifact_hierarchy.py`) 가 `depends-on`(선행) / `referenced-by`(후행) 양방향 자동 검증한다.
3. `RTM/index.md` 의 단계별 진행 요약 표는 이 WBS 의 단계별 작업 수·완료 수와 1:1 로 일치해야 한다.
