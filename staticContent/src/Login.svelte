<script>
	export let name;

	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';

	import Spinner from 'svelte-spinner';

	import { Textfield, Button } from 'svelte-mui';
	import OauthSecurity from './components/OauthSecurity.svelte';

	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });


	let username="";
	let password = "";

	let error = "";
	let loading = false;

	async function handleLogin(e) {
		loading = true;
		console.log("login");
		
		const result = await fetch('/oauth/auth', {
  			method: 'POST',
  			body: JSON.stringify({
  				login: username,
  				password: password
  			}),
  			headers: {
  				"Content-Type": "application/json"
  			}
  		})
		const resp = await result.json()
		if(result.ok) {
			const redirectUri = GET_PARAMS['redirect_uri'];

          	console.log("redirect uri: " + redirectUri);

			let args = "?code=" + resp.code
			if('state' in GET_PARAMS){
				args = args +  "&state="+ encodeURIComponent(GET_PARAMS['state'])
			}
    		window.location = redirectUri + args;

		} else {
			error = resp.error
		}
		loading = false;
	}
</script>

<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
		<OauthSecurity>
			<h1>Logg inn</h1>
			<p><i>Du bruker den samme kontoen for alle tjenester hos Phoenix LAN</i></p>
			<p><b>NB: Vi støtter ikke lenger å logge inn med brukernavn - vi vil senere bruke dette som display-navn</b></p>
			<form id="loginForm" on:submit|preventDefault={handleLogin}>
				<Textfield
			        name="username"
			        autocomplete="off"
			        required
			        bind:value={username}
			        label="E-post addresse"
			        message="Skriv inn e-post addressen du registrerte med"
			    />
				<Textfield
					type="password"
					name="password"
					autocomplete="off"
					required
					bind:value={password}
					label="Passord"
				/>
			</form>
			{#if error}
				<p class="error">{error}</p>
			{/if}
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
			<Button color="primary" raised=true fullWidth=true form="loginForm" type="submit">Submit</Button>
			{/if}
			<p>Du kan også <a href={'register.html?client_id=' + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>registrere deg</a></p>
			<p><a href={"forgot.html?client_id=" + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>Glemt passord?</a></p>
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

	.spinnerContainer {
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