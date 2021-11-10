from collections import OrderedDict
from functools import lru_cache

from django.conf import settings
from django.apps import apps

from systems.index import module, django, component
from systems.models import index as model_index
from systems.commands import index as command_index
from systems.plugins import index as plugin_index
from utility.data import Collection, deep_merge
from utility.filesystem import load_yaml

import os
import sys
import re
import oyaml
import importlib
import inspect
import threading
import logging


logger = logging.getLogger(__name__)


class Indexer(
    module.IndexerModuleMixin,
    django.IndexerDjangoMixin,
    component.IndexerComponentMixin
):
    def __init__(self, manager):
        self.manager = manager

        self._spec = OrderedDict()
        self._roles = {}

        self._base_models = {}
        self._model_mixins = {}
        self._models = {}

        self.module_map = {}
        self.model_class_path = {}
        self.model_class_facades = {}

        self._base_commands = {}
        self._command_mixins = {}
        self._command_tree = {}

        self._plugin_providers = {}

        super().__init__()


    @property
    def spec(self):
        if not self._spec:
            def set_command_module(module_name, spec):
                if 'base' in spec:
                    spec['_module'] = module_name

                for key, value in spec.items():
                    if isinstance(value, dict):
                        set_command_module(module_name, value)


            def load_directory(base_path):
                if settings.APP_DIR in base_path:
                    module = 'core'
                    module_path = settings.APP_DIR
                else:
                    module = base_path.replace(settings.MODULE_BASE_PATH + '/', '').split('/')[1]
                    module_path = os.path.join(self.manager.module_dir, module)

                module_info = Collection(
                    module = module,
                    path = self._get_module_lib_dir(module_path)
                )

                for name in os.listdir(base_path):
                    file_path = os.path.join(base_path, name)
                    if os.path.isdir(file_path):
                        load_directory(file_path)

                    elif name[0] != '_' and re.match(r'^[^\.]+\.(yml|yaml)$', name, re.IGNORECASE):
                        logger.debug("Loading specification from file: {}".format(file_path))
                        spec_data = load_yaml(file_path)
                        sub_model_data = {'data': {}}

                        if spec_data:
                            for key, info in spec_data.items():
                                if key[0] != '_':
                                    self.module_map.setdefault(key, {})
                                    if key == 'roles':
                                        for name, description in info.items():
                                            self.module_map[key][name] = module_info
                                    else:
                                        for name, spec in info.items():
                                            if key == 'command':
                                                set_command_module(module, spec)
                                            else:
                                                app_name = spec.get('app', name)

                                                if key in ('data', 'data_base', 'data_mixins'):
                                                    module_name = model_index.get_module_name(key, app_name)
                                                    model_class = model_index.get_model_name(name, spec)
                                                    dynamic_class = model_index.get_dynamic_class_name(model_class)

                                                    self.model_class_path[model_class] = module_name
                                                    self.model_class_path[dynamic_class] = module_name
                                                    self.module_map[key][app_name] = module_info

                                                elif key == 'plugin':
                                                    if spec.get('base', '') == 'data' and spec.get('data', False):
                                                        for provider_name, provider_spec in spec.get('providers', {}).items():
                                                            data_name = "{}_{}".format(spec['data'], provider_name)

                                                            module_name = model_index.get_module_name('data', spec['data'])
                                                            model_class = model_index.get_model_name(data_name)
                                                            dynamic_class = model_index.get_dynamic_class_name(model_class)

                                                            self.model_class_path[model_class] = module_name
                                                            self.model_class_path[dynamic_class] = module_name
                                                            self.module_map['data'][data_name] = module_info

                                                            sub_model_data['data'][data_name] = {
                                                                'class': model_class,
                                                                'base': spec['data'],
                                                                'fields': provider_spec.get('fields', {}) if provider_spec else {},
                                                                'submodel': True
                                                            }

                            deep_merge(spec_data, sub_model_data)
                            deep_merge(self._spec, spec_data)

            for spec_path in self.get_module_dirs('spec'):
                load_directory(spec_path)

            for name, spec in self._spec['data'].items():
                if spec.get('submodel', False):
                    parent_spec = self._spec['data'][spec['base']]

                    self._spec['data'][name]['roles'] = parent_spec.get('roles', {})
                    self._spec['data'][name]['api'] = parent_spec.get('api', True)
                    self._spec['data'][name]['packages'] = parent_spec.get('packages', [])

        return self._spec

    @property
    def roles(self):
        if not self._roles:
            for name, description in self.spec['roles'].items():
                self._roles[name] = description

            logger.debug("Application roles: {}".format(self._roles))

        return self._roles


    @lru_cache(maxsize = None)
    def get_facade_index(self):
        facade_index = {}
        for model in self.get_models():
            facade = model.facade
            facade_index[facade.name] = facade
        return facade_index


    @property
    def command_tree(self):
        return self._command_tree

    def find_command(self, *args, **kwargs):
        return command_index.find_command(*args, **kwargs)


    def get_plugin_base(self, name):
        return self._plugin_providers[name]['base']

    def get_plugin_providers(self, name, include_system = False):
        providers = {}
        for provider, provider_class in self._plugin_providers[name]['providers'].items():
            if include_system or not provider_class.check_system():
                providers[provider] = provider_class
        return providers


    def generate(self):
        self.print_spec()
        self.generate_data_structures()
        self.generate_plugins()

        if sys.argv[1] != 'makemigrations':
            self.generate_commands()

        self.print_results()


    def generate_data_structures(self):
        logger.info("* Generating data mixins")
        for name, spec in self.spec.get('data_mixins', {}).items():
            logger.info(" > {}".format(name))
            self._model_mixins[name] = model_index.ModelMixin(name)
            logger.info("    - {}".format(self._model_mixins[name]))
            logger.info("    - {}".format(self._model_mixins[name].facade_class))

        logger.info("* Generating base data models")
        for name, spec in self.spec.get('data_base', {}).items():
            logger.info(" > {}".format(name))
            self._base_models[name] = model_index.BaseModel(name)
            logger.info("    - {}".format(self._base_models[name]))
            logger.info("    - {}".format(self._base_models[name].facade_class))

        logger.info("* Generating data models")
        for name, spec in self.spec.get('data', {}).items():
            logger.info(" > {}".format(name))
            self._models[name] = model_index.Model(name, ensure_exists = True)
            logger.info("    - {}".format(self._models[name]))
            logger.info("    - {}".format(self._models[name].facade_class))


    def generate_commands(self):
        logger.info("* Generating command mixins")
        for name, spec in self.spec.get('command_mixins', {}).items():
            logger.info(" > {}".format(name))
            self._command_mixins[name] = command_index.CommandMixin(name)
            logger.info("    - {}".format(self._command_mixins[name]))

        logger.info("* Generating base commands")
        for name, spec in self.spec.get('command_base', {}).items():
            logger.info(" > {}".format(name))
            self._base_commands[name] = command_index.BaseCommand(name)
            logger.info("    - {}".format(self._base_commands[name]))

        logger.info("* Generating command tree")
        self._command_tree = command_index.generate_command_tree(
            self.spec.get('command', {})
        )


    def generate_plugins(self):
        logger.info("* Generating base plugins")
        for name, spec in self.spec.get('plugin', {}).items():
            logger.info(" > {}".format(name))
            self._plugin_providers[name] = {
                'base': plugin_index.BasePlugin(name, True),
                'providers': {}
            }
            logger.info("    - {}".format(self._plugin_providers[name]['base']))

            providers = {}
            for provider_name, info in spec.get('providers', {}).items():
                providers[provider_name] = plugin_index.BaseProvider(name, provider_name, True)
                logger.info("      - {}".format(providers[provider_name]))

            self._plugin_providers[name]['providers'] = providers


    def print_spec(self):
        if settings.LOG_LEVEL == 'debug':
            logger.debug(oyaml.dump(self.spec, indent = 2))

    def print_command_tree(self, command, prefix = ''):
        logger.info("{} {}".format(prefix, command))
        if getattr(command, 'get_subcommands', None):
            for subcommand in command.get_subcommands():
                self.print_command_tree(subcommand, "{} > ".format(prefix))


    def print_results(self):
        if settings.LOG_LEVEL == 'info':
            logger.info('* Registered models')
            logger.info(self._base_models)
            logger.info(self._model_mixins)
            logger.info(self._models)

            logger.info('* Django registered models')
            for model in apps.get_models():
                logger.info(" - {}".format(model))
                model_index.display_model_info(model)

            logger.info('* Command tree')
            self.print_command_tree(self._command_tree)