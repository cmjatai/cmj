#!/usr/bin/env bash

SOLR_URL=${SOLR_URL-'http://localhost:8983/solr'}

curl -X POST "$SOLR_URL/admin/configs?action=DELETE&name=cmj_configset&omitHeader=true"