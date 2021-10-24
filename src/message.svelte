<script>
	export let message;
	export let direction = "right";
	export let highlight = "#ffffff";
	export let num_ticks = 0;
</script>

<p style="text-align: {direction}; background-color: {highlight}" >
	Age of this message: {num_ticks}
	<br/>
	<br/>
	{message}
</p>