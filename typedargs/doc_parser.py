"""Experimental module for better google docstring parsing."""
import ast
import inspect
from io import StringIO
from collections import namedtuple
from typing import List, Tuple, Iterator
from textwrap import fill, dedent
from .basic_structures import ParameterInfo, ReturnInfo
from .exceptions import ValidationError
from .terminal import get_terminal_size



BlankLine = namedtuple("BlankLine", ['contents'])
SectionHeader = namedtuple("SectionHeader", ['name'])
ContinuationLine = namedtuple("ContinuationLine", ['contents'])
Line = namedtuple("Line", ['contents'])
ListItem = namedtuple("ListItem", ['marker', 'contents'])


# pylint: disable=too-few-public-methods;Experimental class
class ParsedDocstring:
    """A parser for google docstrings.

    The parser will collect all of the sections and parse them into
    paragraphs that are separated by blank lines or indented sections
    depending on what kind of section it is.
    """

    MAIN_SECTION = 0
    ARGS_SECTION = 1
    RETURN_SECTION = 2

    def __init__(self, doc):
        self._sections = {ParsedDocstring.MAIN_SECTION: [], ParsedDocstring.ARGS_SECTION: [], ParsedDocstring.RETURN_SECTION: []}

        sections = self._collect_sections(doc)

        for order, section in sorted(sections, key=lambda x: x[0]):
            lines = sections[(order, section)]
            sec_type = self._classify_section(section)
            if sec_type is None:
                lines = [BlankLine(""), Line(section + ":"), BlankLine("")] + lines + [BlankLine("")]
                sec_type = ParsedDocstring.MAIN_SECTION

            self._sections[sec_type].extend(lines)

        for section, lines in self._sections.items():
            lines = self._merge_blank_lines(lines)
            self._sections[section] = lines

        self.param_info = {parse_param(arg.contents, True)[0]: parse_param(arg.contents, True)[1] for arg in self._sections.get(self.ARGS_SECTION, []) if isinstance(arg, Line)}
        self.return_info = None
        if len(self._sections.get(ParsedDocstring.RETURN_SECTION, [])) > 0:
            self.return_info = parse_return(self._sections[self.RETURN_SECTION][0].contents, True)

        self.maindoc = self._merge_adjacent_lines(self._sections[ParsedDocstring.MAIN_SECTION])

    @property
    def short_desc(self):
        """One line description of this parsed docstring.

        Returns:
            str
        """

        if len(self.maindoc) == 0:
            return ""

        return self.maindoc[0].contents

    @classmethod
    def _merge_adjacent_lines(cls, lines):
        out_lines = []

        for line in lines:
            if not isinstance(line, Line) or len(out_lines) == 0 or not isinstance(out_lines[-1], Line):
                out_lines.append(line)
            else:
                out_lines[-1] = Line(out_lines[-1].contents + " " + line.contents)

        return out_lines

    @classmethod
    def _merge_blank_lines(cls, lines):
        out_lines = []

        for line in lines:
            if not isinstance(line, BlankLine) or len(out_lines) == 0 or not isinstance(out_lines[-1], BlankLine):
                out_lines.append(line)

        if len(out_lines) > 0 and isinstance(out_lines[-1], BlankLine):
            out_lines = out_lines[:-1]

        if len(out_lines) > 0 and isinstance(out_lines[0], BlankLine):
            out_lines = out_lines[1:]

        return out_lines

    @classmethod
    def _merge_continuations(cls, lines):
        if len(lines) == 0:
            return []

        out_lines = []
        curr_line = lines[0]

        for line in lines[1:]:
            if isinstance(line, ContinuationLine):
                if curr_line is None:
                    out_lines.append(Line(line.contents))
                elif isinstance(curr_line, Line):
                    curr_line = Line(curr_line.contents + ' ' + line.contents)
                elif isinstance(curr_line, ListItem):
                    curr_line = ListItem(curr_line.marker, curr_line.contents + ' ' + line.contents)
            else:
                if curr_line is not None:
                    out_lines.append(curr_line)

                curr_line = None

                if isinstance(line, BlankLine):
                    out_lines.append(line)
                else:
                    curr_line = line

        if curr_line is not None:
            out_lines.append(curr_line)

        return out_lines

    @classmethod
    def _classify_section(cls, section):
        """Attempt to find the canonical name of this section."""

        name = section.lower()

        if name in frozenset(['args', 'arguments', "params", "parameters"]):
            return cls.ARGS_SECTION

        if name in frozenset(['returns', 'return']):
            return cls.RETURN_SECTION

        if name in frozenset(['main']):
            return cls.MAIN_SECTION

        return None

    @classmethod
    def _classify_line(cls, line):
        """Classify a line into a type of object."""

        line = line.rstrip()

        if len(line) == 0:
            return BlankLine('')

        if ' ' not in line and line.endswith(':'):
            name = line[:-1]
            return SectionHeader(name)

        if line.startswith('  '):
            return ContinuationLine(line.lstrip())

        if line.startswith(' - '):
            return ListItem('-', line[3:].lstrip())

        if line.startswith('- '):
            return ListItem('-', line[2:].lstrip())

        return Line(line)

    @classmethod
    def _parse_sections(cls, lines):
        curr_section = "Main"
        curr_lines = []
        sections = {}

        section_counter = 0

        for line in lines:
            line_obj = cls._classify_line(line)
            if isinstance(line_obj, SectionHeader):
                sections[(section_counter, curr_section)] = curr_lines
                curr_lines = []
                curr_section = line_obj.name
                section_counter += 1
            else:
                curr_lines.append(line)

        sections[(section_counter, curr_section)] = curr_lines
        return sections

    @classmethod
    def _dedent_and_parse(cls, lines):
        paragraph = '\n'.join(lines)
        dedented = dedent(paragraph)
        lines = dedented.splitlines()
        return [cls._classify_line(x) for x in lines]

    #pylint:disable=too-many-branches
    @classmethod
    def _collect_sections(cls, doc):
        doc = inspect.cleandoc(doc)
        lines = doc.splitlines()

        sections = cls._parse_sections(lines)

        for section in sections:
            reclassified = cls._dedent_and_parse(sections[section])
            sections[section] = cls._merge_continuations(reclassified)

        return sections

    @classmethod
    def _join_paragraph(cls, lines, leading_blanks, trailing_blanks):
        if leading_blanks is False:
            remove_count = 0
            for line in lines:
                if len(line) == 0:
                    remove_count += 1
                else:
                    break

            if remove_count > 0:
                lines = lines[remove_count:]

        if trailing_blanks is False:
            remove_count = 0
            for line in reversed(lines):
                if len(line) == 0:
                    remove_count += 1
                else:
                    break

            if remove_count > 0:
                lines = lines[:-remove_count]

        return " ".join(lines)

    @classmethod
    def _join_paragraphs(cls, lines, use_indent=False, leading_blanks=False, trailing_blanks=False):
        """Join adjacent lines together into paragraphs using either a blank line or indent as separator."""

        curr_para = []
        paragraphs = []

        for line in lines:
            if use_indent:
                if line.startswith(' '):
                    curr_para.append(line.lstrip())
                    continue
                elif line == '':
                    continue
                else:
                    if len(curr_para) > 0:
                        paragraphs.append(cls._join_paragraph(curr_para, leading_blanks, trailing_blanks))

                    curr_para = [line.lstrip()]
            else:
                if len(line) != 0:
                    curr_para.append(line)
                else:
                    paragraphs.append(cls._join_paragraph(curr_para, leading_blanks, trailing_blanks))
                    curr_para = []

        # Finish the last paragraph if there is one
        if len(curr_para) > 0:
            paragraphs.append(cls._join_paragraph(curr_para, leading_blanks, trailing_blanks))

        return paragraphs

    def wrap_and_format(self, width=None, include_params=False, include_return=False, excluded_params=None):
        """Wrap, format and print this docstring for a specific width.

        Args:
            width (int): The number of characters per line.  If set to None
                this will be inferred from the terminal width and default
                to 80 if not passed or if passed as None and the terminal
                width cannot be determined.
            include_return (bool): Include the return information section
                in the output.
            include_params (bool): Include a parameter information section
                in the output.
            excluded_params (list): An optional list of parameter names to exclude.
                Options for excluding things are, for example, 'self' or 'cls'.
        """

        if excluded_params is None:
            excluded_params = []

        out = StringIO()
        if width is None:
            width, _height = get_terminal_size()

        for line in self.maindoc:
            if isinstance(line, Line):
                out.write(fill(line.contents, width=width))
                out.write('\n')
            elif isinstance(line, BlankLine):
                out.write('\n')
            elif isinstance(line, ListItem):
                out.write(fill(line.contents, initial_indent=" %s " % line.marker[0], subsequent_indent="   ", width=width))
                out.write('\n')

        if include_params:
            included_params = set(self.param_info) - set(excluded_params)
            if len(included_params) > 0:
                out.write("\nParameters:\n")

                for param in included_params:
                    info = self.param_info[param]
                    out.write(" - %s (%s):\n" % (param, info.type_name))
                    out.write(fill(info.desc, initial_indent="   ", subsequent_indent="   ", width=width))
                    out.write('\n')

        if include_return:
            print("Returns:")
            print("    " + self.return_info.type_name)
            #pylint:disable=fixme; Issue tracked in #32
            # TODO: Also include description information here

        return out.getvalue()


def _iter_validators(validators_string: str) -> Iterator[str]:
    """Iterate over each complete validator."""

    while validators_string:
        item, _comma, validators_string = [val.strip() for val in validators_string.partition(',')]

        if not item:
            raise ValidationError('Malformed validators notation. Empty item found.', validators_string=validators_string)

        if '(' in item:
            # validator with args
            validators_string = '{}{}{}'.format(item, _comma, validators_string)
            item, _br, validators_string = [val.strip() for val in validators_string.partition(')')]

            if not _br:
                raise ValidationError('Malformed validators notation. Closing parenthesis missed.', validators_string=validators_string)

            item += _br
            validators_string = validators_string.strip().lstrip(',')

        yield item


def _parse_param_validators(param_desc: str) -> List[Tuple[str, list]]:
    """Get validators from parameter description.

    Validators should be specified in braces. Arguments of validator should be in brackets.
    Example of param_desc value:

        {nonnegative, range(1, 5), list(['a', 'b'], istrue(True))} Parameter descriptiom

    Validator arguments in parenthesis should be valid python code.
    Allowed validator argument types are: None, str, int, bool, float, list

    Args:
        param_desc: parameter description

    Returns:
          A list of validators
    """

    param_desc = param_desc.strip()
    if not param_desc.startswith('{'):
        return []

    validators_string, _br, _ = param_desc.partition('}')
    if not _br:
        raise ValidationError('Malformed validators notation. Closing brace missed.', param_desc=param_desc)

    validators_string = validators_string.lstrip('{')

    result_list = []
    for validator in _iter_validators(validators_string):
        if '(' not in validator:
            # it is a validator without arguments
            v_name = "validate_{}".format(validator)
            result_list.append((v_name, []))
        else:
            # it is a validator with arguments
            v_name, _br, v_args = [val.strip() for val in validator.partition('(')]
            v_args = v_args.rstrip(')').strip()

            if not v_name or not v_args:
                raise ValidationError('Malformed validators notation.', param_desc=param_desc, validator=validator)

            try:
                v_args = ast.literal_eval(v_args)
            except (ValueError, SyntaxError):
                raise ValidationError('Malformed validators notation. Cannot evaluate validator arguments', param_desc=param_desc, validator=validator)

            v_args = list(v_args) if isinstance(v_args, tuple) else [v_args]
            v_name = "validate_{}".format(v_name)

            result_list.append((v_name, v_args))

    return result_list


def _parse_return_value_formatter(formatter: str) -> Tuple[str, List[str]]:
    """
    formatter examples: hex, string, one_line[string, str]
    """
    base, _br, subs = [item.strip() for item in formatter.partition('[')]
    if _br:
        if not subs.endswith(']'):
            raise ValidationError('Malformed formatter notation.', formatter=formatter)

        subs = subs[:-1]
        subs = [s.strip() for s in subs.split(',') if s.strip()]
        return base, subs

    return base, []


def parse_param(param, include_desc=False, validate_type=True):
    """Parse a single typed parameter statement."""

    param_def, _colon, desc = param.partition(':')

    validators = _parse_param_validators(desc)

    if not include_desc:
        desc = None
    else:
        if validators:
            desc = desc.split('}', 1)[1]
        desc = desc.strip()

    if _colon == "":
        raise ValidationError("Invalid parameter declaration in docstring, missing colon", declaration=param)

    param_name, _space, param_type = param_def.partition(' ')
    if len(param_type) < 2 or param_type[0] != '(' or param_type[-1] != ')':
        if validate_type:
            raise ValidationError("Invalid parameter type string not enclosed in ( ) characters", param_string=param_def, type_string=param_type)

        return param_name, ParameterInfo(None, None, validators, desc)

    param_type = param_type[1:-1]
    return param_name, ParameterInfo(None, param_type, validators, desc)


def parse_return(return_line, include_desc=False, validate_type=True):
    """Parse a single return statement declaration.

    The valid types of return declaration are a Returns: section heading
    followed a line that looks like:
    type [format-as formatter]: description

    OR

    type [show-as (context | string | formatter)]: description sentence
    """

    ret_def, _colon, desc = return_line.partition(':')
    if _colon == "":
        if validate_type:
            raise ValidationError("Invalid return declaration in docstring, missing colon", declaration=ret_def)

        desc = ret_def
        ret_def = None

    if not include_desc:
        desc = None

    if ret_def and 'show-as' in ret_def:
        ret_type, _showas, show_type = ret_def.partition('show-as')
        show_type = _parse_return_value_formatter(show_type)

        if show_type[0] == 'context':
            return ReturnInfo(None, None, None, False, desc)

        return ReturnInfo(None, None, show_type, True, desc)

    if ret_def and 'format-as' in ret_def:
        ret_type, _showas, formatter = ret_def.partition('format-as')
        ret_type = ret_type.strip()
        formatter = _parse_return_value_formatter(formatter)

        return ReturnInfo(None, ret_type, formatter, True, desc)

    return ReturnInfo(None, ret_def, None, True, desc)
