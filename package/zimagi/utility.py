from terminaltables import AsciiTable

from . import exceptions

import shutil
import re
import json
import logging


logger = logging.getLogger(__name__)


def get_service_url(host, port):
    return "https://{}:{}/".format(host, port)


def wrap_api_call(type, path, processor, params = None):
    try:
        return processor()

    except Exception as error:
        logger.debug("{} API error: {}".format(type.title(), format_error(path, error, params)))
        raise error


def normalize_value(value, strip_quotes = False, parse_json = False):
    if value is not None:
        if isinstance(value, str):
            if strip_quotes:
                value = value.lstrip("\'\"").rstrip("\'\"")

            if value:
                if re.match(r'^(NONE|None|none|NULL|Null|null)$', value):
                    value = None
                elif re.match(r'^(TRUE|True|true)$', value):
                    value = True
                elif re.match(r'^(FALSE|False|false)$', value):
                    value = False
                elif re.match(r'^\d+$', value):
                    value = int(value)
                elif re.match(r'^\d*\.\d+$', value):
                    value = float(value)
                elif parse_json and value[0] in ['[', '{']:
                    value = json.loads(value)

        elif isinstance(value, (list, tuple)):
            value = list(value)
            for index, element in enumerate(value):
                value[index] = normalize_value(element, strip_quotes, parse_json)

        elif isinstance(value, dict):
            for key, element in value.items():
                value[key] = normalize_value(element, strip_quotes, parse_json)
    return value


def format_options(options):
    if options is None:
        options = {}

    for key, value in options.items():
        if isinstance(value, dict):
            options[key] = json.dumps(value)
        elif isinstance(value, (list, tuple)):
            options[key] = json.dumps(list(value))

    return options


def format_error(path, error, params = None):
    params = ''
    if params:
        params = "\n{}".format(json.dumps(params, indent = 2))

    return "[ {} ]{}\n\n{}".format(
        path,
        params,
        str(error),
        '> ' + "\n".join([ item.strip() for item in exceptions.format_exception_info() ])
    )

def format_response_error(response):
    try:
        error_detail = json.loads(response.text).get('detail', response.text)
    except Exception:
        error_detail = response.text

    return "Error {}: {}\n\n".format(response.status_code, response.reason, error_detail)


def format_table(data, prefix = None):
    table_rows = AsciiTable(data).table.splitlines()
    prefixed_rows = []

    if prefix:
        for row in table_rows:
            prefixed_rows.append("{}{}".format(prefix, row))
    else:
        prefixed_rows = table_rows

    return ("\n".join(prefixed_rows), len(table_rows[0]))


def format_list(data, prefix = None, row_labels = False, width = None):
    if width is None:
        columns, rows = shutil.get_terminal_size(fallback = (80, 25))
        width = columns

    prefixed_text = [
        "=" * width
    ]
    if not row_labels:
        labels = list(data[0])
        values = data[1:]
    else:
        values = data

    def format_item(item):
        text = []

        if row_labels:
            values = item[1:]
            if len(values) > 0 and "\n" in values[0]:
                values[0] = "\n{}".format(values[0])

            text.append(" * {}: {}".format(
                item[0].replace("\n", ' '),
                "\n".join(values)
            ))
        else:
            text.append("-" * width)
            for index, label in enumerate(labels):
                value = str(item[index]).strip()
                if "\n" in value:
                    value = "\n{}".format(value)

                text.append(" * {}: {}".format(
                    label.replace("\n", ' '),
                    value
                ))
        return text

    for item in values:
        text = format_item(item)
        if text:
            prefixed_text.extend(text)

    return "\n".join(prefixed_text)


def format_data(data, prefix = None, row_labels = False, width = None):
    if width is None:
        columns, rows = shutil.get_terminal_size(fallback = (80, 25))
        width = columns

    table_text, table_width = format_table(data, prefix)
    if table_width <= width:
        return "\n" + table_text
    else:
        return "\n" + format_list(data, prefix, row_labels = row_labels, width = width)