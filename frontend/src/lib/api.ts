import { logout } from "../store/authStore.svelte";

/**
 * Authenticated fetch: sends cookies and auto-logs-out on a 401 response
 * (e.g. an expired/invalidated token). Do NOT use this for /auth/login or
 * /auth/signup, since those endpoints legitimately return 401.
 */
export const apiFetch = async (
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> => {
  const response = await fetch(input, {
    credentials: "include",
    ...init,
  });

  if (response.status === 401) {
    logout();
    throw new Error("Session expired");
  }

  return response;
};
