#!/usr/bin/env python3
"""Validate change-request metadata completeness (new issue N2).

Usage:
    scripts/validate_cr.py <project>

Each `projects/<project>/change-requests/CR-<seq>/` directory must contain a
full cycle of:
  1. index.md              — CR summary + status timeline
  2. cr-request.md         — original user request
  3. cr-impact-analysis.md — impact sections from app / infra / BM
  4. cr-decision.md        — user decision
  5. cr-action-result.md   — corrective-action result  (only required after
                             cr-decision.md's decision is 'approved' or
                             'conditional')

Each file must have the frontmatter fields prescribed by its template (see
templates/artifacts/change-requests/).

Exit codes:
    0   all CRs complete
    1   issues detected
    2   project not found
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


ROOT = pathlib.Path(__file__).parent.parent

REQUIRED_FIELDS = {
    "cr-request.md": ("type", "cr-id", "project", "requested-by", "date", "status"),
    "cr-impact-analysis.md": ("type", "cr-id", "project", "analyzed-by", "date", "status"),
    "cr-decision.md": ("type", "cr-id", "project", "decided-by", "date", "decision"),
    "cr-action-result.md": ("type", "cr-id", "project", "owner", "date", "status"),
    "index.md": ("type", "cr-id", "project", "status", "opened"),
}


def _read_fm(path: pathlib.Path):
    text = path.read_text()
    fm_text, _body = split_frontmatter(text)
    if fm_text is None:
        return None, []
    dupes = find_duplicate_keys(fm_text)
    return parse_frontmatter(fm_text), dupes


def check_cr_dir(cr_dir: pathlib.Path) -> list:
    issues = []
    cr_name = cr_dir.name
    for fname, required in REQUIRED_FIELDS.items():
        if fname == "cr-action-result.md":
            # Only required after decision approved / conditional
            decision_path = cr_dir / "cr-decision.md"
            if not decision_path.exists():
                continue
            fm, _dupes = _read_fm(decision_path)
            if fm is None:
                continue
            decision = str(fm.get("decision", "")).strip().lower()
            if decision not in {"approved", "conditional"}:
                continue
            if not (cr_dir / fname).exists():
                issues.append(f"{cr_name}/: missing {fname} (decision={decision})")
                continue
        elif not (cr_dir / fname).exists():
            if fname == "index.md":
                issues.append(
                    f"{cr_name}/: missing index.md (CR summary required by templates/artifacts/change-requests/index.md.tmpl)"
                )
            else:
                issues.append(f"{cr_name}/: missing {fname}")
            continue

        fm, dupes = _read_fm(cr_dir / fname)
        if fm is None:
            issues.append(f"{cr_name}/{fname}: missing frontmatter block")
            continue
        for dup in dupes:
            issues.append(f"{cr_name}/{fname}: duplicate frontmatter key '{dup}'")
        for field in required:
            if field not in fm:
                issues.append(f"{cr_name}/{fname}: missing '{field}'")
                continue
            val = fm[field]
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(f"{cr_name}/{fname}: '{field}' is empty")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="project name under projects/")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"error: project not found: {project_dir}", file=sys.stderr)
        sys.exit(2)

    cr_root = project_dir / "change-requests"
    if not cr_root.is_dir():
        print(f"OK: no change-requests/ directory — nothing to validate.")
        return

    cr_dirs = sorted(p for p in cr_root.iterdir() if p.is_dir() and p.name.startswith("CR-"))
    if not cr_dirs:
        print("OK: no CR-<seq>/ directories yet — nothing to validate.")
        return

    all_issues = []
    for cr_dir in cr_dirs:
        all_issues.extend(check_cr_dir(cr_dir))

    if all_issues:
        for msg in all_issues:
            print(msg)
        print(f"\n{len(all_issues)} CR metadata issue(s) found across {len(cr_dirs)} CR(s).")
        sys.exit(1)
    print(f"OK: {len(cr_dirs)} CR(s) validated; all metadata complete.")


if __name__ == "__main__":
    main()
