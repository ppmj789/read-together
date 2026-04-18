# Spec Amendment #1 — Claude CLI Invocation Architecture (v2)

- 작성일: 2026-04-18 (v2 전면 개정)
- 상태: v2 초안 → 사용자 최종 승인 대기
- 원본 설계서: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`
- 근거:
  - Phase 7 Task 3 findings: `/home/earth/ai_team_e2e/docs/superpowers/findings/2026-04-18-phase7-findings.md` (F-T3-02, F-T3-01, F-T3-03)
  - v2 보강 실증: `/tmp/probe_step{3,4,5,6,7}.{sh,log}` (본 문서 §8)

---

## 0. v2 요약

v1 초안은 "모든 하위 호출을 `claude -p --agent <name>` 단일 트랙으로" 제안했으나, 추가 실증(probe 3–7)에서 다음 두 사실이 확정되었다:

1. `claude -p --agent <name>` 로 띄운 subprocess 세션은 **Agent 툴을 보유하지 않음** (서브에이전트 모드로 전환됨).
2. `claude -p --append-system-prompt "$(cat roles/<role>.md)"` 로 띄운 subprocess 는 **최상위 모드 유지 + Agent 툴 보유**. 단, 그 세션이 Agent 툴로 호출한 서브에이전트는 실제 툴셋이 **`Read, Glob, Grep`** 로 고정됨(frontmatter 무시, SDK/런타임 제어).

이 두 관찰이 v2 의 구조를 정한다.

### 핵심 구조

- **PM 은 Skill 로만 존재** (subprocess 호출 없음). Opus · xhigh 고정. 사용자 Claude Code 세션 시작 시 SessionStart hook 으로 자동 로딩 → 사용자 세션 자체가 PM 페르소나로 동작.
- **주 산출물 저작 호출 (Track A)**: `Bash` 툴로 `claude -p --append-system-prompt "$(cat .claude/roles/<role>.md)" --model <m> --effort <e> ...` subprocess. 각 호출이 독립된 새 최상위 세션이며 **Agent 툴 포함 전체 툴 보유**. 중첩(3–4단) 자유, Agent Teams 패턴 활용 가능.
- **자문·리뷰 응답 호출 (Track B)**: 같은 세션 안에서 **Agent 툴** 로 서브에이전트 dispatch. 서브에이전트 툴셋 = `Read, Glob, Grep` (읽기 전용). 쓰기가 필요한 자문은 존재하지 않음 — 자문가가 보고서를 *저작* 해야 하면 그것은 Track A.
- **모델·effort 위임 체인**: PM → 직속, 총괄 → 직속, 파트리더 → 직속. 두 단계 이상 건너뛴 지정 금지.
- **Effort 유효 범위**: `medium | high | xhigh`. `low`·`max` 금지.
- **사업관리가 자원·비용 관장**: 프로젝트 계획 단계에서 예산 가이드 수립, 각 단계 진입 시 PM 이 사업관리 자문 **필수 경유**, 실행 중 수시 자문.
- **감리팀**: 별도 `git worktree` 에서 Track A 로 실행 (물리적 격리).

### 파일 구조 3 계층

| 위치 | 역할 | 특징 |
|------|------|------|
| `.claude/roles/<role>.md` | **단일 소스 페르소나** | Mission/Responsibilities/Rules/Escalation 등 실체 전부. 호출 시 `cat` 으로 읽어 `--append-system-prompt` 에 주입. |
| `.claude/agents/<name>.md` | **Track B 용 얇은 껍데기** | frontmatter(name, description, tools, model, effort) + body 한 줄 "페르소나는 `.claude/roles/<role>.md` 참조, Read 로 읽고 그 역할로 행동". Agent 툴 `subagent_type` 해석에 쓰임. |
| `.claude/skills/<skill>/SKILL.md` | **Skill 껍데기** | PM 1개 + 자문 Skill(선택). 모두 Opus · xhigh 고정. body 는 `.claude/roles/<role>.md` 로 페르소나 로드 지시. |

---

## 1. 배경 — 왜 개정하는가 (v1 요지 포함, 실증 보강)

### Phase 7 Task 3 F-T3-02

PM 에이전트는 frontmatter 에 `Agent` 툴을 선언했으나, 런타임에서 **해당 툴이 실제로 노출되지 않음**. 이로 인해 원본 §1-1(3단 계층 Agent 호출), §7-2(Agent 툴 병렬 dispatch) 가 불가능.

### 보강 실증 (v2 에서 추가)

| Probe | 검증 | 결과 |
|-------|------|------|
| Step 3 | `claude -p --agent backend-developer-sonnet` 에서 Agent 툴 사용 | **부재** — Write/Edit/Bash 차단 상태에서 Agent 호출 요청 시 파일 미생성 + Sonnet 환각 응답 |
| Step 4 | `--append-system-prompt` 로 띄운 세션 Agent 툴 | 모호 (stream 없어 판별 불가, step 5 로 대체) |
| Step 5 | stream-json 기반 Agent 툴 실제 호출 확인 | **Agent 툴 호출 확정** — tool_use 블록 기록. 단 자식 서브에이전트는 "Write 없다" 보고 |
| Step 6 | 서브에이전트 Write 가능성 1차 | 부모가 지시 위반하고 직접 Write — 판별 실패 |
| Step 7 | 서브에이전트 자기 진단(Read 로 frontmatter 확인 + Write 시도) | **서브에이전트 실제 툴셋 = `Read, Glob, Grep`** 확정. frontmatter 의 tools 는 선언일 뿐이고 런타임이 별도 제한 |

→ 설계 원칙: **주 저작은 Track A(독립 최상위 세션), 자문은 Track B(서브에이전트 읽기 전용).** `claude -p --append-system-prompt` 를 통해 원본 조직도·병렬·동적 모델·감리 격리 전부 성립. Agent Teams 패턴 활용도 복구.

---

## 2. 섹션별 개정

### 2-1. §1-1 조직도 — 보완

최상위 계층에 "사용자 Claude Code 세션" 을 명시 추가. 이는 권한 계층 신설이 아니라 **PM 을 띄우는 실행 세션** 이 누구인지 문서적으로 닫기 위함.

```
사용자 Claude Code 세션 (기본 최상위 모드)
   │
   │ SessionStart hook → .claude/roles/project-manager.md 자동 주입
   │ (또는 Skill invoke: project-manager)
   │
   ▼
PM (현 세션 = PM 페르소나)
   │
   ├─ Track A: Bash claude -p --append-system-prompt roles/application-director.md
   │     → 응용총괄 (새 최상위 세션)
   │         ├─ Track A: Bash claude -p ... roles/part-leader.md  (대규모)
   │         │     └─ Track A: Bash claude -p ... roles/backend-developer.md
   │         │            └─ Track B: Agent 툴 → security-specialist 서브에이전트 (자문)
   │         └─ Track B: Agent 툴 → business-manager 서브에이전트 (예산 자문)
   │
   ├─ Track A: Bash claude -p ... roles/infrastructure-director.md → 인프라총괄
   ├─ Track B: Agent 툴 → business-manager  (단계 진입 자문)
   ├─ Track B: Agent 툴 → quality-assurance
   └─ Track B: Agent 툴 → tester

(감리) 사용자가 별도 git worktree 에서 Track A 로 audit-team 실행
```

### 2-2. §1-2 기술 기반 — 대체

**Before (원본):** Claude Code 전통 서브에이전트 + 상위 에이전트가 `Agent` 툴로 하위 호출.

**After:**

```markdown
호출 방식은 두 트랙으로 구성된다.

**Track A — 주 산출물 저작 호출 (독립 최상위 세션)**
- 상위 에이전트가 Bash 툴로 다음 커맨드를 subprocess 실행:

    claude -p --append-system-prompt "$(cat .claude/roles/<role>.md)" \
      --model <opus|sonnet|haiku> --effort <medium|high|xhigh> \
      --dangerously-skip-permissions \
      [--add-dir <worktree-path>] \
      "<작업 지시 prompt>"

- 각 호출은 **독립된 새 최상위 Claude Code 세션**. Agent 툴을 포함한 전체 내장 툴 보유.
- 서브프로세스 내부에서 또 다시 Bash 로 `claude -p --append-system-prompt ...` 호출 가능 → 다단 중첩 자유.
- 주 산출물을 저작하거나 하위를 호출해야 하는 모든 역할에 사용.

**Track B — 자문·리뷰 응답 호출 (같은 세션 내 서브에이전트)**
- 현 세션의 Agent 툴로 `subagent_type=<agent-name>` 을 지정하여 dispatch.
- 서브에이전트의 실제 툴셋은 **`Read, Glob, Grep`** 로 Claude Code 런타임이 고정 (frontmatter 의 tools 리스트는 무시됨).
- 자문·리뷰·분석 응답에만 사용. 쓰기·코드 편집·실행이 필요한 작업은 불가.
- `.claude/agents/<name>.md` 껍데기가 Agent 툴 `subagent_type` 해석에 쓰임.

**PM 은 Track A·B 어느 쪽도 아니다**
- PM 은 Skill 로만 존재 (`.claude/skills/project-manager/SKILL.md`).
- 사용자 Claude Code 세션 시작 시 SessionStart hook 으로 자동 주입 → 현 세션이 PM 페르소나.
- 사용자가 PM 과 직접 대화. 사용자 세션 자체가 PM.

**병렬 실행**
- Track A 병렬: Bash 백그라운드 패턴 (§7-2 참조).
- Track B 병렬: 한 응답 안에서 여러 Agent 툴 호출을 동시 제출 (Claude Code 네이티브).
- 감리: 별도 git worktree 에서 Track A.
```

### 2-3. §2-1 표준 포맷 — 대체 (3 파일 유형)

#### `.claude/roles/<role>.md` (단일 소스)

```markdown
---
name: <role-name>                         # kebab-case (모델 접미사 없음)
description: |
  <2-3줄 역할 요약>
---

# Role: <한국어 역할명>

## Mission
...

## Responsibilities
...

## How You Invoke Sub-executions (Track A)
(해당 역할이 Track A 호출 주체일 때만. 아래 표 양식을 반드시 채워서 기재.
 규칙은 §2-12 호출 플레이북과 반드시 정합해야 한다 — drift-guard 검증 대상.)

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| (단계 진입·이벤트·조건) | (role-name) | (산출물 또는 의사결정) | (파일 경로·변수·선행 산출물) |

## How You Consult Advisors (Track B)
(모든 Track A 호출 주체 + 실무자. 자문이 필요한 모든 상황을 아래 표로.
 §2-12 상황 기반 자문 매트릭스와 정합.)

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| (기술·비즈니스 상황) | (advisor role) | (의사결정 근거 · 리뷰) |

## How You Report
...

## Artifacts You Own
...

## Rules
...

## Escalation Protocol
...

## Language
한국어 응답 규칙
```

원본 §2-1 의 `## Who You Call` 대신 `## How You Invoke Sub-executions` (Track A 호출) + `## How You Consult Advisors` (Track B 호출) 두 섹션으로 분리.

#### `.claude/agents/<name>.md` (Track B 껍데기)

```markdown
---
name: <name>                              # role-name 또는 role-name-<opus|sonnet|haiku>
description: |
  <2-3줄 — Agent 툴 노출용. 언제 이 서브에이전트를 자문으로 부르면 좋은지.>
tools: [Read, Glob, Grep]                 # 선언적(실 런타임은 이와 무관). 문서성 목적으로만 기재.
model: opus | sonnet | haiku
effort: medium | high | xhigh
---

# Role: <한국어 역할명> (자문 서브에이전트 껍데기)

이 파일은 Agent 툴의 subagent_type 해석용 껍데기입니다.
호출되면 먼저 `Read` 툴로 다음 파일을 읽고 그 역할의 관점으로 질의에 답하세요:

  .claude/roles/<role-name>.md

자문 응답 규칙:
- 읽기 전용 분석·평가·조언만 수행합니다 (Write/Edit/Bash 미보유).
- 쓰기가 필요한 판단을 내려야 할 경우 그 사실을 응답에 명시하고 상위에게 Track A 재호출을 권고합니다.
- 응답은 한국어로 간결하게.
```

#### `.claude/skills/<skill>/SKILL.md` (Skill 껍데기)

```markdown
---
name: <skill-name>
description: |
  <언제 이 스킬을 invoke 해야 하는지 자연어. 예: "사용자와 프로젝트 관리 대화를 시작할 때, SI 프로젝트 PM 페르소나가 필요한 경우">
model: opus
effort: xhigh
---

# Skill: <한국어 Skill 명>

이 스킬이 invoke 되면 먼저 `Read` 툴로 다음 파일을 읽고 그 역할의 페르소나로 현 세션을 수행하세요:

  .claude/roles/<role-name>.md

그 역할의 Mission, Responsibilities, Rules, Escalation Protocol 을 자기 행동 규범으로 삼으세요.
```

### 2-4. §2-2 툴 권한 정책 — 대체

| 호출 경로 | 세션 특성 | 실제 툴셋 | 추가 제약 |
|----------|----------|---------|----------|
| **Track A** (`claude -p --append-system-prompt`) | 새 최상위 세션 | `Read, Write, Edit, Glob, Grep, Bash, Agent` 등 전체 | 감리 호출은 `--add-dir <audit-worktree>` 로 작업 디렉토리 격리 |
| **Track B** (Agent 툴 서브에이전트) | 현 세션 하위 | `Read, Glob, Grep` (런타임 고정) | 쓰기 불가 — 자문·분석 전용 |
| **PM Skill** (Skill invoke) | 현 세션 페르소나 확장 | 세션 전체 툴 계승 | Opus · xhigh 고정 |
| **사용자 세션** | 최상위 interactive | 전체 | — |

원본 §2-2 표의 `Agent` 컬럼 및 "Task*" 관련 모든 항목은 **삭제**. `Task*` 툴 전면 제거(§2-9 참조).

### 2-5. §2-3 모델 할당 — 대체 + 위임 체인 추가

#### 2-5-1. 고정 모델 역할 (7개) — 유지

원본과 동일: project-manager(Opus), application-director(Opus), infrastructure-director(Opus), business-manager(Sonnet), quality-assurance(Sonnet), tester(Sonnet), audit-team(Sonnet).

#### 2-5-2. 동적 모델 역할 (13개 × 3버전 = 39 파일) — 유지

파생 원칙 유지. 단일 소스는 `.claude/roles/<role>.md` 하나이며, `.claude/agents/<role>-{opus,sonnet,haiku}.md` 껍데기 3개를 자동 생성.

#### 2-5-3. 위임 체인 (신설)

모델·effort 선택 권한은 **자기 직속 하위에 대해서만** 행사한다. 두 단계 이상 건너뛴 지정은 금지 (인간 조직의 위임 원칙).

| 결정자 | 결정 대상 (소규모) | 결정 대상 (대규모) |
|-------|------------------|-----------------|
| PM | 응용총괄, 인프라총괄, 사업관리, QA, tester | (동일) |
| 응용총괄 | AA, SWA, 데이터모델러, 개발자·디자이너·퍼블리셔 | 파트리더(들) |
| 인프라총괄 | 기술아키텍트, DBA, 보안전문가, 인프라엔지니어 | (동일) |
| 파트리더 | — | 자기 파트 소속 개발자·디자이너·퍼블리셔 |
| 실무자 | — (결정 권한 없음, 자문 Track B 는 상위가 지정한 정책 준수) | (동일) |

#### 2-5-4. 자문 호출 시 모델·effort 승계

Track B(Agent 툴 서브에이전트) 호출 시 사용하는 모델·effort 는 **상위가 하위에게 내려준 "자문 정책 표"** 를 그대로 사용한다. 하위가 임의 승급 불가. 정책 표 예시는 §2-8 참조.

#### 2-5-5. Skill 모델·effort 고정

모든 Skill(PM Skill + 자문 Skill) 은 **Opus · xhigh 로 SKILL.md frontmatter 에 고정**. 이유: Skill 은 "자문이 자문받는 자보다 격이 높아야 한다" 는 원칙을 반영. 호출 세션의 모델·effort 와 무관하게 Skill 만 Opus xhigh 로 동작.

### 2-6. §2-4 Effort 정책 — 범위 축소

**유효 범위: `medium | high | xhigh` 3단계.** `low` 및 `max` 모두 금지.

#### frontmatter 기본값

| 대상 | 기본 effort | 조정 허용 | 비고 |
|------|-----------|--------|------|
| PM(Skill), 총괄, 감리, 사업관리, QA, tester | `xhigh` | ❌ | 항상 최고 |
| 동적 모델 13 역할 | `xhigh` | ✅ (medium~xhigh 내) | 호출자가 난이도 판단 |
| 모든 Skill | `xhigh` | ❌ | Opus · xhigh 고정 |

조정 시 항상 `xhigh` 유지 항목(보안, 데이터모델, 아키, 설계 · 재감리 대상 · 시정조치) 은 원본 §2-4 와 동일.

### 2-7. §2-5 감리 독립성 — 보완 (worktree 격리)

감리 독립성 프롬프트는 원본 §2-5 그대로 유지.

감리 호출 방식 보완:

```
- 감리는 별도 git worktree 에서 Track A 로 실행:
    git worktree add <audit-wt-path> <branch>
    cd <audit-wt-path>
    claude -p --append-system-prompt "$(cat .claude/roles/audit-team.md)" \
      --model sonnet --effort xhigh --dangerously-skip-permissions \
      --add-dir <audit-wt-path>/99_audit \
      "<감리 범위 및 지시>"
- 감리 세션이 worktree 안에서 무엇을 수정하든 메인 작업 트리에는 영향 없음.
- 감리 종료 후 99_audit/ 변경분만 메인으로 머지하거나 참조.
- 프롬프트·hook·permission 차단 불필요 — 물리적 격리로 대체.
```

### 2-8. §2-6 자원·비용 관장 (신설)

사업관리(business-manager) 는 모델·effort 선택의 **예산 프레임** 을 설정·감시한다. 실제 모델 선택은 §2-5-3 위임 체인의 각 상위가 수행.

- **예산 가이드 수립**: 프로젝트 계획 단계에서 PM 이 사업관리(Track B) 에 자문하여 `00_kickoff/project-plan.md` 의 "모델·effort 예산 가이드" 섹션을 작성. 권장 구조:
  - 전체 예산 규모(토큰/$ 추정)
  - 계층별·단계별 기본 모델·effort 권장 조합
  - "고난이도 · 최상위 모델 사용" 이 권고되는 작업 유형
- **단계별 자문 필수 경유**: 각 단계 게이트 체크리스트에 "PM 이 사업관리 자문을 경유하여 해당 단계 모델·effort 정책 확정" 을 1 포인트로 포함. 이 확정된 정책이 위임 체인을 통해 하위에 전파.
- **실행 중 자문**: 응용총괄·파트리더·개발자가 필요 시 Track B 로 사업관리 자문. 사업관리는 읽기 전용 자문 응답 (비용 추정, 모델 승강 권고).
- **모니터링**: `projects/<프로젝트명>/agent-call-log.md` 누적 기록. 사업관리가 단계 종료 시 집계하여 PM 에 보고 (자동 차단 없음).
- **경계**: 사업관리는 **직접 하위를 호출하지 않음**. 예산 프레임과 경보만 담당.

#### 자문 정책 표 주입 규약

상위가 Track A 로 하위를 호출할 때 프롬프트에 "자문 정책 표" 를 포함. 하위는 Track B 자문 시 이 표를 **그대로 준수**.

예시 (응용총괄이 backend-developer-sonnet 을 호출할 때 프롬프트 일부):

```
[자문 정책 — 사업관리 예산 가이드 기반]

자문이 필요할 때는 Agent 툴로 다음 서브에이전트만 호출하세요:
| 자문 대상 | subagent_type                 | model(Skill 고정) | 목적                 |
|----------|-------------------------------|-------------------|---------------------|
| 보안     | security-specialist-sonnet    | (Opus via Skill)  | 인증·권한 안전성 자문 |
| 설계     | software-architect-sonnet     | (Opus via Skill)  | 모듈 인터페이스 자문 |
| DB      | database-administrator-sonnet | (Opus via Skill)  | 스키마·인덱스 자문   |
| 예산    | business-manager              | (Opus via Skill)  | 추가 자원 승인 요청  |
```

(Skill 이 Opus · xhigh 고정이므로 자문 실체는 Opus. 껍데기 `subagent_type` 이름만 sonnet/haiku 변형이더라도 Skill 로 invoke 하면 Opus 로 동작. Agent 툴로 바로 dispatch 하는 경우엔 껍데기의 model 을 따름.)

### 2-9. §7-2 병렬 작업 — 대체

```
**원칙**: 단계 내 의존성 없는 산출물은 반드시 병렬.

**Track A 병렬 (다수 개발자 동시 호출)**
- 상위 에이전트는 Bash 백그라운드 패턴으로 복수 자식 Track A 호출:

    ( claude -p --append-system-prompt "$(cat roles/backend-developer.md)" \
        --model sonnet --effort high --dangerously-skip-permissions \
        "<지시1>" > /tmp/<unique1>.log 2>&1 & \
      claude -p --append-system-prompt "$(cat roles/web-developer.md)" \
        --model sonnet --effort high --dangerously-skip-permissions \
        "<지시2>" > /tmp/<unique2>.log 2>&1 & \
      wait )

- 각 자식 출력은 고유 로그 파일로 분리.
- 인용 충돌이 깊어지면 /tmp/<unique>.sh 스크립트로 분리 실행 (Phase 7 Task 3 검증).
- 수행 완료 후 로그를 Read 로 수거 → 상위가 통합.

**Track B 병렬 (자문 다중 dispatch)**
- 한 응답 안에서 여러 Agent 툴 호출을 동시 제출 (Claude Code 네이티브).
- 예: backend-developer 가 security·DBA·software-architect 세 자문을 한 턴에 병렬 dispatch.

**Agent Teams 패턴**
- 파트리더 또는 응용총괄 세션(Track A 최상위 모드)에서 개발자들을 Track A 로 병렬 호출하면서
  Agent 툴로 자문가를 즉시 dispatch → 수평 협업 구성.
- 산출물 공동 저작은 파일 기반(§1-3) — 개발자들이 공유 작업 디렉토리에서 파일을 주고받음.

**쓰기 충돌 방지**
- 동일 파일을 여러 Track A 자식이 동시 수정 금지 (프롬프트 수준 원칙).
- 향후 `.locks/` 디렉토리 또는 호출자의 사전 DAG 분석으로 강화 (§10 미해결).
```

### 2-10. §9 구현 빌드 순서 — 추가

기존 Phase 0–6 뒤에 **Phase 6.5 — v2 아키텍처 적용** 추가.

1. **`.claude/roles/` 디렉토리 신설**: 20개 역할의 단일 소스 페르소나 파일 작성(기존 `.claude/agents/templates/` 내용을 이쪽으로 이전·재구성).
2. **`.claude/agents/` 재생성**: 기존 45개 파일을 얇은 껍데기로 교체. `scripts/derive_dynamic_agents.py` 를 "껍데기 생성" 모드로 수정. PM 용 `project-manager.md` 는 **삭제** (Skill 전용).
3. **`.claude/skills/` 디렉토리 신설**:
   - 필수: `.claude/skills/project-manager/SKILL.md`
   - 선택(초기 생략 가능): 자문 Skill 들 (security-specialist, business-manager 등). 필요성·비용 대비 효과를 Phase 7 실측 후 결정.
4. **SessionStart hook 설정**: `.claude/settings.json` 의 `hooks.SessionStart` 에 project-manager Skill 자동 invoke 추가 — 구체 방식은 `docs/orchestrator-playbook.md` 에 기재.
5. **`scripts/validate_agent.py` 스키마 업데이트**:
   - `Agent` · `Task*` 관련 검증 로직 제거.
   - agents 껍데기 파일은 "body 가 roles/ 참조 지시 한 단락" 만 허용하는 lint 추가.
   - skills 파일은 "Opus · xhigh 고정" 검증.
6. **`scripts/derive_dynamic_agents.py` 재실행** → 39 파생 껍데기 재생성.
7. **Drift-guard test + 전체 pytest 통과 확인**.
8. **`docs/orchestrator-playbook.md` 신규 작성**:
   - 사용자가 `cd /home/earth/ai_team && claude` 로 진입했을 때 PM Skill 이 자동 로딩되어 PM 과 대화 시작하는 표준 UX.
   - Track A / Track B 호출 패턴 샘플 커맨드.
   - 병렬 관리, 로그 수집, 에러 처리, 감리 worktree 실행.
9. **Phase 7 플랜 파일 업데이트**: 모든 "Agent 툴로 호출", "claude -p --agent" 문구를 Track A/B 규약으로 교체. Task 0 항목을 "v2 실증 완료" 로 갱신.
10. **`agent-call-log.md` 템플릿 신설**: 모든 Track A·B 호출을 append 하는 형식 정의(시각, 호출자, 대상, 트랙, 모델, effort, 사유 요약).
11. **`docs/call-playbook.md` 신규 작성**: §2-12 호출 플레이북(단계별 매트릭스 · 상황 기반 자문 매트릭스 · 에스컬레이션 경로 · 금지 사례) 정본. Role 파일 20개 작성 시 이 플레이북을 참조하여 각 Role 파일의 `## How You Invoke Sub-executions` / `## How You Consult Advisors` 표를 채움.
12. **`scripts/validate_agent.py` drift-guard 확장**: Role 파일의 호출 규칙 표가 `docs/call-playbook.md` 의 매트릭스와 정합하는지 검증 (역할별 entry 누락·잉여 탐지, 금지 사례 위반 탐지).
13. **산출물 템플릿 재구성**: 기존 `templates/` 하위의 단일 파일 템플릿들을 `templates/artifacts/<artifact-type>/` 디렉토리 + `index.md.tmpl` + 자식 템플릿 구조로 재편성 (§2-13-8).
14. **`scripts/scaffold_artifact.py` 신설**: 에이전트가 산출물 디렉토리를 만들 때 index.md + 초기 자식 틀 자동 생성 (§2-13-8).
15. **`scripts/validate_artifact_hierarchy.py` 신설**: index.md 자식 목록·실제 파일·depends-on/referenced-by 양방향 정합·3-hop 상한 검증.
16. **`scripts/bootstrap_project.py` 업데이트**: 프로젝트 스캐폴드 시 §2-13-2 의 신규 디렉토리 구조로 생성. 규모별 분기(소규모 완화 / 대규모 강화) 반영.

### 2-11. §10 미해결 사항 — 축소 + 신규

#### 해소
- 원본 "감리팀 경로 화이트리스트" → **해소**. `git worktree` 격리로 해결 (§2-7).
- v1 "감리팀 경로 화이트리스트 (CLI 플래그 제한적)" → **해소**.

#### 유지·보완
- **병렬 호출 파일 잠금**: 원본 유지. `.locks/` 또는 DAG 사전 분석 검토.
- **`part-leader` 수 동적 결정**: 원본 유지.
- **감리 세션 개시 UX**: 슬래시 커맨드 `/audit <stage>` vs 자연어 지시 — 구현 시 결정.

#### 신규
- **프롬프트 캐시 자연 히트 검증**: 같은 에이전트를 5분 TTL 내 반복 호출 시 Anthropic API prompt cache 히트 여부 Phase 6.5 초반 실증.
- **서브에이전트(Track B) 확장 툴 주입 검증**: 향후 Claude Code 업데이트로 서브에이전트 툴셋이 확장될 수 있음. 정기 점검.
- **Skill 의 실제 동작 실증**: probe 로 검증되지 않은 가정(Skill 이 `.claude/roles/<role>.md` 를 Read 로 로드하여 페르소나 전환). Phase 6.5 초반 1 스텝.
- **모델·effort 호출 로그 표준**: `agent-call-log.md` append-only 포맷 정의. 추후 감사 자료로 활용.

### 2-12. 호출 플레이북 — 신설

각 Role 파일의 호출 규칙은 본 서브섹션의 매트릭스와 **정합해야 한다**. 정본은 `docs/call-playbook.md` 에 별도 파일로 둔다 (§3 신규 산출물). `scripts/validate_agent.py` 의 drift-guard 가 양자 일관성 검증.

#### 2-12-1. 단계별 호출 매트릭스 (V-Model)

| 단계 | 주도자 | 필수 Track A (주 산출물 저작) | 필수 Track B (자문·리뷰) |
|------|-------|-----------------------------|-------------------------|
| 00_kickoff | PM (Skill, 사용자 세션) | — (PM 직접 저작) | business-manager(예산 가이드), quality-assurance(계획 리뷰) |
| 01_analysis | application-director | application-architect, data-modeler, tester | technical-architect, quality-assurance |
| 02_design (소규모) | application-director + infrastructure-director | software-architect, designer, web-publisher, data-modeler(물리), technical-architect, database-administrator, security-specialist | quality-assurance |
| 02_design (대규모) | application-director (파트 분할) | part-leader × N + 공통 설계 역할 | (동일) |
| 03_implementation (소규모) | application-director | backend-developer, web-developer, batch-developer | security-specialist, database-administrator, software-architect 수시 |
| 03_implementation (대규모) | part-leader | 파트별 개발자들 | (동일) + tester 수시 |
| 04_test | tester (PM 감독) | tester(통합·시스템·UAT 실행), infrastructure-engineer(테스트 환경) | quality-assurance |
| 05_deployment | infrastructure-engineer | infrastructure-engineer, technical-architect(리뷰) | security-specialist |
| 감리 (analysis, 대규모만) | 사용자 호출 | audit-team (worktree) | — |
| 감리 (design, 필수) | 사용자 호출 | audit-team (worktree) | — |
| 감리 (closing, 필수) | 사용자 호출 | audit-team (worktree) | — |

#### 2-12-2. 상황 기반 자문 매트릭스 (Track B)

**보안**
| 트리거 | 자문 대상 |
|-------|---------|
| 인증·세션·결제 로직 작성 또는 리뷰 | security-specialist |
| 외부 API 연동 설계·구현 | security-specialist + software-architect |
| 감사 로그·민감정보 저장 설계 | security-specialist + database-administrator |
| 권한 모델·RBAC 설계 | security-specialist + application-architect |

**데이터베이스**
| 트리거 | 자문 대상 |
|-------|---------|
| 복잡 쿼리·인덱스 설계 | database-administrator |
| 스키마 변경·마이그레이션 계획 | database-administrator + data-modeler |
| 트랜잭션 격리 수준 판단 | database-administrator + software-architect |

**성능·확장성**
| 트리거 | 자문 대상 |
|-------|---------|
| 대용량 처리 설계 | technical-architect + database-administrator |
| 배치 최적화 | technical-architect + batch-developer |
| 캐시·큐 전략 | technical-architect + software-architect |

**아키텍처·인터페이스**
| 트리거 | 자문 대상 |
|-------|---------|
| 모듈 경계 모호 | software-architect |
| 외부 시스템 연동 아키 | technical-architect + software-architect |
| 프론트·백 인터페이스 스펙 | software-architect + backend-developer + web-developer |

**예산·일정**
| 트리거 | 자문 대상 |
|-------|---------|
| 예산 초과 우려 | business-manager |
| 일정 지연 우려 | business-manager + PM |
| 추가 자원 요청 | business-manager |

**품질·테스트**
| 트리거 | 자문 대상 |
|-------|---------|
| 품질 기준 해석 모호 | quality-assurance |
| 테스트 케이스 해석 난해 | tester |
| 단계 산출물 품질 우려 | quality-assurance + 해당 단계 주도자 |

#### 2-12-3. 에스컬레이션 경로

| 발생자 | 1차 | 2차 | 3차 |
|-------|----|----|-----|
| 실무 개발자 | 파트리더(대규모) / 응용총괄(소규모) | PM | 사용자 |
| 자문가 (Track B 중) | 자문 요청자 | 요청자의 상위 | PM |
| 파트리더 | 응용총괄 | PM | 사용자 |
| 응용총괄 · 인프라총괄 | PM | 사용자 | — |
| PM | 사용자 | — | — |
| 감리 | PM (지적만 전달, 판단·처리는 PM) | — | — |

모든 에스컬레이션은 `projects/<프로젝트명>/escalations.md` 에 append (원본 §7-3).

#### 2-12-4. 금지된 호출 (위임 체인 위반)

| 금지 사례 | 사유 |
|---------|------|
| PM 이 개발자·파트리더를 직접 Track A 호출 (총괄 건너뜀) | 두 단계 이상 건너뛴 지정 — §2-5-3 위배 |
| 응용총괄이 개발자의 모델·effort 를 파트리더 경유 없이 지정 (대규모 시) | 동일 |
| 실무자가 다른 실무자를 Track A 호출 | 실무자는 Track A 호출 권한 없음 (자문 Track B 만) |
| 사업관리가 직접 하위 에이전트 호출 (Track A 또는 B) | 예산 프레임·모니터링만 담당 (§2-8) |
| 감리팀이 코드·산출물 직접 수정 | 감리는 읽기 전용 지적만 (§2-7) |
| PM 을 `claude -p` subprocess 로 호출 | PM 은 Skill 전용 (#14) |
| 자문 Skill 을 Opus·xhigh 외 값으로 호출 | Skill 은 frontmatter 레벨 고정 (#19) |

### 2-13. 문서 산출물 계층화 — 신설 (원본 §3-1 · §5 보완)

원본 §3-1 의 산출물 디렉토리 구조는 단계별 분리까지만 규정하고, 각 산출물(requirements.md · screen-spec.md · program-list.md 등)은 단일 파일을 전제했다. 대규모 프로젝트에서는 단일 파일이 **수십~수백 KB** 로 폭증하여 하위 에이전트가 자기 업무에 필요한 일부만 참조하더라도 **전체 파일 로드 → 토큰 과다 소모** 가 필연. 본 서브섹션은 모든 산출물을 **디렉토리 + `index.md` + 자식 파일** 3계층 이상으로 분해하여, 에이전트가 "인덱스 → 인덱스 → 대상" 3-hop 이하로 필요한 부분만 로드할 수 있게 한다.

#### 2-13-1. 계층 구조 원칙

- **산출물은 디렉토리, 자식은 파일**: 원본 §3-1 의 모든 산출물(단계별 디렉토리 안의 단일 `.md` 파일) 을 **동명 디렉토리**로 전환.
  - 예: `02_design/screen-spec.md` → `02_design/screens/` 디렉토리
  - 예: `02_design/program-list.md` → `02_design/programs/` 디렉토리
  - 예: `01_analysis/requirements.md` → `01_analysis/requirements/` 디렉토리
- **각 디렉토리에 `index.md` 1개 필수**: 해당 디렉토리의 엔트리 포인트. 자식 목록과 요약을 담는다.
- **자식은 의미 단위로 분해**: RQ-ID, SCN-ID, PRG-ID, ENT-ID 등 ID 기반 개별 파일. 대규모 시 **그룹 서브디렉토리**(예: `SCN-AUTH/`, `PRG-AUTH/`) 로 2단 계층 허용.
- **3-hop 상한**: `<단계>/index.md` → `<단계>/<영역>/index.md` → `<단계>/<영역>/<그룹>/<ID>.md` 가 최대 깊이. 3-hop 으로 해결되지 않으면 영역 분할을 재검토.

#### 2-13-2. 디렉토리 구조 예시 (원본 §3-1 교체)

```
projects/<프로젝트명>/
├─ 00_kickoff/
│  ├─ index.md
│  ├─ statement-of-work.md                  (단일 파일 유지 — 사용자 제공)
│  ├─ project-plan/
│  │  ├─ index.md
│  │  ├─ overview.md
│  │  ├─ scope.md
│  │  ├─ organization.md
│  │  ├─ schedule.md
│  │  ├─ budget.md                           # 사업관리 작성 (§2-8 "모델·effort 예산 가이드" 포함)
│  │  └─ wbs/
│  │     ├─ index.md
│  │     └─ wbs-phase-<NN>-<name>.md
│  └─ rollback-history.md                    (append-only 로그, 단일 파일 유지)
│
├─ 01_analysis/
│  ├─ index.md
│  ├─ requirements/
│  │  ├─ index.md                            # 전체 RQ-ID 목록
│  │  ├─ RQ-<group>/
│  │  │  ├─ index.md
│  │  │  └─ RQ-<group>-<NN>-<slug>.md
│  │  └─ ...
│  ├─ as-is-analysis/
│  │  ├─ index.md
│  │  └─ <section>.md
│  ├─ to-be-workflow/
│  │  ├─ index.md
│  │  └─ WF-<name>.md
│  ├─ uat-test-cases/
│  │  ├─ index.md
│  │  └─ UT-<group>/UT-<group>-<NN>.md
│  ├─ integration-test-cases/
│  │  ├─ index.md
│  │  └─ IT-<group>/IT-<group>-<NN>.md
│  └─ reviews/
│     ├─ index.md
│     └─ <artifact-id>-review-v<N>.md
│
├─ 02_design/
│  ├─ index.md
│  ├─ architecture/
│  │  ├─ index.md
│  │  ├─ overview.md
│  │  ├─ layers.md
│  │  └─ components/
│  │     ├─ index.md
│  │     └─ CMP-<name>.md
│  ├─ db/
│  │  ├─ index.md
│  │  ├─ logical/
│  │  │  ├─ index.md                         # 엔티티 목록
│  │  │  └─ ENT-<name>.md
│  │  └─ physical/
│  │     ├─ index.md                         # 테이블 목록
│  │     └─ TBL-<name>.md
│  ├─ screens/
│  │  ├─ index.md
│  │  └─ SCN-<group>/
│  │     ├─ index.md
│  │     └─ SCN-<group>-<NN>-<slug>.md
│  ├─ interfaces/
│  │  ├─ index.md
│  │  └─ IF-<group>/IF-<NN>.md
│  ├─ programs/
│  │  ├─ index.md                            # 전체 PRG-ID 목록
│  │  └─ PRG-<group>/
│  │     ├─ index.md
│  │     └─ PRG-<group>-<NN>-<slug>.md
│  ├─ unit-test-cases/
│  │  ├─ index.md
│  │  └─ UT-UNIT-<group>/UT-UNIT-<NN>.md
│  ├─ security-review/
│  │  ├─ index.md
│  │  └─ findings/FIND-<NN>-<slug>.md
│  └─ reviews/
│     ├─ index.md
│     └─ <artifact-id>-review-v<N>.md
│
├─ 03_implementation/
│  ├─ index.md
│  ├─ unit-test-results/
│  │  ├─ index.md
│  │  └─ UT-RES-<group>/...
│  └─ reviews/
│     └─ ...
│
├─ 04_test/
│  ├─ index.md
│  ├─ integration-test-results/index.md, IT-RES-*.md
│  ├─ system-test-results/index.md, ST-RES-*.md
│  ├─ uat-results/index.md, UAT-RES-*.md
│  ├─ qa-report/index.md, <section>.md
│  └─ reviews/
│
├─ 05_deployment/
│  ├─ index.md
│  ├─ deployment-plan/index.md + <section>.md
│  ├─ operation-manual/index.md + <section>.md
│  ├─ training-material/index.md + <section>.md
│  └─ reviews/
│
├─ 99_audit/
│  ├─ 01_analysis-audit/ (대규모 시)
│  │  ├─ index.md
│  │  ├─ audit-plan.md
│  │  ├─ audit-report/index.md, FIND-*.md
│  │  ├─ corrective-action-plan/index.md, ACT-*.md
│  │  ├─ corrective-action-result/index.md, RES-*.md
│  │  └─ re-audit-report-v<N>/index.md, FIND-*.md
│  ├─ 02_design-audit/ (동일 구조)
│  └─ 03_closing-audit/ (동일 구조)
│
├─ change-requests/
│  ├─ index.md
│  └─ CR-<seq>/
│     ├─ request.md
│     ├─ impact-analysis.md
│     └─ decision.md
│
├─ escalations.md                             (append-only 로그, 단일 파일 유지)
├─ project-state.md                            (단일 파일 유지 — 상태 표)
└─ RTM/                                        (§2-13-4 참조)
```

**단일 파일 유지 예외**: `statement-of-work.md`, `rollback-history.md`, `escalations.md`, `project-state.md` — 작고 append-only 성격이거나 외부 입력이라 분할 이점 없음.

#### 2-13-3. `index.md` 표준 포맷

```markdown
---
artifact-id: <parent-id>                # 예: SCREENS, SCN-AUTH, PROGRAMS
type: index
stage: <00_kickoff | 01_analysis | ...>
area: <screens | programs | ...>
child-count: <N>
version: <v1 | v2 ...>
---

# <단계> / <영역> [/ <그룹>] — <한국어 제목>

## 개요
(2–3줄 — 이 디렉토리가 무엇을 담는지, 상위 산출물과 관계)

## 하위 항목
| ID | 제목 | 파일 | 담당 | 상태 | 요약 |
|----|------|------|-----|-----|------|
| SCN-AUTH-01 | 로그인 페이지 | [./SCN-AUTH-01-login.md](./SCN-AUTH-01-login.md) | web-publisher | in-review | 이메일·비밀번호 + OAuth |
| ... |

## 상위 인덱스
- [../index.md](../index.md)

## 의존성 요약 (선택)
| 자식 ID | depends-on | referenced-by |
|--------|-----------|--------------|
| SCN-AUTH-01 | RQ-AUTH-01, CMP-AUTH | PRG-AUTH-01, IF-AUTH-login |

## 변경 이력
- 2026-MM-DD v1: 초기 작성 (owner: <role>)
```

#### 2-13-4. 자식 파일 frontmatter 규약 (상호 참조)

```markdown
---
id: <ID>                              # 예: SCN-AUTH-01, PRG-AUTH-01
title: <한국어 제목>
stage: <단계>
area: <영역>
group: <그룹, 선택>
owner: <role-name>                    # 저작 담당 역할
depends-on: [<ID>, <ID>, ...]         # 선행 산출물
referenced-by: [<ID>, ...]            # 후행 산출물 (갱신 시 index drift-guard 갱신)
reviewed-by: [<review file 경로>, ...]
status: draft | in-review | approved | rollback
---

# <한국어 제목>

## 본문
...
```

의존성·역참조는 원본 §1-3 의 "파일 기반 협업" 원칙을 계층 구조에서도 유지하는 수단. drift-guard 가 양방향 일관성 검증.

#### 2-13-5. RTM 계층화 (원본 §5 보완)

원본 §5 의 단일 `RTM.md` 를 계층화:

```
projects/<프로젝트명>/RTM/
├─ index.md                          # RQ-ID 마스터 목록 · 단계별 진행 상태
├─ by-stage/
│  ├─ analysis.md                    # 01_analysis 에서 작성된 RQ 추적
│  ├─ design.md
│  ├─ implementation.md
│  ├─ test.md
│  └─ deployment.md
├─ by-part/                          # 대규모 시만 생성
│  ├─ index.md
│  └─ <part-name>.md
└─ _archived/<YYYYMMDD>-v<N>/        # rollback 백업 (원본 §5-4 유지, 디렉토리로 확장)
   ├─ index.md
   └─ <snapshot files>.md
```

- `RTM/index.md` 가 모든 연결의 허브. 에이전트가 RQ-ID 를 찾을 때 가장 먼저 Read.
- 단계별·파트별 분리 파일은 상세 매핑(산출물 파일 경로들) 을 담음.
- Rollback 시 스냅샷을 `_archived/<날짜>-v<N>/` 디렉토리로 통째 보존.

#### 2-13-6. 에이전트 로딩 전략 (3-hop 이하)

예: 대규모 프로젝트의 web-developer-sonnet (auth 파트 소속) 이 `PRG-AUTH-01 로그인 화면 구현` 작업 배정받음.

1. **1-hop** — `projects/<>/02_design/programs/PRG-AUTH/index.md` Read (~1KB): 파트 내 프로그램 목록 확인 → PRG-AUTH-01 파일 경로 획득.
2. **2-hop** — `projects/<>/02_design/programs/PRG-AUTH/PRG-AUTH-01-login.md` Read (~3KB): 본체 로드.
3. **3-hop (필요 시)** — frontmatter `depends-on: [RQ-AUTH-01, SCN-AUTH-01, IF-AUTH-login]` 중 관련 1–2개 Read (~5KB).

**총 context ≈ 5–10KB**. 같은 정보를 단일 `program-list.md` (수십~수백 KB) 로 로드 대비 **80–94% 절감**.

자문(Track B) 호출 시 `agent-call-log.md` 에 "어느 인덱스·어느 자식 파일 참조했는지" 함께 기록 → 향후 참조 패턴 분석 자료.

#### 2-13-7. 규모별 적용

- **일관성 원칙**: 모든 규모에 동일한 계층 구조 적용. 스케일 업 시 재구조화 비용 0.
- **소규모 완화**: 자식이 **1–2개** 뿐인 디렉토리는 `index.md` 생략 허용 (자식 파일 자체가 충분히 작을 때). 자식이 3개 이상이면 `index.md` 필수.
- **대규모 강화**: 파트별 디렉토리 하위에 `SCN-<part>-<group>/`, `PRG-<part>-<group>/` 같은 3단 계층 강제. `RTM/by-part/` 활성화.

#### 2-13-8. 관련 스크립트 · 템플릿

- **`scripts/scaffold_artifact.py` 신설**: 에이전트가 새 산출물 디렉토리를 만들 때 `index.md` + 초기 자식 틀 자동 생성. 호출 규약:
  ```
  python3 scripts/scaffold_artifact.py <project> <stage> <area> [--group <name>]
  ```
- **`scripts/validate_artifact_hierarchy.py` 신설**: drift-guard. `index.md` 의 자식 목록과 실제 파일 시스템 일치, frontmatter `depends-on` / `referenced-by` 양방향 정합, 3-hop 상한 준수 검증.
- **`templates/artifacts/<artifact-type>/` 재구성**: 템플릿을 **유형별 디렉토리** 로 재편성. 각 유형에 `index.md.tmpl` + 하나 이상의 자식 템플릿.
  - 예: `templates/artifacts/screens/index.md.tmpl`, `templates/artifacts/screens/screen.md.tmpl`

### 2-14. 의사결정 로그 — 변경

#### 철회
- **#1 (전통 서브에이전트 + Agent Teams 미사용)** — 철회. v2 에서 Agent Teams 패턴은 Track A 세션 내 Agent 툴로 활용 가능.

#### 신규

| # | 결정 | 사유 |
|---|------|------|
| 13 | 하위 호출 메커니즘을 **Claude Code CLI (`claude -p`) subprocess** 로 일원화 | F-T3-02 로 서브에이전트 런타임 Agent 툴 부재 확인 |
| 14 | PM 은 Skill 로만 존재 (subprocess 호출 금지). 사용자 Claude Code 세션 = PM 페르소나 | `claude -p --agent project-manager` 경로는 서브에이전트 모드라 Agent 툴 없음. Skill + SessionStart 가 자연스러움 |
| 15 | 감리 격리는 `git worktree` + Track A | probe/프롬프트·hook 차단보다 물리 격리가 간결·확실 |
| 16 | 모델·effort 지정 권한은 **자기 직속 하위에 한정**. 두 단계 이상 건너뛴 지정 금지 | 인간 조직 위임 원칙. 관리 가시성·책임 경계 확보 |
| 17 | 사업관리가 모델·effort **예산 프레임 수립·모니터링** 담당. 실제 선택은 위임 체인 내 상위 | 자원·비용의 전사적 관리자 역할 분리 |
| 18 | Effort 범위 `medium | high | xhigh` 로 제한. `low`·`max` 금지 | 사용자 지정 (품질 하한·비용 상한 모두 보수적) |
| 19 | 자문 Skill + PM Skill 모두 **Opus · xhigh 고정** | 자문가는 자문받는 자보다 격이 높아야 한다 |
| 20 | 모든 Track A 호출은 `claude -p --append-system-prompt "$(cat roles/<role>.md)"` 로 **최상위 모드 유지** + Agent 툴 보유 | probe step 5·6·7 로 확정. `--agent` 플래그는 서브에이전트 모드로 전환시켜 Agent 툴을 빼앗음 |
| 21 | Track B 서브에이전트 실제 툴셋 = **`Read, Glob, Grep`** (SDK 레벨 고정) | probe step 7 에서 서브에이전트가 자기 frontmatter 를 Read 한 결과 실제 툴과 불일치 확인. 쓰기가 필요한 호출은 Track A |
| 22 | `--disallowed-tools` 는 부모 세션에만 적용. 서브에이전트는 원래 읽기 전용이라 별도 제어 불필요 | probe step 5 의 "상속" 가설은 step 7 에서 "Read/Glob/Grep 기본값" 으로 재해석됨 |
| 23 | `Task*` 툴 (TaskCreate/Update/List/Get) 전면 제거 | Agent 툴 제거와 동일 맥락. 서브에이전트 추적 기능은 Track A·B 구조에서 활용 불가 |
| 24 | 실무자 Bash 전면 허용 | 테스트·빌드·린터 실행에 필요. `claude` 바이너리 재호출 차단 같은 별도 규칙 없음 |
| 25 | 역할별 호출 규칙은 **Role 파일(자기 책임 표) + `docs/call-playbook.md`(중앙 매트릭스)** 2단으로 유지. drift-guard 로 일관성 강제 | 시점 기반·상황 기반 호출 판단을 명시화하여 에이전트 행동 재현성 확보. 중앙 문서로 전체 조망, Role 파일로 에이전트 자기 행동 규범 주입 |
| 26 | 모든 산출물을 **디렉토리 + `index.md` + 자식 파일** 계층으로 분해 (3-hop 상한). 원본 §3-1·§5 의 단일 파일 방식 전환 | 대규모 프로젝트에서 단일 파일(수십~수백 KB)이 후속 에이전트의 context 를 극심히 소모. 인덱스 3단 이하로 필요 영역만 로드하여 80–94% 토큰 절감 |

---

## 3. 신규 산출물

| 파일/디렉토리 | 내용 | 오너 |
|-------------|------|------|
| `.claude/roles/` | 20개 역할 단일 소스 페르소나 | (신규) |
| `.claude/skills/project-manager/SKILL.md` | PM Skill 껍데기 | (신규) |
| `.claude/skills/<advisor>/SKILL.md` | 자문 Skill 껍데기 (선택, Phase 7 실측 후 도입 여부 결정) | (선택) |
| `.claude/settings.json` — `hooks.SessionStart` | PM Skill 자동 로딩 | (갱신) |
| `docs/orchestrator-playbook.md` | 사용자 · PM Skill 시작 표준 패턴, Track A/B 샘플 커맨드, 병렬·로그·에러 처리 | (신규) |
| `docs/call-playbook.md` | §2-12 호출 플레이북 정본 (단계별·상황별 매트릭스 · 에스컬레이션 · 금지 사례). Role 파일들의 호출 규칙 정합성 기준 | (신규) |
| `templates/artifacts/<artifact-type>/` | 산출물 유형별 디렉토리. 각 유형에 `index.md.tmpl` + 자식 템플릿 (§2-13-8) | (재편성) |
| `scripts/scaffold_artifact.py` | 산출물 디렉토리 스캐폴드 스크립트 | (신규) |
| `scripts/validate_artifact_hierarchy.py` | index.md · 파일·의존성 정합 drift-guard | (신규) |
| `projects/<프로젝트명>/agent-call-log.md` | 모든 Track A·B 호출 기록 append-only | PM 소유 |
| `projects/<프로젝트명>/00_kickoff/project-plan.md` 의 "모델·effort 예산 가이드" 섹션 | 사업관리 작성 | business-manager |

---

## 4. 영향 범위

| 영역 | 영향 | 작업량 |
|------|------|-------|
| 설계서 본문 (`2026-04-17-ai-si-team-design.md`) | §1-1, §1-2, §2-1~§2-5, §2-6(신설), §7-2, §9, §10, 의사결정 로그 | 큼 |
| `.claude/agents/` 45개 | 얇은 껍데기로 교체 (PM 삭제 → 44개) | 큼 (자동화 가능) |
| `.claude/roles/` 20개 신규 | 원본 페르소나 내용 이전·재구성 | 중 (기존 내용 재활용) |
| `.claude/skills/` | project-manager Skill 1개 필수, 자문 Skill 선택 | 중 |
| `.claude/settings.json` | SessionStart hook 추가 | 소 |
| 스크립트 2개 | `validate_agent.py` 스키마 · `derive_dynamic_agents.py` 껍데기 모드 | 중 |
| 테스트 | drift-guard 재설정, validator test 갱신 | 중 |
| Phase 7 플랜 | 호출 예시 전부 Track A/B 로 교체 | 중 |
| orchestrator-playbook 신규 | 새 파일 작성 | 중 |
| Phase 7 샘플 프로젝트(book-mgmt-api) | gitignored — 재시작 시 새 bootstrap | 영향 없음 |

---

## 5. 다음 세션 실행 계획

1. **본 v2 Amendment 사용자 최종 승인**.
2. **원본 설계서 본문 수정**: §1-1 ~ §10 + 의사결정 로그를 v2 대로 편집. 원본 파일명 유지 (버전은 git 로그).
3. **`.claude/roles/` 20개 파일 작성** (기존 에이전트 body 에서 페르소나 본문만 이전).
4. **`scripts/validate_agent.py` · `scripts/derive_dynamic_agents.py` 업데이트** + pytest 갱신.
5. **에이전트 껍데기 45개 생성** (자동화). PM 껍데기는 삭제.
6. **`.claude/skills/project-manager/SKILL.md` 작성**.
7. **SessionStart hook 설정** (`.claude/settings.json`).
8. **Phase 6.5 선행 실증 1–2 건**:
   - Skill invoke → `.claude/roles/<role>.md` 로드 → 페르소나 전환 동작 확인.
   - 같은 에이전트 반복 호출 시 Anthropic prompt cache 히트 여부 간단 측정.
9. **`docs/orchestrator-playbook.md` 작성**.
10. **Phase 7 플랜 업데이트** (Track A/B 규약 반영).
11. **Phase 7 재실행**: book-mgmt-api 새 bootstrap 후 전체 공정.

---

## 6. 실측 데이터 (Phase 7 Task 3 + v2 보강 probes)

### 6-1. Phase 7 Task 3 (v1 기반)

- **4단 체인**: `claude -p --agent application-director` → `claude -p --agent part-leader-sonnet` → `claude -p --agent backend-developer-sonnet` → 결과 역전파 정상.
- **2×2×2 병렬 fan-out**: ALPHA/BRAVO 총괄 × P1/P2 파트리더 × backend/web 개발자 = 8 leaf 동시, 응답 원문 최상위까지 보존.
- **자율 행동**: 인용 충돌 회피 위한 `/tmp/*.sh` 분리, `/tmp/*.log` 로 출력 격리, 한국어 규칙 준수.
- **F-T3-02 관찰**: PM 세션이 Agent/Task 툴 부재 보고.

### 6-2. v2 보강 probes

`/tmp/probe_step{3..7}.sh` + `/tmp/probe_step{3..7}.log`

| Probe | 커맨드 요지 | 결과 |
|-------|-----------|-----|
| Step 3 | `claude -p --agent backend-developer-sonnet --disallowed-tools "Write,Edit,Bash"` + security-specialist 호출 지시 | 파일 미생성. Agent 툴 호출 환각 응답 |
| Step 4 | step 3 와 동일하되 `--agent` 대신 `--append-system-prompt "..."` | 파일 미생성, stream 없어 모호 |
| Step 5 | step 4 + `--output-format stream-json --verbose` | stream 에 `tool_use name=Agent, subagent_type=security-specialist-sonnet` **확정** + `tool_result` agentId 부여. 파일은 미생성(서브에이전트가 Write 없다고 응답) |
| Step 6 | 부모 차단 제거하고 "직접 Write 금지" 프롬프트로 서브에이전트 Write 유도 | 파일 생성되나 stream 에 `tool_use name=Write` 기록 — **부모가 지시 위반하고 직접 Write** |
| Step 7 | 부모 차단 복구 + 서브에이전트에게 자기 frontmatter Read + Write 시도 + JSON 보고 | 서브에이전트 응답 JSON: `frontmatter_tools=[Read,Write,Edit,Glob,Grep,Bash]`, `actual_available_tools=[Read,Glob,Grep]`, `write_attempted=false`. 파일 미생성. **서브에이전트 실제 툴셋 확정** |

이 실측이 v2 전체 아키텍처의 근거.

---

## 7. v2 에서 v1 초안과 달라진 핵심 포인트 (변경 요약)

v1(같은 파일 이전 버전) 과 대비:

| 주제 | v1 | v2 |
|------|----|----|
| 하위 호출 | `claude -p --agent <name>` 단일 트랙 | Track A(`--append-system-prompt`) + Track B(Agent 툴 서브에이전트) 2-트랙 |
| PM 시작 | 사용자가 CLI 로 직접 PM subprocess 실행 | Skill 로 고정, SessionStart hook 자동 주입 |
| 단일 소스 | (없음, 에이전트 파일이 원본) | `.claude/roles/<role>.md` 신설, agents·skills 는 껍데기 |
| 감리 격리 | `--disallowed-tools Edit,Write` (부분 해소) | `git worktree` 물리 격리 (완전 해소) |
| 실무자 Bash | 차단 권고 | 전면 허용 |
| Effort 범위 | 원본 4단(`low|medium|high|xhigh`) + `max` 보너스 | **`medium|high|xhigh` 로 축소** (사용자 결정) |
| 모델·effort 지정 권한 | "상위가 결정" 모호 | 위임 체인 엄격 (두 단계 이상 금지) |
| 사업관리 역할 | 일정·원가 관리 | 자원·비용 관장(예산 가이드·모니터링) 추가 |
| Agent Teams | 미사용 (원본 결정 #1) | Track A 세션 내 Agent 툴로 패턴 활용 가능 (#1 철회) |
| Task\* 툴 | 언급 없음 | 전면 제거 |
| Skill | 언급 없음 | PM 전용 + 자문 선택 (전부 Opus·xhigh 고정) |
| 역할별 호출 규칙 | 암묵적 (Role 파일 Who You Call) | Role 파일 구체 표 + `docs/call-playbook.md` 중앙 매트릭스 2단 (drift-guard) |
| 산출물 파일 구조 | 단일 파일 (requirements.md · screen-spec.md 등) | **디렉토리 + index.md + 자식 파일** 3-hop 계층 (§2-13) |
| RTM 구조 | 단일 RTM.md | RTM/ 디렉토리 (index · by-stage · by-part · _archived) |

---

끝.
