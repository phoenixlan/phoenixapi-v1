<script>
	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';

    import SvelteMarkdown from 'svelte-markdown'

	import { Button } from 'svelte-mui';

	import Spinner from 'svelte-spinner';

    let loading = false;
    let consentWithdrawn = false; 

	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });

	const fetchTos = (async () => {
		const result = await fetch(`/consent_withdrawal_code/${GET_PARAMS['uuid']}`)
		if(!result.ok) {
            throw await result.json()['error']
		}
		return await result.json()
	})()

	const withdrawConsent = async () => {
		const result = await fetch(`/consent_withdrawal_code/${GET_PARAMS['uuid']}/use`, {
            method: "POST"
        })
		if(!result.ok) {
            throw await result.json()['error']
		}
		return await result.json()
	}

    const get_consent_label = (label) => {
        if(label == "ConsentType.event_notification") {
            return "ved registrering";
        }
        return "annen grunn"
    }

    const removeConsent = async () => {
        await withdrawConsent();
        consentWithdrawn = true;
    }

</script>

<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
        {#if loading}
			<div class="spinnerContainer">
				<Spinner
					size="50"
					speed="750"
					color="#999"
					thickness="2"
					gap="40"
				/>
			</div>
        {:else}
            {#if consentWithdrawn}
            <h1>Samtykket er fjernet</h1>
            {:else}
                <h1>Ta tilbake samtykke til e-poster utenom arrangementet</h1>
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
                <h2>Informasjon om samtykket</h2>
                <p>Tid: {new Date(data.created*1000)}</p>
                <p>Når: {get_consent_label(data.consent_type)}</p>
                <h2>Trekk tilbake samtykke</h2>
                <p>Du kan trekke tilbake samtykke til at vi sender deg promosjons e-post. Merk at du vil enda motta e-post med informasjon om arrangementer du er crew eller deltaker i, da det er <i>nødvendig for gjennomføring av vår del av "avtalen" vi inngår når du deltar</i> </p>
                <p>Trykk på knappen for å fjerne ditt samtykke til å motta e-post fra oss.</p>
                <Button color="primary" raised=true fullWidth=true form="registerForm" on:click={removeConsent}>Fjern samtykke</Button>
                {:catch error}
                <b>En feil skjedde: {error}</b>
                {/await}
            {/if}

        {/if}
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