<script lang="ts">
	import * as Card from "$lib/components/ui/card/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { FieldGroup, Field, FieldLabel, FieldDescription, FieldError } from "$lib/components/ui/field/index.js";
	import { Input } from "$lib/components/ui/input/index.js";
	import { authClient } from "$lib/auth-client";
	import { goto } from "$app/navigation";

	const id = $props.id();

	let email = $state("");
	let password = $state("");
	let error = $state("");
	let loading = $state(false);

	const redirectTo = $derived(
		typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("redirect") : null,
	);

	async function handleLogin(event: SubmitEvent) {
		event.preventDefault();
		error = "";
		loading = true;
		const { error: signInError } = await authClient.signIn.email({ email, password });
		loading = false;
		if (signInError) {
			error = signInError.message ?? "Invalid email or password.";
			return;
		}
		goto(redirectTo ?? "/");
	}
</script>

<Card.Root class="mx-auto w-full max-w-sm">
	<Card.Header>
		<Card.Title class="text-2xl">Login</Card.Title>
		<Card.Description>Enter your email and password to login to your account</Card.Description>
	</Card.Header>
	<Card.Content>
		<form onsubmit={handleLogin}>
			<FieldGroup>
				<Field>
					<FieldLabel for="email-{id}">Email</FieldLabel>
					<Input id="email-{id}" type="email" placeholder="m@example.com" required bind:value={email} />
				</Field>
				<Field>
					<FieldLabel for="password-{id}">Password</FieldLabel>
					<Input id="password-{id}" type="password" required bind:value={password} />
				</Field>
				{#if error}
					<FieldError>{error}</FieldError>
				{/if}
				<Field>
					<Button type="submit" class="w-full" disabled={loading}>
						{loading ? "Signing in..." : "Login"}
					</Button>
					<FieldDescription class="text-center">
						Don't have an account? <a href="/signup" class="underline">Sign up</a>
					</FieldDescription>
				</Field>
			</FieldGroup>
		</form>
	</Card.Content>
</Card.Root>
