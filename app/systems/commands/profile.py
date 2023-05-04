from collections import OrderedDict
from django.conf import settings

from systems.models.base import BaseModel
from utility.data import Collection, ensure_list, flatten, clean_dict, normalize_value, format_value, prioritize, dump_json

import re
import copy
import yaml
import logging


logger = logging.getLogger(__name__)


noalias_dumper = yaml.dumper.SafeDumper
noalias_dumper.ignore_aliases = lambda self, data: True


class BaseProfileComponent(object):

    def __init__(self, name, profile):
        self.name = name
        self.profile = profile
        self.command = profile.command
        self.manager = self.command.manager

    def priority(self):
        return 10


    def ensure_module_config(self):
        # Override in subclass if needed
        return False


    def get_names(self, relation):
        return [ getattr(x, x.facade.key()) for x in relation.all() ]

    def get_info(self, name, config):
        return self.profile.get_info(name, config)

    def pop_info(self, name, config):
        return self.profile.pop_info(name, config)

    def get_value(self, name, config):
        return self.profile.get_value(name, config)

    def pop_value(self, name, config):
        return self.profile.pop_value(name, config)

    def get_values(self, name, config):
        return self.profile.get_values(name, config)

    def pop_values(self, name, config):
        return self.profile.pop_values(name, config)

    def interpolate(self, config, **replacements):
        return self.profile.interpolate(config, replacements)

    def get_variables(self, instance, variables = None):
        if not variables:
            variables = {}
        return self.profile.get_variables(instance, variables)


    def exec(self, command, **parameters):
        return self.command.exec_local(command, parameters)

    def run_list(self, elements, processor):
        return self.command.run_list(elements, processor)


class CommandProfile(object):

    def __init__(self, module, name = None, data = None):
        if not data:
            data = {}

        self.name = name
        self.module = module
        self.command = module.command
        self.manager = self.command.manager
        self.data = data
        self.components = []

        self.config = Collection()


    def get_component_names(self, filter_method = None):
        return self.manager.index.load_component_names(self, filter_method)


    def initialize(self, config, components):
        self.components = components if components else []

        if not config:
            config = {}

        self.init_config(config)
        self.load_parents()
        self.data = self.get_schema()


    def init_config(self, dynamic_config):
        self.command.options.initialize(True)

        for stored_config in self.command.get_instances(self.command._config):
            self.config.set(stored_config.name, stored_config.value)

        if isinstance(dynamic_config, dict):
            for name, value in dynamic_config.items():
                self.config.set(name, value)

    def get_config(self):
        return self.data.get('config', {})

    def set_config(self, config):
        if 'config' not in self.data:
            self.data['config'] = {}

        for name, value in self.interpolate_config(config).items():
            self.data['config'][name] = value


    def interpolate_config(self, input_config, **options):
        config = {}
        for name, value in input_config.items():
            config[name] = self.interpolate_config_value(value, **options)
            if not self.config.check(name):
                self.config.set(name, config[name])
        return config

    def interpolate_config_value(self, value, **options):
        options['config_overrides'] = self.config.export()
        return normalize_value(self.command.options.interpolate(value, **options))


    def load_parents(self):
        self.parents = []

        self.set_config(self.get_config())

        if 'parents' in self.data:
            parents = self.data.pop('parents')
            for parent in reversed(ensure_list(parents)):
                module = self.module.instance

                if isinstance(parent, str):
                    profile_name = self.interpolate_config_value(parent)
                else:
                    profile_name = self.interpolate_config_value(parent['profile'])
                    if 'module' in parent:
                        module_name = self.interpolate_config_value(parent['module'])
                        if module_name != 'self':
                            module = self.get_module(module_name)

                self.parents.insert(0,
                    module.provider.get_profile(profile_name)
                )
            for profile in reversed(self.parents):
                profile.load_parents()


    def get_schema(self):
        schema = {'config': {}}

        for profile in self.parents:
            parent_schema = profile.get_schema()
            self.merge_schema(schema, parent_schema)

        self.merge_schema(schema, self.data)

        for component in self.get_component_names('ensure_module_config'):
            if component in schema:
                for name, component_config in schema[component].items():
                    if '_module' not in component_config:
                        component_config['_module'] = self.module.instance.name

        for name, value in schema['config'].items():
            if not self.config.check(name):
                self.config.set(name, value)

        return schema

    def merge_schema(self, schema, data):
        for key, value in data.items():
            if isinstance(value, dict):
                schema.setdefault(key, {})
                self.merge_schema(schema[key], value)
            else:
                schema[key] = value


    def display_schema(self, operation):
        self.command.info('')
        self.process_components(operation, display_only = True)

        if self.include('profile'):
            component = self.manager.index.load_component(self, 'profile')
            profiles = self.expand_instances(component.name, self.data)

            for profile, config in profiles.items():
                if self.include_instance(profile, config):
                    getattr(component, operation)(profile, config, True)


    def run(self, components = None, config = None, display_only = False, test = False):
        self.command.data(
            "Running profile:",
            f"{self.module.instance.name}:{self.name}",
            'profile_name',
        )

        operation = 'run'

        self.initialize(config, components)
        if display_only:
            self.display_schema(operation)
        else:
            self.process_components(operation,
                extra_config = { 'test': test }
            )

    def destroy(self, components = None, config = None, display_only = False):
        self.command.data("Destroying profile:", "{}:{}".format(self.module.instance.name, self.name), 'profile_name')

        def remove_instance(instance_config):
            return not instance_config.get('_keep', False)

        operation = 'destroy'

        self.initialize(config, components)
        if display_only:
            self.display_schema(operation)
        else:
            self.process_components(operation, include_method = remove_instance)


    def process_components(self, operation, include_method = None, display_only = False, extra_config = None):
        component_map = self.manager.index.load_components(self)
        for priority, components in sorted(component_map.items()):
            def process(component):
                operation_method = getattr(component, operation, None)
                if callable(operation_method) and self.include(component.name):
                    if extra_config and isinstance(extra_config, dict):
                        for property, value in extra_config.items():
                            setattr(component, property, value)

                    self._process_component_instances(component,
                        component_method = operation_method,
                        include_method = include_method,
                        display_only = display_only
                    )
            self.command.run_list(components, process)


    def _process_component_instances(self, component, component_method, include_method = None, display_only = False):
        data = copy.deepcopy(self.data)
        requirements = Collection()
        processed = Collection()
        rendered_instances = OrderedDict() if display_only else None

        def get_wait_keys(_name):
            wait_keys = []
            if _name in requirements and requirements[_name]:
                for _child_name in flatten(ensure_list(requirements[_name])):
                    if processed[_child_name]:
                        wait_keys.extend(processed[_child_name])
                    wait_keys.extend(get_wait_keys(_child_name))

            return list(set(wait_keys))

        def check_include(config):
            return (
                include_method(self.interpolate_config_value(config))
                if callable(include_method)
                else True
            )

        def render_instance(name):
            instance_config = copy.deepcopy(data[component.name][name])
            name = self.interpolate_config_value(name)

            instance_config = self.interpolate_config_value(instance_config,
                config = 'query',
                config_value = False,
                function_suppress = '^\s*\<+[^\>]+\>+\s*$',
                conditional_suppress = '\s*\<+[^\>]+\>+\s*'
            )
            if self.include_instance(name, instance_config):
                if '_config' in instance_config:
                    instance_config = self.interpolate_config_value(instance_config,
                        function_suppress = '^\s*\<+[^\>]+\>+\s*$',
                        conditional_suppress = '\s*\<+[^\>]+\>+\s*'
                    )
                    component_method(name, instance_config)

                rendered_instances[name] = instance_config

        def process_instances(interpolate_references):
            instance_map = self.order_instances(self.expand_instances(component.name, data,
                interpolate_references = interpolate_references
            ))
            for priority, names in sorted(instance_map.items()):
                expansion = Collection()

                def process_instance(name):
                    instance_config = copy.deepcopy(data[component.name][name])
                    name = self.interpolate_config_value(name)

                    if self.include_instance(name, instance_config):
                        if (
                            isinstance(instance_config, dict)
                            and '_foreach' in instance_config
                        ):
                            expansion[priority] = True

                        if priority not in expansion and \
                                name not in processed and \
                                check_include(instance_config):

                            instance_config = self.interpolate_config_value(instance_config)

                            if isinstance(instance_config, dict):
                                requirements[name] = instance_config.pop('_requires', [])
                                if requirements[name]:
                                    instance_config['_wait_keys'] = get_wait_keys(name)

                            if settings.DEBUG_COMMAND_PROFILES:
                                self.command.info(yaml.dump(
                                    { name: instance_config },
                                    Dumper = noalias_dumper
                                ))
                            log_keys = component_method(name, instance_config)
                            processed[name] = ensure_list(log_keys) if log_keys else []

                if display_only:
                    self.command.run_list(names, render_instance)
                else:
                    self.command.run_list(names, process_instance)

                if not display_only and priority in expansion:
                    return process_instances(True)

        if display_only:
            process_instances(True)
            self.command.info(yaml.dump(
                { component.name: rendered_instances },
                Dumper = noalias_dumper
            ))
        else:
            process_instances(False)
            self.command.wait_for_tasks([ log_keys for name, log_keys in processed.export().items() ])


    def expand_instances(self, component_name, data = None, interpolate_references = True):
        instance_data = copy.deepcopy(self.data if data is None else data)
        instance_map = {}

        def get_replacements(info, replacements, keys = None):
            if keys is None:
                keys = []

            tag = ".".join(keys) if keys else 'value'

            if isinstance(info, dict):
                replacements["<<{}>>".format(tag)] = info
                replacements["<<>{}>>".format(tag)] = dump_json(info)
                for key, value in info.items():
                    get_replacements(value, replacements, keys + [str(key)])
            elif isinstance(info, (list, tuple)):
                replacements["<<{}>>".format(tag)] = info
                replacements["<<>{}>>".format(tag)] = dump_json(info)
                for index, value in enumerate(info):
                    get_replacements(value, replacements, keys + [str(index)])
            else:
                replacements["<<{}>>".format(tag)] = info

            return replacements

        def substitute_config(config, replacements):
            if isinstance(config, dict):
                config = copy.deepcopy(config)
                for key in list(config.keys()):
                    real_key = substitute_config(key, replacements)
                    real_value = substitute_config(config[key], replacements)

                    if isinstance(real_key, (dict, list, tuple)) or real_key != key:
                        config.pop(key, None)

                    if isinstance(real_key, dict):
                        for sub_key, sub_value in real_key.items():
                            config[sub_key] = sub_value if sub_value is not None else real_value
                    elif isinstance(real_key, (list, tuple)):
                        for sub_key in real_key:
                            config[sub_key] = real_value
                    else:
                        config[real_key] = real_value

            elif isinstance(config, (list, tuple)):
                config = copy.deepcopy(config)
                for index, value in enumerate(config):
                    config[index] = substitute_config(value, replacements)
            else:
                for token in replacements.keys():
                    if str(config) == token:
                        config = replacements[token]
                    else:
                        replacement = replacements[token]
                        if isinstance(replacements[token], (list, tuple, dict)):
                            replacement = dump_json(replacements[token])

                        if isinstance(config, str):
                            config = config.replace(token, str(replacement))

                if isinstance(config, str) and re.match(r'^\<\<.*\>\>$', config):
                    config = None
            return config

        for name, config in instance_data[component_name].items():
            if config and isinstance(config, dict):
                collection = config.get('_foreach', None)

                if collection and (interpolate_references or not isinstance(collection, str) or not collection.startswith('&')):
                    config.pop('_foreach')

                    collection = self.interpolate_config_value(collection)

                    if isinstance(collection, (list, tuple)):
                        for item in collection:
                            replacements = get_replacements(item, {})
                            new_name = self.interpolate_config_value(substitute_config(name, replacements))
                            instance_map[new_name] = substitute_config(config, replacements)

                    elif isinstance(collection, dict):
                        for key, item in collection.items():
                            replacements = get_replacements(item, {
                                "<<dict_key>>": key
                            })
                            new_name = self.interpolate_config_value(substitute_config(name, replacements))
                            instance_map[new_name] = substitute_config(config, replacements)
                    else:
                        self.command.error("Component instance expansions must be lists or dictionaries: {}".format(collection))
                else:
                    instance_map[name] = config
            else:
                instance_map[name] = config

        for name, config in instance_map.items():
            if data is None:
                self.data[component_name][name] = config
            else:
                data[component_name][name] = config

        return instance_map

    def order_instances(self, configs):
        for name, value in configs.items():
            if isinstance(value, dict) and '_requires' in value and value['_requires'] is not None:
                value['_requires'] = self.interpolate_config_value(value['_requires'])

        return prioritize(configs, keep_requires = True, requires_field = '_requires')


    def include(self, component, force = False, check_data = True):
        if component == 'profile' and 'profile' in self.data:
            return True

        if not force and self.components and component not in self.components:
            return False

        return not check_data or component in self.data

    def include_inner(self, component, force = False):
        return self.include(component,
            force = force,
            check_data = False
        )

    def include_instance(self, name, config):
        if isinstance(config, dict):
            when = config.pop('_when', None)
            when_not = config.pop('_when_not', None)
            when_in = config.pop('_when_in', None)
            when_not_in = config.pop('_when_not_in', None)
            when_type = config.pop('_when_type', 'AND').upper()

            if when is not None:
                result = when_type == 'AND'
                for variable in ensure_list(when):
                    value = format_value('bool', self.interpolate_config_value(variable))
                    if when_type == 'AND':
                        if not value:
                            return False
                    elif value:
                        result = True
                return result

            if when_not is not None:
                result = when_type == 'AND'
                for variable in ensure_list(when_not):
                    value = format_value('bool', self.interpolate_config_value(variable))
                    if when_type == 'AND':
                        if value:
                            return False
                    elif not value:
                        result = True
                return result

            if when_in is not None:
                value = self.interpolate_config_value(when_in)
                return name in ensure_list(value)

            if when_not_in is not None:
                value = self.interpolate_config_value(when_not_in)
                return name not in ensure_list(value)

        return True


    def get_variables(self, instance, variables = None):
        if not variables:
            variables = {}

        system_fields = [ x.name for x in instance.facade.system_field_instances ]

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            for name, value in instance.config.items():
                variables[name] = value

        for field in instance.facade.fields:
            value = getattr(instance, field)

            if not isinstance(value, BaseModel) and field[0] != '_' and field not in system_fields:
                variables[field] = value

        return clean_dict(variables)


    def get_instances(self, facade_name, excludes = None):
        if not excludes:
            excludes = []

        facade_index = self.manager.index.get_facade_index()
        excludes = ensure_list(excludes)
        return [
            instance
            for instance in self.command.get_instances(facade_index[facade_name])
            if not excludes or instance.name not in excludes
        ]

    def get_module(self, name):
        facade = self.command.facade(self.command._module)
        return self.command.get_instance(facade, name, required = False)


    def get_info(self, name, config, remove = True):
        return config.pop(name, None) if remove else config.get(name, None)

    def pop_info(self, name, config):
        return self.get_info(name, config, True)

    def get_value(self, name, config, remove = False):
        value = self.get_info(name, config, remove)
        if value is not None:
            value = self.interpolate_config_value(value)
        return value

    def pop_value(self, name, config):
        return self.get_value(name, config, True)

    def get_values(self, name, config, remove = False):
        value = self.get_value(name, config, remove)
        return ensure_list(value) if value is not None else []

    def pop_values(self, name, config):
        return self.get_values(name, config, True)


    def interpolate(self, config, replacements = None):
        if not replacements:
            replacements = {}

        def _interpolate(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    data[key] = _interpolate(value)
            elif isinstance(data, (list, tuple)):
                for index, value in enumerate(data):
                    data[index] = _interpolate(value)
            elif isinstance(data, str):
                data = re.sub(r"([\{\}])", r"\1\1", data)
                data = re.sub(r"\<([a-z][\_\-a-z0-9]+)\>", r"{\1}", data)
                data = data.format(**replacements)
            return data

        return _interpolate(copy.deepcopy(config)) if replacements else config
