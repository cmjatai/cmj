#!/usr/bin/env bash

docker stop cmj
docker cp $1 cmjpostgres:/tmp/cmj.backup

docker exec -it cmjpostgres psql -hcmjdb -Ucmj -dpostgres -c "DROP DATABASE IF EXISTS cmj;"
docker exec -it cmjpostgres psql -hcmjdb -Ucmj -dpostgres -c "CREATE DATABASE cmj WITH OWNER = cmj ENCODING = 'UTF8' CONNECTION LIMIT = -1;"

docker exec -it cmjpostgres pg_restore -hcmjdb -Ucmj --role "cmj" --dbname=cmj --verbose /tmp/cmj.backup
