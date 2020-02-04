# pylint: disable=unused-argument,missing-docstring

import json

from typedargs.exceptions import ValidationError


def convert(arg, **kwargs):
    if arg is None:
        return None

    if isinstance(arg, str):
        return json.loads(arg)
    if isinstance(arg, dict):
        return arg

    raise TypeError("Unknown argument type")


def _json_formatter(arg):
    if isinstance(arg, bytearray):
        return repr(arg)

    return str(arg)


def default_formatter(arg, **kwargs):
    return json.dumps(arg, sort_keys=True, indent=4, separators=(',', ': '), default=_json_formatter)


def format_one_line(dict_arg, key_formatter=None, val_formatter=None):
    """Get string representation of arg

    Args:
        dict_arg (dict): object of type map
        key_formatter (callable | string | None): formatter for dict key
        val_formatter (callable | string | None): formatter for dict value

    Returns:
        string: string representation of arg
    """
    if dict_arg == {}:
        return str(dict_arg)

    def _get_callable_formatter(obj, formatter):
        validation_err = ValidationError('Cannot convert to string')

        if formatter is None:
            return str

        if not callable(formatter):
            if isinstance(formatter, str):
                f_name = 'format_{}'.format(formatter)
                if not (hasattr(obj, f_name) and callable(getattr(obj, f_name))):
                    raise validation_err
                formatter = getattr(obj, f_name)
            else:
                raise validation_err
        return formatter

    key = list(dict_arg.keys())[0]
    val = dict_arg[key]
    key_formatter = _get_callable_formatter(key, key_formatter)
    val_formatter = _get_callable_formatter(val, val_formatter)

    str_items = []
    for key, val in dict_arg.items():
        key_str = key_formatter(key)
        val_str = val_formatter(val)
        str_items.append("{}: {}".format(key_str, val_str))
    return '{%s}' % ', '.join(str_items)
