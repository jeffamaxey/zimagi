#!/usr/bin/env python3
#-------------------------------------------------------------------------------
import sys
import os
import re
import copy
import yaml
#-------------------------------------------------------------------------------

values_file_path = sys.argv[1]
if not values_file_path:
    raise Exception("Helm values file path must be specified")

helm_values = {
    'postgresql': {
        'postgresqlUsername': os.environ['ZIMAGI_POSTGRES_USER'],
        'postgresqlPassword': os.environ['ZIMAGI_POSTGRES_PASSWORD'],
        'postgresqlDatabase': os.environ['ZIMAGI_POSTGRES_DB'],
    },
    'redis': {'auth': {'password': os.environ['ZIMAGI_REDIS_PASSWORD']}},
    'persistenceFlavour': {'minikube': True},
}
ignore_variables = [
    'ZIMAGI_POSTGRES_USER',
    'ZIMAGI_POSTGRES_PASSWORD',
    'ZIMAGI_POSTGRES_DB',
    'ZIMAGI_REDIS_PASSWORD',
    'ZIMAGI_CA_KEY',
    'ZIMAGI_CA_CERT',
    'ZIMAGI_KEY',
    'ZIMAGI_CERT'
]
env_values = [
    {'name': name, 'value': value}
    for name, value in os.environ.items()
    if re.match(r'^ZIMAGI_[_A-Z0-9]+$', name) and name not in ignore_variables
]
# Set service environment variables
for service_tag in ('scheduler', 'worker', 'commandApi', 'dataApi'):
    helm_values[service_tag] = {
        'extraEnv': copy.deepcopy(env_values)
    }

# Save Helm values overrides
with open(values_file_path, 'w') as file:
    file.write(yaml.dump(helm_values))
    os.chmod(values_file_path, 0o660)
