# Coding Discipline — 구현 시점 행동 원칙 (SSOT)

본 문서는 본 하네스의 **구현 담당 6 직군** — `backend-developer`,
`web-developer`, `batch-developer`, `web-publisher`, `infrastructure-engineer`,
`policy-engineer` — 가 코드를 저작·수정할 때 공통으로 따르는 행동 원칙의
단일 출처(SSOT) 다.

본 문서는 Andrej Karpathy 의 4 원칙 (출처:
`https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md`)
중 본 하네스 정책과 정합하는 §1·§3 을 채택하고, §2 는 enumeration 정책
우선 단서를 부착하여 한정 채택, §4 는 기존 검증 체계로 이미 강제되므로
별도 인용하지 않는다.

## §1 Think Before Coding — 가정 표면화

코드를 내려쓰기 전에:

- 사양의 모호점·암묵 가정·해석이 갈릴 수 있는 부분을 **명시적으로
  표면화**한다. 내부 추론으로 한 가지를 선택하고 조용히 진행하지 말 것.
- 인접 모듈·과거 경험에서 동작을 **추론(infer) 금지**.
- 모호함이 한 단계라도 남으면 다음 순서로 처리:
  1. 자문 가능 영역 (인터페이스·보안·DB·아키 경계·접근성·운영) → Track B
     자문 호출 (`docs/call-playbook.md` §0).
  2. 자문으로 해소되지 않으면 ESCALATION 프로토콜로 caller 에 반환.
- "추측해서라도 짧게" 보다 **"정확하게 멈춰 묻기"** 를 택한다.

## §2 Simplicity First — 본 하네스 정책 우선 단서

원칙 (Karpathy 원문 의도):

- 요구되지 않은 추상화·플래그·유연성·예외 처리를 추가하지 않는다.
- 200 줄 구현이 50 줄로 줄어들면 다시 쓴다.

**단, 다음 정책은 Simplicity 보다 우선:**

- `docs/exception-handling-ratio-policy.md` 의 **7 Failure Categories
  enumeration · FMEA 표 · UT variant ratio 0.7** — 불가능해 보이는
  시나리오라도 카테고리상 enumerate 의무가 있으면 enumerate 한다 (lenient
  mode `variant-count ≤ 5` 에 한해 비율 강제 면제).
- `policy-engineer` 의 **SRP · 결정론 · 표준 라이브러리만** 규칙은 §2 와
  같은 방향이므로 그대로 따른다.

요컨대: enumeration 의무가 있는 영역 (PRG·IF·SCN·BATCH 본문 FMEA / UT
variant) 은 정책을 따르고, 그 외 코드 (보일러플레이트·단순 변환·utility
함수 등) 는 짧고 단순하게.

## §3 Surgical Changes — 인접 코드 보존

기존 파일을 수정할 때:

- 수정 대상 외 **인접 코드·주석·포매팅·import 순서**를 그대로 보존.
- 정상 동작 코드를 같이 리팩토링하지 말 것.
- 기존 스타일 컨벤션이 본인 선호와 달라도 따른다.
- **본인 변경**으로 새로 발생한 사용처 없는 import·변수·함수만 정리.
  사전부터 dead 인 코드는 PM/리뷰어에 flag 만 하고 삭제 금지.
- "공유 파일 단독 수정 규칙"(루트 `CLAUDE.md`) 과 결합: surgical change
  가 공유 파일 영역 (`project-state.md`, `RTM/**`, `agent-call-log.md`,
  각 디렉토리 `index.md` 등) 을 건드리면 즉시 PM 에스컬레이션.

## §4 Goal-Driven Execution — 본 하네스 기존 메커니즘으로 강제

Karpathy §4 (성공 기준 정의·검증 루프) 는 본 하네스에서 다음 메커니즘으로
이미 강제되므로 본 SSOT 에서 별도 인용하지 않는다:

- `02_design/unit-test-cases/UT-*.md` (성공 기준 명세)
- `scripts/validate_artifact_hierarchy.py` · `check_frontmatter.py`
  · `sync_back_references.py` (자동 검증)
- `projects/<name>/scripts/run_project_hooks.sh` (프로젝트별 hook)
- ESCALATION 프로토콜 (블록 시 caller 반환)

## 페르소나 인용 형식 (참고)

본 SSOT 를 인용하는 6 개 개발자 페르소나는 `## Rules` 섹션 끝에 다음
한 줄을 둔다:

> - **구현 시점 행동 원칙 (Coding Discipline SSOT)**:
>   `docs/coding-discipline.md` §1(Think Before Coding — 가정 표면화)
>   · §3(Surgical Changes — 인접 코드 보존) 준수. §2(Simplicity First)
>   는 7 Failure Categories enumeration 정책
>   (`docs/exception-handling-ratio-policy.md`) 이 우선.
