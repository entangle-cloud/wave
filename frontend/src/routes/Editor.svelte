<script lang="ts">
  import { apiFetch } from "../lib/api";
  import { Button, ScrollArea, Dialog, Label, Select, Avatar } from "bits-ui";
  import { Toaster, toast } from "svelte-sonner";
  import Editor from "../lib/Components/editor.svelte";
  import SaveIcon from "@iconify-svelte/hugeicons/save";
  import {
    editorTitle,
    editorContent,
    activeDoc,
  } from "../store/editorStore.svelte";
  import { ensurePosts, postsByCategory } from "../store/sidebarStore.svelte";
  import {
    categories,
    selectedCategoryId,
  } from "../store/categoryStore.svelte";
  import AngleDownFilledIcon from "@iconify-svelte/reicon/angle-down-filled";
  import ArrowsUpIcon from "@iconify-svelte/reicon/arrows-up";
  import ArrowsDownIcon from "@iconify-svelte/reicon/arrows-down";
  import { onMount } from "svelte";
  import { mappedCategories } from "../lib/funcs";
  import CheckCircleDuotoneIcon from "@iconify-svelte/reicon/check-filled";
  import TrashIconFilled from "@iconify-svelte/reicon/trash-filled";
  import { userStore } from "../store/authStore.svelte";
  import { z } from "zod";
  import MiniChatBox from "../lib/Components/MiniChatBox.svelte";

  let { params }: { params?: { id?: string } } = $props();

  const saveSchema = z.object({
    title: z.string().min(1, "Title is required"),
    description: z.string().min(1, "Description is required"),
    categoryId: z.string().min(1, "Category is required"),
  });

  let saveOpen = $state(false);
  let editorRef: Editor;
  let loadedContent = $state<string | null>(null);
  let errors = $state({ title: "", description: "", category: "" });
  let isLoading = $state(false);

  type SectionInfo = {
    id: string;
    text?: string;
    level: number;
  };

  type OutlineSection = {
    id: string;
    text?: string;
    content: unknown[];
    level: number;
  };

  let meta = $state({
    id: 0,
    title: "New Document",
    tags: "",
    description: "",
    authorName: "",
    authorAvatar: "",
    authorIsActive: true,
  });

  const categoryItems = $derived(
    $categories.map((category) => ({
      value: category.id.toString(),
      label: category.name,
    })),
  );

  function getSelectedCategoryId() {
    return $selectedCategoryId ?? "";
  }

  function setSelectedCategoryId(value: string | null | undefined) {
    selectedCategoryId.set(value || null);
  }

  const openSaveSheet = () => {
    if (!meta.title) {
      meta.title = editorRef?.getDocTitle() ?? "";
    }
    saveOpen = true;
  };

  const saveDoc = async () => {
    const validation = saveSchema.safeParse({
      title: meta.title,
      description: meta.description,
      categoryId: getSelectedCategoryId(),
    });

    if (!validation.success) {
      let flattenErrors = z.flattenError(validation.error).fieldErrors;
      if (flattenErrors.categoryId) {
        errors.category = flattenErrors.categoryId[0];
      }
      if (flattenErrors.description) {
        errors.description = flattenErrors.description[0];
      }
      if (flattenErrors.title) {
        errors.title = flattenErrors.title[0];
      }

      console.log(errors);

      return;
    }

    saveOpen = false;

    if (params && params.id === "new") {
      const request = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/posts`,
        {
          method: "POST",
          headers: {
            "content-type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            title: $editorTitle,
            category_id: Number(getSelectedCategoryId()),
            content: $editorContent,
            description: meta.description,
          }),
        },
      );

      if (request.ok) {
        await ensurePosts(Number(getSelectedCategoryId()));
      }

      console.log(await request.json());
    } else if (params && params.id !== "new") {
      const request = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/posts/${meta.id}`,
        {
          method: "PATCH",
          headers: {
            "content-type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            post_id: Number(params.id),
            title: $editorTitle,
            category_id: Number(getSelectedCategoryId()),
            content: $editorContent,
            description: meta.description,
          }),
        },
      );
    }
  };

  const deleteDocument = async (id: number) => {
    const request = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/posts/${id}`,
      {
        method: "DELETE",
        credentials: "include",
      },
    );

    if (request.ok) {
      console.log("delete successful");
      await ensurePosts(Number(getSelectedCategoryId()));
    }
  };

  async function loadDocument(postId: string) {
    isLoading = true;
    const request = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/posts/${postId}`,
    );
    if (request.ok) {
      const requestJson: {
        content: string;
        author_id: number;
        category_id: number;
        created_At: Date;
        id: number;
        title: string;
        description: string;
        author_avatar: string;
        author_active: boolean;
        author_name: string;
        content_ref: string;
      } = await request.json();
      loadedContent = requestJson.content;
      meta.title = requestJson.title;
      meta.id = requestJson.id;
      meta.authorAvatar = requestJson.author_avatar;
      meta.authorIsActive = requestJson.author_active;
      meta.authorName = requestJson.author_name;
      meta.description = requestJson.description;
      setSelectedCategoryId(requestJson.category_id.toString());
    }
    activeDoc.set(postId);
  }

  onMount(async () => {
    const mappedCategory = mappedCategories;
    categories.set(mappedCategory);
    const postId = params?.id;
    if (postId && postId !== "new") {
      // toast.promise(loadDocument(postId), {
      //   loading: "Loading document",
      //   success: "Document loaded",
      //   error: "Error loading document",
      // });
    } else {
      editorTitle.set(null);
      loadedContent = null;
      activeDoc.set(null);
    }
  });

  $effect(() => {
    const postId = params?.id;
    if (postId && postId !== "new") {
      toast.promise(loadDocument(postId), {
        success: ()=> {isLoading = false; return "Document loaded"},
        error: ()=>"Error loading document",
        loading: () => {
          isLoading = true;
          return "Loading document";
        },
      });
    } else {
      editorTitle.set(null);
      loadedContent = "#";
      activeDoc.set(null);
      meta.authorName = $userStore?.name ? $userStore.name : "";
      meta.authorAvatar = $userStore?.avatar ? $userStore.avatar : "";
    }
  });
</script>

<svelte:head>
  <title>{meta.title} - 🌊 Wave</title>
</svelte:head>

<Toaster />
<div
  class="flex h-full flex-col overflow-hidden rounded-lg bg-white ring ring-base-300"
>
  <div class="navbar shrink-0 border-b border-base-200">
    <div class="flex-1 flex items-center">
      <div class="grow">
        <a href="/#" class="btn btn-ghost text-xl"
          >{$editorTitle ?? "Untitled"}</a
        >
      </div>
      <div class="justify-end flex items-center mx-4 gap-2">
        <Avatar.Root
          delayMs={200}
          class="data-[status=loaded]:border-foreground bg-muted text-muted-foreground h-10 w-10 rounded-full border text-[17px] font-medium uppercase data-[status=loading]:border-transparent"
        >
          <div
            class="flex h-full w-full items-center justify-center overflow-hidden rounded-full border-2 border-transparent"
          >
            <Avatar.Image src={meta.authorAvatar} alt={meta.authorName} />
            <Avatar.Fallback class="border-muted border"
              >{meta.authorName.length > 0
                ? meta.authorName[0].toUpperCase
                : "R"}</Avatar.Fallback
            >
          </div>
        </Avatar.Root>
        <Label.Root class={meta.authorIsActive ? "" : "text-olive-400"}>
          {meta.authorName}
        </Label.Root>
      </div>
    </div>
    <div class="flex-none">
      <ul class="menu menu-horizontal flex items-center px-1 gap-1.5">
        <li>
          <Button.Root
            class="btn btn-primary btn-soft btn-sm"
            onclick={openSaveSheet}
          >
            <SaveIcon class="size-4" />
            Save</Button.Root
          >
        </li>
        {#if params && params?.id !== "new"}
          <li>
            <Button.Root
              onclick={() => deleteDocument(Number(params.id))}
              class="btn btn-soft btn-error btn-sm"
            >
              <TrashIconFilled class="size-4" />
              Delete
            </Button.Root>
          </li>
        {/if}
      </ul>
    </div>
  </div>

  <div class="grid gap-2 flex-1 min-h-0 grid-cols-10">
    <ScrollArea.Root class="min-h-0 col-span-7 flex-1 pb-6">
      <ScrollArea.Viewport class="size-full">
        <Editor bind:this={editorRef} content={loadedContent} />
      </ScrollArea.Viewport>
      <ScrollArea.Scrollbar
        orientation="vertical"
        class="flex w-2.5 touch-none select-none rounded-bl-md p-0.5 transition-colors hover:bg-base-200"
      >
        <ScrollArea.Thumb
          class="relative flex-1 rounded-full bg-base-content/25"
        />
      </ScrollArea.Scrollbar>
      <ScrollArea.Corner />
    </ScrollArea.Root>
    {#if params?.id !== "new" && isLoading === false}
      <div
        class="h-full py-4 flex flex-col bg-olive-50 col-span-3 justify-end duration-2000 transition-all transform"
      >
        <div class="grow flex items-center px-4">
          <div class="w-full">
            <div class="card bg-olive-100">
              <div class="card-body">
                <p class="font-semibold text-olive-600">
                  Use AI to find infomration or do anything with the document.
                </p>
              </div>
            </div>
          </div>
        </div>
        <MiniChatBox />
      </div>
    {/if}
  </div>
</div>

<Dialog.Root bind:open={saveOpen}>
  <Dialog.Portal>
    <Dialog.Overlay class="sheet-overlay fixed inset-0 z-40 bg-black/40" />
    <Dialog.Content
      class="sheet-content fixed inset-y-0 right-0 z-50 flex w-80 flex-col overflow-y-auto bg-base-100 shadow-xl"
    >
      <div class="border-b border-base-200 px-6 py-4">
        <Dialog.Title class="text-lg font-bold">Save document</Dialog.Title>
        <Dialog.Description class="text-sm text-base-content/60">
          Review and complete the metadata before saving.
        </Dialog.Description>
      </div>

      <form
        id="save-form"
        class="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-4"
        onsubmit={(e) => {
          e.preventDefault();
          saveDoc();
        }}
      >
        <Label.Root class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">Title</span>
          <input
            type="text"
            class="input input-bordered w-full"
            bind:value={meta.title}
          />
          {#if errors.title.length > 0}
            <span class="text-error text-sm mt-1.5">{errors.title}</span>
          {/if}
        </Label.Root>

        <Label.Root class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">Tags</span>
          <input
            type="text"
            class="input input-bordered w-full"
            placeholder="comma, separated, tags"
            bind:value={meta.tags}
          />
        </Label.Root>

        <Label.Root class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">
            Description
          </span>
          <textarea
            class="textarea textarea-bordered w-full"
            rows="3"
            bind:value={meta.description}
          ></textarea>
          {#if errors.description.length > 0}
            <span class="text-error text-sm mt-1.5">{errors.description}</span>
          {/if}
        </Label.Root>

        <div class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">Category</span
          >

          <Select.Root
            type="single"
            items={categoryItems}
            allowDeselect
            bind:value={getSelectedCategoryId, setSelectedCategoryId}
          >
            <Select.Trigger
              class="input input-bordered cursor-pointer flex w-full items-center"
              aria-label="Select category"
            >
              <Select.Value placeholder="None" />
              <AngleDownFilledIcon
                class="size-6 opacity-60 ml-auto pointer-events-none"
              />
            </Select.Trigger>
            <Select.Portal>
              <Select.Content
                sideOffset={6}
                class="menu rounded-box z-50 max-h-64 min-w-(--bits-select-anchor-width) overflow-y-auto border border-base-300 bg-base-100 p-2 shadow-lg"
              >
                <Select.ScrollUpButton
                  class="flex w-full items-center justify-center"
                >
                  <ArrowsUpIcon class="size-3" />
                </Select.ScrollUpButton>
                <Select.Viewport>
                  {#each $categories as category (category.id)}
                    <Select.Item
                      value={category.id.toString()}
                      label="{category.parentId ? '— ' : ''}{category.name}"
                      class="rounded-button gap-2 data-highlighted:bg-muted outline-hidden data-disabled:opacity-50 flex h-10 w-full select-none items-center py-3 pl-5 pr-1.5 text-sm capitalize"
                    >
                      {#snippet children({ selected })}
                        <span
                          class="size-2 shrink-0 rounded-full"
                          style="background:{category.color}"
                        ></span>
                        <span
                          class="truncate {selected ? 'font-semibold' : ''}"
                        >
                          {category.parentId ? "— " : ""}{category.name}
                        </span>
                        {#if selected}
                          <CheckCircleDuotoneIcon class="size-4" />
                        {/if}
                      {/snippet}
                    </Select.Item>
                  {:else}
                    <div class="px-3 py-1.5 text-sm text-base-content/50">
                      No categories yet
                    </div>
                  {/each}
                </Select.Viewport>
                <Select.ScrollDownButton
                  class="flex w-full items-center justify-center"
                >
                  <ArrowsDownIcon class="size-3" />
                </Select.ScrollDownButton>
              </Select.Content>
            </Select.Portal>
          </Select.Root>
          {#if errors.category.length > 0}
            <span class="text-error text-sm my-1.5">{errors.category}</span>
          {/if}
        </div>
      </form>

      <div class="flex justify-end gap-2 border-t border-base-200 px-6 py-4">
        <Dialog.Close class="btn btn-ghost">Cancel</Dialog.Close>
        <Button.Root
          type="submit"
          form="save-form"
          class="btn btn-primary btn-soft"
        >
          <SaveIcon height="1em" /> Save
        </Button.Root>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  :global(.sheet-overlay) {
    animation: sheet-fade 150ms ease-out;
  }
  :global(.sheet-content) {
    animation: sheet-slide 200ms cubic-bezier(0.16, 1, 0.3, 1);
  }
  @keyframes sheet-fade {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes sheet-slide {
    from {
      transform: translateX(320px);
    }
    to {
      transform: translateX(0);
    }
  }
</style>
