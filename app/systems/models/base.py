from django.conf import settings
from django.db import models as django
from django.db.models.base import ModelBase
from django.utils.timezone import now

from .index import get_spec_key, get_stored_class_name, check_dynamic, get_dynamic_class_name, get_facade_class_name
from .facade import ModelFacade
from utility.mutex import check_mutex, MutexError, MutexTimeoutError

import importlib
import copy
import time
import logging


logger = logging.getLogger(__name__)


django.options.DEFAULT_NAMES += (
    'data_name',
    'scope',
    'scope_process',
    'dynamic_fields',
    'provider_name',
    'provider_relation',
    'command_base'
)


_base_model_new = ModelBase.__new__

def _override_model_new(cls, name, bases, attrs, **kwargs):
    orig_attrs = copy.copy(attrs)
    try:
        return _base_model_new(cls, name, bases, attrs, **kwargs)
    except RuntimeError as e:
        for key, value in orig_attrs.items():
            attrs[key] = value

        if 'Meta' in attrs:
            attrs['Meta'].abstract = True
        else:
            attrs['Meta'] = type('Meta', (object,), {
                'abstract': True
            })
        logger.info(
            f"Converting model {name} to an abstract object because it is not in INSTALLED_APPS"
        )
        return _base_model_new(cls, name, bases, attrs, **kwargs)

ModelBase.__new__ = _override_model_new


def format_field_choices(choices):
    choice_list = []
    if isinstance(choices, (list, tuple)):
        for choice in choices:
            if isinstance(choice, (list, tuple)):
                choice_list.append(tuple(choice))
            else:
                choice_list.append((choice, choice))
    else:
        choice_list.extend((value, label) for value, label in choices.items())
    return choice_list


def model_index():
    return settings.MANAGER.index

def classify_parents(parent_classes):
    map = {}
    for parent in parent_classes:
        try:
            key = get_spec_key(parent.__module__)
        except Exception as e:
            key = 'base'

        map.setdefault(key, [])
        map[key].append(parent)
    return map

def classify_model(model_class_name):
    if module_name := model_index().model_class_path.get(
        model_class_name, None
    ):
        return get_spec_key(module_name)
    return 'unknown'


class DatabaseAccessError(Exception):
    pass

class FacadeNotExistsError(Exception):
    pass


class BaseModelMixin(django.Model):

    created = django.DateTimeField(null = True, editable = False)
    updated = django.DateTimeField(null = True, editable = False)


    class Meta:
        abstract = True


    def initialize(self, command):
        return True


    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = now()
        self.updated = now()

        super().save(*args, **kwargs)

    def save_related(self, provider, relation_values = None):
        if not relation_values:
            relation_values = {}

        relations = self.facade.get_relations()
        relation_values = {
            **provider.command.get_relations(self.facade),
            **relation_values
        }
        for field, value in relation_values.items():
            facade = provider.command.facade(
                relations[field]['model'].facade.name
            )
            if relations[field]['multiple']:
                provider.update_related(self, field, facade, value)
            else:
                provider.set_related(self, field, facade, value)

    @property
    def facade(self):
        return copy.deepcopy(self.__class__.facade)


    def run_transaction(self, transaction_id, callback):
        transaction_id = f"model-transaction-{self.facade.name}-{transaction_id}"
        while True:
            try:
                with check_mutex(transaction_id):
                    callback()
                    break

            except (MutexError, MutexTimeoutError) as error:
                logger.debug(f"Failed to acquire transaction lock {transaction_id}: {error}")

            time.sleep(0.1)


class BaseMetaModel(ModelBase):

    def __new__(cls, name, bases, attrs, **kwargs):
        spec_key = classify_model(name)
        parent_map = classify_parents(bases)
        meta_info = attrs.get('_meta_info', {})
        meta_bases = []

        logger.info(f"++++ Creating new model: {name} <{spec_key}> {bases}")
        for field, value in meta_info.items():
            logger.debug(f" init meta > {field} - {value}")

        for key in ('data', 'data_mixins', 'data_base', 'base'):
            for parent in parent_map.get(key, []):
                if key in ('base', 'data_base') and getattr(parent, 'Meta', None):
                    meta_bases.append(parent.Meta)

                for field, value in getattr(parent, '_meta_info', {}).items():
                    if field[0] != '_' and field not in ('abstract', 'db_table'):
                        meta_info.setdefault(field, value)

        meta_info['abstract'] = bool(spec_key != 'data' or check_dynamic(name))
        if not meta_info['abstract']:
            spec = model_index().spec['data'][meta_info['data_name']]
            app_name = spec.get('app', meta_info['data_name'])
            data_info = model_index().module_map['data'][app_name]
            meta_info[
                'db_table'
            ] = f"{data_info.module.replace('-', '_')}_{meta_info['data_name']}"

        attrs['Meta'] = type('Meta', tuple(meta_bases), meta_info)

        for field in dir(attrs['Meta']):
            if field[0] != '_':
                logger.debug(f" final meta > {field} - {getattr(attrs['Meta'], field)}")

        return super().__new__(cls, name, bases, attrs, **kwargs)


    @property
    def facade_class(cls):
        class_name = get_stored_class_name(cls.__name__)
        facade_class_name = get_facade_class_name(class_name)
        dynamic_facade_class_name = get_dynamic_class_name(facade_class_name)

        module_name = model_index().model_class_path.get(class_name, None)
        module = importlib.import_module(module_name)

        if getattr(module, facade_class_name, None):
            facade_class = getattr(module, facade_class_name)
        elif getattr(module, dynamic_facade_class_name, None):
            facade_class = getattr(module, dynamic_facade_class_name)
        else:
            raise FacadeNotExistsError(
                f"Neither dynamic or coded facades exist for model {class_name}"
            )
        return facade_class

    @property
    def facade(cls):
        facade = None
        if not cls._meta.abstract:
            facade = model_index().model_class_facades.get(cls.__name__, None)
            if not facade:
                facade = cls.facade_class(cls)
                model_index().model_class_facades[cls.__name__] = facade
        return facade


class BaseMixin(
    django.Model,
    metaclass = BaseMetaModel
):
    class Meta:
        abstract = True

class BaseModel(
    BaseModelMixin,
    metaclass = BaseMetaModel
):
    class Meta:
        abstract = True
        facade_class = ModelFacade
