"""System-level drift-guard: all roles/agents/skills/templates/docs are present
and consistent with the v2 design (spec §1-1, §2-1, §3-1 and call-playbook).

This test covers what previously lived in v1's test_all_agents_valid.py but
now targets the v2 three-tier structure (roles/ · agents/ · skills/) and the
hierarchical templates/ layout.
"""
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
VALIDATOR = ROOT / "scripts" / "validate_agent.py"
ROLES_DIR = ROOT / ".claude" / "roles"
AGENTS_DIR = ROOT / ".claude" / "agents"
SKILLS_DIR = ROOT / ".claude" / "skills"
TEMPLATES_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "docs"

FIXED_ROLES_WITH_SHELL = [
    "application-director", "infrastructure-director",
    "business-manager", "quality-assurance", "tester", "audit-team",
]
DYNAMIC_ROLES = [
    "application-architect", "software-architect", "data-modeler", "part-leader",
    "backend-developer", "batch-developer", "web-developer", "web-publisher", "designer",
    "technical-architect", "database-administrator", "security-specialist",
    "infrastructure-engineer",
]
ALL_ROLE_NAMES = ["project-manager"] + FIXED_ROLES_WITH_SHELL + DYNAMIC_ROLES   # 20
MODELS = ("opus", "sonnet", "haiku")


# ---------- roles/ --------------------------------------------------------

def test_all_20_role_files_exist():
    for role in ALL_ROLE_NAMES:
        p = ROLES_DIR / f"{role}.md"
        assert p.exists(), f"missing role file: {p}"


def test_no_stray_files_in_roles_dir():
    for p in ROLES_DIR.iterdir():
        assert p.is_file() and p.suffix == ".md", f"unexpected entry in roles/: {p}"
    md_files = list(ROLES_DIR.glob("*.md"))
    assert len(md_files) == 20, f"expected exactly 20 role files, got {len(md_files)}"


# ---------- agents/ -------------------------------------------------------

def test_fixed_agent_shells_exist():
    """Fixed roles (except PM) have exactly one shell."""
    for role in FIXED_ROLES_WITH_SHELL:
        p = AGENTS_DIR / f"{role}.md"
        assert p.exists(), f"missing fixed agent shell: {p}"


def test_no_pm_agent_shell():
    assert not (AGENTS_DIR / "project-manager.md").exists()
    for m in MODELS:
        assert not (AGENTS_DIR / f"project-manager-{m}.md").exists()


def test_dynamic_agent_shells_all_three_variants():
    for role in DYNAMIC_ROLES:
        for m in MODELS:
            p = AGENTS_DIR / f"{role}-{m}.md"
            assert p.exists(), f"missing dynamic agent shell: {p}"


def test_total_agents_count_is_45():
    md_files = list(AGENTS_DIR.glob("*.md"))
    assert len(md_files) == 45, f"expected 45 agent shells, got {len(md_files)}"


def test_no_nested_dirs_in_agents():
    # v2 eliminates agents/audit/ and agents/templates/
    for p in AGENTS_DIR.iterdir():
        assert p.is_file(), f"unexpected subdirectory in agents/: {p}"


# ---------- skills/ ------------------------------------------------------

def test_pm_skill_exists():
    p = SKILLS_DIR / "project-manager" / "SKILL.md"
    assert p.exists(), f"missing PM skill: {p}"


# ---------- Validation ---------------------------------------------------

def test_validate_all_passes():
    """Every role/agent/skill file must validate under v2 rules."""
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), "--all"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK:" in r.stdout


# ---------- templates/ ---------------------------------------------------

def test_stage_gates_present():
    assert (TEMPLATES_DIR / "stage-gates.md").exists()


def test_required_artifact_templates_present():
    required = [
        # Common
        "_common/index.md.tmpl",
        "_common/child.md.tmpl",
        # Top-level single files
        "project-state.md.tmpl",
        "agent-call-log.md.tmpl",
        "escalations.md.tmpl",
        "rollback-history.md.tmpl",
        "statement-of-work.md.tmpl",
        "review-meeting.md.tmpl",
        # RTM
        "rtm/index.md.tmpl",
        "rtm/by-stage.md.tmpl",
        # Change requests
        "change-requests/cr-request.md.tmpl",
        "change-requests/cr-impact-analysis.md.tmpl",
        "change-requests/cr-decision.md.tmpl",
        # Audit
        "audit/audit-plan.md.tmpl",
        "audit/finding.md.tmpl",
    ]
    artifacts = TEMPLATES_DIR / "artifacts"
    for rel in required:
        p = artifacts / rel
        assert p.exists(), f"missing template: {p}"


# ---------- docs/ --------------------------------------------------------

def test_design_spec_present():
    assert (DOCS_DIR / "superpowers" / "specs" /
            "2026-04-17-ai-si-team-design.md").exists()


def test_call_playbook_present():
    assert (DOCS_DIR / "call-playbook.md").exists()


# ---------- Settings ------------------------------------------------------

def test_session_start_hook_configured():
    settings = ROOT / ".claude" / "settings.json"
    assert settings.exists(), "missing .claude/settings.json"
    text = settings.read_text()
    assert "SessionStart" in text
    assert ".claude/roles/project-manager.md" in text
