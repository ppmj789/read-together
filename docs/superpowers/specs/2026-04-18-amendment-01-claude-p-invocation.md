# Spec Amendment #1 — Claude CLI Subprocess Invocation

- 작성일: 2026-04-18
- 상태: 초안 (다음 세션에서 검토·승인·적용)
- 원본 설계서: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`
- 관련 Phase 7 findings: `/home/earth/ai_team_e2e/docs/superpowers/findings/2026-04-18-phase7-findings.md` (F-T3-02)

---

## 1. 배경 — 왜 개정하는가

Phase 7 Task 3 실행 중 **F-T3-02 (CRITICAL)** 가 관찰되었다:

> Claude Code 서브에이전트는 프런트매터에 `Agent` 툴을 선언해도 **런타임에 실제로 Agent 툴을 보유하지 않음**. 즉 어떤 서브에이전트도 다른 서브에이전트를 `Agent` 툴로 호출할 수 없다.

이로 인해 원본 spec §1-1 (3단 계층 호출), §7-2 (병렬 dispatch "상위 에이전트가 한 응답 안에서 여러 Agent 호출 동시 제출") 가 현 Claude Code 구현에서 실현 불가능해졌다.

대안으로 **Claude Code CLI (`claude -p`) 의 subprocess 호출**을 Bash 툴로 실행하는 방식을 검증했다. Phase 7 Task 3 에서 다음이 **경험적으로 확인**됨:

1. `claude -p --agent <name>` 로 `.claude/agents/<name>.md` 시스템 프롬프트 완전 주입 (Korean Language 규칙 포함 모두 반영)
2. **4단 중첩 체인** 정상 작동: 나 → application-director → part-leader-sonnet → backend-developer-sonnet → 결과 역전파
3. **병렬 fan-out** 정상 작동: 응용총괄 2명 × 파트리더 2명 × 개발자 2명 = **8 최하위 동시 실행**, 응답 원문 전부 최상위까지 보존
4. 런타임 모델·effort 지정: `--model <opus|sonnet|haiku>`, `--effort <low|medium|high|xhigh|max>` — 원본 spec §2-3/§2-4 의 동적 선택 정책과 1:1 대응 (보너스: `max` 레벨 추가 지원)
5. 감리팀 경로 화이트리스트 **CLI 레벨 강제 가능**: `--add-dir <project>/99_audit --disallowed-tools Edit,Write` — 원본 spec §10 미해결 1건 해소

결론: 원본 설계의 조직도·병렬·동적 모델·감리 격리 정책이 **`claude -p` 방식으로 더 명확하게** 실현된다. 에이전트 구현 메커니즘만 전면 교체, 그 외 모든 역할·공정·산출물 체계는 유지.

---

## 2. 섹션별 개정

### 2-1. §1-2 기술 기반 — **대체**

**Before:**
> - Claude Code 전통 서브에이전트 (`.claude/agents/*.md`)만 사용. Claude Code Agent Teams 기능은 사용하지 않음(중첩 팀 미지원 제약).
> - 상위 에이전트는 `Agent` 툴을 보유하여 하위 에이전트를 직접 호출·병렬 호출한다.
> - 실무자(leaf) 에이전트는 `Agent` 툴을 갖지 않는다.
> - 감리 에이전트는 특수한 툴 제약(읽기 전용 + 감리 디렉토리 쓰기만)을 갖는다.

**After:**
> - 에이전트 정의는 `.claude/agents/*.md` 에 저장. Claude Code 내부의 Agent-tool 기반 계층 호출은 **사용하지 않음** — Phase 7 Task 3(F-T3-02)에서 서브에이전트가 런타임에 Agent 툴을 실제로 보유하지 못함을 확인.
> - 모든 하위 호출은 **Bash 툴로 `claude -p` 를 subprocess 실행**하여 수행한다:
>   ```bash
>   claude -p --agent <name> --model <m> --effort <e> \
>     --dangerously-skip-permissions \
>     [--add-dir <path>] [--disallowed-tools <list>] \
>     "<prompt>"
>   ```
> - 상위 계층(PM · 총괄 · 파트리더)에만 `Bash` 툴을 부여 → 하위 호출 주체가 됨.
> - 실무자 에이전트에는 `Bash` 툴을 **부여하지 않아** 추가 호출을 차단.
> - 감리 에이전트에도 `Bash` 미부여. 최상위(사용자) 가 직접 `claude -p --agent audit-team --add-dir <project>/99_audit --disallowed-tools Edit,Write ...` 로 명시 호출.
> - 각 `claude -p` 호출은 독립된 Claude 세션 — 완전한 컨텍스트 격리.
> - 이 방식은 Phase 7 Task 3에서 4단 체인 + 2×2×2 병렬 모두 실증됨.

### 2-2. §2-1 표준 포맷 — **변경**

frontmatter 변경 지점:

- `tools` 리스트에서 **`Agent` 제거 전면**. (원본 comment "상위 계층만 보유" 삭제.)
- 상위 계층은 `Bash` 포함. 실무자는 `Bash` 미포함. 감리팀은 `Bash` 미포함.

body 변경 지점:

- 섹션 이름 **`## Who You Call`** → **`## How You Invoke`** 로 변경.
- 내용 재작성 (상위 계층에만 해당):

  ```markdown
  ## How You Invoke (lower tier)

  하위 에이전트 호출은 Bash 툴로 다음 커맨드를 subprocess 실행하여 수행합니다:

      claude -p --agent <agent-name> \
        --model <opus|sonnet|haiku> \
        --effort <low|medium|high|xhigh|max> \
        --dangerously-skip-permissions \
        "<작업 지시 prompt>"

  복수 하위를 병렬 실행할 때는 Bash 백그라운드 패턴:

      ( claude -p --agent <A> ... > /tmp/a.log & \
        claude -p --agent <B> ... > /tmp/b.log & \
        wait )

  인용 충돌 위험 시 각 호출을 `/tmp/<unique>.sh` 스크립트로 분리하여 실행.

  자식 stdout 원문을 수거해 **압축·요약 없이** 당신의 응답에 그대로 포함시켜 상위로 전달하세요.
  ```

- 실무자 에이전트(leaf)에는 `## How You Invoke` 섹션 **없음** (하위 호출 안 하므로). 기존 Escalation Protocol 은 그대로 유지.

### 2-3. §2-2 툴 권한 정책 — **대체**

| 계층 | 기본 툴 | 하위 호출 | 추가 제약 |
|------|--------|----------|----------|
| PM · 총괄 · 파트리더 | Read, Write, Edit, Glob, Grep, **Bash** | ✅ `claude -p` subprocess | — |
| 실무자 (leaf) | Read, Write, Edit, Glob, Grep | ❌ (Bash 없음) | — |
| 감리팀 | Read, Glob, Grep, Write(감리 디렉토리만) | ❌ (Bash 없음) | 호출 시 **CLI 레벨 강제** — `--add-dir <project>/99_audit --disallowed-tools Edit,Write`(Write는 감리 디렉토리 내부만 허용하는 별도 훅 또는 샌드박스 병행 권장) |

기존 `Agent` 컬럼 **제거**.

### 2-4. §2-3 모델 할당 — **보완**

"호출 시 기록" 항목 변경:

**Before:** "상위 에이전트는 어떤 버전을 왜 골랐는지를 Agent 툴 호출 description 에 명시"

**After:** "상위 에이전트는 선택된 변형의 이유를 `claude -p` 호출 로그에 기록합니다. 권장 패턴:

    # 로그: PRG-LOGIN-01 인증 설계 — high-difficulty → security-specialist-opus
    claude -p --agent security-specialist-opus \
      --model opus --effort xhigh \
      --dangerously-skip-permissions \
      ...

호출 로그는 `projects/<프로젝트명>/agent-call-log.md` 에 append 한다(신규 산출물 — 아래 §5 참고)."

### 2-5. §2-4 effort 정책 — **보완**

"frontmatter 기본값" 항목 수정:

**Before:** "호출자는 Agent 툴 호출 단계에서 필요 시 오버라이드(구현 방식은 Claude Code 표준에 따름)."

**After:** "호출자는 `claude -p --effort <level>` 플래그로 지정. Claude Code CLI 는 `low | medium | high | xhigh | max` 5단계 지원. 기본값은 frontmatter `effort: xhigh` 이지만 **CLI 플래그가 항상 우선**.

`max` 레벨은 원본 spec 의사결정 로그 #12 에 없는 보너스 레벨로, 다음 경우에만 제한적으로 사용:
- 설계감리 재감리 3회 이상 실패 후 여전히 지적 발생
- 보안 침해 incident response
- 기타 명시적 승급 사유가 로그에 기록된 경우

일반 작업은 `xhigh` 가 상한."

### 2-6. §7-2 병렬 작업 — **대체**

**Before:** "상위 에이전트는 한 응답 안에서 여러 Agent 툴 호출을 동시 제출."

**After:** "상위 에이전트는 Bash 백그라운드 패턴으로 복수 자식을 병렬 실행합니다:

```bash
( claude -p --agent <A> ... > /tmp/a.log 2>&1 & \
  claude -p --agent <B> ... > /tmp/b.log 2>&1 & \
  wait )
```

- 각 자식 출력은 고유 로그 파일로 저장 (출력 섞임 방지).
- 인용 부호 중첩이 깊어지면 각 호출을 `/tmp/<unique>.sh` 스크립트로 분리 실행 (Phase 7 Task 3 검증).
- 수행 완료 후 로그 파일을 읽어 원문을 수거, 상위에 전달.
- 같은 파일에 대한 동시 쓰기는 금지 — 이는 프롬프트 수준 원칙이며, 추후 `.locks/` 파일 기반 잠금 또는 호출자의 사전 DAG 분석으로 강화."

### 2-7. §9 구현 빌드 순서 — **추가 항목**

기존 Phase 0–6 뒤에 **Phase 6.5 — `claude -p` 규약 적용**:

1. `scripts/validate_agent.py` 스키마 업데이트: `Agent` 툴 제거, `Bash` 유무로 leaf/non-leaf 판별, 감리팀은 기존 예외 유지.
2. 45 에이전트 파일(고정 7 + 동적 원본 13 + 파생 39 − 파생은 스크립트 재실행) 일괄 패치:
   - frontmatter `tools` 에서 `Agent` 제거, 필요 시 `Bash` 조정.
   - `## Who You Call` → `## How You Invoke` 재작성 (상위 계층만).
   - 실무자 프롬프트는 frontmatter 만 조정 (body 는 변화 적음).
3. `scripts/derive_dynamic_agents.py` 재실행 → 39 파생 재생성.
4. Drift-guard test + 전체 pytest 통과 확인.
5. `docs/orchestrator-playbook.md` 신규 작성 — 최상위 세션(사용자)이 PM 에이전트를 `claude -p` 로 호출하는 표준 패턴, 병렬 관리, 로그 수집, 에러 처리, 샘플 커맨드.
6. Phase 7 플랜 파일 업데이트 — 모든 "Agent 툴로 호출" 문구를 "Bash 로 `claude -p` 실행" 으로 교체.

### 2-8. §10 미해결 사항 — **변경**

- **해소** (체크 표시 또는 제거):
  - 기존 "감리팀 경로 화이트리스트 강제 — Claude Code frontmatter만으로는 `99_audit/` 외부 쓰기 차단 불가" → **해소**. CLI `--add-dir` + `--disallowed-tools` 로 강제 가능. (완전한 쓰기 경로 화이트리스트는 추가 훅 또는 샌드박스 병행 검토.)

- **신규 항목**:
  - Nested `claude -p` 호출의 **비용·토큰 프로파일링**. 각 호출은 별도 API 세션이라 프롬프트 캐시 미적용 — 실제 Phase 7 E2E 돌린 후 집계하여 `--max-budget-usd` 적용 기준 수립.
  - **최상위 오케스트레이터(사용자 세션) 역할 정의**. "사용자가 직접 판단 vs. PM 에이전트가 판단" 의 경계선을 `docs/orchestrator-playbook.md` 에서 명문화.
  - **호출 로그 표준**. 모든 `claude -p` 호출을 `projects/<프로젝트명>/agent-call-log.md` 에 기록하는 형식 정의 (일시, 호출자, 대상 에이전트, 모델, effort, 사유 요약). 추후 감리·감사 자료로 활용.

### 2-9. 의사결정 로그 — **추가**

기존 로그에 다음 2건 append:

| # | 결정 | 사유 |
|---|------|------|
| 13 | 하위 에이전트 호출을 **Claude Code CLI(`claude -p`) subprocess** 로 수행. Claude Code 내부 Agent-tool 계층 호출은 사용하지 않음. | Phase 7 Task 3에서 서브에이전트가 런타임에 Agent 툴을 실제로 보유하지 못함을 확인(F-T3-02). `claude -p` 는 공식 CLI 이며 nested(4단) + 병렬(2×2×2) 모두 실증. 설계의 조직도·병렬·동적 모델·감리 격리 전부 오히려 더 명확히 실현됨. |
| 14 | **감리팀 경로·툴 화이트리스트를 CLI 레벨에서 강제** (`--add-dir`, `--disallowed-tools`). | Phase 7에서 `claude -p` 플래그로 구현 가능 확인. 스펙 §10 미해결 1건 해소. |

---

## 3. 신규 산출물 (일부는 §9 Phase 6.5 작업에서 생성)

| 파일 | 내용 | 오너 |
|------|------|------|
| `docs/orchestrator-playbook.md` | 최상위 세션(사용자) 이 PM·에이전트를 다루는 표준 패턴·권고·샘플 커맨드 | (신규) |
| `projects/<프로젝트명>/agent-call-log.md` | 모든 `claude -p` 호출 기록 — 시각, 호출자, 대상, 모델, effort, 사유, 결과 요약 | PM 소유 (append-only) |

---

## 4. 영향 범위

| 영역 | 영향 | 작업량 |
|------|------|-------|
| 설계서 (`2026-04-17-ai-si-team-design.md`) | §1-2, §2-1, §2-2, §2-3, §2-4, §7-2, §9, §10, 의사결정 로그 수정 | 중 |
| 에이전트 파일 45개 | frontmatter tools 조정, `Who You Call` → `How You Invoke`, 일부 Rule 갱신 | 큼 (그러나 대부분 템플릿 일괄 치환) |
| 동적 역할 템플릿 13개 | 수정 후 파생 재생성 | 중 |
| 스크립트 2개 | `validate_agent.py` 스키마 패치, `derive_dynamic_agents.py` 그대로 | 소 |
| 테스트 | drift-guard 포함 재실행. validator test 에 신규 요구(Bash 유무로 leaf 판별) 반영 필요 | 중 |
| Phase 7 플랜 | 호출 예시 전부 `claude -p` 로 교체 | 중 |
| 오케스트레이터 플레이북 신규 | 새 파일 작성 | 중 |
| Phase 7 샘플 프로젝트(book-mgmt-api) | gitignored — Phase 7 재개 시 새로 생성 | 영향 없음 |

---

## 5. 다음 세션 실행 계획 (권장 Task 순서)

1. **Amendment 검토 및 최종 승인** (사용자).
2. **설계서 본문 수정** — 위 §2-x 항목을 원본 `2026-04-17-ai-si-team-design.md` 에 편집. 의사결정 로그 #13, #14 추가. 원본 파일명 유지 (날짜는 작성일, 버전 관리는 git 로그로).
3. **validator 업데이트**: `Agent` 툴 관련 검증 로직 제거, `Bash` 유무 기반 leaf 판별 추가. 테스트도 갱신. Drift guard 포함 모든 pytest 통과 확인.
4. **고정 에이전트 7개 패치**: project-manager, application-director, infrastructure-director, business-manager, quality-assurance, tester, audit-team. frontmatter tools 정리 + body 의 Who You Call → How You Invoke 재작성 (상위 계층만).
5. **동적 역할 템플릿 13개 패치**: 동일 요령. part-leader 는 상위 계층, 나머지 12개는 실무자.
6. **파생 39개 재생성**: `python3 scripts/derive_dynamic_agents.py` 후 drift-guard test 통과 확인.
7. **`docs/orchestrator-playbook.md` 작성**: 최상위 세션(사용자)이 PM 에이전트를 `claude -p` 로 시작하는 표준 커맨드, 단계별 관리 팁, 로그 수집·비용·에러 처리.
8. **Phase 7 플랜 업데이트**: 호출 예시 블록을 `claude -p` 로 교체. Task 0 (native agent invocation) 항목은 "확인 완료 — 새 방식으로 대체" 로 수정.
9. **Phase 7 재실행**: book-mgmt-api 재시작 (직전 샘플 데이터는 gitignored 이라 자연 소멸 또는 수동 `rm -rf` 후 새 bootstrap).

---

## 6. 실측 데이터 (Phase 7 Task 3 실행 증적)

**Test 1 — 4단 체인:**
- 커맨드: `claude -p --agent application-director --model sonnet --effort medium ...` 이 내부에서 `claude -p --agent part-leader-sonnet ...` 호출 → 이것이 다시 `claude -p --agent backend-developer-sonnet ...` 호출.
- 결과: `return a + b` 가 최하위에서 최상위까지 원문 보존되어 역전파.

**Test 2 — 병렬 2×2×2 fan-out:**
- 최상위 배치: `( claude -p --agent application-director(ALPHA) & claude -p --agent application-director(BRAVO) & wait )`
- 각 응용총괄 내부: `( claude -p --agent part-leader-sonnet(P1) & claude -p --agent part-leader-sonnet(P2) & wait )`
- 각 파트리더 내부: `( claude -p --agent backend-developer-sonnet & claude -p --agent web-developer-sonnet & wait )`
- 결과:
  - `ALPHA: { P1: [A, A], P2: [B, C] }`
  - `BRAVO: { P1: [X, X], P2: [Y, Z] }`
- 8 최하위 동시 실행, 응답 원문 전부 수집.

**에이전트 자율 행동 관찰:**
- 인용 부호 중첩 해소를 위해 자발적으로 `/tmp/*.sh` 스크립트 파일 분리
- 결과 파일(`/tmp/*.log`)로 출력 격리 → 이후 read → 상위 전달
- 모든 계층이 Korean Language 규칙 준수

이 실측이 개정 전체 근거.
