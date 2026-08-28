import type { RoutePrecondition } from "svelte-spa-router";
import { push } from "svelte-spa-router";
import { checkAuthenticated } from "./store/authStore.svelte";

/**
 * Route precondition: allow only when authenticated,
 * otherwise redirect to the login page.
 */
export const requireAuth: RoutePrecondition = () => {
  if (checkAuthenticated()) return true;

  push("/login");
  return false;
};

/**
 * Route precondition: allow only when NOT authenticated (login/signup),
 * otherwise redirect to home.
 */
export const skipIfAuthed: RoutePrecondition = () => {
  if (!checkAuthenticated()) return true;

  push("/");
  return false;
};
