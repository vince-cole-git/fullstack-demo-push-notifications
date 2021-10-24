demo for use of WebSockets 
the idea is to allow push notifications to be sent from Elastic to the middleware (Python: FastAPI) and then on up to the UI (JavaScript: Svelte), in order to avoid the UI having to constantly poll the middleware which then has to constantly poll Elastic in response (or perform some kind of caching)

progress so far:
* UI opens a WS to the middleware, and subscribes to messages coming from it
* UI sends a boolean down the WS to the middle to toggle on/off its behaviour WRT polling Elastic
* Elastic is running with MetricBeats, so the index is being populated with system stats
* UI contains logic to determine when the backend status has changed (ie. when received message has different data to before)

TODO:
* have multiple parallel independent components in the UI (each driven by their own backend data)
* remove the logic (to determine when the backend status has changed) from the UI
* put this logic in the middleware instead
* OR (even better) see if Elastic can send push notifications to the middleware (when the data has changed, so then this logic would reside within Elastic itself)

to start the UI:
    npm run dev

to start Python server:
    cd src; uvicorn main:app

to start Elastic backend:
    docker run --memory=3gb --name es01-test --net elastic -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.1
    
to populate Elastic with data:
    https://www.elastic.co/guide/en/beats/metricbeat/7.15/metricbeat-installation-configuration.html