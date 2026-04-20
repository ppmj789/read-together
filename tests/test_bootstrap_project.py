"""Tests for scripts/bootstrap_project.py (v2 hierarchical bootstrap)."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "bootstrap_project.py"


def run(*args, **kwargs):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=ROOT, **kwargs)


def _cleanup(name):
    d = ROOT / "projects" / name
    if d.exists():
        shutil.rmtree(d)


# ---------- Validation ----------------------------------------------------

def test_bootstrap_rejects_empty_name():
    r = run("", "--scale", "small")
    assert r.returncode != 0


def test_bootstrap_rejects_unsafe_name():
    r = run("../evil", "--scale", "small")
    assert r.returncode != 0


def test_bootstrap_rejects_bad_scale():
    r = run("demo-x", "--scale", "huge")
    assert r.returncode != 0


def test_bootstrap_refuses_existing_project():
    name = "demo-exist-guard"
    try:
        r1 = run(name, "--scale", "small")
        assert r1.returncode == 0, r1.stdout + r1.stderr
        r2 = run(name, "--scale", "small")
        assert r2.returncode != 0
        assert "already exists" in r2.stderr or "already exists" in r2.stdout
    finally:
        _cleanup(name)


# ---------- Small-mode structure -----------------------------------------

def test_bootstrap_small_creates_expected_stage_dirs():
    name = "demo-small"
    demo = ROOT / "projects" / name
    try:
        r = run(name, "--scale", "small")
        assert r.returncode == 0, r.stdout + r.stderr

        # Stage root directories
        for d in ("00_kickoff", "01_analysis", "02_design",
                  "03_implementation", "04_test", "05_deployment",
                  "99_audit", "change-requests", "RTM"):
            assert (demo / d).is_dir(), f"missing dir: {d}"

        # Representative area sub-directories
        for d in ("00_kickoff/project-plan",
                  "01_analysis/requirements",
                  "02_design/architecture",
                  "02_design/db/logical",
                  "02_design/db/physical",
                  "02_design/screens",
                  "02_design/batch-jobs",
                  "02_design/programs",
                  "03_implementation/unit-test-results",
                  "04_test/qa-report",
                  "05_deployment/deployment-plan",
                  "99_audit/02_design-audit",
                  "99_audit/03_closing-audit",
                  "RTM/by-stage"):
            assert (demo / d).is_dir(), f"missing area dir: {d}"

        # Small mode: NO analysis audit
        assert not (demo / "99_audit" / "01_analysis-audit").exists()
    finally:
        _cleanup(name)


def test_bootstrap_areas_have_index_md():
    name = "demo-idx"
    demo = ROOT / "projects" / name
    try:
        run(name, "--scale", "small")
        # Every area root must have index.md
        for d in ("00_kickoff/project-plan",
                  "01_analysis/requirements",
                  "02_design/architecture",
                  "02_design/db/physical",
                  "02_design/screens",
                  "02_design/batch-jobs",
                  "02_design/programs",
                  "04_test/qa-report",
                  "99_audit/02_design-audit"):
            assert (demo / d / "index.md").is_file(), f"missing index: {d}/index.md"
    finally:
        _cleanup(name)


def test_bootstrap_top_level_files_seeded():
    name = "demo-seed"
    demo = ROOT / "projects" / name
    try:
        run(name, "--scale", "small")
        for f in ("00_kickoff/statement-of-work.md",
                  "00_kickoff/rollback-history.md",
                  "escalations.md",
                  "project-state.md",
                  "agent-call-log.md",
                  "RTM/index.md",
                  "RTM/by-stage/analysis.md",
                  "RTM/by-stage/design.md",
                  "RTM/by-stage/implementation.md",
                  "RTM/by-stage/test.md",
                  "RTM/by-stage/deployment.md"):
            assert (demo / f).is_file(), f"missing seed file: {f}"
    finally:
        _cleanup(name)


def test_bootstrap_project_state_filled_in():
    name = "demo-state"
    demo = ROOT / "projects" / name
    try:
        run(name, "--scale", "small")
        text = (demo / "project-state.md").read_text()
        assert f"project: {name}" in text
        assert "scale: small" in text
    finally:
        _cleanup(name)


def test_bootstrap_agent_call_log_filled_in():
    name = "demo-log"
    demo = ROOT / "projects" / name
    try:
        run(name, "--scale", "small")
        text = (demo / "agent-call-log.md").read_text()
        assert f"project: {name}" in text
    finally:
        _cleanup(name)


def test_bootstrap_archived_dir_has_gitkeep():
    name = "demo-archive"
    demo = ROOT / "projects" / name
    try:
        run(name, "--scale", "small")
        assert (demo / "RTM" / "_archived" / ".gitkeep").is_file()
    finally:
        _cleanup(name)


# ---------- Large-mode structure -----------------------------------------

def test_bootstrap_large_adds_analysis_audit_and_by_part():
    name = "demo-large"
    demo = ROOT / "projects" / name
    try:
        r = run(name, "--scale", "large")
        assert r.returncode == 0, r.stdout + r.stderr
        # Analysis audit tree
        for d in ("99_audit/01_analysis-audit",
                  "99_audit/01_analysis-audit/audit-report",
                  "99_audit/01_analysis-audit/corrective-action-plan",
                  "99_audit/01_analysis-audit/corrective-action-result"):
            assert (demo / d).is_dir(), f"missing large-only dir: {d}"
            assert (demo / d / "index.md").is_file(), f"missing index: {d}/index.md"
        # by-part RTM slot
        assert (demo / "RTM" / "by-part").is_dir()
        assert (demo / "RTM" / "by-part" / "index.md").is_file()

        state = (demo / "project-state.md").read_text()
        assert "scale: large" in state
    finally:
        _cleanup(name)


def test_bootstrap_hierarchy_passes_validate_hierarchy():
    name = "demo-hier"
    try:
        run(name, "--scale", "small")
        validator = ROOT / "scripts" / "validate_artifact_hierarchy.py"
        r = subprocess.run([sys.executable, str(validator), name],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "OK:" in r.stdout
    finally:
        _cleanup(name)
