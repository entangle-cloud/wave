import { writable } from "svelte/store";

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
