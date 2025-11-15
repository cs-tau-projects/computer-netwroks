# test_utils.py
import os
import io
import textwrap
import pytest

from utils import load_users, balanced_parentheses, lcm, caesar


# ---------------------------
# load_users
# ---------------------------
def test_load_users_basic(tmp_path):
    users_txt = tmp_path / "users.txt"
    users_txt.write_text(
        "Alice\tsecret\n"
        "Bob\tsimplepass\n",
        encoding="utf-8"
    )
    users = load_users(str(users_txt))
    assert users == {"Alice": "secret", "Bob": "simplepass"}


def test_load_users_ignores_blank_and_malformed_lines(tmp_path):
    users_txt = tmp_path / "users.txt"
    users_txt.write_text(
        "\n"
        "Charlie\t pass with spaces  \n"
        "MALFORMED LINE WITHOUT TAB\n"
        "   \n"
        "Dana\tpw\n",
        encoding="utf-8"
    )
    users = load_users(str(users_txt))
    # MALFORMED line ignored, blanks ignored, values stripped
    assert users == {"Charlie": "pass with spaces", "Dana": "pw"}


def test_load_users_duplicate_username_last_wins(tmp_path):
    users_txt = tmp_path / "users.txt"
    users_txt.write_text(
        "Eve\tfirst\n"
        "Eve\tsecond\n",
        encoding="utf-8"
    )
    users = load_users(str(users_txt))
    assert users == {"Eve": "second"}


# ---------------------------
# balanced_parentheses
# ---------------------------
@pytest.mark.parametrize(
    "s,expected",
    [
        ("", True),          # empty is balanced
        ("()", True),
        ("()()", True),
        ("(())", True),
        ("(()())", True),
        ("(", False),
        (")", False),
        ("())(", False),
        ("(()", False),
    ],
)
def test_balanced_parentheses_valid_inputs(s, expected):
    assert balanced_parentheses(s) == expected


@pytest.mark.parametrize(
    "s",
    [
        "abc",       # letters not allowed
        "() ()",     # space not allowed
        "()\t()",    # tab not allowed
        "()[",       # other punctuation not allowed
        "( )",       # space between
    ],
)
def test_balanced_parentheses_invalid_inputs(s):
    assert balanced_parentheses(s) is None


# ---------------------------
# lcm
# ---------------------------
@pytest.mark.parametrize(
    "x,y,expected",
    [
        (0, 0, 0),
        (0, 5, 0),
        (5, 0, 0),
        (1, 1, 1),
        (6, 8, 24),
        (12, 18, 36),
        (7, 5, 35),
        (-6, 8, 24),    # sign shouldn’t matter in LCM
        (6, -8, 24),
        (-6, -8, 24),
    ],
)
def test_lcm_values(x, y, expected):
    assert lcm(x, y) == expected


def test_lcm_commutativity_and_associativity():
    # Basic spot checks for properties
    assert lcm(12, 18) == lcm(18, 12)
    # Associativity in general doesn’t strictly hold for LCM as a function of two args,
    # but lcm(a, lcm(b, c)) == lcm(lcm(a, b), c) should produce same result here:
    ab_c = lcm(lcm(4, 6), 8)
    a_bc = lcm(4, lcm(6, 8))
    assert ab_c == a_bc == 24


# ---------------------------
# caesar
# ---------------------------
def test_caesar_basic_shift():
    assert caesar("abc", 2) == "cde"
    assert caesar("xyz", 3) == "abc"   # wrap-around


def test_caesar_preserves_spaces_and_lowercases_output():
    assert caesar("a b c", 1) == "b c d"
    assert caesar("Hello World", 3) == "khoor zruog"  # lowercase output per spec


def test_caesar_negative_shift():
    assert caesar("bcd", -1) == "abc"
    assert caesar("abc", -3) == "xyz"


@pytest.mark.parametrize(
    "text",
    [
        "hi!",         # punctuation
        "hello2you",   # digits
        "tab\there",   # tabs
        "newline\nx",  # newlines
    ],
)
def test_caesar_invalid_characters_return_none(text):
    assert caesar(text, 5) is None
