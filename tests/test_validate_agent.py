"""Tests for scripts/validate_agent.py (v2 roles/agents/skills validator)."""
import subprocess
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "validate_agent.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


# ---------- Builders --------------------------------------------------------

def role_fm(name="application-director", description="|\n  Two-line\n  description."):
    return "---\n" + f"name: {name}\ndescription: {description}\n" + "---\n"


def role_body(with_invoke=True, with_consult=True):
    parts = [
        "\n# Role: 응용총괄\n",
        "\n## Mission\nLead.\n",
        "\n## Responsibilities\nCoordinate.\n",
    ]
    if with_invoke:
        parts.append("\n## How You Invoke Sub-executions (Track A)\n| t | dst | why | ctx |\n|---|----|----|----|\n")
    if with_consult:
        parts.append("\n## How You Consult Advisors (Track B)\n| s | dst | why |\n|---|----|----|\n")
    parts.extend([
        "\n## How You Report\nTo PM.\n",
        "\n## Artifacts You Own\nreview records.\n",
        "\n## Rules\nDelegation chain enforced.\n",
        "\n## Language\n한국어.\n",
    ])
    return "".join(parts)


def agent_fm(name="backend-developer-sonnet", model="sonnet", effort="xhigh",
             tools="[Read, Glob, Grep]", description="|\n  Backend dev shell."):
    return ("---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            f"tools: {tools}\n"
            f"model: {model}\n"
            f"effort: {effort}\n"
            "---\n")


def agent_body(role_ref="backend-developer"):
    return (f"\n# Role: Shell\n\n이 껍데기는 `.claude/roles/{role_ref}.md` 를 참조합니다.\n")


def skill_fm(name="project-manager", model="opus", effort="xhigh",
             description="|\n  PM loader skill."):
    return ("---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            f"model: {model}\n"
            f"effort: {effort}\n"
            "---\n")


def skill_body(role_ref="project-manager"):
    return (f"\n# Skill: PM\n\n로드: `.claude/roles/{role_ref}.md`\n")


def write_role(tmp_path, name, content):
    d = tmp_path / ".claude" / "roles"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{name}.md"
    p.write_text(content)
    return p


def write_agent(tmp_path, name, content):
    d = tmp_path / ".claude" / "agents"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{name}.md"
    p.write_text(content)
    return p


def write_skill(tmp_path, name, content):
    d = tmp_path / ".claude" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    p = d / "SKILL.md"
    p.write_text(content)
    return p


# ---------- Role tests -----------------------------------------------------

def test_valid_role_passes(tmp_path):
    p = write_role(tmp_path, "application-director", role_fm() + role_body())
    r = run(str(p))
    assert r.returncode == 0, r.stdout + r.stderr


def test_role_name_mismatch_fails(tmp_path):
    p = write_role(tmp_path, "different-name", role_fm(name="application-director") + role_body())
    r = run(str(p))
    assert r.returncode != 0
    assert "name" in r.stdout


def test_role_with_tools_field_fails(tmp_path):
    fm = role_fm() + ""
    # Insert tools key inside frontmatter
    bad_fm = fm.replace("---\n", "---\ntools: [Read, Write]\n", 1)
    # The above inserts tools before the opening '---' -- correct instead:
    bad_fm = fm.replace("name: application-director\n",
                        "name: application-director\ntools: [Read, Write]\n")
    p = write_role(tmp_path, "application-director", bad_fm + role_body())
    r = run(str(p))
    assert r.returncode != 0
    assert "tools" in r.stdout


def test_role_missing_mission_fails(tmp_path):
    body = role_body().replace("\n## Mission\nLead.\n", "")
    p = write_role(tmp_path, "application-director", role_fm() + body)
    r = run(str(p))
    assert r.returncode != 0


def test_role_missing_invocation_contract_fails(tmp_path):
    # spec 2026-05-16: every role must declare one invocation-contract section
    # ('호출·산출 계약 (ledger)' / 'ledger NEXT' / 'Invoke Sub-executions').
    body = role_body(with_invoke=False, with_consult=False)
    p = write_role(tmp_path, "application-director", role_fm() + body)
    r = run(str(p))
    assert r.returncode != 0


def test_audit_team_role_follows_ledger_contract(tmp_path):
    # spec 2026-05-16: claude -p 폐기. audit-team is no longer track-section
    # exempt; like every authoring node it declares the ledger contract.
    body = (role_body(with_invoke=False, with_consult=False)
            + "\n## 호출·산출 계약 (ledger)\n감리 산출.\n")
    p = write_role(tmp_path, "audit-team", role_fm(name="audit-team") + body)
    r = run(str(p))
    assert r.returncode == 0, r.stdout + r.stderr


def test_unknown_role_name_fails(tmp_path):
    # 'random-name' is not one of the 21 defined roles
    p = write_role(tmp_path, "random-name", role_fm(name="random-name") + role_body())
    r = run(str(p))
    assert r.returncode != 0
    assert "unknown role-name" in r.stdout


# ---------- Agent shell tests ---------------------------------------------

def test_valid_agent_shell_passes(tmp_path):
    p = write_agent(tmp_path, "backend-developer-sonnet", agent_fm() + agent_body())
    r = run(str(p))
    assert r.returncode == 0, r.stdout + r.stderr


def test_agent_with_agent_tool_fails(tmp_path):
    p = write_agent(tmp_path, "backend-developer-sonnet",
                    agent_fm(tools="[Read, Glob, Grep, Agent]") + agent_body())
    r = run(str(p))
    assert r.returncode != 0


def test_agent_with_task_tool_fails(tmp_path):
    p = write_agent(tmp_path, "backend-developer-sonnet",
                    agent_fm(tools="[Read, Glob, Grep, TaskCreate]") + agent_body())
    r = run(str(p))
    assert r.returncode != 0


def test_agent_tools_must_be_exactly_three(tmp_path):
    # Write too — extra beyond Read/Glob/Grep breaks the rule
    p = write_agent(tmp_path, "backend-developer-sonnet",
                    agent_fm(tools="[Read, Glob, Grep, Write]") + agent_body())
    r = run(str(p))
    assert r.returncode != 0


def test_agent_effort_low_fails(tmp_path):
    p = write_agent(tmp_path, "backend-developer-sonnet",
                    agent_fm(effort="low") + agent_body())
    r = run(str(p))
    assert r.returncode != 0


def test_agent_effort_max_fails(tmp_path):
    p = write_agent(tmp_path, "backend-developer-sonnet",
                    agent_fm(effort="max") + agent_body())
    r = run(str(p))
    assert r.returncode != 0


def test_agent_missing_roles_reference_fails(tmp_path):
    # Body without reference to .claude/roles/backend-developer.md
    p = write_agent(tmp_path, "backend-developer-sonnet",
                    agent_fm() + "\n# Shell\nNo roles ref here.\n")
    r = run(str(p))
    assert r.returncode != 0


def test_agent_fixed_role_wrong_model_fails(tmp_path):
    # application-director must be opus
    p = write_agent(tmp_path, "application-director",
                    agent_fm(name="application-director", model="sonnet",
                             description="|\n  Director shell.") +
                    agent_body(role_ref="application-director"))
    r = run(str(p))
    assert r.returncode != 0


def test_agent_fixed_role_correct_model_passes(tmp_path):
    p = write_agent(tmp_path, "application-director",
                    agent_fm(name="application-director", model="opus",
                             description="|\n  Director shell.") +
                    agent_body(role_ref="application-director"))
    r = run(str(p))
    assert r.returncode == 0, r.stdout + r.stderr


def test_agent_dynamic_role_variant_mismatch_fails(tmp_path):
    # File name says -opus but model says sonnet
    p = write_agent(tmp_path, "backend-developer-opus",
                    agent_fm(name="backend-developer-opus", model="sonnet") + agent_body())
    r = run(str(p))
    assert r.returncode != 0


def test_agent_dynamic_all_three_variants_pass(tmp_path):
    for m in ("opus", "sonnet", "haiku"):
        p = write_agent(tmp_path, f"backend-developer-{m}",
                        agent_fm(name=f"backend-developer-{m}", model=m) + agent_body())
        r = run(str(p))
        assert r.returncode == 0, f"{m}: {r.stdout + r.stderr}"


def test_pm_agent_shell_rejected(tmp_path):
    # project-manager is Skill-only; an agent shell must fail
    p = write_agent(tmp_path, "project-manager",
                    agent_fm(name="project-manager", model="opus",
                             description="|\n  PM shell (should not exist).") +
                    agent_body(role_ref="project-manager"))
    r = run(str(p))
    assert r.returncode != 0
    assert "Skill-only" in r.stdout


# ---------- Skill tests ---------------------------------------------------

def test_valid_skill_passes(tmp_path):
    p = write_skill(tmp_path, "project-manager", skill_fm() + skill_body())
    r = run(str(p))
    assert r.returncode == 0, r.stdout + r.stderr


def test_skill_wrong_model_fails(tmp_path):
    p = write_skill(tmp_path, "project-manager",
                    skill_fm(model="sonnet") + skill_body())
    r = run(str(p))
    assert r.returncode != 0


def test_skill_wrong_effort_fails(tmp_path):
    p = write_skill(tmp_path, "project-manager",
                    skill_fm(effort="high") + skill_body())
    r = run(str(p))
    assert r.returncode != 0


def test_skill_missing_roles_ref_fails(tmp_path):
    p = write_skill(tmp_path, "project-manager",
                    skill_fm() + "\n# Skill\nNo roles ref.\n")
    r = run(str(p))
    assert r.returncode != 0


# ---------- Misc ----------------------------------------------------------

def test_file_not_found_fails(tmp_path):
    missing = tmp_path / ".claude" / "roles" / "nope.md"
    r = run(str(missing))
    assert r.returncode != 0


def test_missing_frontmatter_fails(tmp_path):
    p = write_role(tmp_path, "application-director", role_body())  # no frontmatter
    r = run(str(p))
    assert r.returncode != 0


# ---------- claude -p 폐기 drift-guard ------------------------------------

def test_role_with_claude_p_is_rejected(tmp_path):
    # spec 2026-05-16: claude -p subprocess invocation is forbidden in any
    # role/agent/skell file.
    body = (role_body()
            + "\n호출: claude -p --append-system-prompt ...\n")
    p = write_role(tmp_path, "application-director", role_fm() + body)
    r = run(str(p))
    assert r.returncode == 1
    assert "claude -p" in (r.stdout + r.stderr)


def test_all_real_roles_have_no_claude_p():
    # The real repo's roles/agents/skills must be free of claude -p (sole
    # exception: project-manager.md's 'never ... claude -p' description line).
    r = run("--all")
    assert r.returncode == 0, r.stdout + r.stderr


# ---------- Integration: real project files pass --------------------------

def test_all_real_roles_pass():
    """Drift-guard: every .claude/roles/*.md in the real repo must validate."""
    r = run("--all")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK:" in r.stdout
