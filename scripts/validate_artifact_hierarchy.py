#!/usr/bin/env python3
"""Drift-guard for the v2 hierarchical artifact structure.

Usage:
    scripts/validate_artifact_hierarchy.py <project>

Checks:
1. Every directory under projects/<name>/ (excluding _archived, reviews, src,
   infra, and a short exempt list) has an index.md IF it has ≥3 child files
   (per spec §3-1 §2-13-7 "자식이 1–2개뿐인 디렉토리는 index.md 생략 허용").
2. Every child file's frontmatter `depends-on` and `referenced-by` lists point
   to real IDs found elsewhere in the project (bidirectional drift-guard).
3. 3-hop path limit: <stage>/<area>/<group>/<id>.md maximum depth.

Returns exit 0 if no drift, 1 otherwise.
"""
import argparse
import pathlib
import sys

try:
    from scripts._frontmatter import split_frontmatter, parse_frontmatter  # type: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from _frontmatter import split_frontmatter, parse_frontmatter  # type: ignore


ROOT = pathlib.Path(__file__).parent.parent

# Directories that do not need index.md (reviews, _archived, src, infra, top-level,
# and some leaf-only areas like change-requests root)
INDEX_EXEMPT_DIRS = {
    "_archived",
    "reviews",
    "src",
    "infra",
}


def load_child_files(project_dir: pathlib.Path) -> dict:
    """Walk project tree, collect frontmatter 'id' -> (path, fm) for child files.

    Index files (filename == 'index.md') are excluded from the ID map.
    """
    id_map = {}
    for md in project_dir.rglob("*.md"):
        if md.name == "index.md":
            continue
        # Skip root-level single files (project-state.md, escalations.md, agent-call-log.md)
        # those aren't in the ID system.
        try:
            rel = md.relative_to(project_dir)
        except ValueError:
            continue
        text = md.read_text()
        fm_text, _body = split_frontmatter(text)
        if fm_text is None:
            continue
        fm = parse_frontmatter(fm_text)
        cid = fm.get("id")
        if not cid:
            continue
        if cid in id_map:
            # Duplicate ID
            print(f"DUPLICATE ID: '{cid}' in {rel} and {id_map[cid][0].relative_to(project_dir)}",
                  file=sys.stderr)
            continue
        id_map[cid] = (md, fm)
    return id_map


def check_index_presence(project_dir: pathlib.Path) -> list:
    """Check that every directory with ≥3 child files has an index.md."""
    issues = []
    for d in project_dir.rglob("*"):
        if not d.is_dir():
            continue
        if d.name in INDEX_EXEMPT_DIRS:
            continue
        # Skip dirs whose path contains an exempt segment
        if any(seg in INDEX_EXEMPT_DIRS for seg in d.relative_to(project_dir).parts):
            continue
        children = [p for p in d.iterdir() if p.is_file() and p.suffix == ".md"]
        # Subdirectories count too — a section root with only subdirs still benefits from index
        subdirs = [p for p in d.iterdir() if p.is_dir() and p.name not in INDEX_EXEMPT_DIRS]
        total = len(children) + len(subdirs)
        index_path = d / "index.md"
        if total >= 3 and not index_path.exists():
            issues.append(f"missing index.md (child-count={total}): {d.relative_to(project_dir)}")
    return issues


def check_bidirectional_deps(project_dir: pathlib.Path, id_map: dict) -> list:
    """Check depends-on / referenced-by bidirectional consistency."""
    issues = []
    for cid, (path, fm) in id_map.items():
        deps = fm.get("depends-on", [])
        if isinstance(deps, str):
            # Normalize: flow-list not parsed? fallback split
            deps = [d.strip() for d in deps.strip("[]").split(",") if d.strip()]
        refs = fm.get("referenced-by", [])
        if isinstance(refs, str):
            refs = [r.strip() for r in refs.strip("[]").split(",") if r.strip()]

        rel = path.relative_to(project_dir)

        # Verify depends-on targets exist and list back-reference to us
        for dep in deps:
            if dep not in id_map:
                issues.append(f"{rel}: depends-on '{dep}' does not exist in project")
                continue
            _dep_path, dep_fm = id_map[dep]
            dep_refs = dep_fm.get("referenced-by", [])
            if isinstance(dep_refs, str):
                dep_refs = [r.strip() for r in dep_refs.strip("[]").split(",") if r.strip()]
            if cid not in dep_refs:
                issues.append(
                    f"{rel}: depends-on '{dep}' but '{dep}' is missing '{cid}' in its "
                    "referenced-by (bidirectional drift)"
                )

        # Verify referenced-by targets exist and list forward-reference to us
        for ref in refs:
            if ref not in id_map:
                issues.append(f"{rel}: referenced-by '{ref}' does not exist in project")
                continue
            _ref_path, ref_fm = id_map[ref]
            ref_deps = ref_fm.get("depends-on", [])
            if isinstance(ref_deps, str):
                ref_deps = [d.strip() for d in ref_deps.strip("[]").split(",") if d.strip()]
            if cid not in ref_deps:
                issues.append(
                    f"{rel}: referenced-by '{ref}' but '{ref}' is missing '{cid}' in its "
                    "depends-on (bidirectional drift)"
                )

    return issues


def check_depth_limit(project_dir: pathlib.Path) -> list:
    """3-hop path limit: <stage>/<area>/<group>/<id>.md max depth (4 path segments)."""
    issues = []
    for md in project_dir.rglob("*.md"):
        rel = md.relative_to(project_dir)
        parts = rel.parts
        # Allow root-level single files (statement-of-work etc. under 00_kickoff or root)
        if len(parts) <= 1:
            continue
        # 99_audit can go 5 deep (99_audit/<stage>-audit/<area>/<group>/<id>) — permit 5
        if parts[0] == "99_audit":
            max_depth = 5
        else:
            max_depth = 4
        if len(parts) > max_depth:
            issues.append(f"3-hop limit exceeded ({len(parts)} segments): {rel}")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="project name under projects/")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"error: project not found: {project_dir}", file=sys.stderr)
        sys.exit(2)

    all_issues = []

    id_map = load_child_files(project_dir)
    all_issues.extend(check_index_presence(project_dir))
    all_issues.extend(check_bidirectional_deps(project_dir, id_map))
    all_issues.extend(check_depth_limit(project_dir))

    if all_issues:
        for msg in all_issues:
            print(msg)
        print(f"\n{len(all_issues)} issue(s) found.")
        sys.exit(1)
    print(f"OK: projects/{args.project}/ hierarchy is clean "
          f"({len(id_map)} child file(s), index presence & bi-directional "
          "dependencies validated)")


if __name__ == "__main__":
    main()
