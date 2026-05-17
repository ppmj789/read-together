#!/usr/bin/env python3
"""Validate the projects/<name>/ledger/ delegation tree.

Checks (exit 1 on any failure, 0 if clean or no ledger dir):
  - frontmatter id == filename stem
  - parent referenced node file exists
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frontmatter import split_frontmatter, parse_frontmatter  # noqa: E402


def validate(project_root: Path) -> list[str]:
    errors: list[str] = []
    ledger = project_root / "ledger"
    if not ledger.is_dir():
        return errors
    nodes = sorted(p for p in ledger.glob("*.md") if p.name != "index.md")
    ids = {p.stem for p in nodes}
    for p in nodes:
        fm_text, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        fm = parse_frontmatter(fm_text) if fm_text is not None else {}
        node_id = str(fm.get("id", "")).strip()
        if node_id != p.stem:
            errors.append(f"{p.name}: frontmatter id '{node_id}' != filename stem '{p.stem}'")
        parent = str(fm.get("parent", "") or "").strip()
        if parent and parent not in ids:
            errors.append(f"{p.name}: parent '{parent}' has no node file")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_ledger.py <project_root>", file=sys.stderr)
        return 2
    errs = validate(Path(argv[1]))
    for e in errs:
        print(f"LEDGER-ERROR: {e}", file=sys.stderr)
    if errs:
        print(f"validate_ledger: {len(errs)} error(s)", file=sys.stderr)
        return 1
    print("validate_ledger: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
