"""Minimal YAML-ish frontmatter parser shared by validator/bootstrap/scaffold scripts.

Avoids a PyYAML dependency. Supports:
- simple `key: value` lines
- block literal: `key: |\\n  line1\\n  line2\\n`
- inline flow list: `key: [a, b, c]`
- multi-line block list:
      key:
        - item1
        - item2
  (added 2026-04-19 — Phase 7 Task 8 finding: agent-emitted frontmatter often
  uses YAML block list, which silently parsed as empty before this change.)

Not a full YAML parser — just enough for the agent/role/skill frontmatter used
throughout this repo.
"""
import re

KEY_LINE_RE = re.compile(r"^[a-zA-Z_-][a-zA-Z0-9_-]*:")
LIST_ITEM_RE = re.compile(r"^\s+-\s+(.*)$")


def split_frontmatter(text: str):
    """Return (frontmatter_text or None, body)."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5:]


def find_duplicate_keys(fm) -> list:
    """Return the list of keys that appear more than once at top level.

    Detecting duplicates is important because a second assignment silently
    overwrites the first under YAML semantics — in this repo that has shown up
    as `reviewed-by: [...]` followed by `reviewed-by: []` on a later line,
    which parses to an empty list and loses the reviewer data (Phase 7
    findings agent-review scan, new issue N3).
    """
    if fm is None:
        return []
    seen: dict = {}
    dupes: list = []
    current_block_key = None
    current_list_key = None
    for line in fm.splitlines():
        if current_block_key is not None:
            if KEY_LINE_RE.match(line):
                current_block_key = None
            else:
                continue
        if current_list_key is not None:
            if LIST_ITEM_RE.match(line):
                continue
            current_list_key = None
        if KEY_LINE_RE.match(line):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            value = re.sub(r"\s+#.*$", "", value)
            if key in seen and key not in dupes:
                dupes.append(key)
            seen[key] = True
            if value == "|":
                current_block_key = key
            elif value == "" and not (value.startswith("[") and value.endswith("]")):
                current_list_key = key
    return dupes


def parse_frontmatter(fm) -> dict:
    """Parse one-level frontmatter into a dict.

    Values are either `str` (scalar or block literal), or `list[str]`
    (flow list `[a, b]` or multi-line block list `key:\\n  - a\\n  - b`).
    Blank lines inside a |-block are preserved.
    """
    if fm is None:
        return {}

    result: dict = {}
    current_block_key = None
    block_lines: list = []
    current_list_key = None
    list_items: list = []

    def _flush_block():
        nonlocal current_block_key, block_lines
        if current_block_key is not None:
            result[current_block_key] = "\n".join(block_lines).strip()
            current_block_key = None
            block_lines = []

    def _flush_list():
        """Promote pending block-list to a real list value.

        Only runs when items were actually collected — an empty `key:` with no
        following items keeps its `""` scalar value (backward compat).
        """
        nonlocal current_list_key, list_items
        if current_list_key is not None and list_items:
            result[current_list_key] = list_items
        current_list_key = None
        list_items = []

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

        # Inside a pending block-list: collect indented `- item` lines until
        # we see a new key line (or end of frontmatter).
        if current_list_key is not None:
            m = LIST_ITEM_RE.match(line)
            if m:
                list_items.append(m.group(1).strip())
                continue
            # Non-list line — flush whatever we have and re-process this line.
            _flush_list()

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
            elif value == "":
                # Empty value — could be a null scalar OR the start of a
                # multi-line block list. Default to "" (backward compat) and
                # let _flush_list promote it to a real list if items follow.
                current_list_key = key
                list_items = []
                result[key] = ""
            else:
                result[key] = value
        # Non-key, non-block, non-list-item lines are ignored.

    _flush_block()
    _flush_list()
    return result
