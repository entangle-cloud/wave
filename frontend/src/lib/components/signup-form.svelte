<script lang="ts">
	import * as Card from "$lib/components/ui/card/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { FieldGroup, Field, FieldLabel, FieldDescription, FieldError } from "$lib/components/ui/field/index.js";
	import { Input } from "$lib/components/ui/input/index.js";
	import { authClient } from "$lib/auth-client";
	import { goto } from "$app/navigation";

	const id = $props.id();

	let name = $state("");
	let email = $state("");
	let password = $state("");
	let error = $state("");
	let loading = $state(false);

	async function handleSignup(event: SubmitEvent) {
		event.preventDefault();
		error = "";
		loading = true;
		const { error: signUpError } = await authClient.signUp.email({ name, email, password });
		loading = false;
		if (signUpError) {
			error = signUpError.message ?? "Sign up failed. Please try again.";
			return;
		}
		goto("/");
	}
</script>

<Card.Root class="mx-auto w-full max-w-sm">
	<Card.Header>
		<Card.Title class="text-2xl">Sign Up</Card.Title>
		<Card.Description>Create an account to get started</Card.Description>
	</Card.Header>
	<Card.Content>
		<form onsubmit={handleSignup}>
			<FieldGroup>
				<Field>
					<FieldLabel for="name-{id}">Name</FieldLabel>
					<Input id="name-{id}" type="text" placeholder="John Doe" required bind:value={name} />
				</Field>
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
						{loading ? "Creating account..." : "Sign Up"}
					</Button>
					<FieldDescription class="text-center">
						Already have an account? <a href="/login" class="underline">Login</a>
					</FieldDescription>
				</Field>
			</FieldGroup>
		</form>
	</Card.Content>
</Card.Root>
