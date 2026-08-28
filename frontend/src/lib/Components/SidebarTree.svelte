<script lang="ts">
  import { Collapsible } from "bits-ui";
  import { categories } from "../../store/categoryStore.svelte";
  import{activeDoc} from "../../store/editorStore.svelte"
  import {router} from "svelte-spa-router"
  import DocumentTextIcon from "@iconify-svelte/reicon/document-duotone";
  import {
    ensurePosts,
    postsByCategory,
    postsLoading,
    openIds,
    isLoading,
    handleOpenChange,
  } from "../../store/sidebarStore.svelte";
  import { buildCategoryTree, type CategoryNode } from "../tree";
  import AngleDownIcon from "@iconify-svelte/reicon/angle-down";
  import { onMount } from "svelte";
  let { collapsed = false }: { collapsed?: boolean } = $props();

  const tree = $derived(buildCategoryTree($categories));

  const isActiveDoc = (docId: number) => $activeDoc === docId.toString();

  // Map of category id -> parent id, for expanding ancestor nodes
  const parentOf = $derived.by(() => {
    const m = new Map<number, number | null>();
    for (const c of $categories) m.set(c.id, c.parentId);
    return m;
  });

  // Expand a category and all of its ancestors in the tree
  function expandCategory(id: number) {
    let cur: number | null | undefined = id;
    while (cur != null) {
      openIds[cur] = true;
      cur = parentOf.get(cur) ?? null;
    }
  }

  // On mount and whenever the route points at a category, auto-expand it
  $effect(() => {
    const loc = router.location; // reactive; e.g. "/categories/5"
    const match = loc.match(/^#?\/?categories\/(\d+)/);
    if (match) expandCategory(Number(match[1]));
  });

  onMount(async () => {
    for (const [id, isOpen] of Object.entries(openIds)) {
      if (isOpen) void ensurePosts(Number(id));
    }
  });
</script>

{#snippet chevron(open: boolean)}
  <AngleDownIcon
    class="size-4 transform transition-transform duration-300 ease-in-out  {open
      ? 'rotate-0'
      : '-rotate-90'}"
  />
{/snippet}

{#snippet dot(color: string)}
  <span
    class="size-2.5 shrink-0 rounded-full border border-base-content/20"
    style="background:{color}"
  ></span>
{/snippet}

{#snippet nodeItem(node: CategoryNode, depth: number)}
  {@const id = node.category.id}
  {@const open = !!openIds[id]}
  <Collapsible.Root {open} onOpenChange={(v) => handleOpenChange(node, v)}>
    <div
      class="{node.category.parentId === null ? "mt-2" : ""} flex items-center rounded-box pr-1 px-2 hover:bg-base-content/10"
    >
      <a
        href="#/categories/{id}"
        title={node.category.name}
        class="flex min-w-0 flex-1 items-center gap-2 py-1.5 font-light text-base-content {collapsed &&
        depth > 0
          ? 'hidden'
          : ''}"
        style="padding-left:{depth * 12}px"
      >
        {@render dot(node.category.color)}
        {#if !collapsed}
          <span class="truncate">{node.category.name}</span>
        {/if}
      </a>
      <Collapsible.Trigger
        class="btn btn-ghost btn-square btn-xs shrink-0"
        aria-label={open ? "Collapse" : "Expand"}
        tabindex={collapsed && depth > 0 ? -1 : undefined}
      >
        {#if !collapsed || depth === 0}
          {@render chevron(open)}
        {/if}
      </Collapsible.Trigger>
    </div>
    {#if !collapsed}
      <Collapsible.Content class="overflow-hidden">
        {#each node.children as child (child.category.id)}
          {@render nodeItem(child, depth + 1)}
        {/each}
        {@render docsListWithDepth(node, depth)}
      </Collapsible.Content>
    {/if}
  </Collapsible.Root>
{/snippet}

{#snippet docsListWithDepth(node: CategoryNode, depth: number)}
  {@const posts = $postsByCategory[node.category.id]}
  {@const loading = $postsLoading.includes(node.category.id)}
  {#if loading}
    <div
      class="flex items-center gap-2 py-1.5 text-xs text-base-content/60"
      style="padding-left:{(depth + 2) * 12}px"
    >
      <span class="loading loading-sm"></span>
      Loading documents...
    </div>
  {:else if node.children.length === 0 && posts && posts.length === 0}
    <div
      class="py-1.5 text-xs italic text-base-content/40"
      style="padding-left:{(depth + 2) * 12}px"
    >
      No documents
    </div>
  {:else if posts && posts.length > 0}
    <ul
      class="menu w-full gap-0.5 p-0 text-sm transform transition-transform duration-300 ease-in-out"
    >
      {#each posts as post (post.id)}
        <li class="transform transition-transform duration-300 ease-in-out">
          <a
            href="#/docs/{post.id}"
            class="rounded-box {isActiveDoc(post.id) ? 'bg-olive-200' : ''} font-light"
            style="padding-left:{(depth + 2) * 12}px"
            title={post.title}
          >
            <DocumentTextIcon class="size-4.5" />
            <span class="truncate">{post.title}</span>
          </a>
        </li>
      {/each}
    </ul>
  {/if}
{/snippet}

<ul class="menu w-full gap-0.5 p-0 text-sm">
  {#each tree as root (root.category.id)}
    {@render nodeItem(root, 0)}
  {/each}
  {#if $isLoading === true}
    <li class="menu-disabled"><span></span></li>
  {:else if tree.length === 0}
    <li class="menu-disabled"><span>No categories yet</span></li>
  {/if}
</ul>
