<script>
	import { count } from './stores.js';

	function randomize() {
		count.update(n => Math.round( 100 * Math.random() ));
	}
    
</script>

<button on:click={randomize}>
	@
</button>