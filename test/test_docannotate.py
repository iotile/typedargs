"""Tests for docstring based annotation system."""

# pylint: disable=unused-argument,redefined-outer-name,missing-docstring

import pytest
from builtins import int, str
from typedargs import type_system, docannotate, param, return_type
from typedargs.annotate import get_help
from typedargs.exceptions import ValidationError, ArgumentError
from typedargs.doc_annotate import parse_docstring


DOCSTRING1 = """Do something.

        Args:
            param1 (integer): A basic parameter
            param2 (bool): The basic dict parameter

        Returns:
            map(string, int): A generic struct
        """

HELPSTRING = """
basic_func(integer param1, bool param2)

Do something.

Args:
    param1 (integer): A basic parameter
    param2 (bool): The basic dict parameter

Returns:
    map(string, int): A generic struct
"""

def test_docannotate_basic():
    """Make sure we can docannotate a function."""

    @docannotate
    def basic_func(param1, param2):
        """Do something.

        Args:
            param1 (integer): A basic parameter
            param2 (bool): The basic dict parameter

        Returns:
            map(string, int): A generic struct
        """

        assert isinstance(param1, int)
        assert isinstance(param2, bool)

        return {'hello': 1}

    ret = basic_func('15', 'false')
    assert ret == {'hello': 1}

    formatted = basic_func.metadata.format_returnvalue(ret)
    assert formatted == "hello: 1"

    help_text = get_help(basic_func)
    assert help_text == HELPSTRING


def test_docparse():
    """Make sure we can parse a docstring."""

    params, retinfo = parse_docstring(DOCSTRING1)

    assert 'param1' in params
    assert 'param2' in params
    assert retinfo is not None


DOCSTRING_FORMATAS = """basic line

Returns:
    integer format-as hex: basic description.
"""

DOCSTRING_SHOWAS = """basic short desc

Returns:
    RandomType show-as string: basic description.
"""

DOCSTRING_CONTEXT = """basic short desc

Returns:
    RandomType show-as context: basic description.
"""


def test_return_parsing():
    """Make sure we can parse a show-as and format-as line."""

    _params, retinfo = parse_docstring(DOCSTRING_SHOWAS)
    assert retinfo == (None, str, True, None)

    _params, retinfo = parse_docstring(DOCSTRING_FORMATAS)
    assert retinfo == ("integer", "hex", True, None)

    _params, retinfo = parse_docstring(DOCSTRING_CONTEXT)
    assert retinfo == (None, None, False, None)
