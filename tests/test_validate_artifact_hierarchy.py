"""Tests for scripts/validate_artifact_hierarchy.py."""
import shutil
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.py"
VALIDATOR = ROOT / "scripts" / "validate_artifact_hierarchy.py"


def _bootstrap(name, scale="small"):
    r = subprocess.run([sys.executable, str(BOOTSTRAP), name, "--scale", scale],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def _cleanup(name):
    d = ROOT / "projects" / name
    if d.exists():
        shutil.rmtree(d)


def _validate(name):
    return subprocess.run([sys.executable, str(VALIDATOR), name],
                          capture_output=True, text=True, cwd=ROOT)


# ---------- Basic ----------------------------------------------------------

def test_freshly_bootstrapped_project_passes():
    name = "hv-fresh"
    try:
        _bootstrap(name)
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "OK:" in r.stdout
    finally:
        _cleanup(name)


def test_unknown_project_fails():
    r = _validate("does-not-exist")
    assert r.returncode != 0


# ---------- Missing index.md ---------------------------------------------

def test_missing_index_when_three_plus_children_fails():
    name = "hv-missing-idx"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # Create a bare directory with 3 non-indexed children (no index.md)
        bad = demo / "02_design" / "programs" / "PRG-XYZ"
        bad.mkdir(parents=True)
        for i in range(3):
            f = bad / f"PRG-XYZ-0{i+1}.md"
            f.write_text(f"---\nid: PRG-XYZ-0{i+1}\ntitle: t\n---\n# t\n")
        r = _validate(name)
        assert r.returncode != 0
        assert "missing index.md" in r.stdout
    finally:
        _cleanup(name)


def test_missing_index_with_one_child_allowed():
    # Per §2-13-7: directories with 1–2 children may omit index.md.
    name = "hv-one-child"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        small_group = demo / "02_design" / "programs" / "PRG-TINY"
        small_group.mkdir(parents=True)
        (small_group / "PRG-TINY-01.md").write_text(
            "---\nid: PRG-TINY-01\ntitle: t\n---\n# t\n")
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


# ---------- Bidirectional dependency checks -------------------------------

def test_depends_on_nonexistent_id_fails():
    name = "hv-bad-dep"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        group = demo / "01_analysis" / "requirements" / "RQ-A"
        group.mkdir(parents=True)
        (group / "RQ-A-01.md").write_text(
            "---\nid: RQ-A-01\ntitle: t\ndepends-on: [RQ-GHOST-99]\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "does not exist" in r.stdout
    finally:
        _cleanup(name)


def test_one_way_reference_fails():
    name = "hv-oneway"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        group = demo / "01_analysis" / "requirements" / "RQ-PAIR"
        group.mkdir(parents=True)
        # A depends on B, but B does not list A in referenced-by
        (group / "RQ-PAIR-A.md").write_text(
            "---\nid: RQ-PAIR-A\ntitle: a\ndepends-on: [RQ-PAIR-B]\nreferenced-by: []\n---\n# a\n"
        )
        (group / "RQ-PAIR-B.md").write_text(
            "---\nid: RQ-PAIR-B\ntitle: b\ndepends-on: []\nreferenced-by: []\n---\n# b\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "bidirectional drift" in r.stdout
    finally:
        _cleanup(name)


def test_bidirectional_consistent_passes():
    name = "hv-bothways"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        group = demo / "01_analysis" / "requirements" / "RQ-PAIR"
        group.mkdir(parents=True)
        (group / "RQ-PAIR-A.md").write_text(
            "---\nid: RQ-PAIR-A\ntitle: a\ndepends-on: [RQ-PAIR-B]\nreferenced-by: []\n---\n# a\n"
        )
        (group / "RQ-PAIR-B.md").write_text(
            "---\nid: RQ-PAIR-B\ntitle: b\ndepends-on: []\nreferenced-by: [RQ-PAIR-A]\n---\n# b\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


# ---------- 3-hop depth limit --------------------------------------------

def test_depth_limit_exceeded_fails():
    name = "hv-depth"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # Build a too-deep path: 02_design/programs/GROUP/SUB/EXTRA/leaf.md (6 segments)
        too_deep = demo / "02_design" / "programs" / "GROUP" / "SUB" / "EXTRA"
        too_deep.mkdir(parents=True)
        (too_deep / "leaf.md").write_text("---\nid: LEAF\ntitle: t\n---\n# t\n")
        r = _validate(name)
        assert r.returncode != 0
        assert "3-hop limit exceeded" in r.stdout
    finally:
        _cleanup(name)


def test_audit_allows_one_extra_level():
    # 99_audit tree permits one extra level (5 segments).
    name = "hv-audit"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # 99_audit/02_design-audit/audit-report/FIND-01.md is 4 segments — fine
        # Add 5-segment path: 99_audit/02_design-audit/audit-report/v1/FIND-02.md
        five = demo / "99_audit" / "02_design-audit" / "audit-report" / "v1"
        five.mkdir(parents=True)
        (five / "FIND-02.md").write_text("---\nid: FIND-02\n---\n# f\n")
        r = _validate(name)
        # Should still pass (audit exception)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


# ---------- Group / index ID references (Phase 7 patches #2, #17) ---------

def test_child_can_reference_index_group_id():
    """A child's depends-on may point to an index.md group ID; no back-ref required."""
    name = "hv-group-ref"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        group = demo / "01_analysis" / "requirements" / "RQ-GRP"
        group.mkdir(parents=True)
        # Index declares group-level id
        (group / "index.md").write_text(
            "---\nid: RQ-GRP\ntitle: group\n---\n# grp\n"
        )
        # Three children so the directory qualifies as ≥3
        for i in range(1, 4):
            (group / f"RQ-GRP-0{i}.md").write_text(
                f"---\nid: RQ-GRP-0{i}\ntitle: t{i}\ndepends-on: []\nreferenced-by: []\n---\n# t\n"
            )
        # External review file references the GROUP id, not each child
        reviews = demo / "01_analysis" / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        (reviews / "rq-grp-review-v1.md").write_text(
            "---\nid: REV-RQ-GRP-V1\ntitle: review\ndepends-on: [RQ-GRP]\nreferenced-by: []\n---\n# review\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "group(s)" in r.stdout
    finally:
        _cleanup(name)


def test_unknown_group_id_reference_fails():
    """A child referencing a nonexistent group ID still fails."""
    name = "hv-group-bad"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        reviews = demo / "01_analysis" / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        (reviews / "ghost-review.md").write_text(
            "---\nid: REV-GHOST\ntitle: r\ndepends-on: [NON-EXISTENT-GRP]\nreferenced-by: []\n---\n# r\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "does not exist" in r.stdout
    finally:
        _cleanup(name)


# ---------- Audit-authored advisory (Phase 7 patch #19) -------------------

def test_audit_finding_drift_is_advisory_only():
    """Bidirectional drift inside 99_audit/<cycle>-audit/audit-report/ is advisory."""
    name = "hv-audit-advisory"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # audit-team-authored finding references a real RQ id but the RQ does
        # not back-reference the finding (audit-team can't edit outside
        # 99_audit/, so drift is unavoidable).
        req_group = demo / "01_analysis" / "requirements" / "RQ-AD"
        req_group.mkdir(parents=True)
        (req_group / "RQ-AD-01.md").write_text(
            "---\nid: RQ-AD-01\ntitle: r\ndepends-on: []\nreferenced-by: []\n---\n# r\n"
        )
        audit_dir = demo / "99_audit" / "02_design-audit" / "audit-report"
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / "FIND-ADV-01.md").write_text(
            "---\nid: FIND-ADV-01\ntitle: f\ndepends-on: [RQ-AD-01]\nreferenced-by: []\n---\n# f\n"
        )
        r = _validate(name)
        # Should PASS — the drift is advisory, printed to stderr as WARN
        assert r.returncode == 0, r.stdout + r.stderr
        assert "WARN (audit-authored" in r.stderr
    finally:
        _cleanup(name)


# ---------- Architecture owner check --------------------------------------

def test_architecture_owner_correct_passes():
    name = "hv-arch-ok"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        app = demo / "02_design" / "architecture" / "application"
        (app / "overview.md").write_text(
            "---\nid: ARCH-APP-OVR\ntitle: t\nowner: application-architect\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        (app / "code-architecture.md").write_text(
            "---\nid: ARCH-APP-CODE\ntitle: t\nauthor: software-architect-sonnet\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        tech = demo / "02_design" / "architecture" / "technology"
        (tech / "overview.md").write_text(
            "---\nid: ARCH-TECH-OVR\ntitle: t\nowner: technical-architect\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


def test_architecture_owner_wrong_fails():
    name = "hv-arch-bad"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        # technology/ subdomain should reject application-architect as owner
        bad = demo / "02_design" / "architecture" / "technology" / "overview.md"
        bad.write_text(
            "---\nid: ARCH-TECH-OVR\ntitle: t\nowner: application-architect\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "architecture/technology owner mismatch" in r.stdout
    finally:
        _cleanup(name)


def test_architecture_owner_index_md_skipped():
    # index.md is director-shared and not subject to subdomain owner rule.
    name = "hv-arch-idx"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        idx = demo / "02_design" / "architecture" / "application" / "index.md"
        # bootstrap already wrote index.md; simulate a director-owned index
        idx.write_text(
            "---\nid: ARCH-APP-INDEX\ntitle: 응용 아키텍처\nowner: application-director\n---\n# 응용\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


# ---------- design-system owner check -------------------------------------

def test_design_system_owner_correct_passes():
    name = "hv-ds-ok"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        ds = demo / "02_design" / "design-system"
        (ds / "colors.md").write_text(
            "---\nid: DS-COLORS\ntitle: t\nowner: designer\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        (ds / "typography.md").write_text(
            "---\nid: DS-TYPO\ntitle: t\nauthor: designer-sonnet\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


def test_design_system_owner_wrong_fails():
    name = "hv-ds-bad"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        bad = demo / "02_design" / "design-system" / "colors.md"
        bad.write_text(
            "---\nid: DS-COLORS\ntitle: t\nowner: web-publisher\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "02_design/design-system owner mismatch" in r.stdout
    finally:
        _cleanup(name)


# ---------- UT variant ratio check ----------------------------------------

def test_ut_variant_ratio_correct_passes():
    name = "hv-ut-ok"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        ut_dir = demo / "02_design" / "unit-test-cases" / "UT-OK"
        ut_dir.mkdir(parents=True)
        (ut_dir / "UT-OK-01.md").write_text(
            "---\nid: UT-OK-01\ntitle: t\nparent-prg: PRG-OK-01\n"
            "variant-count: 10\nvariant-happy-count: 2\nvariant-exception-count: 8\n"
            "exception-categories: [1, 7]\ndepends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


def test_ut_variant_ratio_too_many_happy_fails():
    name = "hv-ut-happy"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        ut_dir = demo / "02_design" / "unit-test-cases" / "UT-BAD"
        ut_dir.mkdir(parents=True)
        # 5 happy + 5 exception → happy ratio 0.5 > 0.3
        (ut_dir / "UT-BAD-01.md").write_text(
            "---\nid: UT-BAD-01\ntitle: t\nparent-prg: PRG-BAD-01\n"
            "variant-count: 10\nvariant-happy-count: 5\nvariant-exception-count: 5\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "UT variant ratio violation" in r.stdout
        assert "happy" in r.stdout
    finally:
        _cleanup(name)


def test_ut_variant_ratio_sum_mismatch_fails():
    name = "hv-ut-sum"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        ut_dir = demo / "02_design" / "unit-test-cases" / "UT-SUM"
        ut_dir.mkdir(parents=True)
        (ut_dir / "UT-SUM-01.md").write_text(
            "---\nid: UT-SUM-01\ntitle: t\nparent-prg: PRG-SUM-01\n"
            "variant-count: 10\nvariant-happy-count: 2\nvariant-exception-count: 7\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode != 0
        assert "sum mismatch" in r.stdout
    finally:
        _cleanup(name)


def test_ut_variant_ratio_undefined_skipped():
    # frontmatter 에 ratio 필드가 전혀 없으면 advisory skip (단계적 도입)
    name = "hv-ut-skip"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        ut_dir = demo / "02_design" / "unit-test-cases" / "UT-SKIP"
        ut_dir.mkdir(parents=True)
        (ut_dir / "UT-SKIP-01.md").write_text(
            "---\nid: UT-SKIP-01\ntitle: t\ndepends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        _cleanup(name)


def test_ut_variant_ratio_advisory_warns_over_12():
    name = "hv-ut-warn"
    demo = ROOT / "projects" / name
    try:
        _bootstrap(name)
        ut_dir = demo / "02_design" / "unit-test-cases" / "UT-WARN"
        ut_dir.mkdir(parents=True)
        # 15 variants total — over 12, but ratio still valid
        (ut_dir / "UT-WARN-01.md").write_text(
            "---\nid: UT-WARN-01\ntitle: t\nparent-prg: PRG-WARN-01\n"
            "variant-count: 15\nvariant-happy-count: 3\nvariant-exception-count: 12\n"
            "depends-on: []\nreferenced-by: []\n---\n# t\n"
        )
        r = _validate(name)
        # advisory only — should still pass
        assert r.returncode == 0, r.stdout + r.stderr
        assert "variant advisory" in r.stderr
    finally:
        _cleanup(name)
