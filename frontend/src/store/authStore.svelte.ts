import { writable, derived, get } from "svelte/store";

/** The authenticated user's session data. */
export type UserRole = "admin" | "editor" | "viewer";

export type User = {
  email: string;
  name: string;
  avatar: string | null;
  id: number;
  role: UserRole;
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

/** True when the current user is an admin. */
export const isAdmin = derived(
  userStore,
  ($user) => $user?.role === "admin",
);

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
      avatar: requestJson.user.avatar_url,
      name: requestJson.user.name,
      id: requestJson.user.id,
      role: (requestJson.user.role ?? "viewer") as UserRole,
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
  turnsiteToken: string
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
        turnstile_token: turnsiteToken
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
      role: (requestJson.role ?? "viewer") as UserRole,
      expiresAt: requestJson.access_token
        ? decodeExpiry(requestJson.access_token)
        : null,
    };
    userStore.set(user);
    scheduleExpiry(user);
    return true;
  }
  return false;
};

/**
 * Updates the user's profile.
 */
export const updateProfile = async (
  name: string,
  email: string,
  password: string | undefined,
  avatar: File | null
): Promise<boolean> => {
  const form = new FormData()
  form.append("name", name)
  form.append("email", email)
  if (password) {
    form.append("password", password)
  }

  if (avatar)
    form.append("avatar", avatar)
  const request = await fetch(`${import.meta.env.VITE_API_ENDPOINT}/auth/me`, {
    method: "PUT",
    credentials: "include",
    body: form
  });

  if (request.ok) {
    const requestJson = await request.json();
    userStore.update(($user) => {
      if ($user) {
        return { ...$user, name: requestJson.name, email: requestJson.email };
      }
      return $user;
    });
    return true;
  }
  return false;
};

/** Clears the current session and returns the user to the login page. */
export const logout = () => {
  clearExpiryTimer();
  userStore.set(null);
  document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  location.hash = "#/login";
};

/**
 * Synchronous check used by route guards.
 * @returns True when a session exists.
 */
export const checkAuthenticated = () => get(isAuthenticated);

/** Synchronous check for admin role, used by route guards. */
export const checkIsAdmin = () => get(userStore)?.role === "admin";

/**
 * Refresh the stored session (name, email, avatar, role) from the backend.
 * Useful because the role lives server-side and localStorage can go stale.
 */
export const refreshUser = async (): Promise<void> => {
  try {
    const res = await fetch(`${import.meta.env.VITE_API_ENDPOINT}/auth/me`, {
      credentials: "include",
    });
    if (!res.ok) return;
    const data = await res.json();
    userStore.update(($user) => {
      if (!$user) return $user;
      return {
        ...$user,
        name: data.name ?? $user.name,
        email: data.email ?? $user.email,
        avatar: data.avatar_url ?? $user.avatar,
        role: (data.role ?? $user.role) as UserRole,
      };
    });
  } catch {
    // Keep cached session on network failure
  }
};

/**
 * Initializes session expiry tracking. Call once at app start so that a
 * restored session (from localStorage) is still auto-logged-out on expiry,
 * and any already-expired session is cleared immediately.
 */
export const initAuth = () => {
  scheduleExpiry(get(userStore));
};
