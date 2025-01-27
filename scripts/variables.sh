#
#=========================================================================================
# Project variables
#

# Set top level directory as working directory
cd "${__zimagi_dir}"

# Set magic variables for current file, directory, os, etc.
export __zimagi_file="${__zimagi_script_dir}/${__zimagi_base}"
export __zimagi_test_dir="${__zimagi_script_dir}/test"
export __zimagi_binary_dir="${__zimagi_dir}/bin"
export __zimagi_docker_dir="${__zimagi_dir}/docker"
export __zimagi_build_dir="${__zimagi_dir}/build"
export __zimagi_charts_dir="${__zimagi_dir}/charts"
export __zimagi_certs_dir="${__zimagi_dir}/certs"

export __zimagi_app_dir="${__zimagi_dir}/app"
export __zimagi_package_dir="${__zimagi_dir}/package"
export __zimagi_data_dir="${__zimagi_dir}/data"
export __zimagi_lib_dir="${__zimagi_dir}/lib"

export __zimagi_helm_values_file="${__zimagi_data_dir}/helm.values.yml"
export __zimagi_app_env_file="${__zimagi_data_dir}/app.env.sh"
export __zimagi_runtime_env_file="${__zimagi_data_dir}/runtime.env.sh"
export __zimagi_cli_env_file="${__zimagi_data_dir}/cli.env.sh"

# shellcheck disable=SC2034,SC2015
export __zimagi_reactor_invocation="$(printf %q "${__zimagi_file}")$( (($#)) && printf ' %q' "$@" || true)"
export __zimagi_reactor_core_flags="
    -v --verbose          Enable verbose mode, print script as it is executed
    -d --debug            Enables debug mode
    -n --no-color         Disable color output
    -h --help             Display help message"

# Default environment configuration
if [[ "$PATH" != *"${__zimagi_script_dir}"* ]]; then
  export PATH="${__zimagi_script_dir}:${__zimagi_dir}/bin:$PATH"
fi
export LOG_LEVEL="${LOG_LEVEL:-6}" # 7 = debug -> 0 = emergency
export NO_COLOR="${NO_COLOR:-}"    # true = disable color. otherwise autodetected

export DOCKER_STANDARD_PARENT_IMAGE="ubuntu:20.04"
export DOCKER_NVIDIA_PARENT_IMAGE="nvidia/cuda:11.4.2-cudnn8-runtime-ubuntu20.04"

export DEFAULT_MINIKUBE_DRIVER="docker"
export DEFAULT_MINIKUBE_CPUS=2
export DEFAULT_KUBERNETES_VERSION="1.23.1"
export DEFAULT_MINIKUBE_CONTAINER_RUNTIME="docker"
export DEFAULT_MINIKUBE_PROFILE="skaffold"

export DEFAULT_HELM_VERSION="3.8.0"

export DEFAULT_CLI_POSTGRES_PORT=5432
export DEFAULT_CLI_REDIS_PORT=6379
export DEFAULT_CLI_COMMAND_PORT=5123
export DEFAULT_CLI_DATA_PORT=5323
export DEFAULT_CLI_CELERY_FLOWER_PORT=5555

export DEFAULT_KUBERNETES_COMMAND_PORT=5133
export DEFAULT_KUBERNETES_DATA_PORT=5333

export DEFAULT_SECRET_KEY="XXXXXX20181105"
export DEFAULT_POSTGRES_DB="zimagi"
export DEFAULT_POSTGRES_USER="zimagi"
export DEFAULT_POSTGRES_PASSWORD="A1B3C5D7E9F10"
export DEFAULT_REDIS_PASSWORD="A1B3C5D7E9F10"

export DEFAULT_APP_NAME="zimagi"
export DEFAULT_BASE_IMAGE="zimagi/zimagi"
export DEFAULT_DOCKER_RUNTIME="standard"
export DEFAULT_DOCKER_TAG="dev"
export DEFAULT_USER_PASSWORD="en7hs0hb36kq9l1u00cz7v"
export DEFAULT_DATA_KEY="b12e75f78n876543210H36j250162731"
export DEFAULT_ADMIN_API_KEY="RFJwNYpqA4zihE8jVkivppZfGVDPnzcq"
export DEFAULT_ADMIN_API_TOKEN="uy5c8xiahf93j2pl8s00e6nb32h87dn3"
export DEFAULT_TEST_SCRIPT_NAME="command"
export DEFAULT_CERT_SUBJECT="/C=US/ST=DC/L=Washington/O=zimagi/CN=localhost"
export DEFAULT_CERT_DAYS=3650

# Directory creation
mkdir -p "${__zimagi_data_dir}"
mkdir -p "${__zimagi_lib_dir}"
