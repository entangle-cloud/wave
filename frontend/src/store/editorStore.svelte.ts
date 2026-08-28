import { writable } from "svelte/store";
export const editorTitle = writable<string | null>(null);
export const editorContent = writable<string | null>(null);
export const activeDoc = writable<string | null> (null)
