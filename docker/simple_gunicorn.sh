#!/usr/bin/env bash

DJANGODIR=/var/cmjatai/cmj                     # Django project directory (*)
DJANGO_SETTINGS_MODULE=cmj.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=cmj.wsgi                    # WSGI module name (*)

cd $DJANGODIR
source /var/cmjatai/.virtualenvs/cmj/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Get eth0 IP and filter out the netmask portion (/24, e.g.)
IP=`ip addr | grep 'inet .* eth0' | awk '{print $2}' | sed 's/\/[0-9]*//'`

gunicorn --bind $IP:8000 cmj.wsgi:application
