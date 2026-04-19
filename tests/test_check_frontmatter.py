"""Tests for scripts/check_frontmatter.py (Phase 7 patch #1)."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.py"
CHECKER = ROOT / "scripts" / "check_frontmatter.py"


def _bootstrap(name, scale="small"):
    r = subprocess.run(
        [sys.executable, str(BOOTSTRAP), name, "--scale", scale],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def _cleanup(name):
    d = ROOT / "projects" / name
    if d.exists():
        shutil.rmtree(d)


def _run(name):
    return subprocess.run(
        [sys.executable, str(CHECKER), name],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_unknown_project_exits_2():
    r = _run("__cf_missing__")
    assert r.returncode == 2


def test_freshly_bootstrapped_project_passes():
    name = "cf-fresh"
    try:
        _bootstrap(name)
        r = _run(name)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "OK:" in r.stdout
    finally:
        _cleanup(name)


def test_missing_owner_detected():
    name = "cf-no-owner"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        group = demo / "01_analysis" / "requirements" / "RQ-BAD"
        group.mkdir(parents=True)
        (group / "RQ-BAD-01.md").write_text(
            "---\nid: RQ-BAD-01\ntitle: t\ndepends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _run(name)
        assert r.returncode == 1
        assert "missing 'owner'" in r.stdout
    finally:
        _cleanup(name)


def test_audit_file_exempt_from_owner_requirement():
    name = "cf-audit-exempt"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        audit_dir = demo / "99_audit" / "02_design-audit" / "audit-report"
        audit_dir.mkdir(parents=True, exist_ok=True)
        # Audit file without owner — should be allowed
        (audit_dir / "FIND-01.md").write_text(
            "---\nid: FIND-01\ntitle: f\ndepends-on: []\nreferenced-by: []\n---\n# f\n"
        )
        r = _run(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


def test_missing_frontmatter_block_detected():
    name = "cf-nofm"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        group = demo / "01_analysis" / "requirements" / "RQ-NOFM"
        group.mkdir(parents=True)
        (group / "RQ-NOFM-01.md").write_text("# just a heading, no frontmatter\n")
        r = _run(name)
        assert r.returncode == 1
        assert "missing frontmatter block" in r.stdout
    finally:
        _cleanup(name)
