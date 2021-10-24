from fastapi import FastAPI, WebSocket
app = FastAPI()

from pprint import pprint

import subprocess
from datetime import datetime

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         command = await websocket.receive_text()        
#         process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
#         process.wait()
#         data = str(process.stdout.readlines()[0], 'utf-8')
#         await websocket.send_text(f"Command ({command}) response is: {data}")

from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

import asyncio


from uvicorn.main import Server
original_handler = Server.handle_exit
class AppStatus:
    should_exit = False
    @staticmethod
    def handle_exit(*args, **kwargs):
        AppStatus.should_exit = True
        original_handler(*args, **kwargs)
Server.handle_exit = AppStatus.handle_exit


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    i = 0
    await websocket.accept()
    print( str(datetime.now()) + " - WebSocket accepted" )

    is_publishing = False
    while AppStatus.should_exit is False:

        try:
            i = int( await asyncio.wait_for( websocket.receive_text(), 1 ) )
            print( str(datetime.now()) + " - server received input " + str(i) )
            is_publishing = (i > 0)
        except:
            #print( str(datetime.now()) + " - bad input or timeout, ignoring..." )
            i = i

        if is_publishing:
            print( str(datetime.now()) + " - querying elastic..." )
            data = es.search( index="metricbeat-*", body={ "query":{"match_all":{}}, "size": 1, "sort": { "@timestamp": "desc"} } )
            await websocket.send_text( "Elastic Data is: " + str(data["hits"]["hits"][0]) )

    await websocket.close()
    print( str(datetime.now()) + " - WebSocket closed" )
