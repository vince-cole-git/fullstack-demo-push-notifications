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


# all of our 'websocket_endpoint' functions call this function, as soon as the UI opens the socket for that endpoint
# currently, what we do in here is start an infinite loop (until app 'should_exit' is flagged) which runs in its own thread
# each iteration of the loop, we sleep (polling_period_sec) waiting to receive input (if any) from the UI in that period
# the input value controls a flag (is_publishing)
# regardless, after each polling period, we then check is_publishing (if True: perform an Elastic query, check if data is new, if new then send it up to the UI)
#
# TODO: 
# open a client on the Elastic 'push notification' WS
# set up a handler, to fire when Elastic pushes a message (ie. new data) to us
# this needs to be in a thread so the the UI webserver can then also execute as before (and allow the UI to open its websockets to all our 'websocket_endpoint' functions)
# there will be an open WS per channel that the UI wants us to notify it on
# the handler needs to:
# - determine which channel the messsage is for
# - if there is an open WS for that channel, send the message to it
#
async def websocket_handler(websocket: WebSocket, channel = ''):
    
    es_version = "6.5.3"
    es_index = "metricbeat-" + es_version + "-" + datetime.today().strftime("%Y.%m.%d")
    es_query = { "bool": { "must": [ { "term": { "metricset.name": channel.split('.')[-1] } } ] } }

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
                es_result = es.search( index=es_index, body=es_query_body )
                es_record = es_result["hits"]["hits"][0]["_source"]["system"]
            except:
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
		

# connect to the Elastic 'push notifications' websocket 
#from websocket import create_connection
#ws = create_connection("ws://localhost:9400/ws/_changes")
#print("Sending 'Hello, World'...")
#ws.send("Hello, World")
#print("Sent")
#print("Receiving...")
#result =  ws.recv()
#print("Received '%s'" % result)
#ws.close()
import websocket
import _thread
import time

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        print("### opened ###")
        # i = 0
        # while i < 10:
        #     time.sleep(1)
        #     ws.send("Hello %d" % i)
        #     i = i+1
        time.sleep(1)
        ws.close()
        print("thread terminating...")

    _thread.start_new_thread(run, ())

websocket.enableTrace(True)
ws = websocket.WebSocketApp("ws://localhost:9400/ws/_changes",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close)

ws.run_forever()
