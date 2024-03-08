#!/usr/bin/env bash

while true; do
    echo "Esperando Database Setup"
    COUNT_PG=`psql $1 -c '\l \q' | grep cmj | wc -l`
    if ! [ "$COUNT_PG" -eq "0" ]; then
       break
    fi
    sleep 10
done
