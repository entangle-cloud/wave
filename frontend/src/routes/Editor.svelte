<script lang="ts">
  import { Button, ScrollArea, Dialog, Label, Select } from "bits-ui";
  import Editor from "../lib/Components/editor.svelte";
  import SaveIcon from "@iconify-svelte/hugeicons/save";
  import { editorTitle, editorContent } from "../store/editorStore.svelte";
  import {
    categories,
    selectedCategoryId,
  } from "../store/categoryStore.svelte";
  import AngleDownFilledIcon from "@iconify-svelte/reicon/angle-down-filled";
  import ArrowsUpIcon from "@iconify-svelte/reicon/arrows-up";
  import ArrowsDownIcon from "@iconify-svelte/reicon/arrows-down";

  let saveOpen = $state(false);
  let editorRef: Editor;

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

  let sections = $state<OutlineSection[]>([]);
  let meta = $state({ title: "", tags: "", description: "" });

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
    sections = (editorRef?.getOutline() ?? []) as OutlineSection[];
    if (!meta.title) {
      meta.title = editorRef?.getDocTitle() ?? "";
    }
    saveOpen = true;
  };

  const saveDoc = async () => {
    console.log(
      "save",
      meta,
      sections.map((s) => s.id),
    );
    saveOpen = false;
    console.log($editorContent);
    console.log(getSelectedCategoryId());
    const request = await fetch(`${import.meta.env.VITE_API_ENDPOINT}/posts`, {
      method: "POST",
      headers: {
        'content-type': 'application/json',
      },
      credentials: "include",
      body: JSON.stringify({
        title: $editorTitle,
        category_id: Number(getSelectedCategoryId()),
        content: $editorContent,
      })
    })
    console.log(await request.json())
  };
</script>

<div
  class="flex h-full flex-col overflow-hidden rounded-lg bg-white ring ring-base-300"
>
  <div class="navbar shrink-0 border-b border-base-200 shadow-sm">
    <div class="flex-1">
      <a href="/#" class="btn btn-ghost text-xl">{$editorTitle ?? "Untitled"}</a
      >
    </div>
    <div class="flex-none">
      <ul class="menu menu-horizontal px-1">
        <li>
          <Button.Root
            class="btn btn-primary btn-soft btn-sm"
            onclick={openSaveSheet}
          >
            <SaveIcon height="1em" />
            Save</Button.Root
          >
        </li>
      </ul>
    </div>
  </div>

  <ScrollArea.Root class="min-h-0 flex-1 pb-6">
    <ScrollArea.Viewport class="size-full">
      <Editor bind:this={editorRef} />
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
          Review metadata and sections before saving.
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
                      class="flex items-center gap-2 rounded-field px-3 py-1.5 text-sm data-highlighted:bg-base-200"
                    >
                      {#snippet children({ selected })}
                        <span
                          class="size-2 shrink-0 rounded-full"
                          style="background:{category.color}"
                        ></span>
                        <span class="truncate">
                          {category.parentId ? "— " : ""}{category.name}
                        </span>
                        {#if selected}
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            class="ml-auto size-4"
                          >
                            <path d="M20 6 9 17l-5-5" />
                          </svg>
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
        </div>

        <div class="mt-2">
          <h3
            class="mb-2 text-xs font-semibold uppercase tracking-wider text-base-content/50"
          >
            Sections ({sections.length})
          </h3>
          <ul class="menu w-full gap-0.5 bg-base-200 rounded-box p-2">
            {#each sections as section (section.id)}
              <li style="margin-left:{(section.level - 1) * 0.75}rem;">
                <span class="truncate text-sm">
                  {section.text || "Untitled section"}
                </span>
              </li>
            {:else}
              <li>
                <span class="text-sm text-base-content/50"
                  >No sections found</span
                >
              </li>
            {/each}
          </ul>
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
