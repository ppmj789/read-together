"""Tests for scripts/validate_cr.py (new issue N2)."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.py"
VALIDATOR = ROOT / "scripts" / "validate_cr.py"


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


def _run(name):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), name],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_unknown_project_exits_2():
    r = _run("__vcr_missing__")
    assert r.returncode == 2


def test_no_cr_directory_is_ok():
    name = "vcr-empty"
    try:
        _bootstrap(name)
        r = _run(name)
        assert r.returncode == 0
        # Either "no change-requests/" or "no CR-" message
        assert "OK:" in r.stdout
    finally:
        _cleanup(name)


def _make_cr(demo: pathlib.Path, cr_id: str,
             decision: str = "approved",
             with_action: bool = True,
             with_index: bool = True):
    cr_dir = demo / "change-requests" / cr_id
    cr_dir.mkdir(parents=True, exist_ok=True)
    if with_index:
        (cr_dir / "index.md").write_text(
            f"---\ntype: change-request-index\ncr-id: {cr_id}\n"
            f"project: t\nstatus: CLOSED\nopened: 2026-04-19\n---\n"
        )
    (cr_dir / "cr-request.md").write_text(
        f"---\ntype: change-request-request\ncr-id: {cr_id}\n"
        f"project: t\nrequested-by: user\ndate: 2026-04-19\nstatus: open\n---\n"
    )
    (cr_dir / "cr-impact-analysis.md").write_text(
        f"---\ntype: change-request-impact-analysis\ncr-id: {cr_id}\n"
        f"project: t\nanalyzed-by: [application-director]\ndate: 2026-04-19\nstatus: reviewed\n---\n"
    )
    (cr_dir / "cr-decision.md").write_text(
        f"---\ntype: change-request-decision\ncr-id: {cr_id}\n"
        f"project: t\ndecided-by: user\ndate: 2026-04-19\ndecision: {decision}\n---\n"
    )
    if with_action:
        (cr_dir / "cr-action-result.md").write_text(
            f"---\ntype: change-request-action-result\ncr-id: {cr_id}\n"
            f"project: t\nowner: application-director\ndate: 2026-04-19\nstatus: completed\n---\n"
        )


def test_complete_approved_cr_passes():
    name = "vcr-complete"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _make_cr(demo, "CR-001", decision="approved", with_action=True)
        r = _run(name)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "OK:" in r.stdout
    finally:
        _cleanup(name)


def test_rejected_cr_without_action_result_passes():
    """Rejected decisions do not require cr-action-result.md."""
    name = "vcr-rejected"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _make_cr(demo, "CR-001", decision="rejected", with_action=False)
        r = _run(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


def test_approved_cr_missing_action_result_fails():
    name = "vcr-missing-action"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _make_cr(demo, "CR-001", decision="approved", with_action=False)
        r = _run(name)
        assert r.returncode == 1
        assert "missing cr-action-result.md" in r.stdout
    finally:
        _cleanup(name)


def test_missing_index_detected():
    name = "vcr-no-index"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _make_cr(demo, "CR-001", decision="approved", with_action=True, with_index=False)
        r = _run(name)
        assert r.returncode == 1
        assert "missing index.md" in r.stdout
    finally:
        _cleanup(name)


def test_duplicate_key_detected_in_cr():
    name = "vcr-dup"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        _make_cr(demo, "CR-001", decision="approved")
        # Inject duplicate key into cr-request.md
        req = demo / "change-requests" / "CR-001" / "cr-request.md"
        text = req.read_text()
        text = text.replace(
            "status: open",
            "status: open\nstatus: draft",
        )
        req.write_text(text)
        r = _run(name)
        assert r.returncode == 1
        assert "duplicate frontmatter key" in r.stdout
    finally:
        _cleanup(name)
