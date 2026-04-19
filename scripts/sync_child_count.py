#!/usr/bin/env python3
"""Sync index.md `child-count` frontmatter against actual directory contents.

Usage:
    scripts/sync_child_count.py <project>            # write mode (fix in place)
    scripts/sync_child_count.py <project> --check    # dry-run; exit 1 on drift

Motivation (new issue N12): every hierarchical index.md records a
`child-count:` field that must match the directory's real child-count (md
files + subdirectories excluding _archived/reviews). Agents write this once
at creation and frequently neglect to update it when children are added or
removed, leaving silent metadata drift that later confuses the RTM summary.

Exit codes:
    0   already in sync / updated successfully
    1   drift detected (--check)
    2   project not found
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
SKIP_SUBDIRS = {"_archived", "reviews"}


def actual_child_count(d: pathlib.Path) -> int:
    md_files = [p for p in d.iterdir() if p.is_file() and p.suffix == ".md" and p.name != "index.md"]
    subdirs = [p for p in d.iterdir() if p.is_dir() and p.name not in SKIP_SUBDIRS]
    return len(md_files) + len(subdirs)


def update_index(index_path: pathlib.Path, new_count: int) -> None:
    text = index_path.read_text()
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        return
    new_fm_lines = []
    replaced = False
    for line in fm_text.splitlines():
        if line.startswith("child-count:"):
            new_fm_lines.append(f"child-count: {new_count}")
            replaced = True
        else:
            new_fm_lines.append(line)
    if not replaced:
        new_fm_lines.append(f"child-count: {new_count}")
    new_text = "---\n" + "\n".join(new_fm_lines) + "\n---\n" + body
    index_path.write_text(new_text)


def scan(project_dir: pathlib.Path, check_only: bool, verbose: bool = True) -> int:
    drift_count = 0
    for index_path in project_dir.rglob("index.md"):
        d = index_path.parent
        if d.name in SKIP_SUBDIRS:
            continue
        text = index_path.read_text()
        fm_text, _body = split_frontmatter(text)
        if fm_text is None:
            continue
        fm = parse_frontmatter(fm_text)
        recorded = fm.get("child-count")
        if recorded is None:
            continue
        try:
            recorded_int = int(str(recorded).strip())
        except ValueError:
            continue
        actual = actual_child_count(d)
        if recorded_int == actual:
            continue
        drift_count += 1
        rel = index_path.relative_to(project_dir)
        if check_only:
            if verbose:
                print(f"DRIFT: {rel} child-count={recorded_int} but actual={actual}")
        else:
            update_index(index_path, actual)
            if verbose:
                print(f"SYNC: {rel} child-count {recorded_int} -> {actual}")
    return drift_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--check", action="store_true", help="dry-run; exit 1 on drift")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    if not project_dir.is_dir():
        print(f"error: project not found: {project_dir}", file=sys.stderr)
        sys.exit(2)

    drift = scan(project_dir, args.check, verbose=True)
    if args.check and drift:
        print(f"\n{drift} index.md file(s) have child-count drift.")
        sys.exit(1)
    if drift:
        print(f"OK: synced {drift} index.md file(s).")
    else:
        print(f"OK: projects/{args.project}/ child-count is clean.")


if __name__ == "__main__":
    main()
