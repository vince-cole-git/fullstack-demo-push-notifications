# RABBIT
docker pull rabbitmq:3.9-management
# start the container
docker run --memory=500mb -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 -p 15674:15674 -p 15670:15670 rabbitmq:3.9-management
# in new terminal, enter the container
docker exec -it $(docker container list | grep rabbit | cut -d' ' -f1) /bin/bash
# in the container, enable the plugins
    rabbitmq-plugins enable rabbitmq_web_stomp rabbitmq_web_stomp_examples
# BROWSER - localhost:15672 - show exchanges

# ELASTIC
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.15.2
docker run --memory=1gb --name es01-test --net elastic -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.2
# BROWSER - localhost:9200/_search - no records

# KIBANA
docker pull docker.elastic.co/kibana/kibana:7.15.2
# ensure the file ./kibana.docker.yml exists (with correct config in it)
docker run --memory=1gb --name kib01-test --volume="$(pwd)/kibana.docker.yml:/usr/share/kibana/config/kibana.yml:ro" --net elastic -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://es01-test:9200" docker.elastic.co/kibana/kibana:7.15.2
# BROWSER - localhost:5601 - no index patterns

# METRICBEAT
docker pull docker.elastic.co/beats/metricbeat:7.15.2
docker run --net elastic docker.elastic.co/beats/metricbeat:7.15.2 setup -E setup.kibana.host=kib01-test:5601 -E output.elasticsearch.hosts=["http://es01-test:9200"]
# ^ this will create the index pattern and dashboards, then exit
# BROWSER - localhost:5601 - index pattern should now exist (metricbeat-*) - no records
# ensure the file ./metricbeat.docker.yml exists (with correct config in it) especially the following lines:
    username: '${ELASTICSEARCH_USERNAME:}'
    password: '${ELASTICSEARCH_PASSWORD:}'
docker run --memory=100mb --net elastic --user=root --volume="$(pwd)/metricbeat.docker.yml:/usr/share/metricbeat/metricbeat.yml:ro" --volume="/var/run/docker.sock:/var/run/docker.sock:ro" --volume="/sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro" --volume="/proc:/hostfs/proc:ro" --volume="/:/hostfs:ro" docker.elastic.co/beats/metricbeat:7.15.2 metricbeat -e -E output.elasticsearch.hosts=["es01-test:9200"]
# BROWSER - localhost:5601 - index pattern (metricbeat-*) - should now contain records

# ELASTIC WATCHER
python elastic_watcher.py 'system.cpu'
# BROWSER - localhost:15672 - show exchanges - now contains metrics-demo - Message rates Publish(In)=0.2 - note that Publish(Out)=0

### RABBIT CLIENT ###
# BROWSER - localhost:5000 - ensure no subscriptions are active
# BROWSER - localhost:15672 - show exchanges - metrics-demo - still nothing new
# BROWSER - localhost:5000 - activate some subscriptions 
# BROWSER - localhost:15672 - show exchanges - metrics-demo - note that now Publish(Out) rate is > 0 (and queues now exist!)
# BROWSER - localhost:5000 - CLOSE
# BROWSER - localhost:15672 - no queues now - Publish(Out)=0
# BROWSER - localhost:5000 - OPEN 2 INSTANCES
# BROWSER - localhost:15672 - there are now 2x queues - note that now Publish(Out) > 0 - messages are copied out to 2 clients (so rate is higher)


######################################################################################################################################
# TO ENABLE SECURITY (use these instead of the above)
######################################################################################################################################

# ELASTIC
docker run --memory=1gb --name es01-test --net elastic -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "pack.security.enabled=true" docker.elastic.co/elasticsearch/elasticsearch:7.15.2
docker exec -it $(docker container list | grep elasticsearch | cut -d' ' -f1) /bin/bash
    elasticsearch-setup-passwords auto # now MUST copy the passwords out to a text file!
# BROWSER - login as user "elastic"

# KIBANA
docker run --memory=1gb --name kib01-test --volume="$(pwd)/kibana.docker.yml:/usr/share/kibana/config/kibana.yml:ro" --net elastic -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://es01-test:9200" docker.elastic.co/kibana/kibana:7.15.2
docker exec -it $(docker container list | grep kibana | cut -d' ' -f1) /bin/bash
    kibana-keystore create
    kibana-keystore add elasticsearch.password ### <--- literally that. Then, will be prompted for it, ie. the password (from text file) for user "kibana_system"
docker cp $(docker container list | grep kibana | cut -d' ' -f1):/usr/share/kibana/config/kibana.keystore ./kibana.docker.keystore
Ctrl-C # kill the container
echo 'elasticsearch.username: "kibana_system"' >> kibana.docker.yml
docker container prune
docker run --memory=1gb --name kib01-test --volume="$(pwd)/kibana.docker.yml:/usr/share/kibana/config/kibana.yml:ro" --volume="$(pwd)/kibana.keystore:/usr/share/kibana/config/kibana.keystore:ro" --net elastic -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://es01-test:9200" docker.elastic.co/kibana/kibana:7.15.2
# BROWSER - login as user "elastic"

# METRICBEAT
#BROWSER - execute these requests in the Kibana dev console:
    #
    POST _xpack/security/role/metricbeat_writer
    {
      "cluster": ["manage_index_templates","monitor"],
      "indices": [
        {
          "names": [ "metricbeat-*" ], 
          "privileges": ["write","create_index"]
        }
      ]
    }
    #
    POST _xpack/security/role/metricbeat_ilm
    {
    "cluster": ["manage_ilm"],
    "indices": [
        {
        "names": [ "metricbeat-*","shrink-metricbeat-*"],
        "privileges": ["write","create_index","manage","manage_ilm"]
        }
    ]
    }
    POST /_xpack/security/user/metricbeat_internal
    {
     "password" : "metricbeat_internal_password",
     "roles" : [ "metricbeat_ilm","metricbeat_writer","kibana_user" ],
     "full_name" : "Internal Metricbeat User"
    }
    #
# in FILE: metricbeat.docker.yml 
# change the lines
  username: '${ELASTICSEARCH_USERNAME:}'
  password: '${ELASTICSEARCH_PASSWORD:}'
# to
  username: 'metricbeat_internal'
  password: 'metricbeat_internal_password'
# (run it as before)
docker run --net elastic --volume="$(pwd)/metricbeat.docker.yml:/usr/share/metricbeat/metricbeat.yml:ro" docker.elastic.co/beats/metricbeat:7.15.2 setup -E setup.kibana.host=kib01-test:5601 -E output.elasticsearch.hosts=["http://es01-test:9200"]
docker run --memory=100mb --net elastic --user=root --volume="$(pwd)/metricbeat.docker.yml:/usr/share/metricbeat/metricbeat.yml:ro" --volume="/var/run/docker.sock:/var/run/docker.sock:ro" --volume="/sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro" --volume="/proc:/hostfs/proc:ro" --volume="/:/hostfs:ro" docker.elastic.co/beats/metricbeat:7.15.2 metricbeat -e -E output.elasticsearch.hosts=["es01-test:9200"]
