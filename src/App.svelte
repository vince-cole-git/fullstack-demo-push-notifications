<script>
	import { onMount } from 'svelte';

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
	
</script>

<h1>WebSocket Demo</h1>

<div style="vertical-align:top">
	{#each channels as channel}
		<Widget {channel} />
	{/each}
</div>