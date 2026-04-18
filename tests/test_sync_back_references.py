"""Unit tests for scripts/sync_back_references.py."""
import pathlib
import subprocess
import sys
import textwrap

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "sync_back_references.py"


def _make_child(path: pathlib.Path, *, cid: str, depends_on=None, referenced_by=None):
    deps = "[" + ", ".join(depends_on or []) + "]"
    refs = "[" + ", ".join(referenced_by or []) + "]"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            f"""\
            ---
            id: {cid}
            title: {cid} 제목
            stage: 01_analysis
            area: requirements
            group: test
            owner: tester
            depends-on: {deps}
            referenced-by: {refs}
            reviewed-by: []
            status: draft
            version: v1
            ---

            # {cid}

            본문.
            """
        )
    )


def _read_field(path: pathlib.Path, key: str) -> str:
    for line in path.read_text().splitlines():
        if line.startswith(f"{key}:"):
            return line[len(key) + 1 :].strip()
    raise AssertionError(f"{key} not found in {path}")


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Create a temporary projects/<name>/ tree under tmp_path/projects/."""
    proj_root = tmp_path / "projects" / "demo"
    proj_root.mkdir(parents=True)
    # Make script see tmp_path as ROOT by symlinking projects/ — easiest is to
    # invoke the script with cwd=tmp_path and patch ROOT detection: simplest
    # path is to copy the script into tmp_path with adjusted ROOT.
    # We instead invoke the function directly by importing and patching ROOT.
    sys.path.insert(0, str(ROOT / "scripts"))
    import sync_back_references as mod  # type: ignore

    monkeypatch.setattr(mod, "ROOT", tmp_path)
    yield proj_root, mod


def test_adds_missing_back_reference(project):
    proj, mod = project
    _make_child(proj / "01_analysis/requirements/auth/RQ-AUTH-01.md", cid="RQ-AUTH-01")
    _make_child(
        proj / "01_analysis/integration-test-cases/IT-01.md",
        cid="IT-01",
        depends_on=["RQ-AUTH-01"],
    )

    rc = mod.sync("demo", check_only=False)
    assert rc == 0
    assert _read_field(proj / "01_analysis/requirements/auth/RQ-AUTH-01.md", "referenced-by") == "[IT-01]"


def test_idempotent(project):
    proj, mod = project
    _make_child(
        proj / "01_analysis/requirements/auth/RQ-AUTH-01.md",
        cid="RQ-AUTH-01",
        referenced_by=["IT-01"],
    )
    _make_child(
        proj / "01_analysis/integration-test-cases/IT-01.md",
        cid="IT-01",
        depends_on=["RQ-AUTH-01"],
    )

    rc = mod.sync("demo", check_only=False)
    assert rc == 0
    # Second pass must not change anything either
    rc2 = mod.sync("demo", check_only=False)
    assert rc2 == 0


def test_check_mode_returns_1_when_updates_pending(project):
    proj, mod = project
    _make_child(proj / "01_analysis/requirements/auth/RQ-AUTH-01.md", cid="RQ-AUTH-01")
    _make_child(
        proj / "01_analysis/integration-test-cases/IT-01.md",
        cid="IT-01",
        depends_on=["RQ-AUTH-01"],
    )

    rc = mod.sync("demo", check_only=True)
    assert rc == 1
    # File must NOT have been modified in --check mode
    assert _read_field(proj / "01_analysis/requirements/auth/RQ-AUTH-01.md", "referenced-by") == "[]"


def test_merges_with_existing_back_references(project):
    proj, mod = project
    _make_child(
        proj / "01_analysis/requirements/auth/RQ-AUTH-01.md",
        cid="RQ-AUTH-01",
        referenced_by=["UAT-01"],
    )
    _make_child(
        proj / "01_analysis/integration-test-cases/IT-01.md",
        cid="IT-01",
        depends_on=["RQ-AUTH-01"],
    )
    _make_child(
        proj / "01_analysis/uat-test-cases/UAT-01.md",
        cid="UAT-01",
        depends_on=["RQ-AUTH-01"],
    )

    rc = mod.sync("demo", check_only=False)
    assert rc == 0
    refs = _read_field(proj / "01_analysis/requirements/auth/RQ-AUTH-01.md", "referenced-by")
    # Sorted union
    assert refs == "[IT-01, UAT-01]"


def test_broken_depends_on_returns_error(project):
    proj, mod = project
    _make_child(
        proj / "01_analysis/integration-test-cases/IT-01.md",
        cid="IT-01",
        depends_on=["RQ-DOES-NOT-EXIST"],
    )

    rc = mod.sync("demo", check_only=False)
    assert rc == 2  # broken-reference error


def test_unknown_project_returns_error(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    import sync_back_references as mod  # type: ignore

    monkeypatch.setattr(mod, "ROOT", tmp_path)
    rc = mod.sync("nonexistent", check_only=False)
    assert rc == 2


def test_cli_help_runs():
    """--help should exit 0 and print description."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Sync back-references" in result.stdout
