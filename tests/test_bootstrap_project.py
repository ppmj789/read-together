import subprocess
import sys
import pathlib

SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "bootstrap_project.py"
TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / ".claude" / "agents" / "templates" / "artifacts"


def run(*args, **kwargs):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, **kwargs)


def test_bootstrap_rejects_empty_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create a fake project root with templates
    (tmp_path / ".claude" / "agents" / "templates" / "artifacts").mkdir(parents=True)
    r = run("", "--scale", "small")
    assert r.returncode != 0


def test_bootstrap_rejects_unsafe_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".claude" / "agents" / "templates" / "artifacts").mkdir(parents=True)
    r = run("../evil", "--scale", "small")
    assert r.returncode != 0


def test_bootstrap_rejects_bad_scale(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".claude" / "agents" / "templates" / "artifacts").mkdir(parents=True)
    r = run("demo", "--scale", "huge")
    assert r.returncode != 0


def test_bootstrap_refuses_existing_project():
    # Use the real repo root; projects/ must have .gitkeep but no 'demo-existing' entry
    # We'll create and then re-run to trigger the refuse
    project_root = pathlib.Path(__file__).parent.parent
    demo_dir = project_root / "projects" / "demo-bootstrap-test"
    try:
        r = run("demo-bootstrap-test", "--scale", "small", cwd=project_root)
        assert r.returncode == 0, r.stdout + r.stderr
        # Run again — should refuse
        r2 = run("demo-bootstrap-test", "--scale", "small", cwd=project_root)
        assert r2.returncode != 0
    finally:
        # Cleanup the demo directory regardless
        import shutil
        if demo_dir.exists():
            shutil.rmtree(demo_dir)


def test_bootstrap_creates_full_tree_small():
    project_root = pathlib.Path(__file__).parent.parent
    demo_dir = project_root / "projects" / "demo-small"
    try:
        r = run("demo-small", "--scale", "small", cwd=project_root)
        assert r.returncode == 0, r.stdout + r.stderr
        expected_dirs = [
            "00_kickoff", "00_kickoff/reviews",
            "01_analysis", "01_analysis/reviews",
            "02_design", "02_design/reviews",
            "03_implementation", "03_implementation/reviews",
            "04_test", "04_test/reviews",
            "05_deployment", "05_deployment/reviews",
            "99_audit", "99_audit/02_design-audit", "99_audit/03_closing-audit",
            "change-requests", "RTM/_archived",
        ]
        for d in expected_dirs:
            assert (demo_dir / d).is_dir(), f"missing dir: {d}"
        # Small mode: NO 01_analysis-audit
        assert not (demo_dir / "99_audit" / "01_analysis-audit").exists()
        # Seeded files
        for f in ("00_kickoff/statement-of-work.md", "00_kickoff/project-plan.md",
                  "00_kickoff/rollback-history.md", "project-state.md",
                  "RTM.md", "escalations.md"):
            assert (demo_dir / f).is_file(), f"missing file: {f}"
        # project-state.md has scale and project name filled in
        state = (demo_dir / "project-state.md").read_text()
        assert "project: demo-small" in state
        assert "scale: small" in state
    finally:
        import shutil
        if demo_dir.exists():
            shutil.rmtree(demo_dir)


def test_bootstrap_large_mode_adds_analysis_audit():
    project_root = pathlib.Path(__file__).parent.parent
    demo_dir = project_root / "projects" / "demo-large"
    try:
        r = run("demo-large", "--scale", "large", cwd=project_root)
        assert r.returncode == 0, r.stdout + r.stderr
        assert (demo_dir / "99_audit" / "01_analysis-audit").is_dir()
        state = (demo_dir / "project-state.md").read_text()
        assert "scale: large" in state
    finally:
        import shutil
        if demo_dir.exists():
            shutil.rmtree(demo_dir)
