import { writable } from "svelte/store";
import { apiFetch } from "../lib/api";

export type Category = {
  id: number;
  name: string;
  parentId: number | null;
  color: string;
  created_by?: number | null;
  description?: string;
};

const seedCategories: Category[] = [];

export const categories = writable<Category[]>(seedCategories);

export const selectedCategoryId = writable<string | null>(null);

export const loadCategories = async () => {
  try {
    const response = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/category/categories`,
      { credentials: "include" },
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
};

export type CategoryNode = Category & { depth: number };

export const sortCategoriesForDisplay = (
  categories: Category[],
): CategoryNode[] => {
  const byParent = new Map<number | null, Category[]>();
  for (const category of categories) {
    const key = category.parentId;
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key)!.push(category);
  }

  const result: CategoryNode[] = [];

  function walk(parentId: number | null, depth: number) {
    for (const category of byParent.get(parentId) ?? []) {
      result.push({ ...category, depth });
      walk(category.id, depth + 1);
    }
  }

  walk(null, 0);
  return result;
};
