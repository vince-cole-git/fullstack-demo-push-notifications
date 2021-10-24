<script>
	import { onMount } from 'svelte';
	import store from './store.js';
	import Message from './message.svelte';
	let message = '';
	let messages = [];
	let is_checked = false

	onMount(() => {
		store.subscribe(currentMessage => {
				messages = [...messages, currentMessage];
		})
	})
	
	function onToggleFlow() {
		store.sendMessage( is_checked ? "0" : "1" );
	}

$: mystore = $store
</script>

<h1>WebSocket Demo</h1>


<p>
	Subscribe? <input type="checkbox" on:change={onToggleFlow} bind:checked={is_checked} />
</p>


{#if is_checked}
	<h1>Status</h1>
	{#each mystore as {value, is_changed, num_ticks}, i}
			<Message num_ticks={num_ticks} message={value} highlight={is_changed ? '#ffff00' : '#ffffff'} direction="left" />
	{/each}
{/if}