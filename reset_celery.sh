#!/bin/sh
redis-cli flushall
#sudo pkill -9 -f 'celery'
echo "" > logs/celery/celery1-1.log 
celery multi start 1 -A cmj -l INFO -Q:1 celery -c:1 1 --hostname=localhost --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log
tail -f -n 1000 logs/celery/celery1-1.log
