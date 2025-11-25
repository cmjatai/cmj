#!/usr/bin/env bash

echo -e "\033[38;2;255;255;0;2m\033[1m====> StartPRD...\033[0m"

/bin/bash wait-for-pg.sh "postgresql://cmj_st1:cmj_st1@cmjdb:5432/cmj"

yes yes | python3 manage.py migrate

## SOLR
USE_SOLR="${USE_SOLR:=False}"
SOLR_URL="${SOLR_URL:=http://localhost:8983}"
SOLR_COLLECTIONS="${SOLR_COLLECTIONS:=portalcmj_cmj}"
NUM_SHARDS=${NUM_SHARDS:=1}
RF=${RF:=1}
MAX_SHARDS_PER_NODE=${MAX_SHARDS_PER_NODE:=1}
IS_ZK_EMBEDDED="${IS_ZK_EMBEDDED:=False}"

if [ "${USE_SOLR-False}" == "True" ] || [ "${USE_SOLR-False}" == "true" ]; then

    echo "Solr configurations"
    echo "==================="
    echo "URL: $SOLR_URL"
    echo "COLLECTION: $SOLR_COLLECTIONS"
    echo "NUM_SHARDS: $NUM_SHARDS"
    echo "REPLICATION FACTOR: $RF"
    echo "MAX SHARDS PER NODE: $MAX_SHARDS_PER_NODE"
    echo "ASSUME ZK EMBEDDED: $IS_ZK_EMBEDDED"
    echo "========================================="

    echo "running Solr script"
    /bin/bash wait-for-solr.sh $SOLR_URL
    CHECK_SOLR_RETURN=$?

    if [ $CHECK_SOLR_RETURN == 1 ]; then
        echo "Connecting to Solr..."

        if [ "${IS_ZK_EMBEDDED-False}" == "True" ] || [ "${IS_ZK_EMBEDDED-False}" == "true" ]; then
            ZK_EMBEDDED="--embedded_zk"
            echo "Assuming embedded ZooKeeper instalation..."
        fi

        python3 solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED
    else
        echo "Solr is offline, not possible to connect."
    fi

else
    echo "Solr support is not initialized."
fi

rm /var/cmjatai/cmj/logs/celery/*.pid
celery multi start 16 -A cmj -l INFO -Q:1-5 cq_arq -Q:6-7 cq_core -Q:8 cq_videos -Q:9-14 cq_base -Q:15-16 celery -c 2 --hostname=cmjredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log

celery -A cmj beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

#celery multi start 1 -A cmj -l INFO -Q:1 celery -c:1 1 --hostname=cmjredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log

/bin/sh start_daphne.sh &
/bin/sh start_gunicorn.sh &
/usr/sbin/nginx -g "daemon off;"
