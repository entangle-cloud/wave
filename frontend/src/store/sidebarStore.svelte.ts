import { get, writable } from "svelte/store";
import { fetchPostsByCategory, type Post } from "../lib/funcs";
import { type CategoryNode } from "../lib/tree";

const STORAGE_KEY = "sidebar:openIds";

function loadOpenIds(): Record<number, boolean> {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<number, boolean>) : {};
  } catch {
    return {};
  }
}

export const postsByCategory = writable<Record<number, Post[]>>({});
export const postsLoading = writable<number[]>([]);
export const openIds = $state<Record<number, boolean>>(loadOpenIds());
export const isLoading = writable<boolean>(false);

// Persist the expanded tree state across page loads
$effect.root(() => {
  $effect(() => {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...openIds }));
  });
});

const failedCategories = new Set<number>();

export async function ensurePosts(categoryId: number) {
  if (get(postsByCategory)[categoryId] || failedCategories.has(categoryId)) {
    return;
  }
  postsLoading.update((ids) => [...ids, categoryId]);
  try {
    const posts = await fetchPostsByCategory(categoryId);
    postsByCategory.update((map) => ({ ...map, [categoryId]: posts.posts }));
  } catch {
    failedCategories.add(categoryId);
    postsByCategory.update((map) => ({ ...map, [categoryId]: [] }));
  } finally {
    postsLoading.update((ids) => ids.filter((id) => id !== categoryId));
  }
}

export function handleOpenChange(node: CategoryNode, isOpen: boolean) {
  openIds[node.category.id] = isOpen;
  if (isOpen) ensurePosts(node.category.id);
}
