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
