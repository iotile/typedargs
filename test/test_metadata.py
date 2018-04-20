"""Tests of metadata extraction functionality."""

import pytest
from typedargs.metadata import AnnotatedMetadata
from typedargs.exceptions import ValidationError, ArgumentError


@pytest.fixture
def func1():
    def _inside_func1(group, stream, domain=False, x=True):
        pass

    return AnnotatedMetadata(_inside_func1)

def test_spec_check(func1):
    """Make sure we can check if a spec is filled."""

    assert func1.check_spec([1, 2, 3, 4]) == {
        'group': 1,
        'stream': 2,
        'domain': 3,
        'x': 4
    }

    with pytest.raises(ValidationError):
        func1.check_spec([1, 2], dict(group=3))

    with pytest.raises(ArgumentError):
        func1.check_spec([1])
