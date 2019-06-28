#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/cenv

export CENV_API_INIT=True
#-------------------------------------------------------------------------------

if [ ! -z "$CENV_POSTGRES_HOST" -a ! -z "$CENV_POSTGRES_PORT" ]
then
  ./scripts/wait.sh --hosts="$CENV_POSTGRES_HOST" --port="$CENV_POSTGRES_PORT"
fi

echo "> Initializing application"
ce module init --verbosity=3
ce run core display
ce env get

echo "> Starting application"
export CENV_API_EXEC=True

gunicorn services.api.wsgi:application \
  --cert-reqs=1 \
  --ssl-version=2 \
  --certfile=/etc/ssl/certs/cenv.crt \
  --keyfile=/etc/ssl/private/cenv.key \
  --limit-request-field_size=0 \
  --limit-request-line=0 \
  --timeout=14400 \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind=0.0.0.0:5123