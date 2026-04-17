import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
VALIDATOR = ROOT / "scripts" / "validate_agent.py"

EXPECTED_FIXED = [
    "project-manager.md",
    "application-director.md",
    "infrastructure-director.md",
    "business-manager.md",
    "quality-assurance.md",
    "tester.md",
    "audit/audit-team.md",
]

DYNAMIC_ROLES = [
    "application-architect", "software-architect", "technical-architect",
    "data-modeler", "part-leader",
    "backend-developer", "batch-developer", "web-developer",
    "web-publisher", "designer",
    "database-administrator", "security-specialist", "infrastructure-engineer",
]
DYNAMIC_EXPECTED = [
    f"{role}-{m}.md" for role in DYNAMIC_ROLES for m in ("opus", "sonnet", "haiku")
]

def test_fixed_agents_exist_and_validate():
    paths = [ROOT / ".claude" / "agents" / p for p in EXPECTED_FIXED]
    for p in paths:
        assert p.exists(), f"missing fixed agent: {p}"
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), *map(str, paths)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr

def test_dynamic_agents_exist_and_validate():
    paths = [ROOT / ".claude" / "agents" / p for p in DYNAMIC_EXPECTED]
    for p in paths:
        assert p.exists(), f"missing dynamic agent: {p}"
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), *map(str, paths)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr

def test_stage_gates_present():
    assert (ROOT / ".claude" / "agents" / "templates" / "stage-gates.md").exists()

def test_all_required_artifact_templates_present():
    required = [
        "requirements.md.tmpl", "as-is-analysis.md.tmpl",
        "to-be-workflow.md.tmpl", "uat-test-cases.md.tmpl",
        "integration-test-cases.md.tmpl",
        "architecture.md.tmpl", "db-logical.md.tmpl", "db-physical.md.tmpl",
        "screen-spec.md.tmpl", "interface-spec.md.tmpl",
        "program-list.md.tmpl", "unit-test-cases.md.tmpl",
        "security-review.md.tmpl",
        "unit-test-results.md.tmpl", "integration-test-results.md.tmpl",
        "system-test-results.md.tmpl", "uat-results.md.tmpl",
        "qa-report.md.tmpl",
        "deployment-plan.md.tmpl", "operation-manual.md.tmpl",
        "training-material.md.tmpl",
        "review-meeting.md.tmpl",
        "audit-plan.md.tmpl", "audit-report.md.tmpl",
        "corrective-action-plan.md.tmpl",
        "corrective-action-result.md.tmpl",
        "re-audit-report.md.tmpl",
        "project-plan.md.tmpl", "project-state.md.tmpl",
        "rtm.md.tmpl",
        "cr.md.tmpl", "escalations.md.tmpl", "rollback-history.md.tmpl",
    ]
    for t in required:
        p = ROOT / ".claude" / "agents" / "templates" / "artifacts" / t
        assert p.exists(), f"missing template: {p}"
