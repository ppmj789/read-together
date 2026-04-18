#!/usr/bin/env python3
"""Bootstrap a new project directory tree (v2 hierarchical structure).

Usage:
    python3 scripts/bootstrap_project.py <project-name> --scale small|large

Creates projects/<name>/ with the full v2 hierarchy per spec §3-1:
- each stage/area is a directory (not a single file)
- each directory gets an index.md from templates/artifacts/_common/
- top-level single files: statement-of-work.md, rollback-history.md,
  escalations.md, project-state.md, agent-call-log.md
- RTM/ directory (index + by-stage + _archived)
- 99_audit/ with design-audit and closing-audit (+ analysis-audit for large)
"""
import argparse
import datetime
import pathlib
import re
import shutil
import sys


ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = ROOT / "templates"
ARTIFACTS_TMPL = TEMPLATES_ROOT / "artifacts"
COMMON_INDEX = ARTIFACTS_TMPL / "_common" / "index.md.tmpl"
COMMON_CHILD = ARTIFACTS_TMPL / "_common" / "child.md.tmpl"

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

# Areas per stage (directories that get an index.md).
# key = relative path from project root, value = label used in the index header
STAGE_AREAS = {
    # 00_kickoff
    "00_kickoff": "착수 (Kickoff)",
    "00_kickoff/project-plan": "프로젝트 수행계획서",
    "00_kickoff/project-plan/wbs": "WBS",
    # 01_analysis
    "01_analysis": "분석 (Analysis)",
    "01_analysis/requirements": "요구사항",
    "01_analysis/as-is-analysis": "AS-IS 분석",
    "01_analysis/to-be-workflow": "TO-BE 워크플로우",
    "01_analysis/uat-test-cases": "UAT 테스트 케이스",
    "01_analysis/integration-test-cases": "통합 테스트 케이스",
    "01_analysis/reviews": "분석 리뷰",
    # 02_design
    "02_design": "설계 (Design)",
    "02_design/architecture": "아키텍처",
    "02_design/architecture/components": "아키텍처 컴포넌트",
    "02_design/db": "데이터베이스",
    "02_design/db/logical": "논리 데이터 모델",
    "02_design/db/physical": "물리 데이터 모델",
    "02_design/screens": "화면 설계",
    "02_design/interfaces": "인터페이스 설계",
    "02_design/programs": "프로그램 목록",
    "02_design/unit-test-cases": "단위 테스트 케이스",
    "02_design/security-review": "보안 리뷰",
    "02_design/reviews": "설계 리뷰",
    # 03_implementation
    "03_implementation": "구현 (Implementation)",
    "03_implementation/unit-test-results": "단위 테스트 결과",
    "03_implementation/reviews": "구현 리뷰",
    # 04_test
    "04_test": "시험 (Test)",
    "04_test/integration-test-results": "통합 테스트 결과",
    "04_test/system-test-results": "시스템 테스트 결과",
    "04_test/uat-results": "UAT 결과",
    "04_test/qa-report": "QA 리포트",
    "04_test/reviews": "시험 리뷰",
    # 05_deployment
    "05_deployment": "이행 (Deployment)",
    "05_deployment/deployment-plan": "이행 계획",
    "05_deployment/operation-manual": "운영 매뉴얼",
    "05_deployment/training-material": "교육 자료",
    "05_deployment/reviews": "이행 리뷰",
    # 99_audit
    "99_audit": "감리",
    "99_audit/02_design-audit": "설계 감리",
    "99_audit/02_design-audit/audit-report": "설계 감리 지적",
    "99_audit/02_design-audit/corrective-action-plan": "설계 감리 시정조치 계획",
    "99_audit/02_design-audit/corrective-action-result": "설계 감리 시정조치 결과",
    "99_audit/03_closing-audit": "종료 감리",
    "99_audit/03_closing-audit/audit-report": "종료 감리 지적",
    "99_audit/03_closing-audit/corrective-action-plan": "종료 감리 시정조치 계획",
    "99_audit/03_closing-audit/corrective-action-result": "종료 감리 시정조치 결과",
    # change-requests
    "change-requests": "변경 요청",
    # RTM
    "RTM": "RTM — 요구사항추적매트릭스",
    "RTM/by-stage": "RTM 단계별 상세",
}

LARGE_ONLY_AREAS = {
    "99_audit/01_analysis-audit": "분석 감리 (대규모 전용)",
    "99_audit/01_analysis-audit/audit-report": "분석 감리 지적",
    "99_audit/01_analysis-audit/corrective-action-plan": "분석 감리 시정조치 계획",
    "99_audit/01_analysis-audit/corrective-action-result": "분석 감리 시정조치 결과",
    "RTM/by-part": "RTM 파트별 상세 (대규모 전용)",
}

# Empty directories (_archived targets, no index.md)
EMPTY_DIRS = [
    "RTM/_archived",
]

# Root-level single files (template → destination)
ROOT_FILES = [
    ("statement-of-work.md.tmpl", "00_kickoff/statement-of-work.md"),
    ("rollback-history.md.tmpl",  "00_kickoff/rollback-history.md"),
    ("escalations.md.tmpl",       "escalations.md"),
    ("project-state.md.tmpl",     "project-state.md"),
    ("agent-call-log.md.tmpl",    "agent-call-log.md"),
]

# RTM tree special files
RTM_FILES = [
    ("rtm/index.md.tmpl",    "RTM/index.md"),
    ("rtm/by-stage.md.tmpl", "RTM/by-stage/analysis.md"),
    ("rtm/by-stage.md.tmpl", "RTM/by-stage/design.md"),
    ("rtm/by-stage.md.tmpl", "RTM/by-stage/implementation.md"),
    ("rtm/by-stage.md.tmpl", "RTM/by-stage/test.md"),
    ("rtm/by-stage.md.tmpl", "RTM/by-stage/deployment.md"),
]


def validate_name(name: str) -> None:
    if not name:
        print("error: project name must not be empty", file=sys.stderr)
        sys.exit(2)
    if not SAFE_NAME_RE.match(name):
        print(
            f"error: unsafe project name '{name}' — "
            "only alphanumerics, dash, and underscore are allowed",
            file=sys.stderr,
        )
        sys.exit(2)


def render_index(area_path: str, label: str) -> str:
    """Produce an index.md body by substituting placeholders in the common template."""
    base = COMMON_INDEX.read_text()
    # Heuristic: stage = first path segment, area = second onward
    parts = area_path.split("/")
    stage = parts[0]
    area = "/".join(parts[1:]) if len(parts) > 1 else ""
    artifact_id = area_path.upper().replace("/", "-").replace("_", "-") or "ROOT"
    today = datetime.date.today().isoformat()
    text = base
    text = text.replace("<PARENT-ID>", artifact_id)
    text = text.replace(
        "<00_kickoff | 01_analysis | 02_design | 03_implementation | 04_test | 05_deployment | 99_audit>",
        stage,
    )
    text = text.replace("<requirements | screens | programs | ...>", area or "(none)")
    text = text.replace(
        "# <단계> / <영역> [/ <그룹>] — <한국어 제목>",
        f"# {area_path} — {label}",
    )
    text = text.replace("YYYY-MM-DD", today)
    return text


def fill_project_state(path: pathlib.Path, project_name: str, scale: str) -> None:
    """Fill `project:`, `scale:`, `started:` in the project-state.md frontmatter."""
    text = path.read_text()
    today = datetime.date.today().isoformat()
    text = re.sub(r"(?m)^project:\s*$", f"project: {project_name}", text, count=1)
    text = re.sub(r"(?m)^started:\s*$", f"started: {today}", text, count=1)
    text = re.sub(
        r"(?m)^scale:\s*(#.*)?$",
        f"scale: {scale}              # small | large",
        text,
        count=1,
    )
    path.write_text(text)


def fill_agent_call_log(path: pathlib.Path, project_name: str) -> None:
    text = path.read_text()
    today = datetime.date.today().isoformat()
    text = text.replace("<프로젝트명>", project_name)
    text = text.replace("YYYY-MM-DD", today)
    path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="project name (alnum, dash, underscore only)")
    parser.add_argument("--scale", required=True, choices=("small", "large"),
                        help="project scale")
    args = parser.parse_args()

    validate_name(args.name)

    project_dir = ROOT / "projects" / args.name
    if project_dir.exists():
        print(f"error: projects/{args.name}/ already exists — refusing to overwrite",
              file=sys.stderr)
        return 1

    # Verify templates exist
    for must_exist in [COMMON_INDEX, ARTIFACTS_TMPL]:
        if not must_exist.exists():
            print(f"error: missing template path: {must_exist}", file=sys.stderr)
            return 3

    areas = dict(STAGE_AREAS)
    if args.scale == "large":
        areas.update(LARGE_ONLY_AREAS)

    created_dirs = []
    created_files = []

    # Create directories + index.md per area
    for rel_path, label in areas.items():
        d = project_dir / rel_path
        d.mkdir(parents=True, exist_ok=True)
        created_dirs.append(rel_path)

        index_path = d / "index.md"
        index_path.write_text(render_index(rel_path, label))
        created_files.append(str(index_path.relative_to(project_dir)))

    # Empty dirs (_archived, etc.)
    for rel in EMPTY_DIRS:
        d = project_dir / rel
        d.mkdir(parents=True, exist_ok=True)
        # Drop a .gitkeep so the empty dir can be tracked
        (d / ".gitkeep").touch()
        created_dirs.append(rel)

    # Root-level single files
    for tmpl_rel, dest_rel in ROOT_FILES:
        src = ARTIFACTS_TMPL / tmpl_rel
        if not src.is_file():
            print(f"error: missing template: {src}", file=sys.stderr)
            shutil.rmtree(project_dir, ignore_errors=True)
            return 3
        dest = project_dir / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        created_files.append(dest_rel)

    # RTM special files
    for tmpl_rel, dest_rel in RTM_FILES:
        src = ARTIFACTS_TMPL / tmpl_rel
        if not src.is_file():
            print(f"error: missing template: {src}", file=sys.stderr)
            shutil.rmtree(project_dir, ignore_errors=True)
            return 3
        dest = project_dir / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        created_files.append(dest_rel)

    # Post-process: project-state and agent-call-log
    fill_project_state(project_dir / "project-state.md", args.name, args.scale)
    fill_agent_call_log(project_dir / "agent-call-log.md", args.name)

    # Report
    print(f"Bootstrapped projects/{args.name}/ (scale={args.scale})")
    print()
    print(f"Created {len(created_dirs)} directories, {len(created_files)} seed files.")
    print(
        "\n다음 단계:\n"
        "  1. `00_kickoff/statement-of-work.md` 에 과업지시서 작성.\n"
        "  2. PM 세션 시작 (`cd ai_team && claude`) — SessionStart hook 이 "
        "`.claude/roles/project-manager.md` 자동 주입.\n"
        "  3. PM 이 business-manager 자문으로 `00_kickoff/project-plan/budget.md` "
        "예산 가이드를 확정한 뒤 01_analysis 진입."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
