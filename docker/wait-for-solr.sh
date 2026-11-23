#!/usr/bin/env bash

# Pass the base SOLR URL as parameter, i.e., bash check_solr http://localhost:8983

SOLR_URL=$1
# URL do Solr para o log, sem a senha (http://usuario:***@host:porta)
SOLR_URL_LOG=$(printf '%s' "$SOLR_URL" | sed -E 's#(://[^:/@]+):[^@]*@#\1:***@#')

RETRY_COUNT=0
RETRY_LIMIT=60 # wait until 1 min

echo "Waiting for Solr connection at $SOLR_URL_LOG ..."
while [[ $RETRY_COUNT < $RETRY_LIMIT ]]; do
   echo "Attempt to connect to solr: $RETRY_COUNT of $RETRY_LIMIT"
   let RETRY_COUNT=RETRY_COUNT+1;
   echo "$SOLR_URL_LOG/solr/admin/collections?action=LIST"
   RESULT=$(curl -s -o /dev/null -I "$SOLR_URL/solr/admin/collections?action=LIST" -w '%{http_code}')
   echo $RESULT
   if [ $RESULT == 200 ]; then
      echo "Solr server is up!"
      exit 1
   else
      sleep 1
   fi
done
echo "Solr connection failed."
exit 2