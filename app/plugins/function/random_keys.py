from systems.plugins.index import BaseProvider

import random


class Provider(BaseProvider('function', 'random_keys')):

    def exec(self, dict_value, limit = None):
        keys = list(dict_value.keys())
        random.shuffle(keys)

        return keys[:min(int(limit), len(keys))] if limit else keys
