import { writable } from "svelte/store";
export const editorTitle = writable<string | null>(null);
export const editorContent = writable<string | null>(null);
export const activeDoc = writable<string | null> (null)
export const documentLoading = writable<boolean>(false)
export const docVersion = writable<number | null>(0)