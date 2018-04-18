"""Experimental module for better google docstring parsing."""

from __future__ import unicode_literals
from builtins import int, str
import inspect
from .basic_structures import ParameterInfo, ReturnInfo
from .exceptions import ValidationError


# pylint: disable=too-few-public-methods;Experimental class
class ParsedDocstring(object):
    """A parser for google docstrings.

    The parser will collect all of the sections and parse them into
    paragraphs that are separated by blank lines or indented sections
    depending on what kind of section it is.
    """

    MAIN_SECTION = 0
    ARGS_SECTION = 1
    RETURN_SECTION = 2

    def __init__(self, doc):
        self.known_sections = {}
        self.unknown_sections = {}

        self._collect_sections(doc)

        self.short_desc = None
        if self.MAIN_SECTION in self.known_sections and len(self.known_sections[self.MAIN_SECTION]) > 0:
            self.short_desc = self.known_sections[self.MAIN_SECTION][0]

        self.param_info = {parse_param(arg, True)[0]: parse_param(arg, True)[1] for arg in self.known_sections.get(self.ARGS_SECTION, [])}
        self.return_info = None
        if self.RETURN_SECTION in self.known_sections:
            self.return_info = parse_return(self.known_sections[self.RETURN_SECTION][0], True)

    #pylint:disable=too-many-branches
    def _collect_sections(self, doc):
        doc = inspect.cleandoc(doc)
        lines = doc.splitlines()
        curr_section = self.MAIN_SECTION
        new_section = None
        section_indent = None
        section_contents = []

        for line in lines:
            line = line.rstrip()

            if str(line) == 'Args:':
                new_section = self.ARGS_SECTION
            elif str(line) == 'Returns:':
                new_section = self.RETURN_SECTION
            elif len(line) > 0 and line[0] != ' ' and line[-1] == ':':
                new_section = line[:-1]

            if new_section is not None:
                use_indent = False
                if isinstance(curr_section, int):
                    if curr_section == self.ARGS_SECTION:
                        use_indent = True

                    self.known_sections[curr_section] = self._join_paragraphs(section_contents, use_indent=use_indent)
                else:
                    self.unknown_sections[curr_section] = self._join_paragraphs(section_contents, use_indent=use_indent)

                curr_section = new_section
                new_section = None
                section_indent = None
                section_contents = []

                continue

            if section_indent is None:
                stripped = line.lstrip()
                section_indent = len(line) - len(stripped)

            if len(line) >= section_indent:
                line = line[section_indent:]

            section_contents.append(line)

        # Make sure we finish putting the last section into our table
        if curr_section is not None:
            use_indent = False
            if isinstance(curr_section, int):
                if curr_section == self.ARGS_SECTION:
                    use_indent = True

                self.known_sections[curr_section] = self._join_paragraphs(section_contents, use_indent=use_indent)
            else:
                self.unknown_sections[curr_section] = self._join_paragraphs(section_contents, use_indent=use_indent)

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

        # Finish the last paragraph if ther is one
        if len(curr_para) > 0:
            paragraphs.append(cls._join_paragraph(curr_para, leading_blanks, trailing_blanks))

        return paragraphs


def parse_param(param, include_desc=False):
    """Parse a single typed parameter statement."""

    param_def, _colon, desc = param.partition(':')
    if not include_desc:
        desc = None

    if _colon == "":
        raise ValidationError("Invalid parameter declaration in docstring, missing colon", declaration=param)

    param_name, _space, param_type = param_def.partition(' ')
    if len(param_type) < 2 or param_type[0] != '(' or param_type[-1] != ')':
        raise ValidationError("Invalid parameter type string not enclosed in ( ) characters", param_string=param_def, type_string=param_type)

    param_type = param_type[1:-1]
    return param_name, ParameterInfo(param_type, [], desc)


def parse_return(return_line, include_desc=False):
    """Parse a single return statement declaration.

    The valid types of return declarion are a Returns: section heading
    followed a line that looks like:
    type [format-as formatter]: description

    OR

    type [show-as (string | context)]: description sentence
    """

    ret_def, _colon, desc = return_line.partition(':')
    if _colon == "":
        raise ValidationError("Invalid return declaration in docstring, missing colon", declaration=ret_def)

    if not include_desc:
        desc = None

    if 'show-as' in ret_def:
        ret_type, _showas, show_type = ret_def.partition('show-as')
        ret_type = ret_type.strip()
        show_type = show_type.strip()

        if show_type not in ('string', 'context'):
            raise ValidationError("Unkown show-as formatting specifier", found=show_type, expected=['string', 'context'])

        if show_type == 'string':
            return ReturnInfo(None, str, True, desc)

        return ReturnInfo(None, None, False, desc)

    if 'format-as' in ret_def:
        ret_type, _showas, formatter = ret_def.partition('format-as')
        ret_type = ret_type.strip()
        formatter = formatter.strip()

        return ReturnInfo(ret_type, formatter, True, desc)

    return ReturnInfo(ret_def, None, True, desc)
