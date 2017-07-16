# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import range, str
import inspect
from collections import namedtuple
from decorator import decorate
from typedargs.exceptions import ValidationError
from typedargs.typeinfo import type_system
from typedargs.utils import _check_and_execute


class BasicContext(dict):
    """A Basic context for holding functions in a Hierarchical Shell."""
    pass


def get_spec(func):
    if inspect.isclass(func):
        func = func.__init__

    spec = inspect.getargspec(func)

    if spec.defaults is None:
        numreq = len(spec.args)
    else:
        numreq = len(spec.args) - len(spec.defaults)

    #If the first argument is self, don't return it
    start = 0
    if numreq > 0 and spec.args[0] == 'self':
        start = 1

    reqargs = spec.args[start:numreq]
    optargs = set(spec.args[numreq:])

    return reqargs, optargs


def spec_filled(req, opt, pos, kw):
    left = [x for x in pos if x not in kw]
    left = req[len(left):]

    if len(left) == 0:
        return True

    return False


def get_signature(func):
    """
    Return the pretty signature for this function:
    foobar(type arg, type arg=val, ...)
    """

    name = func.__name__

    if inspect.isclass(func):
        func = func.__init__

    spec = inspect.getargspec(func)
    num_args = len(spec.args)

    num_def = 0
    if spec.defaults is not None:
        num_def = len(spec.defaults)

    num_no_def = num_args - num_def

    args = []
    for i in range(0, len(spec.args)):
        typestr = ""
        if i == 0 and spec.args[i] == 'self':
            continue

        if spec.args[i] in func.type_info:
            typestr = "%s " % func.type_info[spec.args[i]]

        if i >= num_no_def:
            default = str(spec.defaults[i-num_no_def])
            if len(default) == 0:
                default = "''"

            args.append("%s%s=%s" % (typestr, str(spec.args[i]), default))
        else:
            args.append(typestr + str(spec.args[i]))

    return "%s(%s)" % (name, ", ".join(args))


def print_help(func):
    """
    Print usage information about a context or function.

    For contexts, just print the context name and its docstring
    For functions, print the function signature as well as its
    argument types.
    """

    if isinstance(func, BasicContext):
        name = context_name(func)

        print("\n" + name + "\n")
        doc = inspect.getdoc(func)
        if doc is not None:
            doc = inspect.cleandoc(doc)
            print(doc)

        return

    sig = get_signature(func)
    doc = inspect.getdoc(func)
    if doc is not None:
        doc = inspect.cleandoc(doc)

    print("\n" + sig + "\n")
    if doc is not None:
        print(doc)

    if inspect.isclass(func):
        func = func.__init__

    print("\nArguments:")
    for key in func.type_info.iterkeys():
        type = func.type_info[key]
        desc = ""
        if key in func.param_descs:
            desc = func.param_descs[key]

        print(" - %s (%s): %s" % (key, type, desc))


def print_retval(func, value):
    if hasattr(func, 'typed_retval') and func.typed_retval is True:
        print(type_system.format_return_value(func, value))
        return

    if not hasattr(func, 'retval'):
        print(str(value))

    elif func.retval.printer[0] is not None:
        func.retval.printer[0](value)
    elif func.retval.desc != "":
        print("%s: %s" % (func.retval.desc, str(value)))
    else:
        print(str(value))


def find_all(container):
    if isinstance(container, dict):
        names = container.keys()
    else:
        names = dir(container)

    built_context = BasicContext()

    for name in names:
        #Ignore _ and __ names
        if name.startswith('_'):
            continue

        if isinstance(container, dict):
            obj = container[name]
        else:
            obj = getattr(container, name)

        # Check if this is an annotated object that should be included.  Check the type of
        # annotated to avoid issues with module imports where someone did from annotate import *
        # into the module causing an annotated symbol to be defined as a decorator

        # If we are in a dict context then strings point to lazily loaded modules so include them
        # too.
        if isinstance(container, dict) and isinstance(obj, str):
            built_context[name] = obj
        elif hasattr(obj, 'annotated') and isinstance(getattr(obj, 'annotated'), int):
            built_context[name] = obj

    return built_context


def context_from_module(module):
    """
    Given a module, create a context from all of the top level annotated
    symbols in that module.
    """

    con = find_all(module)

    if hasattr(module, "__doc__"):
        setattr(con, "__doc__", module.__doc__)

    if hasattr(module, "_name_"):
        name = module._name_
    else:
        name = module.__name__

    setattr(con, '_annotated_name', name)
    setattr(con, 'context', True)

    con = annotated(con)

    return name, con


def check_returns_data(func):
    if hasattr(func, 'typed_retval') and func.typed_retval is True:
        return True

    if not hasattr(func, 'retval'):
        return False

    return func.retval.data


def _parse_validators(valids):
    """Parse a list of validator names or n-tuples, checking for errors.

    Returns:
        list((func_name, [args...])): A list of validator function names and a
            potentially empty list of optional parameters for each function.
    """

    outvals = []

    for val in valids:
        if isinstance(val, str):
            args = []
        elif len(val) > 1:
            args = val[1:]
            val = val[0]
        else:
            raise ValidationError("You must pass either an n-tuple or a string to define a validator", validator=val)

        name = "validate_%s" % str(val)
        outvals.append((name, args))

    return outvals


#Decorators
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

        func.type_info[name] = type_name
        func.validator_info[name] = _parse_validators(validators)

        if 'desc' in kwargs:
            func.param_descs[name] = kwargs['desc']

        # Only decorate the function once even if we have multiple param decorators
        if func.decorated:
            return func

        func.decorated = True
        return decorate(func, _check_and_execute)

    return _param


def returns(desc=None, printer=None, data=True):
    """
    Specify how the return value of this function should be handled

    If data == True, then this function just returns data and does
    not return a context so that the context for future calls remains
    unchanged.
    """

    def _returns(func):
        annotated(func)

        func.retval = namedtuple("ReturnValue", ["desc", "printer", "data"])
        func.retval.desc = desc
        func.retval.printer = (printer,)
        func.retval.data = data

        return func

    return _returns


def stringable(func):
    """Specify that the return value for this function should just be printed as a string
    """

    func.retval = namedtuple("ReturnValue", ["desc", "printer", "data"])
    func.retval.desc = ""
    func.retval.printer = (None,)
    func.retval.data = True
    return func


def return_type(type, formatter=None):
    """
    Specify that this function returns a typed value

    type must be a type known to the MoMo type system and formatter
    must be a valid formatter for that type
    """

    def _returns(func):
        annotated(func)
        func.typed_retval = True
        func.retval_type = type_system.get_type(type)
        func.retval_typename = type
        func.retval_formatter = formatter

        return func

    return _returns


def context(name=None):
    """
    Declare that a class defines a MoMo context for use with the momo function for discovering
    and using functionality.
    """

    def _context(cls):
        annotated(cls)
        cls.context = True

        if name is not None:
            cls._annotated_name = name
        else:
            cls._annotated_name = cls.__name__

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


def context_name(context):
    """
    Given a context, return its proper name
    """

    if hasattr(context, "_annotated_name"):
        return context._annotated_name
    elif inspect.isclass(context):
        return context.__class__.__name__

    return str(context)


def takes_cmdline(func):
    func = annotated(func)
    func.takes_cmdline = True

    return func


def annotated(func):
    """Mark a function as callable from the command line.

    This function is meant to be called as decorator.  This function
    also initializes metadata about the function's arguments that is
    built up by the param decorator.

    Args:
        func (callable): The function that we wish to mark as callable
            from the command line.
    """

    if hasattr(func, 'annotated'):
        return func

    func.validator_info = {}
    func.type_info = {}
    func.param_descs = {}

    func.annotated = True
    func.finalizer = False
    func.takes_cmdline = False
    func.decorated = False

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
