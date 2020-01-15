from django.conf import settings
from django.db import models as django

from settings.roles import Roles
from data.state.models import State
from systems.models import environment, group, provider
from utility.runtime import Runtime

import os


class ModuleFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def ensure(self, command, reinit = False):
        if reinit or command.get_state('module_ensure', True) or \
            (settings.CLI_EXEC and not command.get_env().runtime_image):

            if not self.retrieve(settings.CORE_MODULE):
                command.options.add('module_provider_name', 'sys_internal')
                command.module_provider.create(settings.CORE_MODULE, {})

            for name, fields in self.manager.default_modules.items():
                provider = fields.pop('provider', 'git')
                command.exec_local('module save', {
                    'module_provider_name': provider,
                    'module_name': name,
                    'module_fields': fields
                })

            for module in command.get_instances(self):
                module.provider.update()
                module.provider.load_parents()

            self.manager.ordered_modules = None

            command.exec_local('module install', {
                'verbosity': command.verbosity
            })
            command.set_state('module_ensure', False)

    def keep(self):
        return [ settings.CORE_MODULE ] + list(self.manager.default_modules.keys())

    def get_field_remote_display(self, instance, value, short):
        return value

    def get_field_reference_display(self, instance, value, short):
        return value

    def get_field_status_display(self, instance, value, short):
        if value == self.model.STATUS_VALID:
            return self.success_color(value)
        return self.error_color(value)


class Module(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    STATUS_VALID = 'valid'
    STATUS_INVALID = 'invalid'

    remote = django.CharField(null = True, max_length = 256)
    reference = django.CharField(null = True, max_length = 128)

    class Meta(environment.EnvironmentModel.Meta):
        verbose_name = "module"
        verbose_name_plural = "modules"
        facade_class = ModuleFacade
        dynamic_fields = ['status']
        ordering = ['-provider_type', 'name']
        provider_name = 'module'

    @property
    def status(self):
        path = self.provider.module_path(self.name, ensure = False)
        mcmi_path = os.path.join(path, 'mcmi.yml')

        if os.path.isfile(mcmi_path):
            return self.STATUS_VALID
        return self.STATUS_INVALID


    def allowed_groups(self):
        return [ Roles.admin, Roles.module_admin ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        State.facade.store('module_ensure', value = True)
        State.facade.store('group_ensure', value = True)
        State.facade.store('config_ensure', value = True)
