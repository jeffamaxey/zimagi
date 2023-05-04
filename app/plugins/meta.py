from plugins import base
from systems.plugins import index as plugin_index


class MetaProviderAccessError(Exception):
    pass


class BasePlugin(base.BasePlugin):

    @classmethod
    def generate(cls, plugin, generator):
        super().generate(plugin, generator)

        def register_types(self):
            for subtype, spec in generator.spec['subtypes'].items():
                if getattr(generator, 'provider', None):
                    self.set(subtype, plugin_index.BaseProvider(
                        "{}.{}".format(generator.name, subtype),
                        generator.provider
                    ))
                else:
                    self.set(subtype, plugin_index.BasePlugin(
                        "{}.{}".format(generator.name, subtype)
                    ))

        plugin.register_types = register_types


    def __init__(self, type, name, command, *args, **options):
        super().__init__(type, name, command)
        self.provider_index = {}
        self.register_types()
        self.args = args
        self.options = options

    def register_types(self):
        # Override in subclass
        pass


    def context(self, subtype, test = False):
        if subtype is None:
            return super().context(subtype, test)

        provider = self.provider(subtype)(
            self.provider_type,
            self.name,
            self.command,
            *self.args,
            **self.options
        )
        provider.test = test
        return provider


    def provider_schema(self, type):
        provider = self.context(type, self.test)
        return provider.provider_schema()


    def __getattr__(self, type):
        return self.context(type, self.test)

    def provider(self, type):
        if type in self.provider_index:
            return self.provider_index[type]
        else:
            raise MetaProviderAccessError(
                f"Sub provider {type} does not exist in {self.name} index"
            )


    def set(self, type, provider_cls):
        self.provider_index[type] = provider_cls
