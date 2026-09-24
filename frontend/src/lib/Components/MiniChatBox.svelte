<script lang="ts">
  import { apiFetch } from "../api";
  import ArrowEnterLeft24RegularIcon from "@iconify-svelte/fluent/arrow-enter-left-24-regular";
  import { Button, Switch, Label } from "bits-ui";
  import {
    documentLoading,
    docVersion,
    editorContent,
  } from "../../store/editorStore.svelte";
  import { miniChatResponses } from "../../store/chatStore.svalte";
  import { map } from "zod";
  let question = $state("");
  let isLoading = $state(false);
  let responses = $state<string[]>([]);
  let sentMarkdown = $state("");

  let researchMode = $state(false);

  function getChecked() {
    return researchMode;
  }

  function setChecked(newChecked: boolean) {
    researchMode = newChecked;
  }

  const splitSections = (md: string) => {
    return md
      .split(/^(?=#{1,3} )/m) // split before h1-h3 headings
      .filter((p) => p.trim())
      .map((markdown, i) => ({ id: `s${i}`, markdown }));
  };

  const handleSubmit = (e: any) => {
    e.preventDefault();
    sentMarkdown = $editorContent || "";
    const documentSections = splitSections($editorContent || "");
    isLoading = true;
    if (question.trim().length === 0) return;
    apiFetch(`${import.meta.env.VITE_API_ENDPOINT}/ask`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        question: `${question} \n`,
        referenceDocument: documentId,
        sections: documentSections,
        base_version: $docVersion,
        research_mode: researchMode
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        responses.push(data.response);
        miniChatResponses.set(responses);

        if (data.edits.length) {
          if ($editorContent !== sentMarkdown) {
            // user kept typing while the model was working: don't overwrite
            responses.push(
              "The document changed while I was editing. Please retry.",
            );
            return;
          }
          const byId = new Map(
            data.edits.map((e: { section_id: string; markdown: string }) => [
              e.section_id,
              e.markdown,
            ]),
          );
          const next = documentSections
            .map((s) => ((byId.get(s.id) ?? s.markdown) as string).trimEnd())
            .join("\n\n");
          editorContent.set(next);
          question = "";
        }
      })
      .finally(() => (isLoading = false));
  };

  function handleKeydown(e: any) {
    if (question.trim().length === 0) return;
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      e.target.form?.requestSubmit();
    }
  }

  let {
    documentId,
    categoryId,
  }: { documentId: string | undefined; categoryId: string | undefined } =
    $props();
</script>

<div class="px-3">
  {#if $documentLoading}
    <div class="mb-4">
      <span class="loading loading-sm fill-indigo-400"></span>
      Loading document
    </div>
  {/if}

  <div class="border-olive-400 rounded-lg border bg-white p-1">
    <form onsubmit={handleSubmit} class="group">
      <textarea
        onkeydown={handleKeydown}
        class="border-none rounded-lg resize-none w-full textarea focus:ring-0 focus:outline-0"
        placeholder="How can I help you?"
        bind:value={question}
      ></textarea>
      <div class="h-10 items-center gap-2 flex justify-end">
        <div
          class=" items-center space-x-2 px-2 group-focus-within:flex hidden"
        >
          <Switch.Root
            id="research"
            bind:checked={getChecked, setChecked}
            name="hello"
            class="focus-visible:ring-black focus-visible:ring-offset-white data-[state=checked]:bg-black data-[state=unchecked]:bg-gray-200 data-[state=unchecked]:shadow-inner dark:data-[state=checked]:bg-white dark:data-[state=unchecked]:bg-gray-700 focus-visible:outline-none peer inline-flex h-6 min-h-6 w-10 shrink-0 cursor-pointer items-center rounded-full px-0.75 transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Switch.Thumb
              class="bg-white data-[state=unchecked]:shadow-sm dark:border-white/30 dark:bg-black dark:shadow-lg pointer-events-none block size-4 shrink-0 rounded-full transition-transform data-[state=checked]:translate-x-4.5 data-[state=unchecked]:translate-x-0 dark:border dark:data-[state=unchecked]:border"
            />
          </Switch.Root>
          <Label.Root for="research" class="text-sm text-olive-700 font-medium"
            >Research</Label.Root
          >
        </div>
        <div class="{isLoading ? 'aura' : ''} group-focus-within:block hidden">
          <Button.Root class="btn rounded-lg btn-sm"
            ><ArrowEnterLeft24RegularIcon class="size-4" /> Enter</Button.Root
          >
        </div>
      </div>
    </form>
  </div>
</div>
