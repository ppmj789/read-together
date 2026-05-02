# Stage Gates — Completion Criteria (v2)

This document defines the closure conditions that PM must verify before
transitioning a project from one stage to the next. Each list is exhaustive:
if any item is missing, the stage is not complete.

All paths are relative to `projects/<project-name>/`. The **v2 hierarchical
structure** is assumed: each `<stage>/<area>/` is either a directory with
`index.md` + `<ID>.md` children (when ≥3 children) or a single file (when
1–2 children) per spec §3-1 §2-13-7. The `scripts/validate_artifact_hierarchy.py`
drift-guard validates index presence and bidirectional `depends-on` /
`referenced-by` frontmatter.

Every stage gate now includes a **Hierarchy gate** that requires
`validate_artifact_hierarchy.py <project>` to exit 0 and — for any stage that
introduced or modified child-file back-references —
`sync_back_references.py <project>` to report clean.

---

## 00_kickoff

Required artifacts (directory or file per §3-1):
- `00_kickoff/statement-of-work.md` (provided by the user; PM must confirm presence and completeness)
- `00_kickoff/project-plan/` directory — authored in three ordered waves:
  - **Wave 1 (plan skeleton)**: `index.md`, `overview.md`, `scope.md`, `organization.md`, `schedule.md`
  - **Wave 2 (budget)**: `budget.md` authored after `business-manager` Track B advisory
  - **Wave 3 (WBS)**: `wbs/index.md` + `wbs/W-<letter>-<seq>.md` children, authored after Waves 1–2 as input. WBS rows must cover every stage (00–05) with columns: 단계 · 작업 ID · 해야할 작업 · 담당자(주) · 담당자(자문) · Input · Output · 선행. See `docs/wbs-large-streaming-example.md` for the reference form applied to a large-scale project.
- `00_kickoff/rollback-history.md` (empty file with heading and table skeleton)

Review requirement:
- `00_kickoff/reviews/project-plan-review-v<N>.md` with ≥2 participants, using `templates/artifacts/review-meeting.md.tmpl`. Review must take place **after WBS validation gate passes** so the reviewed plan already contains user-ok'd WBS.

Advisory gates (mandatory per §2-6):
- `business-manager` Track B advisory for `budget.md` logged in `agent-call-log.md`
- `quality-assurance` Track B review of the finalized plan logged in `agent-call-log.md`

Project-state requirement:
- `project-state.md` present with `scale:` filled, `current-stage: 00_kickoff`, and `Stage Progress` initialized

Hierarchy gate:
- `python3 scripts/validate_artifact_hierarchy.py <project>` exits 0

WBS validation gate (MANDATORY, precedes project-plan review and Approval):
- `00_kickoff/project-plan/wbs/` 전 child (W-*.md) 가 8 컬럼 필드를 모두 채우고 있어야 한다.
- User가 WBS 전체를 직접 검토하고 다음 6 섹션 체크리스트에 PASS 해야 한다 (참조: `docs/wbs-large-streaming-example.md` "사용자 점검 체크리스트"):
  1. 파이프라인 완전성 (단계·승인·감리 누락 없음)
  2. 담당자 배치 적정성 (저작자 vs 자문 분리, 개발자 저작·아키텍트/디자이너/DBA/data-modeler 자문 원칙)
  3. 산출물 매핑 (I/O 연속성, PRG type·SCN·BATCH·IF·UT 체인)
  4. 순서(Precedence) 무결성 (`선행` 컬럼의 DAG 정합성)
  5. 도메인 파트 분할 적정성 (large 모드 해당; 기술 유형 편중·DB 쏠림 없음)
  6. 규모별 필수 요소 (large 모드면 분석 감리 포함, 파트리더 실제 등장 등)
- 검증 결과는 `project-state.md` **WBS Validation Log** 표에 기록: `Date · Reviewed By (user) · Result (ok | 수정요청) · Notes (수정요청 사유)`.
- 결과가 `수정요청` 이면 PM 이 WBS 를 재저작한 뒤 동일 표에 다음 줄(`ok`) 을 추가해야 한다. 마지막 행이 `ok` 가 아니면 Approval gate 진입 불가.
- WBS Validation 통과 없이 project-plan review 또는 01_analysis 진입을 시도하는 것은 stage-gate 위반.

Project-fit Hook Generation gate (MANDATORY, WBS Validation 직후, project-plan review·Approval 직전):
- PM 이 SOW·WBS·project-plan/scope 분석으로 본 프로젝트에 fit 한 검증 hook 후보 5–8 건을 추천 (예: 7 카테고리 RQ enumerate 완전성, 외부 의존 RQ → IT variant 4종 매핑, 도메인 파트 owner 화이트리스트, RQ↔PRG↔UT 매핑 완전성, FMEA 표 카테고리 정합, large mode by-part 강제 등 — 후보 종류는 사용자 협의 시점에 동적 결정).
- PM 이 사용자에게 후보 제시 → 사용자 선택·추가·제외 → 합의 명세를 prompt 로 묶어 `policy-engineer-opus` Track A dispatch.
- `policy-engineer` 가 `projects/<name>/scripts/` 에 `run_project_hooks.sh` 디스패처 + `hook_<stage>_<purpose>.py` 개별 hook + `hooks-manifest.md` 저작.
- PM 이 dry-run 으로 모든 stage 에 대해 `bash projects/<name>/scripts/run_project_hooks.sh <stage>` 실행하고 exit 0 (hook 부재 stage 는 INFO + exit 0) 확인.
- 결과를 `project-state.md` **Hook Generation Log** 표에 기록: `Date · Hooks Authored (count) · Manifest Path · Dry-run Result · Notes`.
- 사용자가 "hook 협의 skip" 을 명시 선택한 경우는 매니페스트에 그 사실을 기재하고 통과 (placeholder 디스패처는 모든 stage 에서 INFO + exit 0 으로 동작).
- 본 게이트 PASS 없이 Approval Log 진입 시도는 stage-gate 위반.

Approval gate:
- `Approval Log` entry for `00_kickoff` by `user` (선행: WBS Validation Log 마지막 행 = `ok` AND Hook Generation Log 1건 이상)

---

## 01_analysis

Required artifacts (directory + children, each child id-registered in RTM):
- `01_analysis/requirements/` — `index.md` + `RQ-<area>-<seq>.md` children (all RQ-xxx IDs registered in RTM)
- `01_analysis/as-is-analysis/` — `index.md` + AS-<area>-<seq> children
- `01_analysis/to-be-workflow/` — `index.md` + TB-<area>-<seq> children
- `01_analysis/uat-test-cases/` — `index.md` + UAT-<seq> children (all UAT-xxx registered)
- `01_analysis/integration-test-cases/` — `index.md` + IT-<seq> children (all IT-xxx registered)
- For each area above: a matching `01_analysis/reviews/<area>-review-v<N>.md` with ≥2 participants, using `templates/artifacts/review-meeting.md.tmpl`

Advisory gates (mandatory per §2-6):
- `business-manager` stage-entry advisory logged in `agent-call-log.md`
- `quality-assurance` review of analysis artifacts logged in `agent-call-log.md`

RTM requirement:
- `RTM/by-stage/01_analysis.md` populated with REQ-ID, 요구사항명, 유형, 출처, IT-ID, UAT-ID for every child
- `RTM/index.md` summary reflects RQ-ID master list

Audit gate (if `project-state.scale == large`):
- `99_audit/01_analysis-audit/audit-report/index.md` + `FIND-*.md` final result = PASS
  (after any corrective-action-plan + corrective-action-result + re-audit cycles)

Hierarchy gate:
- `python3 scripts/sync_back_references.py <project>` reports clean (apply mode if drift)
- `python3 scripts/validate_artifact_hierarchy.py <project>` exits 0

Project-fit hook gate (PM stage-gate self-check):
- `bash projects/<project>/scripts/run_project_hooks.sh 01_analysis` exits 0
- 디스패처 부재 시 stage 종결 보고 자체 금지 (00_kickoff Hook Generation gate 미완)

Approval gate:
- `Approval Log` entry for `01_analysis` by `user`

---

## 02_design

Required artifacts (directory + children):
- `02_design/architecture/` — 4 subdomain 분할 (각각 `index.md` + 자식 산출물). 4 영역 모두 PASS 필수:
  - `02_design/architecture/application/` (AA·SWA 공동 저작)
    - AA 저작: `overview.md` · `domain-model.md` · `business-flow.md` · `components/CMP-<seq>-<slug>.md` · `decisions/ADR-<seq>-<slug>.md` (AA 결정)
    - SWA 저작: `code-architecture.md` · `module-patterns.md` · `interface-policy.md` · `decisions/ADR-<seq>-<slug>.md` (SWA 결정)
  - `02_design/architecture/technology/` (TA 저작)
    - `overview.md` · `middleware.md` · `deployment-topology.md` · `nfr-technology.md` · `decisions/ADR-<seq>-<slug>.md`
  - `02_design/architecture/data/` (data-modeler 저작) — 응용 차원 데이터 아키 (논리 모델은 `02_design/db/logical/` 와 별도, 큰 그림 측면)
  - `02_design/architecture/security/` (security-specialist 저작) — 응용·기술 차원 보안 아키 (보안 리뷰 산출물 `02_design/security-review/` 와 별도)
- `02_design/db/` — `index.md` + `db-logical/` + `db-physical/` subdirs (logical delivered by data-modeler, physical co-designed with DBA)
- `02_design/design-system/` — `index.md` + designer 저작 5종 (overview·colors·typography·layout·logo-brand). `type: web` PRG 가 1개 이상 있는 프로젝트는 필수. SCN 과 마크업이 인용할 단일 디자인 출처.
- `02_design/screens/` — `index.md` + SCN-<seq> children (required when any PRG has `type: web`). web-developer 단독 저작; SCN 본문은 design-system 토큰을 인용한다.
- `02_design/batch-jobs/` — `index.md` + BATCH-<seq> children (required when any PRG has `type: batch`; covers 스케줄·트리거·재처리 정책·리소스 한도)
- `02_design/interfaces/` — `index.md` + IF-<seq> children
- `02_design/programs/` — `index.md` + PRG-<seq> children (every program in the list, each with frontmatter `type: web | batch | daemon`)
- `02_design/unit-test-cases/` — `index.md` + UT-<seq> children (all UT-xxx IDs registered in RTM)
- `02_design/security-review/` — `index.md` + SEC-<seq> children
- `02_design/infra/` — `index.md` + INF-<seq> children (when infrastructure design is in scope)
- For each area above: a matching review in `02_design/reviews/` with ≥2 participants using `templates/artifacts/review-meeting.md.tmpl`. Directors may Track-B self-review their own authored areas to surface blind spots (Phase 7 Task 9 positive pattern).
- **Architecture review participation (mandatory)**: `02_design/architecture/` 의 4 영역 통합 리뷰는 다음 참가자가 모두 포함되어야 PASS — application-architect (응용), software-architect (SW), technical-architect (기술), data-modeler (데이터), security-specialist (보안). 응용·기술 ADR 의 상호 인용 정합성 (AA `application/components/CMP-*` ↔ TA `technology/deployment-topology.md`, SWA `application/interface-policy.md` ↔ AA `application/business-flow.md`) 을 리뷰 본문에서 점검.

Advisory gates (mandatory):
- `business-manager` stage-entry advisory
- `quality-assurance` review of design artifacts

RTM requirement:
- `RTM/by-stage/02_design.md` populated for every PRG-ID with columns: REQ-ID, PRG-ID, 프로그램유형(web|batch|daemon), SCN-ID(web 필수), BATCH-ID(batch 필수), IF-ID, UT-UNIT-ID, 담당, 상태. `프로그램유형` 은 해당 `PRG-*.md` frontmatter `type` 과 일치해야 함.
- `RTM/by-artifact/` 역색인: `SCN-*.md`, `PRG-*.md`, `BATCH-*.md`, `IF-*.md` 각각의 ID → 그 산출물이 만족하는 REQ-ID 목록을 기록 (신규 이슈 N15 설계→RQ 역매핑; 배치잡설계서도 동일 원칙 적용).

Audit gate (MANDATORY regardless of scale):
- `99_audit/02_design-audit/audit-report/index.md` + `FIND-*.md` final result = PASS
- Invoked via `scripts/run_audit.sh <project> 02_design <prompt-file>` (helper guarantees CLI arg order and output path)

Exception-handling ratio policy (`docs/exception-handling-ratio-policy.md`):
- **PRG/IF/SCN/BATCH 본문 FMEA 표 의무** (정책 §3·§4) — 각 산출물에 7 Failure Categories enumerate + 표 양식. SWA Track B 자문 finding 시 corrective.
- **UT-*.md frontmatter 비율 강제** (정책 §5) — `variant-happy-count / variant-count ≤ 0.3`, `variant-exception-count / variant-count ≥ 0.7`, 합계 일관성. `validate_artifact_hierarchy.py` 가 자동 검증 (Hierarchy gate 에 포함).
- 변경 후 단계적 도입 — 기존 UT 가 frontmatter 비율 필드를 갖지 않으면 advisory skip 되며, 새로 저작·갱신되는 UT 는 strict 검증.

Program-type artifact rules (per PRG-ID):

| PRG `type` | 필수 산출물 | depends-on 연결 |
|-----------|------------|-----------------|
| `web` | `PRG-*.md` 프로그램설계서 + `SCN-*.md` 화면설계서 | PRG ↔ SCN (양방향) |
| `batch` | `PRG-*.md` 프로그램설계서 + `BATCH-*.md` 배치잡설계서 | PRG ↔ BATCH (양방향) |
| `daemon` | `PRG-*.md` 프로그램설계서 단독 | 연결 없음 (관리콘솔 노출 시 SCN 연결 허용) |

Hybrid 프로그램(예: 배치 트리거 + 관리화면)은 PRG 하나에 주력 `type` 을 기록하고, 필요한 보조 설계서(SCN, BATCH) 를 모두 `depends-on` 으로 연결한다. 검증은 `validate_artifact_hierarchy.py` 의 양방향 drift-guard 가 자동 수행.

Hierarchy gate:
- `sync_back_references.py <project>` clean
- `validate_artifact_hierarchy.py <project>` exits 0

Project-fit hook gate (PM stage-gate self-check):
- `bash projects/<project>/scripts/run_project_hooks.sh 02_design` exits 0

Approval gate:
- `Approval Log` entry for `02_design` by `user`

---

## 03_implementation

Required artifacts:
- Source code in `src/<layer>/` matching every PRG-ID in RTM. **Batch-type PRG** 는 `src/batch/<domain>/<job>.<ext>` 의 헤더 주석에 `PRG-<id>`, `BATCH-<id>`, 관련 `RQ-<id>` 를 모두 명시 (grep 가능한 고정 포맷).
- `03_implementation/unit-test-results/` — `index.md` + `UT-RES-<group>.md` children. Each result PASS for every UT-ID, or explicit exemption cited. `UT-RES-*.md` frontmatter `depends-on` 은 해당 UT-ID 뿐 아니라 **커버하는 PRG-ID 및 (batch 유형이면) BATCH-ID** 를 모두 포함.
- Code review records in `03_implementation/reviews/` for each implemented module (≥2 participants; author + part-leader or SWA)
- `infra/` artifacts (Dockerfile, docker-compose.yml, migrations/, scripts/, README.md, .env.example, .github/workflows/) if infrastructure scope is in this stage. **Batch 스케줄러·모니터링 구성 파일** (cron·systemd timer·cloud scheduler 정의, 알림 룰) 은 해당 `BATCH-*.md` 를 frontmatter `depends-on` 또는 주석 헤더로 참조해야 하며, 배치잡 없이 방치된 인프라 파일 / 인프라 없이 방치된 BATCH-ID 는 모두 stage-gate fail.

Advisory gates:
- `business-manager` stage-entry advisory
- `security-specialist`, `database-administrator` Track B consultations logged when auth / DB / payment code was written

RTM requirement:
- `RTM/by-stage/03_implementation.md` 소스경로 column populated for every PRG-ID

Exception-handling ratio policy (정책 §6):
- **One RPC = one handler**: PRG/RPC 1개당 핸들러 함수 1개. variant 별 함수 분리 시 코드 리뷰 finding (SWA 자문).
- **Precondition guard chain**: 핸들러 진입 직후 단일 검증 체인. 흩어진 if 분기 금지.
- **예외 경로 누락 없음**: UT-*.md 의 모든 exception variant 가 코드의 guard chain 에 검증 분기로 존재. 누락은 finding.
- **코드 헤더 주석에 카테고리·variant 키워드 명시**: 어느 7 카테고리·variant 를 다루는지 핸들러 헤더 주석에 enumerate.

MOCK→real environment gate (Phase 7 patch #11):
- If 03_implementation was authored in MOCK mode (no real DB / external API), PM must author a transition checklist in
  `03_implementation/mock-to-real-transition.md` before 04_test. Minimum items: DB connectivity verified, secrets wiring
  verified, outbound network reachability verified, feature flags default state confirmed. The 04_test environment must
  pass all checklist items before integration-test execution.

Hierarchy gate:
- `sync_back_references.py <project>` clean
- `validate_artifact_hierarchy.py <project>` exits 0

Project-fit hook gate (PM stage-gate self-check):
- `bash projects/<project>/scripts/run_project_hooks.sh 03_implementation` exits 0

Approval gate:
- `Approval Log` entry for `03_implementation` by `user`

---

## 04_test

Required artifacts:
- `04_test/integration-test-results/` — `index.md` + `IT-RES-<seq>.md` children (PASS/FAIL per IT-ID). **모든 BATCH-ID 는 최소 1개 이상의 IT-ID 로 커버** (스케줄 트리거·실패 재처리·run-window 초과 시나리오 포함); 미커버 BATCH 는 `qa-report/` 에 미시험 리스크로 명시 후 carry-forward 가능.
- `04_test/system-test-results/` — `index.md` + `ST-RES-<seq>.md` children
- `04_test/uat-results/` — `index.md` + `UAT-RES-<seq>.md` children (PASS/FAIL per UAT-ID)
- `04_test/qa-report/` — `index.md` + topic children
- Result-review record in `04_test/reviews/` with ≥2 participants

Advisory gates:
- `business-manager` stage-entry advisory
- `quality-assurance` + `tester` Track B pass/fail recommendation

Change-request cycle (when failures arise):
- Each FAIL that requires an upstream-artifact change spawns a `change-requests/CR-<seq>/` directory with
  `cr-request.md`, `cr-impact-analysis.md`, and `cr-decision.md` using the templates under
  `templates/artifacts/change-requests/`. CR status transitions in `project-state.md` Audit Log / Approval Log.

RTM requirement:
- `RTM/by-stage/04_test.md` 결과 column populated for every IT-ID, UAT-ID (and implicitly every linked REQ-ID)

Hierarchy gate:
- `sync_back_references.py <project>` clean
- `validate_artifact_hierarchy.py <project>` exits 0

Project-fit hook gate (PM stage-gate self-check):
- `bash projects/<project>/scripts/run_project_hooks.sh 04_test` exits 0

Approval gate:
- `Approval Log` entry for `04_test` by `user` (CONDITIONAL PASS with carry-forward findings is acceptable when PM
  records each carry-forward's owner and deadline; unresolved items must appear in `04_test/qa-report/` and be
  routed to `05_deployment` or `03_closing-audit`)

---

## 05_deployment

Required artifacts:
- `05_deployment/deployment-plan/` — `index.md` + `DEPLOY-<seq>.md` children. **Batch 스케줄러 배포 단계** (cron·timer 활성화, 모니터링·알림 연결, 첫 실행 검증) 를 포함하고 관련 BATCH-ID 를 `depends-on` 으로 참조.
- `05_deployment/operation-manual/` — `index.md` + `OPS-<seq>.md` children. **모든 BATCH-ID 에 대해 OPS-* 하나 이상**이 존재해야 하며(정상 실행 확인, 장애 탐지 경로, 수동 재실행 절차, run-window 초과 대응), `depends-on: [BATCH-...]` 를 기재.
- `05_deployment/training-material/` — `index.md` + `TRAIN-<seq>.md` children. 운영자 교육 자료는 배치잡 일상 운영 섹션 포함.
- Review record in `05_deployment/reviews/` with ≥2 participants (director self-review via Track B encouraged)

Advisory gates:
- `business-manager` stage-entry advisory
- `security-specialist` Track B review for secrets / audit log decisions

Audit gate (MANDATORY regardless of scale):
- `99_audit/03_closing-audit/audit-report/index.md` + `FIND-*.md` final result = PASS
- Invoked via `scripts/run_audit.sh <project> 03_closing <prompt-file>`

Hierarchy gate:
- `sync_back_references.py <project>` clean
- `validate_artifact_hierarchy.py <project>` exits 0

Project-fit hook gate (PM stage-gate self-check):
- `bash projects/<project>/scripts/run_project_hooks.sh 05_deployment` exits 0

Approval gate:
- `Approval Log` entry for `05_deployment` by `user` (final project approval → `current-stage: closed`)

---

## Audit Stage (each occurrence)

For A-AUDIT-N / D-AUDIT-N / C-AUDIT-N cycles, the final result is determined by:

1. Latest `audit-report/index.md` + `FIND-*.md` final result = PASS, OR
2. After every finding flagged in the most recent report, a matching pair of:
   - `99_audit/<stage>-audit/corrective-action-plan/` — `index.md` + `PLAN-FIND-*.md` children
   - `99_audit/<stage>-audit/corrective-action-result/` — `index.md` + `RES-FIND-*.md` children
   exists, and a later `99_audit/<stage>-audit/re-audit-report-v<N>/` marks all prior findings as resolved.

The PM must ensure every finding in every report is traceable to either resolution (1) or (2) before declaring audit pass.

Audit-team artifacts live inside the audit worktree at
`<wt>/projects/<project>/99_audit/<cycle>-audit/...` — the path is load-bearing (Phase 7 Task 10 finding #18); `scripts/run_audit.sh` enforces it through a three-layer defense (header, audit-team Mission, post-run fallback copy).

Drift-guard scope for `99_audit/`: bidirectional `depends-on` / `referenced-by` checks are **advisory** for audit-team-authored child files, because audit-team is forbidden from editing artifacts outside `99_audit/` (including the back-references it would otherwise need to inject into corrective-action files). PM-authored corrective-action files use normal bidirectional references via `sync_back_references.py`. (Phase 7 patch #19)

---

## Completion verification procedure (PM)

When about to transition stage N → N+1:

1. Read this file.
2. For each `Required artifacts` entry, verify the directory / file exists, `index.md` is present if the directory has ≥3 children, and every child has valid frontmatter (`id`, `depends-on`, `referenced-by`, `author`).
3. For each `Review requirement`, open the review file and count `participants` in its frontmatter. Must be ≥2.
4. For each `Advisory gate`, confirm a row exists in `agent-call-log.md` for the required Track B consultation.
5. If `RTM requirement` is listed, read `RTM/by-stage/<stage>.md` and verify the named columns are populated for every relevant ID. Also confirm `RTM/index.md` reflects summary counts.
6. Run `python3 scripts/sync_back_references.py <project>` (apply mode) and `python3 scripts/validate_artifact_hierarchy.py <project>` — both must exit 0.
7. If `Audit gate` applies, verify the final audit cycle passed per the audit closure procedure above.
8. If `Approval gate` passes (user has signed off in `project-state.md` Approval Log), proceed. Otherwise, request approval.

Failure in any step → fix it or redirect work; never paper over gaps (§8).
