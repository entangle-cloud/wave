<script lang="ts">
  import { categories } from "../store/categoryStore.svelte";
  import { apiFetch } from "../lib/api";
  import { toast } from "svelte-sonner";
  import ChatBox from "../lib/Components/ChatBox.svelte";
  import DocumentOnePageMultiple24RegularIcon from "@iconify-svelte/fluent/document-one-page-24-regular";

  import { Style, Avatar } from "@dicebear/core";
  import definition from "@dicebear/styles/initials.json" with { type: "json" };

  let { params }: { params: { id: string } } = $props();

  const style = new Style(definition);

  let documents = $state<{
    category: {
      id: number;
      name: string;
      description: string | undefined;
      colour: string;
    };
    posts: { title: string; description: string; id: number }[];
  }>({
    category: {
      id: 0,
      name: "",
      description: "",
      colour: "",
    },
    posts: [],
  });

  let isLoading = $state(true);

  const documentRequest = async (id: string) => {
    const response = await apiFetch(
      `${import.meta.env.VITE_API_ENDPOINT}/posts/categories/${id}`,
      {
        credentials: "include",
      },
    );

    if (response.ok) {
      const documentRequestJson = await response.json();
      documents = documentRequestJson;
      documents.category.description = $categories.find(
        (cat) => cat.id === documents.category.id,
      )?.description;
    }
    isLoading = false;
  };

  $effect(() => {
    const categoryId = params?.id;
    if (categoryId) {
      toast.promise(documentRequest(categoryId), {
        success: "Documents loaded",
        loading: "Loading documents",
        error: "Failed to load documents",
      });
    }
  });

  const avatar = $derived(
    new Avatar(style, {
      backgroundColor: ["ffe3ea", "e3edff", "e2f5e9", "fdf1d4", "efe6ff", "ffadad", "ffd6a5", "d4a373", "d5bdaf", "b8e0d2", "71a5de"  ],
      lettersVariant: { single: 1 },
      seed: documents.category.name,
    }),
  );

  // if you render it as a data URI, derive that too
  const avatarUri = $derived(avatar.toDataUri());
</script>

<svelte:head>
  <title>{documents.category.name} - 🌊 Wave</title>
</svelte:head>

<ChatBox />
<div class="px-6 max-w-5xl mx-auto mt-8">
  {#if !isLoading}
    <div class="gap-2">
      <div class="flex gap-2 items-center">
        <div class="size-10 rounded-xl">
          <img class="rounded-xl" src={avatarUri} alt={documents.category.name} />
        </div>
        <h1 class="text-4xl text-olive-800 font-bold">
          {documents.category.name}
        </h1>
      </div>
      <h2 class="px-12 text-lg text-olive-600">
        {documents.category.description}
      </h2>
    </div>
  {/if}
  <div class="my-2 flex flex-col gap-2">
    {#if isLoading}
      <div class="grid gap-2">
        <div class="skeleton h-10"></div>
        <div class="skeleton h-10"></div>
        <div class="skeleton h-10"></div>
      </div>
    {:else}
      <div class="mt-8">
        {#each documents.posts as document}
          <div
            class="rounded-lg hover:bg-olive-100 transition-all transform duration-300 bg-white w-full mb-4"
          >
            <div>
              <div class="flex gap-2">
                <div class="shrink"></div>
                <div>
                  <a href={`/#/docs/${document.id}`}>
                    <h2
                      class="text-olive-800 card-title font-medium underline underline-offset-4 decoration-olive-300 hover:decoration-olive-600 transition-all duration-300 transform"
                    >
                      <DocumentOnePageMultiple24RegularIcon  class="size-4 text-olive-600" />
                      {document.title}
                    </h2>
                  </a>
                  <p class="text-olive-600 px-6 select-none">
                    {document.description}
                  </p>
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
