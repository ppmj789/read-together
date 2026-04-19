"""Unit tests for scripts/_frontmatter.py.

Covers the original inline + block-literal cases and the multi-line block list
support added 2026-04-19 (Phase 7 Task 8 finding).
"""
import pathlib
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _frontmatter import parse_frontmatter, split_frontmatter  # type: ignore  # noqa: E402


# --- split_frontmatter ---------------------------------------------------


def test_split_with_frontmatter():
    text = "---\nkey: value\n---\nbody here\n"
    fm, body = split_frontmatter(text)
    assert fm == "key: value"
    assert body == "body here\n"


def test_split_no_frontmatter():
    text = "no leading dashes\nbody\n"
    fm, body = split_frontmatter(text)
    assert fm is None
    assert body == text


# --- parse_frontmatter — scalars ----------------------------------------


def test_parse_simple_scalar():
    fm = parse_frontmatter("name: alice\nage: 30")
    assert fm == {"name": "alice", "age": "30"}


def test_parse_strips_trailing_comment():
    fm = parse_frontmatter("scale: small  # small | large\n")
    assert fm == {"scale": "small"}


# --- parse_frontmatter — inline flow list -------------------------------


def test_parse_inline_list():
    fm = parse_frontmatter("deps: [a, b, c]\n")
    assert fm == {"deps": ["a", "b", "c"]}


def test_parse_inline_empty_list():
    fm = parse_frontmatter("deps: []\n")
    assert fm == {"deps": []}


def test_parse_inline_list_strips_whitespace():
    fm = parse_frontmatter("deps: [  a , b ,c  ]\n")
    assert fm == {"deps": ["a", "b", "c"]}


# --- parse_frontmatter — block literal -----------------------------------


def test_parse_block_literal():
    text = textwrap.dedent(
        """\
        description: |
          line one
          line two
        next: value
        """
    )
    fm = parse_frontmatter(text)
    assert fm["description"] == "line one\nline two"
    assert fm["next"] == "value"


# --- parse_frontmatter — multi-line block list (NEW) ---------------------


def test_parse_block_list_two_items():
    text = textwrap.dedent(
        """\
        depends-on:
          - RQ-AUTH-01
          - RQ-AUTH-02
        """
    )
    fm = parse_frontmatter(text)
    assert fm == {"depends-on": ["RQ-AUTH-01", "RQ-AUTH-02"]}


def test_parse_block_list_followed_by_another_key():
    text = textwrap.dedent(
        """\
        depends-on:
          - A
          - B
        referenced-by:
          - C
        status: draft
        """
    )
    fm = parse_frontmatter(text)
    assert fm == {
        "depends-on": ["A", "B"],
        "referenced-by": ["C"],
        "status": "draft",
    }


def test_parse_block_list_at_end_of_frontmatter():
    text = textwrap.dedent(
        """\
        title: hello
        depends-on:
          - X
          - Y
          - Z
        """
    )
    fm = parse_frontmatter(text)
    assert fm == {"title": "hello", "depends-on": ["X", "Y", "Z"]}


def test_parse_empty_key_with_no_items_stays_string():
    """Empty `key:` with no following list items must keep string value
    (backward compat with prior parser behavior)."""
    text = "depends-on:\nstatus: draft\n"
    fm = parse_frontmatter(text)
    # depends-on is empty string (no items followed), not list
    assert fm["depends-on"] == ""
    assert fm["status"] == "draft"


def test_parse_mix_inline_and_block_lists():
    text = textwrap.dedent(
        """\
        a-inline: [1, 2]
        b-block:
          - x
          - y
        c-inline: []
        d-block:
          - z
        """
    )
    fm = parse_frontmatter(text)
    assert fm == {
        "a-inline": ["1", "2"],
        "b-block": ["x", "y"],
        "c-inline": [],
        "d-block": ["z"],
    }


def test_parse_block_list_single_item():
    text = textwrap.dedent(
        """\
        deps:
          - just-one
        """
    )
    fm = parse_frontmatter(text)
    assert fm == {"deps": ["just-one"]}


def test_parse_block_list_with_complex_values():
    """List items can contain spaces, hyphens, IDs."""
    text = textwrap.dedent(
        """\
        depends-on:
          - RQ-MEMBER-03
          - QA-REPORT-RESULTS
          - IT-RES-09
        """
    )
    fm = parse_frontmatter(text)
    assert fm == {"depends-on": ["RQ-MEMBER-03", "QA-REPORT-RESULTS", "IT-RES-09"]}
