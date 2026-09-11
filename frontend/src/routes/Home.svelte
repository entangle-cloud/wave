<script lang="ts">
  import { onMount } from "svelte";
  import { loadCategories } from "../store/categoryStore.svelte";
  import { apiFetch } from "../lib/api";
  import ChatBox from "../lib/Components/ChatBox.svelte";
  import Document16Icon from "@iconify-svelte/fluent-color/document-16";
  import { push } from "svelte-spa-router";
  import { Button } from "bits-ui";

  let latestDocs = $state<{ title: string; id: number; description: string }[]>(
    [],
  );

  let isLoading = $state(false);
  onMount(async () => {
    isLoading = true;
    await loadCategories();
    const request = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/api/activity`,
    ).finally(() => (isLoading = false));
    const latestActivityResponse = await request.json();
    latestDocs = latestActivityResponse.postActivity;
  });
</script>

<svelte:head>
  <title>Home - 🌊 Wave</title>
</svelte:head>

<div class="flex flex-col">
  <ChatBox />
  <div class="grow h-full">
    <div class="max-w-5xl mx-auto px-4">
      <div class="card w-9/10 bg-olive-100">
        <div class="card-body">
          <h2 class="font-semibold text-olive-500">New Activity</h2>
          {#if isLoading}
            <div class="flex flex-col gap-4">
              <div class="skeleton h-4 w-full"></div>
              <div class="skeleton h-4 w-full"></div>
              <div class="skeleton h-4 w-full"></div>
              <div class="skeleton h-4 w-full"></div>
            </div>
          {:else}
            <div class="grid grid-cols-2 gap-4">
              {#each latestDocs as doc}
                <div class="bg-base-100 rounded-lg shadow-sm px-4 py-4 flex">
                  <div>
                    <Document16Icon class="size-4" />
                  </div>
                  <div>
                    <span class="text-olive-600 flex gap-2">
                      <Button.Root
                        class="link truncate line-clamp-1"
                        onclick={() => push(`#/docs/${doc.id}`)}
                      >
                        {doc.title}
                      </Button.Root>
                    </span>
                    <span
                      class="text-xs text-olive-500 font-light truncate line-clamp-1"
                      >{doc.description}</span
                    >
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>
