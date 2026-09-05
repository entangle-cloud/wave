<script lang="ts">
  import { Button, Label } from "bits-ui";
  import { login } from "../store/authStore.svelte";

  let email = $state("");
  let password = $state("");
  let submitting = $state(false);
  let error = $state(false);

  const handleSubmit = async (event: SubmitEvent) => {
    event.preventDefault();
    submitting = true;
    try {
      const request = await login(email, password);
      console.log(request);
      if (!request) {
        error = true;
      } else {
        location.hash = "#/";
      }
    } finally {
      submitting = false;
    }
  };
</script>

<svelte:head>
<title>Login - 🌊 Wave</title>
</svelte:head>
<h2 class="card-title mb-4 justify-center">Log in</h2>

<form onsubmit={handleSubmit} class="flex flex-col gap-3">
  <div class="form-control w-full">
    <Label.Root for="login-email" class="label-text mb-1">Email</Label.Root>
    <input
      id="login-email"
      type="email"
      class="input input-bordered w-full"
      placeholder="you@example.com"
      bind:value={email}
      required
    />
  </div>

  <div class="form-control w-full">
    <Label.Root for="login-password" class="label-text mb-1"
      >Password</Label.Root
    >
    <input
      id="login-password"
      type="password"
      class="input input-bordered w-full"
      placeholder="••••••••"
      bind:value={password}
      required
    />
  </div>

  <Button.Root type="submit" class="btn btn-primary mt-2" disabled={submitting}>
    {#if submitting}
      <span class="loading loading-spinner loading-sm"></span>
      Logging in...
    {:else}
      Log in
    {/if}
  </Button.Root>
  <a href="#/signup" class="btn">Sign up</a>
</form>

{#if error}
  <div class="mt-4">
    <Label.Root class="label text-red-700"
      >Incorrect username of password</Label.Root
    >
  </div>
{/if}
