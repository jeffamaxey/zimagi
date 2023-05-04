from collections import OrderedDict

from django.conf import settings

from systems.commands import args
from utility import text, data
from .meta import MetaBaseMixin

import re
import copy
import pandas


class BaseMixin(object, metaclass = MetaBaseMixin):

    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass


    def parse_flag(self, name, flag, help_text, tags = None):
        with self.option_lock:
            if name not in self.option_map:
                flag_default = self.options.get_default(name)

                if flag_default:
                    option_label = self.success_color(f"option_{name}")
                    help_text = f"{help_text} <{self.value_color('True')}>"
                else:
                    option_label = self.key_color(f"option_{name}")

                self.add_schema_field(
                    name,
                    args.parse_bool(
                        self.parser,
                        name,
                        flag,
                        f"[@{option_label}] {help_text}",
                        default=flag_default,
                    ),
                    optional=True,
                    tags=tags,
                )
                if flag_default is not None:
                    self.option_defaults[name] = flag_default

                self.option_map[name] = True

    def parse_variable(self, name, optional, type, help_text, value_label = None, default = None, choices = None, tags = None):
        with self.option_lock:
            if name not in self.option_map:
                variable_default = None

                if optional:
                    variable_default = self.options.get_default(name)
                    if variable_default is not None:
                        option_label = self.success_color(f"option_{name}")
                    else:
                        option_label = self.key_color(f"option_{name}")
                        variable_default = default

                    if variable_default is None:
                        default_label = ''
                    else:
                        default_label = f" <{self.value_color(variable_default)}>"

                    help_text = f"[@{option_label}] {help_text}{default_label}"

                if optional and isinstance(optional, (str, list, tuple)):
                    if not value_label:
                        value_label = name

                    self.add_schema_field(name,
                        args.parse_option(self.parser, name, optional, type, help_text,
                            value_label = value_label.upper(),
                            default = variable_default,
                            choices = choices
                        ),
                        optional = True,
                        tags = tags
                    )
                else:
                    self.add_schema_field(name,
                        args.parse_var(self.parser, name, type, help_text,
                            optional = optional,
                            default = variable_default,
                            choices = choices
                        ),
                        optional = optional,
                        tags = tags
                    )
                if variable_default is not None:
                    self.option_defaults[name] = variable_default

                self.option_map[name] = True

    def parse_variables(self, name, optional, type, help_text, value_label = None, default = None, tags = None):
        with self.option_lock:
            if name not in self.option_map:
                variable_default = None

                if optional:
                    variable_default = self.options.get_default(name)
                    if variable_default is not None:
                        option_label = self.success_color(f"option_{name}")
                    else:
                        option_label = self.key_color(f"option_{name}")
                        variable_default = default

                    if variable_default is None:
                        default_label = ''
                    else:
                        default_label = f' <{self.value_color(", ".join(data.ensure_list(variable_default)))}>'

                    help_text = f"[@{option_label}] {help_text}{default_label}"

                if optional and isinstance(optional, (str, list, tuple)):
                    help_text = f"{help_text} (comma separated)"

                    if not value_label:
                        value_label = name

                    self.add_schema_field(name,
                        args.parse_csv_option(self.parser, name, optional, type, help_text,
                            value_label = value_label.upper(),
                            default = variable_default
                        ),
                        optional = True,
                        tags = tags
                    )
                else:
                    self.add_schema_field(name,
                        args.parse_vars(self.parser, name, type, help_text,
                            optional = optional,
                            default = variable_default
                        ),
                        optional = optional,
                        tags = tags
                    )
                if variable_default is not None:
                    self.option_defaults[name] = variable_default

                self.option_map[name] = True

    def parse_fields(self, facade, name, optional = False, help_callback = None, callback_args = None, callback_options = None, exclude_fields = None, tags = None):
        with self.option_lock:
            if not callback_args:
                callback_args = []
            if not callback_options:
                callback_options = {}

            if exclude_fields:
                exclude_fields = data.ensure_list(exclude_fields)
                callback_options['exclude_fields'] = exclude_fields

            if name not in self.option_map:
                if facade:
                    help_text = "\n".join(self.field_help(facade, exclude_fields))
                else:
                    help_text = "\nfields as key value pairs\n"

                if help_callback and callable(help_callback):
                    help_text += "\n".join(help_callback(*callback_args, **callback_options))

                self.add_schema_field(name,
                    args.parse_key_values(self.parser, name, help_text,
                        value_label = 'field=VALUE',
                        optional = optional
                    ),
                    optional = optional,
                    tags = tags
                )
                self.option_map[name] = True


    def parse_test(self):
        self.parse_flag('test', '--test', 'test execution without permanent changes', tags = ['system'])

    @property
    def test(self):
        return self.options.get('test', False)


    def parse_force(self):
        self.parse_flag('force', '--force', 'force execution even with provider errors', tags = ['system'])

    @property
    def force(self):
        return self.options.get('force', False)


    def parse_count(self):
        self.parse_variable('count',
            '--count', int,
            'instance count (default 1)',
            value_label = 'COUNT',
            default = 1,
            tags = ['list', 'limit']
        )

    @property
    def count(self):
        return self.options.get('count', 1)


    def parse_clear(self):
        self.parse_flag('clear', '--clear', 'clear all items', tags = ['system'])

    @property
    def clear(self):
        return self.options.get('clear', False)


    def parse_search(self, optional = True, help_text = 'one or more search queries'):
        self.parse_variables('instance_search_query', optional, str, help_text,
            value_label = 'REFERENCE',
            tags = ['search']
        )
        self.parse_flag('instance_search_or', '--or', 'perform an OR query on input filters', tags = ['search'])

    @property
    def search_queries(self):
        return self.options.get('instance_search_query', [])

    @property
    def search_join(self):
        join_or = self.options.get('instance_search_or', False)
        return 'OR' if join_or else 'AND'


    def parse_scope(self, facade):
        for name in facade.scope_parents:
            getattr(self, f"parse_{name}_name")(
                f"--{name.replace('_', '-')}", tags=['scope']
            )

    def set_scope(self, facade, optional = False):
        filters = {}
        for name in OrderedDict.fromkeys(facade.scope_parents).keys():
            instance_name = getattr(self, f"{name}_name", None)
            if optional and not instance_name:
                name = None

            if name and name in facade.fields:
                sub_facade = getattr(self, f"_{facade.get_subfacade(name).name}")
                if facade.name != sub_facade.name:
                    self.set_scope(sub_facade, optional)
                else:
                    sub_facade.set_scope(filters)

                if instance_name:
                    if instance := self.get_instance(
                        sub_facade, instance_name, required=not optional
                    ):
                        filters[f"{name}_id"] = instance.get_id()
                    elif not optional:
                        self.error(f"{facade.name.title()} {instance_name} does not exist")

        facade.set_scope(filters)
        return filters

    def get_scope_filters(self, instance):
        facade = instance.facade
        return {
            f"{name}_name": value
            for name, value in facade.get_scope_filters(instance).items()
        }


    def parse_relations(self, facade):
        for field_name, info in facade.get_relations().items():
            option_name = f"--{field_name.replace('_', '-')}"

            if info['multiple']:
                method_name = f"parse_{field_name}_names"
            else:
                method_name = f"parse_{field_name}_name"

            getattr(self, method_name)(option_name, tags = ['relation'])

    def get_relations(self, facade):
        relations = {}
        for field_name, info in facade.get_relations().items():
            base_name = info['model'].facade.name

            if sub_facade := getattr(self, f"_{base_name}", None):
                self.set_scope(sub_facade, True)

            if info['multiple']:
                accessor_name = f"{field_name}_names"
            else:
                accessor_name = f"{field_name}_name"

            if getattr(self, f"check_{accessor_name}")():
                relations[field_name] = getattr(self, accessor_name, None)

        return relations


    def check_available(self, facade, name, warn = False):
        if instance := self.get_instance(facade, name, required=False):
            if warn:
                self.warning(f"{facade.name.title()} {name} already exists")
            return False
        return True

    def check_exists(self, facade, name, warn = False):
        instance = self.get_instance(facade, name, required = False)
        if not instance:
            if warn:
                self.warning(f"{facade.name.title()} {name} does not exist")
            return False
        return True


    def get_instance_by_id(self, facade, id, required = True):
        instance = facade.retrieve_by_id(id)

        if not instance and required:
            self.error(f"{facade.name.title()} {id} does not exist")
        elif instance and instance.initialize(self):
            return instance
        return None

    def get_instance(self, facade, name, required = True):
        instance = self._get_cache_instance(facade, name)

        if not instance:
            instance = facade.retrieve(name)

            if not instance and required:
                self.error(f"{facade.name.title()} {name} does not exist")
            elif instance and instance.initialize(self):
                self._set_cache_instance(facade, name, instance)
            else:
                return None

        return instance


    def get_instances(self, facade,
        names = [],
        objects = [],
        groups = [],
        fields = {}
    ):
        search_items = []
        results = {}

        if not names and not groups and not objects and not fields:
            search_items = facade.all()
        else:
            search_items.extend(data.ensure_list(names))
            search_items.extend(data.ensure_list(objects))

            for group in data.ensure_list(groups):
                search_items.extend(facade.keys(groups__name = group))

        def init_instance(object):
            if isinstance(object, str):
                cached = self._get_cache_instance(facade, object)
                instance = cached if cached else facade.retrieve(object)
            else:
                instance = object
                cached = self._get_cache_instance(facade, getattr(instance, facade.pk))

            if instance:
                id = getattr(instance, facade.pk)
                if not cached:
                    if instance.initialize(self):
                        self._set_cache_instance(facade, id, instance)
                    else:
                        instance = None
                else:
                    instance = cached

                if instance:
                    if fields:
                        for field, values in fields.items():
                            values = data.normalize_value(values)
                            value = getattr(instance, field, None)
                            if isinstance(values, str) and not value and re.match(r'^(none|null)$', values, re.IGNORECASE):
                                results[id] = instance
                            elif value and value in data.ensure_list(values):
                                results[id] = instance
                    else:
                        results[id] = instance
            else:
                self.error("{} instance {} does not exist".format(facade.name.title(), object))

        self.run_list(search_items, init_instance)
        return results.values()


    def search_instances(self, facade, queries = None, joiner = 'AND', error_on_empty = True):
        if not queries:
            queries = []

        valid_fields = facade.query_fields
        queries = data.ensure_list(queries)
        joiner = joiner.upper()
        results = {}

        def perform_query(filters, excludes, fields):
            instances = facade.query(**filters).exclude(**excludes)
            if len(instances) > 0:
                for instance in self.get_instances(facade,
                    objects = list(instances),
                    fields = fields
                ):
                    results[getattr(instance, facade.pk)] = instance

        if queries:
            filters = {}
            excludes = {}
            extra = {}

            for query in queries:
                matches = re.search(r'^([\~\-])?([^\s\=]+)\s*(?:(\=|[^\s]*))\s*(.*)', query)

                if matches:
                    negate = bool(matches[1])
                    field = matches[2].strip()
                    field_list = re.split(r'\.|__', field)

                    lookup = matches[3]
                    if not lookup and len(field_list) > 1:
                        lookup = field_list.pop()

                    value = re.sub(r'^[\'\"]|[\'\"]$', '', matches[4].strip())

                    if not lookup and not value:
                        value = field
                        lookup = '='
                        field_list[0] = facade.key()

                    base_field = field_list[0]
                    field_path = "__".join(field_list)
                    if lookup != '=':
                        field_path = "{}__{}".format(field_path, lookup)

                    value = data.normalize_value(value, strip_quotes = False, parse_json = True)

                    if joiner.upper() == 'OR':
                        filters = {}
                        excludes = {}
                        extra = {}

                    if base_field in valid_fields:
                        if negate:
                            excludes[field_path] = value
                        else:
                            filters[field_path] = value
                    else:
                        extra[field_path] = value

                    if joiner == 'OR':
                        perform_query(filters, excludes, extra)
                else:
                    self.error("Search filter must be of the format: field[.subfield][.lookup] [=] value".format(query))

            if joiner == 'AND':
                perform_query(filters, excludes, extra)
        else:
            for instance in self.get_instances(facade):
                results[getattr(instance, facade.pk)] = instance

        if error_on_empty and not results:
            if queries:
                self.warning("No {} instances were found: {}".format(facade.name, ", ".join(queries)))
            else:
                self.warning("No {} instances were found".format(facade.name))

        return results.values()


    def facade(self, facade, use_cache = True):
        result = None

        if use_cache and getattr(self, '_facade_cache', None) is None:
            self._facade_cache = {}

        if not isinstance(facade, str):
            name = facade.name
        else:
            name = facade
            facade = self.manager.index.get_facade_index()[name]

        if use_cache and not self._facade_cache.get(name, None):
            self._facade_cache[name] = copy.deepcopy(facade)
        else:
            result = copy.deepcopy(facade)

        return self._facade_cache[name] if use_cache else result


    def get_data_set(self, data_type, *fields,
        filters = None,
        limit = 0,
        order = None,
        dataframe = False,
        dataframe_index_field = None,
        dataframe_merge_fields = None,
        dataframe_remove_fields = None,
        time_index = False
    ):
        processor_separator = '<'
        fields = list(fields)
        aggregates = []
        removals = []

        for index, field in enumerate(fields):
            fields[index] = "".join(field.split())

        def parse_annotations():
            annotations = {}

            for index, field in enumerate(fields):
                field_components = field.split(processor_separator)
                processor = field_components[1] if len(field_components) > 1 else None
                field_components = field_components[0].split(':')

                if len(field_components) > 1:
                    try:
                        field_name = field_components[0]
                        aggregator = field_components[1]
                        expression = field_components[2]
                        aggregator_options = {}

                        if len(field_components) == 4:
                            for assignment in field_components[3].split(';'):
                                name, value = assignment.split('=')
                                aggregator_options[name] = data.normalize_value(value, True)

                        annotations[field_name] = [ aggregator, expression, aggregator_options ]
                        fields[index] = "{}{}{}".format(field_name, processor_separator, processor) if processor else field_name
                        aggregates.append(field_name)

                    except Exception as e:
                        self.error("When passing aggregators as fields to get_data_set format must be field_name:GROUP_FUNC:expression[:option=value[,...]]")

            return annotations

        def collect_fields():
            expanded_fields = OrderedDict()

            for field in fields:
                field_components = field.split(processor_separator)
                if len(field_components) > 1:
                    field = field_components[0]
                    processor_components = field_components[1].split(':')
                    processor_info = {
                        'processor': processor_components[0],
                        'options': {}
                    }
                    if len(processor_components) > 1:
                        processor_info['field'] = processor_components[1]

                        if processor_info['field'] not in expanded_fields:
                            expanded_fields[processor_info['field']] = {}
                            removals.append(processor_info['field'])

                        if len(processor_components) == 3:
                            processor_options = {}
                            for assignment in processor_components[2].split(';'):
                                name, value = assignment.split('=')
                                processor_options[name] = data.normalize_value(value, True)

                            processor_info['options'] = processor_options
                    else:
                        processor_info['field'] = field

                    expanded_fields[field] = processor_info
                else:
                    expanded_fields[field] = {}

            return expanded_fields

        def get_query_fields(field_info):
            local_fields = []
            for field in field_info.keys():
                if '__' in field or field in facade.fields or field in aggregates:
                    local_fields.append(field)
            return local_fields

        def get_merge_values(merge_filters):
            values = []
            for merge_field in data.ensure_list(dataframe_merge_fields):
                values.append(re.sub(r'[^a-z0-9]+', '', str(merge_filters[merge_field]).lower()))
            return values

        def get_dataframe(field_info, local_filters):
            dataframe = facade.dataframe(*get_query_fields(field_info), **local_filters)

            for field, info in field_info.items():
                if info:
                    function = self.get_provider('field_processor', info['processor'])
                    dataframe[field] = function.exec(dataframe, dataframe[info['field']], **info['options'])

            if dataframe_index_field:
                if time_index:
                    dataframe[dataframe_index_field] = pandas.to_datetime(dataframe[dataframe_index_field], utc = True)
                    dataframe[dataframe_index_field] = dataframe[dataframe_index_field].dt.tz_convert(settings.TIME_ZONE)

                dataframe.set_index(dataframe_index_field, inplace = True, drop = True)

            if removals or dataframe_remove_fields:
                for field in removals + list(dataframe_remove_fields or []):
                    if field in dataframe.columns:
                        dataframe.drop(field, axis = 1, inplace = True)

            return dataframe

        def get_merged_dataframe(field_info):
            merge_fields = data.ensure_list(dataframe_merge_fields)
            merge_filter_index = {}
            dataframe = None

            for merge_filters in list(facade.values(*merge_fields, **filters)):
                merge_values = get_merge_values(merge_filters)
                merge_filter_id = data.get_identifier(merge_values)

                if merge_filter_id not in merge_filter_index:
                    sub_dataframe = get_dataframe(field_info, {**filters, **merge_filters})

                    value_prefix = "_".join(merge_values)
                    sub_dataframe.columns = ["{}_{}".format(value_prefix, column) for column in sub_dataframe.columns]

                    if dataframe is None:
                        dataframe = sub_dataframe
                    else:
                        dataframe = dataframe.merge(sub_dataframe, how = "outer", left_index = True, right_index = True)

                    merge_filter_index[merge_filter_id] = True

            return dataframe

        facade = self.facade(data_type, False)
        facade.set_limit(limit)
        facade.set_order(order)
        facade.set_annotations(**parse_annotations())

        field_info = collect_fields()

        if filters is None:
            filters = {}

        if dataframe and dataframe_index_field and dataframe_merge_fields:
            return get_merged_dataframe(field_info)

        records = get_dataframe(field_info, filters)
        return records if dataframe else records.to_dict('records')


    def get_data_item(self, data_type, *fields,
        filters = None,
        order = None,
        dataframe = False,
        dataframe_index_field = None,
        dataframe_merge_fields = None,
        dataframe_remove_fields = None,
        time_index = False
    ):
        return self.get_data_set(data_type, *fields,
            filters = filters,
            order = order,
            limit = 1,
            dataframe = dataframe,
            dataframe_index_field = dataframe_index_field,
            dataframe_merge_fields = dataframe_merge_fields,
            dataframe_remove_fields = dataframe_remove_fields,
            time_index = time_index
        )


    def field_help(self, facade, exclude_fields = None):
        field_index = facade.field_index
        system_fields = [ x.name for x in facade.system_field_instances ]

        if facade.name == 'user':
            system_fields.extend(['last_login', 'password']) # User abstract model exceptions

        lines = ["fields as key value pairs", '', "-" * 40, 'model requirements:']

        for name in facade.required:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace('Field', '').lower()
                if field_label == 'char':
                    field_label = 'string'

                choices = []
                if field.choices:
                    choices = [ self.value_color(x[0]) for x in field.choices ]

                lines.append(
                    f"""    {self.warning_color(field.name)} {field_label}{':> ' + ", ".join(choices) if choices else ''}"""
                )
                if field.help_text:
                    lines.extend(('',
                        "       - {}".format(
                            "\n".join(text.wrap(field.help_text, 40,
                                indent = "         "
                            ))
                        ),
                    ))
        lines.extend(('', 'model options:'))
        for name in facade.optional:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace('Field', '').lower()
                if field_label == 'char':
                    field_label = 'string'

                choices = []
                if field.choices:
                    choices = [ self.value_color(x[0]) for x in field.choices ]

                default = facade.get_field_default(field)

                if default is not None:
                    lines.append(
                        f"""    {self.warning_color(field.name)} {field_label} ({self.value_color(default)}){':> ' + ", ".join(choices) if choices else ''}"""
                    )
                else:
                    lines.append(
                        f"""    {self.warning_color(field.name)} {field_label} {':> ' + ", ".join(choices) if choices else ''}"""
                    )

                if field.help_text:
                    lines.extend(('',
                        "       - {}".format(
                            "\n".join(text.wrap(field.help_text, 40,
                                indent = "         "
                            ))
                        ),
                    ))
        lines.append('')
        return lines


    def _init_instance_cache(self, facade):
        cache_variable = f"_data_{facade.name}_cache"

        if not getattr(self, cache_variable, None):
            setattr(self, cache_variable, {})

        return cache_variable

    def _get_cache_instance(self, facade, name):
        cache_variable = self._init_instance_cache(facade)
        return getattr(self, cache_variable).get(name, None)

    def _set_cache_instance(self, facade, name, instance):
        cache_variable = self._init_instance_cache(facade)
        getattr(self, cache_variable)[name] = instance
