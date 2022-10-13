#!/usr/bin/env bash

/bin/bash wait-for-pg.sh "postgresql://cmj:cmj@cmjdb:5432/cmj"

python3 manage.py migrate

#/bin/sh start_daphne.sh &

/bin/sh start_gunicorn.sh &
/usr/sbin/nginx -g "daemon off;"
