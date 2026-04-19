"""Tests for scripts/sync_child_count.py (new issue N12)."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.py"
SYNC = ROOT / "scripts" / "sync_child_count.py"


def _bootstrap(name):
    r = subprocess.run(
        [sys.executable, str(BOOTSTRAP), name, "--scale", "small"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def _cleanup(name):
    d = ROOT / "projects" / name
    if d.exists():
        shutil.rmtree(d)


def _run(name, *args):
    return subprocess.run(
        [sys.executable, str(SYNC), name, *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_unknown_project_exits_2():
    r = _run("__scc_missing__")
    assert r.returncode == 2


def test_freshly_bootstrapped_is_clean():
    name = "scc-fresh"
    try:
        _bootstrap(name)
        r = _run(name)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "clean" in r.stdout
    finally:
        _cleanup(name)


def _prepare_drift(demo: pathlib.Path):
    """Add 3 children but leave child-count: 0 in index."""
    area = demo / "02_design" / "programs" / "PRG-DRIFT"
    area.mkdir(parents=True)
    (area / "index.md").write_text(
        "---\nid: PRG-DRIFT\ntitle: drift\nchild-count: 0\n---\n# drift\n"
    )
    for i in range(1, 4):
        (area / f"PRG-DRIFT-0{i}.md").write_text(
            f"---\nid: PRG-DRIFT-0{i}\ntitle: t\ndepends-on: []\nreferenced-by: []\nowner: software-architect\n---\n# t\n"
        )


def test_check_mode_reports_drift():
    name = "scc-check"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _prepare_drift(demo)
        r = _run(name, "--check")
        assert r.returncode == 1
        assert "DRIFT:" in r.stdout
        assert "child-count=0" in r.stdout and "actual=3" in r.stdout
    finally:
        _cleanup(name)


def test_write_mode_syncs_child_count():
    name = "scc-write"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _prepare_drift(demo)
        r = _run(name)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "SYNC:" in r.stdout or "synced" in r.stdout
        # Re-check; should now be clean
        r2 = _run(name, "--check")
        assert r2.returncode == 0
        # The index content should now say child-count: 3
        idx = (demo / "02_design" / "programs" / "PRG-DRIFT" / "index.md").read_text()
        assert "child-count: 3" in idx
    finally:
        _cleanup(name)
