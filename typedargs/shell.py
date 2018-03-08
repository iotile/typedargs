"""Hierarchical Shell provides as REPL like environment for executing commmands."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

#shell.py
#Given a command line string, attempt to map it to a function and fill in
#the parameters based on that function's annotated type information.

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import inspect
import shlex
import platform
import importlib
from builtins import str
from future.utils import iteritems
from typedargs.exceptions import ArgumentError, NotFoundError, ValidationError
import typedargs.annotate as annotate
import typedargs.utils as utils
from typedargs import iprint
from typedargs.typeinfo import type_system


@annotate.context("root")
class InitialContext(dict):
    """A basic context for holding the root callable functions for a shell."""
    pass


class HierarchicalShell(object):
    """A hierarchical shell for navigating through python package API functions."""

    def __init__(self, name):
        self.name = name
        self.init_commands = {}

        self.root = InitialContext()
        self.contexts = [self.root]

        # Keep track of whether we are on windows because shlex does not dequote
        # strings the same on Windows as on other platforms
        self.posix_lex = platform.system() != 'Windows'

        #Initialize the root context if required
        self._check_initialize_context()

        # Initialize our builtin functions
        self.builtins = {}
        self.add_builtin('back', self._builtin_back)
        self.add_builtin('help', self._builtin_help)
        self.add_builtin('quit', self._builtin_quit)

    def add_builtin(self, name, callable):
        """Add a builtin function callable from all contexts.

        Callable should be an annotated function like any other that you
        want to call from a HierarchicalShell

        Args:
            name (str): The name of the function
            callable (callable): The annotated function that we should call
        """

        self.builtins[name] = callable

    def root_update(self, dict_like):
        """Add entries to root from a dict_line object."""
        self.root.update(dict_like)

    def root_add(self, name, value):
        """Add a single function to the root context.

        Args:
            name (str): The name of the callable to add
            value (str or callable): The callable function or a string to
                lazily resolve to the callable later.
        """

        self.root[name] = value

    def context_name(self):
        """Get the string name of the current context."""
        return utils.context_name(self.contexts[-1])

    def finished(self):
        """Check if we have finalized all contexts.

        Returns:
            bool: True if there are no nested contexts left, False otherwise
        """

        return len(self.contexts) == 0

    def valid_identifiers(self):
        """Get a list of all valid identifiers for the current context.

        Returns:
            list(str): A list of all of the valid identifiers for this context
        """

        funcs = list(utils.find_all(self.contexts[-1])) + list(self.builtins)
        return funcs

    @classmethod
    def _deferred_add(cls, add_action):
        """Lazily load a callable.

        Perform a lazy import of a context so that we don't have a huge initial startup time
        loading all of the modules that someone might want even though they probably only
        will use a few of them.
        """

        module, _, obj = add_action.partition(',')

        mod = importlib.import_module(module)
        if obj == "":
            _, con = annotate.context_from_module(mod)
            return con

        if hasattr(mod, obj):
            return getattr(mod, obj)

        raise ArgumentError("Attempted to import nonexistent object from module", module=module, object=obj)

    @classmethod
    def _remove_quotes(cls, word):
        if len(word) > 0 and word.startswith(("'", '"')) and word[0] == word[-1]:
            return word[1:-1]

        return word

    def _split_line(self, line):
        """Split a line into arguments using shlex and a dequoting routine."""

        parts = shlex.split(line, posix=self.posix_lex)
        if not self.posix_lex:
            parts = [self._remove_quotes(x) for x in parts]

        return parts

    def _check_initialize_context(self):
        """
        Check if our context matches something that we have initialization commands
        for.  If so, run them to initialize the context before proceeding with other
        commands.
        """

        path = ".".join([annotate.context_name(x) for x in self.contexts])

        #Make sure we don't clutter up the output with return values from
        #initialization functions
        old_interactive = type_system.interactive
        type_system.interactive = False

        for key, cmds in iteritems(self.init_commands):
            if path.endswith(key):
                for cmd in cmds:
                    line = self._split_line(cmd)
                    self.invoke(line)

        type_system.interactive = old_interactive

    @annotate.finalizer
    def _builtin_back(self):
        """Pop the current context and return to its parent."""
        pass  # Popping the context is handled by invoke since this is marked as a finalizer

    @annotate.takes_cmdline
    def _builtin_quit(self, _cmdline):
        """Quit this hierarchical shell."""
        del self.contexts[:]

    @annotate.takes_cmdline
    @annotate.stringable
    def _builtin_help(self, args):
        """Return help information for a context or function."""

        if len(args) == 0:
            return self.list_dir(self.contexts[-1])
        elif len(args) == 1:
            func = self.find_function(self.contexts[-1], args[0])
            return annotate.get_help(func)

        help_text = "Too many arguments: " + str(args) + "\n"
        help_text += "Usage: help [function]"
        return help_text

    def find_function(self, context, funname):
        """Find a function in the given context by name.

        This function will first search the list of builtins and if the
        desired function is not a builtin, it will continue to search
        the given context.

        Args:
            context (object): A dict or class that is a typedargs context
            funname (str): The name of the function to find

        Returns:
            callable: The found function.
        """

        if funname in self.builtins:
            return self.builtins[funname]

        func = None
        if isinstance(context, dict):
            if funname in context:
                func = context[funname]

                #Allowed lazy loading of functions
                if isinstance(func, str):
                    func = self._deferred_add(func)
                    context[funname] = func
        elif hasattr(context, funname):
            func = getattr(context, funname)

        if func is None:
            raise NotFoundError("Function not found", function=funname)

        return func

    def list_dir(self, context):
        """Return a listing of all of the functions in this context including builtins.

        Args:
            context (object): The context to print a directory for.

        Returns:
            str
        """

        doc = inspect.getdoc(context)

        listing = ""
        listing += "\n"

        listing += annotate.context_name(context) + "\n"

        if doc is not None:
            doc = inspect.cleandoc(doc)
            listing += doc + "\n"

        listing += "\nDefined Functions:\n"
        is_dict = False

        if isinstance(context, dict):
            funs = context.keys()
            is_dict = True
        else:
            funs = utils.find_all(context)

        for fun in sorted(funs):
            override_name = None
            if is_dict:
                override_name = fun

            fun = self.find_function(context, fun)

            if isinstance(fun, dict):
                if is_dict:
                    listing += " - " + override_name + '\n'
                else:
                    listing += " - " + fun.metadata.name + '\n'
            else:
                listing += " - " + fun.metadata.signature(name=override_name) + '\n'

            if annotate.short_description(fun) != "":
                listing += "   " + annotate.short_description(fun) + '\n'

        listing += "\nBuiltin Functions\n"
        for bif in sorted(self.builtins.keys()):
            listing += ' - ' + bif + '\n'

        listing += '\n'
        return listing

    @classmethod
    def _is_flag(cls, arg):
        """Check if an argument is a flag.

        A flag starts with - or -- and the next character must be a letter
        followed by letters, numbers, - or _.  Currently we only check the
        alpha'ness of the first non-dash character to make sure we're not just
        looking at a negative number.

        Returns:
            bool: Whether the argument is a flag.
        """

        if arg == '--':
            return False

        if not arg.startswith('-'):
            return False

        if arg.startswith('--'):
            first_char = arg[2]
        else:
            first_char = arg[1]

        if not first_char.isalpha():
            return False

        return True

    def process_arguments(self, func, args):
        """Process arguments from the command line into positional and kw args.

        Arguments are consumed until the argument spec for the function is filled
        or a -- is found or there are no more arguments.  Keyword arguments can be
        specified using --field=value, -f value or --field value.  Positional
        arguments are specified just on the command line itself.

        If a keyword argument (`field`) is a boolean, it can be set to True by just passing
        --field or -f without needing to explicitly pass True unless this would cause
        ambiguity in parsing since the next expected positional argument is also a boolean
        or a string.

        Args:
            func (callable): A function previously annotated with type information
            args (list): A list of all of the potential arguments to this function.

        Returns:
            (args, kw_args, unused args): A tuple with a list of args, a dict of
                keyword args and a list of any unused args that were not processed.
        """

        pos_args = []
        kw_args = {}

        while len(args) > 0:
            if func.metadata.spec_filled(pos_args, kw_args) and not self._is_flag(args[0]):
                break

            arg = args.pop(0)

            if arg == '--':
                break
            elif self._is_flag(arg):
                arg_value = None
                arg_name = None

                if len(arg) == 2:
                    arg_name = func.metadata.match_shortname(arg[1:], filled_args=pos_args)
                else:
                    if not arg.startswith('--'):
                        raise ArgumentError("Invalid method of specifying keyword argument that did not start with --", argument=arg)

                    # Skip the --
                    arg = arg[2:]

                    # Check if the value is embedded in the parameter
                    # Make sure we allow the value after the equals sign to also
                    # contain an equals sign.
                    if '=' in arg:
                        arg, arg_value = arg.split('=', 1)

                    arg_name = func.metadata.match_shortname(arg, filled_args=pos_args)

                arg_type = func.metadata.param_type(arg_name)
                if arg_type is None:
                    raise ArgumentError("Attempting to set a parameter from command line that does not have type information", argument=arg_name)

                # If we don't have a value yet, attempt to get one from the next parameter on the command line
                if arg_value is None:
                    arg_value = self._extract_arg_value(arg_name, arg_type, args)

                kw_args[arg_name] = arg_value
            else:
                pos_args.append(arg)

        # Always check if there is a trailing '--' and chomp so that we always
        # start on a function name.  This can happen if there is a gratuitous
        # -- for a 0 arg function or after an implicit boolean flag like -f --
        if len(args) > 0 and args[0] == '--':
            args.pop(0)

        return pos_args, kw_args, args

    @classmethod
    def _extract_arg_value(cls, arg_name, arg_type, remaining):
        """Try to find the value for a keyword argument."""

        next_arg = None
        should_consume = False
        if len(remaining) > 0:
            next_arg = remaining[0]
            should_consume = True

            if next_arg == '--':
                next_arg = None

        # Generally we just return the next argument, however if the type
        # is bool we allow not specifying anything to mean true if there
        # is no ambiguity
        if arg_type == "bool":
            if next_arg is None or next_arg.startswith('-'):
                next_arg = True
                should_consume = False
        else:
            if next_arg is None:
                raise ArgumentError("Could not find value for keyword argument", argument=arg_name)

        if should_consume:
            remaining.pop(0)

        return next_arg

    def invoke_one(self, line):
        """Invoke a function given a list of arguments with the function listed first.

        The function is searched for using the current context on the context stack
        and its annotated type information is used to convert all of the string parameters
        passed in line to appropriate python types.

        Args:
            line (list): The list of command line arguments.

        Returns:
            (object, list, bool): A tuple containing the return value of the function, if any,
                a boolean specifying if the function created a new context (False if a new context
                was created) and a list with the remainder of the command line if this function
                did not consume all arguments.
        """

        funname = line.pop(0)

        context = self.contexts[-1]
        func = self.find_function(context, funname)

        #If this is a context derived from a module or package, just jump to it
        #since there is no initialization function
        if isinstance(func, dict):
            self.contexts.append(func)
            self._check_initialize_context()
            return None, line, False

        # If the function wants arguments directly, do not parse them, otherwise turn them
        # into positional and kw arguments
        if func.takes_cmdline is True:
            val = func(line)
            line = []
        else:
            posargs, kwargs, line = self.process_arguments(func, line)

            #We need to check for not enough args for classes before calling or the call won't make it all the way to __init__
            if inspect.isclass(func) and not func.metadata.spec_filled(posargs, kwargs):
                raise ValidationError("Not enough parameters specified to call function", function=func.metadata.name, signature=func.metadata.signature())

            val = func(*posargs, **kwargs)

        # Update our current context if this function destroyed it or returned a new one.
        finished = True

        if func.finalizer is True:
            self.contexts.pop()
        elif val is not None:
            if func.metadata.returns_data():
                val = func.metadata.format_returnvalue(val)
            else:
                self.contexts.append(val)
                self._check_initialize_context()
                finished = False
                val = None

        return val, line, finished

    def invoke(self, line):
        """Invoke a one or more function given a list of arguments.

        The functions are searched for using the current context on the context stack
        and its annotated type information is used to convert all of the string parameters
        passed in line to appropriate python types.

        Args:
            line (list): The list of command line arguments.

        Returns:
            bool: A boolean specifying if the last function created a new context
                (False if a new context was created) and a list with the remainder of the
                command line if this function did not consume all arguments.)
        """

        finished = True

        while len(line) > 0:
            val, line, finished = self.invoke_one(line)
            if val is not None:
                iprint(val)

        return finished

    def invoke_string(self, line):
        """Parse and invoke a string line.

        Args:
            line (str): The line that we want to parse and invoke.

        Returns:
            bool: A boolean specifying if the last function created a new context
                (False if a new context was created) and a list with the remainder of the
                command line if this function did not consume all arguments.)
        """

        # Make sure line is a unicode string on all python versions
        line = str(line)

        # Ignore empty lines and comments
        if len(line) == 0:
            return True

        if line[0] == u'#':
            return True

        args = self._split_line(line)
        return self.invoke(args)
