#!/usr/bin/env python3
"""Validate the projects/<name>/ledger/ delegation tree.

Checks (exit 1 on any failure, 0 if clean or no ledger dir):
  - frontmatter id == filename stem
  - parent referenced node file exists
  - closed node must have non-empty RESPONSE section
  - CHILD INDEX rows must refer to existing ledger files
  - artifacts frontmatter links must exist on disk
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frontmatter import split_frontmatter, parse_frontmatter  # noqa: E402


def _section(body: str, name: str) -> str:
    """Extract and return the content of a ## NAME section, stripping HTML comments."""
    marker = f"## {name}"
    if marker not in body:
        return ""
    seg = body.split(marker, 1)[1]
    if "\n## " in seg:
        seg = seg.split("\n## ", 1)[0]
    out, depth = [], 0
    i = 0
    while i < len(seg):
        if seg[i:i + 4] == "<!--":
            depth += 1
            i += 4
            continue
        if seg[i:i + 3] == "-->":
            depth -= 1
            i += 3
            continue
        if depth == 0:
            out.append(seg[i])
        i += 1
    return "".join(out).strip()


def validate(project_root: Path) -> list[str]:
    errors: list[str] = []
    ledger = project_root / "ledger"
    if not ledger.is_dir():
        return errors
    nodes = sorted(p for p in ledger.glob("*.md") if p.name != "index.md")
    ids = {p.stem for p in nodes}
    for p in nodes:
        body = p.read_text(encoding="utf-8")
        fm_text, _ = split_frontmatter(body)
        fm = parse_frontmatter(fm_text) if fm_text is not None else {}

        node_id = str(fm.get("id", "")).strip()
        if node_id != p.stem:
            errors.append(f"{p.name}: frontmatter id '{node_id}' != filename stem '{p.stem}'")

        parent = str(fm.get("parent", "") or "").strip()
        if parent and parent not in ids:
            errors.append(f"{p.name}: parent '{parent}' has no node file")

        status = str(fm.get("status", "")).strip()
        if status == "closed" and not _section(body, "RESPONSE"):
            errors.append(f"{p.name}: status=closed but RESPONSE section empty")

        for line in _section(body, "CHILD INDEX").splitlines():
            line = line.strip()
            if not line.startswith("|") or "child id" in line or set(line) <= {"|", "-", " "}:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells or not cells[0]:
                continue
            cid = cells[0]
            if not (ledger / f"{cid}.md").is_file():
                errors.append(f"{p.name}: CHILD INDEX lists '{cid}' but ledger/{cid}.md missing")

        raw_artifacts = fm.get("artifacts", [])
        if isinstance(raw_artifacts, list):
            artifact_items = raw_artifacts
        else:
            raw_str = str(raw_artifacts).strip().strip("[]")
            artifact_items = [s.strip().strip("'\"") for s in raw_str.split(",") if s.strip()]
        for rel in artifact_items:
            if not (project_root / rel).exists():
                errors.append(f"{p.name}: artifacts link '{rel}' does not exist")

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
