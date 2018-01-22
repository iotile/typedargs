"""Decorators that allow you to annotate type information with a function or class."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import range, str  # pylint: disable=W0611
import inspect
from future.utils import iteritems
from decorator import decorate
from typedargs.exceptions import ArgumentError
from typedargs.utils import find_all, _check_and_execute, _parse_validators, context_name
from typedargs.metadata import AnnotatedMetadata
from typedargs.typeinfo import type_system  #pylint: disable=W0611; this is needed for backward compatibility


def context_from_module(module):
    """
    Given a module, create a context from all of the top level annotated
    symbols in that module.
    """

    con = find_all(module)

    if hasattr(module, "__doc__"):
        setattr(con, "__doc__", module.__doc__)

    name = module.__name__
    if hasattr(module, "_name_"):
        name = module._name_  # pylint: disable=W0212

    con = annotated(con, name)
    setattr(con, 'context', True)

    return name, con


def get_help(func):
    """Return usage information about a context or function.

    For contexts, just return the context name and its docstring
    For functions, return the function signature as well as its
    argument types.

    Args:
        func (callable): An annotated callable function

    Returns:
        str: The formatted help text
    """

    help_text = ""
    if isinstance(func, dict):
        name = context_name(func)

        help_text = "\n" + name + "\n\n"
        doc = inspect.getdoc(func)
        if doc is not None:
            doc = inspect.cleandoc(doc)
            help_text += doc + '\n'

        return help_text

    sig = func.metadata.signature()
    doc = inspect.getdoc(func)
    if doc is not None:
        doc = inspect.cleandoc(doc)

    help_text += "\n" + sig + "\n\n"
    if doc is not None:
        help_text += doc + '\n'

    if inspect.isclass(func):
        func = func.__init__

    # If we derived the parameter annotations from a docstring,
    # don't insert a custom arguments section since it already
    # exists.
    if func.metadata.load_from_doc:
        return help_text

    help_text += "\nArguments:\n"
    for key, info in iteritems(func.metadata.annotated_params):
        type_name = info.type_name
        desc = ""
        if info.desc is not None:
            desc = info.desc

        help_text += "  - %s (%s): %s\n" % (key, type_name, desc)

    return help_text

# Decorators

def param(name, type_name, *validators, **kwargs):
    """Decorate a function to give type information about its parameters.

    This function stores a type name, optional description and optional list
    of validation functions along with the decorated function it is called
    on in order to allow run time type conversions and validation.

    Args:
        type_name (string): The name of a type that will be known to the type
            system by the time this function is called for the first time.  Types
            are lazily loaded so it is not required that the type resolve correctly
            at the point in the module where this function is defined.
        validators (list(string or tuple)): A list of validators.  Each validator
            can be defined either using a string name or as an n-tuple of the form
            [name, *extra_args].  The name is used to look up a validator function
            of the form validate_name, which is called on the parameters value to
            determine if it is valid.  If extra_args are given, they are passed
            as extra arguments to the validator function, which is called as:

            validator(value, *extra_args)
        desc (string): An optional descriptioon for this parameter that must be
            passed as a keyword argument.

    Returns:
        callable: A decorated function with additional type metadata
    """

    def _param(func):
        func = annotated(func)

        valids = _parse_validators(validators)
        func.metadata.add_param(name, type_name, valids, **kwargs)

        # Only decorate the function once even if we have multiple param decorators
        if func.decorated:
            return func

        func.decorated = True
        return decorate(func, _check_and_execute)

    return _param


def returns(desc=None, printer=None, data=True):
    """Specify how the return value of this function should be handled.

    Args:
        desc (str): A deprecated description of the return value
        printer (callable): A callable function that can format this return value
        data (bool): A deprecated parameter for specifying that this function
            returns data.
    """

    if data is False:
        raise ArgumentError("Specifying non data return type in returns is no longer supported")

    def _returns(func):
        annotated(func)
        func.custom_returnvalue(printer, desc)
        return func

    return _returns


def stringable(func):
    """Specify that the return value should just be printed as a string.

    Args:
        func (callable): The function that we wish to annotate.
    """

    func = annotated(func)
    func.metadata.string_returnvalue()
    return func


def return_type(type_name, formatter=None):
    """Specify that this function returns a typed value.

    Args:
        type_name (str): A type name known to the global typedargs type system
        formatter (str): An optional name of a formatting function specified
            for the type given in type_name.
    """

    def _returns(func):
        annotated(func)
        func.metadata.typed_returnvalue(type_name, formatter)
        return func

    return _returns


def context(name=None):
    """Declare that a class defines a context.

    Contexts are for use with HierarchicalShell for discovering
    and using functionality from the command line.

    Args:
        name (str): Optional name for this context if you don't want
            to just use the class name.
    """

    def _context(cls):
        annotated(cls, name)
        cls.context = True

        return cls

    return _context


def finalizer(func):
    """
    Indicate that this function destroys the context in which it is invoked, such as a quit method
    on a subprocess or a delete method on an object.
    """

    func = annotated(func)
    func.finalizer = True
    return func


def takes_cmdline(func):
    """Annotate that a function should take the entire command line."""
    func = annotated(func)
    func.takes_cmdline = True

    return func


def docannotate(func):
    """Annotate a function using information from its docstring.

    The annotation actually happens at the time the function is first called
    to improve startup time.  For this function to work, the docstring must be
    formatted correctly.  You should use the typedargs pylint plugin to make
    sure there are no errors in the docstring.
    """

    func = annotated(func)
    func.metadata.load_from_doc = True

    if func.decorated:
        return func

    func.decorated = True
    return decorate(func, _check_and_execute)


def annotated(func, name=None):
    """Mark a function as callable from the command line.

    This function is meant to be called as decorator.  This function
    also initializes metadata about the function's arguments that is
    built up by the param decorator.

    Args:
        func (callable): The function that we wish to mark as callable
            from the command line.
        name (str): Optional string that will override the function's
            built-in name.
    """

    if hasattr(func, 'metadata'):
        return func

    func.metadata = AnnotatedMetadata(func, name)

    func.finalizer = False
    func.takes_cmdline = False
    func.decorated = False
    func.context = False

    return func


def short_description(func):
    """
    Given an object with a docstring, return the first line of the docstring
    """

    doc = inspect.getdoc(func)
    if doc is not None:
        doc = inspect.cleandoc(doc)
        lines = doc.splitlines()
        return lines[0]

    return ""
