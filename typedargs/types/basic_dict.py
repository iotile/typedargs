# pylint: disable=unused-argument,missing-docstring

import json
from typedargs.exceptions import ValidationError


MAPPED_BUILTIN_TYPE = dict
MAPPED_TYPE_NAMES = ('dict', )


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


def format_one_line(dict_obj, key_formatter=None, val_formatter=None):
    """Get string representation of passed dict object.

    Args:
        dict_obj (dict): dict object to translate to string.
        key_formatter (callable | string | None): formatter for dict key
        val_formatter (callable | string | None): formatter for dict value

    Returns:
        string: string representation of arg
    """
    if dict_obj == {}:
        return str(dict_obj)

    def _get_callable_formatter(obj, formatter):
        validation_err = ValidationError('Cannot convert to string')

        if formatter is None:
            return str

        if callable(formatter):
            return formatter

        if isinstance(formatter, str):
            f_name = 'format_{}'.format(formatter)
            if not (hasattr(obj, f_name) and callable(getattr(obj, f_name))):
                raise validation_err
            formatter = getattr(obj, f_name)
        else:
            raise validation_err

        return formatter

    key = list(dict_obj.keys())[0]
    val = dict_obj[key]
    key_formatter = _get_callable_formatter(key, key_formatter)
    val_formatter = _get_callable_formatter(val, val_formatter)

    str_items = []
    for key, val in dict_obj.items():
        key_str = key_formatter(key)
        val_str = val_formatter(val)
        str_items.append("{}: {}".format(key_str, val_str))
    return '{%s}' % ', '.join(str_items)
