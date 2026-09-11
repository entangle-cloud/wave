<script lang="ts">
  import { apiFetch } from "../api";
  import { editorContent } from "../../store/editorStore.svelte";
  let question = $state("");

  const handleSubmit = () => {
    if (question.trim().length === 0) return;
    apiFetch(`${import.meta.env}/ask`, {
      body: JSON.stringify({
        question: `question \n`,
        referenceDocument: documentId,
      }),
    });
  };

  function handleKeydown(e: any) {
    if (question.trim().length === 0) return;
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      e.target.form?.requestSubmit();
    }
  }

  let { documentId }: { documentId: string | undefined} = $props();
</script>

<div class="px-3">
  <div class="border-olive-400 rounded-lg border bg-white p-2">
    <form on:submit|preventDefault={handleSubmit}>
      <textarea
        on:keydown={handleKeydown}
        class="border-none resize-none w-full textarea focus:ring-0 focus:outline-0"
        placeholder="How can I help you?"
        bind:value={question}
      ></textarea>
    </form>
  </div>
</div>
