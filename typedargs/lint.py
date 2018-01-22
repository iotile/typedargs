"""A pylint plugin that checks for errors in typedargs declarations.

This should be run using pylint in the following way:

```
pylint --load-plugins typedargs.lint <path to source files>
```

It will return errors if there are problems with annotated
functions or if the docstring for an @docannotate function
is not correctly formatted.
"""

#pylint: disable=all; Work in progress that should not be linted yet

from __future__ import (unicode_literals, print_function, absolute_import)
import sys
import inspect
from builtins import str
from collections import namedtuple
import astroid
import astroid.scoped_nodes
import astroid.node_classes
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from .metadata import ParameterInfo, ReturnInfo


AnnotationList = namedtuple("AnnotationList", ['params', 'returns', 'use_doc'])


class AnnotatedFunctionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    priority = -1

    @classmethod
    def process_param(cls, param):
        """Process an @param decorator into a ParameterInfo."""

        #FIXME: process params here
        return None

    @classmethod
    def process_return_type(cls, return_type):
        """Process an @return_type decorator."""

        ret_type = return_type.args[0]

        #FIXME: process return info here
        return None

    @classmethod
    def extract_annotations(cls, node):
        if not isinstance(node, astroid.scoped_nodes.FunctionDef):
            return None

        if node.decorators is None:
            return None

        annotated = False
        params = []
        returns = []
        use_doc = False

        for dec in node.decorators.nodes:
            if isinstance(dec, astroid.node_classes.Name):
                name = dec.name
                if name == 'annotated':
                    annotated = True
                elif name == 'docannotate':
                    annotated = True
                    use_doc = True
            elif isinstance(dec, astroid.node_classes.Call):
                name = dec.func.name

                if name == 'param':
                    annotated = True
                    param = cls.process_param(dec)
                    params.append(param)
                elif name == 'returns':
                    annotated = True
                    returns.append(dec)
                elif name == 'return_type':
                    annotated = True
                    rets = cls.process_return_type(dec)
                    returns.append(rets)

        if not annotated:
            return None

        return AnnotationList(params, returns, use_doc)


class DocannotationChecker(AnnotatedFunctionChecker):
    name = 'typedargs-annotation'

    msgs = {
        'W6701': (
            'Doc-annotation parameter or return does not correspond to a known type',
            'typedargs-unknown-type',
            'All types annotated using typedargs should resolve to known types.'
        )
    }

    def __init__(self, linter=None):
        super(DocannotationChecker, self).__init__(linter)

    def visit_functiondef(self, node):
        annotations = self.extract_annotations(node)
        if annotations is None:
            return

        if annotations.use_doc:
            print(node)


def register(linter):
    linter.register_checker(DocannotationChecker(linter))
