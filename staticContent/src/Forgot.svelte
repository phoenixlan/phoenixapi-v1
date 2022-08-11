<script>
	export let name;

	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';

	import Fa from 'svelte-fa/src/fa.svelte'
	import { faCheck } from '@fortawesome/free-solid-svg-icons/index.es'

	import Spinner from 'svelte-spinner';

	import OauthSecurity from './components/OauthSecurity.svelte';

	import { Textfield, Button } from 'svelte-mui';

	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });

	let login="";

	let error = "";

	const STATES = {
		input: "INPUT",
		loading: "LOADING",
		success: "SUCCESS",
	}

	let state = STATES.input;

	async function handleForgot(e) {
		state = STATES.loading;
		try {
			const result = await fetch('/user/forgot', {
				method: 'POST',
				body: JSON.stringify({
					login: login,
				}),
				headers: {
					"Content-Type": "application/json"
				}
			})
			const resp = await result.json()
			if(result.status === 200) {
				state = STATES.success;
			} else {
				state = STATES.input;
				error = resp.error
			}
		} catch(e) {
			state = STATES.input;
			error = "Internal error";
		}
	}
</script>

<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
		<OauthSecurity>
			<h1>Glemt passord</h1>
			<p>Har du glemt passordet ditt kan du skrive inn e-posten din her. Eksisterer det en konto for den addressen får du en e-post med en lenke så du kan tilbakestille passordet.</p>
			<p>Skriver du inn brukernavnet ditt vil en e-post sendes til kontoen registrert til brukernavnet, dersom den eksisterer</p>
			<form id="loginForm" on:submit|preventDefault={handleForgot}>
				<Textfield
					name="login"
					autocomplete="off"
					required
					bind:value={login}
					label="E-post addresse eller brukernavn"
				/>
			</form>
			{#if error}
				<p class="error">{error}</p>
			{/if}
			{#if state == STATES.loading}
			<div class="spinnerContainer">
				<Spinner
					size="50"
					speed="750"
					color="#999"
					thickness="2"
					gap="40"
				/>
			</div>
			{:else if state == STATES.success}
			<div class="forgotSuccess">
				<Fa icon={faCheck} style="font-size: 3em; color: green;"/>
				<h1>Sjekk innboksen din</h1>
				<p>Merk at det kan ta minutter før mailen kommer. Sjekk også søppelpost.</p>
			</div>
			{:else}
			<Button color="primary" raised=true fullWidth=true form="loginForm" type="submit">Submit</Button>
			{/if}
			<p>Du kan også <a href={"register.html?client_id=" + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>registrere deg</a> eller <a href={"login.html?client_id=" + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>logge inn</a></p>
		</OauthSecurity>
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