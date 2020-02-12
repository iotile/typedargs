"""Tests for docstring based annotation system."""

# pylint: disable=unused-argument,redefined-outer-name,missing-docstring

import pytest
from typedargs import type_system, docannotate, param, return_type
from typedargs.annotate import get_help, context
from typedargs.exceptions import ValidationError, ArgumentError
from typedargs.doc_annotate import parse_docstring
from typedargs.doc_parser import ParsedDocstring
from typedargs.basic_structures import ParameterInfo


DOCSTRING1 = """Do something.

        Args:
            param1 (integer): A basic parameter
            param2 (bool): The basic dict parameter

        Returns:
            map(string, int): A generic struct

        Raises:
            Exception: Error description
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


def test_docannotate_no_docstring():
    """Make sure we can docannotate a function without docstring."""

    @docannotate
    def basic_func():
        pass

    try:
        # calling returns_data triggers docstring parsing
        _ = basic_func.metadata.returns_data()
    except:
        pytest.fail('Failed to decorate with docannotate a function without docstring.')


def test_docparse():
    """Make sure we can parse a docstring."""

    params, retinfo = parse_docstring(DOCSTRING1)

    assert 'param1' in params
    assert 'param2' in params
    assert retinfo is not None
    assert retinfo.type_name == 'map(string, int)'


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
    assert retinfo == (None, None, 'string', True, None)

    _params, retinfo = parse_docstring(DOCSTRING_FORMATAS)
    assert retinfo == (None, "integer", "hex", True, None)

    _params, retinfo = parse_docstring(DOCSTRING_CONTEXT)
    assert retinfo == (None, None, None, False, None)


DOCSTRING2 = """Do something.

        This function will do some random things.

        Here is a second paragraph of text about what it will
        do.

        - Here is the start of a list
          continuation of line 1
        - Line 2 of list

        UnsupportedSection:
            Here is text in an unsupported section.

            Here is a second unsupported paragraph.

        Args:
            param1 (integer): A basic parameter.
                Extra information about that basic parameter.
            param2 (bool): The basic dict parameter

        Returns:
            map(string, int): A generic struct.
            Here is more first paragraph text

            This is additional information about the return value.
        """


def test_parsed_doc():
    """Make sure we can correctly parse docstring sections."""

    parsed1 = ParsedDocstring(DOCSTRING1)
    parsed2 = ParsedDocstring(DOCSTRING2)

    assert parsed2.short_desc == u'Do something.'
    assert parsed1.short_desc == u'Do something.'

    assert parsed1.param_info == {u'param2': ParameterInfo(type_class=None, type_name=u'bool', validators=[], desc=u'The basic dict parameter'),
                                  u'param1': ParameterInfo(type_class=None, type_name=u'integer', validators=[], desc=u'A basic parameter')}


def test_return_value_formatter():
    """Make sure we support formatter for return object.

    Declaration of formatter for return object may look like

    Returns:
        <type> show-as <formatter>: description

    Where <formatter> could be 'context' or 'string' or part of return object method name.
    If <formatter> is not ('context' | 'string') then func.metadata.format_returnvalue(value) should look for a
    method name format_<formatter> on a given value object to get a string representation.
    Method format_<formatter> could be implemented as requiring argument or not requiring.
    """

    class ReturnType:
        def __init__(self):
            self.val = 'foo\nbar'

        def __str__(self):
            return self.val

        @staticmethod
        def format_single_string_1(val):
            val = str(val)
            return val.replace('\n', ' ')

        def format_single_string_2(self):
            return self.val.replace('\n', ' ')

    @docannotate
    def func_1():
        """
        Returns:
            ReturnType show-as single_string_1: an object with formatter method
        """
        return ReturnType()

    @docannotate
    def func_2():
        """
        Returns:
            ReturnType show-as single_string_2: an object with formatter method
        """
        return ReturnType()

    @docannotate
    def func_noformatter():
        """
        Returns:
            ReturnType show-as noformatter: an object with formatter method
        """
        return ReturnType()

    ret_value_1 = func_1()
    ret_value_2 = func_2()
    ret_value_noformatter = func_noformatter()
    # import pdb; pdb.set_trace()
    assert func_1.metadata.format_returnvalue(ret_value_1) == 'foo bar'
    assert func_2.metadata.format_returnvalue(ret_value_2) == 'foo bar'
    with pytest.raises(ValidationError):
        func_noformatter.metadata.format_returnvalue(ret_value_noformatter)


def test_return_value_formatter_string():
    """Make sure we support `show-as string` return annotation."""

    class ReturnType:
        def __init__(self):
            self.val = 'foo\nbar'

        def __str__(self):
            return self.val

    @docannotate
    def func_string():
        """
        Returns:
            ReturnType show-as string: some description
        """
        return ReturnType()

    ret_value = func_string()
    assert func_string.metadata.format_returnvalue(ret_value) == 'foo\nbar'


def test_func_type_annotation(caplog):
    """Make sure we support python 3 function type annotations."""

    @docannotate
    def func_ann(param: str, flag: bool = True) -> str:
        """A function with type annotations.
        Args:
            param: Description
            flag: An optional flag

        Returns:
            Some result
        """
        return param

    @docannotate
    def func_doc(param, flag=True):
        """A function with types specified in docstring.
        Args:
            param (str): Description
            flag (bool): An optional flag

        Returns:
            str: Some result
        """
        return param

    @docannotate
    def func_mismatch(param: str, flag: bool = True) -> str:
        """A function with type info mismatch between type annotations and docstring.
        Args:
            param (int): Description
            flag (bool): An optional flag

        Returns:
            str: Some result
        """
        return param

    # trigger docstring and type annotations parsing
    _ = func_ann.metadata.returns_data()
    _ = func_doc.metadata.returns_data()
    _ = func_mismatch.metadata.returns_data()

    def _types_list(f):
        types = [info.type_name for param, info in sorted(f.metadata.annotated_params.items())]
        types.append(f.metadata.return_info.type_name)
        return types

    func_ann_types = _types_list(func_ann)
    func_doc_types = _types_list(func_doc)
    func_mismatch_types = _types_list(func_mismatch)

    assert func_ann_types == ['bool', 'str', 'str']

    # Type names should be the same for parsing func_doc docstring and func_ann type annotations
    assert func_ann_types == func_doc_types

    # Check warning message about type info mismatch, it should be only one there for func_mismatch
    assert len(caplog.records) == 1
    warn_record = caplog.records[0]
    assert warn_record.levelname == 'WARNING'
    assert 'Type info mismatch' in warn_record.message and "func_mismatch" in warn_record.message

    # Type annotations for func_ann and func_mismatch are the same.
    # Check if parsed info is the same regardless of wrong param type in func_mismatch docstring
    assert func_ann_types == func_mismatch_types


def test_class_docstring_basic():
    """Make sure we can decorate a class with @docannotate to annotate its __init__() method.

    In this case the class docstring should be used and the __init__ docstring should be ignored.
    """

    @context("Demo")
    @docannotate
    class Demo:
        """A manager.

        Args:
            arg (str): description
        """
        def __init__(self, arg):
            """
            Args:
                arg (int): description
            """

    # trigger type info parsing
    Demo.__init__.metadata.returns_data()

    assert 'arg' in Demo.__init__.metadata.annotated_params
    assert Demo.__init__.metadata.annotated_params['arg'].type_name == 'str'


def test_class_docstring_and_annotations():
    """Make sure type annotations wins.

    In this case, the docstring should be ignored in favor of type annotations.
    """
    @context("Demo")
    @docannotate
    class Demo:
        """
        Args:
            arg (int): description
        """
        def __init__(self, arg: str):
            pass

    # trigger type info parsing
    Demo.__init__.metadata.returns_data()

    assert Demo.__init__.metadata.annotated_params['arg'].type_name == 'str'
