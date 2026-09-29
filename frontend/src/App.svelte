<script lang="ts">
  import Router, { router } from "svelte-spa-router";
  import routes from "./routes";
  import AppLayout from "./lib/layouts/AppLayout.svelte";
  import AuthLayout from "./lib/layouts/AuthLayout.svelte";
  import { initAuth, refreshUser } from "./store/authStore.svelte";
  import { onMount } from "svelte";

  initAuth();

  onMount(() => {
    refreshUser();
  });

  // Routes rendered with the bare AuthLayout (no sidebar)
  const AUTH_ROUTES = ["/login", "/signup"];
</script>

{#if AUTH_ROUTES.includes(router.location)}
  <AuthLayout>
    <Router {routes} />
  </AuthLayout>
{:else}
  <AppLayout>
    <Router {routes} />
  </AppLayout>
{/if}
