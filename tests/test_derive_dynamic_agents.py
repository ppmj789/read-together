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

def test_script_produces_all_files():
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


def test_committed_files_match_templates():
    """Guard against template/derived-file drift.

    If a template was edited without re-running derive_dynamic_agents.py,
    the committed <role>-<model>.md will differ from what the template
    would produce now. This test fails loudly in that case.
    """
    project_root = pathlib.Path(__file__).parent.parent
    templates_dir = project_root / ".claude" / "agents" / "templates"
    output_dir = project_root / ".claude" / "agents"
    drifted = []
    for t in sorted(templates_dir.glob("*.md.tmpl")):
        role = t.name.replace(".md.tmpl", "")
        template_text = t.read_text()
        for model in ("opus", "sonnet", "haiku"):
            name = f"{role}-{model}"
            expected = template_text.replace("__NAME__", name).replace("__MODEL__", model)
            committed = (output_dir / f"{name}.md").read_text()
            if expected != committed:
                drifted.append(f"{name}.md")
    assert not drifted, (
        f"{len(drifted)} derived file(s) drifted from their templates. "
        f"Re-run `python3 scripts/derive_dynamic_agents.py` and commit. "
        f"Files: {drifted}"
    )
