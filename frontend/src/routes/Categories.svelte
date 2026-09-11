<script lang="ts">
  import { Dialog, Button, Label, Avatar } from "bits-ui";
  import {
    categories,
    loadCategories,
    type Category,
  } from "../store/categoryStore.svelte";
  import { onMount } from "svelte";
  import { apiFetch } from "../lib/api";
  import { Toaster, toast } from "svelte-sonner";
  import { userStore } from "../store/authStore.svelte";
  import { Combobox } from "bits-ui";
  import UserCircleIcon from "@iconify-svelte/reicon/user-add";
  import ChevronDownIcon from "@iconify-svelte/reicon/chevron-down";
  import ChevronUpIcon from "@iconify-svelte/reicon/chevron-up";
  import CheckIcon from "@iconify-svelte/reicon/check";
  import X from "@iconify-svelte/reicon/x";

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

  interface Participants {
    name: string;
    email: string;
    avatar_url: string;
    id: number;
    role: string;
  }

  let dialogOpen = $state(false);
  let editingId = $state<number | null>(null);
  let deleteError = $state("");
  let emailAddress = $state("");
  let selectParticipants = $state<string[]>([]);
  let participants = $state<Participants[]>([]);
  let searchParticipants = $state<Participants[]>([]);
  let pendingShare = $state(false);
  let shareDialogOpen = $state(false);
  let selectedCategoryId = $state(0);
  let isLoading = $state(false);
  let sharedUsers = $state<Participants[]>([]);
  let shareStatus = $state<boolean | null>(null);
  let shareMessage = $state("");

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
            "content-type": "application/json",
          },
          body: JSON.stringify({
            id: editingId,
            name: name,
            parent_category: form.parentId,
            color: form.color,
            description: form.description,
          }),
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
    await loadCategories();
    categories.set($categories);
  });

  let controller: AbortController;
  $effect(() => {
    if (emailAddress.trim().length === 0) return;
    const ctrl = new AbortController();
    controller?.abort();
    controller = ctrl;

    const timer = setTimeout(() => {
      apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/api/search_users?search_query=${encodeURIComponent(emailAddress)}`,
        { signal: ctrl.signal },
      )
        .then((res) => {
          if (!res.ok) throw new Error(`Search failed: ${res.status}`);
          return res.json();
        })
        .then((data) => (searchParticipants = data))
        .catch((err) => {
          if (err.name !== "AbortError") console.error(err);
        });
    }, 300);

    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  });

  const removeParticipant = (participant: Participants) => {
    const toStringParticipant = JSON.stringify(participant);
    participants = participants.filter((value) => value !== participant);
    selectParticipants = selectParticipants.filter(
      (value) => value !== toStringParticipant,
    );
  };

  const getParticipants = () => {
    return selectParticipants;
  };

  const setParticipants = (newParticipants: string[]) => {
    console.log(newParticipants);
    newParticipants.forEach((participant) => {
      if (
        participants.some((value) => value.id === JSON.parse(participant).id)
      ) {
        return;
      } else {
        participants.push(JSON.parse(participant));
      }
    });
    return (selectParticipants = newParticipants);
  };

  const share = async () => {
    pendingShare = true;
    const sharedUserIds: Number[] = [];

    selectParticipants.forEach((participant) => {
      let parseParticipant = JSON.parse(participant);
      sharedUserIds.push(parseParticipant.id);
    });
    const shareRequest = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/api/share`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          collection: selectedCategoryId,
          shared_by: $userStore?.id,
          shared_users: sharedUserIds,
        }),
      },
    ).finally(() => {
      pendingShare = false;
    });

    if (shareRequest.ok) {
      shareStatus = true;
      shareMessage = "Sharing updated.";
    } else {
      shareStatus = false;
      shareMessage = "Sharing failed.";
    }
  };

  const openShareDialog = async (categoryId: number) => {
    shareDialogOpen = true;
    isLoading = true;
    const request = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/api/share_details?category_id=${categoryId}`,
    );
    sharedUsers = await request.json();
    participants = sharedUsers;
    isLoading = false;
    selectedCategoryId = categoryId;
  };
</script>

<svelte:head>
  <title>Manage my categories - 🌊 Wave</title>
</svelte:head>

<Toaster />

<Dialog.Root bind:open={shareDialogOpen}>
  <Dialog.Portal>
    <Dialog.Overlay
      class="data-[state=open]:animate-in  data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/80"
    />
    <Dialog.Content
      class="card bg-white data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 outline-hidden fixed left-[50%] top-[50%] z-50 w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 border sm:max-w-lg md:w-full"
      interactOutsideBehavior={pendingShare ? "ignore" : "close"}
      escapeKeydownBehavior={pendingShare ? "ignore" : "close"}
    >
      <div class="card-body">
        <Dialog.Title class="card-title">Share Category</Dialog.Title>
        <Dialog.Description>
          <p>
            Enter the email addresses of the participants you want to share this
            category.
          </p>
          <p>
            <span class="text-gray-600"
              >All subcategories under this category will also be shared.</span
            >
          </p>
        </Dialog.Description>
        <Label.Root class="label">Email Address</Label.Root>
        <Combobox.Root
          type="multiple"
          bind:value={getParticipants, setParticipants}
          name="search-{crypto.randomUUID()}"
          onOpenChangeComplete={(o) => {
            if (!o) emailAddress = "";
          }}
        >
          <div class="relative">
            <UserCircleIcon
              class=" fill-olive-200 size-6 absolute inset-s-3 top-1/5 z-40 size-8-translate-y-1/2"
            />
            <Combobox.Input
              autocomplete="off"
              data-1p-ignore
              data-lpignore="true"
              data-bwignore="true"
              data-form-type="other"
              type="text"
              aria-autocomplete="both"
              autocapitalize="off"
              autocorrect="off"
              oninput={(e) => (emailAddress = e.currentTarget.value)}
              class="input bg-white w-full px-11"
              placeholder="Search for a user"
              aria-label="Search for a user"
            />
            <Combobox.Trigger
              class="absolute inset-e-3 top-1/2 size-6 -translate-y-1/2 touch-none"
            >
              <ChevronDownIcon class="text-muted-foreground size-6" />
            </Combobox.Trigger>
          </div>
          <Combobox.Portal>
            <Combobox.Content
              class="focus-override border-olive-400 bg-white data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 outline-hidden z-50 h-96 max-h-(--bits-combobox-content-available-height) w-(--bits-combobox-anchor-width) min-w-(--bits-combobox-anchor-width) select-none rounded-xl border px-1 py-3 data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1"
              sideOffset={10}
            >
              <Combobox.ScrollUpButton
                class="flex w-full items-center justify-center py-1"
              >
                <ChevronUpIcon class="size-3" />
              </Combobox.ScrollUpButton>
              <Combobox.Viewport class="p-1">
                {#each searchParticipants as participant, i (i + participant.id)}
                  <Combobox.Item
                    class="rounded-lg cursor-pointer gap-2 outline-hidden flex h-10 w-full select-none items-center py-3 pl-5 pr-1.5 text-sm capitalize hover:bg-olive-100"
                    value={JSON.stringify(participant)}
                    label={participant.name}
                  >
                    {#snippet children({ selected })}
                      <Avatar.Root
                        delayMs={200}
                        class="data-[status=loaded]:border-foreground bg-muted text-muted-foreground h-8 w-8 rounded-full border text-[17px] font-medium uppercase data-[status=loading]:border-transparent"
                      >
                        <div
                          class="flex h-full w-full items-center justify-center overflow-hidden rounded-full border-2 border-transparent"
                        >
                          <Avatar.Image
                            src={participant.avatar_url}
                            alt={participant.name}
                          />
                          <Avatar.Fallback class="border-muted border"
                            >{participant.name[0]}</Avatar.Fallback
                          >
                        </div>
                      </Avatar.Root>
                      {participant.name}
                      {#if selected}
                        <div class="ml-auto">
                          <CheckIcon class="size-4" />
                        </div>
                      {/if}
                    {/snippet}
                  </Combobox.Item>
                {:else}
                  <span class="block px-5 py-2 text-sm text-muted-foreground">
                    No results found, try again.
                  </span>
                {/each}
              </Combobox.Viewport>
              <Combobox.ScrollDownButton
                class="flex w-full items-center justify-center py-1"
              >
                <ChevronDownIcon class="size-3" />
              </Combobox.ScrollDownButton>
            </Combobox.Content>
          </Combobox.Portal>
        </Combobox.Root>
        {#if isLoading === false}
          <div class="space-y-2">
            <div class="my-4">
              {#each participants as participant, i (i + participant.id)}
                <div class="flex items-center gap-2">
                  <Avatar.Root
                    delayMs={200}
                    class="data-[status=loaded]:border-olive-50 bg-muted text-olive-500 border-olive-600 bg-olive-100 reground h-10 w-10 rounded-full border text-[17px] font-medium uppercase data-[status=loading]:border-transparent"
                  >
                    <div
                      class="flex h-full w-full items-center justify-center overflow-hidden rounded-full border-2 border-transparent"
                    >
                      <Avatar.Image
                        src={participant.avatar_url}
                        alt={participant.name}
                      />
                      <Avatar.Fallback class="rounded-full"
                        >{participant.name[0]}</Avatar.Fallback
                      >
                    </div>
                  </Avatar.Root>
                  <p>{participant.name}</p>
                  <span class="font-mono badge badge-sm uppercase"
                    >{participant.role}</span
                  >
                  <Button.Root
                    class="btn btn-sm btn-ghost"
                    onclick={() => removeParticipant(participant)}
                    ><X class="size-4"></X></Button.Root
                  >
                </div>
              {/each}
            </div>
            <div class="card-actions flex items-center mt-2">
              <Dialog.Close disabled={pendingShare} class="btn btn-soft"
                >Cancel</Dialog.Close
              >
              <Button.Root
                disabled={pendingShare}
                class="btn btn-neutral"
                onclick={() => {
                  share();
                }}
              >
                {#if pendingShare}
                  <span class="loading loading-spinner"></span>
                  Sharing...
                {:else}
                  Share
                {/if}
              </Button.Root>
              {#if shareStatus === true || shareStatus === false}
                <span class="badge badge-sm">{shareMessage}</span>
              {/if}
            </div>
          </div>
        {:else}
          <div>
            <div class="skeleton rounded-lg w-full"></div>
            <div class="skeleton rounded-lg w-full"></div>
            <div class="skeleton rounded-lg w-full"></div>
            <div class="skeleton rounded-lg w-full"></div>
          </div>
        {/if}
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

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
              class="btn btn-info btn-xs btn-soft"
              onclick={() => openShareDialog(category.id)}>Share</Button.Root
            >
            <Button.Root
              class="btn btn-ghost btn-xs"
              onclick={() => openEdit(category)}
            >
              Edit
            </Button.Root>
            <Button.Root
              class="btn btn-ghost btn-xs text-error"
              onclick={() =>
                toast.promise(removeCategory(category), {
                  success: "Category deleted",
                  error: "Failed to delete category",
                  loading: "Deleting category",
                })}
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
      <form
        onsubmit={(e) =>
          toast.promise(saveCategory(e), {
            loading: "Saving category",
            success: "Saved category",
            error: "Failed to save category",
          })}
        class="flex flex-col gap-4 p-6"
      >
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
