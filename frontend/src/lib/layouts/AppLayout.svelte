<script lang="ts">
  import { Collapsible } from "bits-ui";
  import SidebarRightIcon from "@iconify-svelte/reicon/sidebar-right";
  import SidebarLeftIcon from "@iconify-svelte/reicon/sidebar-left";
  import { userStore, logout } from "../../store/authStore.svelte";
  import SidebarTree from "../Components/SidebarTree.svelte";
  import Logout2DuotoneIcon from "@iconify-svelte/reicon/logout2-duotone";
  import TuningSquareDuotoneIcon from '@iconify-svelte/reicon/tuning-square-duotone';
  import {Avatar} from 'bits-ui'

  let { children }: { children: import("svelte").Snippet } = $props();

  let open = $state(true);

  const navItems = [
    { label: "Home", href: "#/" },
    { label: "Docs", href: "#/docs" },
    { label: "Categories", href: "#/categories" },
  ];

  const user = $derived($userStore);

</script>

<div class="flex h-screen w-full overflow-hidden bg-olive-100">
  <Collapsible.Root bind:open class="h-full">
    <aside
      class="flex h-full flex-col border-r border-base-300 bg-olive-100 transition-all duration-200 ease-in-out {open
        ? 'w-64'
        : 'w-16'}"
    >
      <div class="flex items-center justify-between bg-olive-100 gap-2 p-4">
        <span class="truncate text-lg font-bold {open ? '' : 'hidden'}"
          >🌊 Entangle</span
        >
        <Collapsible.Trigger
          class="btn btn-ghost btn-square btn-sm shrink-0"
          aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
        >
          {#if open}
            <SidebarLeftIcon class="size-5 transition-transform duration-200" />
          {:else}
            <SidebarRightIcon
              class="size-5 transition-transform duration-200"
            />
          {/if}
        </Collapsible.Trigger>
      </div>

      <Collapsible.Content class="min-h-0 flex-1 overflow-y-auto bg-olive-100">
        <nav class="flex flex-col gap-1 px-2 pb-4">
          <ul class="menu w-full p-0">
            {#each navItems as item (item.href)}
              <li>
                <a
                  href={item.href}
                  class={open ? "" : "justify-center"}
                  title={item.label}
                >
                  <span>{item.label}</span>
                </a>
              </li>
            {/each}
          </ul>

          <div class="divider my-2 {open ? '' : 'mx-1'}"></div>

          <div
            class="px-2 text-xs font-semibold uppercase tracking-wider text-base-content/50"
          >
            {open ? "Collections" : ""}
          </div>
          <ul class="menu w-full p-0">
            {#each ["Documents", "Projects", "Archive"] as item (item)}
              <li>
                <a href="#/" class={open ? "" : "justify-center"} title={item}>
                  <span class={open ? "" : "hidden"}>{item}</span>
                </a>
              </li>
            {/each}
          </ul>

          <div class="divider my-2 {open ? '' : 'mx-1'}"></div>

          <div
            class="px-2 text-xs font-semibold uppercase tracking-wider text-base-content/50"
          >
            {open ? "Categories" : ""}
          </div>
          <SidebarTree collapsed={!open} />
        </nav>
      </Collapsible.Content>

      <div class="mt-auto border-t border-base-300 bg-olive-200 p-2">
        <div
          class="flex items-center gap-2 rounded-box p-2 {open
            ? ''
            : 'justify-center'}"
        >
          <Avatar.Root
            delayMs={200}
            class="data-[status=loaded]:border-foreground bg-muted text-muted-foreground h-12 w-12 rounded-full border text-[17px] font-medium uppercase data-[status=loading]:border-transparent"
          >
            <div
              class="flex h-full w-full items-center justify-center overflow-hidden rounded-full border-2 border-transparent"
            >
              <Avatar.Image src={user?.avatar} alt={user?.name} />
              <Avatar.Fallback class="border-muted border uppercase">{user?.name[0]}</Avatar.Fallback>
            </div>
          </Avatar.Root>
          {#if open}
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-medium capitalize">
                {user?.name ?? "User"}
              </div>
              <div class="truncate text-xs text-base-content/60">
                {user?.email ?? ""}
              </div>
            </div>
              <a href="/#/settings" class="btn btn-ghost btn-square btn-sm shrink-0">
                <TuningSquareDuotoneIcon class="size-4" />
              </a>
            <button
              class="btn btn-ghost btn-square btn-sm shrink-0"
              title="Log out"
              onclick={logout}
            >
              <Logout2DuotoneIcon class="size-4" />
            </button>
          {/if}
        </div>
      </div>
    </aside>
  </Collapsible.Root>

  <main class="flex min-w-0 flex-1 flex-col overflow-hidden bg-white">
    <div class="flex-1 overflow-y-auto p-6">
      {@render children()}
    </div>
  </main>
</div>
