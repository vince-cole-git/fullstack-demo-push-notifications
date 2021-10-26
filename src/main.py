import elasticsearch
from fastapi import FastAPI, WebSocket
app = FastAPI()

from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

from datetime import datetime
import asyncio, json


from uvicorn.main import Server
original_handler = Server.handle_exit
class AppStatus:
    es_websocket = None
    es_notifications = []
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
    
    if AppStatus.es_websocket == None:
        _thread.start_new_thread( ElasticWatcher, () )

    es_version = "6.5.3"
    es_index = "metricbeat-" + es_version + "-" + datetime.today().strftime("%Y.%m.%d")
    es_query = { "bool": { "must": [ { "term": { "metricset.name": channel.split('.')[-1] } } ] } }

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
            print("checking notifications array, length: " + str(len(AppStatus.es_notifications)) )
            try:
                es_record = AppStatus.es_notifications.pop()
            except:
                es_record = ''
            if es_record != '':
                json_data = json.loads(es_record)
                print(json_data)
                if json_data['_source']['metricset']['name'] == channel.split('.')[-1]:
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





import websocket
import _thread
import time
import threading


# async def waitForNextNotification():
#     message = None
#     while AppStatus.should_exit is False:
#         time.sleep(1)
#         try:
#             message = notifications.pop(0)
#         except:
#             message = None    
#         if message != None:    
#             print( str(datetime.now()) + " - (ELASTIC) - notification received" )
#             return message

@app.websocket("/ws/elastic")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    print( str(datetime.now()) + " - WebSocket accepted (ELASTIC)" )
    await websocket.send_json({ "channel":"ELASTIC", "content":"Accepted" })
    
    #_thread.start_new_thread( ElasticWatcher, () )

    #while AppStatus.should_exit is False:
    #    time.sleep(1)
    #    await ui_websocket.send_json( await waitForNextNotification() )
    # while AppStatus.should_exit is False:
    #     time.sleep(1)

    # await ui_websocket.close()
    # print( str(datetime.now()) + " - WebSocket closed (ELASTIC)" )


def ElasticWatcher():
    
    def on_message(ws, message):
        print("ElasticWatcher: message")
        AppStatus.es_notifications.append(message)
        print("ElasticWatcher: there are now " + str(len(AppStatus.es_notifications)) + " messages")

    def on_error(ws, error):
        print("ElasticWatcher: error " + error)

    def on_close(ws, close_status_code, close_msg):
        print("ElasticWatcher: closed")

    def on_open(ws):
        #
        async def run(*args):
            print("ElasticWatcher: run started")
            while AppStatus.should_exit is False:
                await time.sleep(1)
            ws.close()
            print("ElasticWatcher: run stopped")
        #
        _thread.start_new_thread(run, ())

    if AppStatus.es_websocket == None:
       
        AppStatus.es_websocket = websocket.WebSocketApp("ws://localhost:9400/ws/_changes",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        print('running the ElasticWatcher websocket forever...')
        AppStatus.es_websocket.run_forever()

