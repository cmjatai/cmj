#!/bin/bash

docker cp /tmp/backup_BD_PORTAL_CMJ_DEV.backup stormdb:/tmp/.
docker exec stormdb psql -U cmj -d postgres -c "DROP DATABASE IF EXISTS cmj;"
docker exec stormdb psql -U cmj -d postgres -c "CREATE DATABASE cmj WITH OWNER = cmj ENCODING = 'UTF8' CONNECTION LIMIT = -1;"
docker exec stormdb pg_restore  --verbose -U cmj -d cmj /tmp/backup_BD_PORTAL_CMJ_DEV.backup
