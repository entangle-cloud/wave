import { writable, derived, get } from "svelte/store";

/** The authenticated user's session data. */
export type User = {
  email: string;
  name: string;
  avatar: string | null;
  id: number;
  /** Epoch ms when the JWT expires, or null if unknown. */
  expiresAt: number | null;
};

const STORAGE_KEY = "ai_docs_user";

/** Decode the `exp` claim (seconds) from a JWT into epoch ms. No verification. */
const decodeExpiry = (token: string): number | null => {
  try {
    const payload = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
    );
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
};

let expiryTimer: ReturnType<typeof setTimeout> | null = null;

const loadStoredUser = (): User | null => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? (JSON.parse(stored) as User) : null;
  } catch {
    return null;
  }
};

const clearExpiryTimer = () => {
  if (expiryTimer !== null) {
    clearTimeout(expiryTimer);
    expiryTimer = null;
  }
};

/** Schedule automatic logout when the session expires, or log out if already expired. */
const scheduleExpiry = (user: User | null) => {
  clearExpiryTimer();
  if (!user || !user.expiresAt) return;
  const ms = user.expiresAt - Date.now();
  if (ms <= 0) {
    logout();
    return;
  }
  expiryTimer = setTimeout(() => logout(), ms);
};

/** Current user session; null when logged out. */
export const userStore = writable<User | null>(loadStoredUser());

userStore.subscribe((user) => {
  try {
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // Storage unavailable (e.g. private mode) - session stays in memory only
  }
});

/** True when a user session exists. */
export const isAuthenticated = derived(userStore, ($user) => $user !== null);

/**
 * Signs the user in.
 *
 * @param email - The user's email address.
 * @param _password - The user's password (unused until backend wiring).
 * @returns True if login succeeded.
 */
export const login = async (
  email: string,
  _password: string,
): Promise<boolean> => {
  if (!email) return false;

  const request = await fetch(`${import.meta.env.VITE_API_ENDPOINT}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      email: email,
      password: _password,
    }),
  });

  if (request.ok) {
    const requestJson = await request.json()
    const user: User = {
      email: requestJson.user.email,
      avatar: requestJson.user.avatar,
      name: requestJson.user.name,
      id: requestJson.user.id,
      expiresAt: decodeExpiry(requestJson.access_token),
    };
    userStore.set(user);
    scheduleExpiry(user);
    return true;
  }
  return false;
};

/**
 * Signs up the user.
 */
export const signup = async (
  email: string,
  name: string,
  password: string,
): Promise<boolean> => {
  const request = await fetch(
    `${import.meta.env.VITE_API_ENDPOINT}/auth/signup`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        name: name,
        email: email,
        password: password,
      }),
    },
  );

  if (request.ok) {
    const requestJson = await request.json()
    const user: User = {
      email,
      name,
      id: requestJson.id,
      avatar: requestJson.avatar,
      expiresAt: decodeExpiry(requestJson.access_token),
    };
    userStore.set(user);
    scheduleExpiry(user);
    return true;
  }
  return false;
};

/** Clears the current session and returns the user to the login page. */
export const logout = () => {
  clearExpiryTimer();
  userStore.set(null);
  location.hash = "#/login";
};

/**
 * Synchronous check used by route guards.
 * @returns True when a session exists.
 */
export const checkAuthenticated = () => get(isAuthenticated);

/**
 * Initializes session expiry tracking. Call once at app start so that a
 * restored session (from localStorage) is still auto-logged-out on expiry,
 * and any already-expired session is cleared immediately.
 */
export const initAuth = () => {
  scheduleExpiry(get(userStore));
};
