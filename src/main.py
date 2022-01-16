from fastapi import FastAPI, WebSocket
app = FastAPI()

from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

from datetime import datetime
import asyncio, json


from uvicorn.main import Server
original_handler = Server.handle_exit
class AppStatus:
    should_exit = False
    @staticmethod
    def handle_exit(*args, **kwargs):
        AppStatus.should_exit = True
        original_handler(*args, **kwargs)
Server.handle_exit = AppStatus.handle_exit

prev_records = {
    "system.process" : '',
    "system.network" : '',
    "system.filesystem" : '',
    "system.cpu" : '',
    "system.load" : '',
    "system.memory" : '',
    "system.process_summary" : '',
    "system.fsstat" : '',
    "system.uptime" : ''
}

async def websocket_handler(websocket: WebSocket, channel = ''):
    
    es_version = "7.15.2"
    es_index = "metricbeat-" + es_version
    print( "querying ES index: " + es_index )
    es_query = { "bool": { "must": [ { "term": { "event.dataset": channel } } ] } }

    channel_split = channel.split('.')

    # TODO can we push from Elastic instead of polling it?
    polling_period_sec = 1
    
    i = 0
    await websocket.accept()
    print( str(datetime.now()) + " - WebSocket accepted (channel: " + channel + ")" )

    is_publishing = False
    while AppStatus.should_exit is False:

        try:
            i = int( await asyncio.wait_for( websocket.receive_text(), polling_period_sec ) )
            print( str(datetime.now()) + " - server received input " + str(i) + " (channel: " + channel + ")")
            is_publishing = (i > 0)
        except:
            i = i

        if is_publishing:
            print( str(datetime.now()) + " - querying elastic..." + " (channel: " + channel + ")")
            try:
                es_query_body = { "query": es_query, "size": 1, "sort": { "@timestamp": "desc"} }
                print( es_query_body )
                es_result = es.search( index=es_index, body=es_query_body )
                print(es_result)
                es_record = es_result["hits"]["hits"][0]["_source"][ channel_split[0] ][ channel_split[1] ]
            except Exception as err:
                print("Exception: " + str(err))
                es_record = ''

            if (es_record != '') and (es_record != prev_records[channel] ):
                prev_records[channel] = es_record
                payload = { "channel": channel, "content": es_record }
                print( str(datetime.now()) + " - sending ws payload: " + json.dumps(payload) )
                await websocket.send_json( payload )

    await websocket.close()
    print( str(datetime.now()) + " - WebSocket closed (channel: " + channel + ")")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket)

@app.websocket("/ws/system.process")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.process")
		
@app.websocket("/ws/system.network")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.network")
		
@app.websocket("/ws/system.filesystem")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.filesystem")
		
@app.websocket("/ws/system.cpu")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.cpu")
		
@app.websocket("/ws/system.load")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.load")
		
@app.websocket("/ws/system.memory")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.memory")

@app.websocket("/ws/system.process_summary")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.process_summary")
		
@app.websocket("/ws/system.fsstat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.fsstat")

@app.websocket("/ws/system.uptime")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, "system.uptime")
		