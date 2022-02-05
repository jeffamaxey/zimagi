#!/bin/bash --login
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

SERVICE_TYPE="$1"

if [[ -z "$SERVICE_TYPE" ]]; then
  echo "Service gateway requires a process type identifier"
  exit 1
fi
if [[ -f "./scripts/config/${SERVICE_TYPE}.sh" ]]; then
  source "./scripts/config/${SERVICE_TYPE}.sh"
fi

export ZIMAGI_SERVICE_INIT=True
export "ZIMAGI_${SERVICE_TYPE^^}_INIT"=True
export ZIMAGI_NO_MIGRATE=True
#-------------------------------------------------------------------------------

trap 'kill --signal TERM "${PROCESS_PID}"; wait "${PROCESS_PID}"; cleanup' SIGTERM

function cleanup () {
  echo "Service shut down: cleaning up"
  rm -f "/var/local/zimagi/${SERVICE_TYPE}.pid"
}

#-------------------------------------------------------------------------------

if [[ ! -z "$ZIMAGI_POSTGRES_HOST" ]] && [[ ! -z "$ZIMAGI_POSTGRES_PORT" ]]; then
  ./scripts/wait.sh --hosts="$ZIMAGI_POSTGRES_HOST" --port=$ZIMAGI_POSTGRES_PORT --timeout=60
fi
if [[ ! -z "$ZIMAGI_REDIS_HOST" ]] && [[ ! -z "$ZIMAGI_REDIS_PORT" ]]; then
  ./scripts/wait.sh --hosts="$ZIMAGI_REDIS_HOST" --port=$ZIMAGI_REDIS_PORT --timeout=60
fi

echo "> Initializing service runtime"
zimagi task core migrate --lock=service_init --lock-timeout=0
zimagi module init --lock=service_init --reset --verbosity=3 --timeout=${ZIMAGI_INIT_TIMEOUT:-600}

if [[ ! -z "$ZIMAGI_ADMIN_API_KEY" ]]; then
  zimagi user save admin encryption_key="$ZIMAGI_ADMIN_API_KEY" --lock=admin_key_save --lock-timeout=0
fi

echo "> Fetching command environment information"
zimagi env get

if [[ ! -z "${ZIMAGI_SERVICE_PROCESS[@]}" ]]; then
  export ZIMAGI_SERVICE_INIT=False
  export "ZIMAGI_${SERVICE_TYPE^^}_INIT"=False
  export "ZIMAGI_${SERVICE_TYPE^^}_EXEC"=True
  export ZIMAGI_SERVICE_EXEC=True
  export ZIMAGI_BOOTSTRAP_DJANGO=True

  echo "> Starting ${SERVICE_TYPE} service"
  "${ZIMAGI_SERVICE_PROCESS[@]}" &

  PROCESS_PID="$!"
  wait "${PROCESS_PID}"
fi