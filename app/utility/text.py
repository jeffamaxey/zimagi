from django.conf import settings

import textwrap
import string
import re


class Template(string.Template):
    delimiter = '@'
    idpattern = r'[a-zA-Z][\_\-a-zA-Z0-9]+(?:\<\<[^\>]+\>\>)?'
    variable_pattern = r'([^\<]+)(?:\<\<([^\>]+)\>\>)?'

    def substitute(self, **variables):
        return self.safe_substitute(**variables)

    def safe_substitute(self, **variables):

        def convert(match):
            named = match.group('named') or match.group('braced')
            if named is not None:
                try:
                    variable_match = re.match(self.variable_pattern, named)
                    variable = variable_match[1]
                    default = variable_match[2]
                    return str(variables[variable.strip()])

                except KeyError:
                    return '' if default is None else default.strip()

            if match.group('escaped') is not None:
                return self.delimiter
            if match.group('invalid') is not None:
                return ''

        return self.pattern.sub(convert, self.template)


def split_lines(text):
    return text.split("\n")

def split_paragraphs(text):
    para_edge = re.compile(r"(\n\s*\n)", re.MULTILINE)
    return para_edge.split(str(text))


def wrap(text, width, init_indent = '', init_style = None, indent = '', style = None):
    wrapper = TextWrapper(width = width)
    lines = wrapper.wrap(text)
    if count := len(lines):
        header = True
        content = init_style(lines[0]) if init_style else lines[0]
        lines[0] = f"{init_indent}{content}"

        if count > 1:
            for index in range(1, len(lines)):
                if header and lines[index] == '':
                    header = False
                    content = lines[index]
                elif header:
                    content = init_style(lines[index]) if init_style else lines[index]
                else:
                    content = style(lines[index]) if style else lines[index]

                lines[index] = f"{indent}{content}"

        lines[-1] = f"{lines[-1]}\n"

    return lines

def wrap_page(text, init_indent = '', init_style = None, indent = '', style = None):
    return wrap(text, settings.DISPLAY_WIDTH, init_indent, init_style, indent, style)


class TextWrapper(textwrap.TextWrapper):

    def wrap(self, text):
        paragraphs = split_paragraphs(text)
        wrapped_lines = []

        for para in paragraphs:
            if para.isspace():
                if not self.replace_whitespace:
                    if self.expand_tabs:
                        para = para.expandtabs()

                    wrapped_lines.append(para[1:-1])
                else:
                    wrapped_lines.append('')
            else:
                wrapped_lines.extend(textwrap.TextWrapper.wrap(self, para))

        return wrapped_lines
