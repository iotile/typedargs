"""Utility functons that are only used internally inside typedargs."""

from builtins import str
from past.builtins import basestring
from .exceptions import ValidationError
from .metadata import AnnotatedMetadata


class BasicContext(dict):
    """A Basic context for holding functions in a Hierarchical Shell."""
    pass


def _check_and_execute(func, *args, **kwargs):
    """
    Check the type of all parameters with type information, converting
    as appropriate and then execute the function.
    """

    convargs = []

    #Convert and validate all arguments
    for i, arg in enumerate(args):
        val = func.metadata.convert_positional_argument(i, arg)
        convargs.append(val)

    convkw = {}
    for key, val in kwargs:
        convkw[key] = func.metadata.convert_argument(key, val)

    if not func.metadata.spec_filled(convargs, convkw):
        raise ValidationError("Not enough parameters specified to call function", function=func.metadata.name, signature=func.metadata.signature())

    retval = func(*convargs, **convkw)
    return retval


def _parse_validators(valids):
    """Parse a list of validator names or n-tuples, checking for errors.

    Returns:
        list((func_name, [args...])): A list of validator function names and a
            potentially empty list of optional parameters for each function.
    """

    outvals = []

    for val in valids:
        if isinstance(val, basestring):
            args = []
        elif len(val) > 1:
            args = val[1:]
            val = val[0]
        else:
            raise ValidationError("You must pass either an n-tuple or a string to define a validator", validator=val)

        name = "validate_%s" % str(val)
        outvals.append((name, args))

    return outvals


def context_name(con):
    """Given a context, return its proper name as a string."""

    if hasattr(con, 'metadata'):
        return con.metadata.name

    return str(con)


def find_all(container):
    """Find all annotated function inside of a container.

    Annotated functions are identified as those that:
    - do not start with a _ character
    - are either annotated with metadata
    - or strings that point to lazily loaded modules

    Args:
        container (object): The container to search for annotated functions.

    Returns:
        dict: A dict with all of the found functions in it.
    """

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
        elif hasattr(obj, 'metadata') and isinstance(getattr(obj, 'metadata'), AnnotatedMetadata):
            built_context[name] = obj

    return built_context
