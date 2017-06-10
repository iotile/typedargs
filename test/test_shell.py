import pytest
from typedargs import param, return_type
from typedargs.shell import HierarchicalShell


@param("arg1", "integer")
@param("force", "bool")
@param("arg2", "string")
@return_type("string")
def func(arg1, force=False, arg2="hello"):
    return (arg1, force, arg2)


@pytest.fixture
def shell():
    hshell = HierarchicalShell('Test Shell')
    hshell.root_add('func', func)

    return hshell


def test_shortarg(shell):
    """Make sure we can specify short kw argument names."""

    shell.invoke(u'func 1 -f -a back'.split(' '))
