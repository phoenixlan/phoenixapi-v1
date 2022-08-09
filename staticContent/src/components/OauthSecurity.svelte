<script>
	import Spinner from 'svelte-spinner';
	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });

    export let optional = false;

	let securityCheckFetchDone = false
	let securityCheckDone = false
	let securityCheckSuccess = false

    // Handle oauth validation gracefully
	function failOauth() {
		oauthTimeout = null;
		if(securityCheckFetchDone && !securityCheckDone) {
			securityCheckDone = true;
		}
	}
	let oauthTimeout = setTimeout(failOauth, 100);
	async function validateOauth() {
		const result = await fetch('/oauth/client/validate?client_id=' + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri']))
		if(result.status === 200) {
			securityCheckSuccess = true;
		}

		securityCheckFetchDone = true;
		if(oauthTimeout == null) {
			securityCheckDone = true;
		}
	}

    if(optional == false || GET_PARAMS['client_id'] || GET_PARAMS['redirect_uri']) {
	    validateOauth();
    } else {
        securityCheckDone = true;
        securityCheckSuccess = true
    }
</script>
{#if !securityCheckDone}
	<div class="securityContainer">
		<h1>Sjekker sikkerhet</h1>
		<Spinner
					size="50"
			speed="750"
			color="#999"
			thickness="2"
			gap="40"
		/>
	</div>
{:else}
    {#if securityCheckSuccess}
        <slot></slot>
    {:else}
	    <h1>Sikkerhets-feil</h1>
	    <p>Sikkerhets-sjekken feilet. Dette kan være fordi du kommer fra en ikke-godkjent nettside, eller fordi nettleseren din gjør noe rart. Du kan ikke logge inn. Om problemet fortsetter, snakk med <a href="mailto:info@phoenix.no">info@phoenix.no</a></p>
    {/if}

{/if}
<style>
	.securityContainer {
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
	}
</style>