#!/usr/bin/env bash

/bin/bash wait-for-pg.sh "postgresql://cmj:cmj@cmjdb:5432/cmj"

python3 manage.py migrate

celery multi start 1 -A cmj -l INFO -Q:1 celery -c:1 1 --hostname=cmjredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log

/bin/sh start_daphne.sh &
/bin/sh start_gunicorn.sh &
/usr/sbin/nginx -g "daemon off;" 
