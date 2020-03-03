"""Define the global type system that allows adding strong type information to python objects."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# typeinfo.py
# Basic routines for converting information from string or other binary
# formats to python types and for displaying those types in supported
# formats
import inspect
import os.path
import importlib
import logging
import sys
import typing

from typedargs.exceptions import ValidationError, ArgumentError, KeyValueException
from typedargs import types, utils


class TypeSystem:
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
        self._mapped_builtin_types = {}
        self._mapped_complex_types = {}
        self._complex_type_proxies = {}
        self.logger = logging.getLogger(__name__)

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

    def _get_type_and_proxy(self, type_or_name):
        """
        Normally, we expect that the type objects contain a certain set of methods
        to support validation, conversion and formatting.  However, for certain
        internal types like int, dict, etc, typing.List[t], typing.Dict[t, t] we provide a separate augmentation
        class that contains the converters.
        """
        if isinstance(type_or_name, str):
            type_obj = None
            proxy_obj = self.get_proxy_for_type(type_or_name)
        elif utils.is_class_from_typing(type_or_name):
            type_obj = type_or_name
            proxy_obj = self.get_proxy_for_type(type_obj)
        elif inspect.isclass(type_or_name):
            type_obj = type_or_name

            if self.is_known_type(type_or_name):
                proxy_obj = self.get_proxy_for_type(type_or_name)
            else:
                proxy_obj = None
        else:
            raise ValidationError("Unknown object passed to convert_to_type", type_or_name=type_or_name)

        return type_obj, proxy_obj

    def convert_to_type(self, value, type_or_name, **kwargs):
        """
        Convert value to type 'type_or_name'

        If the conversion routine takes various kwargs to
        modify the conversion process, \\**kwargs is passed
        through to the underlying conversion function
        """
        type_obj, proxy_obj = self._get_type_and_proxy(type_or_name)

        # Legacy types supported conversion from binary
        # so make sure that remains functional.  This behavior is deprecated so
        # it is only used if the type name is passed in via a string.
        if isinstance(type_or_name, str) and isinstance(value, bytearray):
            return self.convert_from_binary(value, type_or_name, **kwargs)

        if type_obj is not None and not utils.is_class_from_typing(type_obj):
            # When we have a proper modern type class that supports isinstance()
            # checks, we can just verify if we actually need to do anything
            if value is None or isinstance(value, type_obj):
                return value

            # If the value is not already the right type, we only support converting
            # from string.
            if not isinstance(value, str):
                raise ValidationError("Value was not the right type and was not a string",
                                      expected_type=type_obj, value=value)

            return self._try_convert_from_string(value, type_obj, proxy_obj)

        # This is the legacy case, we have no type object, so we rely on the
        # legacy behavior that the proxy object has a `convert` function that
        # implicitly checks if the value is already converted and just returns
        # it.

        try:
            return proxy_obj.convert(value, **kwargs)
        except (ValueError, TypeError) as exc:
            raise ValidationError("Could not convert value", type=type_or_name, value=value,
                                  error_message=str(exc))

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

        typeobj = self.get_proxy_for_type(type)

        if not hasattr(typeobj, 'convert_binary'):
            raise ArgumentError("Type does not support conversion from binary", type=type)

        return typeobj.convert_binary(binvalue, **kwargs)

    def get_type_size(self, type):
        """
        Get the size of this type for converting a hex string to the
        type. Return 0 if the size is not known.
        """

        typeobj = self.get_proxy_for_type(type)

        if hasattr(typeobj, 'size'):
            return typeobj.size()

        return 0

    def format_value(self, value, type_or_name, formatter=None, sub_formatters=None, **kwargs):
        """
        Convert value to type specified by type_or_name and format it as a string.

        type_or_name must be a known type in the type system or a type class.
        And format, if given, must specify a valid formatting option for the specified type.
        """

        typed_val = self.convert_to_type(value, type_or_name, **kwargs)

        typeobj = self.get_proxy_for_type(type_or_name)
        if typeobj is None:
            typeobj = type_or_name

        # Allow types to specify default formatting functions as 'default_formatter'
        # otherwise if no format is specified, just convert the value to a string
        if formatter in (None, 'default', 'str', 'string'):
            if hasattr(typeobj, 'default_formatter'):
                format_func = getattr(typeobj, 'default_formatter')
                return format_func(typed_val, **kwargs)

            return str(typed_val)

        format_func = "format_%s" % str(formatter)
        format_func = getattr(typeobj, format_func, None)

        if not callable(format_func):
            raise ArgumentError("Unknown format for type", type=type_or_name, formatter=formatter, formatter_function=format_func)

        sub_formatters = sub_formatters if sub_formatters else []
        return format_func(typed_val, *sub_formatters, **kwargs)

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

    def _is_known_type_factory(self, class_or_name):
        if class_or_name in self.type_factories or class_or_name in self._mapped_complex_types:
            return True
        return False

    def is_known_type(self, type_or_name):
        """Check if type is known to the type system.

        Returns:
            bool: True if the type is a known instantiated simple type, False otherwise
        """
        if type_or_name in self.known_types or type_or_name in self._mapped_builtin_types or type_or_name in self._complex_type_proxies:
            return True
        return False

    def split_type(self, type_or_name):
        """
        Given a potentially complex type, split it into its base type and specializers
        """
        if isinstance(type_or_name, str):
            name = self._canonicalize_type(type_or_name)
            if '(' not in name:
                return name, False, []

            base, sub = name.split('(')
            if len(sub) == 0 or sub[-1] != ')':
                raise ArgumentError("syntax error in complex type, no matching ) found", passed_type=type_or_name, basetype=base, subtype_string=sub)

            sub = sub[:-1]

            subs = sub.split(',')
            return base, True, subs
        elif utils.is_class_from_typing(type_or_name):
            base = getattr(typing, utils.get_typing_type_name(type_or_name))
            subs = utils.get_typing_type_args(type_or_name)
            return base, bool(subs), subs
        else:
            raise ArgumentError('Cannot split the given type.', type_or_name=type_or_name)

    def instantiate_type(self, type_or_name, base, subtypes):
        """Instantiate a complex type."""

        if isinstance(type_or_name, str):
            type_or_name = self._canonicalize_type(type_or_name)

        if not self._is_known_type_factory(base):
            raise ArgumentError("unknown complex base type specified", passed_type=type_or_name, base_type=base)

        base_type = self._get_known_type_factory(base)

        # Make sure all of the subtypes are valid
        for sub_type in subtypes:
            try:
                self.get_proxy_for_type(sub_type)
            except KeyValueException as exc:
                raise ArgumentError("could not instantiate subtype for complex type", passed_type=type_or_name, sub_type=sub_type, error=exc)

        typeobj = base_type.Build(*subtypes, type_system=self)
        self.inject_type(type_or_name, typeobj)

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

    def _get_known_type_factory(self, type_or_name):
        if type_or_name in self.type_factories:
            return self.type_factories[type_or_name]
        if type_or_name in self._mapped_complex_types:
            return self._mapped_complex_types[type_or_name]
        raise ArgumentError('Type factory not found.', type_or_name=type_or_name)

    def _get_proxy_for_known_type(self, type_or_name):
        """
        Returns:
            type proxy object or None
        """
        if type_or_name in self.known_types:
            return self.known_types[type_or_name]
        if type_or_name in self._mapped_builtin_types:
            return self._mapped_builtin_types[type_or_name]
        if type_or_name in self._complex_type_proxies:
            return self._complex_type_proxies[type_or_name]
        raise ArgumentError('Proxy object not found.', type_or_name=type_or_name)

    def get_proxy_for_type(self, type_or_name):
        """Return the type object corresponding to a given type_or_name.

        type_or_name could be:
        - a simple builtin type like str, int, etc
        - a string name of a known type
        - a string name of an unknown complex type where base type is a known type factory
        - a complex type class from typing module: Dict[T, T] or List[T]
        - a string name of an unknown type (maybe a complex where base type is unknown type factory)
        If type_or_name does not fit these criteria then None would be returned.

        If type_or_name is a string type name and it is not found in known types, this triggers the loading of
        external types until a matching type is found or until there
        are no more external type sources.
        """
        if not isinstance(type_or_name, str) and not self.is_known_type(type_or_name) and not utils.is_class_from_typing(type_or_name):
            return None

        if isinstance(type_or_name, str):
            type_or_name = self._canonicalize_type(type_or_name)

        # If type_or_name is a:
        # - a simple builtin type like str, int, etc
        # - a string name of a known type
        if self.is_known_type(type_or_name):
            return self._get_proxy_for_known_type(type_or_name)

        # here type_or_name could be a string name or a complex type class from typing module
        base_type, is_complex, subtypes = self.split_type(type_or_name)

        # If type_or_name is a:
        # - a string name of an unknown complex type where base type is a known type factory
        # - a complex type class from typing module: Dict[T, T] or List[T]
        if is_complex and self._is_known_type_factory(base_type):
            self.instantiate_type(type_or_name, base_type, subtypes)
            return self.get_proxy_for_type(type_or_name)

        # If type_or_name is a:
        # - a string name of an unknown type (maybe a complex where base type is unknown type factory)

        # If we're here, this is a string type name that we don't know anything about, so go find it.
        self._load_registered_type_sources(type_or_name)

        # If we've loaded everything and we still can't find it then there's a configuration error somewhere
        if not (self.is_known_type(type_or_name) or (is_complex and base_type in self.type_factories)):
            raise ArgumentError("get_proxy_for_type called on unknown type", type=type_or_name, failed_external_sources=[x[0] for x in self.failed_sources])

        return self.get_proxy_for_type(type_or_name)

    def _load_registered_type_sources(self, type_name):
        base_type, is_complex, subtypes = self.split_type(type_name)

        i = 0
        for i, (source, name) in enumerate(self._lazy_type_sources):
            if isinstance(source, str):
                import pkg_resources

                for entry in pkg_resources.iter_entry_points(source):
                    try:
                        mod = entry.load()
                        type_system.load_type_module(mod)
                    except:  #pylint:disable=W0702; We want to catch everything here since we don't want external plugins breaking us
                        fail_info = ("Entry point group: %s, name: %s" % (source, entry.name), sys.exc_info)
                        logging.exception("Error loading external type source from entry point, group: %s, name: %s", source, entry.name)
                        self.failed_sources.append(fail_info)
            else:
                try:
                    source(self)
                except:  #pylint:disable=W0702; We want to catch everything here since we don't want external plugins breaking us
                    fail_info = ("source: %s" % name, sys.exc_info)
                    logging.exception("Error loading external type source, source: %s", source)
                    self.failed_sources.append(fail_info)

            # Only load as many external sources as we need to resolve this type_name
            if self.is_known_type(type_name) or (is_complex and base_type in self.type_factories):
                break

        self._lazy_type_sources = self._lazy_type_sources[i:]

    def is_known_format(self, type, format):
        """
        Check if format is known for given type.

        Returns boolean indicating if format is valid for the specified type.
        """

        typeobj = self.get_proxy_for_type(type)

        formatter = "format_%s" % str(format)
        if not hasattr(typeobj, formatter):
            return False

        return True

    def inject_type(self, type_or_name, typeobj):
        """
        Given a module-like object that defines a type, add it to our type system so that
        it can be used with the iotile tool and with other annotated API functions.

        type_or_name could be a string name or a type from typing module
        """
        # if type_or_name is a type from typing module
        if not isinstance(type_or_name, str):
            if type_or_name in self._complex_type_proxies:
                raise ArgumentError("attempting to inject a type that is already defined", type=type_or_name)
            self._complex_type_proxies[type_or_name] = typeobj
            return

        name = self._canonicalize_type(type_or_name)
        _, is_complex, _ = self.split_type(name)

        if self.is_known_type(name):
            raise ArgumentError("attempting to inject a type that is already defined", type=name)

        if (not is_complex) and self._is_factory(typeobj):
            if name in self.type_factories:
                raise ArgumentError("attempted to inject a complex type factory that is already defined", type=name)
            self.type_factories[name] = typeobj

            mapped_complex_type = getattr(typeobj, 'MAPPED_COMPLEX_TYPE', None)
            if mapped_complex_type:
                self._mapped_complex_types[mapped_complex_type] = typeobj

        elif inspect.isclass(typeobj):
            self.known_types[name] = typeobj
        else:
            self._validate_type(typeobj)

            actual_type = getattr(typeobj, 'MAPPED_BUILTIN_TYPE', None)
            if actual_type is not None:
                self._mapped_builtin_types[actual_type] = typeobj

            for alias in getattr(typeobj, 'MAPPED_TYPE_NAMES', []):
                self.known_types[alias] = typeobj

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
            mod = importlib.import_module(filename, folder)
        except ImportError as exc:
            raise ArgumentError("could not import module in order to load external types", module_path=path, parent_directory=folder, module_name=filename, error=str(exc))

        self.load_type_module(mod)

    def _try_convert_from_string(self, value: str, type_obj, proxy_obj):
        """Attempt to convert a string value to a given type.

        Returns:
            instance of type_obj
        """

        # If there is a proxy object that should be used instead of the actual type
        # then use that.  Otherwise, we expect the type itself to have a FromString
        # method.
        converting_obj = proxy_obj
        if converting_obj is None:
            converting_obj = type_obj

        if inspect.isclass(converting_obj) and type_obj not in self._complex_type_proxies:
            return converting_obj.FromString(value)

        if not hasattr(converting_obj, 'convert'):
            raise ValidationError("Type did not have a convert function for string conversion",
                                  type_obj=type_obj, augmented_type=proxy_obj)

        try:
            converted_value = converting_obj.convert(value)
        except (ValueError, TypeError) as err:
            raise ValidationError("Error converting value from string", message=str(err),
                                  value=value)

        if type_obj is not None and not isinstance(converted_value, type_obj):
            raise ValidationError("Conversion from string did not produce the expected type",
                                  string_value=value, converted_value=repr(converted_value),
                                  expected_type=repr(type_obj))

        return converted_value


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
