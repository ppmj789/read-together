# Exception-Handling Ratio Policy (2:8 법칙)

본 문서는 ai_team 하네스가 단위기능 차원에서 **정상 케이스 ≤ 2 : 비정상
예외 처리 ≥ 8** 비율을 자연스럽게 도출하도록 강제하는 단일 정책
SSOT (Single Source Of Truth) 다. 페르소나·산출물·검증 스크립트는 본
문서를 인용하며, 본 문서가 변경되면 인용처를 동시 갱신해야 한다.

---

## 1. 목적과 진앙지

비즈니스 어플리케이션에서 단위기능의 정상 동작 코드는 2할이고, 나머지
8할은 시스템 보호·비즈니스 정합성을 지키는 예외 처리다. AI 가 정상
케이스 위주로 코드를 생성하면 예외 처리 미흡으로 전체 기능이 망가지므로,
2:8 비율을 단계별 산출물 형태에 맞춰 강제한다.

**비율 강제의 수학적 진앙지는 단위테스트 설계** 다. 요구사항에는 카테고리
커버리지만 강제하고, 설계는 FMEA 메커니즘을 강제하며, 단위테스트에서
숫자 비율을 강제한다 — 그러면 구현은 TDD 방식으로 자연스럽게 따라온다.

---

## 2. 단계별 강제 강도 매트릭스

| 단계 | 강제 강도 | 강제 형태 | 책임 페르소나 |
|------|---------|---------|------------|
| **요구사항** (`01_analysis`) | **약** — 발견 강제 | 7 Failure Categories 카테고리 커버리지 (해당 없는 카테고리는 N/A 사유 명시). 숫자 비율은 강제하지 않음 — "가짜 예외" 양산 방지. | application-architect |
| **설계** (`02_design`) | **중** — 메커니즘 강제 | RPC 실패모드 enumerate · 엔티티 불변식 · 상태머신 illegal transition · FMEA 표 의무. parent-variant 트리 구조 (flat list 금지). | software-architect (PRG/IF), application-architect (도메인 모델·비즈니스 흐름), data-modeler (엔티티 불변식) |
| **단위테스트 설계** (`02_design/unit-test-cases/`) | **강** — **숫자 비율 강제** | `unit-variant-ratio: { happy: ≤ 0.3, exception: ≥ 0.7 }`. parent UT-* 1개 = RPC/PRG 1개 = variant N entries (table-driven 권장). | tester (자문) + backend-developer / web-developer / batch-developer (저작) |
| **구현** (`03_implementation`) | 간접 강제 | 단위테스트 선행으로 자연 도출 + "RPC 1개 = 핸들러 함수 1개" + precondition guard chain 패턴 + 예외 경로 미구현 검출. | backend-developer · web-developer · batch-developer |
| **통합테스트** (`04_test/integration-test-results`) | 이미 강제 | Variant Multiplication 정책 (RQ 의 `failure-categories` × 시나리오 분기). | tester |

---

## 3. 7 Failure Categories (FMEA SSOT)

요구사항·설계·테스트·구현 전 단계가 인용하는 단일 카테고리 정의다.
산출물의 `failure-categories: [<list>]` frontmatter 또는 본문 표에서 각
항목이 어느 카테고리를 다루는지 enumerate 한다.

| # | 카테고리 | 정의 | 대표 사례 |
|---|---------|------|---------|
| 1 | **Input Failure** | 입력 형식·필수값·타입·범위 위반 | 빈 문자열, 음수 금액, 잘못된 이메일 형식 |
| 2 | **State Transition Failure** | illegal transition / 도메인 상태 위반 | 이미 결제 완료된 주문 재결제, 닫힌 계좌에 입금 |
| 3 | **External Dependency Failure** | 외부 API · 메시지 브로커 · DB · 파일 시스템 장애 | 외부 결제 게이트웨이 timeout, Kafka publish 실패 |
| 4 | **Concurrency / Race Failure** | 동시 호출·중복 요청·낙관적 락 충돌 | 동일 주문 동시 결제, 잔액 차감 race |
| 5 | **Partial Failure** | 다단계 작업 중 일부만 성공 | 결제 성공 + 재고 차감 실패, 대량 처리 중 일부 실패 |
| 6 | **Resource Failure** | 메모리·CPU·디스크·커넥션 풀 등 자원 부족 | DB 커넥션 풀 고갈, 파일 업로드 크기 초과 |
| 7 | **Business Rule Violation** | 비즈니스 정책 위반 (한도·권한·금지 행위) | 일일 송금 한도 초과, 권한 없는 데이터 접근, 부정 거래 탐지 |

**요구사항 단계 적용**: 요구사항 위계 전체에서 7 카테고리 각각이 최소
1개 RQ 에 enumerate 되어야 한다. 해당되지 않는 카테고리는
`RQ-<group>-CAT-NA-<n>.md` 에 N/A 사유 단독 기재.

**설계 단계 적용**: 각 PRG/IF 본문에 다음 FMEA 표를 의무 포함:

```
| # | 실패 카테고리 | 트리거 조건 | 검출 위치 | 방어 동작 | 응답·이벤트 매핑 |
|---|------------|-----------|---------|---------|---------------|
| 1 | Input Failure | <조건> | <레이어> | <동작> | <응답 또는 이벤트> |
| ... | ... | ... | ... | ... | ... |
```

해당되지 않는 카테고리는 행에 "N/A: <사유>" 명시.

---

## 4. 3 불변식 (parent-variant 트리 응집)

설계의 enumeration 세분화와 구현·WI·테스트의 응집은 다른 축이다.
2:8 을 leaf 개수로 인식하면 산출물 폭증, parent 1개의 내부 구조로
인식하면 응집된다. 다음 3 불변식이 응집을 보장한다.

### 불변식 ① Tree, not flat list

설계 산출물의 정상/비정상 케이스는 parent 1개의 자식 노드로 트리
표현한다. flat list 금지.

```
PRG-TRANSFER (parent = 구현 단위 = WI 1개)
├─ normal/
│   ├─ happy_KRW
│   └─ happy_FX
└─ exception/
    ├─ insufficient_balance       (cat 7)
    ├─ account_frozen             (cat 2)
    ├─ concurrent_conflict        (cat 4)
    ├─ idempotency_dup            (cat 4)
    ├─ daily_limit_exceeded       (cat 7)
    ├─ recipient_not_found        (cat 1)
    ├─ fx_precision               (cat 1)
    └─ fraud_detected             (cat 7)
```

### 불변식 ② One RPC = one handler

구현 단위는 RPC/PRG 1개당 핸들러 함수 1개. variant 마다 별도 함수로
분리하지 않는다. 그래야 검증 순서·트랜잭션 경계·응답 포맷이 일관된다.

### 불변식 ③ Guard chain, not scattered checks

예외 검증을 핸들러 진입 직후 단일 precondition guard chain 으로
응집한다. 흩어진 if 분기 금지. 검증의 순서·우선순위가 한 곳에 명시되어
비즈니스 정합성이 보장된다.

```pseudo
fn handle_transfer(ctx, req) -> Resp | Error:
    err = validate_preconditions(ctx, req)   # 8개 예외가 응집된 80% 코드
    if err: return err
    return execute_transfer(ctx, req)         # 정상 2개 — 20% 코드

fn validate_preconditions(ctx, req) -> Error?:
    # 잔액 → 계좌상태 → 한도 → 멱등 → 외화정밀도 → 부정거래
    # 순서·우선순위가 한 곳에 명시 — 비즈니스 정합성의 핵심
```

3 불변식이 지켜지면 비율(검증 ≥ 80% / 실행 ≤ 20%)은 자연 도출된다 —
비율 자체를 강제하는 대신 **카테고리 누락 없음 + 3 불변식 준수** 를
강제한다 (가짜 예외 양산 방지).

---

## 5. 단위테스트 variant 비율 (숫자 강제)

`02_design/unit-test-cases/UT-<DOM>-<seq>.md` 자식 파일은 다음
frontmatter 와 본문 구조를 강제한다.

### Frontmatter 필수 필드 (flat key 형식 — 단일 레벨 frontmatter 파서 정합)

```yaml
---
id: UT-<DOM>-<seq>
title: <한국어 제목>
parent-prg: PRG-<DOM>-<seq>          # 본 UT 가 검증하는 parent PRG·RPC ID
variant-count: 10                    # 총 variant 수 (parent 당 12 초과 시 경고)
variant-happy-count: 2               # type=normal variant 수
variant-exception-count: 8           # type=exception variant 수
exception-categories: [1, 2, 4, 7]   # exception variant 들이 다루는 카테고리 (parent RQ failure-categories 부분집합)
depends-on: [RQ-..., PRG-..., SCN-...]
referenced-by: []
---
```

본문에는 다음 표로 variants 를 명세 (트리 표현은 indent 로 — flat list 금지):

```
| Variant | Type | Failure Category | 설명 |
|---------|------|------------------|------|
| happy_KRW | normal | - | <조건·기대 결과> |
| happy_FX | normal | - | <조건·기대 결과> |
| insufficient_balance | exception | 7 | <트리거·기대 응답> |
| ... | ... | ... | ... |
```

### 강제 규칙

1. **숫자 비율**: `variant-happy-count / variant-count ≤ 0.3` 그리고
   `variant-exception-count / variant-count ≥ 0.7`. 위반 시 stage-gate
   fail (`validate_artifact_hierarchy.py` exit 1).
2. **합계 일관성**: `variant-happy-count + variant-exception-count ==
   variant-count`. 위반 시 fail.
3. **One UT = one parent**: UT-*.md 1개 = PRG/RPC 1개 = `variant-count` N
   entries. variant 마다 UT 파일 분리 금지 (산출물 폭증 방지).
4. **카테고리 정합**: `exception-categories` 가 parent PRG 의 RQ
   `failure-categories:` 부분집합. 미정의 카테고리 도입 금지 (advisory —
   parent RQ 추적이 정착된 후 strict 전환).
5. **variant 상한**: `variant-count > 12` 일 때 경고 — 진짜 별개
   기능인지 재검토 트리거.

---

## 6. 구현 단계 검증

`03_implementation` 산출물 (PRG 별 코드) 은 다음을 만족한다 — 위반 시
코드 리뷰 finding:

1. **One RPC = one handler**: PRG·RPC 1개당 핸들러 함수 1개. variant 별
   함수 분리 금지.
2. **Precondition guard chain**: 핸들러 진입 직후 단일 검증 체인. 흩어진
   if 분기 금지.
3. **예외 경로 누락 없음**: UT-*.md 의 모든 exception variant 가 코드의
   guard chain 에 검증 분기로 존재. 누락 시 finding.
4. **코드 헤더 주석에 카테고리 명시**: 어느 카테고리·variant 키워드를
   다루는지 핸들러 헤더 주석에 enumerate.

---

## 7. 위반 시 게이트 동작

| 위반 항목 | 게이트 | 조치 |
|---------|------|-----|
| RQ 위계의 7 카테고리 enumerate 누락 | `01_analysis` 종결 | application-director 가 AA Track A 재호출 + PM 에 SOW 보강 ESCALATION |
| PRG/IF 의 FMEA 표 누락 | `02_design` 설계 리뷰 | software-architect 자문 finding → 책임 개발자에게 corrective Track A 재호출 |
| UT-*.md 의 비율 위반 (`happy > 0.3` 또는 `exception < 0.7`) | `02_design` 종결 | `validate_artifact_hierarchy.py` exits 1 — PASS 보고 금지 |
| 코드의 RPC=핸들러 1:1 위반 | `03_implementation` 코드 리뷰 | 책임 개발자에게 corrective Track A 재호출 |
| 통합테스트 variant multiplication 누락 | `04_test` 종결 | tester 재호출 |

---

## 8. 인용 의무

다음 페르소나·문서는 본 정책을 명시 인용한다 (drift-guard 대상):

- `.claude/roles/application-architect.md` — 7 카테고리 enumerate (요구사항)
- `.claude/roles/software-architect.md` — 7 카테고리 + 3 불변식 (설계 자문)
- `.claude/roles/tester.md` — variant 비율 자문
- `.claude/roles/backend-developer.md` · `web-developer.md` · `batch-developer.md` — UT 저작 시 비율 강제 + 구현 시 3 불변식
- `templates/stage-gates.md` — 단계별 게이트
- `scripts/validate_artifact_hierarchy.py` — UT 비율 자동 검증

본 문서가 단일 출처이므로, 페르소나에는 정의를 중복 기재하지 않고
본 문서 경로 (`docs/exception-handling-ratio-policy.md`) 를 인용한다.
