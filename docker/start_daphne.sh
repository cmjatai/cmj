#!/bin/bash

# As seen in http://tutos.readthedocs.org/en/latest/source/ndg.html

NAME="PortalCMJ.asgi"                                     # Name of the application (*)
DJANGODIR=/var/cmjatai/cmj                    # Django project directory (*)
SOCKFILE=/var/cmjatai/cmj/run/daphne.sock    # we will communicate using this unix socket (*)
USER=`whoami`                                   # the user to run as (*)
GROUP=`whoami`                                  # the group to run as (*)
NUM_WORKERS=1                                   # how many worker processes should Gunicorn spawn (*)
                                                # NUM_WORKERS = 2 * CPUS + 1
DJANGO_SETTINGS_MODULE=cmj.settings            # which settings file should Django use (*)
DJANGO_ASGI_MODULE=cmj.asgi                    # WSGI module name (*)

echo "Starting $NAME as `whoami` on base dir $DJANGODIR"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

exec daphne \
    -u $SOCKFILE ${DJANGO_ASGI_MODULE}:application \
    --access-log /var/cmjatai/cmj/logs/daphne_access.log \
    -v2


