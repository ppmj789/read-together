# AI SI Project Team

Claude Code multi-subagent system that replicates an enterprise SI
(System Integration) project execution organization.

- Spec: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`
  (+ Amendment `2026-04-18-amendment-01-claude-p-invocation.md`)
- Build plan: `docs/superpowers/plans/2026-04-17-ai-si-team-build.md`
- Phase 7 E2E: `docs/superpowers/plans/2026-04-18-phase7-e2e.md`
- Call matrix: `docs/call-playbook.md` — per-role Track A/B invocation rules (drift-guarded)

## Quick Start

1. Bootstrap a project directory (see next section).
2. Drop your statement-of-work into
   `projects/<name>/00_kickoff/statement-of-work.md`.
3. Launch a Claude Code session from the repo root — `SessionStart` hook
   auto-loads the `project-manager` Skill; the session itself is the PM.
4. Talk to PM. PM is the single contact point; it orchestrates
   everything else via **Track A** (Bash `claude -p` subprocesses) and
   **Track B** (Agent-tool subagents).
5. At each stage gate PM reports to you and waits for your approval.
6. When an audit is due, PM runs `scripts/run_audit.sh` which spins up
   the `audit-team` in an isolated git worktree.

## Bootstrapping a new project

```bash
python3 scripts/bootstrap_project.py <project-name> --scale small|large
```

Creates `projects/<project-name>/` with the full v2 hierarchical tree:

- per-stage directories with `index.md` + `<ID>.md` children
- `project-plan/` directory (index + overview/scope/organization/schedule/budget/wbs children)
- `RTM/` directory (`index.md` + `by-stage/*.md` + `_archived/`; `by-part/` when `scale == large`)
- top-level logs: `project-state.md`, `agent-call-log.md`, `escalations.md`,
  `00_kickoff/statement-of-work.md`, `00_kickoff/rollback-history.md`
- `99_audit/` skeleton for design-audit + closing-audit (+ analysis-audit when `large`)
- `index.md` `child-count` fields auto-synced to actual contents

**Project artifacts are gitignored** (`projects/*/` in `.gitignore`).
The platform is what this repo versions; a specific project's output is
not. Run the generator on a fresh checkout to regenerate the skeleton.

### Using a separate git repo per project (optional)

After PM declares the project `closed`, push the artifacts to a client
repo with a nested `git init` — the parent `.gitignore` keeps the two
histories independent:

```bash
cd projects/<name>
git init && git add -A && git commit -m "initial delivery"
git remote add origin <client-repo-url>
git push -u origin master
```

## Invocation tracks (spec §1-2)

| Track | Command | Purpose | Tool set |
|-------|---------|---------|----------|
| **Track A** | `claude -p --dangerously-skip-permissions [--add-dir <p>] --append-system-prompt "$(cat .claude/roles/<role>.md)" --model <m> --effort <e> ...` | Primary authoring · nested dispatch · advisory dispatch | Full (Read/Write/Edit/Glob/Grep/Bash/Agent) |
| **Track B** | `Agent` tool with `subagent_type=<agent-shell-name>` | Advisory / review / analysis only | `Read, Glob, Grep` (read-only, runtime-fixed) |
| **Skill** | `project-manager` Skill loaded by SessionStart hook | PM persona on the user-facing top-level session | Inherits session tools (Opus · xhigh fixed) |

> **CLI argument order is load-bearing**: `--add-dir` must precede
> `--append-system-prompt`. The reverse order silently consumes the
> positional prompt as the `--add-dir` value and aborts the session
> with `Error: Input must be provided` (Phase 7 Task 6 finding).
> `scripts/run_audit.sh` enforces the correct order automatically.

## Agent Catalog

**Fixed-model roles (7)**
- `project-manager` — Opus · xhigh · **Skill only** (sessionstart-loaded, never `claude -p`)
- `application-director` · `infrastructure-director` — Opus · xhigh
- `business-manager` · `quality-assurance` · `tester` — Sonnet · xhigh
- `audit-team` — Sonnet · xhigh · invoked only via `scripts/run_audit.sh`

**Dynamic-model roles (13 × opus/sonnet/haiku = 39 shells)**
- `application-architect` (AA), `software-architect` (SWA),
  `technical-architect` (TA), `data-modeler`
- `part-leader` (activated only when `scale == large`)
- `backend-developer`, `batch-developer`, `web-developer`,
  `web-publisher`, `designer`
- `database-administrator` (DBA), `security-specialist`,
  `infrastructure-engineer`

The upstream caller picks the variant based on the task's difficulty
(spec §2-3 difficulty guide). Never dictate a model more than one level
down the delegation chain.

Source of truth layout:
- `.claude/roles/<role>.md` — single-source persona (one per role, no model suffix)
- `.claude/agents/<role>-<variant>.md` — Track B shells derived from roles
- `.claude/skills/project-manager/SKILL.md` — PM skill shell

## Artifact Templates

See `templates/artifacts/` for stage and role deliverable skeletons:

- `_common/` — `index.md.tmpl` + `child.md.tmpl` (every hierarchical area uses these)
- `change-requests/` — `cr-request` / `cr-impact-analysis` / `cr-decision` / `cr-action-result` / `index`
- `audit/` — `audit-plan` + `finding` (with `pm-classification` A/B/C/D field)
- `rtm/` — `index` + `by-stage` templates
- top-level logs — `project-state` / `agent-call-log` / `escalations` / `review-meeting` / `rollback-history` / `statement-of-work`

Every template carries the required frontmatter schema; violations are
caught by the validators below.

## Stage Gates

`templates/stage-gates.md` lists, per stage, the mandatory artifacts,
reviews, advisory gates (`business-manager` + `quality-assurance`
consultations logged in `agent-call-log.md`), RTM population, audit,
hierarchy gate, and approval gate.

The "Hierarchy gate" line requires `validate_artifact_hierarchy.py` to
exit 0 and — when back-references changed — `sync_back_references.py`
to report clean.

## Validation & helper scripts

```bash
# Agent-frontmatter schema + role/playbook drift-guard
python3 scripts/validate_agent.py --all

# v2 hierarchy: index.md presence, bidirectional deps, 3-hop depth,
# group-ID references, orphan advisory, audit-advisory relaxation
python3 scripts/validate_artifact_hierarchy.py <project>

# Frontmatter completeness (id/title/owner/depends-on/referenced-by + version regex + duplicate-key detection)
python3 scripts/check_frontmatter.py <project>

# Change-request cycle completeness (CR-<seq>/ five files, schema per template)
python3 scripts/validate_cr.py <project>

# Sync referenced-by back-refs from depends-on declarations
python3 scripts/sync_back_references.py <project>

# Sync index.md child-count fields to reality (run automatically by bootstrap)
python3 scripts/sync_child_count.py <project>            # write
python3 scripts/sync_child_count.py <project> --check    # dry-run, exit 1 on drift

# Transition FIND-*.md status raised → resolved for Type-A classifications
python3 scripts/close_audit_findings.py <project> <cycle-id>

# Bootstrap new project (auto-syncs child-count on exit)
python3 scripts/bootstrap_project.py <name> --scale small|large

# Regenerate the 39 dynamic-variant agent shells from role templates
python3 scripts/derive_dynamic_agents.py

# Audit launcher (creates worktree + enforces CLI order + 3-layer output-path defense)
scripts/run_audit.sh <project> <cycle-id> <prompt-file>

# Rollback helper (MOVE vs SNAPSHOT modes — §4-3)
scripts/execute_rollback.sh <project> <stage> <mode>

# Run the full test suite
python3 -m pytest -q
```

At time of writing: **149 tests passing · `validate_agent --all` 66/66 clean**.

## Phase 7 E2E outcome (2026-04-19)

Phase 7 ran the full `book-mgmt-api` sample project end-to-end against
this system, audited it twice (D-AUDIT-1 pass, C-AUDIT-1 pass), then
ran five meta-tests (Tasks 14-18). 42 systemic improvements were
identified and merged to master across three waves:

- 14 from the Phase 7 residual findings list (`#1`–`#19`)
- 20 from a raw-log / review / artifact meta-data scan (`N1`–`N20`)
- 8 from the Part B meta-tests (`C-18-1/2`, `C-17-1/2`, `C-14-1/2/3`, `C-18-3`)

Notable structural additions:
- **Shared-file single-writer rule** (spec §7-2) — `project-state.md`,
  `RTM/`, `agent-call-log.md`, `escalations.md`, and directory index
  files are PM-only; subprocesses escalate instead of editing directly.
- **`--add-dir` scope limit** (call-playbook §0) — subprocesses receive
  only their own authored directory, eliminating parallel-write races.
- **Rollback MOVE/SNAPSHOT modes** (`scripts/execute_rollback.sh`).
- **Audit finding classification** A/B/C/D on the `pm-classification`
  frontmatter field; type-A transitions to `resolved` via
  `scripts/close_audit_findings.py`.
- **Nested Track A depth guard** — 4-level chain recommended; deeper
  chains must pass a `condensed-brief.md` (95 % cache-hit is not
  enough to preserve context past 4 levels).

Full report: `docs/superpowers/findings/2026-04-18-phase7-findings.md`
and `docs/superpowers/findings/2026-04-19-phase7-part-b-findings.md`.

## Role realignment (2026-05-02)

한국 SI 통념 정합을 위해 두 차례 페르소나·디렉토리·dispatch 재정비를 진행
(2 × 5-commit 시리즈). 현재 master 는 다음 흐름이 반영된 상태:

**아키텍트 3종 분담** (`02_design/architecture/`) — application-architect 가
`application/` (overview·domain-model·business-flow·components/CMP-* + ADR)
을, software-architect 가 같은 application/ 안에 code-architecture·module-
patterns·interface-policy + ADR 을, technical-architect 가 좁은 `technology/`
(overview·middleware·deployment-topology·nfr-technology + ADR) 을 저작.
data-modeler 는 `data/`, security-specialist 는 `security/`. Clean
Architecture 기본 채택 ADR 은 SWA 단독 책임. validate_artifact_hierarchy.py
가 subdomain 별 owner 정합을 검증한다.

**웹 직군 흐름** (`02_design/design-system/`, screens, src/web/) —
designer 가 `design-system/` (overview·colors·typography·layout·logo-brand)
단독 저작, web-developer 가 `screens/SCN-*.md` 단독 저작 (한국 SI 통념),
web-publisher 는 02_design 저작 책임 없이 03_implementation 단계에서
SCN+design-system 을 입력받아 `src/web/` HTML 마크업·CSS 껍데기를 단독
저작 (web-developer 의 동적 기능·API 연동 추가 전 선행). validator 가
design-system owner=designer 정합을 검증한다.

상세는 `git log --oneline 3c23e5e..HEAD` 의 `feat(roles)` /
`feat(architecture)` / `feat(design-system)` / `feat(directors)` /
`feat(validator)` 커밋 시리즈를 참고.

## Exception-handling ratio policy (2:8 법칙, 2026-05-02)

단위기능 차원에서 **정상 ≤ 2 : 비정상 예외 처리 ≥ 8** 비율을 자연스럽게
도출하도록, 단계별 산출물 형태에 맞춰 강제하는 통합 정책을 신설.
SSOT: `docs/exception-handling-ratio-policy.md`.

| 단계 | 강제 강도 | 핵심 메커니즘 |
|------|---------|----------|
| 요구사항 | 약 (발견) | 7 Failure Categories 카테고리 커버리지 (AA RQ enumerate) |
| 설계 | 중 (메커니즘) | PRG/IF/SCN/BATCH 본문 FMEA 표 의무 + 3 불변식 (Tree·One-handler·Guard chain) |
| 단위테스트 | **강 (숫자)** | UT-*.md frontmatter `variant-happy-count / variant-count ≤ 0.3`, `variant-exception-count / variant-count ≥ 0.7`, `validate_artifact_hierarchy.py` 가 자동 검증 |
| 구현 | 간접 | TDD 자연 도출 + One RPC = one handler + precondition guard chain + 코드 헤더 카테고리 명시 |
| 통합테스트 | 기존 | Variant Multiplication |

비율 강제의 진앙지는 단위테스트 설계 — 요구사항 단계에 숫자를 들이대면
"가짜 예외" 양산. parent-variant 트리 구조 (1 UT = 1 PRG = N variants)
로 산출물 폭증을 차단하면서 enumeration 은 보존.
