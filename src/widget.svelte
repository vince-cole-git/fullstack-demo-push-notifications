<script>
	export let channel = ''
	import { onMount } from 'svelte';
	import store from './store.js';

	let isUpdating = false
	let myMessages = []

	onMount( () => {
		const mystore = store.createChannel(channel)
		mystore.subscribe( newState => { isUpdating = newState.shift(); myMessages = newState; })
	})

	const onClearMessages = () => store.clearMessages(channel)
	const onToggleUpdates = () => store.toggleUpdates(channel, !isUpdating)

</script>

<fieldset style="width:20em; display: inline-block; float: left">
	<legend>[ {channel} ]</legend>
	<p>
		Updating? <input type="checkbox" on:change={onToggleUpdates} bind:checked={isUpdating} />
		&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
		<input type="button" on:click={onClearMessages} value="Clear!" />
	</p>

	<p><strong>Count: {myMessages.length}</strong></p>
	{#each myMessages as message}
	<p>
		{message}
	</p>
	{/each}

</fieldset>
