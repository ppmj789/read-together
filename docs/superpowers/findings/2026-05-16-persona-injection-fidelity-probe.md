---
name: persona-injection-fidelity-probe
description: |
  Phase 0 HARD GATE 결과 — general-purpose 서브에이전트가 프롬프트로 inline
  주입된 role 페르소나를 충실히 따르는지 실증. PASS (3/3). roles 재작성을
  inline 주입 방식으로 진행 가능.
metadata:
  type: reference
---

# Persona-Injection 충실도 Probe (Phase 0 HARD GATE)

- 일자: 2026-05-16
- 근거 plan: `docs/superpowers/plans/2026-05-16-no-claude-p-ledger-redesign.md` Task 0
- 근거 spec: `docs/superpowers/specs/2026-05-16-no-claude-p-ledger-redesign-design.md` §6-3

## 목적

claude -p 폐기 재설계는 모든 저작 노드를 `subagent_type=general-purpose`
+ 페르소나(`.claude/roles/<role>.md`) 프롬프트 inline 주입으로 dispatch
한다. general-purpose 가 주입된 role 을 충실히 따르지 못하면 roles
재작성 접근 자체를 조정해야 하므로, roles 대량 재작성 전에 검증한다.

## 방법

3개 대표 role(`application-director`, `backend-developer`, `audit-team`)
페르소나를 `[PERSONA]...[/PERSONA]` 블록으로 inline 주입하고,
`subagent_type=general-purpose`, `model=sonnet` 으로 병렬 dispatch.
각 노드에 다음을 `/tmp/persona_probe/<role>_out.md` 로 직접 Write 지시:

1. `ROLE-SELF-ID: <역할 한국어명>` (페르소나 `# Role:` 헤더 기준)
2. `## Artifacts You Own` scope 3줄 요약
3. 이 역할이 절대 하지 않는 일 1가지 (Rules 기준)

자기보고 불신 — 파일시스템에서 직접 검증.

## 결과: PASS (3/3)

| 역할 | ROLE-SELF-ID | Artifacts scope | 금지사항 |
|------|--------------|-----------------|----------|
| application-director | ✓ `응용총괄` | ✓ 01_analysis 전체·02_design 응용영역·src/backend 등 정확 | ✓ "인프라 결정 독단 금지" (Rules 정합) |
| backend-developer | ✓ `백엔드 개발자` | ✓ 02_design 도메인 PRG/IF/DB/UT·03_implementation src 정확 | ✓ "하위 위임 호출 안 함" (Rules 정합) |
| audit-team | ✓ `감리팀 (외부 감리업체)` | ✓ 99_audit 한정·audit-plan·audit-report·re-audit 정확 | ✓ "수행조직 지시·자문 교류 거부" (Rules 정합) |

3건 모두: (a) general-purpose 가 실제 파일을 Write 함, (b) 페르소나
`# Role:` 한국어명을 정확히 자기동일시, (c) Artifacts scope·역할별
금지를 환각 없이 재현.

## 결론

**roles 재작성은 페르소나 inline 주입 방식으로 진행 가능.** Phase 0
게이트 통과 — plan Phase 1 이후 진행.

self-attestation(`ROLE: <한국어명>` 첫 줄)이 신뢰 가능한 신호로 확인됨
— spec §6-3 의 노드 self-attestation 필드 운용 근거로 채택.
