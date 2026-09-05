<script lang="ts">
  import { Label, ScrollArea } from "bits-ui";
  import { marked } from "marked";
  import {
    chatResponse,
    chatReferences,
    responseAvailable,
  } from "../../store/chatStore.svalte";

  let parsedMd = $derived(marked($chatResponse));
</script>

{#if $responseAvailable}
  <div class="mx-auto max-w-5xl">
    <div class="card w-9/10">
      <div class="px-6">
        <div class="bg-olive-100 px-4 py-6 rounded-xl">
          <div class="flex items-center gap-2 mb-4">
            <div class="h-12 w-12 bg-olive-300 p-1.5 rounded-full">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 500 500"
                width="100%"
                height="100%"
              >
                <!-- Headband / Arch -->
                <path
                  d="M 100 240 A 175 175 0 0 1 400 240"
                  fill="none"
                  stroke="#F1551A"
                  stroke-width="18"
                  stroke-linecap="round"
                />

                <!-- Top Antenna / Forehead (Light Purple) -->
                <rect
                  x="210"
                  y="60"
                  width="80"
                  height="90"
                  rx="20"
                  ry="20"
                  fill="#CDA2FF"
                />

                <!-- Left Ear Cup (Dark Purple) -->
                <rect
                  x="50"
                  y="235"
                  width="45"
                  height="120"
                  rx="20"
                  ry="20"
                  fill="#732DC2"
                />

                <!-- Right Ear Cup (Dark Purple) -->
                <rect
                  x="405"
                  y="235"
                  width="45"
                  height="120"
                  rx="20"
                  ry="20"
                  fill="#732DC2"
                />

                <!-- Outer Main Bot Head Body (Medium Purple) -->
                <rect
                  x="80"
                  y="115"
                  width="340"
                  height="340"
                  rx="120"
                  ry="120"
                  fill="#9B51E0"
                />

                <!-- Inner Light Gray Face Screen -->
                <rect
                  x="128"
                  y="150"
                  width="244"
                  height="235"
                  rx="80"
                  ry="80"
                  fill="#F2F2F5"
                />

                <!-- Eyes (Dark Purple) -->
                <circle cx="180" cy="260" r="23" fill="#732DC2" />
                <circle cx="320" cy="260" r="23" fill="#732DC2" />

                <!-- Smiling Mouth (Dark Purple) -->
                <path d="M 198 310 A 52 52 0 0 0 302 310 Z" fill="#732DC2" />

                <!-- Microphone Arm (Orange) -->
                <path
                  d="M 88 315 L 170 355 L 190 355"
                  fill="none"
                  stroke="#F1551A"
                  stroke-width="16"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
            <Label.Root class="label">Tilly</Label.Root>
          </div>
          <div class="mx-2 mb-2 prose">
            {@html parsedMd}
          </div>

          <ScrollArea.Root class="w-full">
            <ScrollArea.Viewport class="w-full max-w-full h-full">
              <div
                class="gap-4 p-2"
                style="display: flex; flex-direction: row; width: max-content;"
              >
                {#each $chatReferences as reference, index}
                  <!-- Card {index} -->
                  <div class="w-72 shrink-0 card card-border bg-white">
                    <div class="card-body">
                      <h2 class="montserrat-heading-bold text-base">
                        <a href={`/#/docs/${reference.id}`}>
                          {reference.title}
                        </a>
                      </h2>
                      <p class="montserrat-body truncate line-clamp-2">
                        {reference.description}
                      </p>
                      <div>
                        <a
                          class="btn btn-xs btn-ghost"
                          href={`/#/docs/${reference.id}`}>Visit</a
                        >
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            </ScrollArea.Viewport>

            <ScrollArea.Scrollbar
              orientation="horizontal"
              class="flex touch-none mt-2 select-none bg-base-200 max-w-9/10 h-2.5 p-0.5 mx-2"
            >
              <ScrollArea.Thumb class="bg-olive-300 rounded-full flex-1" />
            </ScrollArea.Scrollbar>
            <ScrollArea.Corner />
          </ScrollArea.Root>
        </div>
      </div>
    </div>
  </div>
{/if}
