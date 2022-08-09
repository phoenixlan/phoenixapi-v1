<script>
	export let name;

	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';

	import { Textfield, Button } from 'svelte-mui';

	let login="";

	let error = "";

	async function handleForgot(e) {
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

		} else {
			error = resp.error
		}
	}
</script>

<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
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
		<Button color="primary" raised=true fullWidth=true form="loginForm" type="submit">Submit</Button>
		<p>Du kan også <a href="register.html">registrere deg</a> eller <a href="login.html">logge inn</a></p>
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