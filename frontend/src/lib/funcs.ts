import { type Category } from "../store/categoryStore.svelte";
import { apiFetch } from "./api";

let requestJson: {
  colour: string;
  created_at: Date;
  created_by_id: number;
  description: string;
  id: number;
  name: string;
  parent_id: number | null;
  slug: string;
  updated_at: Date;
}[] = [];

try {
  const fetchCategries = await apiFetch(
    `${import.meta.env.VITE_API_ENDPOINT}/category/categories`,
    { credentials: "include" },
  );
  requestJson = await fetchCategries.json();
} catch {
  // Unauthenticated / network error: apiFetch triggers logout; categories
  // stay empty until the user signs in.
}

export const mappedCategories: Category[] = requestJson.map((c) => ({
  id: c.id,
  name: c.name,
  description: c.description,
  parentId: c.parent_id,
  color: c.colour,
  created_by: c.created_by_id,
}));


export type Post = {
  id: number;
  title: string;
  category_id: number;
};

export const fetchPostsByCategory = async (
  categoryId: number,
): Promise<{posts:Post[], category: Category }> => {
  const response = await apiFetch(
    `${import.meta.env.VITE_API_ENDPOINT}/posts/categories/${categoryId}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new Error(`Failed to load posts for category ${categoryId}`);
  }
  return response.json();
};


