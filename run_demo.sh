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
docker run --memory=1gb --name kib01-test --volume="$(pwd)/kibana.yml:/usr/share/kibana/config/kibana.yml:ro" --net elastic -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://es01-test:9200" docker.elastic.co/kibana/kibana:7.15.2
# BROWSER - localhost:5601 - no index patterns


# METRICBEAT
docker pull docker.elastic.co/beats/metricbeat:7.15.2
docker run --net elastic docker.elastic.co/beats/metricbeat:7.15.2 setup -E setup.kibana.host=kib01-test:5601 -E output.elasticsearch.hosts=["http://es01-test:9200"]
# BROWSER - localhost:5601 - index pattern should now exist (metricbeat-*) - no records
docker run --memory=100mb --net elastic --user=root --volume="$(pwd)/metricbeat.docker.yml:/usr/share/metricbeat/metricbeat.yml:ro" --volume="/var/run/docker.sock:/var/run/docker.sock:ro" --volume="/sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro" --volume="/proc:/hostfs/proc:ro" --volume="/:/hostfs:ro" docker.elastic.co/beats/metricbeat:7.15.2 metricbeat -e -E output.elasticsearch.hosts=["es01-test:9200"]
# BROWSER - localhost:5601 - index pattern (metricbeat-*) - should now contain records


# ELASTIC WATCHER
python elastic_watcher.py 'system.cpu'
# BROWSER - localhost:15672 - show exchanges - now contains metrics-demo - Message rates Publish(In)=0.2 - note that Publish(Out)=0

# RABBIT CLIENT
# BROWSER - file:///home/vince/git/lora-mesh-websocket-demo/rabbit_client.html - show console
# BROWSER - localhost:15672 - show exchanges - now metrics-demo - has Message rates Publish(In)=0.2 - note that now Publish(Out)=0.2
# BROWSER - file:///home/vince/git/lora-mesh-websocket-demo/rabbit_client.html - CLOSE
# BROWSER - localhost:15672 - queue has disappeared - note that Publish(Out)=0 again
# BROWSER - file:///home/vince/git/lora-mesh-websocket-demo/rabbit_client.html - OPEN 2 INSTANCES
# BROWSER - localhost:15672 - there are now 2 queues - note that now Publish(Out)=0.4 - it has doubled because messages are copied out to 2 clients

