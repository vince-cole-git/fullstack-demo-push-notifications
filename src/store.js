import { writable } from 'svelte/store';

const sockets = []
const clients = []
let msgs = {}
const msgStores = {}

function setupWebsocket(channel, newState) {

	// prepare the message store
	if (msgs[channel] === undefined) {
		msgs[channel] = []
	}
	if (msgStores[channel] === undefined) {	
		msgStores[channel] = writable([]);
	}	

	// toggling the state? 
    if ((typeof newState) !== "undefined") {
		const oldState = (!!(sockets[channel]) && !!(clients[channel]))
		if (newState !== oldState) {
			// define handlers
			function onMessage(message) {
				msgs[channel] = [ message.body, ...(msgs[channel]) ]
				msgStores[channel].set( msgs[channel] );
			}
			function onOpened() {
				clients[channel].subscribe("/exchange/metrics-demo/"+channel, onMessage)
			}
			function onClosed() {
				clients[channel] = undefined
				sockets[channel] = undefined
			}
			// set the new state
			if (newState) {
				// opened
				sockets[channel] = new WebSocket('ws://localhost:15674/ws');
				clients[channel] = Stomp.over( sockets[channel] );
				clients[channel].connect('guest', 'guest', onOpened, onClosed, '/');
			} else {
				// closed
				clients[channel].disconnect()
				sockets[channel].close()
				onClosed()
			}	
		}
	}

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