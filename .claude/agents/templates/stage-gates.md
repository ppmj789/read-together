# Stage Gates — Completion Criteria

This document defines the closure conditions that PM must verify before
transitioning a project from one stage to the next. Each list is exhaustive:
if any item is missing, the stage is not complete.

All paths are relative to `projects/<project-name>/`.

---

## 00_kickoff

Required artifacts:
- `00_kickoff/statement-of-work.md` (provided by the user; PM must confirm presence and completeness)
- `00_kickoff/project-plan.md` (PM, with business-manager input)
- `00_kickoff/rollback-history.md` (empty file with heading and table skeleton)

Review requirement:
- `00_kickoff/reviews/project-plan-review-v1.md` with ≥2 participants

Project-state requirement:
- `project-state.md` present with `scale:` filled and `Stage Progress` initialized

Approval gate:
- `Approval Log` entry for `00_kickoff` by `user`

---

## 01_analysis

Required artifacts:
- `01_analysis/requirements.md` (all RQ-xxx IDs registered in RTM)
- `01_analysis/as-is-analysis.md`
- `01_analysis/to-be-workflow.md`
- `01_analysis/uat-test-cases.md` (all UAT-xxx IDs registered in RTM)
- `01_analysis/integration-test-cases.md` (all IT-xxx IDs registered in RTM)
- For each above artifact: a matching `01_analysis/reviews/<name>-review-v<N>.md` with ≥2 participants

RTM requirement:
- Columns populated for this stage: REQ-ID, 요구사항명, 유형, 출처, IT-ID, UAT-ID

Audit gate (if project-state.scale == large):
- `99_audit/01_analysis-audit/audit-report.md` final result = PASS
  (after any corrective-action-plan + corrective-action-result + re-audit cycles)

Approval gate:
- `Approval Log` entry for `01_analysis` by `user`

---

## 02_design

Required artifacts:
- `02_design/architecture.md`
- `02_design/db-logical.md`
- `02_design/db-physical.md`
- `02_design/screen-spec.md`
- `02_design/interface-spec.md`
- `02_design/program-list.md`
- `02_design/unit-test-cases.md` (all UT-xxx IDs registered in RTM)
- `02_design/security-review.md`
- For each above artifact: a matching review in `02_design/reviews/` with ≥2 participants

RTM requirement:
- Columns populated: DESIGN-ID, 설계문서, PROG-ID, UT-ID

Audit gate (MANDATORY regardless of scale):
- `99_audit/02_design-audit/audit-report.md` final result = PASS

Approval gate:
- `Approval Log` entry for `02_design` by `user`

---

## 03_implementation

Required artifacts:
- Source code in `src/<layer>/` matching every PRG-ID in RTM
- `03_implementation/unit-test-results.md` — PASS for every UT-ID or explicit exemption
- Code review record in `03_implementation/reviews/` for each implemented module (≥2 participants; author + part-leader or SWA)

RTM requirement:
- `소스경로` column populated for every PRG-ID

Approval gate:
- `Approval Log` entry for `03_implementation` by `user`

---

## 04_test

Required artifacts:
- `04_test/integration-test-results.md` (PASS/FAIL per IT-ID)
- `04_test/system-test-results.md`
- `04_test/uat-results.md` (PASS/FAIL per UAT-ID)
- `04_test/qa-report.md`
- Result-review record in `04_test/reviews/` with ≥2 participants

RTM requirement:
- `결과` column populated for every IT-ID, UAT-ID (and implicitly every linked REQ-ID)

Approval gate:
- `Approval Log` entry for `04_test` by `user`

---

## 05_deployment

Required artifacts:
- `05_deployment/deployment-plan.md`
- `05_deployment/operation-manual.md`
- `05_deployment/training-material.md`
- Review record in `05_deployment/reviews/` with ≥2 participants

Audit gate (MANDATORY regardless of scale):
- `99_audit/03_closing-audit/audit-report.md` final result = PASS

Approval gate:
- `Approval Log` entry for `05_deployment` by `user` (final project approval)

---

## Audit Stage (each occurrence)

For A-AUDIT-N / D-AUDIT-N / C-AUDIT-N cycles, the final result is determined by:

1. Latest `audit-report.md` (or `re-audit-report-v<M>.md`) result field = PASS, OR
2. After every finding flagged in the most recent report, a matching pair of:
   - `corrective-action-plan.md`
   - `corrective-action-result.md`
   exists, and a later `re-audit-report-v<M>.md` marks all prior findings as resolved.

The PM must ensure every finding in every report is traceable to either resolution (1) or (2) before declaring audit pass.

---

## Completion verification procedure (PM)

When about to transition stage N → N+1:

1. Read this file.
2. For each `Required artifacts` item, verify the file exists and is valid Markdown.
3. For each `Review requirement`, open the review file and count `participants` in its frontmatter. Must be ≥2.
4. If `RTM requirement` is listed, read `RTM.md` and verify the named columns are populated for every relevant ID.
5. If `Audit gate` applies, verify the final audit cycle passed per the audit closure procedure above.
6. If `Approval gate` passes (user has signed off in `project-state.md`), proceed. Otherwise, request approval.
