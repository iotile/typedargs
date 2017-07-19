"""Tests to ensure that we can inject external types at runtime."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,redefined-outer-name

import os.path
import pytest
import typedargs.typeinfo as typeinfo
import typedargs.types as types
from typedargs import param
from typedargs.exceptions import ArgumentError


@pytest.fixture(scope="function")
def clean_typesystem(monkeypatch):
    """Patch in a clean type system with only builtin types."""

    typesystem = typeinfo.TypeSystem(types)
    monkeypatch.setattr(typeinfo, 'type_system', typesystem)


def test_type_injection(clean_typesystem):
    """Make sure we can inject external types."""
    import extra_type_package.extra_type as typeobj

    assert not typeinfo.type_system.is_known_type("test_injected_type1")

    typeinfo.type_system.inject_type("test_injected_type1", typeobj)
    assert typeinfo.type_system.is_known_type("test_injected_type1")


def test_external_module_injection(clean_typesystem):
    """Test type injection from an external python module."""

    path = os.path.join(os.path.dirname(__file__), 'extra_types')

    assert not typeinfo.type_system.is_known_type('new_type')
    typeinfo.type_system.load_external_types(path)
    assert typeinfo.type_system.is_known_type('new_type')


def test_external_package_injection(clean_typesystem):
    """Test type injection from an external python package."""

    path = os.path.join(os.path.dirname(__file__), 'extra_type_package')

    assert not typeinfo.type_system.is_known_type('new_pkg_type')
    typeinfo.type_system.load_external_types(path)
    assert typeinfo.type_system.is_known_type('new_pkg_type')


def test_external_package_failure(clean_typesystem):
    """Test type injection raises error from nonexistant path."""

    with pytest.raises(ArgumentError):
        path = os.path.join(os.path.dirname(__file__), 'extra_type_package_nonexistant')
        typeinfo.type_system.load_external_types(path)


def test_lazy_type_loading(clean_typesystem):
    """Make sure type information is loaded lazily."""

    @param("param1", "new_type")
    def inner_function(param1):  # pylint: disable=C0111
        assert isinstance(param1, int)

    with pytest.raises(ArgumentError):
        inner_function('1')

    path = os.path.join(os.path.dirname(__file__), 'extra_types')
    typeinfo.type_system.load_external_types(path)

    inner_function('1')
