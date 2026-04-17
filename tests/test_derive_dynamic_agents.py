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
