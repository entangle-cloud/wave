// src/lib/server/auth.ts
import { betterAuth } from "better-auth";
import { sveltekitCookies } from "better-auth/svelte-kit";
import { getRequestEvent } from "$app/server";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "$lib/server/db";
import { env } from "$env/dynamic/private";

export const auth = betterAuth({
    database: drizzleAdapter(db, { provider: "pg" }),
    baseURL: env.BETTER_AUTH_URL,
    emailAndPassword: {
        enabled: true, // Enables sign up, sign in with email/password
    },
    plugins: [
        sveltekitCookies(getRequestEvent) // Handles SvelteKit session cookies automatically
    ]
});