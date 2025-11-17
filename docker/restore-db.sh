#!/usr/bin/env bash

docker stop cmj
docker cp $1 saplpostgres:/tmp/cmj.backup

docker exec -it saplpostgres psql -hsapldb -Ucmj -dpostgres -c "DROP DATABASE IF EXISTS cmj;"
docker exec -it saplpostgres psql -hsapldb -Ucmj -dpostgres -c "CREATE DATABASE cmj WITH OWNER = cmj ENCODING = 'UTF8' CONNECTION LIMIT = -1;"

docker exec -it saplpostgres pg_restore -hsapldb -Ucmj --role "cmj" --dbname=cmj --verbose /tmp/sapl.backup
