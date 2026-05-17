# claude -p 제거 + 계층 ledger 재설계 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 하네스의 모든 `claude -p` 호출을 제거하고, 위임·의사소통을 계층 Dewey ledger(요청-응답 완결 노드, 실산출물 래퍼)로 구조화한다.

**Architecture:** "Track A" 개념을 폐기하고 단일 primitive(현 세션 Agent 툴 → `subagent_type=general-purpose` + 페르소나 프롬프트 주입)로 통합한다. general-purpose 노드가 자기 산출물·자기 ledger 노드를 직접 저작하고, PM 은 본문이 아닌 노드 경로·`NEXT:` 지시만 셔틀하는 필수 버스가 된다. 위임·통신 이력은 `projects/<name>/ledger/` 계층 트리에 축적된다.

**Tech Stack:** Python 3 (표준 라이브러리, pytest), Bash, Markdown + YAML frontmatter. pytest 설정 파일 없음 — `python3 -m pytest -q` 가 `tests/test_*.py` 자동 수집(기준 153 passing). drift-guard = `scripts/validate_agent.py --all`(기준 66/66).

**근거 spec:** `docs/superpowers/specs/2026-05-16-no-claude-p-ledger-redesign-design.md`

---

## 파일 구조 (생성·수정·삭제 맵)

### 생성
- `scripts/validate_ledger.py` — ledger 트리 무결성 검증기 (ID/parent, CHILD INDEX↔파일, 요청-응답 완결, status 폐쇄, artifacts/rtm 링크 존재)
- `tests/test_validate_ledger.py` — 위 검증기 pytest
- `templates/artifacts/ledger/index.md.tmpl` — 캠페인 루트 인덱스 템플릿
- `templates/artifacts/ledger/node.md.tmpl` — 요청-응답 완결 노드 템플릿
- `docs/superpowers/findings/2026-05-16-persona-injection-fidelity-probe.md` — Phase 0 probe 결과 기록

### 수정
- `docs/call-playbook.md` — drift-guard 정본. §0/§4/§5 전면 교체(단일 Agent 호출 계약 + ledger 프로토콜)
- `CLAUDE.md` — Track 표·CLI 순서·`--add-dir`·공유파일 race 절 제거, ledger·호출 계약 신설
- `.claude/roles/*.md` (21) — director/part-leader = "NEXT 반환, spawn 안 함"; 전 역할 = general-purpose dispatch + ledger 노드 완결
- `.claude/skills/project-manager/SKILL.md`, `.claude/roles/project-manager.md` — PM = 범용 오케스트레이터 + 공유파일 scribe + ledger 캠페인 관리. claude -p 제거
- `.claude/agents/*.md` (46) — 읽기전용 자문 용도 명시 (body 텍스트)
- `scripts/derive_dynamic_agents.py` — agents shell body 생성 텍스트 갱신
- `scripts/validate_agent.py` — 신 호출 계약·ledger 스키마 검증으로 재작성
- `scripts/bootstrap_project.py` — `ledger/` + `ledger/index.md` 시드 추가
- `scripts/run_audit.sh` — claude -p 제거. worktree 셋업만
- `templates/stage-gates.md` — Track A 표현 정정 + ledger-completeness 게이트
- `tests/test_validate_agent.py`, `tests/test_bootstrap_project.py`, `tests/test_run_audit.sh`, `tests/test_derive_dynamic_agents.py` — 대응 테스트 갱신

### 삭제
- `scripts/meta6_parallel_write_repeat.sh` — 병렬 writer race 시나리오 소멸
- (spec 내 meta6 참조 2줄은 이력이므로 유지 — 삭제 금지)

### 불변 (건드리지 않음)
- §7-2 공유 파일 PM 단독, RTM/WBS/stage 골격, 예외비율 2:8 정책, project-fit hook 체계, Karpathy discipline

---

## Phase 0 — 페르소나 주입 충실도 게이트 (HARD GATE)

> spec §6-3. general-purpose 가 프롬프트 주입된 role 페르소나를 충실히 따르지 못하면 roles 재작성 접근을 조정해야 한다. 이 Phase 가 FAIL 이면 진행 중단하고 사용자에게 보고.

### Task 0: persona-injection 충실도 probe

**Files:**
- Create: `docs/superpowers/findings/2026-05-16-persona-injection-fidelity-probe.md`

- [ ] **Step 1: probe 입력 준비**

Run:
```bash
rm -rf /tmp/persona_probe && mkdir -p /tmp/persona_probe
```

- [ ] **Step 2: 페르소나 주입 dispatch 3건 실행**

현 세션(PM)에서 Agent 툴로 3건 병렬 dispatch. 각 prompt 는 다음 형식:

```
[PERSONA — 이 역할로 행동하라. 아래는 너의 역할 정의 전문이다.]
<<<.claude/roles/<ROLE>.md 전문 inline>>>
[/PERSONA]

[TASK]
너는 위 역할이다. /tmp/persona_probe/<ROLE>_out.md 에 다음을 직접 Write 하라:
1. 첫 줄: "ROLE-SELF-ID: <역할 한국어명>" (페르소나의 `# Role:` 헤더에서 가져옴)
2. 다음: 이 역할의 `## Artifacts You Own` 에 적힌 산출물 scope 를 3줄로 요약
3. 마지막: 이 역할이 절대 하지 않는 일 1가지 (페르소나 Rules 기준)
완료 후 최종 메시지에는 "WROTE <경로>" 한 줄만 반환하라.
[/TASK]
```

대상 3 ROLE: `application-director`, `backend-developer`, `audit-team`.
`subagent_type=general-purpose`, `model=sonnet`.

- [ ] **Step 3: 파일시스템 검증 (자기보고 불신)**

Run:
```bash
for r in application-director backend-developer audit-team; do
  echo "=== $r ==="; cat /tmp/persona_probe/${r}_out.md 2>&1; echo
done
```

판정 기준 (3/3 충족 시 PASS):
- 각 파일이 실제 존재 (general-purpose 가 Write 수행)
- `ROLE-SELF-ID:` 가 해당 role 의 `# Role:` 한국어명과 일치 (페르소나 자기동일시)
- Artifacts 요약·금지사항이 해당 role 페르소나 내용과 의미적으로 일치 (환각 아님)

- [ ] **Step 4: 결과를 finding 으로 기록**

`docs/superpowers/findings/2026-05-16-persona-injection-fidelity-probe.md` 작성:
- frontmatter: `name`, `description`, `metadata.type: reference`
- 본문: probe 방법, 3건 원문 발췌, 판정(PASS/FAIL), PASS 면 "roles 재작성은 페르소나 inline 주입 방식으로 진행 가능" 결론, FAIL 이면 구체 실패 양상 + 권고(예: 페르소나 요약본 주입, attestation 강화)

- [ ] **Step 5: 게이트 판정**

PASS → 다음 Phase 진행. FAIL → **plan 실행 중단**, 사용자에게 finding 제시하고 spec §1-2 페르소나 주입 방식 재설계 요청.

- [ ] **Step 6: Commit**

```bash
rm -rf /tmp/persona_probe
git add docs/superpowers/findings/2026-05-16-persona-injection-fidelity-probe.md
git commit -m "docs(finding): persona-injection 충실도 probe 결과 (Phase 0 게이트)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 1 — ledger 기반 (검증기·템플릿·시드)

### Task 1: ledger 노드 템플릿 작성

**Files:**
- Create: `templates/artifacts/ledger/node.md.tmpl`
- Create: `templates/artifacts/ledger/index.md.tmpl`

- [ ] **Step 1: 노드 템플릿 작성**

`templates/artifacts/ledger/node.md.tmpl`:

```markdown
---
id: <ID>
parent: <PARENT_ID_OR_EMPTY>
role: <ROLE>
dispatched-by: PM
model: <opus|sonnet|haiku>
stage: <STAGE>
status: pending
artifacts: []
rtm: []
created: <ISO8601>
responded:
---

## REQUEST
<!-- PM 이 부모 NEXT 지시로부터 작성. 생성 후 정정은 append-only -->

## RESPONSE
<!-- 이 노드 담당 general-purpose 가 직접 작성. 실산출물은 링크만, 본문 복제 금지 -->

## CHILD INDEX
| child id | path | role | one-line purpose | status |
|----------|------|------|------------------|--------|

## NEXT
<!-- 기계가독 지시 (PM 이 파싱·실행). 한 줄당 하나:
  DISPATCH <child-id> role=<role> model=<opus|sonnet|haiku>
  ESCALATE <사유>
  CLOSE
-->
```

`templates/artifacts/ledger/index.md.tmpl`:

```markdown
---
id: ledger-root
title: 위임·의사소통 ledger 캠페인 인덱스
child-count: 0
---

# Ledger — 캠페인 인덱스

| campaign id | root node path | stage | purpose | status |
|-------------|----------------|-------|---------|--------|
```

- [ ] **Step 2: Commit**

```bash
git add templates/artifacts/ledger/
git commit -m "feat(templates): ledger 노드·캠페인 인덱스 템플릿

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 2: validate_ledger.py — frontmatter·ID·parent 무결성 (TDD)

**Files:**
- Create: `tests/test_validate_ledger.py`
- Create: `scripts/validate_ledger.py`

- [ ] **Step 1: Write the failing test**

`tests/test_validate_ledger.py`:

```python
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "validate_ledger.py"


def _run(project_dir):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(project_dir)],
        capture_output=True, text=True,
    )


def _node(tmp_path, ledger_dir, node_id, parent, status="closed",
          request="r", response="x", children_rows="", next_block="CLOSE",
          artifacts="[]", rtm="[]"):
    ledger_dir.mkdir(parents=True, exist_ok=True)
    p = ledger_dir / f"{node_id}.md"
    p.write_text(
        f"---\nid: {node_id}\nparent: {parent}\nrole: backend-developer\n"
        f"dispatched-by: PM\nmodel: sonnet\nstage: 02_design\n"
        f"status: {status}\nartifacts: {artifacts}\nrtm: {rtm}\n"
        f"created: 2026-05-16T00:00:00Z\nresponded: 2026-05-16T01:00:00Z\n---\n\n"
        f"## REQUEST\n{request}\n\n## RESPONSE\n{response}\n\n"
        f"## CHILD INDEX\n| child id | path | role | one-line purpose | status |\n"
        f"|----------|------|------|------------------|--------|\n{children_rows}\n\n"
        f"## NEXT\n{next_block}\n",
        encoding="utf-8",
    )
    return p


def test_clean_single_node_passes(tmp_path):
    ledger = tmp_path / "ledger"
    _node(tmp_path, ledger, "A", parent="")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_missing_parent_file_fails(tmp_path):
    ledger = tmp_path / "ledger"
    _node(tmp_path, ledger, "A-1", parent="A")  # parent A 파일 없음
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "parent" in (r.stdout + r.stderr).lower()


def test_id_filename_mismatch_fails(tmp_path):
    ledger = tmp_path / "ledger"
    ledger.mkdir(parents=True)
    (ledger / "A.md").write_text(
        "---\nid: WRONG\nparent: \nrole: x\ndispatched-by: PM\nmodel: sonnet\n"
        "stage: s\nstatus: closed\nartifacts: []\nrtm: []\n"
        "created: 2026-05-16T00:00:00Z\nresponded: 2026-05-16T01:00:00Z\n---\n\n"
        "## REQUEST\nr\n\n## RESPONSE\nx\n\n## CHILD INDEX\n\n## NEXT\nCLOSE\n",
        encoding="utf-8",
    )
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "id" in (r.stdout + r.stderr).lower()


def test_no_ledger_dir_passes(tmp_path):
    # ledger 디렉토리 미존재 = 검증할 것 없음 = clean
    r = _run(tmp_path)
    assert r.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_ledger.py -q`
Expected: FAIL — `scripts/validate_ledger.py` 부재로 전부 에러

- [ ] **Step 3: Write minimal implementation**

`scripts/validate_ledger.py`:

```python
#!/usr/bin/env python3
"""Validate the projects/<name>/ledger/ delegation tree.

Checks (exit 1 on any failure, 0 if clean or no ledger dir):
  - frontmatter id == filename stem
  - parent referenced node file exists
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frontmatter import split_frontmatter, parse_frontmatter  # noqa: E402


def validate(project_root: Path) -> list[str]:
    errors: list[str] = []
    ledger = project_root / "ledger"
    if not ledger.is_dir():
        return errors
    nodes = sorted(p for p in ledger.glob("*.md") if p.name != "index.md")
    ids = {p.stem for p in nodes}
    for p in nodes:
        fm_text, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        fm = parse_frontmatter(fm_text) if fm_text else {}
        node_id = str(fm.get("id", "")).strip()
        if node_id != p.stem:
            errors.append(f"{p.name}: frontmatter id '{node_id}' != filename stem '{p.stem}'")
        parent = str(fm.get("parent", "") or "").strip()
        if parent and parent not in ids:
            errors.append(f"{p.name}: parent '{parent}' has no node file")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_ledger.py <project_root>", file=sys.stderr)
        return 2
    errs = validate(Path(argv[1]))
    for e in errs:
        print(f"LEDGER-ERROR: {e}", file=sys.stderr)
    if errs:
        print(f"validate_ledger: {len(errs)} error(s)", file=sys.stderr)
        return 1
    print("validate_ledger: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_validate_ledger.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_ledger.py tests/test_validate_ledger.py
git commit -m "feat(scripts): validate_ledger.py — ID/parent 무결성 (TDD)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 3: validate_ledger.py — 요청-응답 완결·status·CHILD INDEX·링크 검증 (TDD)

**Files:**
- Modify: `tests/test_validate_ledger.py` (append)
- Modify: `scripts/validate_ledger.py`

- [ ] **Step 1: Write the failing tests (append to test file)**

`tests/test_validate_ledger.py` 에 추가:

```python
def test_closed_node_with_empty_response_fails(tmp_path):
    ledger = tmp_path / "ledger"
    _node(tmp_path, ledger, "A", parent="", status="closed", response="   ")
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "response" in (r.stdout + r.stderr).lower()


def test_child_index_row_without_child_file_fails(tmp_path):
    ledger = tmp_path / "ledger"
    rows = "| A-1 | ledger/A-1.md | backend-developer | impl | closed |\n"
    _node(tmp_path, ledger, "A", parent="", children_rows=rows)
    # A-1.md 파일 없음
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "a-1" in (r.stdout + r.stderr).lower()


def test_child_index_consistent_passes(tmp_path):
    ledger = tmp_path / "ledger"
    rows = "| A-1 | ledger/A-1.md | backend-developer | impl | closed |\n"
    _node(tmp_path, ledger, "A", parent="", children_rows=rows)
    _node(tmp_path, ledger, "A-1", parent="A")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_link_missing_fails(tmp_path):
    ledger = tmp_path / "ledger"
    _node(tmp_path, ledger, "A", parent="",
          artifacts="[02_design/missing/CMP-001.md]")
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "cmp-001" in (r.stdout + r.stderr).lower()


def test_artifact_link_present_passes(tmp_path):
    (tmp_path / "02_design").mkdir(parents=True)
    (tmp_path / "02_design" / "CMP-001.md").write_text("x", encoding="utf-8")
    ledger = tmp_path / "ledger"
    _node(tmp_path, ledger, "A", parent="",
          artifacts="[02_design/CMP-001.md]")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 2: Run to verify new tests fail**

Run: `python3 -m pytest tests/test_validate_ledger.py -q`
Expected: 4 passed, 5 failed (신규 검증 미구현)

- [ ] **Step 3: Extend implementation**

`scripts/validate_ledger.py` 의 `validate()` 내 `for p in nodes:` 루프에 추가 (parent 체크 뒤):

```python
        body = p.read_text(encoding="utf-8")
        status = str(fm.get("status", "")).strip()

        def _section(name: str) -> str:
            marker = f"## {name}"
            if marker not in body:
                return ""
            seg = body.split(marker, 1)[1]
            for nxt in ("\n## ",):
                if nxt in seg:
                    seg = seg.split(nxt, 1)[0]
            # strip HTML comments
            out, depth = [], 0
            i = 0
            while i < len(seg):
                if seg[i:i+4] == "<!--":
                    depth += 1; i += 4; continue
                if seg[i:i+3] == "-->":
                    depth -= 1; i += 3; continue
                if depth == 0:
                    out.append(seg[i])
                i += 1
            return "".join(out).strip()

        if status == "closed" and not _section("RESPONSE"):
            errors.append(f"{p.name}: status=closed but RESPONSE section empty")

        # CHILD INDEX rows -> child file existence + back-parent
        for line in _section("CHILD INDEX").splitlines():
            line = line.strip()
            if not line.startswith("|") or "child id" in line or set(line) <= {"|", "-", " "}:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells or not cells[0]:
                continue
            cid = cells[0]
            if not (ledger / f"{cid}.md").is_file():
                errors.append(f"{p.name}: CHILD INDEX lists '{cid}' but ledger/{cid}.md missing")

        # artifact links exist
        raw = str(fm.get("artifacts", "[]"))
        items = [s.strip().strip("'\"") for s in raw.strip("[]").split(",") if s.strip()]
        for rel in items:
            if not (project_root / rel).exists():
                errors.append(f"{p.name}: artifacts link '{rel}' does not exist")
```

- [ ] **Step 4: Run test to verify all pass**

Run: `python3 -m pytest tests/test_validate_ledger.py -q`
Expected: PASS (9 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_ledger.py tests/test_validate_ledger.py
git commit -m "feat(scripts): validate_ledger 요청응답완결·CHILD INDEX·링크 검증

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 4: bootstrap_project.py — ledger/ 시드

**Files:**
- Modify: `scripts/bootstrap_project.py`
- Modify: `tests/test_bootstrap_project.py`

- [ ] **Step 1: Write the failing test (append to test_bootstrap_project.py)**

```python
def test_bootstrap_seeds_ledger(tmp_path):
    import subprocess, sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    proj = tmp_path / "demo"
    subprocess.run(
        [sys.executable, str(repo / "scripts" / "bootstrap_project.py"),
         str(proj), "--scale", "small"],
        check=True, capture_output=True, text=True,
    )
    assert (proj / "ledger").is_dir()
    assert (proj / "ledger" / "index.md").is_file()
    txt = (proj / "ledger" / "index.md").read_text(encoding="utf-8")
    assert "campaign id" in txt
```

(테스트 시그니처는 기존 `test_bootstrap_project.py` 의 호출 관행에 맞춰 조정 — 기존 테스트가 bootstrap 을 호출하는 헬퍼가 있으면 그 헬퍼 재사용.)

- [ ] **Step 2: Run to verify fail**

Run: `python3 -m pytest tests/test_bootstrap_project.py -q -k ledger`
Expected: FAIL — `ledger/` 미생성

- [ ] **Step 3: Implement seeding**

`scripts/bootstrap_project.py` 의 디렉토리 시드 로직(다른 단계 디렉토리를 만드는 부분)을 찾아 동일 패턴으로 추가:

```python
    # --- ledger 트리 시드 ---
    ledger_dir = project_root / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_index_tmpl = (
        REPO_ROOT / "templates" / "artifacts" / "ledger" / "index.md.tmpl"
    )
    ledger_index = ledger_dir / "index.md"
    if not ledger_index.exists():
        ledger_index.write_text(
            ledger_index_tmpl.read_text(encoding="utf-8"), encoding="utf-8"
        )
```

(`REPO_ROOT` / `project_root` 변수명은 해당 스크립트의 기존 명명에 맞춤. 기존 템플릿 복사 헬퍼가 있으면 그것을 사용.)

- [ ] **Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_bootstrap_project.py -q`
Expected: PASS (기존 + 신규 모두)

- [ ] **Step 5: Commit**

```bash
git add scripts/bootstrap_project.py tests/test_bootstrap_project.py
git commit -m "feat(bootstrap): projects/<name>/ledger/ 시드

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 2 — 호출 계약 정본 재작성 (call-playbook.md)

### Task 5: call-playbook §0 전면 교체 (단일 Agent 호출 계약 + ledger 프로토콜)

**Files:**
- Modify: `docs/call-playbook.md` (§0 전체, §4, §5 헤더)

- [ ] **Step 1: §0 을 아래 정본으로 교체**

기존 §0(트랙 정의·CLI 순서·`--add-dir` 범위)를 삭제하고 다음으로 대체:

```markdown
## 0. 개요 — 단일 호출 계약 (claude -p 폐기)

본 플랫폼은 `claude -p` subprocess 를 사용하지 않는다. "Track A" 개념은
폐기됐다. 모든 위임·저작·자문은 현 세션의 **Agent 툴 단일 primitive** 로
수행한다.

### 0-1. 저작 노드 호출

PM(유일한 오케스트레이터)이 Agent 툴로 dispatch:

- `subagent_type` = `general-purpose`
- `model` = 난이도 기반 (`opus` | `sonnet` | `haiku`)
- `prompt` = (1) `[PERSONA]` 블록에 `.claude/roles/<role>.md` 전문 inline
  주입 + self-attestation 지시, (2) 처리할 ledger 노드 파일 경로,
  (3) 출력 계약: 실산출물은 소유 경로에 직접 Write, 같은 ledger 노드의
  `## RESPONSE`/`## CHILD INDEX`/`## NEXT` 작성 + frontmatter `status`
  갱신, PM 반환은 **노드 경로 + status + NEXT 요약만**.

`effort` 는 Agent 툴 미노출 → model 티어 + 프롬프트 명시로 근사.

### 0-2. 순수 자문 호출 (읽기전용)

저작이 불필요한 분석·리뷰는 `subagent_type=<role>-<variant>`
(`.claude/agents/`, 툴셋 Read/Glob/Grep)로 dispatch. 더 저렴함.

### 0-3. PM 의 위치

PM 은 모든 hop 의 필수 버스이자 공유 파일 단독 scribe
(`project-state.md`·`RTM/**`·`escalations.md`·`agent-call-log.md`·
`rollback-history.md`). general-purpose 는 Agent 툴 미보유 → 자율 중첩
불가. PM 은 본문이 아닌 노드 경로·`NEXT:` 만 셔틀한다.

### 0-4. ledger 프로토콜

위임·통신은 `projects/<name>/ledger/` 계층 트리에 축적된다. 노드 ID =
Dewey(`A` → `A-1` → `A-1-1`). 노드 = 요청-응답 완결 단일 문서이며
실산출물(00~05 트리)·RTM-ID 를 링크하는 래퍼다. 스키마·소유 규칙은
spec `docs/superpowers/specs/2026-05-16-no-claude-p-ledger-redesign-
design.md` §2.
```

- [ ] **Step 2: §4 금지된 호출 갱신**

`## 4. 금지된 호출` 표에서 claude -p·`--agent`·CLI 순서 관련 행을 삭제하고 다음 행 추가:

```markdown
| `claude -p` subprocess 를 발생시키는 모든 호출 | 무과금·무claude-p 제약 (spec 2026-05-16) |
| general-purpose 노드가 공유 파일(§7-2)을 직접 수정 | 공유 파일은 PM 단독 scribe |
| 저작 노드가 본문을 PM 에 반환 (경로 아닌 본문 셔틀) | PM 컨텍스트 보호 — 경로·NEXT 만 |
```

- [ ] **Step 3: §5 헤더 주석 갱신**

`## 5. 역할별 호출 규칙 정본` 하위 각 역할의 "Track A 호출표"를
"NEXT 디스패치 선언표"로, "Track B 자문표"는 유지하되 머리말을
"순수 자문(읽기전용) 호출표"로 명칭 변경. 표의 *데이터 행 의미는 보존*
(시점→대상→목적→컨텍스트). 명칭만 계약에 맞게 정정.

- [ ] **Step 4: 검증**

Run: `python3 -m pytest tests/test_validate_agent.py -q`
Expected: 일부 FAIL 예상 (validate_agent 가 아직 구 표 명칭 기대) — Task 9 에서 정합. 지금은 call-playbook 자체 정합만 육안 확인.

- [ ] **Step 5: Commit**

```bash
git add docs/call-playbook.md
git commit -m "docs(call-playbook): §0 단일 Agent 호출 계약 + ledger 프로토콜 (claude -p 폐기)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 3 — roles·agents·PM 재작성

### Task 6: project-manager (SKILL + role) 재작성

**Files:**
- Modify: `.claude/skills/project-manager/SKILL.md`
- Modify: `.claude/roles/project-manager.md`

- [ ] **Step 1: project-manager.md 갱신**

다음 변경을 적용:
- frontmatter description 의 "never invoked as a claude -p subprocess" 는 유지(정확).
- `## Mission` / `## Responsibilities` 에서 "Track A dispatch via claude -p" 표현을 "Agent 툴로 general-purpose 노드 dispatch" 로 교체.
- 신규 `## Ledger 캠페인 관리` 섹션 추가 (정본 문구):

```markdown
## Ledger 캠페인 관리

너는 유일한 오케스트레이터이자 ledger 캠페인 관리자다.

1. 캠페인 개시: `projects/<name>/ledger/<root-id>.md` 를
   `templates/artifacts/ledger/node.md.tmpl` 로 생성, frontmatter +
   `## REQUEST` 채움, `ledger/index.md` 에 캠페인 행 추가.
2. dispatch: Agent 툴 `subagent_type=general-purpose`,
   prompt = [PERSONA: .claude/roles/<role>.md 전문] + 노드 경로 +
   출력 계약 (call-playbook §0-1).
3. 반환 수신: 노드 경로·status·NEXT 요약만 받는다 (본문 금지).
   노드 파일의 `## NEXT` 를 직접 파싱한다.
4. NEXT 실행: `DISPATCH <child-id> ...` → 자식 노드 생성(REQUEST=부모
   NEXT) 후 dispatch. `ESCALATE` → §Escalation. `CLOSE` → 부모 노드의
   CHILD INDEX status 셀 갱신.
5. 단계 종결 전 `python3 scripts/validate_ledger.py projects/<name>`
   호출. 비0 → 해당 노드 재dispatch, 종결 보류.
6. 공유 파일(§7-2)은 너만 수정한다. 노드 담당 general-purpose 는 자기
   소유 산출물·자기 ledger 노드만 쓴다.
```

- [ ] **Step 2: SKILL.md 갱신**

`SKILL.md` 본문의 claude -p / Track A CLI 인자 순서 관련 서술을 §0-1
호출 계약 요약으로 교체. "PM 은 Skill 전용·subprocess 아님" 서술은 유지.

- [ ] **Step 3: 검증**

Run: `python3 scripts/validate_agent.py .claude/roles/project-manager.md`
Expected: 현 validate_agent 기준 — 통과 또는 Task 9 에서 정합될 표 관련 경고만. claude -p 문자열 잔존 없는지 육안 확인:

Run: `grep -n "claude -p" .claude/roles/project-manager.md .claude/skills/project-manager/SKILL.md`
Expected: 매치 없음 (description 의 "never ... claude -p subprocess" 설명문은 제외 — 그 줄은 의도적 잔존)

- [ ] **Step 4: Commit**

```bash
git add .claude/roles/project-manager.md .claude/skills/project-manager/SKILL.md
git commit -m "feat(pm): PM = 범용 오케스트레이터 + ledger 캠페인 관리 (claude -p 제거)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 7: director·part-leader 3 역할 재작성 (NEXT 반환, spawn 안 함)

**Files:**
- Modify: `.claude/roles/application-director.md`
- Modify: `.claude/roles/infrastructure-director.md`
- Modify: `.claude/roles/part-leader.md`

- [ ] **Step 1: 각 파일 공통 변환 적용**

세 파일 각각:
- `## How You Invoke Sub-executions (Track A)` 섹션 제목을
  `## How You Declare Delegations (ledger NEXT)` 로 변경.
- 섹션 본문 머리말을 다음 정본으로 교체(표의 데이터 행은 보존):

```markdown
너는 하위를 직접 spawn 하지 않는다 (Agent 툴 미보유). 대신 너에게
배정된 ledger 노드의 `## RESPONSE` 를 작성하고, `## CHILD INDEX` 에
하위 노드를 선언하며, `## NEXT` 에 다음 기계가독 지시를 적는다:

  DISPATCH <child-id> role=<role> model=<opus|sonnet|haiku>

PM 이 이 NEXT 를 읽어 실제 dispatch 를 수행한다. 아래 표는 "어떤
시점에 어떤 역할에게 무엇을 위임하는가"의 정본이며, 그대로 NEXT
지시로 환원된다.
```

- `## How You Consult Advisors (Track B)` → `## How You Consult Advisors (읽기전용 자문)` 로 제목 변경, 본문에 "자문은 PM 을 경유한다: 노드 NEXT 에 `ESCALATE 자문요청 ...` 또는 RESPONSE 에 자문 필요를 명시하면 PM 이 읽기전용 자문 노드를 dispatch 한다" 1문단 추가.
- claude -p / `--add-dir` / CLI 순서 / "독립 최상위 세션" / "중첩 자유" 문구 전부 삭제.

- [ ] **Step 2: claude -p 잔존 확인**

Run: `grep -ln "claude -p\|--append-system-prompt\|--add-dir" .claude/roles/application-director.md .claude/roles/infrastructure-director.md .claude/roles/part-leader.md`
Expected: 매치 없음

- [ ] **Step 3: Commit**

```bash
git add .claude/roles/application-director.md .claude/roles/infrastructure-director.md .claude/roles/part-leader.md
git commit -m "feat(roles): director·part-leader = NEXT 위임 선언 (spawn 폐기)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 8: 나머지 17 역할 재작성 (저작 노드 계약)

**Files:** (수정 — 각각)
- `.claude/roles/application-architect.md`
- `.claude/roles/software-architect.md`
- `.claude/roles/technical-architect.md`
- `.claude/roles/data-modeler.md`
- `.claude/roles/database-administrator.md`
- `.claude/roles/designer.md`
- `.claude/roles/web-publisher.md`
- `.claude/roles/web-developer.md`
- `.claude/roles/backend-developer.md`
- `.claude/roles/batch-developer.md`
- `.claude/roles/infrastructure-engineer.md`
- `.claude/roles/security-specialist.md`
- `.claude/roles/policy-engineer.md`
- `.claude/roles/business-manager.md`
- `.claude/roles/quality-assurance.md`
- `.claude/roles/tester.md`
- `.claude/roles/audit-team.md`

- [ ] **Step 1: 공통 변환 규칙 적용 (17개 전부 동일 규칙)**

각 파일에:
1. claude -p / `--append-system-prompt` / `--add-dir` / CLI 순서 / "독립 최상위 세션" / "중첩" 관련 문장 전부 삭제.
2. `## Artifacts You Own` 바로 뒤에 다음 정본 섹션 삽입:

```markdown
## 호출·산출 계약 (ledger)

너는 PM 이 Agent 툴로 `subagent_type=general-purpose` + 너의 페르소나
프롬프트 주입으로 dispatch 한다. 처리 절차:

1. 배정된 ledger 노드 파일의 `## REQUEST` 와 연결 산출물을 Read.
2. 너의 실산출물을 `## Artifacts You Own` 의 소유 경로에 직접 Write
   (공유 파일 §7-2 은 절대 수정 금지 — 필요 시 RESPONSE 에 명시,
   PM 이 반영).
3. 같은 ledger 노드의 `## RESPONSE`(산출물은 링크만, 본문 복제 금지),
   필요 시 `## CHILD INDEX`, `## NEXT`(CLOSE 또는 ESCALATE) 작성,
   frontmatter `status`·`responded`·`artifacts`·`rtm` 갱신.
4. PM 에 반환하는 최종 메시지는 "노드 경로 + status + NEXT 요약" 한
   문단만. 산출물 본문을 반환에 포함하지 않는다.
5. 페르소나 self-attestation: 응답 첫 줄에 `ROLE: <# Role 한국어명>`.
```

3. director/part-leader 가 아닌 역할이므로 위임 선언 섹션은 추가하지 않음. (audit-team 은 추가 단서 — Step 2)

- [ ] **Step 2: audit-team 특례**

`.claude/roles/audit-team.md` 는 위 공통 + 다음:
- 산출물 소유 경로 = `99_audit/<cycle>-audit/` 한정 유지.
- "별도 git worktree 에서 Track A 실행" → "PM 이 `scripts/run_audit.sh` 로 worktree 격리 후 general-purpose+감리 페르소나로 dispatch" 로 교체.
- 격리 원칙(다른 영역 수정 금지) 문구 유지.

- [ ] **Step 3: 잔존 확인**

Run:
```bash
grep -ln "claude -p\|--append-system-prompt" .claude/roles/*.md | grep -v project-manager
```
Expected: 매치 없음 (project-manager.md 의 의도적 설명문만 예외)

- [ ] **Step 4: Commit**

```bash
git add .claude/roles/
git commit -m "feat(roles): 17 역할 ledger 저작 계약 적용 (claude -p 제거)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 9: .claude/agents shell + derive_dynamic_agents.py 정합

**Files:**
- Modify: `scripts/derive_dynamic_agents.py`
- Modify: `tests/test_derive_dynamic_agents.py`
- Regenerate: `.claude/agents/*.md` (46)

- [ ] **Step 1: 테스트 갱신**

`tests/test_derive_dynamic_agents.py` 에서 생성 body 텍스트를 검사하는 단언을, 새 body 문구(읽기전용 자문 전용 + 저작은 general-purpose 경로 안내)에 맞게 수정. 신규 단언:

```python
def test_agent_shell_states_readonly_advisory(tmp_path_factory):
    # 재생성 후 임의 dynamic shell 1개 body 에 안내 문구 존재
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    sh = (repo / ".claude" / "agents" / "backend-developer-sonnet.md").read_text(encoding="utf-8")
    assert "읽기 전용" in sh
    assert "저작이 필요" in sh  # general-purpose 경로 안내 존재
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 -m pytest tests/test_derive_dynamic_agents.py -q`
Expected: FAIL (새 문구 부재)

- [ ] **Step 3: derive_dynamic_agents.py body 텍스트 갱신**

shell body 생성 문자열을 다음 정본으로 교체:

```
# Role: {korean_name} (읽기 전용 자문 서브에이전트 껍데기)

이 파일은 Agent 툴 subagent_type 해석용 껍데기입니다. 호출되면 먼저
`Read` 로 `.claude/roles/{role}.md` 를 읽고 그 역할 관점으로 답하세요.

자문 규칙:
- 읽기 전용 분석·평가·조언만 수행 (Write/Edit/Bash 미보유).
- **저작이 필요한 작업이면** 그 사실을 응답에 명시하고, 상위(PM)에게
  general-purpose + 페르소나 주입 경로(call-playbook §0-1)로의 dispatch
  를 권고하세요. 이 껍데기로는 산출물·ledger 노드를 쓸 수 없습니다.
- 응답은 한국어로 간결하게.
```

- [ ] **Step 4: 재생성·검증**

Run:
```bash
python3 scripts/derive_dynamic_agents.py
python3 -m pytest tests/test_derive_dynamic_agents.py -q
```
Expected: PASS, `.claude/agents/` 46개 idempotent 재생성

- [ ] **Step 5: Commit**

```bash
git add scripts/derive_dynamic_agents.py tests/test_derive_dynamic_agents.py .claude/agents/
git commit -m "feat(agents): shell body = 읽기전용 자문 + 저작은 general-purpose 경로 안내

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 4 — drift-guard 재작성 (validate_agent.py)

### Task 10: validate_agent.py — claude -p 금지 + ledger 계약 검증

**Files:**
- Modify: `scripts/validate_agent.py`
- Modify: `tests/test_validate_agent.py`

- [ ] **Step 1: 신규 실패 테스트 추가**

`tests/test_validate_agent.py` 에 추가:

```python
def test_role_with_claude_p_is_rejected(tmp_path):
    import subprocess, sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    bad = tmp_path / "bad-role.md"
    bad.write_text(
        "---\nname: bad-role\ndescription: x\n---\n\n# Role: 테스트\n\n"
        "## Mission\nx\n\n호출: claude -p --append-system-prompt ...\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [sys.executable, str(repo / "scripts" / "validate_agent.py"), str(bad)],
        capture_output=True, text=True,
    )
    assert r.returncode == 1
    assert "claude -p" in (r.stdout + r.stderr)


def test_all_real_roles_have_no_claude_p(tmp_path):
    import subprocess, sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [sys.executable, str(repo / "scripts" / "validate_agent.py"), "--all"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 -m pytest tests/test_validate_agent.py -q -k claude_p`
Expected: `test_role_with_claude_p_is_rejected` FAIL (검사 미구현)

- [ ] **Step 3: validate_agent.py 에 검사 추가**

기존 role 검증 함수(파일 단위 검사 루프) 내에 추가:

```python
    # claude -p 금지 (project-manager.md 의 description 설명문만 예외)
    for ln_no, line in enumerate(text.splitlines(), 1):
        if "claude -p" in line or "--append-system-prompt" in line:
            if path.name == "project-manager.md" and "never" in line.lower():
                continue
            errors.append(
                f"{path.name}:{ln_no}: forbidden 'claude -p' invocation "
                f"(spec 2026-05-16: claude -p 폐기)"
            )
```

기존 §5 Track A 표 ↔ role 표 대조 로직은 표 *제목*이 바뀌었으므로
(Task 5/7), 대조 키를 신 제목(`How You Declare Delegations`/`호출·산출
계약`)으로 갱신하거나, 해당 표-대조 검증이 과도하면 "claude -p 부재 +
ledger 계약 섹션 존재" 검증으로 단순화. 기존 통과 테스트가 깨지면 그
테스트의 기대도 신 계약에 맞게 갱신 (drift-guard 의미 보존: role 이
신 계약을 따르는지 검증).

- [ ] **Step 4: 전체 검증**

Run:
```bash
python3 scripts/validate_agent.py --all
python3 -m pytest tests/test_validate_agent.py -q
```
Expected: `validate_agent --all` exit 0, 모든 테스트 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_agent.py tests/test_validate_agent.py
git commit -m "feat(drift-guard): claude -p 금지 + ledger 계약 검증으로 재작성

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 5 — CLAUDE.md·run_audit.sh·stage-gates 정합

### Task 11: 루트 CLAUDE.md 재작성

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 섹션 교체**

- `## 호출 트랙 (spec §1-2, call-playbook §0)` 표 전체를 §0-1/0-2/0-3 요약(단일 Agent 호출 계약)으로 교체. "Track A CLI 인자 순서" 하위 절 삭제.
- `## --add-dir 범위 한정 규칙 (call-playbook §0)` 섹션 전체 삭제.
- `## 공유 파일 단독 수정 규칙 (spec §7-2)` 은 유지하되 "Track A subprocess 는 직접 수정 금지" → "general-purpose 노드는 직접 수정 금지" 로 문구 정정.
- 신규 섹션 추가: `## Ledger 위임·통신 체계 (spec 2026-05-16)` — ledger 트리·노드 스키마 1문단·`scripts/validate_ledger.py` 게이트 안내.
- `## 테스트·검증` 의 "validate_agent.py --all (기준 66/66)" 유지 + "validate_ledger.py (프로젝트 작업 시)" 추가.

- [ ] **Step 2: 잔존 확인**

Run: `grep -n "claude -p\|--add-dir\|--append-system-prompt\|Track A" CLAUDE.md`
Expected: 매치 없음 (또는 "Track A 폐기" 같은 이력 서술만)

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE): claude -p·Track A·--add-dir 제거, ledger 체계 신설

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 12: run_audit.sh — claude -p 제거 (worktree 셋업만)

**Files:**
- Modify: `scripts/run_audit.sh`
- Modify: `tests/test_run_audit.sh`

- [ ] **Step 1: 테스트 기대 갱신**

`tests/test_run_audit.sh` 에서 `claude -p` 호출·CLI 인자 순서를 검사하던 케이스를 다음으로 교체: (a) worktree 가 생성되는지, (b) 프로젝트가 복사되는지, (c) 스크립트가 `claude -p` 를 더 이상 호출하지 않는지(`grep -q 'claude -p' scripts/run_audit.sh` 가 매치 없어야 함), (d) 감리 dispatch 안내(PM 이 general-purpose+감리 페르소나로 dispatch)를 stdout 으로 출력하는지.

- [ ] **Step 2: Run to verify fail**

Run: `bash tests/test_run_audit.sh` (또는 pytest 래퍼가 있으면 `python3 -m pytest -q -k run_audit`)
Expected: FAIL (아직 claude -p 호출 잔존)

- [ ] **Step 3: run_audit.sh 재작성**

claude -p 호출 블록(약 115–121행)과 CLI 인자 순서 주석을 삭제. 스크립트 책무를 다음으로 한정:
1. 인수 검증 (PROJECT, CYCLE)
2. git worktree 생성 (`<cur>-audit-<cycle>-<timestamp>`)
3. 프로젝트 복사
4. stdout 에 PM 용 안내 출력:

```bash
cat <<EOF
[run_audit] worktree 준비 완료: $WT_PATH
다음을 PM 세션에서 수행하라:
  Agent 툴 subagent_type=general-purpose, model=sonnet
  prompt = [PERSONA: .claude/roles/audit-team.md 전문]
         + 감리 대상 worktree 경로: $WT_PATH/projects/$PROJECT
         + 산출물: $WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit/
         + ledger 노드 경로(있으면)
감리 완료 후 결과를 main 트리로 복사: (스크립트 안내 그대로)
EOF
```
5. 결과 복사 로직(worktree → main `99_audit/`)은 유지.

- [ ] **Step 4: 검증**

Run:
```bash
grep -n "claude -p" scripts/run_audit.sh; echo "exit: $?"
bash tests/test_run_audit.sh
```
Expected: grep 매치 없음(exit 1), 테스트 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/run_audit.sh tests/test_run_audit.sh
git commit -m "feat(run_audit): claude -p 제거, worktree 셋업 + PM dispatch 안내

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 13: stage-gates.md — Track A 표현 정정 + ledger-completeness 게이트

**Files:**
- Modify: `templates/stage-gates.md`

- [ ] **Step 1: 표현 정정**

전 단계(00~05)에서 "Track A dispatch"/"claude -p"/"`--add-dir`" 표현을 "PM 이 general-purpose 노드 dispatch (call-playbook §0-1)" 로 정정.

- [ ] **Step 2: ledger-completeness 게이트 추가**

각 단계(01~05) 종결 조건에 항목 추가:

```markdown
- Ledger-completeness gate: `python3 scripts/validate_ledger.py projects/<name>`
  exit 0. 이 단계에서 dispatch 된 모든 ledger 노드가 status=closed 이고,
  CHILD INDEX ↔ 자식 파일 정합, artifacts/rtm 링크 존재가 검증되어야
  단계 종결 가능.
```

- [ ] **Step 3: 검증**

Run: `grep -n "claude -p\|Track A dispatch\|--add-dir" templates/stage-gates.md`
Expected: 매치 없음

- [ ] **Step 4: Commit**

```bash
git add templates/stage-gates.md
git commit -m "docs(stage-gates): Track A 표현 정정 + ledger-completeness 게이트

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 6 — 폐기물 제거 + 전체 회귀

### Task 14: meta6 스크립트 삭제

**Files:**
- Delete: `scripts/meta6_parallel_write_repeat.sh`

- [ ] **Step 1: 참조 부재 재확인**

Run:
```bash
grep -rn "meta6_parallel_write_repeat" --include="*.py" --include="*.sh" --include="*.md" . | grep -v "docs/superpowers/specs/2026-05-16" | grep -v "docs/superpowers/plans/2026-05-16"
```
Expected: 매치 없음 (spec/plan 의 이력 언급만 제외하면 참조 없음)

- [ ] **Step 2: 삭제**

```bash
git rm scripts/meta6_parallel_write_repeat.sh
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(scripts): meta6_parallel_write_repeat.sh 삭제 (병렬 writer race 시나리오 소멸)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 15: 전체 회귀 + 미니 ledger 스모크

**Files:** (없음 — 검증 전용)

- [ ] **Step 1: 전체 pytest**

Run: `python3 -m pytest -q`
Expected: 신규 `test_validate_ledger.py`(9) 포함 전부 PASS. 기존 153 + 신규. 실패 시 근본 원인 수정 후 재실행 (`--no-verify` 우회 금지).

- [ ] **Step 2: drift-guard**

Run: `python3 scripts/validate_agent.py --all`
Expected: exit 0

- [ ] **Step 3: 전 저장소 claude -p 잔존 스캔**

Run:
```bash
grep -rn "claude -p\|--append-system-prompt" --include="*.md" --include="*.py" --include="*.sh" \
  .claude scripts templates CLAUDE.md docs/call-playbook.md \
  | grep -vi "never.*claude -p subprocess" \
  | grep -v "docs/superpowers/specs" | grep -v "docs/superpowers/plans" | grep -v "docs/superpowers/findings"
```
Expected: 매치 없음 (이력 문서·PM 설명문만 예외)

- [ ] **Step 4: 미니 ledger 스모크**

```bash
TMP=$(mktemp -d)
python3 scripts/bootstrap_project.py "$TMP/smoke" --scale small
cp templates/artifacts/ledger/node.md.tmpl "$TMP/smoke/ledger/A.md"
# A.md 를 closed·완결 노드로 채움 (id:A, parent 공백, REQUEST/RESPONSE 채움, NEXT: CLOSE)
python3 - "$TMP/smoke/ledger/A.md" <<'PY'
import sys, pathlib, datetime
p = pathlib.Path(sys.argv[1])
now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
p.write_text(
 f"---\nid: A\nparent: \nrole: backend-developer\ndispatched-by: PM\n"
 f"model: sonnet\nstage: 02_design\nstatus: closed\nartifacts: []\nrtm: []\n"
 f"created: {now}\nresponded: {now}\n---\n\n## REQUEST\nseed\n\n"
 f"## RESPONSE\ndone\n\n## CHILD INDEX\n\n## NEXT\nCLOSE\n", encoding="utf-8")
PY
python3 scripts/validate_ledger.py "$TMP/smoke"; echo "ledger exit: $?"
rm -rf "$TMP"
```
Expected: `validate_ledger: clean`, `ledger exit: 0`

- [ ] **Step 5: 최종 커밋 (검증 산출물 없으면 생략)**

검증만 수행했고 변경 파일이 없으면 커밋 불필요. 회귀 중 수정이 발생했으면:

```bash
git add -A
git commit -m "test: 전체 회귀 통과 + 미니 ledger 스모크 (claude -p 재설계 완료)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Self-Review (작성자 체크 — 완료)

**1. Spec coverage:**
- §1-1 폐기 목록 → Task 14(meta6), Task 5/7/8/11/12/13(claude -p·CLI·--add-dir 제거) ✓
- §1-2 단일 호출 계약 → Task 5(call-playbook §0), Task 6/7/8(roles) ✓
- §1-3 역할에이전트 읽기전용 존속 → Task 9 ✓
- §1-4 PM 역할 → Task 6 ✓
- §2 ledger 모델(스키마·소유·컨텍스트) → Task 1(템플릿), Task 2/3(validate_ledger) ✓
- §3 위계 흐름 → Task 6(PM ledger 관리), Task 7(NEXT 선언) ✓
- §4 재작성 표면 → Task 5/6/7/8/9/10/11/12/13 ✓
- §4-3 신규 validate_ledger.py → Task 2/3 ✓
- §4 bootstrap ledger 시드 → Task 4 ✓
- §5/§6 오류·리스크 → Task 0(persona probe 게이트), validate_ledger 재dispatch 경로 ✓
- §6-4 마이그레이션·이력 보존 → 삭제 대상에서 findings/spec 제외 명시 ✓

**2. Placeholder scan:** 코드 스텝은 실제 코드 제공. 역할 17개는 단일 정본 변환 규칙 + 전수 파일 열거(노이즈 회피 위해 동일 규칙 1회 명시). "TBD/TODO" 없음.

**3. Type consistency:** `validate_ledger.py` 의 `validate()/main()` 시그니처가 Task 2↔3 일관. 템플릿 섹션명(`## REQUEST/RESPONSE/CHILD INDEX/NEXT`)이 Task 1↔2↔3↔6↔7↔8 전반 일관. `status` 값 집합(pending/in-progress/responded/closed) 일관.

**주의:** Task 4·9·10·12 는 기존 스크립트/테스트의 실제 함수·헬퍼 명명에 맞춰 시그니처를 조정해야 함(plan 은 패턴·정본 텍스트를 규정, 변수명은 해당 파일 기존 관행 준수). 기존 통과 테스트가 신 계약과 충돌하면 그 테스트의 기대를 신 계약에 맞게 갱신하되 drift-guard 의미는 보존.
