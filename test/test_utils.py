import sys
from typing import List, Dict
from typedargs import utils


def test_get_typing_type_name():
    """Make sure we can get a correct type name of a type from typing module.

    We need to support at least List and Dict types.
    """
    assert 'List' == utils.get_typing_type_name(List)
    assert 'List' == utils.get_typing_type_name(List[int])
    assert 'Dict' == utils.get_typing_type_name(Dict)
    assert 'Dict' == utils.get_typing_type_name(Dict[str, int])


def test_get_typing_type_args():
    """Make sure we can get a correct type arguments of a type from typing module.

    We need to support at least List and Dict types.
    """
    assert () == utils.get_typing_type_args(List)
    assert (int, ) == utils.get_typing_type_args(List[int])
    assert () == utils.get_typing_type_args(Dict)
    assert (str, int) == utils.get_typing_type_args(Dict[str, int])

