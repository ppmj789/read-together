#!/usr/bin/env python3
"""Bootstrap a new project directory tree from artifact templates.

Usage:
    python3 scripts/bootstrap_project.py <project-name> --scale small|large

Creates projects/<name>/ with the full stage directory tree and seeds
the initial skeleton files from .claude/agents/templates/artifacts/.
"""
import argparse
import datetime
import pathlib
import re
import shutil
import sys


ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_DIR = ROOT / ".claude" / "agents" / "templates" / "artifacts"

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

BASE_DIRS = [
    "00_kickoff",
    "00_kickoff/reviews",
    "01_analysis",
    "01_analysis/reviews",
    "02_design",
    "02_design/reviews",
    "03_implementation",
    "03_implementation/reviews",
    "04_test",
    "04_test/reviews",
    "05_deployment",
    "05_deployment/reviews",
    "99_audit",
    "99_audit/02_design-audit",
    "99_audit/03_closing-audit",
    "change-requests",
    "RTM/_archived",
]

LARGE_ONLY_DIRS = [
    "99_audit/01_analysis-audit",
]

# (template_filename, destination_relative_to_project_root)
SEEDS = [
    ("statement-of-work.md.tmpl", "00_kickoff/statement-of-work.md"),
    ("project-plan.md.tmpl", "00_kickoff/project-plan.md"),
    ("rollback-history.md.tmpl", "00_kickoff/rollback-history.md"),
    ("project-state.md.tmpl", "project-state.md"),
    ("rtm.md.tmpl", "RTM.md"),
    ("escalations.md.tmpl", "escalations.md"),
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


def fill_project_state(path: pathlib.Path, project_name: str, scale: str) -> None:
    """Fill in the `project:`, `scale:`, `started:` frontmatter fields."""
    text = path.read_text()
    today = datetime.date.today().isoformat()
    # Replace only the first empty occurrence of each frontmatter key.
    text = re.sub(r"(?m)^project:\s*$", f"project: {project_name}", text, count=1)
    text = re.sub(r"(?m)^started:\s*$", f"started: {today}", text, count=1)
    text = re.sub(
        r"(?m)^scale:\s*(#.*)?$",
        f"scale: {scale}              # small | large",
        text,
        count=1,
    )
    path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap a new project directory tree from artifact templates."
    )
    parser.add_argument("name", help="project name (alnum, dash, underscore only)")
    parser.add_argument(
        "--scale",
        required=True,
        choices=("small", "large"),
        help="project scale",
    )
    args = parser.parse_args()

    validate_name(args.name)

    project_dir = ROOT / "projects" / args.name
    if project_dir.exists():
        print(
            f"error: projects/{args.name}/ already exists — refusing to overwrite",
            file=sys.stderr,
        )
        return 1

    # Create directories.
    dirs = list(BASE_DIRS)
    if args.scale == "large":
        dirs.extend(LARGE_ONLY_DIRS)

    created_dirs = []
    for d in dirs:
        target = project_dir / d
        target.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(target.relative_to(ROOT)))

    # Seed files from templates.
    created_files = []
    for tmpl_name, dest_rel in SEEDS:
        src = TEMPLATES_DIR / tmpl_name
        if not src.is_file():
            print(f"error: missing template: {src}", file=sys.stderr)
            # Cleanup already-created directory so we do not leave half-built state.
            shutil.rmtree(project_dir, ignore_errors=True)
            return 3
        dest = project_dir / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        created_files.append(str(dest.relative_to(ROOT)))

    # Fill project-state.md with project name, scale, and today's date.
    fill_project_state(project_dir / "project-state.md", args.name, args.scale)

    # Print summary.
    print(f"Bootstrapped projects/{args.name}/ (scale={args.scale})")
    print()
    print(f"Created {len(created_dirs)} directories:")
    for d in created_dirs:
        print(f"  - {d}/")
    print()
    print(f"Seeded {len(created_files)} files:")
    for f in created_files:
        print(f"  - {f}")
    print()
    print(
        "다음 단계: `00_kickoff/statement-of-work.md` 를 작성한 뒤 "
        "project-manager 에이전트를 호출하세요."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
