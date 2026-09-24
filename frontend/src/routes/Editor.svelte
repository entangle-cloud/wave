<script lang="ts">
  // ==========================================
  // Imports
  // ==========================================
  import { onMount, onDestroy } from "svelte";
  import { push, replace } from "svelte-spa-router";
  import { z } from "zod";
  import { type Document } from "../lib/db";

  // UI Components
  import {
    Button,
    AlertDialog,
    ScrollArea,
    Dialog,
    Label,
    Avatar,
    Combobox,
  } from "bits-ui";
  import { Toaster, toast } from "svelte-sonner";
  import Editor from "../lib/Components/editor.svelte";
  import MiniChatBox from "../lib/Components/MiniChatBox.svelte";

  // Icons
  import SaveIcon from "@iconify-svelte/hugeicons/save";
  import AngleDownFilledIcon from "@iconify-svelte/reicon/angle-down-filled";
  import CheckCircleDuotoneIcon from "@iconify-svelte/reicon/check-filled";
  import TrashIconFilled from "@iconify-svelte/reicon/trash-filled";
  import ArrowsUpIcon from "@iconify-svelte/reicon/arrows-up";
  import ArrowsDownIcon from "@iconify-svelte/reicon/arrows-down";
  import Tag2DuotoneIcon from "@iconify-svelte/reicon/tag2-duotone";

  // Stores and Libs
  import { apiFetch } from "../lib/api";
  import { db } from "../lib/db";
  import {
    editorTitle,
    editorContent,
    docVersion,
    activeDoc,
    documentLoading,
  } from "../store/editorStore.svelte";
  import { ensurePosts, postsByCategory } from "../store/sidebarStore.svelte";
  import {
    categories,
    selectedCategoryId,
    sortCategoriesForDisplay,
  } from "../store/categoryStore.svelte";
  import { userStore } from "../store/authStore.svelte";
  import { miniChatResponses } from "../store/chatStore.svalte";
  import { marked } from "marked";

  // ==========================================
  // Types & Schemas
  // ==========================================

  /**
   * Represents information about a document section for outlining
   */
  type SectionInfo = {
    id: string;
    text?: string;
    level: number;
  };

  /**
   * Represents a complete section node in the document outline tree
   */
  type OutlineSection = {
    id: string;
    text?: string;
    content: unknown[];
    level: number;
  };

  /**
   * Zod schema for document validation prior to saving
   */
  const saveSchema = z.object({
    title: z.string().min(1, "Title is required"),
    description: z.string().min(1, "Description is required"),
    categoryId: z.string().min(1, "Category is required"),
  });

  // ==========================================
  // Component Props
  // ==========================================

  /**
   * Component parameters primarily to retrieve route variables (e.g. document id)
   */
  let { params }: { params?: { id?: string } } = $props();

  // ==========================================
  // State Variables
  // ==========================================

  /** Component reference to the Editor instance (null while unmounted) */
  let editorRef = $state<Editor | undefined>(undefined);

  let dialogAlertOpen = $state(false);
  let isDeleting = $state(false);

  /** Whether the document save modal is currently open */
  let saveOpen = $state(false);

  /** Tracks input value for the category selection combobox */
  let categorySearchValue = $state("");

  /** Stores form validation errors */
  let errors = $state({ title: "", description: "", category: "" });

  /**
   * Mount seed for the editor. The editor is destroyed and recreated per
   * document (`{#key}` in the template) and mounts already seeded with the
   * document's content — so route switches never diff one large document
   * into another inside a live ProseMirror view (the previous freeze).
   * Null while the document is loading (skeleton shows instead).
   * Set exactly once per document; later server refreshes update the
   * `editorContent` store in place and must NOT remount (would lose typing).
   */
  let editorMount = $state<{ docId: string | null; seed: string } | null>(null);

  /**
   * Metadata associated with the current document
   */
  let documentTitle = $state("");
  let documentId = $state(0);
  let documentDescription = $state("");
  let authorName = $state("");
  let authorAvatar = $state("");
  let authorIsActive = $state(true);

  // ==========================================
  // Derived State
  // ==========================================

  /** List of categories sorted for presentation in the UI */
  const sortedCategories = $derived(sortCategoriesForDisplay($categories));

  /** Categories filtered by the user's search input in the combobox */
  const filteredCategories = $derived(
    categorySearchValue === ""
      ? sortedCategories
      : sortedCategories.filter((category) =>
          category.name
            .toLowerCase()
            .includes(categorySearchValue.toLowerCase()),
        ),
  );

  /** Formatted categories for use as items in the Combobox component */
  const categoryItems = $derived(
    sortedCategories.map((category) => ({
      value: category.id.toString(),
      label: category.name,
    })),
  );

  // ==========================================
  // Lifecycle & Effects
  // ==========================================

  /**
   * Component mount initialization. Navigates to new document if id is absent,
   * otherwise prepares stores for the loaded document.
   */
  onMount(async () => {
    if (!params?.id) {
      replace("/docs/new");
    }
    // const mappedCategory = mappedCategories;
    // categories.set(mappedCategory);

    const postId = params?.id;
    if (postId && postId !== "new") {
      // toast.promise(loadDocument(postId), {
      //   loading: "Loading document",
      //   success: "Document loaded",
      //   error: "Error loading document",
      // });
    } else {
      editorTitle.set(null);
      activeDoc.set(null);
      editorContent.set("#");
      editorMount = { docId: "new", seed: "#" };
      setSelectedCategoryId("0");
    }
  });

  onDestroy(() => {
    editorTitle.set(null);
    activeDoc.set(null);
    editorContent.set("#");
    editorMount = null;
    setSelectedCategoryId("0");
  });

  /**
   * Reactively fetches the document anytime the route parameter `id` changes.
   * Cleans up editor stores if creating a new document.
   *
   * NOTE: no intermediate `editorContent.set("#")` here — clearing to "#"
   * before the real content caused 2 full synchronous parse+diff+render
   * passes per route switch and froze the UI on large docs. The editor shows
   * a loading skeleton via `documentLoading` instead.
   */
  $effect(() => {
    const postId = params?.id;
    if (postId && postId !== "new") {
      documentLoading.set(true);
      // Unmount the previous document's editor synchronously so its
      // ProseMirror view is fully destroyed before the new one mounts.
      editorMount = null;
      toast.promise(loadDocument(postId), {
        success: () => {
          documentLoading.set(false);
          return "Document loaded";
        },
        error: () => "Error loading document",
        loading: () => {
          documentLoading.set(true);
          return "Loading document";
        },
      });
    } else {
      editorTitle.set(null);
      activeDoc.set(null);
      editorContent.set("#");
      editorMount = { docId: null, seed: "#" };
      authorName = $userStore?.name ? $userStore.name : "";
      authorAvatar = $userStore?.avatar ? $userStore.avatar : "";
    }
  });

  // ==========================================
  // Functions & Event Handlers
  // ==========================================

  /**
   * Retrieves the currently selected category id from the store.
   * @returns {string} The ID of the currently selected category
   */
  function getSelectedCategoryId(): string {
    return $selectedCategoryId ?? "";
  }

  /**
   * Updates the selected category id in the store.
   * @param {string | null | undefined} value - The ID of the category to set as selected
   */
  function setSelectedCategoryId(value: string | null | undefined): void {
    selectedCategoryId.set(value || null);
  }

  /**
   * Event handler for updates on the category combobox search input.
   * @param {Event & { currentTarget: HTMLInputElement }} e - The input event
   */
  const handleCategorySearchInput = (
    e: Event & { currentTarget: HTMLInputElement },
  ) => {
    categorySearchValue = e.currentTarget.value;
  };

  /**
   * Opens the document save modal. Defaults the document title based on
   * editor content if not already populated.
   */
  const openSaveSheet = () => {
    if (!documentTitle) {
      documentTitle = editorRef?.getDocTitle() ?? "";
    }
    saveOpen = true;
  };

  const addDocumentToLocalDB = async (
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
    await db.documents.put({
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
   * Validates document metadata and saves the document to the server and local database.
   * Handles creating new documents vs. updating existing ones.
   */
  const saveDoc = async () => {
    const validation = saveSchema.safeParse({
      title: documentTitle,
      description: documentDescription,
      categoryId: getSelectedCategoryId(),
    });

    if (!validation.success) {
      const flattenErrors = validation.error.flatten().fieldErrors;
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
            description: documentDescription,
          }),
        },
      );

      if (request.ok) {
        const updatedList = $postsByCategory[
          Number(getSelectedCategoryId())
        ].map((item) =>
          item.id === Number(params.id)
            ? { ...item, title: $editorTitle ?? "Untitled" }
            : item,
        );

        postsByCategory.update((map) => ({
          ...map,
          [Number(getSelectedCategoryId())]: updatedList,
        }));

        const jsonRequest = await request.json();
        await addDocumentToLocalDB(
          jsonRequest.id,
          jsonRequest.title,
          $editorContent ? $editorContent : "",
          documentDescription,
          Number(getSelectedCategoryId()),
          jsonRequest.created_by,
          authorName,
          jsonRequest.created_at,
          jsonRequest.updated_at,
        );
        await replace(`/docs/${jsonRequest.id}`);
      }
    } else if (params && params.id !== "new") {
      const request = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/posts/${documentId}`,
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
            description: documentDescription,
          }),
        },
      );
      const jsonRequest = await request.json();

      const updatedList = $postsByCategory[Number(getSelectedCategoryId())].map(
        (item) =>
          item.id === Number(params.id)
            ? { ...item, title: $editorTitle ?? "Untitled" }
            : item,
      );

      postsByCategory.update((map) => ({
        ...map,
        [Number(getSelectedCategoryId())]: updatedList,
      }));

      await addDocumentToLocalDB(
        jsonRequest.id,
        jsonRequest.title,
        $editorContent ? $editorContent : "",
        documentDescription,
        Number(getSelectedCategoryId()),
        jsonRequest.created_by,
        authorName,
        jsonRequest.created_at,
        jsonRequest.updated_at,
      );
    }
  };

  /**
   * Deletes a document by its ID and refreshes the sidebar posts list.
   * @param {number} id - The ID of the document to delete
   */
  const deleteDocument = async (id: number) => {
    isDeleting = true;
    const request = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/posts/${id}`,
      {
        method: "DELETE",
        credentials: "include",
      },
    );

    if (request.ok) {
      console.log("delete successful");
      await push("/");
      dialogAlertOpen = false;
      db.documents.delete(Number(params?.id));
      await ensurePosts(Number(getSelectedCategoryId()));
    } else {
      dialogAlertOpen = false;
      isDeleting = false;
    }
  };

  /**
   * Loads a document from the server by its ID. Populates local state and stores.
   * @param {string} postId - The ID of the post to load
   */
  let loadGeneration = 0;
  async function loadDocument(postId: string) {
    const generation = ++loadGeneration;
    documentLoading.set(true);
    try {
      const current = await db.documents.get(Number(postId));
      // Another document load started while this one was waiting.
      if (generation !== loadGeneration) return;
      if (current) {
        console.info("loaded from database");
        // Set activeDoc BEFORE content so the editor sees the doc switch
        // atomically and takes the fast full-replace path exactly once.
        activeDoc.set(postId);
        editorContent.set(current.content);
        // Mount (or remount, if the key changed) the editor already seeded
        // with this document's content — single parse, no cross-doc diff.
        editorMount = { docId: postId, seed: current.content };
        documentTitle = current.title;
        documentDescription = current.description;
        documentId = current.id;
        authorName = current.createdByName;
        docVersion.set(1)
        setSelectedCategoryId(current.categoryId.toString());
      } else {
        activeDoc.set(postId);
      }
      // Don't let an old refresh update the newly selected document.
      void refreshFromServer(postId, current, generation);
    } catch (e) {
      if (generation === loadGeneration) {
        console.log(e);
      }
    } finally {
      if (generation === loadGeneration) {
        documentLoading.set(false);
      }
    }
  }

  async function refreshFromServer(
    postId: string,
    current: Document | undefined,
    generation: number,
  ) {
    try {
      const request = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/posts/${postId}`,
      );
      // Ignore stale requests.
      if (generation !== loadGeneration) return;
      if (!request.ok) return;
      const requestJson = await request.json();
      // The request may have completed while another document was selected.
      if (generation !== loadGeneration) return;
      authorAvatar = requestJson.author_avatar;
      authorIsActive = requestJson.author_active;
      const localUpdated = current
        ? new Date(current.updatedDateTime).getTime()
        : undefined;
      const serverUpdated = new Date(requestJson.updated_at).getTime();
      const serverIsNewer =
        localUpdated === undefined || localUpdated !== serverUpdated;
      if (!serverIsNewer) {
        return;
      }
      // Check again before changing editor state.
      if (generation !== loadGeneration) return;
      await addDocumentToLocalDB(
        requestJson.id,
        requestJson.title,
        requestJson.content,
        requestJson.description,
        requestJson.category_id,
        requestJson.author_id,
        requestJson.author_name,
        requestJson.created_at,
        requestJson.updated_at,
      );
      // Don't let an old request overwrite the current document.
      // Single content set (was duplicated) — one parse+apply only.
      // Never touches `editorMount`: a mounted editor applies this via its
      // same-doc refresh path; an unmounted one (Dexie miss) mounts now.
      if (generation !== loadGeneration) return;
      activeDoc.set(postId);
      editorContent.set(requestJson.content);
      if (!editorMount || editorMount.docId !== postId) {
        editorMount = { docId: postId, seed: requestJson.content };
      }
      documentTitle = requestJson.title;
      documentId = requestJson.id;
      authorName = requestJson.author_name;
      documentDescription = requestJson.description;
      setSelectedCategoryId(requestJson.category_id.toString());
      docVersion.set(requestJson.updated_at)
      console.info("loaded from server");
    } catch (e) {
      if (generation === loadGeneration) {
        console.log(e);
      }
    }
  }
  /**
   * Toggles a generic loading state
   */
  const isLoadingToggle = () => {};
</script>

<svelte:head>
  <title>{documentTitle ? documentTitle : "New Document"} - 🌊 Wave</title>
</svelte:head>

<AlertDialog.Root bind:open={dialogAlertOpen}>
  <AlertDialog.Portal>
    <AlertDialog.Overlay
      class="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/80"
    />
    <AlertDialog.Content
      class="card card-lg bg-white data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 outline-hidden fixed left-[50%] top-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 border p-7 sm:max-w-lg md:w-full "
    >
      <div class="flex flex-col gap-4 pb-6">
        <AlertDialog.Title class="text-lg font-semibold tracking-tight">
          Are you sure?
        </AlertDialog.Title>
        <AlertDialog.Description class="text-foreground-alt text-sm">
          This will delete the selected document permanently. This action cannot
          be undone.
        </AlertDialog.Description>
      </div>
      <div class="flex w-full items-center justify-end gap-2">
        <AlertDialog.Cancel class="btn rounded-lg btn-neutral">Cancel</AlertDialog.Cancel>
        <AlertDialog.Action
          disabled={isDeleting === true}
          onclick={() => {
            if (params) deleteDocument(Number(params.id));
          }}
          class="btn rounded-lg btn-error"
        >
          {#if isDeleting}
            <span class="loading loading-sm"></span>
            Deleting...
          {:else}
            Confirm
          {/if}
        </AlertDialog.Action>
      </div>
    </AlertDialog.Content>
  </AlertDialog.Portal>
</AlertDialog.Root>

<Toaster />
<div
  class="flex h-full flex-col overflow-hidden rounded-lg bg-white ring ring-base-300"
>
  <div class="navbar shrink-0 border-b border-base-200">
    <div class="flex-1 flex items-center">
      <div class="grow">
        <a href="/#" class="btn rounded-lg btn-ghost text-xl"
          >{documentTitle ?? "Untitled"}</a
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
            <Avatar.Image src={authorAvatar} alt={authorName} />
            <Avatar.Fallback class="border-muted border"
              >{authorName.length > 0
                ? authorName[0].toUpperCase
                : "R"}</Avatar.Fallback
            >
          </div>
        </Avatar.Root>
        <Label.Root class={authorIsActive ? "" : "text-olive-400"}>
          {authorName}
        </Label.Root>
      </div>
    </div>
    <div class="flex-none">
      <ul class="menu menu-horizontal flex items-center px-1 gap-1.5">
        <li>
          <Button.Root
            class="btn rounded-lg btn-primary btn-soft btn-sm"
            onclick={openSaveSheet}
          >
            <SaveIcon class="size-4" />
            Save</Button.Root
          >
        </li>
        {#if params && params?.id !== "new"}
          <li>
            <Button.Root
              onclick={() => (dialogAlertOpen = true)}
              class="btn rounded-lg btn-soft btn-error btn-sm"
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
        {#if editorMount}
          {#key editorMount.docId}
            <Editor
              bind:this={editorRef}
              docId={editorMount.docId}
              initialContent={editorMount.seed}
            />
          {/key}
        {:else}
          <div
            class="flex flex-col gap-3 p-6"
            aria-live="polite"
            aria-busy="true"
          >
            <div class="skeleton h-8 w-2/5"></div>
            <div class="skeleton h-4 w-full"></div>
            <div class="skeleton h-4 w-full"></div>
            <div class="skeleton h-4 w-4/5"></div>
            <div class="skeleton h-4 w-full"></div>
            <div class="skeleton h-4 w-3/5"></div>
            <span class="sr-only">Loading document…</span>
          </div>
        {/if}
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
    {#if params?.id !== "new" && $documentLoading === false}
      <div
        class="h-full py-4 flex flex-col bg-olive-50 col-span-3 duration-2000 transition-all transform min-h-0"
      >
        <ScrollArea.Root class="flex-1 min-h-0 pb-4">
          <ScrollArea.Viewport class="size-full">
            <div class="flex flex-col justify-end min-h-full">
              <div class="grow flex items-center px-4">
                {#if $miniChatResponses.length === 0}
                  <div class="w-full">
                    <div class="card bg-olive-100">
                      <div class="card-body">
                        <p class="font-semibold text-olive-600">
                          Use AI to find information or do anything with the document.
                        </p>
                      </div>
                    </div>
                  </div>
                {/if}
              </div>
              {#if $miniChatResponses.length > 0}
                <div id="responses" class="px-4 flex flex-col gap-4">
                {#each $miniChatResponses as response}
                <div class="bg-olive-100 card">
                  <div class="card-body text-olive-600 prose">
                    {@html marked(response)}
                  </div>
                </div>
                {/each}
                </div>
              {/if}
            </div>
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
        <MiniChatBox categoryId={undefined} documentId={params?.id} />
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
          toast.promise(saveDoc(), {
            loading: "Saving document",
            success: "Document saved",
            error: "Failed to save document",
          });
        }}
      >
        <Label.Root class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">Title</span>
          <input
            type="text"
            class="input input-bordered w-full"
            bind:value={documentTitle}
          />
          {#if errors.title.length > 0}
            <span class="text-error text-sm mt-1.5">{errors.title}</span>
          {/if}
        </Label.Root>

        <Label.Root class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">
            Description
          </span>
          <textarea
            class="textarea textarea-bordered w-full"
            rows="3"
            bind:value={documentDescription}
          ></textarea>
          {#if errors.description.length > 0}
            <span class="text-error text-sm mt-1.5">{errors.description}</span>
          {/if}
        </Label.Root>

        <div class="form-control">
          <span class="label-text mb-1 block text-sm font-medium">Category</span
          >
          <Combobox.Root
            type="single"
            items={categoryItems}
            allowDeselect
            bind:value={getSelectedCategoryId, setSelectedCategoryId}
            onOpenChangeComplete={(open) => {
              if (!open) categorySearchValue = "";
            }}
          >
            <div class="relative w-full">
              <div class="relative">
                <Tag2DuotoneIcon
                  class="text-muted-foreground absolute inset-s-3 top-1/2 size-6 z-40 -translate-y-1/2"
                />
                <Combobox.Input
                  oninput={handleCategorySearchInput}
                  class="input px-9 input-bordered w-full pr-9"
                  placeholder={filteredCategories.find(
                    (value) => value.id.toString() === $selectedCategoryId,
                  )?.name ?? "None"}
                  aria-label="Select category"
                />
                <Combobox.Trigger
                  class="absolute inset-y-0 right-0 flex items-center pr-3 cursor-pointer"
                  aria-label="Toggle category list"
                >
                  <AngleDownFilledIcon
                    class="size-6 opacity-60 pointer-events-none"
                  />
                </Combobox.Trigger>
              </div>

              <Combobox.Portal>
                <Combobox.Content
                  sideOffset={6}
                  class="menu rounded-box z-50 flex max-h-64 min-w-(--bits-combobox-anchor-width) flex-col overflow-hidden border border-base-300 bg-base-100 p-2 shadow-lg"
                >
                  <Combobox.Viewport class="min-h-0 flex-1 overflow-y-auto">
                    {#each filteredCategories as category (category.id)}
                      <Combobox.Item
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
                      </Combobox.Item>
                    {:else}
                      <div class="px-3 py-1.5 text-sm text-base-content/50">
                        No categories found
                      </div>
                    {/each}
                  </Combobox.Viewport>
                </Combobox.Content>
              </Combobox.Portal>
            </div></Combobox.Root
          >
          {#if errors.category.length > 0}
            <span class="text-error text-sm my-1.5">{errors.category}</span>
          {/if}
        </div>
      </form>

      <div class="flex justify-end gap-2 border-t border-base-200 px-6 py-4">
        <Dialog.Close class="btn rounded-lg btn-ghost">Cancel</Dialog.Close>
        <Button.Root
          type="submit"
          form="save-form"
          class="btn rounded-lg btn-primary btn-soft"
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
