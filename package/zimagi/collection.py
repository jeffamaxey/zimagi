from . import utility

import copy


class Collection(object):

    def __init__(self, attributes):
        attributes = utility.normalize_value(copy.deepcopy(attributes),
            strip_quotes = False,
            parse_json = True
        )
        for key, value in attributes.items():
            setattr(self, key, value)


    def __setitem__(self, name, value):
        self.__dict__[name] = value

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def set(self, name, value):
        self.__setitem__(name, value)


    def __getitem__(self, name):
        return None if name not in self.__dict__ else self.__dict__[name]

    def __getattr__(self, name):
        return self.__getitem__(name)

    def get(self, name, default = None):
        return default if name not in self.__dict__ else self.__dict__[name]


    def export(self):
        return copy.deepcopy(self.__dict__)


    def __str__(self):

        def convert(data):
            if isinstance(data, Collection):
                data = data.__dict__

            if isinstance(data, dict):
                for key, value in data.items():
                    data[key] = convert(value)
            elif isinstance(data, (list, tuple)):
                for index, value in enumerate(data):
                    data[index] = convert(value)
            return data

        return utility.dump_json(convert(self), indent = 2)

    def __repr__(self):
        return self.__str__()


    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for key, value in self.__dict__.items():
            setattr(result, key, copy.deepcopy(value, memo))
        return result


class RecursiveCollection(Collection):

    def __init__(self, attributes):
        for property, value in attributes.items():
            attributes[property] = self._create_collections(value)

        super().__init__(attributes)


    def _create_collections(self, data):
        conversion = data

        if isinstance(data, (list, tuple)):
            conversion = [self._create_collections(value) for value in data]
        elif isinstance(data, dict):
            conversion = RecursiveCollection(data)

        return conversion
