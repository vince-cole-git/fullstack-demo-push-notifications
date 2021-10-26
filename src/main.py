import _thread, time, websocket, asyncio, json
from datetime import datetime

from fastapi import FastAPI, WebSocket
app = FastAPI()


from uvicorn.main import Server
original_handler = Server.handle_exit
class AppStatus:
    es_websocket = None
    es_notifications = {}
    should_exit = False
    @staticmethod
    def handle_exit(*args, **kwargs):
        AppStatus.should_exit = True
        original_handler(*args, **kwargs)
Server.handle_exit = AppStatus.handle_exit


# WebSocket client, connected to Elastic. 
# When it receives a push notification it: determines the channel, then appends the message to the queue for that channel
def ElasticWatcher():

    def on_open(ws):
        def run(*args):
            print("ElasticWatcher: run started")
            while AppStatus.should_exit is False:
                print("ElasticWatcher: waiting")
                time.sleep(1)
            ws.close()
        _thread.start_new_thread(run, ())

    def on_message(ws, message):
        print("ElasticWatcher: message" )
        data = json.loads(message)['_source']
        metric = data['metricset']['name']
        module = data['metricset']['module']
        channel = module + '.' + metric
        content = data[module][metric]
        if channel in AppStatus.es_notifications:
            # the queue exists (because this channel is enabled) so enqueue the message
            print("ElasticWatcher: enqueued message for channel " + channel )
            AppStatus.es_notifications[channel].append(content)
        else:
            # there is no queue (because this channel is disabled) so discard the message   
            print("ElasticWatcher: discarded message for channel " + channel )

    def on_error(ws, error):
        print("ElasticWatcher: error " + str(error))

    def on_close(ws, close_status_code, close_msg):
        print("ElasticWatcher: closed")

    if AppStatus.es_websocket == None:
        AppStatus.es_websocket = websocket.WebSocketApp("ws://localhost:9400/ws/_changes",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        AppStatus.es_websocket.run_forever()

_thread.start_new_thread( ElasticWatcher, () )


# WebSocket server, which the UI connects to (via various endpoint functions, defined below it)
# there is an endpoint per channel (these can mean anything we want)
# in this demo (as it uses metricbeat data) we have a channel for each of the different metrics
# as each endpoint calls this (once) and it loops forever, there is an instance of this running per channel
async def websocket_handler(ui_websocket: WebSocket, channel):
    
    is_channel_enabled = False
    i = 0
    await ui_websocket.accept()
    print( str(datetime.now()) + " - WebSocket accepted (channel: " + channel + ")" )

    # loop forever
    while AppStatus.should_exit is False:

        # wait for (up to) 1 second, for a command, to enable/disable this channel
        try:
            i = int( await asyncio.wait_for( ui_websocket.receive_text(), 1 ) )
            print( str(datetime.now()) + " - server received input " + str(i) + " (channel: " + channel + ")")
            is_channel_enabled = (i > 0)
        except:
            pass

        # create/delete the message queue for this channel, if enabling/disabling it        
        if is_channel_enabled:
            if channel not in AppStatus.es_notifications:
                AppStatus.es_notifications[channel] = []
        else:        
            AppStatus.es_notifications.pop( channel, None ) 

        # if this channel is enabled, dequeue its messages and send them to the UI
        if is_channel_enabled:
            print("checking message queue for channel ("+channel+"), num items = " + str(len(AppStatus.es_notifications[channel])) )
            try:
                content = AppStatus.es_notifications[channel].pop()
            except:
                content = ''
            if content != '':
                print( str(datetime.now()) + " - sending ws payload: " + json.dumps(content) )
                await ui_websocket.send_json( content )

    await ui_websocket.close()
    print( str(datetime.now()) + " - UI WebSocket closed (channel: " + channel + ")")


### ENDPOINTS ###

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
