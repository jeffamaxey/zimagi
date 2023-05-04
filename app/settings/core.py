"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from systems.manager import Manager
from .config import Config

import os
import pathlib
import threading
import colorful


class ConfigurationError(Exception):
    pass


#-------------------------------------------------------------------------------
# Core settings

#
# Directories
#
APP_DIR = '/usr/local/share/zimagi'
DATA_DIR = '/var/local/zimagi'
LIB_DIR = '/usr/local/lib/zimagi'

HOST_APP_DIR = Config.value('ZIMAGI_HOST_APP_DIR', None)
HOST_DATA_DIR = Config.value('ZIMAGI_HOST_DATA_DIR', None)
HOST_LIB_DIR = Config.value('ZIMAGI_HOST_LIB_DIR', None)

#
# Development
#
DEBUG = Config.boolean('ZIMAGI_DEBUG', False)
DEBUG_COMMAND_PROFILES = Config.boolean('ZIMAGI_DEBUG_COMMAND_PROFILES', False)

INIT_PROFILE = Config.boolean('ZIMAGI_INIT_PROFILE', False)
COMMAND_PROFILE = Config.boolean('ZIMAGI_COMMAND_PROFILE', False)
DISABLE_MODULE_INIT = Config.boolean('ZIMAGI_DISABLE_MODULE_INIT', False)
DISABLE_MODULE_SYNC = Config.boolean('ZIMAGI_DISABLE_MODULE_SYNC', False)
DISABLE_REMOVE_ERROR_MODULE = Config.boolean('ZIMAGI_DISABLE_REMOVE_ERROR_MODULE', False)

#
# General configurations
#
APP_NAME = Config.string('ZIMAGI_APP_NAME', 'zimagi', default_on_empty = True)
APP_SERVICE = Config.string('ZIMAGI_SERVICE', 'cli', default_on_empty = True)
SECRET_KEY = Config.string('ZIMAGI_SECRET_KEY', 'XXXXXX20181105')
USER_PASSWORD= Config.string('ZIMAGI_USER_PASSWORD', 'en7hs0hb36kq9l1u00cz7v')

ENCRYPT_COMMAND_API = Config.boolean('ZIMAGI_ENCRYPT_COMMAND_API', False)
ENCRYPT_DATA_API = Config.boolean('ZIMAGI_ENCRYPT_DATA_API', False)
ENCRYPT_DATA = Config.boolean('ZIMAGI_ENCRYPT_DATA', True)

ENCRYPTION_STATE_PROVIDER = Config.string('ZIMAGI_ENCRYPTION_STATE_PROVIDER', 'aes256')
ENCRYPTION_STATE_KEY = Config.string('ZIMAGI_ENCRYPTION_STATE_KEY', '/etc/ssl/certs/zimagi.crt')

PARALLEL = Config.boolean('ZIMAGI_PARALLEL', True)
THREAD_COUNT = Config.integer('ZIMAGI_THREAD_COUNT', 10)
QUEUE_COMMANDS = Config.boolean('ZIMAGI_QUEUE_COMMANDS', True)
FOLLOW_QUEUE_COMMAND = Config.boolean('ZIMAGI_FOLLOW_QUEUE_COMMAND', True)

CLI_EXEC = Config.boolean('ZIMAGI_CLI_EXEC', False)
SERVICE_INIT = Config.boolean('ZIMAGI_SERVICE_INIT', False)
SERVICE_EXEC = Config.boolean('ZIMAGI_SERVICE_EXEC', False)
SCHEDULER_INIT = Config.boolean('ZIMAGI_SCHEDULER_INIT', False)

NO_MIGRATE = Config.boolean('ZIMAGI_NO_MIGRATE', False)
AUTO_MIGRATE_TIMEOUT = Config.integer('ZIMAGI_AUTO_MIGRATE_TIMEOUT', 300)
AUTO_MIGRATE_INTERVAL = Config.integer('ZIMAGI_AUTO_MIGRATE_INTERVAL', 5)

ROLE_PROVIDER = Config.string('ZIMAGI_ROLE_PROVIDER', 'role')

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

#
# Time configuration
#
TIME_ZONE = Config.string('ZIMAGI_TIME_ZONE', 'America/New_York')
USE_TZ = True

DEFAULT_DATE_FORMAT = Config.string('ZIMAGI_DEFAULT_DATE_FORMAT', '%Y-%m-%d')
DEFAULT_TIME_FORMAT = Config.string('ZIMAGI_DEFAULT_TIME_FORMAT', '%H:%M:%S')
DEFAULT_TIME_SPACER_FORMAT = Config.string('ZIMAGI_DEFAULT_TIME_SPACER_FORMAT', ' ')

#
# Language configurations
#
LANGUAGE_CODE = Config.string('ZIMAGI_LOCALE', 'en')
USE_I18N = True
USE_L10N = True

#
# Display configurations
#
DISPLAY_LOCK = threading.Lock()

DISPLAY_WIDTH = Config.integer('ZIMAGI_DISPLAY_WIDTH', 80)
DISPLAY_COLOR = Config.boolean('ZIMAGI_DISPLAY_COLOR', True)
COLOR_SOLARIZED = Config.boolean('ZIMAGI_COLOR_SOLARIZED', True)

COMMAND_COLOR = Config.string('ZIMAGI_COMMAND_COLOR', 'cyan')
HEADER_COLOR = Config.string('ZIMAGI_HEADER_COLOR', 'violet')
KEY_COLOR = Config.string('ZIMAGI_KEY_COLOR', 'cyan')
VALUE_COLOR = Config.string('ZIMAGI_VALUE_COLOR', 'violet')
ENCRYPTED_COLOR = Config.string('ZIMAGI_ENCRYPTED_COLOR', 'yellow')
DYNAMIC_COLOR = Config.string('ZIMAGI_DYNAMIC_COLOR', 'magenta')
RELATION_COLOR = Config.string('ZIMAGI_RELATION_COLOR', 'green')
PREFIX_COLOR = Config.string('ZIMAGI_PREFIX_COLOR', 'magenta')
SUCCESS_COLOR = Config.string('ZIMAGI_SUCCESS_COLOR', 'green')
NOTICE_COLOR = Config.string('ZIMAGI_NOTICE_COLOR', 'cyan')
WARNING_COLOR = Config.string('ZIMAGI_WARNING_COLOR', 'orange')
ERROR_COLOR = Config.string('ZIMAGI_ERROR_COLOR', 'red')
TRACEBACK_COLOR = Config.string('ZIMAGI_TRACEBACK_COLOR', 'yellow')

colorful.use_true_colors()

if COLOR_SOLARIZED:
    colorful.use_style('solarized')

#
# Runtime configurations
#
BASE_DATA_PATH = os.path.join(DATA_DIR, 'cli')
RUNTIME_PATH = f"{BASE_DATA_PATH}.yml"

DEFAULT_ENV_NAME = Config.string('ZIMAGI_DEFAULT_ENV_NAME', 'default')
DEFAULT_HOST_NAME = Config.string('ZIMAGI_DEFAULT_HOST_NAME', 'default')
DEFAULT_RUNTIME_REPO = Config.string('ZIMAGI_DEFAULT_RUNTIME_REPO', 'registry.hub.docker.com')
DEFAULT_RUNTIME_IMAGE = Config.string('ZIMAGI_DEFAULT_RUNTIME_IMAGE', 'zimagi/zimagi:latest')
RUNTIME_IMAGE = Config.string('ZIMAGI_RUNTIME_IMAGE', DEFAULT_RUNTIME_IMAGE)

MODULE_BASE_PATH = os.path.join(LIB_DIR, 'modules')
pathlib.Path(MODULE_BASE_PATH).mkdir(parents = True, exist_ok = True)

TEMPLATE_BASE_PATH = os.path.join(LIB_DIR, 'templates')
pathlib.Path(TEMPLATE_BASE_PATH).mkdir(parents = True, exist_ok = True)

DATASET_BASE_PATH = os.path.join(LIB_DIR, 'datasets')
pathlib.Path(DATASET_BASE_PATH).mkdir(parents = True, exist_ok = True)

PROFILER_PATH = os.path.join(LIB_DIR, 'profiler')
pathlib.Path(PROFILER_PATH).mkdir(parents = True, exist_ok = True)

CORE_MODULE = Config.string('ZIMAGI_CORE_MODULE', 'core')
DEFAULT_MODULES = Config.list('ZIMAGI_DEFAULT_MODULES', [])

STARTUP_SERVICES = Config.list('ZIMAGI_STARTUP_SERVICES', [])

#
# Logging configuration
#
LOG_LEVEL = Config.string('ZIMAGI_LOG_LEVEL', 'warning').upper()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        '': {
            'level': LOG_LEVEL,
            'handlers': ['console']
        }
    }
}

#
# System check settings
#
SILENCED_SYSTEM_CHECKS = []

#
# Applications and libraries
#
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'settings.app.AppInit'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware'
]

#
# Authentication configuration
#
AUTH_USER_MODEL = 'user.User'

#
# API configuration
#
ADMIN_USER = Config.string('ZIMAGI_ADMIN_USER', 'admin')
DEFAULT_ADMIN_TOKEN = Config.string('ZIMAGI_DEFAULT_ADMIN_TOKEN', 'uy5c8xiahf93j2pl8s00e6nb32h87dn3')
