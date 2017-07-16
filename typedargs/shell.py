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
import os.path
import platform
import importlib
from builtins import str
from future.utils import iteritems
from typedargs.exceptions import ArgumentError, NotFoundError
import typedargs.annotate as annotate
import typedargs.utils as utils
from typedargs.typeinfo import type_system

builtin_help = {
    'help': "help [function]: print help information about the current context or a function",
    'back': "back: replace the current context with its parent",
    'quit': "quit: quit the momo shell"
}


def process_kwarg(flag, arg_it):
    flag = flag[2:]
    skip = 0

    #Check if of the form name=value
    if '=' in flag:
        name, value = flag.split('=')
    else:
        name = flag
        value = next(arg_it)
        skip = 1

    return name, value, skip


@annotate.param("package", "path", "exists", desc="Path to the python package containing the types")
@annotate.param("module", "string", desc="The name of the submodule to load from package, if applicable")
def import_types(package, module=None):
    """
    Add externally defined types from a python package or module

    The MoMo type system is built on the typedargs package, which defines what kinds of types
    can be used for function arguments as well as how those types should be displayed and
    converted from binary representations or strings.  This function allows you to define external
    types in a separate package and import them into the MoMo type system so that they can be used.
    You might want to do this if you have custom firmware objects that you would like to interact with
    or that are returned in a syslog entry, for example.

    All objects defined in the global namespace of package (if module is None) or package.module if
    module is specified that define valid types will be imported and can from this point on be used
    just like any primitive type defined in typedargs itself.  Imported types are indistinguishable
    from primivtive types like string, integer and path.
    """

    if module is None:
        path = package
    else:
        path = os.path.join(package, module)

    type_system.load_external_types(path)


def print_dir(context):
    doc = inspect.getdoc(context)

    print("")
    print(annotate.context_name(context))

    if doc is not None:
        doc = inspect.cleandoc(doc)
        print(doc)

    print("\nDefined Functions:")

    if isinstance(context, dict):
        funs = context.keys()
    else:
        funs = annotate.find_all(context)

    for fun in funs:
        fun = find_function(context, fun)
        if isinstance(fun, annotate.BasicContext):
            print(" - " + fun.metadata.name)
        else:
            print(" - " + annotate.get_signature(fun))

        if annotate.short_description(fun) != "":
            print("   " + annotate.short_description(fun) + '\n')
        else:
            print("")

    print("\nBuiltin Functions")
    for bif in builtin_help.values():
        print(' - ' + bif)

    print("")


def print_help(context, fname):
    if fname in builtin_help:
        print(builtin_help[fname])
        return

    func = find_function(context, fname)
    annotate.print_help(func)


def _do_help(context, args):
    if len(args) == 0:
        print_dir(context)
    elif len(args) == 1:
        print_help(context, args[0])
    else:
        print("Too many arguments:", args)
        print("Usage: help [function]")

    return [], True


def deferred_add(add_action):
    """
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


def find_function(context, funname):
    func = None
    if isinstance(context, dict):
        if funname in context:
            func = context[funname]

            #Allowed lazy loading of functions
            if isinstance(func, str):
                func = deferred_add(func)
                context[funname] = func
    elif hasattr(context, funname):
        func = getattr(context, funname)

    if func is None:
        raise NotFoundError("Function not found", function=funname)

    return func


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

        self.root_add('import_types', import_types)

        #Initialize the root context if required
        self._check_initialize_context()

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

        funcs = annotate.find_all(self.contexts[-1]).keys() + builtin_help.keys()
        return funcs

    @classmethod
    def _remove_quotes(cls, word):
        if len(word) > 0 and word.startswith(("'", '"')) and word[0] == word[-1]:
            return word[1:-1]

        return word

    def _split_line(self, line):
        """Split a line into arguments using shlex and a dequoting routine."""

        parts = shlex.split(line, posix=self.posix_lex)
        if not self.posix_lex:
            parts = map(self._remove_quotes, parts)

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
            if func.metadata.spec_filled(pos_args, kw_args):
                break

            arg = args.pop(0)

            if arg == '--':
                break
            elif arg.startswith('-'):
                arg_value = None
                arg_name = None

                if len(arg) == 2:
                    arg_name = func.metadata.match_shortname(arg[1:])
                else:
                    if not arg.startswith('--'):
                        raise ArgumentError("Invalid method of specifying keyword argument that did not start with --", argument=arg)

                    # Skip the --
                    arg = arg[2:]

                    # Check if the value is embedded in the parameter
                    if '=' in arg:
                        arg, arg_value = arg.split('=')

                    arg_name = func.metadate.match_shortname(arg)

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

    def invoke(self, line):
        """Invoke a function given a list of command line arguments.

        The function is searched for using the current context on the context stack
        and its annotated type information is used to convert all of the string parameters
        passed in line to appropriate python types.
        """

        funname = line.pop(0)

        context = self.contexts[-1]

        #Check if we are asked for help
        if funname == 'help':
            return _do_help(context, line)
        if funname == 'quit':
            del self.contexts[:]
            return [], True
        if funname == 'back':
            self.contexts.pop()
            return line, True

        func = find_function(context, funname)

        #If this is a context derived from a module or package, just jump to it
        #since there is no initialization function
        if isinstance(func, annotate.BasicContext):
            self.contexts.append(func)
            self._check_initialize_context()
            return line, False

        # If the function wants arguments directly, do not parse them, otherwise turn them
        # into positional and kw arguments
        if func.takes_cmdline is True:
            val = func(line[1:])
        else:
            posargs, kwargs, line = self.process_arguments(func, line)
            val = func(*posargs, **kwargs)

        # Update our current context if this function destroyed it or returned a new one.
        finished = True

        if func.finalizer is True:
            self.contexts.pop()
        elif val is not None:
            if annotate.check_returns_data(func):
                if type_system.interactive:
                    annotate.print_retval(func, val)
            else:
                self.contexts.append(val)
                self._check_initialize_context()
                finished = False

        return line, finished
