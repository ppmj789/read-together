import subprocess
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


def test_audit_team_exempt_from_escalation(tmp_path):
    # audit-team agent has no Agent tool AND no Escalation Protocol -- must still pass
    fm = valid_frontmatter(name="audit-team", tools="[Read, Glob, Grep, Write]", model="sonnet")
    body = (
        "\n# Role: audit\n"
        "\n## Mission\nAudit.\n"
        "\n## Responsibilities\nReview.\n"
        "\n## How You Report\nReports.\n"
        "\n## Artifacts You Own\naudit docs.\n"
        "\n## Rules\nIndependence.\n"
        "\n## Language\nKorean.\n"
    )
    p = write(tmp_path, fm + body)
    r = run([str(p)])
    assert r.returncode == 0, r.stdout + r.stderr


def test_disallowed_tool_fails(tmp_path):
    p = write(tmp_path, valid_frontmatter(tools="[Read, Hammer]") + valid_body())
    r = run([str(p)])
    assert r.returncode != 0
    assert "Hammer" in r.stdout or "Hammer" in r.stderr or "not allowed" in r.stdout


def test_missing_frontmatter_fails(tmp_path):
    p = write(tmp_path, valid_body())  # body only, no ---
    r = run([str(p)])
    assert r.returncode != 0


def test_file_not_found_fails(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    r = run([str(missing)])
    assert r.returncode != 0
    assert "file not found" in r.stderr or "file not found" in r.stdout


def test_multi_file_cli_passes_all_valid(tmp_path):
    # Write two valid agent files in two subdirs
    (tmp_path / "p1").mkdir()
    (tmp_path / "p2").mkdir()
    p1 = tmp_path / "p1" / "agent.md"
    p2 = tmp_path / "p2" / "agent.md"
    p1.write_text(valid_frontmatter() + valid_body())
    p2.write_text(valid_frontmatter(name="other-agent") + valid_body())
    r = run([str(p1), str(p2)])
    assert r.returncode == 0, r.stdout + r.stderr


def test_crlf_line_endings_accepted(tmp_path):
    content = (valid_frontmatter() + valid_body()).replace("\n", "\r\n")
    p = tmp_path / "agent.md"
    p.write_text(content, newline="")
    r = run([str(p)])
    assert r.returncode == 0, r.stdout + r.stderr


def test_block_description_survives_blank_line(tmp_path):
    # description as |-block with blank line inside
    fm = (
        "---\n"
        "name: project-manager\n"
        "description: |\n"
        "  First line of description.\n"
        "\n"
        "  Second paragraph after blank line.\n"
        "tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate]\n"
        "model: opus\n"
        "effort: xhigh\n"
        "---\n"
    )
    p = write(tmp_path, fm + valid_body())
    r = run([str(p)])
    assert r.returncode == 0, r.stdout + r.stderr
