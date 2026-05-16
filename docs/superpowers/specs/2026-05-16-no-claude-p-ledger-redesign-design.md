# Spec — claude -p 제거 + 계층 ledger 지식체계 재설계

- 작성일: 2026-05-16
- 작성자: Claude (브레인스토밍 세션 결과)
- 상태: 설계 사용자 승인 완료 → spec 사용자 검토 대기
- 원본 설계서: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`
- 대체 대상: `docs/superpowers/specs/2026-04-18-amendment-01-claude-p-invocation.md` (Amendment #1 의 Track A `claude -p` 결정을 전면 폐기)
- 근거 실증: 본 문서 §7 (2026-05-16 현 빌드 probe G/N/R, 파일시스템 검증)

---

## 0. 요약

### 0-1. 동인

Anthropic 이 기존 구독 서비스에서 `claude -p`(headless/print) 사용을
제외할 가능성이 제기되었다. 현 플랫폼의 Track A(주 산출물 저작·하위
위임)는 전적으로 `claude -p --append-system-prompt` subprocess 에
의존하므로, 해당 정책이 적용되면 플랫폼은 근간부터 무용지물이 된다.

사용자 결정:

1. 제약의 본질 = **구독 내 무과금 필수** (Claude Agent SDK·Anthropic API
   등 토큰 과금 경로 전면 배제).
2. **앞으로 `claude -p` 방식 호출을 절대 발생시키지 않는다.**
3. 기존 제약은 원점에서 재검토하고, 필요하면 모두 풀어서라도 목적을
   달성한다.

### 0-2. 핵심 구조 (probe 로 확정)

- **claude -p 전면 폐기.** "Track A" 개념 자체 소멸. 모든 호출은 현
  세션의 Agent 툴 단일 primitive.
- **저작 노드 = `subagent_type=general-purpose`** + 페르소나
  (`.claude/roles/<role>.md`) 프롬프트 주입 + 모델 티어(Agent 툴
  `model`). 현 빌드 실측상 general-purpose 는 Write/Edit/Bash 를
  보유하고 종료 후에도 산출물이 잔존한다(§7).
- **중첩 불가.** general-purpose 도 Agent 툴 미보유 → 자율 다단 조직
  불가. **PM 이 모든 hop 의 필수 버스.** 단 PM 은 본문이 아니라 ledger
  노드 경로 + `NEXT:` 지시만 셔틀하므로 hop 수가 많아도 PM 컨텍스트
  비용은 거의 0.
- **계층 ledger 지식체계.** 위임·의사소통이 Dewey 식 계층 ID
  (`A` → `A-1` → `A-1-1`) 의 **요청-응답 완결 단일 노드** 트리로
  구조화·축적된다. 노드는 실산출물(00~05 트리)·RTM-ID 를 링크하는
  **래퍼**이며, 본문을 복제하지 않는다. lazy navigation 으로 컨텍스트
  자동 경계.

### 0-3. 비범주

- cross-project 지식 집계·검색 (이번 범위 제외. 단 ID·스키마는 후일
  확장 가능하도록 설계).
- 페르소나 프롬프트-주입 충실도의 완전 보증 (롤아웃 전 2차 probe 로
  게이팅하되, 아키텍처 차단 요인 아님 — §6-3).
- 사람 팀원 혼합, 실시간 UI (원 설계서 비범주 승계).

---

## 1. 실행 모델

### 1-1. 폐기되는 것

| 폐기 대상 | 사유 |
|----------|------|
| Track A `claude -p --append-system-prompt` subprocess 전부 | 무과금·무claude-p 제약 |
| Track A CLI 인자 순서 규칙 (`--add-dir` ← `--append-system-prompt`) | claude -p 부재로 무의미 |
| `--add-dir` 범위 한정 규칙 | 동상 |
| 공유 파일 병렬쓰기 race / `.locks` 논의 | 저작자가 직렬화되어 구조적 소멸 |
| 4-계층 Track A depth guard, 5단 `condensed-brief` | 깊이가 항상 PM↔노드 1-hop |
| `scripts/meta6_parallel_write_repeat.sh` | 병렬 writer race 시나리오 소멸 |
| Track A / Track B 이원 구분 | 단일 Agent-툴 primitive 로 통합 |

### 1-2. 새 호출 계약 (단일 primitive)

PM 이 현 세션 Agent 툴로 노드를 dispatch 한다:

- `subagent_type` = `general-purpose`
- `model` = 난이도 기반 티어 (`opus` | `sonnet` | `haiku`)
- `prompt` = 다음을 합성:
  1. **페르소나 블록** — `.claude/roles/<role>.md` 전문 inline 주입
     (선두에 `[PERSONA — 이 역할로 행동하라]` 헤더 + 말미에
     self-attestation 지시).
  2. **노드 지시** — 처리할 ledger 노드 파일 경로 (REQUEST 를 그
     파일에서 읽으라).
  3. **출력 계약** — (a) 실산출물은 자신의 소유 경로에 직접 Write,
     (b) 같은 ledger 노드 파일의 `## RESPONSE` + `## CHILD INDEX` +
     `## NEXT` 를 직접 작성하고 frontmatter `status` 갱신, (c) PM 에
     반환하는 최종 메시지는 **노드 경로 + status + NEXT 요약만** (본문
     금지).

- `effort` 파라미터는 Agent 툴에 미노출 → **퇴화**. model 티어 +
  프롬프트 내 명시 지시로 근사한다 (명시된 손실).
- `--add-dir` / `--append-system-prompt` / CLI 순서 — 전부 해당 없음.

### 1-3. 역할에이전트(읽기전용)의 존속

`.claude/agents/<role>-<variant>.md` (46 shell, 툴셋 Read/Glob/Grep)는
**순수 자문(읽기전용 분석·리뷰)** 용도로 존속한다. 저작이 필요 없는
자문은 이 경로가 더 저렴하다. 저작·하위 위임이 필요한 노드는 §1-2
general-purpose 경로.

### 1-4. PM 의 역할

PM(Skill, 사용자 세션)은:

- 유일한 오케스트레이터·필수 버스 — 모든 hop dispatch.
- 공유 파일 단독 scribe — `project-state.md`, `RTM/**`,
  `escalations.md`, `agent-call-log.md`, `rollback-history.md`
  (§7-2 불변 승계).
- ledger 캠페인 관리자 — 노드 생성(REQUEST + frontmatter), 자식
  status 셀 갱신, NEXT 지시 실행, ESCALATION 처리.
- ledger 노드 본문은 보유하지 않는다 — 경로·NEXT·status 만.

---

## 2. ledger 모델

### 2-1. 위치·ID

- 트리 루트: `projects/<name>/ledger/`
- 루트 인덱스: `projects/<name>/ledger/index.md` (캠페인 목록)
- 노드 파일: `projects/<name>/ledger/<id>.md`
- ID 체계: 캠페인 루트 short-code(예: `D02A` = 02_design·application
  캠페인) → 자식 `-<n>` 누적. 예: `D02A` → `D02A-1`(파트리더1) →
  `D02A-1-1`(개발자1). 사람이 읽는 단축 표기는 문서상 `A`, `A-1`,
  `A-1-1` 로 예시한다.

### 2-2. 노드 파일 스키마 (요청-응답 완결 단일 문서)

```markdown
---
id: A-1
parent: A
role: part-leader            # 이 노드 RESPONSE 의 책임 역할
dispatched-by: PM
model: sonnet
stage: 02_design
status: pending              # pending → in-progress → responded → closed
artifacts: []                # 실산출물 프로젝트 상대 경로 링크
rtm: []                      # 연관 RQ/PRG/IF/UT ID
created: 2026-05-16T..Z
responded:                   # 응답 완료 시각
---

## REQUEST
<!-- PM 이 부모 NEXT 지시로부터 작성. 이후 불변(append-only 정정만) -->

## RESPONSE
<!-- 이 노드 담당 general-purpose 가 직접 작성. 실산출물은 링크만 -->

## CHILD INDEX
| child id | path | role | one-line purpose | status |
|----------|------|------|------------------|--------|
<!-- 담당 general-purpose 가 자식 선언 시 작성. status 셀은 이후 PM 갱신 -->

## NEXT
<!-- 기계가독 지시. PM 이 파싱·실행:
  - DISPATCH <child-id> role=<role> model=<m>
  - ESCALATE <사유>
  - CLOSE
-->
```

### 2-3. 소유·동시성 (race-free 증명)

| 영역 | 작성자 | 시점 |
|------|--------|------|
| frontmatter(생성) + REQUEST + 자식 status 셀 | PM | 생성 시 / 자식 폐쇄 시 |
| RESPONSE + CHILD INDEX(행) + NEXT + status 전이 | 노드 담당 general-purpose | dispatch 처리 시 |
| 실산출물(`02_design/...`·`src/...`) | 그 산출물 담당 노드 | 저작 시 |

- 한 분기(branch)는 PM 이 직렬 dispatch → 한 노드 파일에 두 작성자가
  접근하지만 **시간 분리**(PM 생성 → 자문가 응답 → PM status 셀 정정).
- 형제 노드(`A-1-1`/`A-1-2`/`A-1-3`)는 별개 파일 → 병렬 dispatch 해도
  동시쓰기 0.
- 공유 파일은 PM 단독(§1-4) → 구조적으로 race 불가.

### 2-4. 컨텍스트 경계 보장

- 노드 = 인덱스 + 요약 + 링크. 본문(실산출물)은 별 트리.
- 접근자는 인덱스 → 자식 노드를 **필요할 때만** open (lazy).
- PM 은 어떤 시점에도 노드 경로 + NEXT + status 만 보유.

---

## 3. 위계 흐름 (사용자 10단계 = ledger 매체)

1. PM → 총괄 dispatch (캠페인 루트 `A` 생성, REQUEST 채움)
2. 총괄: `A` RESPONSE 작성 + `## CHILD INDEX` 에 파트리더 노드 선언 +
   `## NEXT: DISPATCH A-1 ...` / `A-2 ...`. status=responded. PM 에
   경로+NEXT 만 반환.
3. PM: `A-1`·`A-2` 노드 생성(REQUEST = 총괄 NEXT) → 파트리더 dispatch
4. 파트리더(`A-1`): `A` 의 REQUEST/관련 산출물 읽기 → `A-1` RESPONSE +
   `A-1-1/2/3` 자식 선언 + `NEXT: DISPATCH A-1-1 ...`. responded.
5. PM: `A-1-1/2/3` 생성 → 개발자 dispatch (형제 병렬 가능)
6. 개발자(`A-1-1`): 실코드 `src/...` 직접 Write + `A-1-1` RESPONSE
   (산출물 링크·FMEA·필요 시 ESCALATE). responded.
7. PM: `A-1` 의 자식 status 셀 갱신 → 파트리더 재dispatch (자식 경로만
   전달)
8. 파트리더(`A-1`): 자식 RESPONSE 확인 → `A-1` 롤업 RESPONSE.
   `NEXT: CLOSE`. status=closed. PM 이 `A` 의 status 셀 갱신.
9. PM: 총괄 재dispatch
10. 총괄(`A`): 자식 보고 확인 → `A` 최종 RESPONSE. status=closed →
    PM 에 최종 결과 반환.

ceremony(총괄·파트리더 다단)는 단계/배치당 1회. 말단 개발자 fan-out 만
PRG 별 — 형제는 병렬 dispatch.

---

## 4. 재작성 표면

### 4-1. 삭제·폐기

- `scripts/meta6_parallel_write_repeat.sh`
- 모든 문서의 Track A `claude -p` 절·CLI 순서·`--add-dir` 범위·depth
  guard·condensed-brief 규정

### 4-2. 재작성

| 파일 | 변경 |
|------|------|
| `docs/call-playbook.md` | drift-guard 정본 — 단일 Agent 호출 계약 + ledger 프로토콜로 전면 교체 |
| `CLAUDE.md` (루트) | Track 표·CLI 순서·`--add-dir`·공유파일 race 절 제거, ledger·호출 계약 신설 |
| `.claude/roles/*.md` (21) | director/part-leader = "NEXT 지시 반환, spawn 안 함"; 전 역할 = "general-purpose 로 dispatch됨, 소유 경로 저작, ledger 노드 완결" |
| `.claude/skills/project-manager/SKILL.md`, `.claude/roles/project-manager.md` | PM = 범용 오케스트레이터 + 공유파일 scribe + ledger 캠페인 관리. claude -p 제거 |
| `.claude/agents/*` (46) | 읽기전용 자문 용도로 존속 명시. 저작 = general-purpose+페르소나 주입 경로 문서화 |
| `scripts/run_audit.sh` | claude -p 제거. worktree 셋업만. 감리 = general-purpose+감리 페르소나, 99_audit + ledger 노드 저작 |
| `scripts/validate_agent.py` | 신 호출 계약·ledger 스키마 검증으로 재작성 |
| `scripts/bootstrap_project.py` | `ledger/` + `ledger/index.md` + 노드 템플릿 시드 |
| `templates/stage-gates.md` | Track A 표현 정정 + **ledger-completeness 게이트**(단계 종결 전 모든 dispatch 노드 status=closed) |
| `templates/artifacts/` | ledger 노드 템플릿 추가 |

### 4-3. 신규

- `scripts/validate_ledger.py` — ID/parent 무결성, CHILD INDEX ↔ 자식
  파일 정합, REQUEST/RESPONSE 완결, status 폐쇄 일관, `artifacts:`·
  `rtm:` 링크 존재 검증. 단계 종결 게이트에서 PM 이 호출.

### 4-4. 불변 유지

- §7-2 공유 파일 PM 단독 수정
- 기존 pytest 베이스라인, Karpathy coding-discipline, 예외비율 2:8
  정책, project-fit hook 체계, RTM/WBS/stage-gate 골격

---

## 5. 데이터 흐름·상태 무결성

- ESCALATION = `## NEXT: ESCALATE` 유형. PM 이 처리: 자문 주입 후
  재dispatch, 또는 사용자 표면화.
- validator/hook 실패: PM 이 해당 노드 REQUEST 에 실패 첨부,
  status→in-progress 로 되돌림, 재dispatch.
- 노드 누락·스키마 위반: `validate_ledger.py` 가 검출 → PM 재dispatch.
- 추적성: 위임 전 경로가 ledger 트리에 잔존 → 감리·지식 재활용 강화.

---

## 6. 오류 처리·리스크

### 6-1. PM 단일 병목

- 완화: 본문 미경유(경로·NEXT 만), 형제 병렬 dispatch, ceremony
  배치화.

### 6-2. effort 퇴화

- Agent 툴 effort 미노출. model 티어 + 프롬프트 명시로 근사. 명시된
  손실로 수용.

### 6-3. 페르소나 프롬프트-주입 충실도 (잔여 리스크 1건)

- general-purpose 가 주입된 role 페르소나를 얼마나 충실히 따르는지
  미검증.
- 완화: 노드 frontmatter/RESPONSE 에 self-attestation 필드(역할·준수
  규칙 자기 확인). **롤아웃 전 2차 probe** 로 게이팅. 아키텍처 차단
  요인 아님(저작 가능성은 §7 로 확정).

### 6-4. 마이그레이션

- 파괴적 재설계 → 본 spec → writing-plans → 단계 리팩터.
- Phase 7 findings 및 Amendment #1 은 **이력으로 보존**(삭제 금지 —
  CLAUDE.md 의 findings 보존 원칙).

---

## 7. 실증 근거 (2026-05-16 현 빌드 probe)

`/tmp/aiteam_probe/` 에서 3 probe 병렬 실행 후 **파일시스템 직접 검증**
(자기 보고 불신).

| Probe | 방법 | 파일시스템 결과 | 판정 |
|-------|------|----------------|------|
| **G** | `general-purpose` 에 Read→Write→Bash 지시 | `out_G.txt`(3행 정확)·`bash_G.txt`(BASH_OK) 잔존 | general-purpose = **Write·Edit·Bash 보유, 종료 후 잔존** |
| **N** | `general-purpose` 에 Agent 툴로 하위 spawn 지시 | `nested_N.txt` **부재**. 자기 툴셋 보고 = Bash/Edit/Read/Skill/ToolSearch/Write (**Agent 없음**) | **중첩 불가** |
| **R** | 역할에이전트 `backend-developer-haiku` 에 Write 지시 | `out_R.txt` **부재**. `"Write ... not enabled in this context"`, 툴셋 Read/Glob/Grep | 역할에이전트 **읽기전용 유지** (Phase 7 제약 존속) |

결론: 무claude-p·무과금·저PM컨텍스트 세 제약을 동시에 만족하는 형태는
**general-purpose 저작 노드 + PM 필수 버스 + 계층 ledger** 가 유일.

---

## 8. 의사결정 로그 (본 세션)

| # | 결정 | 근거 |
|---|------|------|
| R1 | 제약 본질 = 구독 내 무과금 필수 | 사용자 명시. SDK/API 경로 배제 |
| R2 | claude -p 절대 미발생 | 사용자 명시 |
| R3 | A안(PM 단독 오케스트레이터) 백본 확정 | 검증된 동작 영역 |
| R4 | 모든 내용 파일 저작, PM 은 경로만 셔틀 | PM 컨텍스트 폭증 방지 |
| R5 | 기존 제약 원점 재검토, 필요시 전면 해제 | 사용자 명시 → probe 수행 |
| R6 | 저작 노드 = general-purpose + 페르소나 주입 | probe G/N/R |
| R7 | 계층 Dewey ledger + 요청-응답 완결 노드 | 사용자 제안 |
| R8 | ledger = 실산출물 래퍼(링크), 컨테이너 아님 | 사용자 선택 |
| R9 | 범위 = 프로젝트 내 (cross-project 제외) | 사용자 선택 |
