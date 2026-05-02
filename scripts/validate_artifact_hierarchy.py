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
   Group / index IDs (captured from `index.md` frontmatter `id:` of a directory
   with ≥3 children) are valid reference targets — this supports review /
   meeting artifacts that naturally reference a whole group rather than every
   child (Phase 7 patch #17).
3. 3-hop path limit: <stage>/<area>/<group>/<id>.md maximum depth.
4. 02_design/architecture/<subdomain>/ 자식 파일의 owner/author 페르소나가
   해당 subdomain 의 책임 페르소나와 일치 (application→AA·SWA,
   technology→TA, data→data-modeler, security→security-specialist).
5. 02_design/<area>/ 단일 페르소나 영역 owner 정합 (design-system→designer).
6. Audit-authored artifacts under 99_audit/: bidirectional checks are advisory
   only, because audit-team is forbidden from editing artifacts outside
   99_audit/ and therefore cannot inject back-references into peer
   corrective-action files (Phase 7 patch #19).

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

INDEX_EXEMPT_DIRS = {
    "_archived",
    "reviews",
    "src",
    "infra",
}


def _as_list(value):
    """Normalize a frontmatter scalar/list value into a Python list of str."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [s.strip() for s in value.strip("[]").split(",") if s.strip()]
    return []


def load_child_files(project_dir: pathlib.Path):
    """Walk project tree, collect both child files and index-level group IDs.

    Returns (id_map, group_id_map) where:
    - id_map maps child `id:` → (path, fm) for every non-index md file.
    - group_id_map maps index.md `id:` → (path, fm) for directories that act
      as a group (≥3 children via subdirs/files). Group IDs live in a
      *separate* namespace but are acceptable targets for depends-on /
      referenced-by references, since review and cross-cutting artifacts
      naturally reference a group instead of listing every child.
    """
    id_map = {}
    group_id_map = {}
    for md in project_dir.rglob("*.md"):
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

        if md.name == "index.md":
            if cid in group_id_map:
                print(
                    f"DUPLICATE GROUP ID: '{cid}' in {rel} and "
                    f"{group_id_map[cid][0].relative_to(project_dir)}",
                    file=sys.stderr,
                )
                continue
            group_id_map[cid] = (md, fm)
            continue

        if cid in id_map:
            print(
                f"DUPLICATE ID: '{cid}' in {rel} and "
                f"{id_map[cid][0].relative_to(project_dir)}",
                file=sys.stderr,
            )
            continue
        id_map[cid] = (md, fm)
    return id_map, group_id_map


def check_index_presence(project_dir: pathlib.Path) -> list:
    """Check that every directory with ≥3 child files has an index.md."""
    issues = []
    for d in project_dir.rglob("*"):
        if not d.is_dir():
            continue
        if d.name in INDEX_EXEMPT_DIRS:
            continue
        if any(seg in INDEX_EXEMPT_DIRS for seg in d.relative_to(project_dir).parts):
            continue
        children = [p for p in d.iterdir() if p.is_file() and p.suffix == ".md"]
        subdirs = [p for p in d.iterdir() if p.is_dir() and p.name not in INDEX_EXEMPT_DIRS]
        total = len(children) + len(subdirs)
        index_path = d / "index.md"
        if total >= 3 and not index_path.exists():
            issues.append(
                f"missing index.md (child-count={total}): {d.relative_to(project_dir)}"
            )
    return issues


def _is_audit_authored(rel: pathlib.PurePath) -> bool:
    """Return True for artifacts authored by audit-team (cannot edit peers)."""
    parts = rel.parts
    if len(parts) < 2:
        return False
    if parts[0] != "99_audit":
        return False
    # corrective-action-* and re-audit-report-* are PM-authored — peer editing
    # is permitted. audit-plan.md and audit-report/ are audit-team-authored.
    audit_segment = parts[-2] if len(parts) >= 2 else ""
    filename = parts[-1]
    if filename == "audit-plan.md":
        return True
    if audit_segment == "audit-report":
        return True
    if audit_segment.startswith("re-audit-report"):
        return True
    return False


def check_bidirectional_deps(project_dir: pathlib.Path, id_map: dict,
                             group_id_map: dict) -> list:
    """Check depends-on / referenced-by bidirectional consistency.

    Group IDs from `group_id_map` are accepted as reference targets but skip
    the back-reference check (an index's summary table expresses the
    back-reference narratively, not via frontmatter).
    Audit-authored artifacts are checked advisory-only (warnings to stderr).
    """
    issues = []
    valid_targets = set(id_map.keys()) | set(group_id_map.keys())

    for cid, (path, fm) in id_map.items():
        deps = _as_list(fm.get("depends-on"))
        refs = _as_list(fm.get("referenced-by"))
        rel = path.relative_to(project_dir)
        advisory = _is_audit_authored(rel)

        for dep in deps:
            if dep not in valid_targets:
                msg = f"{rel}: depends-on '{dep}' does not exist in project"
                if advisory:
                    print(f"WARN (audit-authored, advisory): {msg}", file=sys.stderr)
                else:
                    issues.append(msg)
                continue
            # Back-reference check only applies to child-level targets
            if dep in group_id_map:
                continue
            _dep_path, dep_fm = id_map[dep]
            dep_refs = _as_list(dep_fm.get("referenced-by"))
            if cid not in dep_refs:
                msg = (
                    f"{rel}: depends-on '{dep}' but '{dep}' is missing '{cid}' "
                    "in its referenced-by (bidirectional drift)"
                )
                if advisory:
                    print(f"WARN (audit-authored, advisory): {msg}", file=sys.stderr)
                else:
                    issues.append(msg)

        for ref in refs:
            if ref not in valid_targets:
                msg = f"{rel}: referenced-by '{ref}' does not exist in project"
                if advisory:
                    print(f"WARN (audit-authored, advisory): {msg}", file=sys.stderr)
                else:
                    issues.append(msg)
                continue
            if ref in group_id_map:
                continue
            _ref_path, ref_fm = id_map[ref]
            ref_deps = _as_list(ref_fm.get("depends-on"))
            if cid not in ref_deps:
                msg = (
                    f"{rel}: referenced-by '{ref}' but '{ref}' is missing '{cid}' "
                    "in its depends-on (bidirectional drift)"
                )
                if advisory:
                    print(f"WARN (audit-authored, advisory): {msg}", file=sys.stderr)
                else:
                    issues.append(msg)

    return issues


def check_depth_limit(project_dir: pathlib.Path) -> list:
    """3-hop path limit: <stage>/<area>/<group>/<id>.md max depth (4 segments).

    Exceptions:
    - 99_audit: 5 segments (audit subdirectory + corrective action breakdown).
    - 02_design/architecture: 5 segments. The architecture area is split into
      application/ + technology/ + data/ + security/ subdomains, each of which
      may contain components/ and decisions/ groups; CMP-* and ADR-* leaves
      therefore sit at 5 segments by design.
    """
    issues = []
    for md in project_dir.rglob("*.md"):
        rel = md.relative_to(project_dir)
        parts = rel.parts
        if len(parts) <= 1:
            continue
        if parts[0] == "99_audit":
            max_depth = 5
        elif len(parts) >= 2 and parts[0] == "02_design" and parts[1] == "architecture":
            max_depth = 5
        else:
            max_depth = 4
        if len(parts) > max_depth:
            issues.append(f"3-hop limit exceeded ({len(parts)} segments): {rel}")
    return issues


ARCHITECTURE_OWNERS = {
    "application": {"application-architect", "software-architect"},
    "technology":  {"technical-architect"},
    "data":        {"data-modeler"},
    "security":    {"security-specialist"},
}

# 02_design/<area>/ 단일 페르소나 owner 정합. index.md 는 검증 제외.
DESIGN_AREA_OWNERS = {
    "design-system": {"designer"},
}

_MODEL_SUFFIXES = ("-opus", "-sonnet", "-haiku")


def _strip_model_suffix(role: str) -> str:
    for suffix in _MODEL_SUFFIXES:
        if role.endswith(suffix):
            return role[: -len(suffix)]
    return role


def _check_owner_dir(project_dir: pathlib.Path, base: pathlib.Path,
                    allowed: set, label: str) -> list:
    issues = []
    if not base.is_dir():
        return issues
    for md in base.rglob("*.md"):
        if md.name == "index.md":
            continue
        text = md.read_text()
        fm_text, _body = split_frontmatter(text)
        if fm_text is None:
            continue
        fm = parse_frontmatter(fm_text)
        raw = fm.get("owner") or fm.get("author")
        if not raw:
            continue
        owner = _strip_model_suffix(str(raw).strip())
        if owner not in allowed:
            rel = md.relative_to(project_dir)
            issues.append(
                f"{label} owner mismatch: {rel} has owner/author='{raw}', "
                f"expected one of {sorted(allowed)}"
            )
    return issues


def check_architecture_owner(project_dir: pathlib.Path) -> list:
    """02_design/architecture/<subdomain>/ 자식 파일의 owner/author 가 해당
    subdomain 의 책임 페르소나와 일치하는지 검증.

    - application/ → application-architect 또는 software-architect
    - technology/  → technical-architect
    - data/        → data-modeler
    - security/    → security-specialist

    index.md 는 director 공동 책임으로 검증에서 제외.
    """
    issues = []
    for subdomain, allowed in ARCHITECTURE_OWNERS.items():
        base = project_dir / "02_design" / "architecture" / subdomain
        issues.extend(
            _check_owner_dir(project_dir, base, allowed,
                             f"architecture/{subdomain}")
        )
    return issues


def check_design_area_owner(project_dir: pathlib.Path) -> list:
    """02_design/<area>/ 단일 페르소나 owner 정합 검증 (예: design-system →
    designer 단독).
    """
    issues = []
    for area, allowed in DESIGN_AREA_OWNERS.items():
        base = project_dir / "02_design" / area
        issues.extend(
            _check_owner_dir(project_dir, base, allowed, f"02_design/{area}")
        )
    return issues


def report_orphans(project_dir: pathlib.Path, id_map: dict) -> None:
    """Print advisory WARN lines for orphan child files (referenced-by empty).

    Orphans are not always bugs — closing-audit findings and leaf deliverables
    often have no downstream consumers. The signal is still useful during
    stage-gate review (new issue N6).
    """
    count = 0
    for cid, (path, fm) in id_map.items():
        refs = _as_list(fm.get("referenced-by"))
        if refs:
            continue
        rel = path.relative_to(project_dir)
        # 99_audit findings and qa-report leaves are commonly terminal.
        if rel.parts and rel.parts[0] == "99_audit":
            continue
        print(
            f"WARN (orphan advisory): {rel} has empty referenced-by — confirm "
            "this is a terminal deliverable, not a missing back-reference.",
            file=sys.stderr,
        )
        count += 1
    if count:
        print(f"WARN: {count} orphan advisory message(s) above.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="project name under projects/")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"error: project not found: {project_dir}", file=sys.stderr)
        sys.exit(2)

    all_issues = []

    id_map, group_id_map = load_child_files(project_dir)
    all_issues.extend(check_index_presence(project_dir))
    all_issues.extend(check_bidirectional_deps(project_dir, id_map, group_id_map))
    all_issues.extend(check_depth_limit(project_dir))
    all_issues.extend(check_architecture_owner(project_dir))
    all_issues.extend(check_design_area_owner(project_dir))
    report_orphans(project_dir, id_map)

    if all_issues:
        for msg in all_issues:
            print(msg)
        print(f"\n{len(all_issues)} issue(s) found.")
        sys.exit(1)
    print(
        f"OK: projects/{args.project}/ hierarchy is clean "
        f"({len(id_map)} child file(s), {len(group_id_map)} group(s), "
        "index presence & bi-directional dependencies validated)"
    )


if __name__ == "__main__":
    main()
