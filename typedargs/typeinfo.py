"""Define the global type system that allows adding strong type information to python objects."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

#typeinfo.py
#Basic routines for converting information from string or other binary
#formats to python types and for displaying those types in supported
#formats

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import str

import os.path
import imp
import sys
from typedargs.exceptions import ValidationError, ArgumentError, KeyValueException
import typedargs.types as types


class TypeSystem(object):
    """
    TypeSystem permits the inspection of defined types and supports
    converted string and binary values to and from these types.
    """

    def __init__(self, *args):
        """
        Create a TypeSystem by importing all of the types defined in modules passed
        as arguments to this function.  Each module is imported using
        """

        self.interactive = False
        self.known_types = {}
        self.type_factories = {}

        for arg in args:
            self.load_type_module(arg)

        self._lazy_type_sources = []
        self.failed_sources = []

    def register_type_source(self, source, name=None):
        """Register an external source of types.

        This function does not actually load any external types, it just
        keeps track of the source, which must either be a str that is
        interpreted as a python entry_point group or a callable that
        will be passed an instance of this type system.

        External type sources will only be loaded in an as needed basis when
        a type is encountered (and needed) that is not currently known.  At
        that point external type sources will be considered until the type
        in question is found.

        If an external type source fails to load for some reason, it is logged
        but the error is not fatal.

        Args:
            source (str or callable): Either a pkg_resources entry_point
                group that will be searched for external types or a callable
                function that will be called as source(self) where self
                refers to this TypeSystem object.
            name (str): Optional short name to use for reporting errors having
                to do with this source of types.  This is most useful to pass
                when source is a callable.
        """

        self._lazy_type_sources.append((source, name))

    def convert_to_type(self, value, typename, **kwargs):
        """
        Convert value to type 'typename'

        If the conversion routine takes various kwargs to
        modify the conversion process, **kwargs is passed
        through to the underlying conversion function
        """
        try:
            if isinstance(value, bytearray):
                return self.convert_from_binary(value, typename, **kwargs)

            typeobj = self.get_type(typename)

            conv = typeobj.convert(value, **kwargs)
            return conv
        except (ValueError, TypeError) as exc:
            raise ValidationError("Could not convert value", type=typename, value=value, error_message=str(exc))

    def convert_from_binary(self, binvalue, type, **kwargs):
        """
        Convert binary data to type 'type'.

        'type' must have a convert_binary function.  If 'type'
        supports size checking, the size function is called to ensure
        that binvalue is the correct size for deserialization
        """

        size = self.get_type_size(type)
        if size > 0 and len(binvalue) != size:
            raise ArgumentError("Could not convert type from binary since the data was not the correct size", required_size=size, actual_size=len(binvalue), type=type)

        typeobj = self.get_type(type)

        if not hasattr(typeobj, 'convert_binary'):
            raise ArgumentError("Type does not support conversion from binary", type=type)

        return typeobj.convert_binary(binvalue, **kwargs)

    def get_type_size(self, type):
        """
        Get the size of this type for converting a hex string to the
        type. Return 0 if the size is not known.
        """

        typeobj = self.get_type(type)

        if hasattr(typeobj, 'size'):
            return typeobj.size()

        return 0

    def format_value(self, value, type, format=None, **kwargs):
        """
        Convert value to type and format it as a string

        type must be a known type in the type system and format,
        if given, must specify a valid formatting option for the
        specified type.
        """

        typed_val = self.convert_to_type(value, type, **kwargs)
        typeobj = self.get_type(type)

        #Allow types to specify default formatting functions as 'default_formatter'
        #otherwise if not format is specified, just convert the value to a string
        if format is None:
            if hasattr(typeobj, 'default_formatter'):
                format_func = getattr(typeobj, 'default_formatter')
                return format_func(typed_val, **kwargs)

            return str(typed_val)

        formatter = "format_%s" % str(format)
        if not hasattr(typeobj, formatter):
            raise ArgumentError("Unknown format for type", type=type, format=format, formatter_function=formatter)

        format_func = getattr(typeobj, formatter)
        return format_func(typed_val, **kwargs)

    @classmethod
    def _validate_type(cls, typeobj):
        """
        Validate that all required type methods are implemented.

        At minimum a type must have:
        - a convert() or convert_binary() function
        - a default_formatter() function

        Raises an ArgumentError if the type is not valid
        """

        if not (hasattr(typeobj, "convert") or hasattr(typeobj, "convert_binary")):
            raise ArgumentError("type is invalid, does not have convert or convert_binary function", type=typeobj, methods=dir(typeobj))

        if not hasattr(typeobj, "default_formatter"):
            raise ArgumentError("type is invalid, does not have default_formatter function", type=typeobj, methods=dir(typeobj))

    def is_known_type(self, type_name):
        """Check if type is known to the type system.

        Returns:
            bool: True if the type is a known instantiated simple type, False otherwise
        """

        type_name = str(type_name)
        if type_name in self.known_types:
            return True

        return False

    def split_type(self, typename):
        """
        Given a potentially complex type, split it into its base type and specializers
        """

        name = self._canonicalize_type(typename)
        if '(' not in name:
            return name, False, []

        base, sub = name.split('(')
        if len(sub) == 0 or sub[-1] != ')':
            raise ArgumentError("syntax error in complex type, no matching ) found", passed_type=typename, basetype=base, subtype_string=sub)

        sub = sub[:-1]

        subs = sub.split(',')
        return base, True, subs

    def instantiate_type(self, typename, base, subtypes):
        """Instantiate a complex type."""

        if base not in self.type_factories:
            raise ArgumentError("unknown complex base type specified", passed_type=typename, base_type=base)

        base_type = self.type_factories[base]

        #Make sure all of the subtypes are valid
        for sub_type in subtypes:
            try:
                self.get_type(sub_type)
            except KeyValueException as exc:
                raise ArgumentError("could not instantiate subtype for complex type", passed_type=typename, sub_type=sub_type, error=exc)

        typeobj = base_type.Build(*subtypes, type_system=self)
        self.inject_type(typename, typeobj)

    @classmethod
    def _canonicalize_type(cls, typename):
        return typename.replace(' ', '')

    @classmethod
    def _is_factory(cls, typeobj):
        """
        Determine if typeobj is a factory for producing complex types
        """

        if hasattr(typeobj, 'Build'):
            return True

        return False

    def get_type(self, type_name):
        """Return the type object corresponding to a type name.

        If type_name is not found, this triggers the loading of
        external types until a matching type is found or until there
        are no more external type sources.
        """

        type_name = self._canonicalize_type(type_name)

        # Add basic transformations on common abbreviations
        if str(type_name) == 'int':
            type_name = 'integer'
        elif str(type_name) == 'str':
            type_name = 'string'

        if self.is_known_type(type_name):
            return self.known_types[type_name]

        base_type, is_complex, subtypes = self.split_type(type_name)
        if is_complex and base_type in self.type_factories:
            self.instantiate_type(type_name, base_type, subtypes)
            return self.known_types[type_name]

        # If we're here, this is a type that we don't know anything about, so go find it.
        i = 0
        for i, (source, name) in enumerate(self._lazy_type_sources):
            if isinstance(source, str):
                import pkg_resources
                import traceback

                for entry in pkg_resources.iter_entry_points(source):
                    try:
                        mod = entry.load()
                        type_system.load_type_module(mod)
                    except:  #pylint:disable=W0702; We want to catch everything here since we don't want external plugins breaking us
                        fail_info = ("Entry point group: %s, name: %s" % (source, entry.name), sys.exc_info)
                        traceback.print_exc()
                        self.failed_sources.append(fail_info)
            else:
                try:
                    source(self)
                except:  #pylint:disable=W0702; We want to catch everything here since we don't want external plugins breaking us
                    fail_info = ("source: %s" % name, sys.exc_info)
                    self.failed_sources.append(fail_info)

            # Only load as many external sources as we need to resolve this type_name
            if self.is_known_type(type_name) or (is_complex and base_type in self.type_factories):
                break

        self._lazy_type_sources = self._lazy_type_sources[i:]

        # If we've loaded everything and we still can't find it then there's a configuration error somewhere
        if not (self.is_known_type(type_name) or (is_complex and base_type in self.type_factories)):
            raise ArgumentError("get_type called on unknown type", type=type_name, failed_external_sources=[x[0] for x in self.failed_sources])

        return self.get_type(type_name)

    def is_known_format(self, type, format):
        """
        Check if format is known for given type.

        Returns boolean indicating if format is valid for the specified type.
        """

        typeobj = self.get_type(type)

        formatter = "format_%s" % str(format)
        if not hasattr(typeobj, formatter):
            return False

        return True

    def inject_type(self, name, typeobj):
        """
        Given a module-like object that defines a type, add it to our type system so that
        it can be used with the iotile tool and with other annotated API functions.
        """

        name = self._canonicalize_type(name)
        _, is_complex, _ = self.split_type(name)

        if self.is_known_type(name):
            raise ArgumentError("attempting to inject a type that is already defined", type=name)

        if (not is_complex) and self._is_factory(typeobj):
            if name in self.type_factories:
                raise ArgumentError("attempted to inject a complex type factory that is already defined", type=name)
            self.type_factories[name] = typeobj
        else:
            self._validate_type(typeobj)
            self.known_types[name] = typeobj

        if not hasattr(typeobj, "default_formatter"):
            raise ArgumentError("type is invalid, does not have default_formatter function", type=typeobj, methods=dir(typeobj))

    def load_type_module(self, module):
        """
        Given a module that contains a list of some types find all symbols in the module that
        do not start with _ and attempt to import them as types.
        """

        for name in (x for x in dir(module) if not x.startswith('_')):
            typeobj = getattr(module, name)

            try:
                self.inject_type(name, typeobj)
            except ArgumentError:
                pass

    def load_external_types(self, path):
        """
        Given a path to a python package or module, load that module, search for all defined variables
        inside of it that do not start with _ or __ and inject them into the type system.  If any of the
        types cannot be injected, silently ignore them unless verbose is True.  If path points to a module
        it should not contain the trailing .py since this is added automatically by the python import system
        """

        folder, filename = os.path.split(path)

        try:
            fileobj, pathname, description = imp.find_module(filename, [folder])
            mod = imp.load_module(filename, fileobj, pathname, description)
        except ImportError as exc:
            raise ArgumentError("could not import module in order to load external types", module_path=path, parent_directory=folder, module_name=filename, error=str(exc))

        self.load_type_module(mod)


def iprint(stringable):
    """
    A simple function to only print text if in an interactive session.
    """

    if type_system.interactive:
        print(stringable)


#In order to support function annotations that must be resolved to types when modules
#are imported, create a default TypeSystem object that is used globally to store type
#information

type_system = TypeSystem(types)  # pylint: disable=invalid-name
