#!/usr/bin/env python3
"""Derive thin Agent shell files from .claude/roles/*.md single-source personas.

v2 behavior (design spec §2-1, §2-3):
- .claude/roles/project-manager.md is Skill-only; no agent shell is generated.
- Fixed-model roles (6): one agent shell each at the specified model/effort.
- Dynamic-model roles (13): three shells each (opus/sonnet/haiku), all at effort xhigh.
- All shells are thin: frontmatter + a body that tells the subagent to Read the
  full persona from .claude/roles/<role>.md and answer as that role.

Output: 45 agent shell files under .claude/agents/.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent
ROLES_DIR = ROOT / ".claude" / "roles"
AGENTS_DIR = ROOT / ".claude" / "agents"

# Fixed-model roles: role_name -> (model, effort)
FIXED_ROLES = {
    "application-director":    ("opus",   "xhigh"),
    "infrastructure-director": ("opus",   "xhigh"),
    "business-manager":        ("sonnet", "xhigh"),
    "quality-assurance":       ("sonnet", "xhigh"),
    "tester":                  ("sonnet", "xhigh"),
    "audit-team":              ("sonnet", "xhigh"),
    "policy-engineer":         ("opus",   "xhigh"),
}

# Dynamic-model roles: 3 variants each (opus/sonnet/haiku), effort xhigh default
DYNAMIC_ROLES = [
    "application-architect",
    "software-architect",
    "data-modeler",
    "part-leader",
    "backend-developer",
    "batch-developer",
    "web-developer",
    "web-publisher",
    "designer",
    "technical-architect",
    "database-administrator",
    "security-specialist",
    "infrastructure-engineer",
]

MODELS = ("opus", "sonnet", "haiku")

# Role files that are Skill-only (no Agent shell generated)
SKILL_ONLY = {"project-manager"}

SHELL_TEMPLATE = """\
---
name: {name}
description: |
{description_indented}
tools: [Read, Glob, Grep]
model: {model}
effort: {effort}
---

# Role: {korean_name} (읽기 전용 자문 서브에이전트 껍데기)

이 파일은 Agent 툴 subagent_type 해석용 껍데기입니다. 호출되면 먼저
`Read` 로 `.claude/roles/{role_name}.md` 를 읽고 그 역할 관점으로 답하세요.

자문 규칙:
- 읽기 전용 분석·평가·조언만 수행 (Write/Edit/Bash 미보유).
- **저작이 필요한 작업이면** 그 사실을 응답에 명시하고, 상위(PM)에게
  general-purpose + 페르소나 주입 경로(call-playbook §0-1)로의 dispatch
  를 권고하세요. 이 껍데기로는 산출물·ledger 노드를 쓸 수 없습니다.
- 응답은 한국어로 간결하게.
"""


def parse_role(role_file: pathlib.Path):
    """Parse a roles/*.md file, return (name, description, korean_name)."""
    text = role_file.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{role_file}: missing frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{role_file}: unclosed frontmatter")
    fm = text[4:end]
    body = text[end + 5:]

    # name: simple single-line value
    m = re.search(r"^name:\s*(\S+)\s*$", fm, re.MULTILINE)
    if not m:
        raise ValueError(f"{role_file}: missing name field")
    name = m.group(1).strip()

    # description: block literal (description: |\n  line1\n  line2\n) or single-line
    desc_match = re.search(r"(?ms)^description:\s*\|\s*\n((?:(?:  |\t).*\n?)+?)(?=^\S|\Z)", fm)
    if desc_match:
        desc_raw = desc_match.group(1)
        description = "\n".join(
            line[2:] if line.startswith("  ") else line.lstrip("\t")
            for line in desc_raw.splitlines()
            if line.strip()
        )
    else:
        m2 = re.search(r"^description:\s*(.+?)\s*$", fm, re.MULTILINE)
        description = m2.group(1).strip() if m2 else ""

    # Korean role name from the first "# Role: ..." line in body
    m3 = re.search(r"^# Role:\s*(.+?)\s*$", body, re.MULTILINE)
    korean_name = m3.group(1).strip() if m3 else name

    return name, description, korean_name


def generate_shell(role_name: str, description: str, korean_name: str,
                   name: str, model: str, effort: str) -> str:
    description_indented = "\n".join(f"  {line}" for line in description.strip().split("\n"))
    return SHELL_TEMPLATE.format(
        name=name,
        description_indented=description_indented,
        model=model,
        effort=effort,
        korean_name=korean_name,
        role_name=role_name,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean", action="store_true",
                        help="Remove existing .claude/agents/*.md before generation")
    args = parser.parse_args()

    if not ROLES_DIR.is_dir():
        print(f"roles dir missing: {ROLES_DIR}", file=sys.stderr)
        sys.exit(1)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Wipe existing top-level .md files under agents/ (keep any subdirectories)
    if args.clean and not args.dry_run:
        for p in AGENTS_DIR.glob("*.md"):
            p.unlink()
            print(f"removed: {p}")

    role_files = sorted(ROLES_DIR.glob("*.md"))
    if not role_files:
        print(f"no role files in {ROLES_DIR}", file=sys.stderr)
        sys.exit(1)

    generated = []

    for rf in role_files:
        role_name = rf.stem
        if role_name in SKILL_ONLY:
            print(f"skip (Skill-only): {role_name}")
            continue

        name_fm, description, korean_name = parse_role(rf)
        if name_fm != role_name:
            print(f"warning: {rf}: frontmatter name '{name_fm}' != filename '{role_name}'",
                  file=sys.stderr)

        if role_name in FIXED_ROLES:
            model, effort = FIXED_ROLES[role_name]
            shell = generate_shell(
                role_name=role_name, description=description, korean_name=korean_name,
                name=role_name, model=model, effort=effort,
            )
            out_path = AGENTS_DIR / f"{role_name}.md"
            if args.dry_run:
                print(f"would write: {out_path}")
            else:
                out_path.write_text(shell)
                print(f"wrote: {out_path}")
            generated.append(out_path)
        elif role_name in DYNAMIC_ROLES:
            for model in MODELS:
                variant_name = f"{role_name}-{model}"
                shell = generate_shell(
                    role_name=role_name, description=description, korean_name=korean_name,
                    name=variant_name, model=model, effort="xhigh",
                )
                out_path = AGENTS_DIR / f"{variant_name}.md"
                if args.dry_run:
                    print(f"would write: {out_path}")
                else:
                    out_path.write_text(shell)
                    print(f"wrote: {out_path}")
                generated.append(out_path)
        else:
            print(f"warning: {rf}: role '{role_name}' not in FIXED_ROLES or DYNAMIC_ROLES",
                  file=sys.stderr)

    total_expected = len(FIXED_ROLES) + len(DYNAMIC_ROLES) * len(MODELS)
    print(f"\ngenerated {len(generated)} of {total_expected} expected shell(s)")


if __name__ == "__main__":
    main()
