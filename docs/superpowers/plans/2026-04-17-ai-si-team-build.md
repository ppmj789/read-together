# AI SI Project Team — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code multi-subagent system that replicates an enterprise SI project execution organization (19 roles, 46 agent files), with all scaffolding (artifact templates, RTM, project state, stage-gate validation, git tracking) needed to run a real V-Model waterfall project from kickoff through deployment.

**Architecture:** Traditional Claude Code subagents (`.claude/agents/*.md`) with 3-tier hierarchical calling (Agent tool). Fixed-model agents for leadership/fixed roles (7 files). Dynamic-model roles (13 roles × 3 model tiers = 39 files) generated from single-source templates. Audit team in an isolated namespace with read-only+audit-dir-write constraints. File-system-based collaboration (Markdown artifacts with YAML frontmatter carrying IDs, `depends-on`, `reviewed-by`).

**Tech Stack:** Markdown (YAML frontmatter), Bash, Python 3 (validator/derivation scripts), git, Claude Code (agent runtime).

**Spec:** `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`

**Scope of this plan:** Phases 1-6 of spec §9 (skeleton through project-state/RTM templates) plus a smoke test. Phase 7 (sample project E2E) and Phase 8 (meta-tests 2-6) will be tracked in a follow-up plan once this one is complete and the user has exercised the system.

---

## Plan Notes

1. **Working directory:** `/home/earth/ai_team/`.
2. **git:** Not yet initialized. Task 1 initializes it; every task ends with a commit.
3. **Agent prompt language:** Agent system prompts are written in **English** (better Claude performance on English system prompts). User-facing strings that the agent produces (e.g., reports) should be in **Korean**. Each agent's prompt includes an explicit instruction: "Output all user-facing text in Korean."
4. **`effort` field:** The spec mandates `effort: xhigh` in every agent's frontmatter. Claude Code may or may not honor this field at runtime — include it as our project convention regardless. If Claude Code ignores unknown frontmatter fields, the file still loads.
5. **Dry-run validation:** Each agent file gets validated by the validator script (Task 3) before commit. No agent merges without passing validation.

---

## File Structure After Plan Completion

```
/home/earth/ai_team/
├─ .git/                                    (Task 1)
├─ .gitignore                                (Task 1)
├─ .claude/
│  └─ agents/
│     ├─ project-manager.md                  (Task 5)
│     ├─ application-director.md             (Task 6)
│     ├─ infrastructure-director.md          (Task 7)
│     ├─ business-manager.md                 (Task 8)
│     ├─ quality-assurance.md                (Task 9)
│     ├─ tester.md                           (Task 10)
│     ├─ audit/
│     │  └─ audit-team.md                    (Task 11)
│     ├─ application-architect-opus.md       (Task 25 batch)
│     ├─ application-architect-sonnet.md     (Task 25 batch)
│     ├─ application-architect-haiku.md      (Task 25 batch)
│     ├─ ... (36 more derived dynamic agents)
│     └─ templates/
│        ├─ stage-gates.md                   (Task 4)
│        ├─ agent-frontmatter.schema.yml     (Task 3)
│        ├─ application-architect.md.tmpl    (Task 12)
│        ├─ software-architect.md.tmpl       (Task 13)
│        ├─ technical-architect.md.tmpl      (Task 14)
│        ├─ data-modeler.md.tmpl             (Task 15)
│        ├─ part-leader.md.tmpl              (Task 16)
│        ├─ backend-developer.md.tmpl        (Task 17)
│        ├─ batch-developer.md.tmpl          (Task 18)
│        ├─ web-developer.md.tmpl            (Task 19)
│        ├─ web-publisher.md.tmpl            (Task 20)
│        ├─ designer.md.tmpl                 (Task 21)
│        ├─ database-administrator.md.tmpl   (Task 22)
│        ├─ security-specialist.md.tmpl      (Task 23)
│        ├─ infrastructure-engineer.md.tmpl  (Task 24)
│        └─ artifacts/
│           ├─ requirements.md.tmpl          (Task 26)
│           ├─ as-is-analysis.md.tmpl        (Task 26)
│           ├─ to-be-workflow.md.tmpl        (Task 26)
│           ├─ uat-test-cases.md.tmpl        (Task 26)
│           ├─ integration-test-cases.md.tmpl (Task 26)
│           ├─ architecture.md.tmpl          (Task 27)
│           ├─ db-logical.md.tmpl            (Task 27)
│           ├─ db-physical.md.tmpl           (Task 27)
│           ├─ screen-spec.md.tmpl           (Task 27)
│           ├─ interface-spec.md.tmpl        (Task 27)
│           ├─ program-list.md.tmpl          (Task 27)
│           ├─ unit-test-cases.md.tmpl       (Task 27)
│           ├─ security-review.md.tmpl       (Task 27)
│           ├─ unit-test-results.md.tmpl     (Task 28)
│           ├─ integration-test-results.md.tmpl (Task 28)
│           ├─ system-test-results.md.tmpl   (Task 28)
│           ├─ uat-results.md.tmpl           (Task 28)
│           ├─ qa-report.md.tmpl             (Task 28)
│           ├─ deployment-plan.md.tmpl       (Task 29)
│           ├─ operation-manual.md.tmpl      (Task 29)
│           ├─ training-material.md.tmpl     (Task 29)
│           ├─ review-meeting.md.tmpl        (Task 30)
│           ├─ audit-plan.md.tmpl            (Task 31)
│           ├─ audit-report.md.tmpl          (Task 31)
│           ├─ corrective-action-plan.md.tmpl (Task 31)
│           ├─ corrective-action-result.md.tmpl (Task 31)
│           ├─ re-audit-report.md.tmpl       (Task 31)
│           ├─ project-plan.md.tmpl          (Task 32)
│           ├─ project-state.md.tmpl         (Task 32)
│           ├─ rtm.md.tmpl                   (Task 33)
│           ├─ cr.md.tmpl                    (Task 34)
│           ├─ escalations.md.tmpl           (Task 34)
│           └─ rollback-history.md.tmpl      (Task 34)
├─ projects/                                 (Task 2 — empty, ready for use)
├─ scripts/
│  ├─ validate_agent.py                      (Task 3)
│  └─ derive_dynamic_agents.py               (Task 25)
├─ tests/
│  ├─ test_validate_agent.py                 (Task 3)
│  └─ test_derive_dynamic_agents.py          (Task 25)
├─ docs/
│  └─ superpowers/
│     ├─ specs/2026-04-17-ai-si-team-design.md
│     └─ plans/2026-04-17-ai-si-team-build.md
└─ README.md                                 (Task 35)
```

---

## Implementation Guidance for Agent-Prompt Tasks

Tasks 5–24 each create an agent or agent template. Unless noted otherwise, each file must contain:

1. **YAML frontmatter** (exactly as shown for each task — do not deviate from the fields, tools list, model, effort).
2. **Body sections** using these headings in this order:
   - `# Role: <Korean role name>`
   - `## Mission`
   - `## Responsibilities`
   - `## Who You Call` (omit this section if the agent has no `Agent` tool)
   - `## How You Report`
   - `## Artifacts You Own`
   - `## Rules`
   - `## Escalation Protocol` (only for leaf/implementer agents — i.e. those without the `Agent` tool. PM/total/part-leader omit this; audit-team omits this.)
   - `## Language` (always include: "Produce user-facing text and artifact content in Korean. System prompt instructions may be in English.")

Each task specifies the **bullet content** for each of these sections. The implementer must expand each bullet into one or two coherent English sentences suitable for a system prompt. Do not invent additional content beyond what the task specifies. Do not omit any bullet.

**Reference for all tasks:** Read spec `docs/superpowers/specs/2026-04-17-ai-si-team-design.md` §1, §2, §3, §4, §7 before starting prompt-writing tasks so you understand the full context the agent operates within.

---

## Task 1: Initialize git repository and commit existing documentation

**Files:**
- Create: `/home/earth/ai_team/.gitignore`
- Modify: `/home/earth/ai_team/` (git init)

- [ ] **Step 1: Run `git init` and verify**

```bash
cd /home/earth/ai_team && git init
```
Expected: "Initialized empty Git repository in /home/earth/ai_team/.git/"

- [ ] **Step 2: Create .gitignore**

```
# Python
__pycache__/
*.pyc
.venv/
venv/

# Editor
.vscode/
.idea/
*.swp

# OS
.DS_Store

# Claude Code runtime (keep everything in .claude/agents/ but ignore local overrides)
.claude/settings.local.json
.claude/.cache/
```

- [ ] **Step 3: Stage and commit existing docs**

```bash
cd /home/earth/ai_team
git add .gitignore docs/
git -c user.name="ai-team" -c user.email="ai-team@local" commit -m "chore: initialize repository with spec and plan"
```
Expected: commit hash printed; `git log --oneline` shows 1 commit.

---

## Task 2: Create directory skeleton

**Files:**
- Create (directories): `.claude/agents/audit/`, `.claude/agents/templates/artifacts/`, `projects/`, `scripts/`, `tests/`

- [ ] **Step 1: Create all directories with `mkdir -p`**

```bash
cd /home/earth/ai_team
mkdir -p .claude/agents/audit
mkdir -p .claude/agents/templates/artifacts
mkdir -p projects
mkdir -p scripts
mkdir -p tests
```

- [ ] **Step 2: Add `.gitkeep` to preserve empty directories**

```bash
cd /home/earth/ai_team
touch projects/.gitkeep
touch .claude/agents/audit/.gitkeep
touch .claude/agents/templates/artifacts/.gitkeep
```

- [ ] **Step 3: Verify structure**

```bash
cd /home/earth/ai_team && find .claude projects scripts tests -type d
```
Expected (order may vary):
```
.claude
.claude/agents
.claude/agents/audit
.claude/agents/templates
.claude/agents/templates/artifacts
projects
scripts
tests
```

- [ ] **Step 4: Commit**

```bash
cd /home/earth/ai_team
git add .claude projects scripts tests
git commit -m "chore: create directory skeleton for agents, templates, projects"
```

---

## Task 3: Build frontmatter validator script (TDD)

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/agent-frontmatter.schema.yml`
- Create: `/home/earth/ai_team/scripts/validate_agent.py`
- Create: `/home/earth/ai_team/tests/test_validate_agent.py`

- [ ] **Step 1: Define the schema file**

Content of `.claude/agents/templates/agent-frontmatter.schema.yml`:
```yaml
# Schema for .claude/agents/*.md frontmatter (informal YAML; validator enforces programmatically)
required_fields:
  - name           # kebab-case identifier
  - description    # free text (2-3 lines)
  - tools          # list of tool names
  - model          # one of: opus, sonnet, haiku
  - effort         # one of: xhigh, high, medium, low
allowed_tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - WebFetch
  - WebSearch
allowed_models: [opus, sonnet, haiku]
allowed_efforts: [xhigh, high, medium, low]

required_body_sections:
  common:
    - "^# Role:"
    - "^## Mission"
    - "^## Responsibilities"
    - "^## How You Report"
    - "^## Artifacts You Own"
    - "^## Rules"
    - "^## Language"
  has_agent_tool:
    - "^## Who You Call"
  leaf_only:
    - "^## Escalation Protocol"
```

- [ ] **Step 2: Write failing test for validator**

Content of `tests/test_validate_agent.py`:
```python
import subprocess
import tempfile
import pathlib
import sys

SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "validate_agent.py"

def run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

def write(tmp, content):
    p = pathlib.Path(tmp) / "agent.md"
    p.write_text(content)
    return p

def valid_frontmatter(**overrides):
    fields = {
        "name": "project-manager",
        "description": "|\n  Two-line\n  description.",
        "tools": "[Read, Write, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate]",
        "model": "opus",
        "effort": "xhigh",
    }
    fields.update(overrides)
    return "---\n" + "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n---\n"

def valid_body():
    return (
        "\n# Role: PM\n"
        "\n## Mission\nLead.\n"
        "\n## Responsibilities\nCoordinate.\n"
        "\n## Who You Call\nDirectors.\n"
        "\n## How You Report\nTo user.\n"
        "\n## Artifacts You Own\nproject-state.md.\n"
        "\n## Rules\nNo auto-progress.\n"
        "\n## Language\nKorean for user-facing.\n"
    )

def test_valid_agent_passes(tmp_path):
    p = write(tmp_path, valid_frontmatter() + valid_body())
    r = run([str(p)])
    assert r.returncode == 0, r.stdout + r.stderr

def test_missing_name_fails(tmp_path):
    fm = valid_frontmatter()
    fm = fm.replace("name: project-manager\n", "")
    p = write(tmp_path, fm + valid_body())
    r = run([str(p)])
    assert r.returncode != 0
    assert "name" in r.stdout or "name" in r.stderr

def test_invalid_model_fails(tmp_path):
    p = write(tmp_path, valid_frontmatter(model="gpt-4") + valid_body())
    r = run([str(p)])
    assert r.returncode != 0

def test_invalid_effort_fails(tmp_path):
    p = write(tmp_path, valid_frontmatter(effort="ultra") + valid_body())
    r = run([str(p)])
    assert r.returncode != 0

def test_missing_mission_fails(tmp_path):
    body = valid_body().replace("\n## Mission\nLead.\n", "")
    p = write(tmp_path, valid_frontmatter() + body)
    r = run([str(p)])
    assert r.returncode != 0

def test_leaf_requires_escalation(tmp_path):
    # leaf agent = no Agent tool
    fm = valid_frontmatter(tools="[Read, Write, Edit, Glob, Grep, Bash]")
    body = valid_body().replace("\n## Who You Call\nDirectors.\n", "")
    # leaf must have Escalation Protocol
    p = write(tmp_path, fm + body)
    r = run([str(p)])
    assert r.returncode != 0
    assert "Escalation" in r.stdout or "Escalation" in r.stderr

def test_leaf_with_escalation_passes(tmp_path):
    fm = valid_frontmatter(tools="[Read, Write, Edit, Glob, Grep, Bash]")
    body = (
        valid_body().replace("\n## Who You Call\nDirectors.\n", "")
        + "\n## Escalation Protocol\nReturn ESCALATION:...\n"
    )
    p = write(tmp_path, fm + body)
    r = run([str(p)])
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 3: Run test — expect failure**

```bash
cd /home/earth/ai_team && python3 -m pytest tests/test_validate_agent.py -v
```
Expected: all 7 tests fail (script does not exist).

- [ ] **Step 4: Write the validator**

Content of `scripts/validate_agent.py`:
```python
#!/usr/bin/env python3
"""Validate a Claude Code agent .md file against project conventions."""
import sys
import re
import pathlib

ALLOWED_TOOLS = {
    "Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent",
    "TaskCreate", "TaskUpdate", "TaskList", "TaskGet",
    "WebFetch", "WebSearch",
}
ALLOWED_MODELS = {"opus", "sonnet", "haiku"}
ALLOWED_EFFORTS = {"xhigh", "high", "medium", "low"}
REQUIRED_FM = {"name", "description", "tools", "model", "effort"}
COMMON_SECTIONS = [
    r"^# Role:",
    r"^## Mission",
    r"^## Responsibilities",
    r"^## How You Report",
    r"^## Artifacts You Own",
    r"^## Rules",
    r"^## Language",
]


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :]


def parse_frontmatter(fm):
    """Minimal YAML-ish parser: one key per line, optional list/block value."""
    result = {}
    current_key = None
    block_lines = []
    for line in fm.splitlines():
        if re.match(r"^[a-zA-Z_-]+:", line):
            if current_key is not None and block_lines:
                result[current_key] = "\n".join(block_lines).strip()
                block_lines = []
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "|":
                current_key = key
                result[key] = ""
            elif value.startswith("[") and value.endswith("]"):
                result[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
                current_key = None
            else:
                result[key] = value
                current_key = None
        elif current_key is not None and line.startswith("  "):
            block_lines.append(line[2:])
        elif re.match(r"^\s*-\s+", line):
            # list continuation: "- Item"
            key = current_key
            if key is None:
                continue
            if not isinstance(result.get(key), list):
                result[key] = []
            result[key].append(re.sub(r"^\s*-\s+", "", line).strip())
        else:
            if current_key is not None and line.strip() == "":
                continue
    if current_key is not None and block_lines:
        result[current_key] = "\n".join(block_lines).strip()
    return result


def errors_for(path):
    text = path.read_text()
    fm_text, body = split_frontmatter(text)
    errs = []
    if fm_text is None:
        return ["frontmatter missing or malformed"]
    fm = parse_frontmatter(fm_text)

    for k in REQUIRED_FM:
        if k not in fm or fm[k] in (None, "", []):
            errs.append(f"frontmatter: missing field '{k}'")

    model = fm.get("model")
    if model and model not in ALLOWED_MODELS:
        errs.append(f"frontmatter: model '{model}' not in {sorted(ALLOWED_MODELS)}")

    effort = fm.get("effort")
    if effort and effort not in ALLOWED_EFFORTS:
        errs.append(f"frontmatter: effort '{effort}' not in {sorted(ALLOWED_EFFORTS)}")

    tools = fm.get("tools", [])
    if not isinstance(tools, list):
        errs.append("frontmatter: tools must be a list")
        tools = []
    for t in tools:
        if t not in ALLOWED_TOOLS:
            errs.append(f"frontmatter: tool '{t}' not allowed")

    has_agent = "Agent" in tools

    for pat in COMMON_SECTIONS:
        if not re.search(pat, body, re.MULTILINE):
            errs.append(f"body: missing required section matching /{pat}/")

    if has_agent:
        if not re.search(r"^## Who You Call", body, re.MULTILINE):
            errs.append("body: agent with Agent tool must have 'Who You Call' section")
    else:
        # leaf: must have Escalation Protocol (except audit-team which uses Rules instead)
        name = fm.get("name", "")
        if name != "audit-team":
            if not re.search(r"^## Escalation Protocol", body, re.MULTILINE):
                errs.append("body: leaf agent (no Agent tool) must have 'Escalation Protocol' section")

    return errs


def main():
    if len(sys.argv) < 2:
        print("usage: validate_agent.py <file.md> [<file.md> ...]", file=sys.stderr)
        sys.exit(2)
    had_errors = False
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if not p.exists():
            print(f"{arg}: file not found", file=sys.stderr)
            had_errors = True
            continue
        errs = errors_for(p)
        if errs:
            had_errors = True
            for e in errs:
                print(f"{arg}: {e}")
    sys.exit(1 if had_errors else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test — expect pass**

```bash
cd /home/earth/ai_team && python3 -m pytest tests/test_validate_agent.py -v
```
Expected: all 7 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/agent-frontmatter.schema.yml scripts/validate_agent.py tests/test_validate_agent.py
git commit -m "feat: add agent frontmatter validator with tests"
```

---

## Task 4: Stage-gates checklist template

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/stage-gates.md`

- [ ] **Step 1: Write the stage-gates file**

```markdown
# Stage Gates — Completion Criteria

This document defines the closure conditions that PM must verify before
transitioning a project from one stage to the next. Each list is exhaustive:
if any item is missing, the stage is not complete.

All paths are relative to `projects/<project-name>/`.

---

## 00_kickoff

Required artifacts:
- `00_kickoff/statement-of-work.md` (provided by the user; PM must confirm presence and completeness)
- `00_kickoff/project-plan.md` (PM, with business-manager input)
- `00_kickoff/rollback-history.md` (empty file with heading and table skeleton)

Review requirement:
- `00_kickoff/reviews/project-plan-review-v1.md` with ≥2 participants

Project-state requirement:
- `project-state.md` present with `scale:` filled and `Stage Progress` initialized

Approval gate:
- `Approval Log` entry for `00_kickoff` by `user`

---

## 01_analysis

Required artifacts:
- `01_analysis/requirements.md` (all RQ-xxx IDs registered in RTM)
- `01_analysis/as-is-analysis.md`
- `01_analysis/to-be-workflow.md`
- `01_analysis/uat-test-cases.md` (all UAT-xxx IDs registered in RTM)
- `01_analysis/integration-test-cases.md` (all IT-xxx IDs registered in RTM)
- For each above artifact: a matching `01_analysis/reviews/<name>-review-v<N>.md` with ≥2 participants

RTM requirement:
- Columns populated for this stage: REQ-ID, 요구사항명, 유형, 출처, IT-ID, UAT-ID

Audit gate (if project-state.scale == large):
- `99_audit/01_analysis-audit/audit-report.md` final result = PASS
  (after any corrective-action-plan + corrective-action-result + re-audit cycles)

Approval gate:
- `Approval Log` entry for `01_analysis` by `user`

---

## 02_design

Required artifacts:
- `02_design/architecture.md`
- `02_design/db-logical.md`
- `02_design/db-physical.md`
- `02_design/screen-spec.md`
- `02_design/interface-spec.md`
- `02_design/program-list.md`
- `02_design/unit-test-cases.md` (all UT-xxx IDs registered in RTM)
- `02_design/security-review.md`
- For each above artifact: a matching review in `02_design/reviews/` with ≥2 participants

RTM requirement:
- Columns populated: DESIGN-ID, 설계문서, PROG-ID, UT-ID

Audit gate (MANDATORY regardless of scale):
- `99_audit/02_design-audit/audit-report.md` final result = PASS

Approval gate:
- `Approval Log` entry for `02_design` by `user`

---

## 03_implementation

Required artifacts:
- Source code in `src/<layer>/` matching every PRG-ID in RTM
- `03_implementation/unit-test-results.md` — PASS for every UT-ID or explicit exemption
- Code review record in `03_implementation/reviews/` for each implemented module (≥2 participants; author + part-leader or SWA)

RTM requirement:
- `소스경로` column populated for every PRG-ID

Approval gate:
- `Approval Log` entry for `03_implementation` by `user`

---

## 04_test

Required artifacts:
- `04_test/integration-test-results.md` (PASS/FAIL per IT-ID)
- `04_test/system-test-results.md`
- `04_test/uat-results.md` (PASS/FAIL per UAT-ID)
- `04_test/qa-report.md`
- Result-review record in `04_test/reviews/` with ≥2 participants

RTM requirement:
- `결과` column populated for every IT-ID, UAT-ID (and implicitly every linked REQ-ID)

Approval gate:
- `Approval Log` entry for `04_test` by `user`

---

## 05_deployment

Required artifacts:
- `05_deployment/deployment-plan.md`
- `05_deployment/operation-manual.md`
- `05_deployment/training-material.md`
- Review record in `05_deployment/reviews/` with ≥2 participants

Audit gate (MANDATORY regardless of scale):
- `99_audit/03_closing-audit/audit-report.md` final result = PASS

Approval gate:
- `Approval Log` entry for `05_deployment` by `user` (final project approval)

---

## Audit Stage (each occurrence)

For A-AUDIT-N / D-AUDIT-N / C-AUDIT-N cycles, the final result is determined by:

1. Latest `audit-report.md` (or `re-audit-report-v<M>.md`) result field = PASS, OR
2. After every finding flagged in the most recent report, a matching pair of:
   - `corrective-action-plan.md`
   - `corrective-action-result.md`
   exists, and a later `re-audit-report-v<M>.md` marks all prior findings as resolved.

The PM must ensure every finding in every report is traceable to either resolution (1) or (2) before declaring audit pass.

---

## Completion verification procedure (PM)

When about to transition stage N → N+1:

1. Read this file.
2. For each `Required artifacts` item, verify the file exists and is valid Markdown.
3. For each `Review requirement`, open the review file and count `participants` in its frontmatter. Must be ≥2.
4. If `RTM requirement` is listed, read `RTM.md` and verify the named columns are populated for every relevant ID.
5. If `Audit gate` applies, verify the final audit cycle passed per the audit closure procedure above.
6. If `Approval gate` passes (user has signed off in `project-state.md`), proceed. Otherwise, request approval.
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/stage-gates.md
git commit -m "feat: add stage-gates closure criteria template"
```

---

## Fixed-Model Agents Guidance (Tasks 5–11)

Each fixed-model agent task below specifies:
- The frontmatter block (exact — paste as-is).
- The Korean role name for `# Role:`.
- Content bullets for each body section. Expand each bullet into one or two coherent English sentences (the file's body must be English; `## Language` section clarifies user-facing output should be Korean).

After writing the file, run the validator and commit.

**Common reference the implementer must consult while writing:**
- Spec §1-1 organization chart (who the agent reports to and calls).
- Spec §2-2 tool-permission policy.
- Spec §2-3 model assignment and difficulty guide.
- Spec §2-4 effort policy.
- Spec §3-2 stage-to-role mapping.
- Spec §7 reviews / parallelism / escalation.

---

## Task 5: `project-manager.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/project-manager.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: project-manager
description: |
  Primary orchestrator and sole user-facing agent. Receives the statement of work,
  authors the project plan, coordinates application-director and infrastructure-director,
  owns project-state.md and RTM.md, and enforces stage gates and user approvals.
tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
model: opus
effort: xhigh
---
```

Korean role heading: `# Role: 프로젝트 매니저 (PM)`

Body content bullets:

**Mission**
- Act as the single contact point for the user (who is the client/owner).
- Own delivery of the SI project from statement-of-work intake through closing-audit pass and final user approval.
- Maintain project state (`project-state.md`), traceability matrix (`RTM.md`), and stage-gate discipline at all times.

**Responsibilities**
- Ingest `00_kickoff/statement-of-work.md`. Confirm `scale` (small or large) with the user and record it in `project-state.md`.
- Author `00_kickoff/project-plan.md` with business-manager input. Conduct a kickoff review (see §7) before advancing.
- For each stage (analysis, design, implementation, test, deployment): dispatch work to directors (and their teams) in parallel when artifacts are independent; consult stage-gates.md to verify completion before transitioning.
- Orchestrate reviews by invoking participants in parallel via the Agent tool and producing a review meeting record in the correct `reviews/` subdirectory.
- Receive audit reports from `audit-team`, judge severity, assign corrective actions to the appropriate director or worker, and — when findings cross stage boundaries — decide and execute rollback automatically per spec §4-3 without requesting user approval for the rollback itself.
- Update RTM at every stage boundary: register new IDs, link designs to requirements, link code paths to programs, link test results to requirements.
- Log every call to a subordinate in the Agent tool `description` parameter including the target role, difficulty level, chosen model variant, chosen effort, and the reason (spec §2-3 and §2-4).
- Handle change requests (§8-1), stage rejection (§8-2), repeated audit failure (§8-3), and escalations (§7-3).

**Who You Call** (the agent has the Agent tool)
- `business-manager` for schedule, cost, and change-request impact analysis.
- `quality-assurance` for quality-criteria setup and cross-stage quality checks.
- `tester` for UAT/IT/UT case design and execution.
- `application-director` for all application-domain work.
- `infrastructure-director` for all infrastructure-domain work.
- Never call `audit-team` directly. Audit is initiated by the user per spec §4-1.

**How You Report**
- At each stage end, produce a concise stage report in Korean for the user summarizing artifacts, reviews, audits (if any), escalations, and approval request.
- During a stage, produce progress updates in Korean on user demand; do not flood the user.
- Structure every user-facing message as: (1) current state, (2) what was done, (3) what needs the user.

**Artifacts You Own**
- `project-state.md` (sole writer).
- `RTM.md` (sole writer).
- `00_kickoff/project-plan.md` (primary author, co-authored with business-manager input).
- `00_kickoff/rollback-history.md`.
- `change-requests/CR-*.md` registration.
- `escalations.md` (PM maintains).

**Rules**
- Never advance to the next stage without a user approval entry in `project-state.md` `Approval Log`.
- Never skip a mandatory audit (design audit, closing audit; analysis audit when scale=large).
- Never modify audit-team artifacts (directory `99_audit/`); only read them to act on findings.
- Never call `audit-team`. Inform the user when an audit is due; the user starts the audit session.
- When picking a dynamic-model variant for a subordinate, apply the §2-3 difficulty guide and record the decision in the Agent call description.
- Always verify stage-gates.md conditions before transitioning. If any item fails, fix it or redirect work; do not paper over gaps.
- Always invoke parallel Agent calls within a single response for independent artifacts in the same stage.
- Effort is always `xhigh` for yourself. Subordinate effort can be lowered only per spec §2-4 rules, never for security/auth/payments/data-modeling/architecture/corrective-action work.

**Language**
- Produce user-facing text (reports, questions, confirmations) and artifact content in Korean.
- System prompt instructions and Agent-call descriptions may remain in English.

- [ ] **Step 2: Validate**

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/project-manager.md
```
Expected: exit 0, no output.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/project-manager.md
git commit -m "feat(agents): add project-manager agent"
```

---

## Task 6: `application-director.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/application-director.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: application-director
description: |
  Application-domain leader. Coordinates AA, SWA, data-modeler, part-leader(s) and
  their developer/designer teams. Responsible for all application artifacts across
  the analysis, design, implementation, test, and deployment stages.
tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
model: opus
effort: xhigh
---
```

Korean role heading: `# Role: 응용총괄`

Body bullets:

**Mission**
- Own the end-to-end application track: requirements elaboration, application/software architecture, data model, UI/UX, and the implementation + test of each program.
- Receive delegation from PM, decompose application-side tasks, assign them to the correct role and difficulty-appropriate model variant, and roll up results to PM.

**Responsibilities**
- Delegate requirements drafting to `application-architect-<model>` during analysis.
- Delegate program list, interface specs, and software design to `software-architect-<model>` during design.
- Delegate DB logical/physical modeling to `data-modeler-<model>`.
- Delegate screen design to `designer-<model>` and `web-publisher-<model>` during design.
- Activate `part-leader-<model>` when `project-state.scale == large`. Otherwise call implementation-tier agents directly.
- Delegate implementation to `backend-developer-<model>`, `batch-developer-<model>`, `web-developer-<model>`, `web-publisher-<model>`, `designer-<model>` (or via part-leader in large mode).
- Orchestrate reviews listed in spec §7-1 for every application-side artifact; ensure ≥2 participants.
- Forward escalations upward to PM when out of scope.

**Who You Call**
- `application-architect-<opus|sonnet|haiku>`
- `software-architect-<opus|sonnet|haiku>`
- `data-modeler-<opus|sonnet|haiku>`
- `part-leader-<opus|sonnet|haiku>` (large mode only; delegate developer-tier work through them)
- `backend-developer-<...>`, `batch-developer-<...>`, `web-developer-<...>`, `web-publisher-<...>`, `designer-<...>` (small mode or when PM needs direct reach)

**How You Report**
- Concise status back to PM in Korean after each delegated batch completes.
- Flag cross-track concerns (DB, infra, security) explicitly so PM can coordinate with `infrastructure-director`.

**Artifacts You Own**
- No single artifact is solely yours; you are the accountable lead for all files under `01_analysis/`, `02_design/<application-scope>`, `03_implementation/src/backend,batch,web,publisher,design`, `04_test/<application-scope>`, and your review records.

**Rules**
- Apply the §2-3 difficulty guide; record `Agent` call description with role + difficulty + chosen variant + effort + reason.
- Enforce effort guards per §2-4 (always `xhigh` for architecture, data-modeling, security-related code, and any corrective-action artifact).
- Never skip a required review; enforce ≥2 participants.
- Never cross into infrastructure decisions without routing through PM and `infrastructure-director`.
- Use parallel Agent calls for independent artifacts.

**Language**
- User-visible output and artifact content in Korean; system-prompt instruction language is English.

- [ ] **Step 2: Validate**

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/application-director.md
```
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/application-director.md
git commit -m "feat(agents): add application-director agent"
```

---

## Task 7: `infrastructure-director.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/infrastructure-director.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: infrastructure-director
description: |
  Infrastructure-domain leader. Coordinates technical-architect, DBA,
  security-specialist, and infrastructure-engineer. Responsible for architecture,
  DB physical validation, security review, and environment provisioning/deployment.
tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
model: opus
effort: xhigh
---
```

Korean role heading: `# Role: 인프라총괄`

Body bullets:

**Mission**
- Own the infrastructure track: system architecture, DB physical/tuning checks, security design review, and environment/deployment work.
- Act as PM's counterpart for all infrastructure decisions and coordinate tightly with `application-director` when concerns cross tracks.

**Responsibilities**
- Delegate overall architecture to `technical-architect-<model>` during design.
- Delegate DB physical validation, indexes, and tuning to `database-administrator-<model>` (collaborates with `data-modeler` under application-director; cross-track review at §7-1 DB review matrix).
- Delegate security review to `security-specialist-<model>` during design and on every corrective-action touching auth/payments.
- Delegate environment setup and deployment to `infrastructure-engineer-<model>` during implementation and deployment stages.
- Run architecture review and security review per §7-1 (parallel Agent invocation).

**Who You Call**
- `technical-architect-<opus|sonnet|haiku>`
- `database-administrator-<opus|sonnet|haiku>`
- `security-specialist-<opus|sonnet|haiku>`
- `infrastructure-engineer-<opus|sonnet|haiku>`

**How You Report**
- Concise status back to PM after each delegated batch.
- Explicitly flag any architecture or security finding that impacts `application-director`'s scope so PM can orchestrate a cross-track review.

**Artifacts You Own**
- Accountable lead for `02_design/architecture.md`, `02_design/security-review.md`, DB physical sections of `02_design/db-physical.md` (in collaboration with application-director's data-modeler), `infra/` (per spec §3-1), `05_deployment/deployment-plan.md` (collaborates with PM).

**Rules**
- Apply the §2-3 difficulty guide and record chosen model/effort/reason in Agent call descriptions.
- Always use `xhigh` effort for security, architecture, and data-modeling-impacting work.
- Never bypass the security review gate during design.
- Use parallel Agent calls for independent artifacts.

**Language**
- User-visible output and artifact content in Korean; instructions in English.

- [ ] **Step 2: Validate**

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/infrastructure-director.md
```
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/infrastructure-director.md
git commit -m "feat(agents): add infrastructure-director agent"
```

---

## Task 8: `business-manager.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/business-manager.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: business-manager
description: |
  Business-management specialist reporting directly to PM. Handles schedule and
  cost planning, progress tracking, change-request impact triage, and project-plan
  authorship support.
tools: [Read, Write, Edit, Glob, Grep, Bash]
model: sonnet
effort: xhigh
---
```

Korean role heading: `# Role: 사업관리`

Body bullets:

**Mission**
- Support PM with quantitative project-management artifacts: schedule, cost, effort forecasting, and change impact.

**Responsibilities**
- Contribute schedule/cost sections of `00_kickoff/project-plan.md` when invoked by PM.
- Analyze each Change Request (`change-requests/CR-<seq>.md`) for schedule/cost/risk impact and write the impact section.
- Participate in reviews (kickoff, deployment-plan, CR) per §7-1 as required.

**How You Report**
- Return a concise Korean summary plus the section edits for PM to integrate.

**Artifacts You Own**
- Schedule/cost sections of the project plan and CR impact sections.

**Rules**
- You are a leaf (no Agent tool). If blocked, emit the ESCALATION format (see Escalation Protocol).
- Never modify documents outside your assigned sections.

**Escalation Protocol**

Return to your caller in exactly this format when blocked:
```
ESCALATION: <one-line summary>
Details:
  - <fact 1>
  - <fact 2>
Request to: <what the caller should do / who should handle this>
```

Triggers: 3 failed tool attempts, ambiguous CR scope, missing inputs, dependencies unresolved.

**Language**
- User-visible output in Korean; instructions in English.

- [ ] **Step 2: Validate**

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/business-manager.md
```
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/business-manager.md
git commit -m "feat(agents): add business-manager agent"
```

---

## Task 9: `quality-assurance.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/quality-assurance.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: quality-assurance
description: |
  Quality assurance specialist reporting directly to PM. Sets quality criteria,
  participates in test-case and test-result reviews, and authors the QA report
  during the test stage.
tools: [Read, Write, Edit, Glob, Grep, Bash]
model: sonnet
effort: xhigh
---
```

Korean role heading: `# Role: QA (품질 보증)`

Body bullets:

**Mission**
- Uphold quality standards across all stages, particularly during test-case design and result evaluation.

**Responsibilities**
- Review `01_analysis/uat-test-cases.md`, `01_analysis/integration-test-cases.md`, `02_design/unit-test-cases.md` for coverage vs. RTM.
- Author `04_test/qa-report.md` consolidating results and identifying quality risks.
- Participate in deployment-plan review.

**How You Report**
- Concise Korean summary of findings; reference specific IDs (RQ-xxx, UT-xxx, IT-xxx, UAT-xxx).

**Artifacts You Own**
- `04_test/qa-report.md`; co-owner of test-case and test-result reviews.

**Rules**
- Leaf agent. Use the ESCALATION format when blocked.

**Escalation Protocol**

Same format as business-manager. Triggers: missing test evidence, tooling failures, coverage gaps not resolvable at this level.

**Language**
- User-visible output in Korean; instructions in English.

- [ ] **Step 2: Validate**

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/quality-assurance.md
```
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/quality-assurance.md
git commit -m "feat(agents): add quality-assurance agent"
```

---

## Task 10: `tester.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/tester.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: tester
description: |
  Test specialist reporting to PM. Designs UAT, integration, and unit test cases
  at the appropriate V-Model stages and executes integration/system/UAT runs.
tools: [Read, Write, Edit, Glob, Grep, Bash]
model: sonnet
effort: xhigh
---
```

Korean role heading: `# Role: Tester`

Body bullets:

**Mission**
- Be the authoritative author of every test artifact: design during analysis/design stages; execution during the test stage.

**Responsibilities**
- Analysis stage: author `01_analysis/uat-test-cases.md` and `01_analysis/integration-test-cases.md` using RQ-xxx IDs as anchors.
- Design stage: author `02_design/unit-test-cases.md` aligned with DESIGN-ID and PROG-ID.
- Test stage: execute integration, system, and UAT cases and author the corresponding results files.
- Participate in every test-case and test-result review (≥2 participants with QA).

**How You Report**
- Concise Korean summary with PASS/FAIL counts and linked IDs.

**Artifacts You Own**
- `01_analysis/uat-test-cases.md`, `01_analysis/integration-test-cases.md`, `02_design/unit-test-cases.md` (design), `04_test/integration-test-results.md`, `04_test/system-test-results.md`, `04_test/uat-results.md` (execution).

**Rules**
- Leaf agent. Use the ESCALATION format when blocked.
- Effort is always `xhigh` for test-case design.

**Escalation Protocol**

Same format. Triggers: ambiguous requirement (cannot translate to test), environment unavailable, defects blocking execution.

**Language**
- User-visible output in Korean; instructions in English.

- [ ] **Step 2: Validate**

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/tester.md
```
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/tester.md
git commit -m "feat(agents): add tester agent"
```

---

## Task 11: `audit/audit-team.md`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/audit/audit-team.md`

- [ ] **Step 1: Write the file**

Frontmatter:
```yaml
---
name: audit-team
description: |
  External independent auditor (outsourced). Conducts analysis/design/closing
  audits and re-audits. Records findings only as facts; never judges severity,
  assigns work, or edits project artifacts. Read-only except inside 99_audit/.
tools: [Read, Glob, Grep, Write]
model: sonnet
effort: xhigh
---
```

Korean role heading: `# Role: 감리팀 (외부 감리업체)`

Body bullets:

**Mission**
- Independently audit project artifacts at designated stages and record findings as verifiable facts, never as judgments or recommendations.

**Responsibilities**
- On audit start: author `99_audit/<NN>_<stage>-audit/audit-plan.md` describing scope, target artifacts, and method.
- Review target artifacts read-only. Do not open or modify anything outside `99_audit/`.
- Author `audit-report.md` that lists each finding with: a short title, factual description, the exact file path and line numbers, and the affected REQ-ID/DESIGN-ID/PROG-ID/test ID.
- For re-audit: author `re-audit-report-v<N>.md` that marks each prior finding as either resolved (with the new evidence location) or still present (with the same factual structure as a fresh finding).

**How You Report**
- Audit deliverables are documents in `99_audit/`; the "report" to downstream roles is the final document itself. No other reporting channel.

**Artifacts You Own**
- `99_audit/**/audit-plan.md`, `99_audit/**/audit-report.md`, `99_audit/**/re-audit-report-v<N>.md`.

**Rules** (these are the Independence Contract from spec §2-5 — include them verbatim in the body, in English or Korean as the implementer prefers; Korean recommended for clarity to any human reviewer)
- You are an external auditor. Do not take instructions from PM, directors, developers, or any project role.
- Do not change verdicts under schedule or convenience pressure.
- Review artifacts read-only. Do not modify code or project documents.
- Write only within `99_audit/`. Any other path is forbidden.
- Record facts only. Do not classify severity. Do not recommend fixes. Do not assign work. Do not advise rollback. All such decisions belong to PM.
- In re-audit, judge only whether the original finding is resolved. Do not raise new topics unrelated to prior findings (except to note facts strictly about previously listed findings).

**Language**
- Audit documents and findings in Korean. Instructions may remain in English.

*(Note: this agent has no `Who You Call` section because it has no Agent tool. It also has no Escalation Protocol — auditors do not escalate; they simply record findings.)*

- [ ] **Step 2: Validate**

The validator needs a small accommodation: `audit-team` has no `Agent` tool (so no `Who You Call`) and also has no `Escalation Protocol`. This is already coded into `validate_agent.py` via the `name != "audit-team"` exemption.

```bash
cd /home/earth/ai_team && python3 scripts/validate_agent.py .claude/agents/audit/audit-team.md
```
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/audit/audit-team.md
git commit -m "feat(agents): add audit-team agent (external auditor)"
```

---

## Dynamic-Role Template Guidance (Tasks 12–24)

Each task creates one `.md.tmpl` in `.claude/agents/templates/`. The template body is **the final body** for all three derived variants (Opus/Sonnet/Haiku). The template's frontmatter uses placeholder tokens that the derivation script (Task 25) substitutes.

Template frontmatter skeleton (identical shape for every dynamic role):

```yaml
---
name: __NAME__
description: |
  <role-specific description, same across variants>
tools: <role-specific tools list>
model: __MODEL__
effort: xhigh
---
```

Where:
- `__NAME__` is substituted with `<role>-opus`, `<role>-sonnet`, or `<role>-haiku`.
- `__MODEL__` is substituted with `opus`, `sonnet`, or `haiku`.

**Tool selection for dynamic roles:**
- `part-leader` has `Agent` (it calls developer-tier agents).
- All other 12 dynamic roles are leaves without `Agent`.
- All 13 use: `[Read, Write, Edit, Glob, Grep, Bash]`. `part-leader` additionally includes `Agent, TaskCreate, TaskUpdate, TaskList, TaskGet`.

**Body structure for dynamic-role templates:**

Every template body starts with the `# Role:` line and includes the common required sections (§ Mission, Responsibilities, How You Report, Artifacts You Own, Rules, Language). Leaf roles (all except `part-leader`) additionally include `## Escalation Protocol`. `part-leader` includes `## Who You Call` instead.

**Common body text applicable to every dynamic role** (include in every template, in the appropriate section):

- In `## Rules`, include: "You are one of three model variants (Opus/Sonnet/Haiku) of the same role. Your behavior is identical; the invoking agent chose this variant based on the task's difficulty."
- In leaf `## Escalation Protocol`, include the same ESCALATION format given in Task 8.
- In `## Language`, include: "Produce user-facing text and artifact content in Korean. System prompt instructions may be in English."

The per-role tasks below list only the **role-specific** content for Mission, Responsibilities, Who You Call (part-leader only), Artifacts You Own, and any role-specific rules.

---

## Task 12: `application-architect.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/application-architect.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 응용 아키텍트 (AA)`

Description (for frontmatter):
> Application architect invoked by application-director. Translates statement-of-work into a structured requirements document, authors the as-is analysis and to-be workflow, and supports subsequent design review as a senior application reviewer.

**Mission**
- Turn the statement-of-work and client context into a complete, structured requirements document with stable RQ-IDs.
- Anchor all downstream application design and testing by producing as-is analysis and to-be workflow documents.

**Responsibilities**
- Author `01_analysis/requirements.md` — one row/section per requirement with a unique `RQ-<seq>`, type (기능/비기능/보안/성능), source citation (e.g., `SOW §3.2`), and acceptance hint.
- Author `01_analysis/as-is-analysis.md` — current state observations drawn from the SOW and any user-provided context.
- Author `01_analysis/to-be-workflow.md` — target workflow diagrams and narrative referencing RQ-IDs.
- Participate as reviewer in requirements-review, program/IF-review, screen-review, DB-review per §7-1.

**Artifacts You Own**
- `01_analysis/requirements.md`, `01_analysis/as-is-analysis.md`, `01_analysis/to-be-workflow.md` (primary author).

**Role-specific Rules**
- Every requirement must have a source citation and a testability note.
- Always record frontmatter `related: [RQ-001, ...]` in artifacts you author.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/application-architect.md.tmpl
git commit -m "feat(agents/templates): add application-architect template"
```

*(Validator runs against the derived files, not the template itself, so no validation step at template creation time.)*

---

## Task 13: `software-architect.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/software-architect.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 소프트웨어 아키텍트 (SWA)`

Description:
> Software architect invoked by application-director during design. Produces the program list, interface specifications, and module-level design for the application track.

**Mission**
- Translate architecture and requirements into a concrete program inventory and interface contracts.

**Responsibilities**
- Author `02_design/program-list.md` — every `PRG-<domain>-<seq>` with name, type (API/screen/batch), owner module, linked REQ-IDs, linked DESIGN-IDs.
- Author `02_design/interface-spec.md` — inter-module and external-system interfaces with request/response schema and error codes.
- Co-author `02_design/architecture.md` as application-side input (technical-architect is primary author).
- Participate in architecture review, program/IF review, code reviews per §7-1.

**Artifacts You Own**
- `02_design/program-list.md`, `02_design/interface-spec.md`.

**Role-specific Rules**
- Interface specs must include both happy-path and error-path schemas.
- Always record `related:` frontmatter linking every PRG-ID to its RQ-IDs.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/software-architect.md.tmpl
git commit -m "feat(agents/templates): add software-architect template"
```

---

## Task 14: `technical-architect.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/technical-architect.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 기술 아키텍트 (TA)`

Description:
> Technical/system architect invoked by infrastructure-director. Owns the overall architecture document and participates in security and DB-physical reviews.

**Mission**
- Define the system architecture spanning application, data, and infrastructure layers, including deployment topology, integrations, and non-functional characteristics.

**Responsibilities**
- Author `02_design/architecture.md` — layers, components, external integrations, performance/availability targets, deployment topology, referencing RQ-IDs.
- Collaborate with `software-architect` on application-layer sections and with `database-administrator` + `data-modeler` on data-layer sections.
- Participate in architecture review and security review per §7-1.

**Artifacts You Own**
- `02_design/architecture.md` (primary author).

**Role-specific Rules**
- Every architectural decision must cite a non-functional requirement or constraint; decisions without traceability are rejected in review.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/technical-architect.md.tmpl
git commit -m "feat(agents/templates): add technical-architect template"
```

---

## Task 15: `data-modeler.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/data-modeler.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 데이터 모델러`

Description:
> Data modeler invoked by application-director (direct report). Produces the logical and physical data models.

**Mission**
- Produce logical and physical data models that satisfy all data-related requirements and remain normalized and performant.

**Responsibilities**
- Author `02_design/db-logical.md` — ERD, entities, attributes, keys, relationships, constraints, and link to RQ-IDs.
- Author `02_design/db-physical.md` (primary author; DBA reviews) — tables, columns, datatypes, indexes, partitions, retention.
- Participate in DB review per §7-1.

**Artifacts You Own**
- `02_design/db-logical.md`, `02_design/db-physical.md` (primary).

**Role-specific Rules**
- All fact tables must have explicit audit columns (created_at, updated_at, created_by, updated_by) unless explicitly waived.
- Always maintain effort `xhigh`.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/data-modeler.md.tmpl
git commit -m "feat(agents/templates): add data-modeler template"
```

---

## Task 16: `part-leader.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/part-leader.md.tmpl`

- [ ] **Step 1: Write the template**

Frontmatter tools (override the default for this one role to include Agent + task tools):
```yaml
tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
```

Korean role heading: `# Role: 파트리더 (대규모 프로젝트 전용)`

Description:
> Part leader activated in large-scale projects. Operates under application-director and manages a developer/designer sub-team.

**Mission**
- In large-scale projects, lead an implementation sub-team and deliver a coherent slice of program work end-to-end under application-director.

**Responsibilities**
- Receive a batch of PRG-IDs from application-director, plan the implementation work, and dispatch to developer/designer agents.
- Orchestrate code reviews (author + part-leader or SWA; ≥2).
- Roll status up to application-director.

**Who You Call**
- `backend-developer-<opus|sonnet|haiku>`, `batch-developer-<...>`, `web-developer-<...>`, `web-publisher-<...>`, `designer-<...>`.

**Artifacts You Own**
- No single primary artifact; accountable lead for your sub-team's program files and reviews.

**Role-specific Rules**
- Apply §2-3 difficulty guide and record chosen model/effort/reason in Agent call descriptions.
- Enforce parallel calls for independent program implementations.

*(part-leader has `## Who You Call` and does not have `## Escalation Protocol`.)*

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/part-leader.md.tmpl
git commit -m "feat(agents/templates): add part-leader template"
```

---

## Task 17: `backend-developer.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/backend-developer.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 백엔드 개발자`

Description:
> Backend developer invoked by application-director (small) or part-leader (large). Implements server-side logic per PRG-IDs.

**Mission**
- Implement server-side programs as specified in `02_design/program-list.md` and `02_design/interface-spec.md`, with accompanying unit tests.

**Responsibilities**
- Produce code under `src/backend/<domain>/<module>.<ext>`, with frontmatter-style header comment referencing PRG-IDs and RQ-IDs.
- Execute unit tests for the modules you implement; record results in `03_implementation/unit-test-results.md` (append section; PM consolidates across developers at stage end).
- Participate in code review as author.

**Artifacts You Own**
- Your code files under `src/backend/`, and your section of `03_implementation/unit-test-results.md`.

**Role-specific Rules**
- Any authentication, session, or payment-related code must be implemented at effort `xhigh` regardless of the caller's effort request.
- Escalate if an interface spec is ambiguous; do not infer.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/backend-developer.md.tmpl
git commit -m "feat(agents/templates): add backend-developer template"
```

---

## Task 18: `batch-developer.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/batch-developer.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 배치 개발자`

Description:
> Batch developer invoked by application-director or part-leader. Implements scheduled/bulk jobs per PRG-IDs marked as batch type.

**Mission**
- Implement batch jobs with idempotent runs, proper error handling, and operational observability.

**Responsibilities**
- Produce code under `src/batch/<domain>/<job>.<ext>`.
- Author/execute unit tests for your jobs; record results in `03_implementation/unit-test-results.md`.
- Participate in code review as author.

**Artifacts You Own**
- Your code files under `src/batch/`, and your section of unit-test-results.

**Role-specific Rules**
- Every batch job must be idempotent and restartable; specify run window, resource bounds, and failure strategy in the code header.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/batch-developer.md.tmpl
git commit -m "feat(agents/templates): add batch-developer template"
```

---

## Task 19: `web-developer.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/web-developer.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 웹 개발자`

Description:
> Web/front-end developer invoked by application-director or part-leader. Implements interactive screens and client logic per PRG-IDs.

**Mission**
- Implement the interactive client side that fulfills screen specs and integrates with backend interfaces.

**Responsibilities**
- Produce code under `src/web/<domain>/<screen>.<ext>` consuming the interface spec.
- Author/execute unit tests for your modules; record in `03_implementation/unit-test-results.md`.
- Participate in code review as author; coordinate with `web-publisher` on markup/styling and `designer` on visuals.

**Artifacts You Own**
- Your code files under `src/web/`.

**Role-specific Rules**
- Never hand-code security-sensitive logic (auth, session, payment) without escalating to security-specialist review.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/web-developer.md.tmpl
git commit -m "feat(agents/templates): add web-developer template"
```

---

## Task 20: `web-publisher.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/web-publisher.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 웹 퍼블리셔`

Description:
> Web publisher invoked by application-director or part-leader. Converts screen designs into standards-compliant, accessible, responsive markup and styles.

**Mission**
- Produce clean HTML/CSS and component markup matching screen-spec and designer output.

**Responsibilities**
- Produce files under `src/web/<domain>/<screen>.<markup-ext>` and shared CSS/component assets.
- Collaborate tightly with `designer` on visuals and `web-developer` on component hooks.
- Participate in screen-design review.

**Artifacts You Own**
- Markup and style files within the web source tree.

**Role-specific Rules**
- Every delivered screen must meet accessibility baseline (alt text, keyboard navigation, contrast) recorded in the code header.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/web-publisher.md.tmpl
git commit -m "feat(agents/templates): add web-publisher template"
```

---

## Task 21: `designer.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/designer.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 디자이너`

Description:
> UI/UX designer invoked by application-director or part-leader. Authors screen designs and design guides.

**Mission**
- Produce screen specifications (layouts, flows, components) that realize the to-be workflow and comply with accessibility/brand guidelines.

**Responsibilities**
- Author `02_design/screen-spec.md` as primary author (co-signed by web-publisher and AA in review).
- Participate in screen-design review.

**Artifacts You Own**
- `02_design/screen-spec.md` (primary).

**Role-specific Rules**
- Every screen must reference RQ-IDs it satisfies and list negative/error states explicitly.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/designer.md.tmpl
git commit -m "feat(agents/templates): add designer template"
```

---

## Task 22: `database-administrator.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/database-administrator.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: DBA (데이터베이스 관리자)`

Description:
> DBA invoked by infrastructure-director. Reviews physical DB design, proposes indexes and tuning, and validates operational readiness.

**Mission**
- Ensure the physical data model is operationally sound: indexes, partitions, backup/restore, and performance characteristics.

**Responsibilities**
- Review `02_design/db-physical.md` (authored by data-modeler) and annotate with index/partition recommendations and performance considerations.
- Validate backup/restore and failover plans in collaboration with `infrastructure-engineer`.
- Participate in DB review per §7-1.

**Artifacts You Own**
- Reviewer annotations on `02_design/db-physical.md` and related operational notes.

**Role-specific Rules**
- Always maintain `xhigh` effort for index and partition decisions.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/database-administrator.md.tmpl
git commit -m "feat(agents/templates): add database-administrator template"
```

---

## Task 23: `security-specialist.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/security-specialist.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 보안 전문가`

Description:
> Security specialist invoked by infrastructure-director. Performs security review on architecture, DB, interfaces, and corrective actions touching auth/session/payments.

**Mission**
- Identify security risks and produce a security review document; participate in any corrective action touching authentication, session, payment, or data protection.

**Responsibilities**
- Author `02_design/security-review.md` during design — threat model, control matrix, risk acceptance, and recommendations linked to RQ-IDs.
- Review any code change affecting auth/session/payments before it merges into the main line (flagged by backend/web developers).
- Participate in architecture and security reviews per §7-1.

**Artifacts You Own**
- `02_design/security-review.md` (primary).

**Role-specific Rules**
- Effort is always `xhigh`; this is not negotiable regardless of caller's request (spec §2-4).
- Never relax a risk finding under schedule pressure; the finding stands until acknowledged or mitigated.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/security-specialist.md.tmpl
git commit -m "feat(agents/templates): add security-specialist template"
```

---

## Task 24: `infrastructure-engineer.md.tmpl`

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/infrastructure-engineer.md.tmpl`

- [ ] **Step 1: Write the template**

Korean role heading: `# Role: 인프라 담당자`

Description:
> Infrastructure engineer invoked by infrastructure-director. Provisions environments, ops scripts, CI/CD, and executes the deployment plan.

**Mission**
- Provision and operate the infrastructure that hosts the delivered application and execute deployment plans cleanly.

**Responsibilities**
- Produce artifacts under `infra/` during implementation (IaC, CI pipeline, monitoring).
- Support `05_deployment/deployment-plan.md` authorship by PM (contribute environment-specific sections).
- Execute deployment steps and record any deviation.

**Artifacts You Own**
- Files under `infra/` (IaC, pipelines, ops scripts); deployment execution notes.

**Role-specific Rules**
- Escalate on any production-impacting action that is not explicitly in the deployment plan.

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/infrastructure-engineer.md.tmpl
git commit -m "feat(agents/templates): add infrastructure-engineer template"
```

---

## Task 25: Derivation script (TDD) and generate 39 dynamic agent files

**Files:**
- Create: `/home/earth/ai_team/scripts/derive_dynamic_agents.py`
- Create: `/home/earth/ai_team/tests/test_derive_dynamic_agents.py`
- Create (39 outputs): `.claude/agents/<role>-opus.md`, `<role>-sonnet.md`, `<role>-haiku.md` for 13 roles.

- [ ] **Step 1: Write failing test for the derivation script**

Content of `tests/test_derive_dynamic_agents.py`:
```python
import subprocess
import sys
import pathlib

SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "derive_dynamic_agents.py"

ROLES = [
    "application-architect", "software-architect", "technical-architect",
    "data-modeler", "part-leader",
    "backend-developer", "batch-developer", "web-developer",
    "web-publisher", "designer",
    "database-administrator", "security-specialist", "infrastructure-engineer",
]

def test_script_exists():
    assert SCRIPT.exists()

def test_script_runs_dry_run():
    r = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

def test_script_produces_all_files(tmp_path, monkeypatch):
    # point script at a fake root using env var
    project_root = pathlib.Path(__file__).parent.parent
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True,
        cwd=project_root,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    for role in ROLES:
        for model in ("opus", "sonnet", "haiku"):
            out = project_root / ".claude" / "agents" / f"{role}-{model}.md"
            assert out.exists(), f"missing: {out}"

def test_all_derived_files_pass_validation():
    project_root = pathlib.Path(__file__).parent.parent
    validator = project_root / "scripts" / "validate_agent.py"
    paths = []
    for role in ROLES:
        for model in ("opus", "sonnet", "haiku"):
            paths.append(str(project_root / ".claude" / "agents" / f"{role}-{model}.md"))
    r = subprocess.run([sys.executable, str(validator), *paths], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 2: Run test — expect failure**

```bash
cd /home/earth/ai_team && python3 -m pytest tests/test_derive_dynamic_agents.py -v
```
Expected: all tests fail (script missing).

- [ ] **Step 3: Write the derivation script**

Content of `scripts/derive_dynamic_agents.py`:
```python
#!/usr/bin/env python3
"""Derive <role>-<model>.md agent files from .md.tmpl templates.

Reads every .md.tmpl in .claude/agents/templates/, substitutes
__NAME__ and __MODEL__ tokens in the frontmatter, and writes three
files per template: opus/sonnet/haiku variants.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_DIR = ROOT / ".claude" / "agents" / "templates"
OUTPUT_DIR = ROOT / ".claude" / "agents"

MODELS = ("opus", "sonnet", "haiku")


def derive_one(template_path: pathlib.Path, dry_run: bool = False):
    role = template_path.name.replace(".md.tmpl", "")
    template_text = template_path.read_text()
    results = []
    for model in MODELS:
        name = f"{role}-{model}"
        out_text = template_text.replace("__NAME__", name).replace("__MODEL__", model)
        out_path = OUTPUT_DIR / f"{name}.md"
        if dry_run:
            print(f"would write: {out_path}")
        else:
            out_path.write_text(out_text)
            print(f"wrote: {out_path}")
        results.append(out_path)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    templates = sorted(TEMPLATES_DIR.glob("*.md.tmpl"))
    if not templates:
        print(f"no templates found in {TEMPLATES_DIR}", file=sys.stderr)
        sys.exit(1)
    for t in templates:
        # skip artifacts/ subdirectory templates if any matched (sanity)
        if "artifacts" in t.parts:
            continue
        derive_one(t, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run derivation and re-run tests**

```bash
cd /home/earth/ai_team && python3 scripts/derive_dynamic_agents.py
cd /home/earth/ai_team && python3 -m pytest tests/test_derive_dynamic_agents.py -v
```
Expected: script prints 39 "wrote:" lines; pytest reports all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /home/earth/ai_team
git add scripts/derive_dynamic_agents.py tests/test_derive_dynamic_agents.py .claude/agents/*.md
git commit -m "feat: derivation script + generated 39 dynamic agent files"
```

---

## Artifact Template Tasks (26–34)

Each artifact template is a Markdown file whose content is a skeleton with YAML frontmatter reserving the required fields. Every artifact template should open with:

```markdown
---
# (fields defined per-template below)
---

# <Artifact title — Korean>
```

Frontmatter fields common to every artifact template:

```yaml
id: <leave blank — the author fills this in>
type: <artifact-type-tag e.g. "requirements" | "architecture" | "review-meeting">
stage: <00_kickoff | 01_analysis | 02_design | 03_implementation | 04_test | 05_deployment | 99_audit>
date: <YYYY-MM-DD — author fills>
author: <agent name that produced this>
related: []   # list of RQ/DSN/PRG/UT/IT/UAT IDs linked to this artifact
reviewed-by: []   # list of review file paths once reviewed
```

The `## Language` rule applies to artifacts too: write content in Korean.

Each task below specifies the additional frontmatter fields (if any) and the body skeleton (section headings) for one or more templates.

---

## Task 26: Analysis-stage artifact templates

**Files:**
- Create: `/home/earth/ai_team/.claude/agents/templates/artifacts/requirements.md.tmpl`
- Create: `/home/earth/ai_team/.claude/agents/templates/artifacts/as-is-analysis.md.tmpl`
- Create: `/home/earth/ai_team/.claude/agents/templates/artifacts/to-be-workflow.md.tmpl`
- Create: `/home/earth/ai_team/.claude/agents/templates/artifacts/uat-test-cases.md.tmpl`
- Create: `/home/earth/ai_team/.claude/agents/templates/artifacts/integration-test-cases.md.tmpl`

- [ ] **Step 1: Write each template**

`requirements.md.tmpl`:
```markdown
---
type: requirements
stage: 01_analysis
date:
author: application-architect
related: []
reviewed-by: []
---

# 요구사항정의서

## 개요
(SOW 요약 및 본 문서의 목적)

## 요구사항 목록

| REQ-ID | 요구사항명 | 유형 | 출처 | 설명 | 수용 기준 |
|--------|-----------|------|------|------|-----------|
| RQ-001 | (예) 로그인 | 기능 | SOW §3.2 | (설명) | (수용 기준) |

## 제약사항
...

## 가정 및 의존성
...
```

`as-is-analysis.md.tmpl`:
```markdown
---
type: as-is-analysis
stage: 01_analysis
date:
author: application-architect
related: []
reviewed-by: []
---

# 현황분석서

## 범위
...

## 업무 현황
(프로세스, 시스템, 데이터 흐름 각각 섹션)

## 문제점 및 개선 기회
...

## 관련 요구사항
- 본 분석이 근거를 제공하는 RQ-ID: ...
```

`to-be-workflow.md.tmpl`:
```markdown
---
type: to-be-workflow
stage: 01_analysis
date:
author: application-architect
related: []
reviewed-by: []
---

# To-Be 업무흐름도

## 범위
...

## 주요 업무 흐름
(다이어그램 텍스트 표현 또는 Mermaid 블록)

## RQ-ID별 지원 흐름
| RQ-ID | 해당 업무 흐름 단계 |
|-------|-------------------|
| RQ-001 | ... |

## 예외 및 엣지 시나리오
...
```

`uat-test-cases.md.tmpl`:
```markdown
---
type: uat-test-cases
stage: 01_analysis
date:
author: tester
related: []
reviewed-by: []
---

# 사용자 인수 테스트(UAT) 케이스 설계서

## 케이스 목록

| UAT-ID | 관련 RQ | 전제 조건 | 단계 | 기대 결과 | 우선순위 |
|--------|---------|-----------|------|-----------|----------|
| UAT-01 | RQ-001 | ... | ... | ... | 높음 |

## 수용 기준 요약
...
```

`integration-test-cases.md.tmpl`:
```markdown
---
type: integration-test-cases
stage: 01_analysis
date:
author: tester
related: []
reviewed-by: []
---

# 통합 테스트 케이스 설계서

## 케이스 목록

| IT-ID | 관련 RQ | 관련 인터페이스/모듈 | 전제 | 단계 | 기대 결과 |
|-------|---------|-------------------|------|------|-----------|
| IT-01 | RQ-001 | ... | ... | ... | ... |
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/requirements.md.tmpl \
        .claude/agents/templates/artifacts/as-is-analysis.md.tmpl \
        .claude/agents/templates/artifacts/to-be-workflow.md.tmpl \
        .claude/agents/templates/artifacts/uat-test-cases.md.tmpl \
        .claude/agents/templates/artifacts/integration-test-cases.md.tmpl
git commit -m "feat(artifacts): analysis-stage templates"
```

---

## Task 27: Design-stage artifact templates (design-side)

**Files:**
- Create: `.claude/agents/templates/artifacts/architecture.md.tmpl`
- Create: `.claude/agents/templates/artifacts/db-logical.md.tmpl`
- Create: `.claude/agents/templates/artifacts/db-physical.md.tmpl`
- Create: `.claude/agents/templates/artifacts/screen-spec.md.tmpl`
- Create: `.claude/agents/templates/artifacts/interface-spec.md.tmpl`
- Create: `.claude/agents/templates/artifacts/program-list.md.tmpl`
- Create: `.claude/agents/templates/artifacts/unit-test-cases.md.tmpl`
- Create: `.claude/agents/templates/artifacts/security-review.md.tmpl`

- [ ] **Step 1: Write each template**

`architecture.md.tmpl`:
```markdown
---
type: architecture
stage: 02_design
date:
author: technical-architect
related: []
reviewed-by: []
---

# 아키텍처 설계서

## 개요 및 목적
## 레이어 구성
(애플리케이션 / 데이터 / 인프라 / 통합)

## 컴포넌트 목록
| DESIGN-ID | 컴포넌트 | 설명 | 관련 RQ |
|-----------|---------|------|---------|

## 배포 토폴로지
## 비기능 목표 (성능/가용성/보안/운영)
## 외부 연계
## 주요 설계 의사결정과 근거
```

`db-logical.md.tmpl`:
```markdown
---
type: db-logical
stage: 02_design
date:
author: data-modeler
related: []
reviewed-by: []
---

# DB 논리 설계서

## ERD
## 엔티티 정의
| 엔티티 | 설명 | 주요 속성 | 식별자 |
|--------|------|----------|--------|

## 관계
## 제약사항 (도메인, 무결성)
## 관련 요구사항 맵
| DESIGN-ID | 엔티티 | 관련 RQ |
```

`db-physical.md.tmpl`:
```markdown
---
type: db-physical
stage: 02_design
date:
author: data-modeler
related: []
reviewed-by: []
---

# DB 물리 설계서

## 테이블 정의
| 테이블 | 컬럼 | 자료형 | NULL | 기본값 | 설명 | 관련 DESIGN-ID |
|--------|------|--------|------|--------|------|----------------|

## 인덱스·파티션·보관 주기
## 백업·복구·장애 대응
## DBA 리뷰 반영 이력
```

`screen-spec.md.tmpl`:
```markdown
---
type: screen-spec
stage: 02_design
date:
author: designer
related: []
reviewed-by: []
---

# 화면 설계서

## 화면 목록
| DESIGN-ID | 화면명 | 관련 RQ | URL/경로 |

## 화면별 상세
(각 화면: 목적, 레이아웃, 주요 요소, 상호작용, 에러/예외 상태, 접근성 요건)
```

`interface-spec.md.tmpl`:
```markdown
---
type: interface-spec
stage: 02_design
date:
author: software-architect
related: []
reviewed-by: []
---

# 인터페이스 정의서

## 인터페이스 목록
| DESIGN-ID | 인터페이스명 | 유형(내부/외부) | 프로토콜 | 관련 RQ |

## 상세 정의 (요청/응답/에러)
```

`program-list.md.tmpl`:
```markdown
---
type: program-list
stage: 02_design
date:
author: software-architect
related: []
reviewed-by: []
---

# 프로그램 목록

| PRG-ID | 프로그램명 | 유형(API/화면/배치) | 관련 DESIGN-ID | 관련 RQ |
```

`unit-test-cases.md.tmpl`:
```markdown
---
type: unit-test-cases
stage: 02_design
date:
author: tester
related: []
reviewed-by: []
---

# 단위 테스트 케이스 설계서

| UT-ID | 관련 PRG-ID | 입력 | 기대 결과 | 비고 |
```

`security-review.md.tmpl`:
```markdown
---
type: security-review
stage: 02_design
date:
author: security-specialist
related: []
reviewed-by: []
---

# 보안 검토서

## 위협 모델
## 통제 매트릭스 (자산 × 위협 × 통제)
## 위험 수용 / 완화 결정
## 관련 RQ-ID (특히 비기능·보안 요구사항)
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/architecture.md.tmpl \
        .claude/agents/templates/artifacts/db-logical.md.tmpl \
        .claude/agents/templates/artifacts/db-physical.md.tmpl \
        .claude/agents/templates/artifacts/screen-spec.md.tmpl \
        .claude/agents/templates/artifacts/interface-spec.md.tmpl \
        .claude/agents/templates/artifacts/program-list.md.tmpl \
        .claude/agents/templates/artifacts/unit-test-cases.md.tmpl \
        .claude/agents/templates/artifacts/security-review.md.tmpl
git commit -m "feat(artifacts): design-stage templates"
```

---

## Task 28: Test-stage artifact templates

**Files:**
- Create: `.claude/agents/templates/artifacts/unit-test-results.md.tmpl`
- Create: `.claude/agents/templates/artifacts/integration-test-results.md.tmpl`
- Create: `.claude/agents/templates/artifacts/system-test-results.md.tmpl`
- Create: `.claude/agents/templates/artifacts/uat-results.md.tmpl`
- Create: `.claude/agents/templates/artifacts/qa-report.md.tmpl`

- [ ] **Step 1: Write each template**

`unit-test-results.md.tmpl`:
```markdown
---
type: unit-test-results
stage: 03_implementation
date:
author: multiple  # PM consolidates across developers
related: []
reviewed-by: []
---

# 단위 테스트 실행 결과서

| UT-ID | PRG-ID | 수행자 | 결과(PASS/FAIL) | 증거/로그 위치 | 비고 |
```

`integration-test-results.md.tmpl`:
```markdown
---
type: integration-test-results
stage: 04_test
date:
author: tester
related: []
reviewed-by: []
---

# 통합 테스트 실행 결과서

| IT-ID | 관련 RQ | 결과 | 증거 | 비고 |
```

`system-test-results.md.tmpl`:
```markdown
---
type: system-test-results
stage: 04_test
date:
author: tester
related: []
reviewed-by: []
---

# 시스템 테스트 결과서

## 성능·부하·안정성 결과 요약
## 결과 상세 (시나리오별)
```

`uat-results.md.tmpl`:
```markdown
---
type: uat-results
stage: 04_test
date:
author: tester
related: []
reviewed-by: []
---

# UAT 실행 결과서

| UAT-ID | 관련 RQ | 결과 | 피드백 | 비고 |
```

`qa-report.md.tmpl`:
```markdown
---
type: qa-report
stage: 04_test
date:
author: quality-assurance
related: []
reviewed-by: []
---

# QA 보고서

## 품질 지표 요약
## 주요 결함 및 조치 현황
## 품질 판정 (통과/유보/불가)
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/unit-test-results.md.tmpl \
        .claude/agents/templates/artifacts/integration-test-results.md.tmpl \
        .claude/agents/templates/artifacts/system-test-results.md.tmpl \
        .claude/agents/templates/artifacts/uat-results.md.tmpl \
        .claude/agents/templates/artifacts/qa-report.md.tmpl
git commit -m "feat(artifacts): test-stage templates"
```

---

## Task 29: Deployment-stage artifact templates

**Files:**
- Create: `.claude/agents/templates/artifacts/deployment-plan.md.tmpl`
- Create: `.claude/agents/templates/artifacts/operation-manual.md.tmpl`
- Create: `.claude/agents/templates/artifacts/training-material.md.tmpl`

- [ ] **Step 1: Write each template**

`deployment-plan.md.tmpl`:
```markdown
---
type: deployment-plan
stage: 05_deployment
date:
author: project-manager
related: []
reviewed-by: []
---

# 이행 계획서

## 범위 및 목표
## 이행 일정
## 환경·구성
## 이행 절차 (전/중/후)
## 롤백 계획
## 리스크 및 대응
```

`operation-manual.md.tmpl`:
```markdown
---
type: operation-manual
stage: 05_deployment
date:
author: multiple
related: []
reviewed-by: []
---

# 운영 매뉴얼

## 아키텍처 요약
## 주요 운영 절차 (시작/종료/모니터링/백업)
## 장애 대응 절차
## 연락 체계
```

`training-material.md.tmpl`:
```markdown
---
type: training-material
stage: 05_deployment
date:
author: multiple
related: []
reviewed-by: []
---

# 교육 자료

## 대상·목표
## 주요 기능 소개
## 실습 시나리오
## FAQ
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/deployment-plan.md.tmpl \
        .claude/agents/templates/artifacts/operation-manual.md.tmpl \
        .claude/agents/templates/artifacts/training-material.md.tmpl
git commit -m "feat(artifacts): deployment-stage templates"
```

---

## Task 30: Review meeting template

**Files:**
- Create: `.claude/agents/templates/artifacts/review-meeting.md.tmpl`

- [ ] **Step 1: Write the template**

```markdown
---
type: review-meeting
target:            # path to the artifact being reviewed
target-version: v1
stage:             # fill in
date:
participants:      # MUST have >= 2 entries
  - <author-agent-name> (author)
  - <reviewer-agent-name>
related: []
---

# Review Meeting — <target name>

## Target
- File: <target path>
- Version: v1

## Findings
- [OPEN] (참여자명) (근거)
- [RESOLVED] (참여자명) (근거)

## Decisions
- ...

## Follow-up Actions
- [ ] <책임자>: <조치> (due: YYYY-MM-DD)
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/review-meeting.md.tmpl
git commit -m "feat(artifacts): review-meeting template"
```

---

## Task 31: Audit artifact templates

**Files:**
- Create: `.claude/agents/templates/artifacts/audit-plan.md.tmpl`
- Create: `.claude/agents/templates/artifacts/audit-report.md.tmpl`
- Create: `.claude/agents/templates/artifacts/corrective-action-plan.md.tmpl`
- Create: `.claude/agents/templates/artifacts/corrective-action-result.md.tmpl`
- Create: `.claude/agents/templates/artifacts/re-audit-report.md.tmpl`

- [ ] **Step 1: Write each template**

`audit-plan.md.tmpl`:
```markdown
---
type: audit-plan
stage: 99_audit
audit-cycle:          # A-AUDIT-1 | D-AUDIT-1 | C-AUDIT-1 ...
date:
author: audit-team
related: []
---

# 감리 계획서

## 범위 (대상 단계 및 산출물)
## 방법 (검토 기준, 근거 자료)
## 일정
```

`audit-report.md.tmpl`:
```markdown
---
type: audit-report
stage: 99_audit
audit-cycle:
date:
author: audit-team
related: []
result:               # PASS | FINDINGS — 사실 기반, 심각도 판단 없음
---

# 감리 결과서

## 지적사항
| 번호 | 제목 | 사실 기술 | 근거 위치(파일/라인/ID) | 관련 RQ/DSN/PRG |
|------|------|-----------|------------------------|-----------------|

## 확인 사항 (문제 없음)
- ...
```

`corrective-action-plan.md.tmpl`:
```markdown
---
type: corrective-action-plan
stage: 99_audit
audit-cycle:
date:
author:                # 배정된 담당자 agent 명
related: []
targets:               # 원 지적사항 번호 나열
---

# 시정조치 계획서

## 지적사항 요약
## 조치 방침
## 영향 범위 및 관련 ID
## 일정 및 담당
```

`corrective-action-result.md.tmpl`:
```markdown
---
type: corrective-action-result
stage: 99_audit
audit-cycle:
date:
author:
related: []
targets:
---

# 시정조치 결과서

## 실제 변경 사항 (파일/라인/DESIGN-ID/PRG-ID)
## 재검증 내역
## 남은 이슈 (있을 시)
```

`re-audit-report.md.tmpl`:
```markdown
---
type: re-audit-report
stage: 99_audit
audit-cycle:           # 예: RA-AUDIT-2-v1
date:
author: audit-team
related: []
result:                # PASS | FINDINGS
---

# 재감리 결과서

## 이전 지적사항 해소 여부
| 이전 번호 | 지적 요약 | 해소 여부 | 근거 위치 |
|-----------|----------|----------|-----------|

## (해소되지 않은 경우) 동일 근거 기술만 반복
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/audit-plan.md.tmpl \
        .claude/agents/templates/artifacts/audit-report.md.tmpl \
        .claude/agents/templates/artifacts/corrective-action-plan.md.tmpl \
        .claude/agents/templates/artifacts/corrective-action-result.md.tmpl \
        .claude/agents/templates/artifacts/re-audit-report.md.tmpl
git commit -m "feat(artifacts): audit templates"
```

---

## Task 32: Kickoff and project-state templates

**Files:**
- Create: `.claude/agents/templates/artifacts/project-plan.md.tmpl`
- Create: `.claude/agents/templates/artifacts/project-state.md.tmpl`

- [ ] **Step 1: Write each template**

`project-plan.md.tmpl`:
```markdown
---
type: project-plan
stage: 00_kickoff
date:
author: project-manager
related: []
reviewed-by: []
---

# 프로젝트 수행 계획서

## 개요
## 범위 및 목표
## 조직 및 역할 (응용/인프라/사업관리/QA/tester)
## 규모 (small | large)
## 일정 (WBS 수준)
## 비용 및 공수 (사업관리 입력)
## 품질 계획 (QA 입력)
## 리스크 및 이슈 관리
## 이해관계자 커뮤니케이션 계획
```

`project-state.md.tmpl`:
```markdown
---
project:
started:
scale:               # small | large
current-stage: 00_kickoff
current-step:
---

# Project State

## Scale Configuration
- Size:
- Part Leaders: (enabled if large)

## Stage Progress
- [ ] 00_kickoff
- [ ] 01_analysis
- [ ] 02_design
- [ ] 03_implementation
- [ ] 04_test
- [ ] 05_deployment

## Approval Log

| Stage | Deliverables | Approved By | Date |
|-------|--------------|-------------|------|

## Audit Log

| Audit ID | Type | Result | Findings | Corrective Actions |
|----------|------|--------|----------|-------------------|

## Rollback History

| Date | Trigger | Rolled-back to | Archived versions | Reason |
|------|---------|----------------|-------------------|--------|
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/project-plan.md.tmpl \
        .claude/agents/templates/artifacts/project-state.md.tmpl
git commit -m "feat(artifacts): kickoff and project-state templates"
```

---

## Task 33: RTM template

**Files:**
- Create: `.claude/agents/templates/artifacts/rtm.md.tmpl`

- [ ] **Step 1: Write the template**

```markdown
---
type: rtm
project:
date:
author: project-manager
---

# 요구사항 추적 매트릭스 (RTM)

## 작성 규칙
- REQ-ID 는 요구사항정의서와 동일 ID 사용.
- 단계가 끝날 때마다 해당 단계 컬럼을 채운다. 채움 주체: PM (단독 수정자).
- Rollback 시: 현재 파일을 `RTM/_archived/<YYYYMMDD>-v<N>.md` 로 이동하고 새 RTM 을 생성한다.

## 매트릭스

| REQ-ID | 요구사항명 | 유형 | 출처 | DESIGN-ID | 설계문서 | PROG-ID | 소스경로 | UT-ID | IT-ID | UAT-ID | 결과 | 감리이력 | 상태 |
|--------|-----------|------|------|-----------|---------|---------|---------|-------|-------|--------|------|---------|------|
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/rtm.md.tmpl
git commit -m "feat(artifacts): RTM template"
```

---

## Task 34: Change-request, escalations, rollback-history templates

**Files:**
- Create: `.claude/agents/templates/artifacts/cr.md.tmpl`
- Create: `.claude/agents/templates/artifacts/escalations.md.tmpl`
- Create: `.claude/agents/templates/artifacts/rollback-history.md.tmpl`

- [ ] **Step 1: Write each template**

`cr.md.tmpl`:
```markdown
---
type: change-request
cr-id:
project:
requested-by: user
date:
status: open | approved | rejected | completed
related: []
---

# 변경 요청 (CR-<seq>)

## 요청 내용
## 요청 사유 및 배경
## PM 영향 분석 (응용/인프라 병렬 결과 반영)
## 일정·비용·리스크 영향
## 의사결정 (승인/거절/조건부)
## 반영 계획 (승인된 경우: 어느 단계로 복귀하여 어떤 산출물 갱신)
```

`escalations.md.tmpl`:
```markdown
---
type: escalations
project:
author: project-manager
---

# 에스컬레이션 로그

| Date | From | Issue | Resolved By | Resolution |
|------|------|-------|-------------|-----------|
```

`rollback-history.md.tmpl`:
```markdown
---
type: rollback-history
project:
author: project-manager
---

# Rollback 이벤트 로그

| Date | Trigger | Rolled-back to | Archived versions | Reason |
|------|---------|----------------|-------------------|--------|
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add .claude/agents/templates/artifacts/cr.md.tmpl \
        .claude/agents/templates/artifacts/escalations.md.tmpl \
        .claude/agents/templates/artifacts/rollback-history.md.tmpl
git commit -m "feat(artifacts): CR, escalations, rollback-history templates"
```

---

## Task 35: Root README with agent catalog

**Files:**
- Create: `/home/earth/ai_team/README.md`

- [ ] **Step 1: Write the README**

```markdown
# AI SI Project Team

Claude Code multi-subagent system that replicates an enterprise SI
(System Integration) project execution organization.

- Spec: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`
- Plan: `docs/superpowers/plans/2026-04-17-ai-si-team-build.md`

## Quick Start (once the system is in place)

1. As the client (user), drop a statement-of-work into
   `projects/<name>/00_kickoff/statement-of-work.md`.
2. Talk to the **project-manager** agent. PM is the single contact
   point; it orchestrates everything else.
3. At each stage gate, PM reports to you and waits for your approval.
4. When PM signals an audit is due, start a session with the
   **audit-team** agent (external auditor, isolated in `audit/`).

## Agent Catalog

### Fixed-model agents (7)
- `project-manager` — Opus, xhigh, the user-facing orchestrator.
- `application-director` — Opus, xhigh, application track leader.
- `infrastructure-director` — Opus, xhigh, infrastructure track leader.
- `business-manager` — Sonnet, xhigh, schedule/cost/CR impact.
- `quality-assurance` — Sonnet, xhigh, quality criteria and QA report.
- `tester` — Sonnet, xhigh, UAT/IT/UT design & execution.
- `audit/audit-team` — Sonnet, xhigh, external auditor (independent).

### Dynamic-model agents (13 × 3 = 39)
Each role has `-opus`, `-sonnet`, `-haiku` variants. The upstream caller
picks the variant based on the task's difficulty (spec §2-3).

- `application-architect` (AA)
- `software-architect` (SWA)
- `technical-architect` (TA)
- `data-modeler`
- `part-leader` (activated in large-scale projects; has Agent tool)
- `backend-developer`, `batch-developer`, `web-developer`,
  `web-publisher`, `designer`
- `database-administrator` (DBA)
- `security-specialist`
- `infrastructure-engineer`

## Artifact Templates

See `.claude/agents/templates/artifacts/`. Every stage's expected
deliverables have a template with the required frontmatter and body
skeleton.

## Stage Gates

`.claude/agents/templates/stage-gates.md` lists the mandatory artifacts,
reviews, audits, and approvals required to close each stage.

## Validation Scripts

```bash
# Validate a single agent file
python3 scripts/validate_agent.py .claude/agents/project-manager.md

# Validate every agent file
python3 scripts/validate_agent.py $(ls .claude/agents/*.md)

# Re-derive the 39 dynamic variants from templates
python3 scripts/derive_dynamic_agents.py

# Run tests
python3 -m pytest tests/ -v
```

## Unresolved items (see spec §10)

- Sample project domain (for future meta-test E2E).
- Parallel-write file locking strategy (currently convention-only).
- Part-leader count in large mode (one vs. per-domain).
- Audit session kickoff UX (slash command vs. natural language).
```

- [ ] **Step 2: Commit**

```bash
cd /home/earth/ai_team
git add README.md
git commit -m "docs: add README with agent catalog and quickstart"
```

---

## Task 36: Full-project validation smoke test

**Files:**
- Create: `/home/earth/ai_team/tests/test_all_agents_valid.py`

- [ ] **Step 1: Write the smoke test**

```python
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
VALIDATOR = ROOT / "scripts" / "validate_agent.py"

EXPECTED_FIXED = [
    "project-manager.md",
    "application-director.md",
    "infrastructure-director.md",
    "business-manager.md",
    "quality-assurance.md",
    "tester.md",
    "audit/audit-team.md",
]

DYNAMIC_ROLES = [
    "application-architect", "software-architect", "technical-architect",
    "data-modeler", "part-leader",
    "backend-developer", "batch-developer", "web-developer",
    "web-publisher", "designer",
    "database-administrator", "security-specialist", "infrastructure-engineer",
]
DYNAMIC_EXPECTED = [
    f"{role}-{m}.md" for role in DYNAMIC_ROLES for m in ("opus", "sonnet", "haiku")
]

def test_fixed_agents_exist_and_validate():
    paths = [ROOT / ".claude" / "agents" / p for p in EXPECTED_FIXED]
    for p in paths:
        assert p.exists(), f"missing fixed agent: {p}"
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), *map(str, paths)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr

def test_dynamic_agents_exist_and_validate():
    paths = [ROOT / ".claude" / "agents" / p for p in DYNAMIC_EXPECTED]
    for p in paths:
        assert p.exists(), f"missing dynamic agent: {p}"
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), *map(str, paths)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr

def test_stage_gates_present():
    assert (ROOT / ".claude" / "agents" / "templates" / "stage-gates.md").exists()

def test_all_required_artifact_templates_present():
    required = [
        "requirements.md.tmpl", "as-is-analysis.md.tmpl",
        "to-be-workflow.md.tmpl", "uat-test-cases.md.tmpl",
        "integration-test-cases.md.tmpl",
        "architecture.md.tmpl", "db-logical.md.tmpl", "db-physical.md.tmpl",
        "screen-spec.md.tmpl", "interface-spec.md.tmpl",
        "program-list.md.tmpl", "unit-test-cases.md.tmpl",
        "security-review.md.tmpl",
        "unit-test-results.md.tmpl", "integration-test-results.md.tmpl",
        "system-test-results.md.tmpl", "uat-results.md.tmpl",
        "qa-report.md.tmpl",
        "deployment-plan.md.tmpl", "operation-manual.md.tmpl",
        "training-material.md.tmpl",
        "review-meeting.md.tmpl",
        "audit-plan.md.tmpl", "audit-report.md.tmpl",
        "corrective-action-plan.md.tmpl",
        "corrective-action-result.md.tmpl",
        "re-audit-report.md.tmpl",
        "project-plan.md.tmpl", "project-state.md.tmpl",
        "rtm.md.tmpl",
        "cr.md.tmpl", "escalations.md.tmpl", "rollback-history.md.tmpl",
    ]
    for t in required:
        p = ROOT / ".claude" / "agents" / "templates" / "artifacts" / t
        assert p.exists(), f"missing template: {p}"
```

- [ ] **Step 2: Run tests**

```bash
cd /home/earth/ai_team && python3 -m pytest tests/ -v
```
Expected: all tests pass (from this file, the frontmatter validator file, and the derivation file).

- [ ] **Step 3: Commit**

```bash
cd /home/earth/ai_team
git add tests/test_all_agents_valid.py
git commit -m "test: full-project structural validation smoke test"
```

---

## Completion Criteria

When every task above is complete and every test passes, the AI SI Project Team infrastructure is ready. Next steps (not in this plan):

- **Follow-up plan 1:** Sample-project E2E meta-test. Pick a domain (per spec §10), draft a short statement-of-work, and drive the full flow from kickoff to closing audit. Adjust agents based on observed friction.
- **Follow-up plan 2:** Meta-tests 2–6 from spec §8-7 (agent persona, audit independence, 2-person review, rollback, parallel-write).

---

## Self-Review Notes

- **Spec coverage:** Every section of the spec is referenced by at least one task. §1 aggregated in overall structure; §2 in Tasks 3, 5–25; §3 in Task 27–29; §4 in Task 31; §5 in Task 33; §6 in Tasks 4, 32; §7 in Task 30 and each agent prompt's Rules; §8 in Task 34 + each prompt.
- **Placeholder check:** All `<...>` markers in this plan are clearly marked as content the implementer fills at author-time (not plan-time), e.g. `<Korean role name>`. No step contains "TBD", "implement later", or "fill in details" as hidden placeholders.
- **Type consistency:** Role names, file paths, and ID prefixes are consistent across all tasks and match the spec's Section 5-2 naming rules.
