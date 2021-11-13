import sys, time, json, pika
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

metric = sys.argv[1] # e.g. "system.cpu"
mq_topic = metric
mq_exchange = "metrics-demo"
mq_params = pika.ConnectionParameters(host='localhost')

es = Elasticsearch( [{'host': 'localhost', 'port': 9200}], http_auth=('elastic', '31p3xaJcc3Y9VmKeNXyG') )
es_version = "7.15.2"
es_index = "metricbeat-" + es_version
es_polling_period_sec = 5   # how often we want to check
es_metrics_offset_sec = 10  # how often metrics are captured (because timestamps are for capture, not ingest)

def ksort(d):
    return {k: ksort(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}

def get_timestamp(offset=0):
    return ( datetime.today() - timedelta(seconds=offset) ).isoformat()

def log_debug(message):
    print( get_timestamp() + ": DEBUG : " + message )

def log_error(message):
    print( get_timestamp() + ": ERROR : " + message )

def prepare_query( timestamp_min, timestamp_max ):
    log_debug( 'query date range is ' + timestamp_min + " - " + timestamp_max )
    return { "bool": { "must": [ 
        { "term": { "event.dataset": sys.argv[1] } }, 
        { "range": { "@timestamp": { "gte" : timestamp_min, "lt" : timestamp_max } } } 
    ]}}

def execute_query(es_query):
    es_body = { "query": es_query, "size": 1000, "sort": { "@timestamp": "desc"} }
    return es.search( index=es_index, body=es_body )["hits"]["hits"]

def publish_result(messages):
    if len(messages) > 0:
        conn = pika.BlockingConnection( mq_params )
        channel = conn.channel()
        channel.exchange_declare( exchange=mq_exchange, exchange_type='direct' )
        for msg in messages:
          log_debug( "publish (" + mq_topic + ") " + json.dumps(ksort(msg)) )
          channel.basic_publish( exchange=mq_exchange, routing_key=mq_topic, body=json.dumps(ksort(msg)) )
        conn.close()

timestamp_min = get_timestamp(es_metrics_offset_sec)
while True:

    # prepare the query 
    time.sleep(es_polling_period_sec)
    timestamp_max = get_timestamp(es_metrics_offset_sec)
    es_query = prepare_query(timestamp_min, timestamp_max)
    timestamp_min = timestamp_max

    # execute the query
    try:
        es_records = execute_query(es_query)
    except Exception as e:
        log_error( str(e) )
        continue

    # publish the result    
    (s,m) = metric.split(".")
    try:
        publish_result([ {k:r["_source"][s][m][k] for k in r["_source"][s][m]} for r in es_records ])
    except Exception as e:
        log_error( str(e) )
