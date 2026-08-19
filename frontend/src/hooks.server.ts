// src/hooks.server.ts
import { auth } from "$lib/server/auth";
import { svelteKitHandler } from "better-auth/svelte-kit";
import { building } from "$app/environment";
import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
    // 1. Fetch current session
    const session = await auth.api.getSession({
        headers: event.request.headers,
    });

    // 2. Attach user and session to event.locals for your app routes
    event.locals.session = session?.session ?? null;
    event.locals.user = session?.user ?? null;

    // 3. Delegate authentication endpoints to Better Auth
    return svelteKitHandler({ event, resolve, auth, building });
};