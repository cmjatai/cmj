#!/usr/bin/env bash

SOLR_URL=${SOLR_URL-'http://localhost:8983/solr'}

# zip configset cmj_configset
cd ../cmj_configset/conf && zip -r cmj_configset.zip .

curl -X POST --header "Content-Type:application/octet-stream" --data-binary @cmj_configset.zip "$SOLR_URL/admin/configs?action=UPLOAD&name=cmj_configset"

cd -
rm ../cmj_configset/conf/cmj_configset.zip