from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'value')):

    def exec(self, data, keys, default = None):
        if isinstance(keys, str):
            keys = key.split('.')

        last_index = len(keys) - 1
        for index, key in enumerate(keys):
            data = data.get(key, default) if index == last_index else data.get(key, {})
        return data
