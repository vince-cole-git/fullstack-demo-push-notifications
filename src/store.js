import { writable } from 'svelte/store';

const sockets = []
let msgs = {}
const msgStores = {}

function setupWebsocket(channel) {

	msgs[channel] = []
	msgStores[channel] = writable([]);

	const socket = new WebSocket('ws://localhost:8000/ws' + '/' + channel);	
	
	// on WebSocket Connection Opened
	socket.addEventListener('open', function (event) {
		console.log("WebSocket opened (channel: "+channel+")");
	});

	// on WebSocket Connection Closed
	socket.addEventListener('close', function (event) {
		console.log("WebSocket closed (channel: "+channel+")");
	});

	// on WebSocket Message Received
	socket.addEventListener('message', function(event) {
		console.log("WebSocket message received (channel: "+channel+")")
		const msg = JSON.parse(event.data)
		if (msg.channel == channel) {
			msgs[channel] = [ ...(msgs[channel]), JSON.stringify(msg.content) ]
			msgStores[channel].set( msgs[channel] );
		}	
	});

	sockets[channel] = socket
	return msgStores[channel]
}

const sendMessage = (channel, message) => {
	const socket = sockets[channel]
	if (socket.readyState <= 1) {
		socket.send(message);
	}
}

const forChannel = ( channel ) => { return msgStores[channel] }

const clearMessages = ( channel ) => { 
	msgs[channel] = []
	msgStores[channel].set(msgs[channel]) 
}

export default {
	setupWebsocket,
	sendMessage,
	forChannel,
	clearMessages
}