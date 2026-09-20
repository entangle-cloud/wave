<script lang="ts">
  import { apiFetch } from "../api";
  import ArrowEnterLeft24RegularIcon from "@iconify-svelte/fluent/arrow-enter-left-24-regular";
  import { Button } from "bits-ui";
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
  let sentMarkdown = $state("")

  const splitSections = (md: string) => {
    return md
      .split(/^(?=#{1,3} )/m) // split before h1-h3 headings
      .filter((p) => p.trim())
      .map((markdown, i) => ({ id: `s${i}`, markdown }));
  };

  const handleSubmit = (e: any) => {
    e.preventDefault();
    sentMarkdown = $editorContent || ""
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
            data.edits.map((e: {section_id: string, markdown: string}) => [e.section_id, e.markdown]),
          );
          const next = documentSections
            .map((s) => ((byId.get(s.id) ?? s.markdown)as string).trimEnd())
            .join("\n\n");
          editorContent.set(next)
          question = ""
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
      <div class="h-10 flex justify-end">
        <div class="{isLoading ? 'aura' : ''} group-focus-within:block hidden">
          <Button.Root class="btn btn-sm"
            ><ArrowEnterLeft24RegularIcon class="size-4" /> Enter</Button.Root
          >
        </div>
      </div>
    </form>
  </div>
</div>
