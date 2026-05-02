# CLAUDE.md — AI SI Project Team (platform-level guidance)

이 저장소는 Claude Code multi-subagent 기반 SI 조직 모사 플랫폼이다. 본
CLAUDE.md 는 레포 루트뿐 아니라 **`projects/<name>/` 하위 세션에도 자동
상속**되므로, 여기에 적힌 규칙은 모든 프로젝트 실행에 공통 적용된다.

## Identity

- 저장소: `ai_team` (GitHub: earthnciel/ai_team)
- 목적: SI 프로젝트 실행 조직(PM · 총괄 · 실무자 · 자문가 · 감리)을 모사하는 Claude Code 플랫폼
- 핵심 참조 문서
  - `README.md` — 시작·Quick start·에이전트 카탈로그
  - `docs/call-playbook.md` — 역할별 Track A/B 호출 규칙 정본 (drift-guard 대상)
  - `docs/superpowers/specs/2026-04-17-ai-si-team-design.md` — 설계서 (+ `2026-04-18-amendment-01-claude-p-invocation.md` Amendment #1)
  - `templates/stage-gates.md` — 단계 진입·종결 조건 정본

## 저장소 구조

- `.claude/roles/<role>.md` — 역할 페르소나 단일 소스 (20 개)
- `.claude/agents/<role>-<variant>.md` — Track B 서브에이전트 shell (45 개)
- `.claude/skills/project-manager/SKILL.md` — PM Skill (SessionStart hook 자동 로드)
- `scripts/` — 15 개 validator / helper / bootstrap 스크립트
- `templates/` — `stage-gates.md` + `artifacts/` 템플릿 모음
- `docs/` — 설계서·amendment·call-playbook·findings·plans
- `projects/<name>/` — 실행된 SI 프로젝트 산출물 (**gitignored**)
- `src/`, `infra/`, `meta-tests/` — 프로젝트 런타임 산출물 (**gitignored**)

## 언어·응답

- 사용자 응답: **항상 한국어**. 기술 용어·식별자는 원문 유지.
- 시스템 프롬프트·코드 주석은 영어 허용.
- 악센트·특수 문자 보존 (é, ü, ñ, ç 등 ASCII 치환 금지).

## 호출 트랙 (spec §1-2, call-playbook §0)

| Track | 방법 | 용도 | 툴셋 |
|-------|------|------|------|
| **Track A** | Bash `claude -p ...` subprocess | 주 산출물 저작·하위 호출·자문 dispatch | 전체 (Read/Write/Edit/Glob/Grep/Bash/Agent) |
| **Track B** | 현 세션 `Agent` 툴 + `subagent_type=<name>` | 자문·리뷰·분석 응답 | `Read, Glob, Grep` (읽기 전용) |
| **Skill** | PM Skill (SessionStart hook) | 사용자 세션 PM 페르소나 | 세션 툴 계승 (Opus · xhigh 고정) |

### Track A CLI 인자 순서 (load-bearing)

```
claude -p --dangerously-skip-permissions [--add-dir <p>] \
  --append-system-prompt "$(cat .claude/roles/<role>.md)" \
  --model <m> --effort <e> "<prompt>"
```

- `--add-dir` 는 **반드시** `--append-system-prompt` 앞에. 역순이면 positional prompt 가 `--add-dir` 값으로 흡수되어 세션이 `Error: Input must be provided` 로 종료 (Phase 7 Task 6 finding).
- 감리 호출은 `scripts/run_audit.sh` 헬퍼가 이 순서를 자동 보장.

## 공유 파일 단독 수정 규칙 (spec §7-2)

다음 파일은 PM(또는 영역의 단일 상위 에이전트)만 직렬 수정한다. Track A
subprocess 는 **직접 수정 금지** — 변경 필요 시 에스컬레이션으로 PM 에
전달:

- `projects/<name>/project-state.md`
- `projects/<name>/RTM/**`
- `projects/<name>/agent-call-log.md`
- `projects/<name>/00_kickoff/rollback-history.md`
- `projects/<name>/escalations.md`
- 각 디렉토리의 `index.md` (해당 영역 저작 책임자만)

## `--add-dir` 범위 한정 규칙 (call-playbook §0)

Track A subprocess 를 띄울 때 `--add-dir` 에는 **해당 subprocess 가 저작할
산출물 디렉토리만** 지정한다. 공유 파일 경로를 포함하면 병렬 dispatch 시
race 여지가 생긴다.

- 각 subprocess 가 쓸 수 있는 경로 = (a) 자기 소유 산출물 디렉토리 + (b) 프로젝트 루트 한정 Read 경로
- 공유 파일이 있는 경로를 `--add-dir` 로 발급 금지
- 감리 호출은 `scripts/run_audit.sh` 가 `--add-dir <project>/99_audit` 로 한정

## 프로젝트 작업 중 체크리스트

현재 세션(PM 또는 subprocess)이 특정 프로젝트를 다룰 때:

1. `projects/<name>/project-state.md` 먼저 읽고 `current-stage:`, `scale:` 확인
2. 해당 stage 의 `templates/stage-gates.md` 조건 대조
3. 산출물 작성·수정은 **자기 소유 디렉토리 한정**, 공유 파일 변경이 필요하면 PM 에 에스컬레이션
4. 작업 완료 후 검증 명령:
   - `python3 scripts/validate_artifact_hierarchy.py <name>`
   - `python3 scripts/check_frontmatter.py <name>`
   - `python3 scripts/sync_back_references.py <name>` (참조 변경이 있었을 때)
5. 리뷰·감리는 PM 주관 (감리는 `scripts/run_audit.sh`)

## 산출물 경로 표기 관행 (Phase 7 N15 / Part B C-14-3)

Role · persona probe · `Artifacts You Own` · frontmatter `related:` 등에서
산출물 경로는 **프로젝트 상대 경로** (`projects/<project>/<stage>/...` 또는
단순히 `<stage>/...`) 로 기술한다. 절대 경로 (`/home/earth/ai_team/...`)
나 worktree-특정 경로는 사용하지 않는다 — 감리·메타테스트 worktree 에서
유효성이 깨지기 때문.

## 도메인 중립성 원칙

플랫폼 코드 (roles · scripts · templates · spec 본문)에는 특정 프로젝트
도메인 이름(예: `book-mgmt-api`)을 하드코딩하지 않는다. 프로젝트 이름은
파라미터로 받고, 예시는 `<project>` / `my-project` 같은 placeholder 를 쓴다.

단, `docs/superpowers/findings/`, `docs/superpowers/plans/` 는 과거 실행
기록이므로 실제 프로젝트 이름이 남아있어도 유지.

## 프로젝트별 CLAUDE.md (선택)

`projects/<name>/CLAUDE.md` 를 만들면 그 프로젝트 작업 시 **루트 CLAUDE.md
위에 추가**로 로드된다. 다음 내용을 프로젝트 CLAUDE.md 에 두면 좋다:

- 도메인 용어사전 (업무 용어 ↔ 코드 심볼 매핑)
- 클라이언트별 제약 (예: "모든 외부 API 는 HTTPS만", "PII 는 AES-256-GCM")
- 프로젝트-특정 코딩 규칙 (라이브러리 버전, 데이터베이스 제약 등)

본 루트 CLAUDE.md 는 플랫폼 공통 규칙만 담고, 도메인 규칙은 프로젝트
디렉토리에 둔다.

## Nested git

`projects/*/` 는 `.gitignore` 대상이라, 그 안에서 `git init` 하면 **완전 독립
된** git repo 가 된다 (submodule 아님). 프로젝트 종료 후 고객 저장소로
push 하는 흐름:

```bash
cd projects/<name>
git init && git add -A && git commit -m "initial delivery"
git remote add origin <client-repo-url>
git push -u origin master
```

## 테스트·검증 (변경 후 필수)

```bash
python3 -m pytest -q                    # 기준 144 passing
python3 scripts/validate_agent.py --all # 기준 66/66 clean
```

두 명령이 모두 clean 이어야 commit. 실패 시 근본 원인을 고치고 재실행
(`--no-verify` 같은 우회 금지).

## Phase 7 반영 맥락 (2026-04-19)

Phase 7 E2E + 메타테스트로 42 개 구조 개선이 master 에 반영됨. 중요한 것:

- **공유 파일 단독 수정 규칙**, **`--add-dir` 범위 한정**, **Track A CLI 순서**, **CR 사이클 메타데이터**, **audit finding Type A/B/C/D 분류**, **4-계층 Track A depth guard**, **`reviewed-by` 필수 기재** 등.

구체 이력:
- `docs/superpowers/findings/2026-04-18-phase7-findings.md` (Part A·findings 19건)
- `docs/superpowers/findings/2026-04-19-phase7-part-b-findings.md` (Part B 메타테스트 결과 + 8 개선안)

## 역할 재정비 (2026-05-02)

한국 SI 통념 정합을 위해 아키텍트 3종(AA·SWA·TA)·웹 직군 3종(designer·
web-publisher·web-developer) 페르소나·산출물 디렉토리·dispatch 매트릭스·
validator 를 두 차례 재정비 (각 5-commit 시리즈). 현재 master 는 다음 흐름:

### 아키텍트 분담 (`02_design/architecture/` 4영역 분할)

- `application/` — application-architect (overview·domain-model·business-
  flow·components/CMP-* + ADR) + software-architect (code-architecture·
  module-patterns·interface-policy + ADR). application-director 가 양쪽
  Track A dispatch.
- `technology/` — technical-architect (overview·middleware·deployment-
  topology·nfr-technology + ADR). 좁은 인프라·런타임·미들웨어·토폴로지
  한정. infrastructure-director 가 Track A dispatch.
- `data/` — data-modeler. application-director 소속.
- `security/` — security-specialist. infrastructure-director 소속.
- Clean Architecture 기본 채택 ADR 은 SWA 단독 책임 (TA→SWA 이관됨).
- `validate_artifact_hierarchy.py` 가 subdomain 별 owner 정합을 검증.

### 웹 직군 흐름 (한국 SI 통념)

1. **SWA**: 백엔드 공통 모듈 (인증·세션·RBAC 등) 사전 세팅 (프론트 아님)
2. **web-developer**: `02_design/screens/SCN-*.md` 단독 저작
3. **designer**: `02_design/design-system/` (overview·colors·typography·
   layout·logo-brand) 단독 저작 — SCN 은 안 함
4. **web-publisher**: 03_implementation 단계에서 SCN+design-system 을
   입력받아 `src/web/` HTML 마크업·CSS 껍데기 단독 저작 (web-developer
   의 동적 기능 추가 전 선행). 02_design 저작 책무 없음.
5. **web-developer**: publisher 마크업 위에 프론트엔드 동적 기능·
   백엔드 API 연동 구현.

`validate_artifact_hierarchy.py` 가 `02_design/design-system/` owner=
designer 정합을 검증.
