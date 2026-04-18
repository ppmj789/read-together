"""Minimal YAML-ish frontmatter parser shared by validator/bootstrap/scaffold scripts.

Avoids a PyYAML dependency. Supports:
- simple `key: value` lines
- block literal: `key: |\\n  line1\\n  line2\\n`
- inline flow list: `key: [a, b, c]`
- multi-line flat list via `- item` lines (rare, not required here)

Not a full YAML parser — just enough for the agent/role/skill frontmatter used
throughout this repo.
"""
import re

KEY_LINE_RE = re.compile(r"^[a-zA-Z_-][a-zA-Z0-9_-]*:")


def split_frontmatter(text: str):
    """Return (frontmatter_text or None, body)."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5:]


def parse_frontmatter(fm) -> dict:
    """Parse one-level frontmatter into a dict.

    Values are either `str` (scalar or block literal), or `list[str]` (flow list).
    Blank lines inside a |-block are preserved.
    """
    if fm is None:
        return {}

    result: dict = {}
    current_block_key = None
    block_lines: list = []

    def _flush_block():
        nonlocal current_block_key, block_lines
        if current_block_key is not None:
            result[current_block_key] = "\n".join(block_lines).strip()
            current_block_key = None
            block_lines = []

    for line in fm.splitlines():
        if current_block_key is not None:
            # Inside |-block: close on the next key line, otherwise accumulate
            if KEY_LINE_RE.match(line):
                _flush_block()
                # fall through
            else:
                if line.startswith("  "):
                    block_lines.append(line[2:])
                elif line.startswith("\t"):
                    block_lines.append(line.lstrip("\t"))
                else:
                    block_lines.append(line)
                continue

        if KEY_LINE_RE.match(line):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # strip trailing comment after # (respects quoted, but agent frontmatter doesn't quote)
            value = re.sub(r"\s+#.*$", "", value)
            if value == "|":
                current_block_key = key
                result[key] = ""
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                if not inner:
                    result[key] = []
                else:
                    result[key] = [v.strip() for v in inner.split(",") if v.strip()]
            else:
                result[key] = value
        # Non-key, non-block lines are ignored by this minimal parser.

    _flush_block()
    return result
