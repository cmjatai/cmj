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
DJANGO_SETTINGS_MODULE=cmj.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=cmj.wsgi                    # WSGI module name (*)

echo "Starting $NAME as `whoami` on base dir $DJANGODIR"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --log-level info \
  --timeout $TIMEOUT \
  --workers $NUM_WORKERS \
  --max-requests $MAX_REQUESTS \
  --user $USER \
  --access-logfile /var/cmjatai/cmj/logs/gunicorn_access.log \
  --error-logfile /var/cmjatai/cmj/logs/gunicorn_error.log \
  --bind=unix:$SOCKFILE
