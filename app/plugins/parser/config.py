from systems.plugins.index import BaseProvider
from utility.data import Collection, dump_json

import re


class Provider(BaseProvider('parser', 'config')):

    variable_pattern = r'^\@\{?([a-zA-Z][\_\-a-zA-Z0-9]+)(?:\[([^\]]+)\])?\}?$'
    variable_value_pattern = r'(?<!\@)\@(\>\>?)?\{?([a-zA-Z][\_\-a-zA-Z0-9]+(?:\[[^\]]+\])?)\}?'


    def __init__(self, type, name, command, config):
        super().__init__(type, name, command, config)
        self.variables = Collection()


    def initialize(self, reset = False):
        if reset or not self.variables:
            self.variables.clear()
            for config in self.command.get_instances(self.command._config):
                self.variables[config.name] = config.value

    def check(self, name):
        return name in self.variables

    def set(self, name, value):
        self.variables[name] = value

    def get(self, name, default = None):
        return self.variables.get(name, default)


    def parse(self, value, config):
        if not isinstance(value, str) or '@' not in value:
            return value

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value, config)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                formatter = ref_match.group(1)
                variable_value = self.parse_variable(f"@{ref_match.group(2)}", config)
                if (formatter and formatter == '>>') or isinstance(variable_value, dict):
                    variable_value = dump_json(variable_value)
                elif isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)

                if variable_value is not None:
                    value = value.replace(ref_match.group(0), str(variable_value)).strip()
        return value

    def parse_variable(self, value, config):
        if config_match := re.search(self.variable_pattern, value):
            variables = {**self.variables.export(), **config.get('config_overrides', {})}
            new_value = config_match[1]
            key = config_match[2]

            if new_value in variables:
                data = variables[new_value]

                if key:
                    key = self.command.options.interpolate(key, **config.export())

                if isinstance(data, dict) and key:
                    try:
                        return data[key]
                    except KeyError:
                        return value
                elif isinstance(data, (list, tuple)) and key:
                    try:
                        return data[int(key)]
                    except KeyError:
                        return value
                else:
                    return data

        # Not found, assume desired
        return value
