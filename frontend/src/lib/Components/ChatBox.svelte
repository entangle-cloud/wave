<script lang="ts">
  import { userStore } from "../../store/authStore.svelte";
  import Plus from "@iconify-svelte/reicon/plus";
  import { Avatar, Button, Label } from "bits-ui";
  import { push } from "svelte-spa-router";
  import ChatResponses from "./ChatResponses.svelte";
  import {
    chatResponse,
    chatReferences,
    responseAvailable,
  } from "../../store/chatStore.svalte";
  const userData = $derived($userStore);

  let message = $state("");
  let loading = $state(false);

  const ask = async () => {
    loading = true;
    const request = await fetch(`${import.meta.env.VITE_API_ENDPOINT}/ask`, {
      credentials: "include",
      method: "post",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        question: message,
      }),
    })
      .then((data) => data.json())
      .then((response) => {
        chatResponse.set(response.response);
        chatReferences.set(response.references);
        responseAvailable.set(true);
      })
      .finally(() => (loading = false));
  };
</script>

<div class="grow bg-base-100 h-full">
  <div class="mx-auto max-w-5xl">
    <div class="card w-9/10">
      <div class="card-body">
        <div class="flex gap-1.5 items-center">
          <Avatar.Root
            delayMs={200}
            class="data-[status=loaded]:border-foreground bg-muted text-muted-foreground h-8 w-8 rounded-full  text-[17px] font-medium uppercase data-[status=loading]:border-transparent"
          >
            <div
              class="flex h-full w-full items-center justify-center overflow-hidden rounded-full border-2 border-transparent"
            >
              <Avatar.Image src={userData?.avatar} alt={userData?.name[0]} />
              <Avatar.Fallback class="border-muted border">RR</Avatar.Fallback>
            </div>
          </Avatar.Root>
          <Label.Root class="text-base montserrat-heading"
            >Hi {userData?.name},
            <span class="font-light"
              >Search and find anything from the knowledge base</span
            ></Label.Root
          >
        </div>

        <div
          class="border border-olive-300 focus-within:border-olive-400 rounded-xl p-4"
        >
          <div class="px-2">
            <textarea
              bind:value={message}
              class="bg-white w-full text-lg resize-none focus-within:outline-none"
              placeholder="Just ask anything..."
            >
            </textarea>
          </div>
          <div class="justify-between flex items-center">
            <Button.Root
              onclick={() => push("/docs/new")}
              class="btn btn-ghost btn-circle rounded-full"
              ><Plus class="h-5"></Plus></Button.Root
            >
            <Button.Root
              onclick={ask}
              class="btn btn-md rounded-lg bg-black text-olive-50"
            >
              {#if loading}
                <span class="loading loading-spinner"></span>
                Thinking..
              {:else}
                Ask
              {/if}
            </Button.Root>
          </div>
        </div>
      </div>
    </div>
  </div>
  <ChatResponses />
</div>
