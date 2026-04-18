#!/usr/bin/env python3
"""Scaffold a new artifact directory or child file within a project.

Two modes:

1. Ensure an area/group directory exists with its index.md:
     scripts/scaffold_artifact.py <project> <stage>/<area>[/<group>]

2. Create a child file within an existing indexed area:
     scripts/scaffold_artifact.py <project> <stage>/<area> \\
         --child <child-id> --title "<한국어 제목>" --owner <role-name>

The child file is created from templates/artifacts/_common/child.md.tmpl and
its frontmatter is filled in. The parent index.md's child table is appended.

Examples:
    scripts/scaffold_artifact.py book-mgmt-api 01_analysis/requirements
    scripts/scaffold_artifact.py book-mgmt-api 01_analysis/requirements/RQ-AUTH
    scripts/scaffold_artifact.py book-mgmt-api 01_analysis/requirements/RQ-AUTH \\
        --child RQ-AUTH-01 --title "로그인 기능" --owner application-architect
"""
import argparse
import datetime
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = ROOT / "templates" / "artifacts"
COMMON_INDEX = TEMPLATES_ROOT / "_common" / "index.md.tmpl"
COMMON_CHILD = TEMPLATES_ROOT / "_common" / "child.md.tmpl"


def project_root(project_name: str) -> pathlib.Path:
    p = ROOT / "projects" / project_name
    if not p.is_dir():
        print(f"error: project '{project_name}' not found at {p}", file=sys.stderr)
        sys.exit(2)
    return p


def ensure_index(area_dir: pathlib.Path, stage: str, area: str, label: str) -> pathlib.Path:
    idx = area_dir / "index.md"
    if idx.exists():
        return idx
    area_dir.mkdir(parents=True, exist_ok=True)
    template = COMMON_INDEX.read_text()
    artifact_id = (f"{stage}-{area}" if area else stage).upper().replace("/", "-").replace("_", "-")
    today = datetime.date.today().isoformat()
    text = template
    text = text.replace("<PARENT-ID>", artifact_id)
    text = text.replace(
        "<00_kickoff | 01_analysis | 02_design | 03_implementation | 04_test | 05_deployment | 99_audit>",
        stage,
    )
    text = text.replace("<requirements | screens | programs | ...>", area or "(none)")
    text = text.replace(
        "# <단계> / <영역> [/ <그룹>] — <한국어 제목>",
        f"# {stage}{('/' + area) if area else ''} — {label}",
    )
    text = text.replace("YYYY-MM-DD", today)
    idx.write_text(text)
    return idx


def append_child_row(index_path: pathlib.Path, child_id: str, title: str,
                     file_link: str, owner: str, status: str, summary: str) -> None:
    """Insert a row into the '하위 항목' table in index.md (after header row)."""
    text = index_path.read_text()
    new_row = f"| {child_id} | {title} | [{file_link}]({file_link}) | {owner} | {status} | {summary} |"

    # Find the '하위 항목' section, the table header, and the separator line
    header_marker = "## 하위 항목"
    hdr_idx = text.find(header_marker)
    if hdr_idx == -1:
        raise RuntimeError(f"index.md missing '{header_marker}' section: {index_path}")
    # Find separator line '|----|------|...' after the header row
    sep_pattern = re.compile(r"^\|[-\s|]+\|\s*$", re.MULTILINE)
    sep_match = sep_pattern.search(text, hdr_idx)
    if not sep_match:
        raise RuntimeError(f"index.md table separator not found: {index_path}")
    insert_at = sep_match.end()
    # If a placeholder row '| (자식 파일...' exists right after separator, replace it
    after = text[insert_at:].lstrip("\n")
    placeholder_re = re.compile(r"^\|\s*\(자식 파일[^\n]*\n", re.MULTILINE)
    pm = placeholder_re.match(after)
    if pm:
        # Replace placeholder
        replaced = after[:pm.start()] + new_row + "\n" + after[pm.end():]
        text = text[:insert_at] + "\n" + replaced
    else:
        # Insert directly after separator
        text = text[:insert_at] + "\n" + new_row + text[insert_at:]
    index_path.write_text(text)


def create_child(area_dir: pathlib.Path, child_id: str, title: str,
                 stage: str, area: str, group: str, owner: str) -> pathlib.Path:
    """Create <child_id>-<slug>.md in area_dir from the common child template."""
    # Slug from title: lowercase, replace spaces with dashes, strip punctuation
    slug = re.sub(r"[^a-zA-Z0-9가-힣\s-]", "", title).strip()
    slug = re.sub(r"\s+", "-", slug).lower()
    if not slug:
        slug = "item"
    filename = f"{child_id}-{slug}.md" if slug else f"{child_id}.md"
    target = area_dir / filename
    if target.exists():
        print(f"error: child file already exists: {target}", file=sys.stderr)
        sys.exit(1)

    today = datetime.date.today().isoformat()
    template = COMMON_CHILD.read_text()
    text = template
    text = text.replace("<ID>", child_id)
    text = text.replace("<한국어 제목>", title)
    text = text.replace(
        "<00_kickoff | 01_analysis | 02_design | 03_implementation | 04_test | 05_deployment | 99_audit>",
        stage,
    )
    # The child template has `area: <영역>` — replace with actual path
    text = re.sub(r"(?m)^area:\s*<영역>.*$", f"area: {area}", text, count=1)
    # Replace empty group: keep the key if group provided, blank otherwise
    if group:
        text = re.sub(r"(?m)^group:\s*$", f"group: {group}", text, count=1)
        text = re.sub(r"(?m)^group:\s*#.*$", f"group: {group}", text, count=1)
    text = re.sub(r"(?m)^owner:\s*<role-name>\s*#.*$", f"owner: {owner}", text, count=1)
    text = text.replace("YYYY-MM-DD", today)

    target.write_text(text)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", help="project name")
    parser.add_argument("area_path",
                        help="relative path under project root, e.g. 01_analysis/requirements "
                             "or 01_analysis/requirements/RQ-AUTH")
    parser.add_argument("--label", default="",
                        help="한국어 제목 used in index.md header when creating the area")
    parser.add_argument("--child", help="child ID (e.g. RQ-AUTH-01) to create a new file in this area")
    parser.add_argument("--title", default="", help="child file title (한국어)")
    parser.add_argument("--owner", default="", help="owner role-name for the child file")
    parser.add_argument("--status", default="draft", choices=["draft", "in-review", "approved"],
                        help="initial status for the child row in index (default draft)")
    parser.add_argument("--summary", default="", help="one-line summary for the child row in index")
    args = parser.parse_args()

    project_dir = project_root(args.project)
    area_dir = project_dir / args.area_path

    # Derive stage, area, group
    parts = args.area_path.split("/")
    stage = parts[0]
    area = "/".join(parts[1:]) if len(parts) > 1 else ""
    group = parts[-1] if len(parts) >= 3 else ""

    # Always ensure the index exists
    label = args.label or args.area_path
    ensure_index(area_dir, stage, area, label)
    print(f"ensured: {area_dir}/index.md")

    # Optionally create a child
    if args.child:
        if not args.title:
            print("error: --child requires --title", file=sys.stderr)
            sys.exit(2)
        if not args.owner:
            print("error: --child requires --owner (role-name)", file=sys.stderr)
            sys.exit(2)
        target = create_child(area_dir, args.child, args.title,
                              stage=stage, area=area, group=group, owner=args.owner)
        print(f"created: {target}")

        link = target.name  # relative to index.md in the same directory
        summary = args.summary or args.title
        append_child_row(area_dir / "index.md",
                         child_id=args.child, title=args.title,
                         file_link=f"./{link}", owner=args.owner,
                         status=args.status, summary=summary)
        print(f"updated: {area_dir}/index.md (appended child row)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
