"""Tests for scripts/derive_dynamic_agents.py (v2 shell generator)."""
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "derive_dynamic_agents.py"
ROLES_DIR = ROOT / ".claude" / "roles"
AGENTS_DIR = ROOT / ".claude" / "agents"

DYNAMIC_ROLES = [
    "application-architect", "software-architect", "data-modeler", "part-leader",
    "backend-developer", "batch-developer", "web-developer", "web-publisher", "designer",
    "technical-architect", "database-administrator", "security-specialist",
    "infrastructure-engineer",
]
FIXED_ROLES = [
    "application-director", "infrastructure-director",
    "business-manager", "quality-assurance", "tester", "audit-team",
]
SKILL_ONLY = {"project-manager"}
MODELS = ("opus", "sonnet", "haiku")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=ROOT)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_succeeds():
    r = run("--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "generated 45 of 45 expected shell(s)" in r.stdout


def test_dry_run_skips_pm():
    r = run("--dry-run")
    assert "skip (Skill-only): project-manager" in r.stdout


def test_dry_run_lists_all_45_shells():
    r = run("--dry-run")
    count = sum(1 for line in r.stdout.splitlines() if line.startswith("would write:"))
    assert count == 45, f"expected 45 would-write lines, got {count}"


def test_generated_files_exist_on_disk():
    """Already-committed agents/ should exist after previous `--clean` run."""
    for role in FIXED_ROLES:
        assert (AGENTS_DIR / f"{role}.md").exists(), f"missing: {role}.md"
    for role in DYNAMIC_ROLES:
        for m in MODELS:
            assert (AGENTS_DIR / f"{role}-{m}.md").exists(), f"missing: {role}-{m}.md"


def test_no_pm_agent_shell():
    for role in SKILL_ONLY:
        for m in MODELS:
            assert not (AGENTS_DIR / f"{role}-{m}.md").exists(), \
                f"{role}-{m}.md exists (should be Skill-only)"
        assert not (AGENTS_DIR / f"{role}.md").exists(), \
            f"{role}.md exists (should be Skill-only)"


def test_derived_files_reference_roles_path():
    """Each shell body must reference .claude/roles/<role>.md."""
    for role in FIXED_ROLES:
        text = (AGENTS_DIR / f"{role}.md").read_text()
        assert f".claude/roles/{role}.md" in text, f"{role}.md missing roles ref"
    for role in DYNAMIC_ROLES:
        for m in MODELS:
            text = (AGENTS_DIR / f"{role}-{m}.md").read_text()
            assert f".claude/roles/{role}.md" in text, f"{role}-{m}.md missing roles ref"


def test_fixed_role_model_and_effort():
    """Fixed roles are generated with the specified model/effort."""
    expected = {
        "application-director":    ("opus",   "xhigh"),
        "infrastructure-director": ("opus",   "xhigh"),
        "business-manager":        ("sonnet", "xhigh"),
        "quality-assurance":       ("sonnet", "xhigh"),
        "tester":                  ("sonnet", "xhigh"),
        "audit-team":              ("sonnet", "xhigh"),
    }
    for role, (model, effort) in expected.items():
        text = (AGENTS_DIR / f"{role}.md").read_text()
        assert f"model: {model}" in text, f"{role}: expected model {model}"
        assert f"effort: {effort}" in text, f"{role}: expected effort {effort}"


def test_dynamic_role_has_three_variants():
    """Every dynamic role produces opus/sonnet/haiku."""
    for role in DYNAMIC_ROLES:
        models_seen = set()
        for m in MODELS:
            text = (AGENTS_DIR / f"{role}-{m}.md").read_text()
            assert f"model: {m}" in text
            models_seen.add(m)
        assert models_seen == set(MODELS)


def test_all_shells_have_readonly_tools():
    """Every agent shell must declare tools: [Read, Glob, Grep]."""
    for p in AGENTS_DIR.glob("*.md"):
        text = p.read_text()
        assert "tools: [Read, Glob, Grep]" in text, f"{p.name}: wrong tools"


def test_all_shells_pass_validation():
    """Every generated shell passes validate_agent.py."""
    validator = ROOT / "scripts" / "validate_agent.py"
    paths = [str(p) for p in sorted(AGENTS_DIR.glob("*.md"))]
    assert len(paths) == 45
    r = subprocess.run([sys.executable, str(validator), *paths],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_regeneration_is_idempotent():
    """Running derive twice produces identical outputs (pure function of roles/)."""
    # Snapshot current agents/
    before = {p.name: p.read_text() for p in AGENTS_DIR.glob("*.md")}
    # Re-run with --clean
    r = run("--clean")
    assert r.returncode == 0, r.stdout + r.stderr
    after = {p.name: p.read_text() for p in AGENTS_DIR.glob("*.md")}
    assert before == after, "regeneration produced different output"
