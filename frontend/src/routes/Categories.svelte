<script lang="ts">
  import { Dialog, Button, Label } from "bits-ui";
  import { categories, type Category } from "../store/categoryStore.svelte";
  import { meta } from "zod/v4/core";
  import { onMount } from "svelte";
  import { mappedCategories } from "../lib/funcs";
  import { apiFetch } from "../lib/api";
  import { fromAction } from "svelte/attachments";

  const COLORS = [
    "#ef4444",
    "#f97316",
    "#eab308",
    "#22c55e",
    "#14b8a6",
    "#3b82f6",
    "#8b5cf6",
    "#ec4899",
  ];

  let dialogOpen = $state(false);
  let editingId = $state<number | null>(null);
  let deleteError = $state("");
  let form = $state<{
    name: string;
    parentId: number | null;
    color: string;
    description: string;
  }>({ name: "", parentId: null, color: COLORS[5], description: "" });

  const childrenOf = $derived.by(() => {
    const map = new Map<number | null, Category[]>();
    for (const category of $categories) {
      const siblings = map.get(category.parentId) ?? [];
      siblings.push(category);
      map.set(category.parentId, siblings);
    }
    for (const siblings of map.values()) {
      siblings.sort((a, b) => a.name.localeCompare(b.name));
    }
    return map;
  });

  const descendantIds = (id: number): number[] => {
    const out: number[] = [];
    const walk = (parentId: number) => {
      for (const category of $categories) {
        if (category.parentId === parentId) {
          out.push(category.id);
          walk(category.id);
        }
      }
    };
    walk(id);
    return out;
  };

  const parentOptions = $derived.by(() => {
    if (!editingId) return $categories;
    const excluded = new Set([editingId, ...descendantIds(editingId)]);
    return $categories.filter((category) => !excluded.has(category.id));
  });

  const rootCount = $derived(
    $categories.filter((c) => c.parentId === null).length,
  );

  const openCreate = () => {
    editingId = null;
    form = { name: "", parentId: null, color: COLORS[5], description: "" };
    deleteError = "";
    dialogOpen = true;
  };

  const openEdit = (category: Category) => {
    editingId = category.id;
    form = {
      name: category.name,
      parentId: category.parentId,
      color: category.color,
      description: category.description ?? "",
    };
    deleteError = "";
    dialogOpen = true;
  };

  const saveCategory = async (e: SubmitEvent) => {
    e.preventDefault();
    const name = form.name.trim();
    if (!name) return;

    if (editingId) {
      const crequest = await apiFetch(
      
        `${import.meta.env.VITE_API_ENDPOINT}/category/${editingId}`,
        {
          method: "PATCH",
          credentials: "include",
          headers: {
            'content-type': 'application/json'
          },
          body: JSON.stringify({
            id: editingId,
            name: name,
            parent_category: form.parentId,
            color: form.color,
            description: form.description,
          })
        },
      );
      categories.update((list) =>
        list.map((category) =>
          category.id === editingId
            ? {
                ...category,
                name,
                parentId: form.parentId,
                color: form.color,
                description: form.description.trim(),
              }
            : category,
        ),
      );
    } else {
      const request = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/category`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "content-type": "application/json",
          },
          body: JSON.stringify({
            name: form.name,
            description: form.description,
            color: form.color,
            parent_category: form.parentId,
          }),
        },
      );

      if (request.ok) {
        const requestJson: {
          colour: string;
          created_at: Date;
          created_by_id: number | null;
          description: string;
          id: number;
          name: string;
          parent_id: number | null;
          slug: string;
          updated_at: Date;
        } = await request.json();
        categories.update((list) => [
          ...list,
          {
            id: requestJson.id,
            name: requestJson.name,
            parentId: requestJson.parent_id,
            color: requestJson.colour,
            description: requestJson.description.trim(),
            created_by: requestJson.created_by_id,
          },
        ]);
      }
    }
    dialogOpen = false;
  };

  const removeCategory = async (category: Category) => {
    if ((childrenOf.get(category.id) ?? []).length > 0) {
      deleteError = `"${category.name}" has subcategories. Move or delete them first.`;
      setTimeout(() => (deleteError = ""), 4000);
      return;
    }
    const request = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/category/${category.id}`,
      {
        method: "DELETE",
        credentials: "include",
      },
    );
    if (request.ok) {
      categories.update((list) => list.filter((c) => c.id !== category.id));
    } else {
      deleteError = `Deleting ${category.name} failed`;
    }
  };

  onMount(async () => {
    const mappedCategory = mappedCategories;
    categories.set(mappedCategory);
  });
</script>

<div
  class="flex h-full flex-col overflow-hidden bg-white ring ring-base-300 rounded-xl"
>
  <div class="navbar shrink-0 border-b border-base-200 shadow-sm px-4">
    <div class="flex-1">
      <h1 class="text-lg font-bold">Categories</h1>
      <span class="ml-2 badge badge-ghost">
        {$categories.length} total · {rootCount} root
      </span>
    </div>
    <div class="flex-none">
      <Button.Root class="btn btn-primary btn-soft btn-sm" onclick={openCreate}>
        + New category
      </Button.Root>
    </div>
  </div>

  <div class="min-h-0 flex-1 overflow-y-auto p-6">
    {#if deleteError}
      <div role="alert" class="alert alert-error mb-4 py-2 text-sm">
        <span>{deleteError}</span>
      </div>
    {/if}

    <div class="rounded-box border border-base-200 bg-base-100 p-4">
      {@render treeNodes(null)}
    </div>
  </div>
</div>

{#snippet treeNodes(parentId: number | null)}
  <ul class="menu w-full gap-0.5 p-0">
    {#each childrenOf.get(parentId) ?? [] as category (category.id)}
      <li>
        <div class="flex w-full items-center gap-2">
          <span
            class="size-2.5 shrink-0 rounded-full"
            style="background:{category.color}"
          ></span>
          <span class="font-medium">{category.name}</span>
          {#if category.description}
            <span class="truncate text-xs text-base-content/50">
              {category.description}
            </span>
          {/if}
          <div class="ml-auto flex shrink-0 gap-1">
            <Button.Root
              class="btn btn-ghost btn-xs"
              onclick={() => openEdit(category)}
            >
              Edit
            </Button.Root>
            <Button.Root
              class="btn btn-ghost btn-xs text-error"
              onclick={() => removeCategory(category)}
            >
              Delete
            </Button.Root>
          </div>
        </div>
        {#if (childrenOf.get(category.id) ?? []).length > 0}
          <ul class="border-l border-base-200 ml-4 pl-2">
            {@render treeNodes(category.id)}
          </ul>
        {/if}
      </li>
    {:else}
      <li class="pointer-events-none text-base-content/50">
        <span>No categories yet</span>
      </li>
    {/each}
  </ul>
{/snippet}

<Dialog.Root bind:open={dialogOpen}>
  <Dialog.Portal>
    <Dialog.Overlay class="fixed inset-0 z-40 bg-black/40" />
    <Dialog.Content
      class="fixed top-1/2 left-1/2 z-50 w-md max-w-[90vw] -translate-x-1/2 -translate-y-1/2 rounded-box bg-base-100 p-0 shadow-xl"
    >
      <form onsubmit={saveCategory} class="flex flex-col gap-4 p-6">
        <Dialog.Title class="text-lg font-bold">
          {editingId ? "Edit category" : "New category"}
        </Dialog.Title>

        <div class="form-control">
          <Label.Root class="label">Name</Label.Root>
          <input
            type="text"
            class="input input-bordered w-full"
            placeholder="e.g. Design"
            bind:value={form.name}
          />
        </div>

        <div class="form-control">
          <Label.Root class="label text-xs">Parent category</Label.Root>
          <select
            class="select select-bordered w-full"
            bind:value={form.parentId}
          >
            <option value={null}>None (root category)</option>
            {#each parentOptions as option (option.id)}
              <option value={option.id}>{option.name}</option>
            {/each}
          </select>
        </div>

        <div class="form-control">
          <span class="mb-1 block text-sm font-medium">Color</span>
          <div class="flex flex-wrap items-center gap-2">
            {#each COLORS as color (color)}
              <Button.Root
                type="button"
                aria-label="Pick {color}"
                class="size-6 rounded-full border-2 transition-transform hover:scale-110
                  {form.color === color
                  ? 'border-base-content'
                  : 'border-transparent'}"
                style="background:{color}"
                onclick={() => (form.color = color)}
              ></Button.Root>
            {/each}
            <input
              type="color"
              class="input input-bordered h-8 w-12 cursor-pointer p-0.5"
              bind:value={form.color}
            />
          </div>
        </div>

        <div class="form-control">
          <Label.Root class="label text-xs">Description</Label.Root>
          <textarea
            class="textarea textarea-bordered w-full"
            rows="2"
            placeholder="Optional description"
            bind:value={form.description}
          ></textarea>
        </div>

        <div class="mt-2 flex justify-end gap-2">
          <Dialog.Close class="btn btn-ghost">Cancel</Dialog.Close>
          <Button.Root type="submit" class="btn btn-primary">
            {editingId ? "Save changes" : "Create"}
          </Button.Root>
        </div>
      </form>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
