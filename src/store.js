import { writable } from 'svelte/store';

const sockets = []
const clients = []
let msgs = {}
const msgStores = {}

// create the message store
function createChannel(channel) {
	msgs[channel] = [false]
	msgStores[channel] = writable([]);
	return msgStores[channel]
}

// empty the message store
const clearMessages = ( channel ) => { 
	msgs[channel] = []
	msgStores[channel].set(msgs[channel]) 
}

// define handlers and open or close a websocket
function toggleUpdates(channel, isActive) {

	function onMessage(message) {
		msgs[channel] = [ message.body, ...(msgs[channel]) ]
		msgs[channel][0] = true
		msgStores[channel].set( msgs[channel] );
	}
	function onOpened() {
		console.log("######################## WEBSOCKET OPENED ########################", channel)
		clients[channel].subscribe("/exchange/metrics-demo/"+channel, onMessage)
		msgs[channel][0] = true
		msgStores[channel].set( msgs[channel] );
	}
	function onClosed() {
		console.log("######################## WEBSOCKET CLOSED ########################", channel)
		clients[channel] = undefined
		sockets[channel] = undefined
		msgs[channel][0] = false
		msgStores[channel].set( msgs[channel] );
	}

	if (isActive) {
		sockets[channel] = new WebSocket('ws://localhost:15674/ws');
		clients[channel] = Stomp.over( sockets[channel] );
		clients[channel].connect('guest', 'guest', onOpened, onClosed, '/');
	} else {
		clients[channel].disconnect()
		sockets[channel].close()
		onClosed()
	}	
}

export default {
	createChannel,
	clearMessages,
	toggleUpdates
}