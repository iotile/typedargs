"""Tests for docstring based annotation system."""

# pylint: disable=unused-argument,redefined-outer-name,missing-docstring

import pytest
from typedargs import type_system, docannotate, param, return_type
from typedargs.annotate import get_help, context
from typedargs.exceptions import ValidationError, ArgumentError
from typedargs.doc_annotate import parse_docstring
from typedargs.doc_parser import ParsedDocstring
from typedargs.basic_structures import ParameterInfo
from typing import Any, List, Dict

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
    assert retinfo == (None, None, ('string', []), True, None)

    _params, retinfo = parse_docstring(DOCSTRING_FORMATAS)
    assert retinfo == (None, "integer", ("hex", []), True, None)

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


def test_recursive_parsing_formatters():
    """Make sure we can parse recursive return value formatters."""

    class User:
        def __init__(self, short_name):
            self.short_name = short_name

        @classmethod
        def format_short_name(cls, obj):
            return obj.short_name

    @docannotate
    def func() -> Dict[User, int]:
        """
        Returns:
            dict show-as one_line[short_name, hex]: value description
        """
        return {User('john'): 15, User('bob'): 100}

    assert func.metadata.format_returnvalue(func()) == 'bob: 0x64; john: 0xF;'


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


def test_class_docannotate_no_doc():
    """Make sure we can use @docannotate on class without docstring.

    Type annotations should be used to annotate __init__() method.
    """

    @context("Demo")
    @docannotate
    class Demo:
        def __init__(self, arg: str):
            pass

    # trigger type info parsing
    Demo.__init__.metadata.returns_data()

    assert 'arg' in Demo.__init__.metadata.annotated_params
    assert Demo.__init__.metadata.annotated_params['arg'].type_class == str


def test_class_docannotate_2_docstrings():
    """Make __init__ method is annotated correctly when the class and its __init__ method has docstrings.

    If both docstrings exist then class docstring should be used and __init__ docstring should be ignored.
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


def test_class_docstring_and_annotations(caplog):
    """Make sure type annotations wins if we decorate a class with @docannotate.

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

    assert Demo.__init__.metadata.annotated_params['arg'].type_class == str

    # Check warning message about type info mismatch, it should be only one there for "Demo.__init__"
    assert len(caplog.records) == 1
    warn_record = caplog.records[0]
    assert warn_record.levelname == 'WARNING'
    assert 'Type info mismatch' in warn_record.message and "Demo.__init__" in warn_record.message


def test_docannotate_class_init(caplog):
    """Make sure we can use @docannotate on class __init__() method.

    If method has a type annotations then docstring types should be ignored.
    """

    @context("Demo")
    class Demo:

        @docannotate
        def __init__(self, arg):
            """
            Args:
                arg (str): description
            """

    @context("DemoAnn")
    class DemoAnn:

        @docannotate
        def __init__(self, arg: str):
            pass

    # trigger type info parsing
    Demo.__init__.metadata.returns_data()
    DemoAnn.__init__.metadata.returns_data()

    assert 'arg' in Demo.__init__.metadata.annotated_params
    assert 'arg' in DemoAnn.__init__.metadata.annotated_params

    assert Demo.__init__.metadata.annotated_params['arg'].type_name == 'str'
    assert DemoAnn.__init__.metadata.annotated_params['arg'].type_class == str


def test_custom_type_class():
    """Make sure we can annotate a function with type class.

    @docannotate should use methods of this class to convert arguments from string,
    to validate arguments and to format return value.
    """

    class DemoInteger:
        def __init__(self, value: int):
            self.value = value

        def __eq__(self, other):
            return self.__class__ == other.__class__ and self.value == other.value

        @classmethod
        def FromString(cls, arg):
            return cls(int(arg))

        @classmethod
        def validate_positive(cls, arg):
            if arg.value <= 0:
                raise ValueError('Object value is not positive.')

        @classmethod
        def format_hex(cls, arg):
            return "0x%X" % arg.value

    @docannotate
    def func(arg: DemoInteger) -> DemoInteger:
        """Basic function.

        Args:
            arg: {positive} The input that will be converted to DemoInteger

        Returns:
            DemoInteger show-as hex: Some description
        """
        return arg

    # trigger type info parsing
    func.metadata.returns_data()

    ret_value = func('1')

    # Support of argument conversion from string should not break original function behaviour
    assert func(DemoInteger(1)) == DemoInteger(1)

    # check converting from string
    assert ret_value == DemoInteger(1)

    # check argument validation
    with pytest.raises(ValidationError) as exc_info:
        func('-1')

    assert 'Object value is not positive.' in exc_info.value.msg

    # check formatting return value
    assert func.metadata.format_returnvalue(ret_value) == '0x1'

    # trying to format return value having wrong type should cause raising a ValidationError
    with pytest.raises(ValidationError):
        func.metadata.format_returnvalue(1)

    # passing an argument having wrong type (and not string) should cause raising a ValidationError
    with pytest.raises(ValidationError):
        func(1)


def test_docstring_validators_parsing():
    """Make sure we can parse validators from docstring"""

    @docannotate
    def func(arg1: int, arg2: str, arg3: Any, arg4: bool):
        """
        Args:
            arg1: {positive, range(1, 5)} description
            arg2: {list(['a', 'b'])} description
            arg3: {valid(None, True, 0.5)}
            arg4: descriptiom
        """

    # trigger type info parsing
    _ = func.metadata.returns_data()

    arg1_validators = func.metadata.annotated_params['arg1'].validators
    arg2_validators = func.metadata.annotated_params['arg2'].validators
    arg3_validators = func.metadata.annotated_params['arg3'].validators
    arg4_validators = func.metadata.annotated_params['arg4'].validators

    assert arg1_validators == [('validate_positive', []), ('validate_range', [1, 5])]
    assert arg2_validators == [('validate_list', [['a', 'b']])]
    assert arg3_validators == [('validate_valid', [None, True, 0.5])]
    assert arg4_validators == []


def test_docstring_validators_validation():
    """Make sure we can parse validators from docstring"""

    @docannotate
    def func(arg1: int) -> int:
        """
        Args:
            arg1: {positive, range(1, 5)} description
        """
        return arg1

    # trigger type info parsing
    _ = func.metadata.returns_data()

    assert func('1') == 1

    # check "positive" validator
    with pytest.raises(ValidationError):
        func('-1')

    # check "range" validator
    with pytest.raises(ValidationError):
        func('10')


def test_type_annotations_type_mapping():
    """Make sure we map simple builtin types to our internal type classes.

    If we have a builtin type in a function type annotations then
    we should use mapped internal type class.
    It should work for builtin types: str, int, float, bytes, bool, dict
    """

    @docannotate
    def func(arg1: str, arg2: int, arg3: float, arg4: bytes, arg5: bool, arg6: dict):
        pass

    # trigger type info parsing
    _ = func.metadata.returns_data()

    for arg_info in func.metadata.annotated_params.values():
        internal_type_class = type_system.get_proxy_for_type(arg_info.type_class)
        assert internal_type_class is not None


def test_annotations_complex_types():
    """Make sure @docannotate supports complex types in a function type annotations."""

    @docannotate
    def func_list(arg: List[int]) -> List[int]:
        return arg

    @docannotate
    def func_dict(arg: Dict[str, int]) -> Dict[str, int]:
        return arg

    # trigger type info parsing
    _ = func_list.metadata.returns_data()
    _ = func_dict.metadata.returns_data()

    # check if original function behaviour is not broken, we can pass an argument of expected type
    assert [1, 2, 3] == func_list([1, 2, 3])
    assert {"foo": 1} == func_dict({"foo": 1})

    # check conversion from string
    assert [1, 2, 3] == func_list("[1, 2, 3]")
    # assert {"foo": 1} == func_dict('{"foo": 1}')  # not supported yet by typedargs/types/map.py:map

    # check default formatting
    assert '1\n2\n3' == func_list.metadata.format_returnvalue([1, 2, 3])
    assert "foo: 1" == func_dict.metadata.format_returnvalue({"foo": 1})


