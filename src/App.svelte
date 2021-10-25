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
		"system.process.summary",
		"system.socket.summary",
		"system.fsstat",
		"system.uptime"
	]
	
	onMount( () => {
		//store.setupChannels( channels )
	})

</script>

<h1>WebSocket Demo</h1>

<div style="vertical-align:top">
	{#each channels as channel}
		<Widget {channel} />
	{/each}
</div>