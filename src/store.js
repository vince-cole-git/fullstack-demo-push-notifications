import { writable } from 'svelte/store';

let msgs = []
const msgStore = writable([]);

const socket = new WebSocket('ws://localhost:8000/ws');

// Connection opened
socket.addEventListener('open', function (event) {
    console.log("WebSocket opened");
});

// Connection closed
socket.addEventListener('close', function (event) {
    console.log("WebSocket closed");
});

// Listen for messages
socket.addEventListener('message', function(event) {
	console.log("WebSocket message received")
	
	const msg = event.data
	const is_changed = (msgs.length < 1 ) || (msgs[0].value != msg)
	const num_ticks = is_changed ? 0 : (msgs[0].num_ticks + 1)

	console.log( "status has " + ( is_changed ? '' : 'not' ) + " changed" )

	msgs = [{value: msg, is_changed: is_changed, num_ticks: num_ticks}]
	msgStore.set(msgs);
});


const sendMessage = (message) => {
	if (socket.readyState <= 1) {
		socket.send(message);
	}
}

export default {
	subscribe: msgStore.subscribe,
	sendMessage
}