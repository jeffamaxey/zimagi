from systems.commands.index import CommandMixin


class ConfigMixin(CommandMixin('config')):

    def get_config(self, name, default = None, required = False):
        if not name:
            return default

        config = self.get_instance(self._config, name, required = required)
        return default if config is None else config.value
