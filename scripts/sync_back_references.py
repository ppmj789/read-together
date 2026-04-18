#!/usr/bin/env python3
"""Sync back-references for v2 hierarchical artifacts.

For every child file's `depends-on: [P1, P2, ...]` entry, ensure that each
parent file's `referenced-by:` list includes this child's `id`. Edits only
the single `referenced-by:` line per affected parent; preserves all other
formatting and front-matter content.

Idempotent: running twice with no new changes makes zero edits.

Usage:
    scripts/sync_back_references.py <project>            # apply
    scripts/sync_back_references.py <project> --check    # exit 1 if updates needed (CI mode)

Exit code:
    0  no changes needed (or applied successfully)
    1  --check mode and updates would be needed
    2  unrecoverable error (e.g., depends-on points at non-existent id)
"""
import argparse
import pathlib
import re
import sys

try:
    from scripts._frontmatter import split_frontmatter, parse_frontmatter  # type: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from _frontmatter import split_frontmatter, parse_frontmatter  # type: ignore


ROOT = pathlib.Path(__file__).parent.parent

REF_LINE_RE = re.compile(r"^(referenced-by:\s*)\[([^\]]*)\](\s*)$", re.MULTILINE)


def _normalize_list_value(value):
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            return [x.strip() for x in inner.split(",") if x.strip()]
        return [value] if value else []
    if value is None:
        return []
    return list(value)


def collect_children(project_dir: pathlib.Path):
    """Return dict id -> (path, fm_dict). Skips index.md and files without `id`."""
    out = {}
    for md in project_dir.rglob("*.md"):
        if md.name == "index.md":
            continue
        text = md.read_text()
        fm_text, _body = split_frontmatter(text)
        if fm_text is None:
            continue
        fm = parse_frontmatter(fm_text)
        cid = fm.get("id")
        if not cid:
            continue
        out[cid] = (md, fm)
    return out


def compute_required_back_refs(children: dict):
    """Return dict parent_id -> set of child_ids that should appear in parent's referenced-by."""
    required = {}
    for cid, (_p, fm) in children.items():
        deps = _normalize_list_value(fm.get("depends-on"))
        for dep in deps:
            required.setdefault(dep, set()).add(cid)
    return required


def update_referenced_by(text: str, new_list: list) -> str:
    """Replace the `referenced-by: [...]` line within the leading frontmatter only.

    Preserves leading whitespace and trailing whitespace around the line.
    Returns the new full text. Raises if no referenced-by line is found
    in the frontmatter (caller should ensure target has one).
    """
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        raise ValueError("no frontmatter")
    new_value = "[" + ", ".join(new_list) + "]"

    def _sub(m):
        return f"{m.group(1)}{new_value}{m.group(3)}"

    new_fm, n = REF_LINE_RE.subn(_sub, fm_text, count=1)
    if n == 0:
        raise ValueError("no referenced-by line found in frontmatter")
    return "---\n" + new_fm + "\n---\n" + body


def sync(project_name: str, *, check_only: bool = False) -> int:
    project_dir = ROOT / "projects" / project_name
    if not project_dir.is_dir():
        print(f"ERROR: project not found: {project_dir}", file=sys.stderr)
        return 2

    children = collect_children(project_dir)
    required = compute_required_back_refs(children)

    edits = 0
    errors = 0
    for parent_id, needed_set in required.items():
        if parent_id not in children:
            print(
                f"WARN: depends-on '{parent_id}' has no matching child file (broken reference)",
                file=sys.stderr,
            )
            errors += 1
            continue

        parent_path, parent_fm = children[parent_id]
        existing = set(_normalize_list_value(parent_fm.get("referenced-by")))

        missing = needed_set - existing
        if not missing:
            continue

        merged = sorted(existing | needed_set)
        if check_only:
            print(
                f"WOULD UPDATE: {parent_path.relative_to(ROOT)} (+{len(missing)}: "
                f"{', '.join(sorted(missing))})"
            )
            edits += 1
            continue

        text = parent_path.read_text()
        try:
            new_text = update_referenced_by(text, merged)
        except ValueError as e:
            print(
                f"ERROR: cannot update {parent_path.relative_to(ROOT)}: {e}",
                file=sys.stderr,
            )
            errors += 1
            continue
        parent_path.write_text(new_text)
        print(
            f"UPDATED: {parent_path.relative_to(ROOT)} (+{len(missing)}: "
            f"{', '.join(sorted(missing))})"
        )
        edits += 1

    if errors:
        return 2
    if check_only and edits:
        return 1
    if edits == 0:
        print(f"OK: {project_name} back-references already in sync.")
    else:
        print(f"OK: {project_name} updated {edits} parent file(s).")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("project", help="Project name under projects/")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report what would change but make no edits; exit 1 if any change needed.",
    )
    args = parser.parse_args(argv)
    return sync(args.project, check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
