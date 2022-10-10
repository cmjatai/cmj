#!/usr/bin/env bash

sudo pg_restore --disable-triggers --data-only cmj_30-03-16.tar | docker exec -i cmj_localhost_1 psql -U cmj
