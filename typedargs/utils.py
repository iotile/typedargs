"""Utility functons that are only used internally inside typedargs."""

import inspect
from .typeinfo import type_system
from .exceptions import ValidationError


def _check_and_execute(func, *args, **kwargs):
    """
    Check the type of all parameters with type information, converting
    as appropriate and then execute the function.
    """

    convargs = []
    spec = inspect.getargspec(func)

    #Convert and validate all arguments
    for i in range(0, len(args)):
        arg_name = spec.args[i]
        val = _process_arg(func, arg_name, args[i])
        convargs.append(val)

    convkw = {}
    for key, val in kwargs:
        convkw[key] = _process_arg(func, key, val)

    retval = func(*convargs, **convkw)
    return retval


def _process_arg(func, arg, value):
    """Process an argument, converting its type and optionally validating it."""

    if arg not in func.type_info:
        return value

    val = type_system.convert_to_type(value, func.type_info[arg])
    if arg not in func.validator_info:
        return val

    type_obj = type_system.get_type(func.type_info[arg])

    # Run all of the validators that were defined for this argument.
    # If the validation fails, they will raise an exception that we convert to
    # an instance of ValidationError
    try:
        for validator_name, extra_args in func.validator_info[arg]:
            if not hasattr(type_obj, validator_name):
                raise ValidationError("Could not find validator specified for argument", argument=arg, validator_name=validator_name, type=str(type_obj), method=dir(type_obj))

            validator = getattr(type_obj, validator_name)
            validator(val, *extra_args)
    except (ValueError, TypeError) as exc:
        raise ValidationError(exc.args[0], argument=arg, value=val)

    return val
