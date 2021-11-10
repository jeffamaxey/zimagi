from functools import lru_cache

from plugins import base
from systems.models.base import BaseModel
from utility import query, data

import datetime
import copy
import re


class DataProviderState(object):

    def __init__(self, data):
        if isinstance(data, DataProviderState):
            self.state = data.export()
        else:
            self.state = copy.deepcopy(data) if isinstance(data, dict) else {}

    def export(self):
        return copy.deepcopy(self.state)

    def get_value(self, data, *keys):
        if isinstance(data, (dict, list, tuple)):
            name = keys[0]
            keys = keys[1:] if len(keys) > 1 else []
            value = data.get(name, None)

            if not len(keys):
                return value
            else:
                return self.get_value(value, *keys)

        return None

    def get(self, *keys):
        return self.get_value(self.state, *keys)

    @property
    def variables(self):
        return {}


class BasePlugin(base.BasePlugin):

    @classmethod
    def generate(cls, plugin, generator):
        super().generate(plugin, generator)

        def facade(self):
            if getattr(generator, 'provider', False):
                parent_name = generator.get_parent().spec['data']
                data_name = "{}_{}".format(parent_name, generator.provider)
            else:
                data_name = generator.spec['data']

            return self.command.facade(data_name)

        def store_lock_id(self):
            return generator.spec['store_lock']

        def related_values(self):
            values = super(plugin, self).related_values
            for variable, variable_info in generator.spec['related_values'].items():
                values[variable] = variable_info
            return values

        def output_map(self):
            field_map = super(plugin, self).output_map
            for variable, field_name in generator.spec['output_map'].items():
                field_map[variable] = field_name
            return field_map

        if generator.spec.get('data', None):
            plugin.facade = property(facade)

        if generator.spec.get('related_values', None):
            plugin.related_values = property(related_values)

        if generator.spec.get('output_map', None):
            plugin.output_map = property(output_map)

        if generator.spec.get('store_lock', None):
            plugin.store_lock_id = store_lock_id


    def __init__(self, type, name, command, instance = None):
        super().__init__(type, name, command)
        self.instance = instance

    def check_instance(self, op):
        if not self.instance:
            self.command.error("Provider {} operation '{}' requires a valid model instance given to provider on initialization".format(self.name, op))
        return self.instance


    @property
    def facade(self):
        # Override in subclass
        return None

    @property
    def related_values(self):
        # Override in subclass
        return {}

    @property
    def output_map(self):
        # Override in subclass
        return {}


    def provider_state(self):
        return DataProviderState


    def get(self, name, required = True):
        instance = self.command.get_instance(self.facade, name, required = required)
        if getattr(instance, 'state_config', None):
            instance.state_config = self.provider_state()(instance.state_config)

    def get_variables(self, instance, standardize = False, recurse = True, parents = None):
        variables = {}

        if parents is None:
            parents = []

        instance.initialize(self.command)

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            for name, value in instance.config.items():
                variables[name] = value

        if getattr(instance, 'variables', None) and isinstance(instance.variables, dict):
            for name, value in instance.variables.items():
                variables[name] = value

        for field_name in instance.facade.fields:
            value = getattr(instance, field_name)

            if field_name[0] != '_' and field_name not in ('config', 'variables', 'state_config'):
                variables[field_name] = value

            if value and isinstance(value, datetime.datetime):
                variables[field_name] = value.strftime("%Y-%m-%d %H:%M:%S %Z")

        for field_name, value in variables.items():
            if isinstance(value, BaseModel):
                if recurse:
                    variables[field_name] = self.get_variables(value, standardize)
                else:
                    variables[field_name] = getattr(value, value.facade.key())

            elif isinstance(value, (list, tuple)):
                model_list = False
                for index, item in enumerate(value):
                    if isinstance(item, BaseModel):
                        model_list = True
                        if recurse:
                            value[index] = self.get_variables(item, standardize, False)
                        else:
                            value[index] = getattr(item, item.facade.key())

                if standardize and model_list:
                    self.standardize_list_variables(value)

        if instance.id not in parents:
            parents.append(instance.id)

            for variable, elements in self.get_related_variables(instance, standardize, parents).items():
                if variable not in variables:
                    if standardize and isinstance(elements, (list, tuple)):
                        self.standardize_list_variables(elements)
                    variables[variable] = elements

        return variables

    def get_related_variables(self, instance, standardize = False, parents = None):
        relation_values = self.command.get_relations(instance.facade)
        variables = {}

        if parents is None:
            parents = []

        for field_name, relation_info in instance.facade.get_relations().items():
            variables[field_name] = []
            related_instances = self.get_instance_values(
                relation_values.get(field_name, None),
                getattr(instance, field_name),
                self.command.facade(relation_info['model'].facade)
            )
            for related_instance in related_instances:
                variables[field_name].append(self.get_variables(related_instance, standardize, False, parents))

        return variables


    def get_related_values(self, instance, field_name, variable = None):
        related_field = self.get_related_variables(instance).get(field_name, None)

        if variable:
            values = []
            for related in data.ensure_list(related_field):
                if isinstance(variable, (list, tuple)):
                    value = related
                    for element in variable:
                        value = value[element]
                else:
                    value = related[variable]

                values.append(value)
        else:
            values = related_field

        return values


    def get_instance_values(self, names, relations, facade):
        instances = []

        if names:
            self.command.set_scope(facade)
            for instance in self.command.get_instances(facade, names = names):
                instances.append(instance)
        elif relations and getattr(relations, 'all', None):
            for instance in relations.all():
                instances.append(instance)
        elif isinstance(relations, BaseModel):
            instances.append(relations)

        return instances


    def standardize_list_variables(self, elements):
        element_values = {}
        mixed_values = []

        for item in elements:
            for key in item.keys():
                element_values.setdefault(key, [])
                element_values[key].append(type(item[key]))

        for key, types in element_values.items():
            if len(set(types)) > 1:
                mixed_values.append(key)

        for index, item in enumerate(elements):
            for key in mixed_values:
                item.pop(key)


    def initialize_instances(self):
        # Override in subclass
        pass

    def preprocess_fields(self, fields, instance = None):
        # Override in subclass
        return fields

    def initialize_instance(self, instance, created):
        # Override in subclass
        pass

    def prepare_instance(self, instance, created):
        # Override in subclass
        pass

    def store_related(self, instance, created, test):
        # Override in subclass
        pass

    def finalize_instance(self, instance):
        # Override in subclass
        pass


    def generate_name(self, prefix, state_variable):
        name_index = int(self.command.get_state(state_variable, 0)) + 1
        self.command.set_state(state_variable, name_index)
        return "{}{}".format(prefix, name_index)


    def _init_config(self, fields, create = True):
        self.create_op = create
        self.config = copy.copy(fields)
        self.provider_config()
        self.validate()


    def store_lock_id(self):
        # Override in subclass
        return None

    def store(self, reference, fields, **relations):
        instance = None
        model_fields = {}
        provider_fields = {}
        created = False

        if reference is not None:
            if isinstance(reference, BaseModel):
                instance = reference
            else:
                instance = self.facade.retrieve(reference)

        if not instance:
            fields = { **self.config, **fields }

        fields['provider_type'] = self.name

        for field, value in fields.items():
            if field in self.facade.fields:
                if fields[field] is not None:
                    model_fields[field] = fields[field]
            else:
                provider_fields[field] = fields[field]

        if not instance:
            instance = self.facade.create(reference, **model_fields)
            created = True
        else:
            for field, value in model_fields.items():
                setattr(instance, field, value)

        instance.config = { **instance.config, **provider_fields }

        for variable, variable_info in self.related_values.items():
            if 'field' not in variable_info:
                self.command.error("Options 'field' required and 'lookup' optional for plugin provider 'related_values' specification")

            instance.config[variable] = self.get_related_values(instance,
                variable_info['field'],
                variable_info.get('lookup', None)
            )

        def process():
            self.initialize_instance(instance, created)

            if self.test:
                self.store_related(instance, created, True)
                self.command.success("Test complete")
            else:
                try:
                    if getattr(instance, 'variables', None) is not None:
                        instance.variables = self._collect_variables(instance, instance.variables)

                    for variable, field_name in self.output_map.items():
                        if instance.variables.get(variable, None) is not None:
                            object = instance
                            if isinstance(field_name, (list, tuple)):
                                field_elements = field_name[:-1]
                                field_name = field_name[-1]

                                for element in field_elements:
                                    if isinstance(object, (list, tuple, dict)):
                                        object = object[element]
                                    else:
                                        object = getattr(object, element)

                            if isinstance(object, dict):
                                object[field_name] = instance.variables[variable]
                            else:
                                setattr(object, field_name, instance.variables[variable])

                    self.prepare_instance(instance, created)
                    instance.save()

                except Exception as e:
                    if created:
                        self.command.info("Save failed, now reverting any associated resources...")
                        self.finalize_instance(instance)
                    raise e

                instance.save_related(self, relations)
                self.store_related(instance, created, False)
                self.command.success("Successfully saved {} {}".format(self.facade.name, getattr(instance, instance.facade.key())))

        self.run_exclusive(self.store_lock_id(), process)
        return instance


    def create(self, name, fields = None):
        if not fields:
            fields = {}

        if self.command.check_available(self.facade, name):
            fields = self.preprocess_fields(data.normalize_dict(fields))
            self._init_config(fields, True)
            return self.store(name, fields)
        else:
            self.command.error("Instance {} already exists".format(name))

    def update(self, fields = None):
        if not fields:
            fields = {}

        instance = self.check_instance('instance update')

        fields = self.preprocess_fields(data.normalize_dict(fields), instance)
        self._init_config(fields, False)
        return self.store(instance, fields)


    def delete_lock_id(self):
        # Override in subclass
        return None

    def delete(self, force = False):
        instance = self.check_instance('instance delete')
        instance_key = getattr(instance, instance.facade.key())

        options = self.command.get_scope_filters(instance)
        options['force'] = force

        def remove_child(child):
            sub_facade = self.manager.index.get_facade_index()[child]

            if getattr(sub_facade.meta, 'command_base', None) is not None:
                command_base = sub_facade.meta.command_base
            else:
                command_base = child.replace('_', ' ')

            if command_base:
                clear_options = {**options, "{}_name".format(self.facade.name): instance_key}
                self.command.exec_local("{} clear".format(command_base), clear_options)

        def process():
            if self.facade.keep(instance_key):
                self.command.error("Removal of {} {} is restricted (has dependencies)".format(self.facade.name, instance_key))

            for child in self.facade.get_children(False, 'pre'):
                if child not in ('module', 'group', 'state', 'config', 'log', 'user'):
                    remove_child(child)
            try:
                self.finalize_instance(instance)
            except Exception as e:
                if not force:
                    raise e

            for child in self.facade.get_children(False, 'post'):
                remove_child(child)

            if self.facade.delete(instance_key):
                self.command.success("Successfully deleted {} {}".format(self.facade.name, instance_key))
            else:
                self.command.error("{} {} deletion failed".format(self.facade.name.title(), instance_key))

        self.run_exclusive(self.delete_lock_id(), process)


    def add_related(self, instance, relation, facade, names, **fields):
        for field in fields.keys():
            if field not in facade.fields:
                self.command.error("Given field {} is not in {}".format(field, facade.name))

        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            for name in names:
                sub_instance = self.command.get_instance(facade, name, required = False)

                if not sub_instance:
                    provider_type = fields.pop('provider_type', 'base')
                    provider = self.command.get_provider(facade.provider_name, provider_type)
                    sub_instance = provider.create(name, fields)
                elif fields:
                    sub_instance.provider.update(name, fields)

                if sub_instance:
                    try:
                        with facade.thread_lock:
                            queryset.add(sub_instance)
                    except Exception as e:
                        self.command.error("{} add failed: {}".format(facade.name.title(), str(e)))

                    self.command.success("Successfully added {} {} to {} {}".format(sub_instance.facade.name, name, instance.facade.name, str(instance)))
                else:
                    self.command.error("{} {} creation failed".format(facade.name.title(), name))
        else:
            self.command.error("There is no relation {} on {} class".format(relation, instance_name))

    def remove_related(self, instance, relation, facade, names):
        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        key = getattr(instance, instance.facade.key())
        keep_index = instance.facade.keep_relations().get(relation, {})
        keep = data.ensure_list(keep_index.get(key, []))

        if queryset:
            for name in names:
                if name not in keep:
                    sub_instance = facade.retrieve(name)

                    if sub_instance:
                        try:
                            with facade.thread_lock:
                                queryset.remove(sub_instance)
                        except Exception as e:
                            self.command.error("{} remove failed: {}".format(facade.name.title(), str(e)))

                        self.command.success("Successfully removed {} {} from {} {}".format(sub_instance.facade.name, name, instance.facade.name, key))
                    else:
                        self.command.warning("{} {} does not exist".format(facade.name.title(), name))
                else:
                    self.command.error("{} {} removal from {} is restricted".format(facade.name.title(), name, key))
        else:
            self.command.error("There is no relation {} on {} class".format(relation, instance_name))

    def update_related(self, instance, relation, facade, names, **fields):
        queryset = query.get_queryset(instance, relation)

        if names is None:
            if queryset:
                queryset.clear()
            else:
                self.command.error("Instance {} relation {} is not a valid queryset".format(getattr(instance, instance.facade.key()), relation))
        else:
            all_names = []
            input_names = []
            add_names = []
            remove_names = []

            if queryset:
                sub_key = facade.key()
                for sub_instance in queryset.all():
                    all_names.append(getattr(sub_instance, sub_key))

            for name in names:
                if name.startswith('+'):
                    add_names.append(name[1:])
                elif name.startswith('-'):
                    remove_names.append(name[1:])
                else:
                    input_names.append(name)

            if input_names:
                remove_names = list(set(all_names) - set(input_names))
                add_names = input_names

            if add_names:
                self.add_related(
                    instance, relation,
                    facade,
                    add_names,
                    **fields
                )
            if remove_names:
                self.remove_related(
                    instance, relation,
                    facade,
                    remove_names
                )

    def set_related(self, instance, relation, facade, value, **fields):
        if value is None:
            setattr(instance, relation, None)
        else:
            if isinstance(value, str):
                if re.match(r'(none|null)', value, re.IGNORECASE):
                    setattr(instance, relation, None)
                else:
                    sub_instance = self.command.get_instance(facade, value, required = False)

                    if not sub_instance:
                        provider_type = fields.pop('provider_type', 'base')
                        provider = self.command.get_provider(facade.provider_name, provider_type)
                        sub_instance = provider.create(value, fields)
                    elif fields:
                        sub_instance.provider.update(fields)

                    if sub_instance:
                        setattr(instance, relation, sub_instance)
                        self.command.success("Successfully added {} {} to {} {}".format(sub_instance.facade.name, value, instance.facade.name, str(instance)))
                    else:
                        self.command.error("{} {} creation failed".format(facade.name.title(), value))
            else:
                setattr(instance, relation, value)

        instance.save()


    def _collect_variables(self, instance, variables = None):
        collected_variables = {}
        if not variables:
            variables = {}

        for variable, value in variables.items():
            collected_variables[variable] = value

        if getattr(instance, 'state_config', None) is not None:
            state = self.provider_state()(instance.state_config)
            for variable, value in state.variables.items():
                collected_variables[variable] = value
        return collected_variables


    def _get_field_info(self, fields):
        field_names = []
        field_labels = []

        for field in fields:
            if isinstance(field, (list, tuple)):
                field_names.append(field[0])
                field_labels.append(field[1])
            else:
                field_names.append(field)
                field_labels.append(field)

        return (field_names, field_labels)

    def _get_field_labels(self, processed_fields, existing_fields, labels):
        for index, value in enumerate(processed_fields):
            try:
                existing_index = existing_fields.index(value)
                processed_fields[index] = labels[existing_index]
            except Exception as e:
                pass

        return processed_fields
