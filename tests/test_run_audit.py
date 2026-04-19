"""Tests for scripts/run_audit.sh (arg validation only — real audit run is E2E)."""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_audit.sh"


def _run(*args, timeout: int = 15):
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def test_script_exists_and_executable():
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111, f"{SCRIPT} must be executable"


def test_help_prints_usage_and_exits_zero():
    r = _run("--help")
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "<cycle-id>" in r.stdout
    assert "before --append-system-prompt" in r.stdout  # the CRITICAL arg-order note


def test_no_args_exits_2():
    r = _run()
    assert r.returncode == 2


def test_missing_project_exits_2(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("probe")
    r = _run("nonexistent-project", "02_design", str(prompt))
    assert r.returncode == 2
    assert "project not found" in r.stderr


def test_missing_prompt_file_exits_2(tmp_path):
    r = _run("book-mgmt-api", "02_design", str(tmp_path / "does-not-exist.txt"))
    # Either "project not found" if book-mgmt-api is absent on master, OR
    # "prompt file not found" if it exists. Either way exit 2.
    assert r.returncode == 2


def test_invalid_flag_exits_2():
    """Any unknown invocation pattern without 3 positional args must fail fast."""
    r = _run("--notafag")
    assert r.returncode == 2


# --- Phase 7 Task 10 finding #18 regression guards ---------------------------
# These tests check that the script still has the 3-layer defense against
# audit-team writing to the wrong path (worktree root instead of the project
# copy). They are static checks on the script source — they do not execute
# `claude -p`.

_SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")


def test_prompt_header_prepends_absolute_output_paths():
    """run_audit.sh must prepend an [AUDIT OUTPUT PATH] header that tells the
    audit-team to write under $WT_PATH/projects/$PROJECT/99_audit/."""
    assert "[AUDIT OUTPUT PATH" in _SCRIPT_SRC, (
        "prompt header missing — audit-team will write to worktree root "
        "(Phase 7 Task 10 finding #18 regression)"
    )
    assert "$WT_PATH/projects/$PROJECT/99_audit/${CYCLE}-audit/" in _SCRIPT_SRC, (
        "absolute output path template missing from prompt header"
    )
    # The header must be prepended to the user-supplied prompt, not replace it.
    assert 'PROMPT="${PATH_HEADER}${USER_PROMPT}"' in _SCRIPT_SRC, (
        "prompt must concatenate PATH_HEADER and USER_PROMPT"
    )


def test_fallback_copy_logic_present():
    """run_audit.sh must copy from the worktree-root fallback path if the
    expected projects/<project>/ path is empty (Phase 7 Task 10 finding #18)."""
    assert 'SRC_FALLBACK="$WT_PATH/99_audit/${CYCLE}-audit"' in _SCRIPT_SRC, (
        "SRC_FALLBACK path missing — fallback copy logic will not trigger"
    )
    # Fallback branch must warn the PM so they know the audit wrote to the
    # wrong location and can file a spec/role fix.
    assert "audit output found at fallback path" in _SCRIPT_SRC, (
        "fallback warning message missing"
    )


def test_fallback_copy_roundtrip(tmp_path):
    """Simulate the copy step: when SRC_FALLBACK has content and SRC has only
    seed index.md, run_audit.sh must copy from SRC_FALLBACK. We invoke the
    same bash logic in a standalone wrapper to exercise the branch."""
    import shutil
    wt = tmp_path / "wt"
    main = tmp_path / "main"
    project = "fake-proj"
    cycle = "03_closing"
    src = wt / "projects" / project / "99_audit" / f"{cycle}-audit"
    src_fallback = wt / "99_audit" / f"{cycle}-audit"
    dst = main / "projects" / project / "99_audit" / f"{cycle}-audit"
    src.mkdir(parents=True)
    (src / "index.md").write_text("seed\n")  # seed-only at expected path
    src_fallback.mkdir(parents=True)
    (src_fallback / "audit-plan.md").write_text("real audit output\n")
    (src_fallback / "audit-report").mkdir()
    (src_fallback / "audit-report" / "FIND-C-01.md").write_text("fact\n")

    # Mirror the critical copy branch from run_audit.sh verbatim.
    wrapper = tmp_path / "copy_only.sh"
    wrapper.write_text(f"""#!/bin/bash
set -euo pipefail
SRC="{src}"
SRC_FALLBACK="{src_fallback}"
DST="{dst}"
copied_from=""
if [ -d "$SRC" ] && [ -n "$(ls -A "$SRC" 2>/dev/null | grep -v '^index.md$' || true)" ]; then
  mkdir -p "$DST"; cp -r "$SRC"/. "$DST"/; copied_from="$SRC"
elif [ -d "$SRC_FALLBACK" ]; then
  mkdir -p "$DST"; cp -r "$SRC_FALLBACK"/. "$DST"/
  if [ -d "$SRC" ]; then cp -rn "$SRC"/. "$DST"/ 2>/dev/null || true; fi
  copied_from="$SRC_FALLBACK"
fi
echo "from=$copied_from"
""")
    wrapper.chmod(0o755)
    r = subprocess.run(["bash", str(wrapper)], capture_output=True, text=True, check=True, timeout=10)
    assert f"from={src_fallback}" in r.stdout, r.stdout
    assert (dst / "audit-plan.md").read_text() == "real audit output\n"
    assert (dst / "audit-report" / "FIND-C-01.md").read_text() == "fact\n"
    # Seed index.md merged from SRC via `cp -rn`.
    assert (dst / "index.md").read_text() == "seed\n"
    shutil.rmtree(tmp_path, ignore_errors=True)
