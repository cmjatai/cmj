cd solr/cmj_configset/conf
rm cmjconfigset.zip
zip -r cmjconfigset.zip *
cd ../../../../solr/
solr-8.2.0/bin/solr stop
rm -rf solr-8.2.0
tar xzfv solr-8.2.0.tgz
solr-8.2.0/bin/solr start -c
cd ../cmj
python solr_api.py -u http://localhost:8983 -c cmj_portal -s 1 -rf 1 -ms 1
#./manage.py update_index sigad --verbosity 2
