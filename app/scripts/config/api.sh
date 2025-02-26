export ZIMAGI_STARTUP_SERVICES='[]'
export ZIMAGI_SERVICE_PROCESS=(
  "gunicorn"
  "services.wsgi:application"
  "--cert-reqs=1"
  "--ssl-version=2"
  "--certfile=/etc/ssl/certs/zimagi.crt"
  "--keyfile=/etc/ssl/private/zimagi.key"
  "--limit-request-field_size=0"
  "--limit-request-fields=0"
  "--limit-request-line=0"
  "--timeout=${ZIMAGI_SERVER_TIMEOUT:-14400}"
  "--worker-class=gevent"
  "--workers=${ZIMAGI_SERVER_WORKERS:-4}"
  "--threads=${ZIMAGI_SERVER_THREADS:-12}"
  "--worker-connections=${ZIMAGI_SERVER_CONNECTIONS:-100}"
  "--backlog=${ZIMAGI_SERVER_MAX_PENDING_CONNECTIONS:-3000}"
  "--bind=0.0.0.0:5000"
)
