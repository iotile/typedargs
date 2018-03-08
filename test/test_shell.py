"""Tests for hierarchical shell."""

# pylint: disable=unused-argument,redefined-outer-name

import pytest
from typedargs import param, return_type, context, annotated, stringable
from typedargs.shell import HierarchicalShell
from typedargs.exceptions import ValidationError


@param("arg1", "integer")
@param("force", "bool")
@param("arg2", "string")
@return_type("string")
def func(arg1, force=False, arg2="hello"):
    """Demo function."""
    return (arg1, force, arg2)


@annotated
def func2():
    """Demo function 2."""
    return DemoClass(1)


@context("Test")
class DemoClass(object):
    """Hello."""

    @param("arg1", "integer", "nonnegative", desc="Test description")
    def __init__(self, arg1):
        self.value = arg1

    @return_type("integer", "hex")
    def get_arg(self):
        """Get arg."""
        return self.value

    @stringable
    def return_one(self):  # pylint: disable=R0201
        """Return 1."""
        return 1


@pytest.fixture
def shell():
    """Create a new hierarchical shell."""

    hshell = HierarchicalShell('Test Shell')
    hshell.root_add('func', func)
    hshell.root_add('func2', func2)
    hshell.root_add('demo', DemoClass)

    return hshell


def test_shortarg(shell):
    """Make sure we can specify short kw argument names."""

    val, remainder, finished = shell.invoke_one(u'func 1 -f -a back'.split(' '))
    assert val == "(1, True, 'back')"
    assert len(remainder) == 0
    assert finished is True

    val, remainder, finished = shell.invoke_one(u'func 1 -f false -a back'.split(' '))
    assert val == "(1, False, 'back')"
    assert len(remainder) == 0
    assert finished is True

    val, remainder, finished = shell.invoke_one(u'func2 get_arg'.split(' '))
    assert val is None
    assert len(remainder) == 1
    assert finished is False


def test_context_retval(shell):
    """Make sure functions that return a context work."""

    val, remainder, finished = shell.invoke_one(u'func2'.split(' '))
    assert val is None
    assert len(remainder) == 0
    assert finished is False
    assert len(shell.contexts) == 2
    assert isinstance(shell.contexts[-1], DemoClass)
    assert shell.contexts[-1].value == 1


def test_class_creation(shell):
    """Make sure we can create a class with parameters."""

    shell.invoke_one(u'demo 1'.split(' '))
    assert len(shell.contexts) == 2
    assert shell.contexts[-1].value == 1


def test_class_create_error(shell):
    """Make sure we throw an exception if there are not enough class params."""

    with pytest.raises(ValidationError):
        shell.invoke_one(u'demo'.split(' '))

    # Make sure type checking happens on class constructors
    with pytest.raises(ValidationError):
        shell.invoke_one(u'demo hello'.split(' '))


def test_builtin_help(shell):
    """Make sure the builtins work."""

    val, remained, finished = shell.invoke_one(u'help'.split(' '))
    assert val == """
root
A basic context for holding the root callable functions for a shell.

Defined Functions:
 - demo(integer arg1)
   Hello.
 - func(integer arg1, bool force=False, string arg2=hello)
   Demo function.
 - func2()
   Demo function 2.

Builtin Functions
 - back
 - help
 - quit

"""
    assert remained == []
    assert finished is True

    val, remained, finished = shell.invoke_one(u'help demo'.split(' '))
    assert val == """
Test(integer arg1)

Hello.

Arguments:
  - arg1 (integer): Test description
"""
    assert finished is True
    assert remained == []


def test_builtin_back(shell):
    shell.invoke_one(u'demo 1'.split(' '))
    assert len(shell.contexts) == 2

    val, remained, finished = shell.invoke_one('back'.split(' '))
    assert val is None
    assert remained == []
    assert finished is True
    assert len(shell.contexts) == 1


def test_invoke_string(shell):
    finished = shell.invoke_string(u'demo 1 back')
    assert finished is True

    finished = shell.invoke_string('demo 1 back')
    assert finished is True

    finished = shell.invoke_string(u'func2')
    assert finished is False


def test_valid_identifiers(shell):
    """Regression test failed dict key addition on python 3."""

    idents = shell.valid_identifiers()
    assert sorted(idents) == sorted(['func', 'func2', 'demo', 'back', 'help', 'quit'])

def test_negative_numbers(shell):
    """Make sure we correctly handle negative numbers not as flags."""

    with pytest.raises(ValidationError):
        shell.invoke_string('demo -15')


def test_equals_in_flag(shell):
    """Make sure --flags=string=value works with the flag value being 'string=value'."""

    finished = shell.invoke_string("func 1 --arg2=name=value --")
    assert finished is True
