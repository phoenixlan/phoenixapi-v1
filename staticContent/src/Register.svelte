<script>
	export let name;

	import Spinner from 'svelte-spinner';

	import Logo from './components/Logo.svelte';
	import Panel from './components/Panel.svelte';
	import Fa from 'svelte-fa/src/fa.svelte'
	import { faCheck } from '@fortawesome/free-solid-svg-icons/index.es'


	import { Textfield, Button, Radio, Datefield, Checkbox } from 'svelte-mui';
	import OauthSecurity from './components/OauthSecurity.svelte';

	var GET_PARAMS = {};
   	location.search.substr(1).split("&").forEach(function(item) {GET_PARAMS[item.split("=")[0]] = decodeURIComponent(item.split("=")[1]) });

	let username="";

	let firstname = "";
	let surname = "";

	let password = "";
	let passwordRepeat = "";

	let email = "";

	let genderRadio = "male";

	let phone = "";
	let guardianPhone = "";
	let address = "";
	let zip = "";

	let tosAccepted = false;

	let dateOfBirth = new Date(2005, 0, 1);

	const STATES = {
		input: "INPUT",
		loading: "LOADING",
		success: "SUCCESS",
		failure: "FAILURE"
	}

	let registerState = STATES.input;
	let error = "";

	function getAge(birthDate) {
    	var today = new Date();
    	var age = today.getFullYear() - birthDate.getFullYear();
    	var m = today.getMonth() - birthDate.getMonth();
    	if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    	    age--;
    	}
    	return age;
	}

	async function handleRegister(e) {
		registerState = STATES.loading;
		console.log("register");
		console.log(dateOfBirth);
		const month = ((dateOfBirth.getMonth()+1)+"").padStart(2, "0")
		const day = ((dateOfBirth.getDate()+1)+"").padStart(2, "0")

		const payload = {
			username,
			firstname,
			surname,
			password,
			passwordRepeat,
			dateOfBirth: `${dateOfBirth.getFullYear()}-${month}-${day}`,
			email,
			gender: genderRadio,
			phone,
			guardianPhone,
			address,
			zip,
			clientId: GET_PARAMS['client_id']
		}
		console.log(payload);
		
		const result = await fetch('/user/register', {
  			method: 'POST',
  			body: JSON.stringify(payload),
  			headers: {
  				"Content-Type": "application/json"
  			}
  		})
		console.log(result)
		if(result.ok) {
			registerState = STATES.success
		} else {

			const resp = await result.json()
			registerState = STATES.failure;
			error = resp.error
		}
	}
</script>
<main>
	<Logo />
	<div class="divider"> </div>
	<Panel>
		<OauthSecurity optional=true>
			<form id="registerForm" on:submit|preventDefault={handleRegister}>
				<h1>Registrer deg</h1>
				<Textfield
					name="username"
					autocomplete="off"
					required
					bind:value={username}
					label="Brukernavn"
					message="Ditt brukernavn"
				/>
				<Textfield
					name="firstname"
					autocomplete="on"
					required
					bind:value={firstname}
					label="Fornavn"
					message="Fornavnet ditt"
				/>
				<Textfield
					name="surname"
					autocomplete="on"
					required
					bind:value={surname}
					label="Etternavn"
					message="Ditt etternavn"
				/>
				<Textfield
					type="password"
					name="password"
					autocomplete="off"
					required
					bind:value={password}
					label="Passord"
					message="Ditt passord"
				/>
				<Textfield
					type="password"
					name="passwordrepeat"
					autocomplete="off"
					required
					bind:value={passwordRepeat}
					label="Gjenta passord"
					message="Skriv det samme passordet igjen"
				/>
				<Textfield
					type="email"
					name="email"
					autocomplete="on"
					required
					bind:value={email}
					label="E-post addresse"
					message="Din e-post addresse"
				/>
				<div class="gender">
					<Radio bind:group={genderRadio} color="#1976d2" value="male"><span>Mann</span></Radio>
					<Radio bind:group={genderRadio} color="#1976d2" value="female"><span>Kvinne</span></Radio>
				</div>
				<!-- Birthdate -->
				<Datefield
					label="Fødselsdag"
					bind:value={dateOfBirth}
					isAllowed={
						(date) => {
							return date.getYear() < new Date().getYear()
						}
					}
				/>
				<Textfield
					type="tel"
					name="phone"
					autocomplete="on"
					required
					bind:value={phone}
					label="Telefonnummeret ditt"
					message="Ditt telefonnummer, med eller uten landskode foran(+47)"
				/>
				<Textfield
					name="address"
					autocomplete="on"
					required
					bind:value={address}
					label="Addresse"
					message="Stedet der du bor"
				/>
				<Textfield
					type="number"
					min="1"
					max="9999"
					name="zip"
					autocomplete="on"
					required
					bind:value={zip}
					label="Postkode"
				/>
				<Textfield
					type="tel"
					name="guardianPhone"
					autocomplete="on"
					required={getAge(dateOfBirth) < 18}
					bind:value={guardianPhone}
					label="Foresattes telefonnummer"
					message="Obligatorisk dersom du er under 18 år"
				/>
				<Checkbox bind:checked={tosAccepted}>Jeg godtar brukervilkårene for Phoenix LAN</Checkbox>
			</form>
			<p>Brukervilkår finner du <a href="tos.html" target="_blank">her.</a></p>

			{#if registerState == STATES.failure}
			<div class="registerError">
				<p><b>Kunne ikke registrere deg:</b> {error}</p>
			</div>
			{/if}
			{#if registerState == STATES.failure || registerState == STATES.input }
			{#if tosAccepted}
			<Button color="primary" raised=true fullWidth=true form="registerForm" type="submit">Registrer deg</Button>
			{/if}
			{/if}
			{#if registerState == STATES.loading}
			<div class="registering">
				<Spinner
					size="50"
					speed="750"
					color="#999"
					thickness="2"
					gap="40"
				/>
			</div>
			{/if}
			{#if registerState == STATES.success}
			<div class="registeringSuccess">
				<Fa icon={faCheck} style="font-size: 3em; color: green;"/>
				<h1>Kontoen din er registrert</h1>
				<p>Du må verifisere mail-kontoen for å logge inn. Du skal ha fått en mail. Sjekk inboksen din for å fortsette. Det kan ta et par minutter før mailen kommer. Husk å sjekke søppelpost!</p>
				<p>Mottok du ikke mailen? Kontakt oss: <a href="mailto:info@phoenixlan.no">info@phoenixlan.no</a></p>
			</div>
			{:else}
			<div class="loginPrompt">
				<p>Har du allerede konto? <a href={'login.html?client_id=' + encodeURIComponent(GET_PARAMS['client_id']) + "&redirect_uri=" + encodeURIComponent(GET_PARAMS['redirect_uri'])}>Logg inn</a></p>
			</div>
			{/if}
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

	.gender {
		display: flex;
	}
	.registeringSuccess {
		width: 100%;
		display: flex;
		align-items: center;
		flex-direction: column;
	}
	.registerError {
		color: red;
	}
	.registering {
		width: 100%;
		display: flex;
		align-items: center;
		flex-direction: column;
	}
	.label {
		font-size: 1.0em;
		font-weight: 300em;
		color: #999;
	}

	
</style>