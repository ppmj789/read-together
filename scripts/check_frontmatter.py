#!/usr/bin/env python3
"""Frontmatter completeness check for project artifact child files.

Usage:
    scripts/check_frontmatter.py <project>

Purpose (Phase 7 patch #1):
    Reduce QA-advisor false-positive reports about "frontmatter missing X" by
    providing an authoritative, automated scan. QA (via Track B) is expected
    to run this script before raising frontmatter issues and to cite its
    output verbatim rather than re-deriving the check from memory.

Checks for every non-index child file under projects/<name>/:
    - `id:` present and non-empty
    - `title:` present and non-empty
    - `depends-on:` present (may be [])
    - `referenced-by:` present (may be [])
    - `owner:` present and non-empty (exception: files under 99_audit/ may
      omit owner because audit-team does not declare an owner field)

Exit codes:
    0  all child files have complete frontmatter
    1  one or more frontmatter issues detected
    2  project not found / bad argument
"""
import argparse
import pathlib
import sys

try:
    from scripts._frontmatter import (  # type: ignore[reportMissingImports]
        split_frontmatter, parse_frontmatter, find_duplicate_keys,
    )
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from _frontmatter import (  # type: ignore
        split_frontmatter, parse_frontmatter, find_duplicate_keys,
    )

VERSION_RE = __import__("re").compile(r"^v\d+(\.\d+)?$")


ROOT = pathlib.Path(__file__).parent.parent

REQUIRED_FIELDS_CHILD = ("id", "title", "depends-on", "referenced-by", "owner")
# RTM/ and change-requests/ root are PM-owned log/tracking files with their
# own frontmatter schema (see templates/artifacts/rtm/, change-requests/).
# reviews/ files carry participants/date/target but omit the child owner field.
EXEMPT_DIRS = {"_archived", "src", "infra", "RTM", "reviews", "change-requests"}

# Stage-level meta files (not child artifacts). The SoW is user-authored and
# rollback-history is a PM-owned ledger with its own frontmatter schema.
EXEMPT_STAGE_FILES = {
    ("00_kickoff", "statement-of-work.md"),
    ("00_kickoff", "rollback-history.md"),
}


def _is_audit_path(rel: pathlib.PurePath) -> bool:
    return bool(rel.parts) and rel.parts[0] == "99_audit"


def scan(project_dir: pathlib.Path) -> list:
    issues = []
    for md in project_dir.rglob("*.md"):
        rel = md.relative_to(project_dir)
        if any(seg in EXEMPT_DIRS for seg in rel.parts):
            continue
        if md.name == "index.md":
            continue
        if len(rel.parts) <= 1:
            # root-level files (project-state, agent-call-log, escalations)
            continue
        if len(rel.parts) == 2 and (rel.parts[0], rel.parts[1]) in EXEMPT_STAGE_FILES:
            continue

        text = md.read_text()
        fm_text, _body = split_frontmatter(text)
        if fm_text is None:
            issues.append(f"{rel}: missing frontmatter block")
            continue

        # N3: duplicate-key detection — a later `key:` silently overwrites the
        # first under YAML semantics, losing the first value (observed in
        # Phase 7 review artifacts).
        for dup in find_duplicate_keys(fm_text):
            issues.append(f"{rel}: duplicate frontmatter key '{dup}' (later value silently overwrites earlier)")

        fm = parse_frontmatter(fm_text)

        for field in REQUIRED_FIELDS_CHILD:
            if field == "owner" and _is_audit_path(rel):
                continue
            if field not in fm:
                issues.append(f"{rel}: missing '{field}'")
                continue
            val = fm[field]
            if field in ("depends-on", "referenced-by"):
                if val is None:
                    issues.append(f"{rel}: '{field}' is null (use [] for empty)")
                continue
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(f"{rel}: '{field}' is empty")

        # N14: version format regex (v1, v1.1, v2 — not "3.9" Docker Compose strings)
        version = fm.get("version")
        if isinstance(version, str) and version.strip():
            if not VERSION_RE.match(version.strip()):
                issues.append(
                    f"{rel}: version '{version}' does not match ^v\\d+(\\.\\d+)?$"
                )

    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="project name under projects/")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"error: project not found: {project_dir}", file=sys.stderr)
        sys.exit(2)

    issues = scan(project_dir)
    if issues:
        for msg in issues:
            print(msg)
        print(f"\n{len(issues)} frontmatter issue(s) found.")
        sys.exit(1)
    print(f"OK: projects/{args.project}/ frontmatter is complete.")


if __name__ == "__main__":
    main()
