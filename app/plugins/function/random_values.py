from systems.plugins.index import BaseProvider
from utility.data import ensure_list

import random


class Provider(BaseProvider('function', 'random_values')):

    def exec(self, list_value, limit = None):
        values = ensure_list(list_value)
        random.shuffle(values)

        return values[:min(int(limit), len(values))] if limit else values
