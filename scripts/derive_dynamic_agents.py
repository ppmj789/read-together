#!/usr/bin/env python3
"""Derive <role>-<model>.md agent files from .md.tmpl templates.

Reads every .md.tmpl in .claude/agents/templates/, substitutes
__NAME__ and __MODEL__ tokens in the frontmatter, and writes three
files per template: opus/sonnet/haiku variants.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_DIR = ROOT / ".claude" / "agents" / "templates"
OUTPUT_DIR = ROOT / ".claude" / "agents"

MODELS = ("opus", "sonnet", "haiku")


def derive_one(template_path: pathlib.Path, dry_run: bool = False) -> None:
    role = template_path.name.replace(".md.tmpl", "")
    template_text = template_path.read_text()
    for model in MODELS:
        name = f"{role}-{model}"
        out_text = template_text.replace("__NAME__", name).replace("__MODEL__", model)
        out_path = OUTPUT_DIR / f"{name}.md"
        if dry_run:
            print(f"would write: {out_path}")
        else:
            out_path.write_text(out_text)
            print(f"wrote: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Derive <role>-<model>.md agent files from .md.tmpl templates."
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    templates = sorted(TEMPLATES_DIR.glob("*.md.tmpl"))
    if not templates:
        print(f"no templates found in {TEMPLATES_DIR}", file=sys.stderr)
        sys.exit(1)
    for t in templates:
        derive_one(t, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
