from settings.roles import Roles
from systems.models.index import ModelMixin, ModelMixinFacade
from data.group.cache import Cache


class GroupMixinFacade(ModelMixinFacade('group')):

    def check_group_access(self, instance, command):
        return bool(command.check_access(instance))


class GroupMixin(ModelMixin('group')):

    def access_groups(self, reset = False):
        return self.allowed_groups() + self.group_names(reset)

    def allowed_groups(self):
        return [ Roles.admin ]

    def group_names(self, reset = False):
        return Cache().get(self.facade, self.get_id(),
            reset = reset
        )


    def save(self, *args, **kwargs):
        Cache().clear(self.facade)
        super().save(*args, **kwargs)


    def initialize(self, command):
        if getattr(super(), 'initialize', None) and not super().initialize(
            command
        ):
            return False
        return self.facade.check_group_access(self, command)
