<script>
	import { onMount } from 'svelte';
	//import store from './store.js';

	import Widget from './widget.svelte';

	const channels = [
		"system.process",
		"system.network",
		"system.filesystem",
		"system.cpu",
		"system.load",
		"system.memory",
		"system.process_summary",
		"system.fsstat",
		"system.uptime"
	]
	
	onMount( () => {
		//store.setupChannels( channels )
	})

	let socket;
	function onStart() {
		socket = new WebSocket('ws://localhost:8000/ws/elastic');
	
		// on WebSocket Connection Opened
		socket.addEventListener('open', function (event) {
			console.log("WebSocket opened (ELASTIC)");
		});

		// on WebSocket Connection Closed
		socket.addEventListener('close', function (event) {
			console.log("WebSocket closed (ELASTIC)");
		});

		// on WebSocket Message Received
		socket.addEventListener('message', function(event) {
			console.log("WebSocket message received (ELASTIC) =>")
			const msg = JSON.parse(event.data)
			console.log( msg )
			//msgs[channel] = [ JSON.stringify(msg.content), ...(msgs[channel]) ]
			//msgStores[channel].set( msgs[channel] );
		});	
	}

</script>

<h1>WebSocket Demo</h1>

<p><input type="button" on:click={onStart} value="Start" /></p>

<div style="vertical-align:top">
	{#each channels as channel}
		<Widget {channel} />
	{/each}
</div>

