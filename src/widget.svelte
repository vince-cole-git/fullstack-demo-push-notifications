<script>
	export let channel = ''

	import { onMount } from 'svelte';
	import store from './store.js';
	
	let messages = []
	let isChecked = false

	function onToggleFlow() {} 
	function onClearMessages() {} 

	let mystore = null

	onMount( () => {
		mystore = store.setupWebsocket(channel)
		mystore.sendMessage = store.sendMessage
		mystore.clearMessages = store.clearMessages

		mystore.subscribe( x => { messages = x })

		onToggleFlow = function(){ mystore.sendMessage( channel, isChecked ? "0" : "1" ) }
		onClearMessages = function(){ mystore.clearMessages( channel ) }
	})
</script>

<fieldset style="width:20em; display: inline-block; float: left">
	<legend>[ {channel} ]</legend>
	<p>
		Subscribe? <input type="checkbox" on:change={onToggleFlow} bind:checked={isChecked} />
		&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
		<input type="button" on:click={onClearMessages} value="Clear!" />
	</p>

	<p><strong>Count: {messages.length}</strong></p>
	{#each messages as message}
	<p>
		{message}
	</p>
	{/each}

</fieldset>
