import sys, time, json, pika
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

metric = sys.argv[1] # e.g. "system.cpu"
mq_topic = metric
mq_exchange = "metrics-demo"
mq_params = pika.ConnectionParameters(host='localhost')

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
es_version = "7.15.2"
es_index = "metricbeat-" + es_version

polling_period_sec = 1   # how often we want to check Elastic
metrics_offset_sec = 10  # how often Metricbeat pushes to Elastic (because timestamps are for metric capture, not push)

def get_timestamp():
    return ( datetime.today() - timedelta(seconds=metrics_offset_sec) ).isoformat()

def publish_messages(messages):
    if len(messages) > 0:
        conn = pika.BlockingConnection( mq_params )
        channel = conn.channel()
        channel.exchange_declare( exchange=mq_exchange, exchange_type='direct' )
        for msg in messages:
          print("\npublishing message:\n" + json.dumps(sorted_dict(msg)))
          channel.basic_publish( exchange=mq_exchange, routing_key=mq_topic, body=json.dumps(sorted_dict(msg)) )
        conn.close()

def sorted_dict(d):
    return {k: sorted_dict(v) if isinstance(v, dict) else v
        for k, v in sorted(d.items())}
            
timestamp_old = get_timestamp()
while True:

    # prepare the query
    time.sleep(polling_period_sec)
    timestamp_now = get_timestamp()
    es_query = { "bool": { "must": [ 
        { "term": { "event.dataset": sys.argv[1] } }, 
        { "range": { "@timestamp": { "gte" : timestamp_old, "lt" : timestamp_now } } } 
    ]}}        
    timestamp_old = timestamp_now

    # execute the query
    es_records = []
    try:
        es_results = es.search( index=es_index, body={ "query": es_query, "size": 10000, "sort": { "@timestamp": "desc"} } )
        es_records = es_results["hits"]["hits"]
    except Exception as e:
        print("ERROR: " + str(e))
        es_records = []

    # publish the result
    (s,m) = metric.split(".")
    try:
        publish_messages([ {k:r["_source"][s][m][k] for k in r["_source"][s][m]} for r in es_records ])
    except Exception as e:
        print("ERROR: " + str(e))
