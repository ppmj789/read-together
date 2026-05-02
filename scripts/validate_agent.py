#!/usr/bin/env python3
"""Validate Claude Code agent/role/skill files against v2 project conventions.

Usage:
    scripts/validate_agent.py <file.md> [<file.md> ...]
    scripts/validate_agent.py --all          # validate every file in .claude/{roles,agents,skills}/
    scripts/validate_agent.py --dir <path>   # validate every .md under <path>

File type is inferred from path:
    .claude/roles/<name>.md                  → role (single-source persona)
    .claude/agents/<name>.md                 → agent shell (Track B subagent shell)
    .claude/skills/<name>/SKILL.md           → skill shell

Returns exit 0 if all files validate, 1 otherwise.
"""
import argparse
import pathlib
import re
import sys

# Prefer importing as a package-style helper when invoked via pytest; fall back
# for direct CLI execution.
try:
    from scripts._frontmatter import split_frontmatter, parse_frontmatter  # type: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from _frontmatter import split_frontmatter, parse_frontmatter  # type: ignore


ROOT = pathlib.Path(__file__).parent.parent
ROLES_DIR = ROOT / ".claude" / "roles"
AGENTS_DIR = ROOT / ".claude" / "agents"
SKILLS_DIR = ROOT / ".claude" / "skills"

ALLOWED_MODELS = {"opus", "sonnet", "haiku"}
ALLOWED_EFFORTS = {"xhigh", "high", "medium"}          # low·max prohibited (decision #18)
FORBIDDEN_TOOLS = {"Agent", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet"}

# Required sections in role body
ROLE_REQUIRED_SECTIONS = [
    r"^# Role:",
    r"^## Mission",
    r"^## Responsibilities",
    r"^## How You Report",
    r"^## Artifacts You Own",
    r"^## Rules",
    r"^## Language",
]

# Fixed-model roles: role_name -> (model, effort)
FIXED_ROLE_MODEL = {
    "application-director":    ("opus",   "xhigh"),
    "infrastructure-director": ("opus",   "xhigh"),
    "business-manager":        ("sonnet", "xhigh"),
    "quality-assurance":       ("sonnet", "xhigh"),
    "tester":                  ("sonnet", "xhigh"),
    "audit-team":              ("sonnet", "xhigh"),
    "policy-engineer":         ("opus",   "xhigh"),
}
DYNAMIC_ROLE_NAMES = {
    "application-architect", "software-architect", "data-modeler", "part-leader",
    "backend-developer", "batch-developer", "web-developer", "web-publisher", "designer",
    "technical-architect", "database-administrator", "security-specialist",
    "infrastructure-engineer",
}
SKILL_ONLY = {"project-manager"}   # role exists, but no agent shell generated


# ---------------------------------------------------------------------------
# File-type classification
# ---------------------------------------------------------------------------

def classify(path: pathlib.Path) -> str:
    """Return 'role' | 'agent' | 'skill' | 'unknown' based on where the path
    sits relative to the nearest `.claude` ancestor segment. This works both
    for the real repo layout and for isolated tmp_path test fixtures."""
    parts = path.parts
    if ".claude" not in parts:
        return "unknown"
    idx = parts.index(".claude")
    tail = parts[idx + 1 :]
    if len(tail) >= 2 and tail[0] == "roles" and tail[-1].endswith(".md"):
        return "role"
    if len(tail) >= 2 and tail[0] == "agents" and tail[-1].endswith(".md"):
        return "agent"
    if len(tail) >= 3 and tail[0] == "skills" and tail[-1] == "SKILL.md":
        return "skill"
    return "unknown"


# ---------------------------------------------------------------------------
# Validators per file type
# ---------------------------------------------------------------------------

def validate_role(path: pathlib.Path, fm: dict, body: str) -> list:
    errs = []
    # frontmatter keys
    for k in ("name", "description"):
        if not fm.get(k):
            errs.append(f"role frontmatter: missing '{k}'")
    # tools/model/effort must NOT be in role frontmatter (single source has only persona)
    for forbidden in ("tools", "model", "effort"):
        if forbidden in fm:
            errs.append(f"role frontmatter: '{forbidden}' must not be declared in role file "
                        f"(roles/ are single-source persona; tools/model/effort live on agent shells and Skills)")

    # name ↔ filename
    role_name_from_file = path.stem
    if fm.get("name") and fm["name"] != role_name_from_file:
        errs.append(f"role frontmatter: name '{fm['name']}' != filename '{role_name_from_file}'")

    # required body sections
    for pat in ROLE_REQUIRED_SECTIONS:
        if not re.search(pat, body, re.MULTILINE):
            errs.append(f"role body: missing required section matching /{pat}/")

    # Known role name sanity
    all_known = set(FIXED_ROLE_MODEL.keys()) | DYNAMIC_ROLE_NAMES | SKILL_ONLY
    if role_name_from_file not in all_known:
        errs.append(f"role: unknown role-name '{role_name_from_file}' "
                    "(expected one of the 21 defined roles)")

    # Must reference one of the 3 track-involvement sections
    # Exception: audit-team has neither (isolation principle — does not invoke
    # or consult any performing-side agent, decision #15).
    if role_name_from_file != "audit-team":
        has_invoke = bool(re.search(r"^## How You Invoke Sub-executions", body, re.MULTILINE))
        has_consult = bool(re.search(r"^## How You Consult Advisors", body, re.MULTILINE))
        if not (has_invoke or has_consult):
            errs.append("role body: must have at least one of "
                        "'## How You Invoke Sub-executions' or '## How You Consult Advisors'")

    return errs


def validate_agent(fm: dict, body: str) -> list:
    errs = []
    # frontmatter keys
    for k in ("name", "description", "tools", "model", "effort"):
        if fm.get(k) in (None, "", []):
            errs.append(f"agent frontmatter: missing '{k}'")

    # tools must be exactly [Read, Glob, Grep]
    tools = fm.get("tools", [])
    if not isinstance(tools, list):
        errs.append("agent frontmatter: tools must be a flow list like [Read, Glob, Grep]")
        tools = []
    expected = {"Read", "Glob", "Grep"}
    if set(tools) != expected:
        errs.append(f"agent frontmatter: tools must be exactly {sorted(expected)} "
                    f"(Track B subagents are read-only — decision #21); got {sorted(set(tools))}")

    # forbidden tools
    for t in tools:
        if t in FORBIDDEN_TOOLS:
            errs.append(f"agent frontmatter: forbidden tool '{t}' "
                        f"(Agent/Task* removed per decisions #23, #13)")

    # model/effort
    model = fm.get("model")
    if model and model not in ALLOWED_MODELS:
        errs.append(f"agent frontmatter: model '{model}' not in {sorted(ALLOWED_MODELS)}")
    effort = fm.get("effort")
    if effort and effort not in ALLOWED_EFFORTS:
        errs.append(f"agent frontmatter: effort '{effort}' not in {sorted(ALLOWED_EFFORTS)} "
                    "(low/max prohibited per decision #18)")

    # Body must reference roles/ file
    name = fm.get("name", "")
    # Derive expected role file name: fixed role name as-is; dynamic <role>-<model> → <role>
    if name in FIXED_ROLE_MODEL:
        expected_role = name
    else:
        m = re.match(r"^([a-z-]+)-(opus|sonnet|haiku)$", name)
        expected_role = m.group(1) if m else name

    expected_ref = f".claude/roles/{expected_role}.md"
    if expected_ref not in body:
        errs.append(f"agent body: must reference '{expected_ref}' "
                    "(shell delegates persona to single-source roles/ file)")

    # PM must not have an agent shell
    if expected_role in SKILL_ONLY:
        errs.append(f"agent: role '{expected_role}' is Skill-only (decision #14) "
                    "— remove this agent shell")

    # fixed role sanity
    if name in FIXED_ROLE_MODEL:
        exp_model, exp_effort = FIXED_ROLE_MODEL[name]
        if model != exp_model:
            errs.append(f"agent fixed-role '{name}': expected model '{exp_model}', got '{model}'")
        if effort != exp_effort:
            errs.append(f"agent fixed-role '{name}': expected effort '{exp_effort}', got '{effort}'")

    # dynamic role sanity
    if name not in FIXED_ROLE_MODEL:
        m = re.match(r"^([a-z-]+)-(opus|sonnet|haiku)$", name)
        if not m:
            errs.append(f"agent name '{name}': expected '<role>-<opus|sonnet|haiku>' for dynamic role")
        else:
            role, model_suffix = m.group(1), m.group(2)
            if role not in DYNAMIC_ROLE_NAMES:
                errs.append(f"agent name '{name}': role '{role}' not a dynamic role "
                            "(expected one of: "
                            f"{sorted(DYNAMIC_ROLE_NAMES)})")
            if model != model_suffix:
                errs.append(f"agent name '{name}': model field '{model}' != filename suffix '{model_suffix}'")

    return errs


def validate_skill(fm: dict, body: str) -> list:
    errs = []
    # frontmatter keys
    for k in ("name", "description", "model", "effort"):
        if not fm.get(k):
            errs.append(f"skill frontmatter: missing '{k}'")

    # skill must be Opus + xhigh fixed
    if fm.get("model") != "opus":
        errs.append(f"skill frontmatter: model must be 'opus' (decision #19); got '{fm.get('model')}'")
    if fm.get("effort") != "xhigh":
        errs.append(f"skill frontmatter: effort must be 'xhigh' (decision #19); got '{fm.get('effort')}'")

    # skill body must reference corresponding roles/ file
    # derive role name from skill frontmatter name (e.g. 'project-manager')
    skill_name = fm.get("name", "")
    expected_ref = f".claude/roles/{skill_name}.md"
    if expected_ref not in body:
        errs.append(f"skill body: must reference '{expected_ref}' "
                    "(skill delegates persona to single-source roles/ file)")

    return errs


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def errors_for(path: pathlib.Path) -> list:
    if not path.exists():
        return [f"file not found: {path}"]
    text = path.read_text()
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        return ["frontmatter missing or malformed"]
    fm = parse_frontmatter(fm_text)

    kind = classify(path)
    if kind == "role":
        return validate_role(path, fm, body)
    if kind == "agent":
        return validate_agent(fm, body)
    if kind == "skill":
        return validate_skill(fm, body)
    return [f"path does not fit known categories (.claude/roles|agents|skills): {path}"]


def iter_all_files() -> list:
    files = []
    if ROLES_DIR.is_dir():
        files.extend(sorted(ROLES_DIR.glob("*.md")))
    if AGENTS_DIR.is_dir():
        files.extend(sorted(AGENTS_DIR.glob("*.md")))
    if SKILLS_DIR.is_dir():
        files.extend(sorted(SKILLS_DIR.glob("*/SKILL.md")))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help=".md files to validate (or use --all / --dir)")
    parser.add_argument("--all", action="store_true", help="validate every file under .claude/{roles,agents,skills}/")
    parser.add_argument("--dir", help="validate every *.md (and SKILL.md) under this directory")
    args = parser.parse_args()

    if args.all and args.dir:
        print("error: use --all or --dir, not both", file=sys.stderr)
        sys.exit(2)

    targets = []
    if args.all:
        targets = iter_all_files()
    elif args.dir:
        d = pathlib.Path(args.dir)
        targets = sorted(d.rglob("*.md"))
    else:
        targets = [pathlib.Path(p) for p in args.paths]

    if not targets:
        print("no files to validate", file=sys.stderr)
        sys.exit(2)

    had_errors = False
    for p in targets:
        errs = errors_for(p)
        if errs:
            had_errors = True
            for e in errs:
                print(f"{p}: {e}")
    if not had_errors:
        print(f"OK: {len(targets)} file(s) validated")
    sys.exit(1 if had_errors else 0)


if __name__ == "__main__":
    main()
