### DEMO 2: ELASTIC PUSH NOTIFICATION PLUGIN

Middleware listens to "push" notifications from Elastic instead of polling it
Middleware also pushes notifications to the UI, over WebSockets
It is both a WebSocket client (to Elastic) and a server (to the UI)

there will a subsequent demo for each of the following change:
* DEMO 3: Using RabbitMQ instead of Websockets (to push updates to the UI)

## What is being demonstrated here:
* Generating system metrics using metricbeat (which stores them in Elastic)
* Python middleware accepting the metrics from Elastic (for "subscribed" channels only)
* Python middleware pushing the metrics into the UI via a WebSocket
* UI displaying the metrics
* UI sending signals (via the WebSocket to the middleware) to toggle channel subscriptions on/off

## start the UI:
    npm run dev
    BROWSER - http://localhost:5000/

UI displays a 'widget' per channel, with a "subscribe" button and an area to display the metrics
there is a channel per metric type, as reported by metricbeat
each widget is independent of the others and has its own channel, uses a WebSocket to talk to the middleware. Each WebSocket uses its own middleware endpoint.
look in the dev tools - Network/Console - see how all WS have failed (because there is no MW running)

## start the middleware (before Elastic is started):
    cd src; 
    virtualenv ./demo2
    source ./demo2/bin/activate
    pip install -r ../requirements.txt     
    uvicorn main:app

This will FAIL because there is a dependency from the middleware to Elastic. 
The middleware tries to listen to the Elastic websocket, but Elastic isn't running yet, so this fails.
So we need to start Elastic first...

## to run Elastic container (temporary, for installing plugin only)
    sudo docker run --memory=1gb --name es01-test --net elastic -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.5.3

## install the plugin (into temporary Elastic container) and extract the plugins directory 
    # build the plugin
    git clone https://github.com/ForgeRock/es-change-feed-plugin.git
    cd es-change-feed-plugin
    mvn clean install  
    sudo docker cp target/es-changes-feed-plugin.zip es01-test:/tmp/es-changes-feed-plugin.zip
    # install the plugin
    sudo docker exec -it es01-test /bin/bash
    /usr/share/elasticsearch/bin/elasticsearch-plugin install file:///tmp/es-changes-feed-plugin.zip
    /usr/share/elasticsearch/bin/elasticsearch-plugin list
    exit
    # get the plugins directory
    mkdir es-plugins
    cd es-plugins
    sudo docker cp es01-test:/usr/share/elasticsearch/plugins .

## to run Elastic container (mounting the extracted plugins directory into it, so it runs the plugin we want)
    sudo docker container stop es01-test
    sudo docker container rm es01-test
    sudo docker run -v $(pwd)/plugins:/usr/share/elasticsearch/plugins --memory=1gb --name es01-test --net elastic -p 9200:9200 -p 9300:9300 -p 9400:9400 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.5.3


## start the middleware (once Elastic is running):
    cd src; 
    virtualenv ./demo2
    source ./demo2/bin/activate
    pip install -r ../requirements.txt     
    uvicorn main:app
check this in the browser - http://localhost:8000

refresh the UI - now see how the WS connections have succeeded
in the UI try to "Subscribe" - nothing happens (but NOT due to errors, this time though)
check the Python console output 
  - note how the UI can send (in this case, boolean) messages down the WS to the MW (per channel) to toggle a subscription on/off
  - subscriptions are NOT failing - its simply the case that there aren't any metrics being produced yet
We need to produce some metrics...  

## prepare to start the MP
### first start Kibana
    sudo docker run --memory=1gb --name kib01-test --net elastic -p 5601:5601 -e "ELASTICSEARCH_URL=http://es01-test:9200" docker.elastic.co/kibana/kibana:6.5.3
### then setup the Metrics index
    sudo docker run --net elastic docker.elastic.co/beats/metricbeat:6.5.3 setup -E setup.kibana.host=kib01-test:5601 -E output.elasticsearch.hosts=["http://es01-test:9200"]
Check in browser:
    http://localhost:5601/app/discover

## start the MP (metricbeat) 
    sudo docker run --name=metricbeat --user=root  --volume="/var/run/docker.sock:/var/run/docker.sock:ro" --volume="/sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro" --volume="/proc:/hostfs/proc:ro" --volume="/:/hostfs:ro" docker.elastic.co/beats/metricbeat:6.5.3 metricbeat -e -E output.elasticsearch.hosts=["192.168.1.145:9200"]

Check data is appearing:
    Elastic - http://localhost:9200/_search
    Kibana  - http://localhost:5601/app/kibana#/discover?_g=()&_a=(columns:!(_source),index:'metricbeat-*',interval:auto)

## In the MW console should now see metrics being reported (and discarded because no subscriptions yet)

## in the UI now watch the page - for any "Subscribed" channels - metrics will now start to appear!
 - see subscribed channel's Count increasing
 - see how channels increase independently of each other

## Notes:
MW no longer polls Elastic
UI no longer contains logic for determining whether to show messages or not (this is done in MW)
MW is still a bit complex
There is still a dependency from MW upon the Elastic (plugin) already being running
It would be better to decouple these, via a message bus (see DEMO 3)
