#!/usr/bin/env python3
"""Transition audit FIND-*.md `status:` from raised → resolved after corrective action.

Usage:
    scripts/close_audit_findings.py <project> <cycle-id>
    scripts/close_audit_findings.py <project> <cycle-id> --check   # dry-run

Motivation (new issue N9): after the PM completes corrective actions for an
audit cycle, each `99_audit/<cycle>-audit/audit-report/FIND-*.md` must have
its frontmatter `status:` transitioned from `raised` to `resolved`. Phase 7
showed this transition was forgotten in practice — findings stayed at
`status: raised` forever, which loses closure information.

The script updates only findings whose `pm-classification:` is `A` (the
explicit RESOLVED path). Types B/C/D stay in their current status because
their closure semantics differ (accepted / deferred / observed).

Exit codes:
    0   all type-A findings closed (or already closed)
    1   type-A findings still raised (--check only); never fails outside check
    2   project / cycle not found
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


def _transition(path: pathlib.Path) -> bool:
    text = path.read_text()
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        return False
    new_fm_lines = []
    changed = False
    for line in fm_text.splitlines():
        if line.startswith("status:"):
            _, _, value = line.partition(":")
            value = value.strip()
            if value == "raised":
                new_fm_lines.append("status: resolved")
                changed = True
                continue
        new_fm_lines.append(line)
    if not changed:
        return False
    path.write_text("---\n" + "\n".join(new_fm_lines) + "\n---\n" + body)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("cycle_id", help="cycle dir name, e.g. 02_design or 03_closing")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"error: project not found: {project_dir}", file=sys.stderr)
        sys.exit(2)

    audit_report = project_dir / "99_audit" / f"{args.cycle_id}-audit" / "audit-report"
    if not audit_report.is_dir():
        print(f"error: audit report dir not found: {audit_report}", file=sys.stderr)
        sys.exit(2)

    still_raised = []
    transitioned = []
    for find_path in sorted(audit_report.glob("FIND-*.md")):
        text = find_path.read_text()
        fm_text, _body = split_frontmatter(text)
        if fm_text is None:
            continue
        fm = parse_frontmatter(fm_text)
        cls = str(fm.get("pm-classification", "")).strip().upper()
        status = str(fm.get("status", "")).strip().lower()
        # Only type A transitions to resolved. B stays accepted, C deferred, D observed.
        if cls != "A":
            continue
        if status != "raised":
            continue
        if args.check:
            still_raised.append(find_path.relative_to(project_dir))
            continue
        if _transition(find_path):
            transitioned.append(find_path.relative_to(project_dir))

    if args.check:
        if still_raised:
            for p in still_raised:
                print(f"STILL-RAISED: {p}")
            print(f"\n{len(still_raised)} type-A finding(s) still at status=raised.")
            sys.exit(1)
        print("OK: no type-A findings remain at status=raised.")
        return

    for p in transitioned:
        print(f"RESOLVED: {p}")
    if transitioned:
        print(f"\n{len(transitioned)} finding(s) transitioned to resolved.")
    else:
        print("OK: nothing to transition.")


if __name__ == "__main__":
    main()
