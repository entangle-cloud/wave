<script lang="ts">
  /**
   * Layout for unauthenticated routes (login/signup).
   * Renders a centered card on a full-height background with app branding.
   */
  let { children }: { children: import("svelte").Snippet } = $props();
  import ArrowLeftSquareFilled from "@iconify-svelte/reicon/arrow-left-square-filled";
</script>

<div class="min-h-screen bg-gray-100 flex flex-col justify-center sm:py-12">
  <div class="p-10 xs:p-0 mx-auto md:w-full md:max-w-lg">
    <div class="flex items-end gap-2 justify-center mb-4">
      <img src="/wave.png" alt="wave" class="h-24" />
      <h1 class="font-thin text-center text-2xl mb-5">Wave by Entangle</h1>
    </div>
    <div
      class="bg-white card shadow w-full rounded-lg divide-y divide-gray-200"
    >
      <div class="card-body">
        {@render children()}
      </div>
    </div>
    <div class="py-5">
      <div class="grid grid-cols-2 gap-1">
        <div class="text-center sm:text-left whitespace-nowrap">
          <button
            class="transition btn btn-ghost duration-200 text-gray-600 font-normal text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-opacity-50 ring-inset"
          >
            <ArrowLeftSquareFilled height="1.25em" />
            Back to App
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
