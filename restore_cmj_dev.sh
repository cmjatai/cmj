#!/bin/bash

docker cp /tmp/backup_BD_PORTAL_CMJ_DEV.backup stormdb:/tmp/.
docker exec stormdb psql -U cmj -d postgres -c "drop database cmj;"
docker exec stormdb psql -U cmj -d postgres -c "create database cmj;"
docker exec stormdb pg_restore  --verbose -U cmj -d cmj /tmp/backup_BD_PORTAL_CMJ_DEV.backup
