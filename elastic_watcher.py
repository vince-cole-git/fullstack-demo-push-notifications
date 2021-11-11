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

def publish_message(message):
    if len(message) > 0:
        conn = pika.BlockingConnection( mq_params )
        channel = conn.channel()
        channel.exchange_declare( exchange=mq_exchange, exchange_type='direct' )
        channel.basic_publish( exchange=mq_exchange, routing_key=mq_topic, body=json.dumps(message) )
        conn.close()

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
    try:
        publish_message( es_records )
    except Exception as e:
        print("ERROR: " + str(e))
