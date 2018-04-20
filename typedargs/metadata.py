"""The basic class that is used to store metadata about a function."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import range, str
import inspect
from future.utils import viewitems
import typedargs.typeinfo as typeinfo
from .exceptions import TypeSystemError, ArgumentError, ValidationError, InternalError
from .basic_structures import ParameterInfo, ReturnInfo
from .doc_annotate import parse_docstring


class AnnotatedMetadata(object): #pylint: disable=R0902; These instance variables are required.
    """All of the associated metadata for an annotated function or class.

    Args:
        func (callable): The function that we are annotated so that
            we can pull out relevant argument spec information.  If func
            is a class, we pull arguments from its __init__ routine
        name (str): An optional name that will overwrite the default name
            of this function
    """

    def __init__(self, func, name=None):
        self.annotated_params = {}
        self._has_self = False

        docstring = func.__doc__

        if inspect.isclass(func):
            # If we're annotating a class, the name of the class should be
            # the class name so keep track of that before looking at its
            # __init__ function.
            if name is None:
                name = func.__name__

            func = func.__init__

            # If __init__ has anotated params, copy them to the class so
            # we print correct signatures
            if hasattr(func, 'metadata'):
                self.annotated_params = func.metadata.annotated_params

        # If we are called to annotate a context, we won't necessarily
        # have any arguments
        try:
            args, varargs, kwargs, defaults = inspect.getargspec(func)  # pylint: disable=deprecated-method

            # Skip self argument if this is a method function
            if len(args) > 0 and args[0] == 'self':
                args = args[1:]
                self._has_self = True

            if defaults is None:
                defaults = []

            self.varargs = varargs
            self.kwargs = kwargs
            self.arg_names = args
            self.arg_defaults = defaults
        except TypeError:
            self.varargs = None
            self.kwargs = None
            self.arg_names = []
            self.arg_defaults = []

        self.return_info = ReturnInfo(None, None, False, None)

        if name is None:
            name = func.__name__

        self.name = name

        self.load_from_doc = False
        self._doc_parsed = False
        self._docstring = docstring

    def _ensure_loaded(self):
        if self.load_from_doc and not self._doc_parsed:
            params, ret_info = parse_docstring(self._docstring)
            for param_name, param_info in viewitems(params):
                self.add_param(param_name, param_info.type_name, param_info.validators)

            if ret_info is not None:
                self.return_info = ret_info

            self._doc_parsed = True

    def spec_filled(self, pos_args, kw_args):
        """Check if we have enough arguments to call this function.

        Args:
            pos_args (list): A list of all the positional values we have.
            kw_args (dict): A dict of all of the keyword args we have.

        Returns:
            bool: True if we have a filled spec, False otherwise.
        """

        req_names = self.arg_names
        if len(self.arg_defaults) > 0:
            req_names = req_names[:-len(self.arg_defaults)]

        req = [x for x in req_names if x not in kw_args]
        return len(req) <= len(pos_args)

    def add_param(self, name, type_name, validators, desc=None):
        """Add type information for a parameter by name.

        Args:
            name (str): The name of the parameter we wish to annotate
            type_name (str): The name of the parameter's type
            validators (list): A list of either strings or n tuples that each
                specify a validator defined for type_name.  If a string is passed,
                the validator is invoked with no extra arguments.  If a tuple is
                passed, the validator will be invoked with the extra arguments.
            desc (str): Optional parameter description.
        """

        if name in self.annotated_params:
            raise TypeSystemError("Annotation specified multiple times for the same parameter", param=name)

        if name not in self.arg_names and name != self.varargs and name != self.kwargs:
            raise TypeSystemError("Annotation specified for unknown parameter", param=name)

        info = ParameterInfo(type_name, validators, desc)
        self.annotated_params[name] = info

    def typed_returnvalue(self, type_name, formatter=None):
        """Add type information to the return value of this function.

        Args:
            type_name (str): The name of the type of the return value.
            formatter (str): An optional name of a formatting function specified
                for the type given in type_name.
        """
        self.return_info = ReturnInfo(type_name, formatter, True, None)

    def string_returnvalue(self):
        """Mark the return value as data that should be converted with str."""
        self.return_info = ReturnInfo(None, str, True, None)

    def custom_returnvalue(self, printer, desc=None):
        """Use a custom function to print the return value.

        Args:
            printer (callable): A function that should take in the return
                value and convert it to a string.
            desc (str): An optional description of the return value.
        """
        self.return_info = ReturnInfo(None, printer, True, desc)

    def has_varargs(self):
        """Check if this function supports variable arguments."""
        return self.varargs is not None

    def has_kwargs(self):
        """Check if this function supports arbitrary keyword arguments."""
        return self.kwargs is not None

    def returns_data(self):
        """Check if this function returns data."""

        self._ensure_loaded()

        return self.return_info.is_data

    def match_shortname(self, name, filled_args=None):
        """Try to convert a prefix into a parameter name.

        If the result could be ambiguous or there is no matching
        parameter, throw an ArgumentError

        Args:
            name (str): A prefix for a parameter name
            filled_args (list): A list of filled positional arguments that will be
                removed from consideration.

        Returns:
            str: The full matching parameter name
        """

        filled_count = 0
        if filled_args is not None:
            filled_count = len(filled_args)

        possible = [x for x in self.arg_names[filled_count:] if x.startswith(name)]
        if len(possible) == 0:
            raise ArgumentError("Could not convert short-name full parameter name, none could be found", short_name=name, parameters=self.arg_names)
        elif len(possible) > 1:
            raise ArgumentError("Short-name is ambiguous, could match multiple keyword parameters", short_name=name, possible_matches=possible)

        return possible[0]

    def param_type(self, name):
        """Get the parameter type information by name.

        Args:
            name (str): The full name of a parameter.

        Returns:
            str: The type name or None if no type information is given.
        """

        self._ensure_loaded()

        if name not in self.annotated_params:
            return None

        return self.annotated_params[name].type_name

    def signature(self, name=None):
        """Return our function signature as a string.

        By default this function uses the annotated name of the function
        however if you need to override that with a custom name you can
        pass name=<custom name>

        Args:
            name (str): Optional name to override the default name given
                in the function signature.

        Returns:
            str: The formatted function signature
        """

        self._ensure_loaded()

        if name is None:
            name = self.name

        num_args = len(self.arg_names)

        num_def = 0
        if self.arg_defaults is not None:
            num_def = len(self.arg_defaults)

        num_no_def = num_args - num_def

        args = []
        for i in range(0, len(self.arg_names)):
            typestr = ""

            if self.arg_names[i] in self.annotated_params:
                typestr = "{} ".format(self.annotated_params[self.arg_names[i]].type_name)

            if i >= num_no_def:
                default = str(self.arg_defaults[i-num_no_def])
                if len(default) == 0:
                    default = "''"

                args.append("{}{}={}".format(typestr, str(self.arg_names[i]), default))
            else:
                args.append(typestr + str(self.arg_names[i]))

        return "{}({})".format(name, ", ".join(args))

    def format_returnvalue(self, value):
        """Format the return value of this function as a string.

        Args:
            value (object): The return value that we are supposed to format.

        Returns:
            str: The formatted return value, or None if this function indicates
                that it does not return data
        """

        self._ensure_loaded()

        if not self.return_info.is_data:
            return None

        # If the return value is typed, use the type_system to format it
        if self.return_info.type_name is not None:
            return typeinfo.type_system.format_value(value, self.return_info.type_name, self.return_info.formatter)

        # Otherwise we expect a callable function to convert this value to a string
        return self.return_info.formatter(value)

    def convert_positional_argument(self, index, arg_value):
        """Convert and validate a positional argument.

        Args:
            index (int): The positional index of the argument
            arg_value (object): The value to convert and validate

        Returns:
            object: The converted value.
        """

        # For bound methods, skip self
        if self._has_self:
            if index == 0:
                return arg_value

            index -= 1

        arg_name = self.arg_names[index]
        return self.convert_argument(arg_name, arg_value)

    def check_spec(self, pos_args, kwargs=None):
        """Check if there are any missing or duplicate arguments.

        Args:
            pos_args (list): A list of arguments that will be passed as positional
                arguments.
            kwargs (dict): A dictionary of the keyword arguments that will be passed.

        Returns:
            dict: A dictionary of argument name to argument value, pulled from either
                the value passed or the default value if no argument is passed.

        Raises:
            ArgumentError: If a positional or keyword argument does not fit in the spec.
            ValidationError: If an argument is passed twice.
        """

        if kwargs is None:
            kwargs = {}

        if self.varargs is not None or self.kwargs is not None:
            raise InternalError("check_spec cannot be called on a function that takes *args or **kwargs")

        missing = object()

        arg_vals = [missing]*len(self.arg_names)
        kw_indices = {name: i for i, name in enumerate(self.arg_names)}

        for i, arg in enumerate(pos_args):
            if i >= len(arg_vals):
                raise ArgumentError("Too many positional arguments, first excessive argument=%s" % str(arg))

            arg_vals[i] = arg

        for arg, val in viewitems(kwargs):
            index = kw_indices.get(arg)
            if index is None:
                raise ArgumentError("Cannot find argument by name: %s" % arg)

            if arg_vals[index] is not missing:
                raise ValidationError("Argument %s passed twice" % arg)

            arg_vals[index] = val

        # Fill in any default variables if their args are missing
        if len(self.arg_defaults) > 0:
            for i in range(0, len(self.arg_defaults)):
                neg_index = -len(self.arg_defaults) + i
                if arg_vals[neg_index] is missing:
                    arg_vals[neg_index] = self.arg_defaults[i]

        # Now make sure there isn't a missing gap
        if missing in arg_vals:
            index = arg_vals.index(missing)
            raise ArgumentError("Missing a required argument (position: %d, name: %s)" % (index, self.arg_names[index]))

        return {name: val for name, val in zip(self.arg_names, arg_vals)}

    def convert_argument(self, arg_name, arg_value):
        """Given a parameter with type information, convert and validate it.

        Args:
            arg_name (str): The name of the argument to convert and validate
            arg_value (object): The value to convert and validate

        Returns:
            object: The converted value.
        """

        self._ensure_loaded()

        type_name = self.param_type(arg_name)
        if type_name is None:
            return arg_value

        val = typeinfo.type_system.convert_to_type(arg_value, type_name)

        validators = self.annotated_params[arg_name].validators
        if len(validators) == 0:
            return val

        type_obj = typeinfo.type_system.get_type(type_name)

        # Run all of the validators that were defined for this argument.
        # If the validation fails, they will raise an exception that we convert to
        # an instance of ValidationError
        try:
            for validator_name, extra_args in validators:
                if not hasattr(type_obj, validator_name):
                    raise ValidationError("Could not find validator specified for argument", argument=arg_name, validator_name=validator_name, type=str(type_obj), method=dir(type_obj))

                validator = getattr(type_obj, validator_name)
                validator(val, *extra_args)
        except (ValueError, TypeError) as exc:
            raise ValidationError(exc.args[0], argument=arg_name, arg_value=val)

        return val
