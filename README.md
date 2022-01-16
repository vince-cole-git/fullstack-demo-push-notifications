### DEMO 1: OF BASIC WEBSOCKET USE

Does NOT use "push" notifications from Elastic
But it DOES use them between the middleware and the UI, over WebSockets

there will a subsequent demo for each of the following changes:
* DEMO 2: Using Elastic push instead of polling
* DEMO 3: Using RabbitMQ instead of Websockets (to push updates to the UI)

^these^ are mainly middleware changes, but several UI improvements were also made (as it evolved over time)

## What is being demonstrated here:
* Generating system metrics using metricbeat (which stores them in Elastic)
* Python middleware pulling the metrics from Elastic (for "subscribed" channels only)
* Python middleware pushing the metrics into the UI via a WebSocket
* UI displaying the metrics
* UI sending signals (via the WebSocket to the middleware) to toggle channel subscriptions on/off

## start the UI:
    npm run dev

there is a widget per channel (each type of system metrics available) a "subscribe" button and an area to display the metrics
each widget is independent of the others and has its own channel, uses a WebSocket to talk to the middleware
look in the dev tools - Network/Console - see how all WS have failed (because there is no MW running)
## start the middleware:
    cd src; uvicorn main:app

refresh the UI - now see how the WS connections have succeeded
in the UI try to "Subscribe" - nothing happens
check the Python console output - subscriptions fail unless Elastic is running
## start Elastic:
    docker run --memory=1gb --name es01-test --net elastic -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.2

in the UI try to "Subscribe" - nothing happens again
check the Python console output - subscriptions fail unless Elastic contains the Metrics index
this doesn't exist, because the Metrics Producer isn't running yet

## prepare to start the MP
### first start Kibana
    docker run --memory=1gb --name kib01-test --net elastic -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://es01-test:9200" docker.elastic.co/kibana/kibana:7.15.2
### then setup the Metrics index
    docker run --net elastic docker.elastic.co/beats/metricbeat:7.15.2 setup -E setup.kibana.host=kib01-test:5601 -E output.elasticsearch.hosts=["http://es01-test:9200"]

## start the MP (metricbeat) 
    docker run --name=metricbeat --user=root  --volume="/var/run/docker.sock:/var/run/docker.sock:ro" --volume="/sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro" --volume="/proc:/hostfs/proc:ro" --volume="/:/hostfs:ro" docker.elastic.co/beats/metricbeat:7.15.2 metricbeat -e -E output.elasticsearch.hosts=["192.168.1.145:9200"]

## in the UI try to "Subscribe" - now it works
