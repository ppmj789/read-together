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
[최상위 실행 세션] = 사용자 Claude Code 세션
       │ SessionStart hook → PM Skill 자동 로딩
       │ (현 세션 = PM 페르소나)
       ▼
[수행 조직]
  PM (project-manager, Skill 로만 존재)
  ├─ 직속 (Track A 로 호출)
  │   ├─ business-manager     (사업관리 — 자원·비용 관장, §2-6)
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
  audit-team   (별도 git worktree 에서 실행, §2-5)
```

- **역할 수**: 수행 조직 18 + 감리 1 = 19개 역할. 대규모 모드 활성화 시 `part-leader` 역할이 활성화된다.
- **파일 수**: `.claude/roles/*.md` 20개(단일 소스) + `.claude/agents/*.md` 45개(Track B 껍데기, PM 제외) + `.claude/skills/*/SKILL.md` 최소 1개(PM) ~ 최대 11개(자문 Skill 선택). 자세한 규칙은 §2-3.
- 사용자는 `project-manager` 와만 직접 대화한다 (사용자 세션 자체가 PM).

### 1-2. 기술 기반

하위 호출은 두 트랙으로 구성되며, PM 은 Skill 로만 존재한다.

**Track A — 주 산출물 저작 호출 (독립 최상위 세션)**
- 상위 에이전트가 `Bash` 툴로 다음 커맨드를 subprocess 실행:

    claude -p \
      --dangerously-skip-permissions \
      [--add-dir <worktree-path>] \
      --append-system-prompt "$(cat .claude/roles/<role>.md)" \
      --model <opus|sonnet|haiku> --effort <medium|high|xhigh> \
      "<작업 지시 prompt>"

    # CLI 인자 순서는 load-bearing. `--add-dir` 은 반드시 `--append-system-prompt`
    # 앞에 두어야 한다. 역순이면 positional prompt 가 `--add-dir` 값으로 흡수되어
    # 세션이 `Error: Input must be provided` 로 실패 (Phase 7 Task 6 finding).

- 각 호출은 **독립된 새 최상위 Claude Code 세션**. `Agent` 툴을 포함한 전체 내장 툴 보유.
- subprocess 내부에서 다시 `claude -p --append-system-prompt ...` 호출 가능 → 다단 중첩 허용. 단 **체인 깊이는 4 단 권고** (PM → 총괄 → 파트리더 → 개발자). 5 단 이상 필요 시 4 단에서 `condensed-brief.md` 저작 후 하위에 명시 참조 (신규 이슈 N20 — 95% cache-hit 이어도 최하위 agent 는 압축된 brief 만 보아 세부 지시 누락 위험).
- 주 산출물을 저작하거나 하위를 호출해야 하는 모든 역할에 사용.
- 근거: `--agent` 플래그는 세션을 서브에이전트 모드로 전환시켜 Agent 툴을 박탈. `--append-system-prompt` 는 최상위 모드 유지 (Phase 7 실증 step 5·6·7 확정).

**Track B — 자문·리뷰 응답 호출 (같은 세션 내 서브에이전트)**
- 현 세션의 `Agent` 툴로 `subagent_type=<agent-name>` 을 지정하여 dispatch.
- 서브에이전트의 실제 툴셋은 **`Read, Glob, Grep`** 로 Claude Code 런타임이 고정 (frontmatter 의 tools 리스트는 선언일 뿐).
- 자문·리뷰·분석 응답에만 사용. 쓰기·코드 편집·실행이 필요한 작업은 불가 (이 경우 Track A).
- `.claude/agents/<name>.md` 껍데기가 Agent 툴 `subagent_type` 해석에 쓰임.

**PM 은 Skill 로만 존재**
- `.claude/skills/project-manager/SKILL.md` 이 유일한 PM 파일. `.claude/agents/project-manager.md` 는 **존재하지 않음**.
- 사용자 Claude Code 세션 시작 시 `.claude/settings.json` 의 `hooks.SessionStart` 가 PM Skill 을 자동 invoke → 현 세션이 PM 페르소나.
- 사용자가 PM 과 직접 대화. 사용자 세션 자체가 PM.

**감리**
- 별도 git worktree 에서 Track A 로 실행 (§2-5). 물리적 격리.

### 1-3. 파일 기반 협업

에이전트는 독립 컨텍스트를 갖기 때문에 **산출물 파일**을 유일한 공유 정보원으로 사용한다. 모든 산출물은 Markdown 이며 프런트매터에 식별자(ID), 의존성(`depends-on`), 리뷰 링크(`reviewed-by`)를 기록한다.

---

## 2. 에이전트 파일 규격

### 2-1. 표준 포맷 (3 파일 유형)

파일은 **단일 소스 Role + Track B 용 Agent 껍데기 + Skill 껍데기** 3 계층으로 나뉜다.

#### 2-1-1. `.claude/roles/<role>.md` — 단일 소스 페르소나

```markdown
---
name: <kebab-case-role-name>              # 모델 접미사 없음 (예: backend-developer)
description: |
  <2-3줄 역할 요약>
---

# Role: <한국어 역할명>

## Mission
...

## Responsibilities
...

## How You Invoke Sub-executions (Track A)
(해당 역할이 Track A 호출 주체일 때만 기재. 아래 표 양식으로 구체 규칙 명시.
 규칙은 §2-7 호출 플레이북과 정합. drift-guard 검증 대상.)

| 시점 / 트리거 | 호출 대상 | 목적 | 전달 컨텍스트 |
|-------------|---------|-----|------------|
| (단계 진입·이벤트·조건) | (role-name) | (산출물 또는 의사결정) | (파일·변수·선행 산출물) |

## How You Consult Advisors (Track B)
(모든 Track A 호출 주체 + 실무자. 자문 상황을 아래 표로.)

| 상황 | 자문 대상 | 목적 |
|------|---------|-----|
| (기술·비즈 상황) | (advisor role) | (의사결정 근거 · 리뷰) |

## How You Report
(상위/사용자 보고 프로토콜)

## Artifacts You Own
(본인이 생성/수정 책임을 지는 산출물 경로. §3-1 계층 구조 기반)

## Rules
(역할별 위반 금지 규칙)

## Escalation Protocol
(실무자에 필수 주입. 형식은 §7-3)

## Language
한국어 응답 규칙
```

#### 2-1-2. `.claude/agents/<name>.md` — Track B 서브에이전트 껍데기

```markdown
---
name: <name>                              # <role-name> 또는 <role-name>-<opus|sonnet|haiku>
description: |
  <Agent 툴 노출용 자연어 2-3줄. 언제 이 서브에이전트를 자문으로 부르면 좋은지.>
tools: [Read, Glob, Grep]                 # 선언적. 실 런타임은 이와 무관 (런타임이 3툴로 고정).
model: opus | sonnet | haiku
effort: medium | high | xhigh
---

# Role: <한국어 역할명> (자문 서브에이전트 껍데기)

이 파일은 Agent 툴의 `subagent_type` 해석용 껍데기입니다.
호출되면 먼저 `Read` 툴로 다음 파일을 읽고 그 역할의 관점으로 질의에 답하세요:

  .claude/roles/<role-name>.md

자문 응답 규칙:
- 읽기 전용 분석·평가·조언만 수행 (Write/Edit/Bash 미보유).
- 쓰기가 필요한 판단은 응답에 명시하고 상위에게 Track A 재호출을 권고.
- 응답은 한국어로 간결하게.
```

#### 2-1-3. `.claude/skills/<skill-name>/SKILL.md` — Skill 껍데기

```markdown
---
name: <skill-name>
description: |
  <언제 이 스킬을 invoke 해야 하는지 자연어.
   예: "사용자와 프로젝트 관리 대화를 시작할 때, SI 프로젝트 PM 페르소나가 필요한 경우">
model: opus
effort: xhigh
---

# Skill: <한국어 Skill 명>

이 스킬이 invoke 되면 먼저 `Read` 툴로 다음 파일을 읽고 그 역할의 페르소나로 현 세션을 수행하세요:

  .claude/roles/<role-name>.md

그 역할의 Mission, Responsibilities, Rules, Escalation Protocol 을 자기 행동 규범으로 삼으세요.
```

**요점**:
- 단일 소스는 `.claude/roles/`. 나머지는 껍데기.
- PM 은 `.claude/skills/project-manager/SKILL.md` 만 존재 (Agent 껍데기 없음).
- Skill 은 모두 `model: opus`, `effort: xhigh` 로 frontmatter 고정.

### 2-2. 툴 권한 정책

호출 경로별로 실 툴셋이 다르다.

| 호출 경로 | 세션 특성 | 실제 툴셋 | 비고 |
|----------|----------|---------|------|
| **Track A** (`claude -p --append-system-prompt`) | 새 최상위 세션 | `Read, Write, Edit, Glob, Grep, Bash, Agent` 등 전체 | 주 산출물 저작·하위 호출·자문 dispatch 자유 |
| **Track B** (Agent 툴 서브에이전트) | 현 세션의 하위 | `Read, Glob, Grep` (런타임 고정) | 쓰기 불가 — 자문·분석 전용. frontmatter 의 tools 는 선언일 뿐 |
| **PM Skill** (Skill invoke) | 현 세션 페르소나 확장 | 세션 전체 툴 계승 | Opus · xhigh 고정 |
| **사용자 세션** | 최상위 interactive | 전체 | SessionStart hook 으로 PM Skill 자동 로드 |
| **감리 (audit-team)** | 별도 git worktree 에서 Track A | 전체 | **worktree 격리로 메인 트리 무영향** — 경로 화이트리스트·hook 불필요. 감리 프롬프트는 "코드·산출물 직접 수정 금지, 지적만" 유지 (§2-5) |

`Agent` · `TaskCreate/Update/List/Get` 툴은 **모든 frontmatter 에서 제거**. Track A 세션이 Agent 툴을 런타임에 보유하므로 선언 불필요. Task* 는 Track A/B 구조에서 활용 불가.

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

**파일명 규약**: Track B 껍데기(`.claude/agents/<role-name>-<model>.md`) 는 3버전 모두 존재.
- 예: `.claude/agents/backend-developer-opus.md`, `-sonnet.md`, `-haiku.md`

Track A 호출은 변형 접미사와 무관하게 **단일 소스** `.claude/roles/<role-name>.md` 를 `--append-system-prompt` 로 주입하며, `--model` 플래그로 런타임 모델을 지정한다. Track B 호출은 `subagent_type=<role-name>-<model>` 로 껍데기를 직접 지정.

`.claude/roles/<role>.md` 는 **단일 소스**. Track A·B 어느 쪽에서 호출되든 동일 페르소나 본문이 사용됨. 유지보수 단일화를 위해 `scripts/derive_dynamic_agents.py` 로 roles 본문을 읽어 agents 껍데기 39개를 자동 생성한다.

#### 난이도 판단 가이드 (상위 에이전트 프롬프트에 삽입)

| 난이도 | 특징 | 모델 |
|--------|------|------|
| **High** | 새로운 아키텍처·프레임워크, 보안 중대 사안, 성능 최적화, 복합 도메인 설계, 요구사항 간 충돌 해소 필요 | Opus |
| **Medium** | 표준 비즈니스 로직, 통상적 화면/API, 정규화된 DB, 일반 테스트 케이스 | Sonnet |
| **Low** | 단순 CRUD, 반복 패턴, 목록/상세 화면, 간단한 배치, 정형 양식 문서화 | Haiku |

#### 위임 체인 (Delegation Chain)

모델·effort 선택 권한은 **자기 직속 하위에 대해서만** 행사한다. 두 단계 이상 건너뛴 지정은 금지 (인간 조직 위임 원칙).

| 결정자 | 결정 대상 (소규모) | 결정 대상 (대규모) |
|-------|------------------|-----------------|
| PM | 응용총괄, 인프라총괄, 사업관리, QA, tester | (동일) |
| 응용총괄 | AA, SWA, 데이터모델러, 개발자·디자이너·퍼블리셔 | 파트리더(들) |
| 인프라총괄 | 기술아키텍트, DBA, 보안전문가, 인프라엔지니어 | (동일) |
| 파트리더 | — | 자기 파트 소속 개발자·디자이너·퍼블리셔 |
| 실무자 | — (결정 권한 없음) | (동일) |

금지 사례는 §2-7 호출 플레이북 참조.

#### 자문 호출 시 정책 승계

상위가 Track A 로 하위를 호출할 때 프롬프트에 **"자문 정책 표"** 를 포함한다. 하위가 Track B 자문 시 이 표의 `subagent_type` · `model` 을 그대로 사용 (임의 승급 불가). Skill 경로로 자문하는 경우 Skill frontmatter 가 `model: opus, effort: xhigh` 로 고정되어 있으므로 어떤 세션에서 invoke 해도 Opus·xhigh 로 동작.

#### Skill 모델·effort 고정

모든 Skill(PM Skill + 자문 Skill) 의 frontmatter 는 `model: opus, effort: xhigh` 로 **고정**. 이유: 자문가는 자문받는 자보다 격이 높아야 한다는 원칙.

#### 호출 시 기록

모든 Track A·B 호출은 `projects/<프로젝트명>/agent-call-log.md` 에 append (시각, 호출자, 대상, 트랙, 모델, effort, 사유 요약). 추후 감사·비용 분석 자료.

### 2-4. Reasoning Effort 정책

**유효 범위**: `medium | high | xhigh` 3단계. `low`·`max` 모두 사용 금지.

**기본값**: 모든 에이전트의 기본 effort 는 `xhigh`. 근거: SI 프로젝트 산출물은 품질·정확성 우선이며, 토큰 비용보다 재작업 비용이 훨씬 크다.

#### 역할별 effort 규약

| 역할군 | 기본 effort | 조정 허용 | 비고 |
|--------|-------------|-----------|------|
| PM Skill, 고정 Opus 총괄 | `xhigh` | ❌ | 항상 최대 사고로 조율·판단 |
| 사업관리, QA, tester, 감리 (고정 Sonnet) | `xhigh` | ❌ | 정형 업무라도 오탐지 방지 |
| 동적 모델 (13 역할 × 3 버전) | `xhigh` | ✅ (medium~xhigh 내에서) | 호출자(직속 상위)가 작업 난이도에 따라 조정 |
| 모든 Skill (PM · 자문) | `xhigh` | ❌ | frontmatter 고정 |

#### 조정 규칙

호출자는 저·중난이도 작업에 한해 `high` 또는 `medium` 으로 낮출 수 있다 (하한 `medium`). 단 다음은 **언제나 `xhigh`**:
- 보안·인증·결제 관련 코드 (security-specialist, 관련 개발자)
- 데이터 모델링 (data-modeler)
- 아키텍처·인터페이스 설계 (AA, SWA, TA)
- 시정조치·재감리 대상 산출물

조정 시 `agent-call-log.md` 에 effort·사유 명시 (예: `PRG-UTIL-03 CRUD — medium — web-developer-haiku, 반복 패턴 사유`).

#### frontmatter 기본값

Role 파일 자체에는 effort 기본값 없음 (호출자가 CLI 플래그로 지정). Track B 껍데기(.claude/agents/) 와 Skill 파일(.claude/skills/) 에는 frontmatter 에 effort 명시.

### 2-5. 감리 독립성 + worktree 격리

감리팀은 **별도 git worktree 에서 Track A** 로 실행한다. 메인 트리와 물리적으로 분리된 작업 공간을 갖기 때문에 경로 화이트리스트·hook 강제 없이도 감리가 메인 산출물을 직접 수정할 수 없다.

#### 호출 방식

PM 이 `scripts/run_audit.sh <project> <cycle-id> <prompt-file>` 헬퍼로 실행하거나(의사결정 #15, 본 Amendment), 사용자가 직접 실행:

```bash
git worktree add <audit-wt-path> <branch>
cd <audit-wt-path>
# CLI 인자 순서 주의: --add-dir 는 반드시 --append-system-prompt 앞에 (Phase 7 Task 6 finding)
claude -p \
  --dangerously-skip-permissions \
  --add-dir <audit-wt-path>/projects/<project> \
  --append-system-prompt "$(cat .claude/roles/audit-team.md)" \
  --model sonnet --effort xhigh \
  "<감리 범위 및 지시>"
```

`scripts/run_audit.sh` 를 쓰면 worktree 생성, 프로젝트 복사, CLI 순서, 3-layer 경로 방어, 결과 복사가 자동화된다 (Phase 7 Task 6·10 확정).

감리 종료 후 `99_audit/` 변경분만 메인으로 머지하거나 참조.

#### 감리 독립성 프롬프트 (`.claude/roles/audit-team.md` 에 필수 주입)

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

### 2-6. 자원·비용 관장 (사업관리 역할)

사업관리(business-manager) 는 모델·effort 선택의 **예산 프레임** 을 설정·감시한다. 실제 모델 선택은 §2-3 위임 체인의 각 상위가 수행한다.

- **예산 가이드 수립**: 프로젝트 계획 단계에서 PM 이 사업관리(Track B) 에 자문하여 `00_kickoff/project-plan/budget.md` 를 작성. 포함 내용:
  - 전체 예산 규모(토큰/$ 추정)
  - 계층별·단계별 기본 모델·effort 권장 조합
  - "고난이도·최상위 모델 사용" 권고 작업 유형
- **단계별 자문 필수 경유**: 각 단계 진입 시 PM 이 사업관리 자문을 **반드시 경유**하여 해당 단계 모델·effort 정책을 확정한다. 단계 게이트 체크리스트(§6-2) 에 1 포인트로 포함.
- **실행 중 자문**: 응용총괄·인프라총괄·파트리더·실무자가 필요 시 Track B 로 사업관리 자문. 예산 초과 우려, 모델 승급 요청, 일정 이슈 등.
- **모니터링**: `agent-call-log.md` 누적을 단계 종료 시 집계하여 PM 에 보고. 자동 차단 없음.
- **경계**: 사업관리는 **직접 하위를 호출하지 않음**. 예산 프레임·경보만 담당.

### 2-7. 역할 호출 플레이북

각 역할이 "언제 누구를 호출해야 하는지" 는 2단 구조로 관리한다:

1. **Role 파일(`.claude/roles/<role>.md`)** 의 `## How You Invoke Sub-executions` / `## How You Consult Advisors` 섹션: 자기 책임 범위의 구체 규칙을 표로 기재 (§2-1-1 포맷).
2. **`docs/call-playbook.md`**: 중앙 매트릭스 정본. 단계별 호출 매트릭스, 상황 기반 자문 매트릭스, 에스컬레이션 경로, 금지된 호출 사례를 포함.

`scripts/validate_agent.py` 의 drift-guard 가 Role 파일의 호출 규칙 표와 call-playbook.md 매트릭스 간 정합성을 검증한다 (역할별 entry 누락·잉여 탐지, 금지 사례 위반 탐지).

#### 금지된 호출 (위임 체인 위반)

| 금지 사례 | 사유 |
|---------|------|
| PM 이 개발자·파트리더를 직접 Track A 호출 (총괄 건너뜀) | 두 단계 이상 건너뛴 지정 — §2-3 위반 |
| 응용총괄이 개발자의 모델·effort 를 파트리더 경유 없이 지정 (대규모 시) | 동일 |
| 실무자가 다른 실무자를 Track A 호출 | 실무자는 Track A 호출 권한 없음 (자문 Track B 만) |
| 사업관리가 직접 하위 에이전트 호출 | 예산 프레임·모니터링만 담당 (§2-6) |
| 감리팀이 코드·산출물 직접 수정 | 감리는 읽기 전용 지적만 (§2-5) |
| PM 을 `claude -p` subprocess 로 호출 | PM 은 Skill 전용 |
| 자문 Skill 을 Opus·xhigh 외 값으로 호출 | Skill frontmatter 고정 |

---

## 3. 공정 흐름 (V-Model 폭포수)

### 3-1. 산출물 디렉토리 구조 (계층화)

모든 산출물은 **디렉토리 + `index.md` + 자식 파일** 3계층 이상으로 분해한다. 대규모 프로젝트에서 단일 파일은 수십~수백 KB 로 폭증하여 후속 에이전트의 context 를 극심히 소모하기 때문. 에이전트는 "인덱스 → 인덱스 → 대상" **3-hop 이하** 로 필요한 부분만 로드한다.

#### 원칙

- **산출물은 디렉토리, 자식은 ID 기반 파일**: 원본 설계의 단일 `.md` 파일(`requirements.md`, `screen-spec.md`, `program-list.md` 등) 을 **동명 디렉토리** 로 전환.
- **각 디렉토리에 `index.md` 1개 필수** (소규모에서 자식 1–2개뿐이면 생략 허용).
- **3-hop 상한**: `<단계>/index.md` → `<단계>/<영역>/index.md` → `<단계>/<영역>/<그룹>/<ID>.md`.
- **단일 파일 유지 예외**: `statement-of-work.md`, `rollback-history.md`, `escalations.md`, `project-state.md` — 작고 append-only 이거나 외부 입력.

#### 디렉토리 구조

```
projects/<프로젝트명>/
├─ 00_kickoff/
│  ├─ index.md
│  ├─ statement-of-work.md                 (과업지시서 — 사용자 제공, 단일 파일)
│  ├─ project-plan/
│  │  ├─ index.md
│  │  ├─ overview.md
│  │  ├─ scope.md
│  │  ├─ organization.md
│  │  ├─ schedule.md
│  │  ├─ budget.md                          (사업관리 작성 — 모델·effort 예산 가이드, §2-6)
│  │  └─ wbs/
│  │     ├─ index.md
│  │     └─ wbs-phase-<NN>-<name>.md
│  └─ rollback-history.md                   (append-only 로그, 단일 파일)
│
├─ 01_analysis/
│  ├─ index.md
│  ├─ requirements/
│  │  ├─ index.md                            (전체 RQ-ID 목록)
│  │  └─ RQ-<group>/
│  │     ├─ index.md
│  │     └─ RQ-<group>-<NN>-<slug>.md
│  ├─ as-is-analysis/ (index.md + 세분 파일)
│  ├─ to-be-workflow/ (index.md + WF-<name>.md)
│  ├─ uat-test-cases/ (index.md + UT-<group>/UT-<NN>.md)
│  ├─ integration-test-cases/ (index.md + IT-<group>/IT-<NN>.md)
│  └─ reviews/ (index.md + <artifact-id>-review-v<N>.md)
│
├─ 02_design/
│  ├─ index.md
│  ├─ architecture/ (index.md + overview.md + layers.md + components/index.md + CMP-*.md)
│  ├─ db/
│  │  ├─ index.md
│  │  ├─ logical/ (index.md + ENT-*.md)
│  │  └─ physical/ (index.md + TBL-*.md)
│  ├─ screens/ (index.md + SCN-<group>/index.md + SCN-<group>-<NN>-*.md)
│  ├─ interfaces/ (index.md + IF-<group>/IF-*.md)
│  ├─ programs/ (index.md + PRG-<group>/index.md + PRG-<group>-<NN>-*.md)
│  ├─ unit-test-cases/ (index.md + UT-UNIT-<group>/UT-UNIT-<NN>.md)
│  ├─ security-review/ (index.md + findings/FIND-*.md)
│  └─ reviews/
│
├─ 03_implementation/
│  ├─ index.md
│  ├─ unit-test-results/ (index.md + UT-RES-<group>/...)
│  └─ reviews/
│
├─ 04_test/
│  ├─ index.md
│  ├─ integration-test-results/ (index.md + IT-RES-*.md)
│  ├─ system-test-results/ (index.md + ST-RES-*.md)
│  ├─ uat-results/ (index.md + UAT-RES-*.md)
│  ├─ qa-report/ (index.md + <section>.md)
│  └─ reviews/
│
├─ 05_deployment/
│  ├─ index.md
│  ├─ deployment-plan/ (index.md + <section>.md)
│  ├─ operation-manual/ (index.md + <section>.md)
│  ├─ training-material/ (index.md + <section>.md)
│  └─ reviews/
│
├─ 99_audit/
│  ├─ 01_analysis-audit/ (대규모 시만)
│  ├─ 02_design-audit/ (필수)
│  └─ 03_closing-audit/ (필수)
│      각 감리 디렉토리:
│      ├─ index.md
│      ├─ audit-plan.md
│      ├─ audit-report/ (index.md + FIND-*.md)
│      ├─ corrective-action-plan/ (index.md + ACT-*.md)
│      ├─ corrective-action-result/ (index.md + RES-*.md)
│      └─ re-audit-report-v<N>/ (index.md + FIND-*.md)
│
├─ change-requests/
│  ├─ index.md
│  └─ CR-<seq>/
│     ├─ request.md
│     ├─ impact-analysis.md
│     └─ decision.md
│
├─ escalations.md                            (append-only 로그, 단일 파일)
├─ project-state.md                           (상태 표, 단일 파일)
├─ agent-call-log.md                          (모든 Track A·B 호출 기록, §2-3)
└─ RTM/                                       (§5 참조 — 계층 구조)

src/
├─ backend/
├─ batch/
├─ web/
└─ ...

infra/
└─ ...
```

각 단계 내에서 rollback 발생 시 해당 단계 산출물은 그 단계 디렉토리 내 `_archived/<YYYYMMDD>-v<N>/` 로 이동한다 (index.md 포함 디렉토리 통째로 보존).

#### `index.md` 표준 포맷

```markdown
---
artifact-id: <parent-id>                    # 예: SCREENS, SCN-AUTH, PROGRAMS
type: index
stage: <00_kickoff | 01_analysis | ...>
area: <screens | programs | ...>
child-count: <N>
version: <v1 | v2 ...>
---

# <단계> / <영역> [/ <그룹>] — <한국어 제목>

## 개요
(2–3줄)

## 하위 항목
| ID | 제목 | 파일 | 담당 | 상태 | 요약 |
|----|------|------|-----|-----|------|
| ... | ... | [./...](...) | ... | ... | ... |

## 상위 인덱스
- [../index.md](../index.md)

## 의존성 요약 (선택)
| 자식 ID | depends-on | referenced-by |
|--------|-----------|--------------|
```

#### 자식 파일 frontmatter 규약

```markdown
---
id: <ID>                                    # 예: SCN-AUTH-01, PRG-AUTH-01
title: <한국어 제목>
stage: <단계>
area: <영역>
group: <그룹, 선택>
owner: <role-name>
depends-on: [<ID>, ...]
referenced-by: [<ID>, ...]                  # 양방향 drift-guard
reviewed-by: [<review file 경로>, ...]
status: draft | in-review | approved | rollback
---
```

#### 에이전트 로딩 전략

예: web-developer-sonnet(auth 파트) 이 `PRG-AUTH-01` 구현 작업 시
1. `02_design/programs/PRG-AUTH/index.md` Read (~1KB) — 파트 내 프로그램 목록
2. `02_design/programs/PRG-AUTH/PRG-AUTH-01-login.md` Read (~3KB) — 본체
3. (필요 시) `depends-on` 의 선행 산출물 1–2개 Read (~5KB)

단일 파일 대비 **80–94% 토큰 절감**.

관련 스크립트: `scripts/scaffold_artifact.py` (디렉토리·index 생성), `scripts/validate_artifact_hierarchy.py` (drift-guard).

### 3-2. 단계별 주도·산출물 (요약)

아래 표의 산출물 이름은 요약 표기이며, 실제 파일 구조는 §3-1 계층 규약(디렉토리 + `index.md` + 자식 파일) 을 따른다.

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
3. `RTM/` 디렉토리 전체 → `RTM/_archived/<YYYYMMDD>-v<seq>/` 로 스냅샷 보존 (index · by-stage · by-part 파일 통째).
4. rollback 대상 구간 이후의 감리이력·결과 컬럼은 공란 초기화 (요구사항 ID는 보존).
5. `00_kickoff/rollback-history.md` 에 이벤트 로그:
   | Date | Trigger | Rolled-back to | Archived versions | Reason |
6. 단계 N부터 재수행 시작.

---

## 5. 요구사항추적매트릭스 (RTM) — 계층화

### 5-1. 형식

RTM 은 단일 파일이 아닌 **`projects/<프로젝트명>/RTM/` 디렉토리** 로 관리한다 (대규모 시 RTM 이 수천 행에 이를 수 있어 단일 파일은 context 소모 극심).

```
projects/<프로젝트명>/RTM/
├─ index.md                         # RQ-ID 마스터 목록 · 단계별 진행 상태 요약
├─ by-stage/
│  ├─ analysis.md                   # 01_analysis 에서 작성된 RQ 추적
│  ├─ design.md                     # DESIGN-ID, PROG-ID, UT-ID
│  ├─ implementation.md             # 소스 경로
│  ├─ test.md                       # IT-ID, UAT-ID, 결과
│  └─ deployment.md
├─ by-part/                          # 대규모 시만 생성
│  ├─ index.md
│  └─ <part-name>.md
└─ _archived/<YYYYMMDD>-v<N>/       # rollback 스냅샷 (디렉토리 통째 보존)
   ├─ index.md
   └─ <snapshot files>.md
```

`RTM/index.md` 가 **최상위 엔트리 포인트**. 에이전트가 RQ-ID 를 찾을 때 가장 먼저 Read.

#### index.md 형식

| REQ-ID | 요구사항명 | 유형 | 현 단계 | 연결 파일(경로들) | 상태 | 감리이력 요약 |

단계별 세부(설계문서 경로·소스 경로·테스트 결과 등) 는 `by-stage/<stage>.md` 에 기록.

단계별 채워지는 컬럼:
- 분석: REQ-ID, 요구사항명, 유형, 출처, IT-ID, UAT-ID
- 설계: DESIGN-ID, 설계문서 경로, PROG-ID, UT-ID
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

- 현 RTM 디렉토리 전체 → `RTM/_archived/<YYYYMMDD>-v<N>/` 로 스냅샷 보존 (index.md 포함 파일들 통째).
- 새 RTM 에서 되돌아간 구간 이후 컬럼 공란화, 요구사항 ID 유지.
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

`templates/stage-gates.md` 에 단계별 완료 조건 정의.

예시 (분석):
```
Required artifacts (각 디렉토리 + index.md + 자식 파일, §3-1 준수):
  - 01_analysis/requirements/index.md (RTM 의 RQ-xxx 전체 포함, 자식 파일들 정합)
  - 01_analysis/as-is-analysis/index.md + 자식
  - 01_analysis/to-be-workflow/index.md + 자식
  - 01_analysis/uat-test-cases/index.md + 자식
  - 01_analysis/integration-test-cases/index.md + 자식
  - 각 산출물마다 reviews/ 내 review-v<N>.md 존재
Stage-entry advisory gate (§2-6):
  - PM 이 해당 단계 진입 시점에 business-manager(Track B) 자문 경유 완료
    → project-plan/budget.md 의 모델·effort 정책 섹션이 해당 단계에 대해 갱신됨
Audit gate (if scale == large):
  - 99_audit/01_analysis-audit/audit-report/index.md 의 최종 결과 = PASS
    (또는 시정조치→재감리 통과)
Approval gate:
  - project-state.md Approval Log 에 해당 단계 엔트리 존재
Call-log gate:
  - agent-call-log.md 에 해당 단계 Track A·B 호출 이력 기록됨
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

**오케스트레이션**: 주관자가 Track B(Agent 툴) 로 참여자들을 병렬 자문 dispatch → 의견 취합 → 리뷰 회의록 생성. Track B 서브에이전트는 읽기 전용이므로 회의록 파일 작성은 주관자 본인이 Track A 세션에서 수행.

**리뷰 회의록 포맷**: `<단계>/reviews/<산출물명>-review-v<N>.md` — 프런트매터(participants, date, target, related IDs) + Findings + Decisions + Follow-up Actions.

**검증**: 리뷰 회의록의 `participants` 수가 2 미만이면 시스템이 경고하고 해당 산출물은 미완료로 본다.

### 7-2. 병렬 작업

**원칙**: 단계 내 의존성 없는 산출물은 반드시 병렬.

#### Track A 병렬 (다수 실행 주체 동시 호출)

상위 에이전트는 Bash 백그라운드 패턴으로 복수 자식 Track A 호출:

```bash
# CLI 인자 순서: --add-dir 가 있는 경우 반드시 --append-system-prompt 앞에.
( claude -p \
    --dangerously-skip-permissions \
    --append-system-prompt "$(cat .claude/roles/backend-developer.md)" \
    --model sonnet --effort high \
    "<지시1>" > /tmp/<unique1>.log 2>&1 & \
  claude -p \
    --dangerously-skip-permissions \
    --append-system-prompt "$(cat .claude/roles/web-developer.md)" \
    --model sonnet --effort high \
    "<지시2>" > /tmp/<unique2>.log 2>&1 & \
  wait )
```

- 각 자식 출력은 고유 로그 파일로 분리.
- 인용 충돌이 깊어지면 `/tmp/<unique>.sh` 스크립트로 분리 실행.
- 완료 후 로그를 Read 로 수거 → 상위가 통합.

#### Track B 병렬 (자문 다중 dispatch)

상위는 한 응답 안에서 여러 Agent 툴 호출을 동시 제출 (Claude Code 네이티브 기능).
예: backend-developer 가 security·DBA·SWA 세 자문을 한 턴에 병렬 dispatch.

#### Agent Teams 패턴

파트리더 또는 응용총괄 세션(Track A 최상위 모드) 에서 개발자들을 Track A 로 병렬 호출하면서 Agent 툴로 자문가를 동시 dispatch → 수평 협업 구성. 산출물 공동 저작은 §1-3 의 파일 기반 협업(공유 작업 디렉토리).

#### 쓰기 충돌 방지

- 각 산출물 frontmatter `depends-on:` 으로 DAG 구성.
- 동일 파일을 여러 Track A 자식이 동시 수정 금지 (프롬프트 수준 원칙). 향후 `.locks/` 디렉토리 또는 호출자의 사전 DAG 분석으로 강화(§10).
- 리뷰(Track B 읽기) 는 병렬 안전.

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

- Track A (`claude -p --append-system-prompt`) 호출 실패 시 3회 재시도. 인용·셸 이슈 의심 시 두 번째 시도에서 `/tmp/<unique>.sh` 스크립트 분리 실행.
- Track B (Agent 툴 서브에이전트) 호출 실패 시 3회 재시도.
- 지속 실패 시 §7-3 에스컬레이션 포맷으로 상위에 전달.

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

### Phase 0–6 (초기 스캐폴드)

1. **스켈레톤**: `.claude/roles/` · `.claude/agents/` · `.claude/skills/` 디렉토리, `templates/artifacts/` 및 `templates/stage-gates.md`.
2. **`.claude/roles/` 20개 단일 소스 페르소나 작성**: project-manager, application-director, infrastructure-director, business-manager, quality-assurance, tester, audit-team + 동적 13역할(AA, SWA, TA, data-modeler, part-leader, backend/batch/web-developer, web-publisher, designer, DBA, security-specialist, infrastructure-engineer).
3. **`.claude/agents/` 껍데기 45개 생성**: 고정 6개(PM 제외) + 동적 13역할 × 3버전 = 39. `scripts/derive_dynamic_agents.py` 를 "껍데기 생성" 모드로.
4. **`.claude/skills/project-manager/SKILL.md` 작성** (필수) + 자문 Skill 선택 (초기 생략 가능, Phase 7 실측 후 결정).
5. **산출물 템플릿**: `templates/artifacts/<artifact-type>/index.md.tmpl` + 자식 템플릿(§3-1 계층 구조).
6. **project-state.md / RTM/ 템플릿** + `agent-call-log.md` 템플릿.

### Phase 6.5 (v2 아키텍처 검증)

7. **SessionStart hook 설정**: `.claude/settings.json` 의 `hooks.SessionStart` 에 PM Skill 자동 invoke 추가. `docs/orchestrator-playbook.md` 에 사용자 UX 기재.
8. **`scripts/validate_agent.py` 스키마 업데이트**: `Agent`·`Task*` 관련 로직 제거, agents 껍데기 body lint, Skills Opus·xhigh 고정 검증.
9. **`docs/call-playbook.md` 신규 작성**: §2-7 에 요약된 호출 플레이북 정본 (단계별·상황별 매트릭스 · 에스컬레이션 · 금지 사례).
10. **`scripts/validate_agent.py` drift-guard 확장**: Role 파일 호출 규칙 표와 `docs/call-playbook.md` 간 정합 검증.
11. **`scripts/scaffold_artifact.py` 신설**: 산출물 디렉토리 + index.md + 초기 자식 틀 자동 생성.
12. **`scripts/validate_artifact_hierarchy.py` 신설**: index.md 자식 목록과 실제 파일 일치, depends-on/referenced-by 양방향 정합, 3-hop 상한 검증.
13. **`scripts/bootstrap_project.py` 업데이트**: 프로젝트 스캐폴드 시 §3-1 계층 구조로 생성. 규모별 분기 반영.
14. **실증 선행 2건**:
    - Skill invoke → `.claude/roles/<role>.md` Read → 페르소나 전환 동작 확인.
    - 동일 에이전트 반복 호출 시 Anthropic prompt cache 자연 히트 여부 간단 측정.
15. **Drift-guard + 전체 pytest 통과**.

### Phase 7 (Meta-Testing)

16. **Meta-Test 1 (샘플 프로젝트 E2E)** — 최소 규모로 전체 공정 완주. 난이도 판단 로직·호출 플레이북·계층 구조 정합성 검증.
17. **Meta-Test 2~6** — 에이전트 페르소나, 감리 독립성 negative, 2인 원칙, rollback 복원력, 병렬 쓰기 충돌.

단계별로 문서가 완결된 후 다음 구현 단계로 진행. 각 단계는 별도 커밋.

---

## 10. 미해결 사항 / 향후 결정

#### 유지 (원본에서 계속)
- 샘플 프로젝트의 도메인 선정 (Meta-Test 1 입력용).
- 병렬 호출 시 파일 잠금(locking) 구현 방법 — `.locks/` 디렉토리 도입 또는 호출자 사전 DAG 분석.
- `part-leader` 수 동적 결정 방식 (대규모 시 1명 vs 기능 도메인별 다수).
- **감리 세션 개시 UX** — 슬래시 커맨드 `/audit <stage>` vs 자연어 지시. 구현 시 결정.

#### 해소
- ~~감리팀 경로 화이트리스트 강제~~ → **해소**. §2-5 `git worktree` 격리로 해결.

#### 신규 (v2 반영 과정에서 도출)
- **프롬프트 캐시 자연 히트 검증**: 같은 에이전트를 5분 TTL 내 반복 Track A 호출 시 Anthropic API prompt cache 히트 여부 Phase 6.5 에서 실증.
- **서브에이전트(Track B) 확장 툴 주입**: 향후 Claude Code 업데이트로 서브에이전트 툴셋이 확장될 수 있음. 정기 점검 포인트.
- **Skill 의 실제 동작 실증**: Skill invoke 가 `.claude/roles/<role>.md` 를 Read 로 로드하여 페르소나 전환하는 실동작 검증. Phase 6.5 초반 1 스텝.
- **자문 Skill 도입 범위**: PM Skill 은 필수. 자문 Skill(보안·SWA·DBA 등) 은 Phase 7 비용·효과 측정 후 도입 결정.

(향후 구현·운영 중 발견되는 사항은 이 문서를 갱신하여 반영한다.)

---

## 의사결정 로그 (Design Decisions)

| # | 결정 | 사유 |
|---|------|------|
| 1 | ~~전통 서브에이전트 방식 (Claude Code Agent Teams 미사용)~~ **[철회, #20 로 대체]** | v2 Amendment — `claude -p --append-system-prompt` 로 최상위 모드 유지 시 Agent 툴·Agent Teams 패턴 활용 가능 |
| 2 | 조직도 3단 고정 + 대규모 시 part-leader 동적 | 사용자 지정 |
| 3 | 감리는 외부 네임스페이스 (audit/ → git worktree 격리) | 외주업체 독립성 반영 |
| 4 | V-Model 폭포수 + 단계별 사용자 승인 필수 | 사용자 지정 |
| 5 | 감리는 지적만, 판단·rollback은 PM 책임 | 사용자 지정 |
| 6 | Rollback 자동 실행 (사용자 개입 없이) | 사용자 지정 |
| 7 | 모든 산출물 Markdown | 사용자 지정 |
| 8 | 모든 작업에 2인 이상 리뷰 | 사용자 지정 |
| 9 | 단계 내 병렬 작업 필수 | 사용자 지정 |
| 10 | 단일 프로젝트 전제 | 사용자 지정 |
| 11 | 동적 모델 선택 (13역할 × Opus/Sonnet/Haiku) + PM·총괄·파트리더가 직속 하위에 대해서만 선택 | 사용자 지정 — 위임 체인 원칙 (#16) |
| 12 | 모든 에이전트 기본 effort = xhigh. 동적 모델은 저·중난이도 시 `high`/`medium` 으로 조정 허용(`low`·`max` 금지). 보안·아키·모델링 등은 예외 | 사용자 지정 — 재작업 비용 > 토큰 비용, 하한·상한 보수적 |
| 13 | 하위 호출 메커니즘을 **Claude Code CLI (`claude -p`) subprocess** 로 일원화 | Phase 7 F-T3-02 로 Claude Code 내부 서브에이전트 런타임의 Agent 툴 부재 확인 |
| 14 | PM 은 Skill 로만 존재 (subprocess 호출 금지). 사용자 Claude Code 세션 = PM 페르소나 (SessionStart hook 자동 로드) | `claude -p --agent project-manager` 경로는 서브에이전트 모드라 Agent 툴 없음 — Skill + SessionStart 가 자연스러움 |
| 15 | 감리 격리는 `git worktree` + Track A. 호출 경로는 `scripts/run_audit.sh <project> <cycle-id> <prompt-file>` 헬퍼 (PM 직접 호출 허용 — Amendment 2026-04-19). 헬퍼가 worktree 생성, 프로젝트 복사, `--add-dir` 먼저 · `--append-system-prompt` 뒤의 CLI 순서, 3-layer 산출물 경로 방어, 복귀 복사를 자동화. 감리 FIND 의 PM 분류는 Type A(사실 오류→RESOLVED) / B(리스크→ACCEPTED) / C(차기→DEFERRED) / D(관찰→OBSERVED) 4가지로 고정하며 `FIND-*.md` frontmatter `pm-classification:` 필드에 기록 (Phase 7 N8) | 프롬프트·hook 차단보다 물리 격리가 간결·확실. 원래 "사용자 수동 호출" 규정은 Phase 7 에서 PM-dispatched-with-helper 로 갱신 — PM Skill 세션과 인간 사용자가 같은 터미널을 공유하므로 헬퍼 경유는 격리를 훼손하지 않으면서 수동 셸 작업을 제거 |
| 16 | 모델·effort 지정 권한은 **자기 직속 하위에 한정**. 두 단계 이상 건너뛴 지정 금지 | 인간 조직 위임 원칙. 관리 가시성·책임 경계 확보 |
| 17 | 사업관리가 모델·effort **예산 프레임 수립·모니터링** 담당. 실제 선택은 위임 체인 내 상위 | 자원·비용의 전사적 관리자 역할 분리 |
| 18 | Effort 범위 `medium | high | xhigh` 로 제한 (`low`·`max` 금지) | 사용자 지정 — 품질 하한·비용 상한 모두 보수적 |
| 19 | 자문 Skill + PM Skill 모두 **Opus · xhigh 고정** | 자문가는 자문받는 자보다 격이 높아야 한다 |
| 20 | 모든 Track A 호출은 `claude -p --append-system-prompt "$(cat roles/<role>.md)"` 로 **최상위 모드 유지** + Agent 툴 보유 | Phase 7 probe step 5·6·7 로 확정. `--agent` 플래그는 서브에이전트 모드 전환시켜 Agent 툴 박탈 |
| 21 | Track B 서브에이전트 실제 툴셋 = **`Read, Glob, Grep`** (런타임 고정) | probe step 7 에서 서브에이전트가 자기 frontmatter 를 Read 한 결과 실제 툴과 불일치 확인. 쓰기가 필요한 호출은 Track A |
| 22 | `--disallowed-tools` 는 부모 세션에만 적용. 서브에이전트는 원래 읽기 전용이라 별도 제어 불필요 | probe step 7 결과 — 상속 가설은 "기본 읽기 전용" 으로 재해석 |
| 23 | `Task*` 툴 (TaskCreate/Update/List/Get) 전면 제거 | Agent 툴 제거와 동일 맥락. Track A·B 구조에서 활용 불가 |
| 24 | 실무자 Bash 전면 허용 | 테스트·빌드·린터 실행에 필요 |
| 25 | 역할별 호출 규칙은 **Role 파일(자기 책임 표) + `docs/call-playbook.md`(중앙 매트릭스)** 2단. drift-guard 로 일관성 강제 | 시점 기반·상황 기반 호출 판단 명시화. 에이전트 행동 재현성 + 휴먼 리뷰 용이 |
| 26 | 모든 산출물을 **디렉토리 + `index.md` + 자식 파일** 3-hop 계층으로 분해 (원본 §3-1·§5 단일 파일 방식 전환) | 대규모 프로젝트에서 단일 파일의 context 폭증 해소. 필요 영역만 로드하여 80–94% 토큰 절감 |
