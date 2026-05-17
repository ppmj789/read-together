import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "validate_ledger.py"


def _run(project_dir):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(project_dir)],
        capture_output=True, text=True,
    )


def _node(ledger_dir, node_id, parent, status="closed",
          request="r", response="x", children_rows="", next_block="CLOSE",
          artifacts="[]", rtm="[]"):
    ledger_dir.mkdir(parents=True, exist_ok=True)
    p = ledger_dir / f"{node_id}.md"
    p.write_text(
        f"---\nid: {node_id}\nparent: {parent}\nrole: backend-developer\n"
        f"dispatched-by: PM\nmodel: sonnet\nstage: 02_design\n"
        f"status: {status}\nartifacts: {artifacts}\nrtm: {rtm}\n"
        f"created: 2026-05-16T00:00:00Z\nresponded: 2026-05-16T01:00:00Z\n---\n\n"
        f"## REQUEST\n{request}\n\n## RESPONSE\n{response}\n\n"
        f"## CHILD INDEX\n| child id | path | role | one-line purpose | status |\n"
        f"|----------|------|------|------------------|--------|\n{children_rows}\n\n"
        f"## NEXT\n{next_block}\n",
        encoding="utf-8",
    )
    return p


def test_clean_single_node_passes(tmp_path):
    ledger = tmp_path / "ledger"
    _node(ledger, "A", parent="")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_missing_parent_file_fails(tmp_path):
    ledger = tmp_path / "ledger"
    _node(ledger, "A-1", parent="A")  # parent A 파일 없음
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "parent" in (r.stdout + r.stderr).lower()


def test_id_filename_mismatch_fails(tmp_path):
    ledger = tmp_path / "ledger"
    ledger.mkdir(parents=True)
    (ledger / "A.md").write_text(
        "---\nid: WRONG\nparent: \nrole: x\ndispatched-by: PM\nmodel: sonnet\n"
        "stage: s\nstatus: closed\nartifacts: []\nrtm: []\n"
        "created: 2026-05-16T00:00:00Z\nresponded: 2026-05-16T01:00:00Z\n---\n\n"
        "## REQUEST\nr\n\n## RESPONSE\nx\n\n## CHILD INDEX\n\n## NEXT\nCLOSE\n",
        encoding="utf-8",
    )
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "id" in (r.stdout + r.stderr).lower()


def test_no_ledger_dir_passes(tmp_path):
    # ledger 디렉토리 미존재 = 검증할 것 없음 = clean
    r = _run(tmp_path)
    assert r.returncode == 0
