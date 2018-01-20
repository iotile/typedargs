import os.path
import typedargs.typeinfo as typeinfo
import typedargs.types as types
import pkg_resources
from typedargs.exceptions import ArgumentError
import pytest


@pytest.fixture(scope="function")
def clean_typesystem(monkeypatch):
    """Patch in a clean type system with only builtin types."""

    typesystem = typeinfo.TypeSystem(types)
    monkeypatch.setattr(typeinfo, 'type_system', typesystem)

    return typesystem


def test_external_callable(clean_typesystem):
    """Make sure we can load external types from a callable."""

    def _load_type(typesys):
        path = os.path.join(os.path.dirname(__file__), 'extra_types')
        typesys.load_external_types(path)

    with pytest.raises(ArgumentError):
        clean_typesystem.get_type('new_type')

    clean_typesystem.register_type_source(_load_type, 'Test load')
    new_type = clean_typesystem.get_type('new_type')
