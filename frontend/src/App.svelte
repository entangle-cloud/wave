<script>
  import Router, { router } from "svelte-spa-router";
  import routes from "./routes";
  import AppLayout from "./lib/layouts/AppLayout.svelte";
  import AuthLayout from "./lib/layouts/AuthLayout.svelte";
  import { categories } from "./store/categoryStore.svelte";
  import { loadCategories } from "./store/categoryStore.svelte";
  import { initAuth } from "./store/authStore.svelte";
  import { userStore } from "./store/authStore.svelte";

  // Seed the sidebar store before any child (incl. SidebarTree) renders
  if ($categories.length === 0 && $userStore) {
    loadCategories();
  }

  // Start JWT-expiry tracking for any restored session
  initAuth();

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
