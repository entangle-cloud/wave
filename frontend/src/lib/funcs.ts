import { type Category } from "../store/categoryStore.svelte";
import { apiFetch } from "./api";
import { db, type AppDB } from "./db";

type CategoryDto = {
  colour: string;
  created_at: string;
  created_by_id: number;
  description: string;
  id: number;
  name: string;
  parent_id: number | null;
  slug: string;
  updated_at: string;
};

const mapCategoryDto = (c: CategoryDto): Category => ({
  id: c.id,
  name: c.name,
  description: c.description,
  parentId: c.parent_id,
  color: c.colour,
  created_by: c.created_by_id,
});

/**
 * Lazily fetches categories. Must only be called from authenticated routes —
 * calling it unauthenticated triggers apiFetch's 401 -> logout() path.
 * Previously this ran as a top-level await on module import, so merely
 * importing this module (e.g. via SidebarTree on /login or /signup) fired
 * api.ts:12. Now nothing runs at import time.
 */
export const fetchMappedCategories = async (): Promise<Category[]> => {
  try {
    const response = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/category/categories`,
      { credentials: "include" },
    );
    const requestJson = (await response.json()) as CategoryDto[];
    return requestJson.map(mapCategoryDto);
  } catch {
    // Unauthenticated / network error: apiFetch triggers logout; callers
    // treat empty list as "no categories yet".
    return [];
  }
};

export type Post = {
  id: number;
  title: string;
  category_id: number;
};

export const fetchPostsByCategory = async (
  categoryId: number,
): Promise<{ posts: Post[]; category: Category }> => {
  const response = await apiFetch(
    `${import.meta.env.VITE_API_ENDPOINT}/posts/categories/${categoryId}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new Error(`Failed to load posts for category ${categoryId}`);
  }
  return response.json();
};


export const addDocumentToLocalDB = async (
  database: AppDB,
  id: number,
  title: string,
  content: string,
  description: string,
  categoryId: number,
  createdBy: number,
  createdByName: string,
  createdDateTime: Date,
  updatedDateTime: Date,
) => {
  await database.documents.put({
    id: id,
    title,
    content,
    description,
    categoryId,
    createdBy,
    createdByName,
    createdDateTime,
    updatedDateTime,
  });
};

/**
 * Patches an existing local document with the latest typed content.
 * Bumps `updatedDateTime` to now so the local copy is marked newer than
 * the last server sync. No-op when the record doesn't exist yet locally
 * (e.g. a fresh server doc that hasn't been cached — the full
 * `addDocumentToLocalDB` sync on load/save will create it).
 */
export const updateLocalDraft = async (
  database: AppDB,
  id: number,
  content: string,
  title?: string,
): Promise<Date | undefined> => {
  const existing = await database.documents.get(id);
  if (!existing) return undefined;
  if (existing.content === content && (title === undefined || existing.title === title)) {
    return undefined;
  }
  const updatedDateTime = new Date();
  await database.documents.update(id, {
    content,
    ...(title !== undefined ? { title } : {}),
    updatedDateTime,
  });
  return updatedDateTime;
};
