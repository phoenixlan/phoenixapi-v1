<script>
	export let name;

	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';

	import { Textfield, Button } from 'svelte-mui';
import OauthSecurity from './components/OauthSecurity.svelte';

	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });


	let username="";
	let password = "";

	let error = "";

	async function handleLogin(e) {
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
		if(result.status === 200) {
			const redirectUri = GET_PARAMS['redirect_uri'];

          	console.log("redirect uri: " + redirectUri);
    		window.location = redirectUri + "?code=" + resp.code;

		} else {
			error = resp.error
		}
	}
</script>

<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
		<OauthSecurity>
			<h1>Logg inn</h1>
			<p><i>Du bruker den samme kontoen for alle tjenester hos Phoenix LAN</i></p>
			<form id="loginForm" on:submit|preventDefault={handleLogin}>
				<Textfield
			        name="username"
			        autocomplete="off"
			        required
			        bind:value={username}
			        label="Brukernavn eller e-post addresse"
			        message="Både brukernavn og e-post addresse er gyldig"
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
			<Button color="primary" raised=true fullWidth=true form="loginForm" type="submit">Submit</Button>
			<p>Du kan også <a href={'register.html?client_id=' + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>registrere deg</a></p>
			<p><a href="forgot.html">Glemt passord?</a></p>
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

	.divider {
		height: 2em;
	}
	.error {
		color:#d42b2b;
	}
	
</style>