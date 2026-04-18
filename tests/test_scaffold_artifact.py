"""Tests for scripts/scaffold_artifact.py."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.py"
SCAFFOLD = ROOT / "scripts" / "scaffold_artifact.py"


def _bootstrap(name):
    r = subprocess.run([sys.executable, str(BOOTSTRAP), name, "--scale", "small"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def _cleanup(name):
    d = ROOT / "projects" / name
    if d.exists():
        shutil.rmtree(d)


def _scaffold(*args):
    return subprocess.run([sys.executable, str(SCAFFOLD), *args],
                          capture_output=True, text=True, cwd=ROOT)


def test_scaffold_area_creates_index_idempotent():
    name = "scf-area"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # Bootstrap already creates 01_analysis/requirements/index.md; calling
        # scaffold on an existing area should be a no-op (return success).
        r = _scaffold(name, "01_analysis/requirements")
        assert r.returncode == 0, r.stdout + r.stderr
        assert (demo / "01_analysis" / "requirements" / "index.md").is_file()
    finally:
        _cleanup(name)


def test_scaffold_group_directory_with_index():
    name = "scf-group"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        r = _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                      "--label", "인증 요구사항")
        assert r.returncode == 0, r.stdout + r.stderr
        group_dir = demo / "01_analysis" / "requirements" / "RQ-AUTH"
        assert group_dir.is_dir()
        assert (group_dir / "index.md").is_file()
        text = (group_dir / "index.md").read_text()
        assert "인증 요구사항" in text or "RQ-AUTH" in text
    finally:
        _cleanup(name)


def test_scaffold_child_creates_file_and_updates_index():
    name = "scf-child"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # Make the group first
        _scaffold(name, "01_analysis/requirements/RQ-AUTH", "--label", "인증")
        # Create child
        r = _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                      "--child", "RQ-AUTH-01",
                      "--title", "로그인 기능",
                      "--owner", "application-architect",
                      "--summary", "이메일·비밀번호 로그인")
        assert r.returncode == 0, r.stdout + r.stderr

        # Child file present
        group_dir = demo / "01_analysis" / "requirements" / "RQ-AUTH"
        child_files = [p for p in group_dir.iterdir()
                       if p.name.startswith("RQ-AUTH-01") and p.suffix == ".md"]
        assert len(child_files) == 1, f"expected exactly one child file, got {child_files}"

        # Index updated with a row containing the ID
        index_text = (group_dir / "index.md").read_text()
        assert "RQ-AUTH-01" in index_text
        assert "로그인 기능" in index_text
        assert "application-architect" in index_text
    finally:
        _cleanup(name)


def test_scaffold_child_requires_title_and_owner():
    name = "scf-missing"
    try:
        _bootstrap(name)
        # Missing --title
        r1 = _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                       "--child", "RQ-AUTH-01", "--owner", "application-architect")
        assert r1.returncode != 0
        # Missing --owner
        r2 = _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                       "--child", "RQ-AUTH-01", "--title", "Test")
        assert r2.returncode != 0
    finally:
        _cleanup(name)


def test_scaffold_child_duplicate_id_fails():
    name = "scf-dup"
    try:
        _bootstrap(name)
        _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                  "--child", "RQ-AUTH-01", "--title", "First",
                  "--owner", "application-architect")
        # Same ID + same title → same filename → must fail
        r = _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                      "--child", "RQ-AUTH-01", "--title", "First",
                      "--owner", "application-architect")
        assert r.returncode != 0
    finally:
        _cleanup(name)


def test_scaffold_unknown_project_fails():
    r = _scaffold("does-not-exist", "01_analysis/requirements")
    assert r.returncode != 0


def test_scaffold_child_frontmatter_filled():
    name = "scf-fm"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _scaffold(name, "01_analysis/requirements/RQ-AUTH",
                  "--child", "RQ-AUTH-02", "--title", "로그아웃",
                  "--owner", "application-architect")
        group_dir = demo / "01_analysis" / "requirements" / "RQ-AUTH"
        child = next(p for p in group_dir.iterdir() if p.name.startswith("RQ-AUTH-02"))
        text = child.read_text()
        assert "id: RQ-AUTH-02" in text
        assert "title: 로그아웃" in text
        assert "owner: application-architect" in text
        assert "stage: 01_analysis" in text
    finally:
        _cleanup(name)
