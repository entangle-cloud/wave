import { writable } from "svelte/store";
import { apiFetch } from "../lib/api";

export type Category = {
  id: number;
  name: string;
  parentId: number | null;
  color: string;
  created_by?: number | null,
  description?: string;
};

const seedCategories: Category[] = [];

export const categories = writable<Category[]>(seedCategories);

export const selectedCategoryId = writable<string | null>(null);

export async function loadCategories() {
  try {
    const response = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/category/categories`,
      { credentials: "include" }
    );
    const data = await response.json();
    const mapped = data.map((c: any) => ({
      id: c.id,
      name: c.name,
      description: c.description,
      parentId: c.parent_id,
      color: c.colour,
      created_by: c.created_by_id,
    }));
    categories.set(mapped);
  } catch {
    categories.set([]);
  }
}
