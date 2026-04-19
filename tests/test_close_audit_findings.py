"""Tests for scripts/close_audit_findings.py (new issue N9)."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.py"
CLOSE = ROOT / "scripts" / "close_audit_findings.py"


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


def _run(name, cycle, *args):
    return subprocess.run(
        [sys.executable, str(CLOSE), name, cycle, *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def _write_find(path: pathlib.Path, cls: str, status: str = "raised"):
    path.write_text(
        f"---\nid: FIND-01\ntype: audit-finding\ngroup: 02_design-audit\n"
        f"audit-session: 02_design-audit\naudit-round: 1\nstage: 02_design\n"
        f"status: {status}\npm-classification: {cls}\nversion: v1\n---\n# finding\n"
    )


def test_unknown_project_exits_2():
    r = _run("__close_missing__", "02_design")
    assert r.returncode == 2


def test_type_a_raised_transitions_to_resolved():
    name = "close-type-a"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        audit = demo / "99_audit" / "02_design-audit" / "audit-report"
        _write_find(audit / "FIND-01.md", cls="A", status="raised")
        r = _run(name, "02_design")
        assert r.returncode == 0, r.stdout + r.stderr
        assert "RESOLVED:" in r.stdout
        assert "status: resolved" in (audit / "FIND-01.md").read_text()
    finally:
        _cleanup(name)


def test_type_b_stays_raised():
    """Type B = ACCEPTED; status stays as-is (tracked separately in RES-SUMMARY)."""
    name = "close-type-b"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        audit = demo / "99_audit" / "02_design-audit" / "audit-report"
        _write_find(audit / "FIND-01.md", cls="B", status="raised")
        r = _run(name, "02_design")
        assert r.returncode == 0, r.stdout + r.stderr
        # Should not transition
        assert "status: raised" in (audit / "FIND-01.md").read_text()
    finally:
        _cleanup(name)


def test_check_mode_detects_raised_type_a():
    name = "close-check-a"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        audit = demo / "99_audit" / "02_design-audit" / "audit-report"
        _write_find(audit / "FIND-01.md", cls="A", status="raised")
        r = _run(name, "02_design", "--check")
        assert r.returncode == 1
        assert "STILL-RAISED:" in r.stdout
    finally:
        _cleanup(name)


def test_check_mode_clean_when_all_resolved():
    name = "close-check-clean"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        audit = demo / "99_audit" / "02_design-audit" / "audit-report"
        _write_find(audit / "FIND-01.md", cls="A", status="resolved")
        r = _run(name, "02_design", "--check")
        assert r.returncode == 0
        assert "OK:" in r.stdout
    finally:
        _cleanup(name)
