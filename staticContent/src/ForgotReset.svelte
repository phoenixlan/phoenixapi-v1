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

	let password = "";
	let passwordRepeat = "";

	let error = "";

	const STATES = {
		input: "INPUT",
		loading: "LOADING",
		success: "SUCCESS",
	}

	let state = STATES.input;

	const validateCode = (async () => {
		const result = await fetch(`/password_reset_code/${GET_PARAMS['code']}`)

		return result.ok
	})()

	async function handleForgot(e) {
		state = STATES.loading;
		try {
			const result = await fetch(`/password_reset_code/${GET_PARAMS['code']}`, {
				method: 'POST',
				body: JSON.stringify({
					password,
					passwordRepeat
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
			{#await validateCode}
			<div class="spinnerContainer">
				<Spinner
					size="50"
					speed="750"
					color="#999"
					thickness="2"
					gap="40"
				/>
			</div>
			{:then success}
			{#if success}
				<h1>Skriv inn nytt passord</h1>
				<form id="loginForm" on:submit|preventDefault={handleForgot}>
					<Textfield
						name="password"
						autocomplete="off"
						type="password"
						required
						bind:value={password}
						label="Nytt passord"
					/>

					<Textfield
						name="passwordRepeat"
						autocomplete="off"
						type="password"
						required
						bind:value={passwordRepeat}
						label="Nytt passord(igjen)"
					/>
				</form>
				<p><b>Merk: </b>Å bytte passord vil også logge deg ut alle steder der du er logget inn</p>
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

					<h1>Du har byttet passord</h1>
					<p><a href={'login.html?client_id=' + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>Logg inn</a></p>
				</div>
				{:else}
				<Button color="primary" raised=true fullWidth=true form="loginForm" type="submit">Submit</Button>
				{/if}
			{:else}
				<h1>Feil</h1>
				<p>Koden kan ikke brukes. Prøv på nytt.</p>
				<p>Sliter du med å endre passord? Kontakt <a href="info@phoenixlan.no">info@phoenixlan.no</a></p>

			{/if}
			{:catch error}
			<h1>Feil</h1>
			<p>Oops, kunne ikke validere forespørselen din</p>
			{/await}
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

	.spinnerContainer{
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