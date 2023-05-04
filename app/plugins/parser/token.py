from systems.plugins.index import BaseProvider
from utility.data import create_token

import re


class Provider(BaseProvider('parser', 'token')):

    token_pattern = r'^\%([\%\!])([a-zA-Z][\_\-a-zA-Z0-9]+)(?:\:(\d+))?$'


    def parse(self, value, config):
        if not isinstance(value, str) or not value.startswith('%'):
            return value

        if ref_match := re.search(self.token_pattern, value):
            operation = ref_match[1]
            length = ref_match[3]
            length = int(length) if length else 20
            state_name = f"token-{ref_match[2]}-{length}"

            value = self.command.get_state(state_name) if operation == '%' else None
            if not value:
                value = create_token(length)
                self.command.set_state(state_name, value)

        return value
