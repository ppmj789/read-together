# WBS — 대규모 복합(웹·배치·데몬·스트리밍·복합 DB) 프로젝트 샘플

본 문서는 사용자가 전체 파이프라인·담당자 배치·산출물 매핑·작업 순서를
종합 점검하기 위한 검토용 WBS 이다. 실제 프로젝트에서는 이 표를 해당
`projects/<name>/00_kickoff/project-plan/wbs/` 로 옮겨 세분·조정한다.

## 가정 (Scope Assumption)

- **규모**: `large` — 파트리더 필수 (spec §2-2)
- **애플리케이션 특성**: web(REST API + SPA) + batch + daemon(항시 상주)
- **스트리밍**: Kafka (producer·consumer 양방향, 이벤트 토픽 다수)
- **데이터 저장소**: RDB(OLTP) + NoSQL(이벤트 스토어·조회 전용 캐시)
- **환경**: dev/stg/prd 3-tier, IaC 기반 프로비저닝

## 조직 구성

- **PM** — 사용자 단일 접점
- **총괄**: `application-director`, `infrastructure-director`
- **상시 자문**: `business-manager`(예산·일정), `quality-assurance`(품질)
- **애플리케이션 파트리더 4 명** (`application-director` 산하):
  - P1 — Web Part Leader (프런트·API)
  - P2 — Batch Part Leader (배치잡)
  - P3 — Stream Part Leader (Kafka consumer·producer, daemon)
  - P4 — Data Part Leader (RDB·NoSQL·마이그레이션·정합성)
- **인프라 팀** (`infrastructure-director` 산하):
  - `technical-architect`, `database-administrator`, `security-specialist`, `infrastructure-engineer`
- **검증**: `tester`, `audit-team`(분석·설계·종료 각 3 회)
- **실무 role 매핑** (파트별):
  - P1: `application-architect`, `software-architect`, `designer`, `web-publisher`, `web-developer`, `backend-developer`
  - P2: `software-architect`, `batch-developer`, `data-modeler`(자문)
  - P3: `software-architect`, `backend-developer`(Kafka 담당), `technical-architect`(자문)
  - P4: `data-modeler`, `database-administrator`(공동), `backend-developer`(마이그레이션)

## 컬럼 정의

| 컬럼 | 의미 |
|------|------|
| 단계 | V-Model 단계 코드 (00~05) |
| 작업 ID | `W-<단계>-<seq>` 또는 파트 코드 내포 (`W-I-W-01` = 구현·Web) |
| 해야할 작업 | 단일 실행 단위 |
| 담당자(주) | Track A 저작 주체 (1인) |
| 담당자(자문·검토) | Track B 자문 또는 리뷰 참여자 |
| Input 산출물 | 선행 산출물 ID 또는 경로 |
| Output 산출물 | 생성 산출물 ID 또는 경로 |
| 선행 | 완료 대기할 작업 ID(순서) |

---

## 00_kickoff

| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-K-01 | SOW 수령·검토 | PM | — | 사용자 제공 SOW | `00_kickoff/statement-of-work.md` | — |
| W-K-02 | 규모·파트 구성 결정(large, P1~P4) | PM | application-director, infrastructure-director (Track B) | SOW | `project-state.md` (scale: large) | W-K-01 |
| W-K-03 | 프로젝트 계획 저작 | PM | — | SOW, 조직안 | `00_kickoff/project-plan/{overview,scope,organization,schedule,budget,wbs}.md` | W-K-02 |
| W-K-04 | 예산·일정 자문 | business-manager (Track B) | — | project-plan 초안 | `agent-call-log.md` + `budget.md` 확정 | W-K-03 |
| W-K-05 | 계획 리뷰 (≥2 참여) | PM | QA, 총괄 2 명 | project-plan | `00_kickoff/reviews/project-plan-review-v1.md` | W-K-04 |
| W-K-06 | 착수 승인 | user | PM | review 결과 | `project-state.md` Approval Log | W-K-05 |

---

## 01_analysis

| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-A-01 | 요구사항 수집·분해 | application-architect | 파트리더 P1~P4 (Track B) | SOW, 현업 인터뷰 | `01_analysis/requirements/RQ-{WEB,BAT,STR,DAT,NFR}-*` | W-K-06 |
| W-A-02 | AS-IS 분석 | application-architect | technical-architect(인프라 현황) | 현행 시스템 조사 | `01_analysis/as-is-analysis/AS-*` | W-A-01 |
| W-A-03 | TO-BE 워크플로우 | application-architect | 파트리더 P1~P4 | RQ-*, AS-* | `01_analysis/to-be-workflow/TB-*` | W-A-02 |
| W-A-04 | 논리 데이터 모델 초안 (RDB + NoSQL 범위) | data-modeler | DBA(Track B) | RQ-DAT, TB-* | `02_design/db/logical/ENT-*` (분석 단계 착수 허용) | W-A-03 |
| W-A-05 | 이벤트·스트림 요구 도출 (Kafka 토픽 맵) | application-architect | software-architect, technical-architect | RQ-STR-*, TB-* | `01_analysis/to-be-workflow/TB-STREAM-events.md` | W-A-03 |
| W-A-06 | 비기능 요구 정리 | application-architect | technical-architect, security-specialist | RQ-NFR-* | `01_analysis/requirements/RQ-NFR-*` 세부화 | W-A-01 |
| W-A-07 | UAT 케이스 저작 | tester | QA(Track B) | RQ-* 전체 | `01_analysis/uat-test-cases/UAT-*` | W-A-03 |
| W-A-08 | 통합 테스트 케이스 저작 | tester | QA, software-architect | RQ-*, TB-* | `01_analysis/integration-test-cases/IT-*` (BATCH·Stream 시나리오 포함) | W-A-03 |
| W-A-09 | 영역별 리뷰 (≥2) | 각 저자 | QA + director | 각 영역 산출물 | `01_analysis/reviews/<area>-review-v1.md` | W-A-04~08 |
| W-A-10 | 분석 감리 | audit-team (worktree) | — | 01_analysis/* 전체 + RTM analysis | `99_audit/01_analysis-audit/audit-report/*` | W-A-09 |
| W-A-11 | 감리 시정조치 | PM (분배) | 해당 저자 | FIND-* | `corrective-action-{plan,result}/*` + re-audit PASS | W-A-10 |
| W-A-12 | RTM 갱신 | PM | — | 모든 RQ-*, UAT-*, IT-* | `RTM/by-stage/analysis.md`, `RTM/index.md` | W-A-11 |
| W-A-13 | 분석 승인 | user | PM | 감리 PASS + RTM | Approval Log | W-A-12 |

---

## 02_design

| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-D-01 | 시스템 아키텍처 (토폴로지) | technical-architect | application-director, security-specialist | RQ-NFR, AS-*, TB-* | `02_design/architecture/ARCH-TOPO-*` | W-A-13 |
| W-D-02 | RDB 물리 설계 | database-administrator | data-modeler | ENT-* | `02_design/db/physical/TBL-RDB-*` | W-A-04 |
| W-D-03 | NoSQL 물리 설계 (컬렉션·샤드키·인덱스) | database-administrator | data-modeler | ENT-* | `02_design/db/physical/COLL-NOSQL-*` | W-A-04 |
| W-D-04 | Kafka·Stream 아키텍처 설계 | technical-architect | infrastructure-engineer, software-architect | TB-STREAM-events, ARCH-TOPO | `02_design/architecture/ARCH-STREAM-*` + `02_design/infra/INF-KAFKA-*` | W-D-01 |
| W-D-05 | 프로그램 목록 (type: web/batch/daemon) | software-architect | 파트리더 P1~P3 | RQ-*, ARCH-* | `02_design/programs/PRG-*` (frontmatter `type` 필수) | W-D-01 |
| W-D-06 | 인터페이스 설계 (REST + Kafka 토픽 스키마) | software-architect | DBA, security-specialist | PRG-*, ARCH-STREAM | `02_design/interfaces/IF-REST-*, IF-KAFKA-*` | W-D-05 |
| W-D-07 | 화면 설계 (web PRG 용) | designer | web-publisher, application-architect | PRG-web(type:web), RQ-WEB | `02_design/screens/SCN-*` (PRG-web 과 양방향 연결) | W-D-05 |
| W-D-08 | 배치잡 설계 (batch PRG 용) | software-architect | infrastructure-engineer, DBA | PRG-batch(type:batch), BATCH 정책 | `02_design/batch-jobs/BATCH-*` (PRG-batch 양방향 연결) | W-D-05 |
| W-D-09 | 데몬/스트림 컨슈머 내부 설계 | software-architect | technical-architect, DBA | PRG-daemon(type:daemon), IF-KAFKA | `02_design/programs/PRG-daemon-*` 확장 (오프셋·백프레셔·DLQ 정책 포함) | W-D-06 |
| W-D-10 | 단위 테스트 케이스 | tester | QA | PRG-*, SCN-*, BATCH-*, IF-* | `02_design/unit-test-cases/UT-*` (유형별 SCN/BATCH 커버 필수) | W-D-05~09 |
| W-D-11 | 보안 리뷰 | security-specialist | technical-architect | ARCH-*, IF-*, PRG-* | `02_design/security-review/SEC-*` | W-D-06 |
| W-D-12 | 인프라 상세 설계 | infrastructure-engineer | technical-architect, DBA | ARCH-*, BATCH-* | `02_design/infra/INF-*` (스케줄러·모니터링·알림, BATCH-ID depends-on 필수) | W-D-08 |
| W-D-13 | 파트별 설계 리뷰 (P1~P4) | 각 파트리더 | director + 저자 | 각 영역 | `02_design/reviews/design-<area>-v1.md` | W-D-10~12 |
| W-D-14 | 설계 감리 | audit-team | — | 02_design/* 전체 + RTM design | `99_audit/02_design-audit/audit-report/*` | W-D-13 |
| W-D-15 | 감리 시정조치 | PM (분배) | 해당 저자 | FIND-* | corrective-action-* + re-audit PASS | W-D-14 |
| W-D-16 | RTM 갱신 (REQ↔PRG·SCN·BATCH·IF·UT 매핑) | PM | 각 저자 | 모든 설계 산출물 | `RTM/by-stage/design.md`, `RTM/by-artifact/*` | W-D-15 |
| W-D-17 | 설계 승인 | user | PM | 감리 PASS + RTM | Approval Log | W-D-16 |

---

## 03_implementation (파트별 병렬)

### Web Part (P1)
| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-I-W-01 | API 백엔드 구현 | backend-developer (P1) | part-leader P1, SWA | PRG-web, IF-REST, TBL-RDB | `src/api/*` (헤더에 PRG-*, RQ-*) | W-D-17 |
| W-I-W-02 | 프런트 구현 | web-developer (P1) | designer, web-publisher | PRG-web, SCN-*, IF-REST | `src/web/*` + `UT-RES-WEB-FE-*` | W-D-17 |
| W-I-W-03 | 마크업·스타일 | web-publisher (P1) | designer | SCN-* | `src/web/styles/*`, `src/web/components/*` | W-I-W-02 (동시) |
| W-I-W-04 | P1 단위 테스트 실행 | backend-developer/web-developer | tester(해석 자문) | UT-* | `03_implementation/unit-test-results/UT-RES-WEB-*` | W-I-W-01~03 |

### Batch Part (P2)
| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-I-B-01 | 배치잡 구현 | batch-developer (P2) | part-leader P2, DBA, infra-engineer | PRG-batch, BATCH-*, TBL-RDB/COLL-NOSQL | `src/batch/<domain>/*` (**헤더에 PRG-*, BATCH-*, RQ-* 3종 필수**) | W-D-17 |
| W-I-B-02 | P2 단위 테스트 실행 | batch-developer | tester | UT-* | `03_implementation/unit-test-results/UT-RES-BAT-*` (depends-on: BATCH-*) | W-I-B-01 |

### Stream Part (P3) — Kafka consumer/producer, daemon
| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-I-S-01 | Kafka producer 구현 | backend-developer (P3) | part-leader P3, technical-architect | PRG-daemon, IF-KAFKA (produce) | `src/stream/producer/*` | W-D-17 |
| W-I-S-02 | Kafka consumer 구현 (오프셋·DLQ·백프레셔) | backend-developer (P3) | technical-architect, DBA | PRG-daemon, IF-KAFKA (consume), COLL-NOSQL | `src/stream/consumer/*` | W-D-17 |
| W-I-S-03 | 데몬 헬스체크·메트릭 | backend-developer (P3) | infrastructure-engineer | PRG-daemon | `src/stream/health/*` | W-I-S-01, W-I-S-02 |
| W-I-S-04 | P3 단위 테스트 실행 | backend-developer | tester | UT-* | `03_implementation/unit-test-results/UT-RES-STR-*` | W-I-S-01~03 |

### Data Part (P4)
| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-I-D-01 | RDB 마이그레이션 스크립트 | backend-developer (P4) | DBA | TBL-RDB-* | `src/migrations/*` (+ 롤백 스크립트) | W-D-17 |
| W-I-D-02 | NoSQL 초기 스키마·인덱스 | backend-developer (P4) | DBA | COLL-NOSQL-* | `src/nosql-init/*` | W-D-17 |
| W-I-D-03 | 데이터 정합성 검증 스크립트 | backend-developer (P4) | data-modeler, DBA | ENT-*, TBL-*, COLL-* | `src/data-checks/*` | W-I-D-01, W-I-D-02 |
| W-I-D-04 | P4 단위 테스트 실행 | backend-developer | tester | UT-* | `03_implementation/unit-test-results/UT-RES-DAT-*` | W-I-D-01~03 |

### 공통 인프라
| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-I-C-01 | 컨테이너·IaC | infrastructure-engineer | technical-architect | INF-* | `infra/{Dockerfile,compose,IaC}` | W-D-17 |
| W-I-C-02 | Kafka 브로커 운영 구성 | infrastructure-engineer | technical-architect | INF-KAFKA, IF-KAFKA | `infra/kafka/*` (IF-KAFKA-* depends-on) | W-I-C-01 |
| W-I-C-03 | 스케줄러 (cron/timer/cloud scheduler) | infrastructure-engineer | — | BATCH-*, INF-* | `infra/schedulers/*` (**BATCH-* depends-on 필수**) | W-I-C-01 |
| W-I-C-04 | 모니터링·알림 | infrastructure-engineer | security-specialist | ARCH-*, INF-* | `infra/monitoring/*`, `infra/alerts/*` | W-I-C-01 |
| W-I-C-05 | CI/CD 파이프라인 | infrastructure-engineer | part-leader 전원 | 전 src | `.github/workflows/*` | W-I-C-01 |
| W-I-C-06 | 파트별 코드 리뷰 (≥2) | part-leader + SWA | — | 각 파트 src | `03_implementation/reviews/<part>-review-v1.md` | W-I-{W,B,S,D}-04 |
| W-I-C-07 | MOCK→real transition checklist | PM | infra-engineer | 전 src | `03_implementation/mock-to-real-transition.md` | W-I-C-01~05 |
| W-I-C-08 | RTM 구현 컬럼 채움 | PM | 각 저자 | 전 UT-RES, 전 src | `RTM/by-stage/implementation.md` | W-I-C-06 |
| W-I-Z-01 | 구현 승인 | user | PM | 전체 리뷰 + RTM | Approval Log | W-I-C-07, W-I-C-08 |

---

## 04_test

| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-T-01 | 테스트 환경 구축 | infrastructure-engineer | technical-architect | infra/*, mock-to-real checklist | 테스트 환경 가동 | W-I-Z-01 |
| W-T-02 | 통합 테스트 실행 (모든 BATCH-ID 커버) | tester | QA, part-leader 전원 | IT-*, 전 UT-RES | `04_test/integration-test-results/IT-RES-*` | W-T-01 |
| W-T-03 | 시스템 테스트 (성능·장애복구·Kafka lag) | tester | technical-architect, DBA | ARCH-*, IT-* | `04_test/system-test-results/ST-RES-*` | W-T-02 |
| W-T-04 | UAT 실행 | tester | QA, 사용자 | UAT-* | `04_test/uat-results/UAT-RES-*` | W-T-03 |
| W-T-05 | QA 리포트 | quality-assurance | tester | 모든 RES | `04_test/qa-report/*` | W-T-04 |
| W-T-06 | CR 처리 (FAIL 발생 시) | PM | director, 저자 | 실패 결과 + 영향분석 | `change-requests/CR-*/{request,impact-analysis,decision}.md` | W-T-02~04 (필요 시) |
| W-T-07 | 결과 리뷰 (≥2) | QA + tester + director | — | RES + qa-report | `04_test/reviews/test-review-v1.md` | W-T-05 |
| W-T-08 | RTM 시험 컬럼 채움 | PM | tester | 전 RES | `RTM/by-stage/test.md` | W-T-07 |
| W-T-09 | 시험 승인 (CONDITIONAL PASS 포함) | user | PM | 리뷰 + carry-forward 명세 | Approval Log | W-T-08 |

---

## 05_deployment

| 작업 ID | 작업 | 담당자(주) | 담당자(자문) | Input | Output | 선행 |
|--------|------|-----------|-------------|-------|--------|------|
| W-R-01 | 배포 계획 (단계·롤백·배치 스케줄러 활성화) | PM | infrastructure-engineer, DBA | ARCH-*, INF-*, BATCH-* | `05_deployment/deployment-plan/DEPLOY-*` (BATCH-* depends-on) | W-T-09 |
| W-R-02 | 운영 매뉴얼 (파트별 + 모든 BATCH-ID) | 각 파트리더 | infrastructure-engineer | PRG-*, BATCH-*, IF-KAFKA, SEC-* | `05_deployment/operation-manual/OPS-*` (**BATCH-ID 1:1 커버 필수**) | W-R-01 |
| W-R-03 | 교육 자료 | application-director | 각 파트리더 | OPS-*, 사용자 가이드 초안 | `05_deployment/training-material/TRAIN-*` (배치 운영 섹션 포함) | W-R-02 |
| W-R-04 | 보안 최종 검토 (secrets·감사로그·알림) | security-specialist | technical-architect | DEPLOY-*, SEC-* | `agent-call-log.md` 보안 자문 + SEC-* v2 | W-R-01 |
| W-R-05 | 이행 리뷰 (≥2) | director + QA | 각 파트리더 | 위 모두 | `05_deployment/reviews/deployment-review-v1.md` | W-R-02~04 |
| W-R-06 | 종료 감리 | audit-team | — | 전 프로젝트 + 전 RTM | `99_audit/03_closing-audit/audit-report/*` | W-R-05 |
| W-R-07 | 감리 시정조치 | PM (분배) | 해당 저자 | FIND-* | corrective-action-* + re-audit PASS | W-R-06 |
| W-R-08 | 배포 실행 (환경별 순차) | infrastructure-engineer | DBA, security-specialist | DEPLOY-* | 배포 실행 로그 + `rollback-history.md` | W-R-07 |
| W-R-09 | 배포 후 검증 (smoke, batch 첫 실행, stream lag) | tester + infrastructure-engineer | part-leader 전원 | 운영 모니터링 | 검증 결과 기록 | W-R-08 |
| W-R-10 | RTM deployment 컬럼 채움 | PM | — | 배포 단위 매핑 | `RTM/by-stage/deployment.md` | W-R-09 |
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
- [ ] 파트리더 P1~P4 가 각 파트의 구현·리뷰·운영매뉴얼·CR 대응을 모두 커버?
- [ ] 인프라(스케줄러·Kafka·모니터링) 는 `infrastructure-engineer` 단독 저자, `technical-architect`·`security-specialist`·DBA 는 자문?
- [ ] 테스트 케이스 저작과 실행은 모두 `tester` 단일화(QA 는 리뷰·기준만)?
- [ ] 감리(audit-team) 는 별도 worktree 에서만 작동하고 프로젝트 산출물 직접 수정 없음?

### 3. 산출물 매핑(I/O)
- [ ] 모든 PRG-* frontmatter `type` 이 web/batch/daemon 중 하나?
- [ ] web PRG → SCN 양방향 연결, batch PRG → BATCH 양방향 연결이 설계 단계에 담겨있음?
- [ ] BATCH-* 가 UT → UT-RES → IT-RES → OPS 까지 downstream 으로 모두 참조됨?
- [ ] Kafka IF (IF-KAFKA-*) 가 Stream 구현·consumer·producer 코드 헤더·IT 시나리오에 모두 매핑?
- [ ] RTM: RQ → PRG → 유형별(SCN/BATCH/IF) → UT → UT-RES → IT-RES → UAT-RES → OPS 체인이 각 단계 by-stage 에 채워짐?

### 4. 순서(Precedence)
- [ ] 논리 DB(ENT-*)는 분석 단계에서 시작(W-A-04), 물리 DB(TBL-RDB/COLL-NOSQL)는 설계 단계에서만 시작?
- [ ] 배치잡 설계(BATCH-*)는 PRG 목록(W-D-05) 이후에만 시작?
- [ ] 구현 착수(W-I-\*-01)는 설계 승인(W-D-17) 이후에만 허용? (파트별 동시 착수 가능)
- [ ] 테스트 환경(W-T-01)은 MOCK→real checklist(W-I-C-07) 이후?
- [ ] 배포(W-R-08)는 종료 감리 PASS(W-R-07) 이후?

### 5. 대규모(large) 필수 요소
- [ ] 파트리더 4 명 모두 실제 작업(W-I-\*, W-R-02) 에 등장?
- [ ] `99_audit/01_analysis-audit` (분석 감리, 대규모 전용) 포함?
- [ ] `RTM/by-part/` 가 파트별 RTM 관리에 사용되도록 계획에 명시? (현 WBS 표엔 compact 표기, 실제 프로젝트에서 추가)

---

## 실 프로젝트 이관 시 주의

1. 이 표의 `W-<단계>-<seq>` ID 는 그대로 `projects/<name>/00_kickoff/project-plan/wbs/W-*.md` 의 child ID 로 사용 가능.
2. 각 작업 행을 하나의 `W-*.md` 파일로 분해하면 drift-guard(`validate_artifact_hierarchy.py`) 가 `depends-on`(선행) / `referenced-by`(후행) 양방향 자동 검증한다.
3. `RTM/index.md` 의 단계별 진행 요약 표는 이 WBS 의 단계별 작업 수·완료 수와 1:1 으로 일치해야 한다.
