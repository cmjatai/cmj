#!/usr/bin/env bash
NAME="PortalCMJ.wsgi"                                     # Name of the application (*)
DJANGODIR=/var/cmjatai/cmj                      # Django project directory (*)
SOCKFILE=/var/cmjatai/cmj/run/gunicorn.sock     # we will communicate using this unix socket (*)
USER=`whoami`                                   # the user to run as (*)
GROUP=`whoami`                                  # the group to run as (*)
NUM_WORKERS=16                                   # how many worker processes should Gunicorn spawn (*)
                                                # NUM_WORKERS = 2 * CPUS + 1
TIMEOUT=300
MAX_REQUESTS=1000                                # number of requests before restarting worker
MAX_REQUESTS_JITTER=200                          # evita que os workers reiniciem todos juntos
CONFIG_FILE=/var/cmjatai/cmj/docker/gunicorn.conf.py
DJANGO_SETTINGS_MODULE=cmj.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=cmj.wsgi                    # WSGI module name (*)

echo "Starting $NAME as `whoami` on base dir $DJANGODIR"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Métricas do Prometheus em modo multiprocess: os workers gravam aqui e o
# /metrics soma tudo. O diretório é limpo a cada subida do gunicorn.
export PROMETHEUS_MULTIPROC_DIR=/var/cmjatai/cmj/run/prometheus
rm -rf $PROMETHEUS_MULTIPROC_DIR
mkdir -p $PROMETHEUS_MULTIPROC_DIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  -c $CONFIG_FILE \
  --name $NAME \
  --log-level info \
  --timeout $TIMEOUT \
  --workers $NUM_WORKERS \
  --max-requests $MAX_REQUESTS \
  --max-requests-jitter $MAX_REQUESTS_JITTER \
  --user $USER \
  --access-logfile /var/cmjatai/cmj/logs/gunicorn_access.log \
  --error-logfile /var/cmjatai/cmj/logs/gunicorn_error.log \
  --bind=unix:$SOCKFILE
