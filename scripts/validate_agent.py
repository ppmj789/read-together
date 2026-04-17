#!/usr/bin/env python3
"""Validate a Claude Code agent .md file against project conventions."""
import sys
import re
import pathlib

ALLOWED_TOOLS = {
    "Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent",
    "TaskCreate", "TaskUpdate", "TaskList", "TaskGet",
    "WebFetch", "WebSearch",
}
ALLOWED_MODELS = {"opus", "sonnet", "haiku"}
ALLOWED_EFFORTS = {"xhigh", "high", "medium", "low"}
REQUIRED_FM = {"name", "description", "tools", "model", "effort"}
COMMON_SECTIONS = [
    r"^# Role:",
    r"^## Mission",
    r"^## Responsibilities",
    r"^## How You Report",
    r"^## Artifacts You Own",
    r"^## Rules",
    r"^## Language",
]


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :]


KEY_LINE_RE = re.compile(r"^[a-zA-Z_-]+:")


def parse_frontmatter(fm):
    """Minimal YAML-ish parser: one key per line, optional flow-list or |-block value.

    A `|`-block continues until the next line that matches the key pattern
    `^[a-zA-Z_-]+:`. Blank lines inside the block are preserved (as empty
    strings in the joined text) so descriptions with blank separators are
    not silently truncated.
    """
    result = {}
    current_block_key = None
    block_lines = []

    def _flush_block():
        nonlocal current_block_key, block_lines
        if current_block_key is not None:
            result[current_block_key] = "\n".join(block_lines).strip()
            current_block_key = None
            block_lines = []

    for line in fm.splitlines():
        if current_block_key is not None:
            # Inside a |-block: close on the next key line, otherwise accumulate.
            if KEY_LINE_RE.match(line):
                _flush_block()
                # fall through to handle this line as a new key
            else:
                # Preserve blank lines; strip up to 2 leading spaces of indent
                # (standard YAML block-scalar indent used in agent files).
                if line.startswith("  "):
                    block_lines.append(line[2:])
                else:
                    block_lines.append(line)
                continue

        if KEY_LINE_RE.match(line):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "|":
                current_block_key = key
                result[key] = ""
            elif value.startswith("[") and value.endswith("]"):
                result[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            else:
                result[key] = value
        # Lines outside a block that are not key lines (e.g. blank separators
        # or stray text) are ignored by this minimal parser.

    _flush_block()
    return result


def errors_for(path):
    text = path.read_text()
    # Normalize CRLF so files saved on Windows editors are accepted.
    text = text.replace("\r\n", "\n")
    fm_text, body = split_frontmatter(text)
    errs = []
    if fm_text is None:
        return ["frontmatter missing or malformed"]
    fm = parse_frontmatter(fm_text)

    for k in REQUIRED_FM:
        if k not in fm or fm[k] in (None, "", []):
            errs.append(f"frontmatter: missing field '{k}'")

    model = fm.get("model")
    if model and model not in ALLOWED_MODELS:
        errs.append(f"frontmatter: model '{model}' not in {sorted(ALLOWED_MODELS)}")

    effort = fm.get("effort")
    if effort and effort not in ALLOWED_EFFORTS:
        errs.append(f"frontmatter: effort '{effort}' not in {sorted(ALLOWED_EFFORTS)}")

    tools = fm.get("tools", [])
    if not isinstance(tools, list):
        errs.append("frontmatter: tools must be a list")
        tools = []
    for t in tools:
        if t not in ALLOWED_TOOLS:
            errs.append(f"frontmatter: tool '{t}' not allowed")

    has_agent = "Agent" in tools

    for pat in COMMON_SECTIONS:
        if not re.search(pat, body, re.MULTILINE):
            errs.append(f"body: missing required section matching /{pat}/")

    if has_agent:
        if not re.search(r"^## Who You Call", body, re.MULTILINE):
            errs.append("body: agent with Agent tool must have 'Who You Call' section")
    else:
        # leaf: must have Escalation Protocol (except audit-team which uses Rules instead)
        name = fm.get("name", "")
        if name != "audit-team":
            if not re.search(r"^## Escalation Protocol", body, re.MULTILINE):
                errs.append("body: leaf agent (no Agent tool) must have 'Escalation Protocol' section")

    return errs


def main():
    if len(sys.argv) < 2:
        print("usage: validate_agent.py <file.md> [<file.md> ...]", file=sys.stderr)
        sys.exit(2)
    had_errors = False
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if not p.exists():
            print(f"{arg}: file not found", file=sys.stderr)
            had_errors = True
            continue
        errs = errors_for(p)
        if errs:
            had_errors = True
            for e in errs:
                print(f"{arg}: {e}")
    sys.exit(1 if had_errors else 0)


if __name__ == "__main__":
    main()
