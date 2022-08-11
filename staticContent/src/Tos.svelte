<script>
	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';

    import SvelteMarkdown from 'svelte-markdown'

	import Spinner from 'svelte-spinner';

	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });

	const fetchTos = (async () => {
		const result = await fetch(`/static/tos/tos.md`)

		if(!result.ok) {
			return "# feil\nKunne ikke hente regler"
		}
		return await result.text()
	})()

</script>

<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
			<h1>Regler for bruk</h1>
			{#await fetchTos}
			<div class="spinnerContainer">
				<Spinner
					size="50"
					speed="750"
					color="#999"
					thickness="2"
					gap="40"
				/>
			</div>
			{:then data}
            <SvelteMarkdown source={ data } />
			{:catch error}
			<b>Kunne ikke hente regler for bruk - en registrering nå er ikke gyldig</b>
			{/await}
	</Panel>
</main>

<style>
	main {
		display: flex;
		align-items: center;	
		flex-direction: column;

		width: 100%;
	}
	h1 {
		font-weight: 400;
	}

	.spinnerContainer {
		width: 100%;
		display: flex;
		align-items: center;
		flex-direction: column;
	}
	.forgotSuccess {
		width: 100%;
		display: flex;
		align-items: center;
		flex-direction: column;
	}
	.divider {
		height: 2em;
	}
	.error {
		color:#d42b2b;
	}
	
</style>