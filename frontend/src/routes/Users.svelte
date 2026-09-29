<script lang="ts">
  import { onMount } from "svelte";
  import { Avatar, Button, Dialog } from "bits-ui";
  import { Toaster, toast } from "svelte-sonner";
  import { apiFetch } from "../lib/api";
  import { userStore, type UserRole } from "../store/authStore.svelte";
  import UserIcon from "@iconify-svelte/reicon/user-duotone";
  import SearchIcon from "@iconify-svelte/reicon/search";
  import CheckIcon from "@iconify-svelte/reicon/check";
  import ChevronDownIcon from "@iconify-svelte/reicon/chevron-down";
  import ChevronUpIcon from "@iconify-svelte/reicon/chevron-up";
  import { Select } from "bits-ui";

  type ManagedUser = {
    id: number;
    email: string;
    name: string;
    avatar_url: string | null;
    role: UserRole;
    is_active: boolean;
    created_at: string;
  };

  const ROLES: UserRole[] = ["admin", "editor", "viewer"];

  let users = $state<ManagedUser[]>([]);
  let loading = $state(true);
  let loadError = $state("");
  let search = $state("");
  let roleFilter = $state<"all" | UserRole>("all");

  let deleteTarget = $state<ManagedUser | null>(null);
  let deleteDialogOpen = $state(false);
  let deleting = $state(false);

  let pendingRole = $state<Record<number, boolean>>({});
  let pendingStatus = $state<Record<number, boolean>>({});

  const currentUser = $derived($userStore);

  const filtered = $derived.by(() => {
    const q = search.trim().toLowerCase();
    return users.filter((u) => {
      if (roleFilter !== "all" && u.role !== roleFilter) return false;
      if (!q) return true;
      return (
        u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
      );
    });
  });

  const counts = $derived.by(() => ({
    total: users.length,
    admins: users.filter((u) => u.role === "admin").length,
    editors: users.filter((u) => u.role === "editor").length,
    viewers: users.filter((u) => u.role === "viewer").length,
  }));

  const userRoles: Array<{ label: string; value: string; disabled: boolean }> =
    [
      {
        value: "admin",
        label: "ADMIN",
        disabled: false,
      },
      {
        value: "viewer",
        label: "VIEWER",
        disabled: false,
      },
      {
        value: "editor",
        label: "EDITOR",
        disabled: false,
      },
    ];

  const roleBadgeClass = (role: UserRole) =>
    role === "admin"
      ? "badge-error"
      : role === "editor"
        ? "badge-info"
        : "badge-ghost";

  const loadUsers = async () => {
    loading = true;
    loadError = "";
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_ENDPOINT}/users`);
      if (res.status === 403) {
        loadError = "You need an admin account to manage users.";
        return;
      }
      if (!res.ok) throw new Error(`Load failed: ${res.status}`);
      users = await res.json();
    } catch (e) {
      loadError = e instanceof Error ? e.message : "Failed to load users";
    } finally {
      loading = false;
    }
  };

  onMount(() => {
    toast.promise(loadUsers(), {
      loading: "Loading users",
      success: "Users loaded",
      error: "Failed to load users",
    });
  });

  const changeRole = async (target: ManagedUser, nextRole: UserRole) => {
    if (target.role === nextRole || pendingRole[target.id]) return;
    if (target.id === currentUser?.id) {
      toast.error("You cannot change your own role");
      return;
    }
    const previous = target.role;
    pendingRole = { ...pendingRole, [target.id]: true };
    // Optimistic update with rollback on failure
    users = users.map((u) =>
      u.id === target.id ? { ...u, role: nextRole } : u,
    );
    try {
      const res = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/users/${target.id}`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ role: nextRole }),
        },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Update failed: ${res.status}`);
      }
      const updated: ManagedUser = await res.json();
      users = users.map((u) => (u.id === target.id ? updated : u));
      toast.success(`${updated.name} is now ${updated.role}`);
    } catch (e) {
      users = users.map((u) =>
        u.id === target.id ? { ...u, role: previous } : u,
      );
      toast.error(e instanceof Error ? e.message : "Failed to update role");
    } finally {
      pendingRole = { ...pendingRole, [target.id]: false };
    }
  };

  const toggleActive = async (target: ManagedUser) => {
    if (pendingStatus[target.id]) return;
    if (target.id === currentUser?.id) {
      toast.error("You cannot deactivate your own account");
      return;
    }
    pendingStatus = { ...pendingStatus, [target.id]: true };
    const next = !target.is_active;
    try {
      const res = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/users/${target.id}`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ is_active: next }),
        },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Update failed: ${res.status}`);
      }
      const updated: ManagedUser = await res.json();
      users = users.map((u) => (u.id === target.id ? updated : u));
      toast.success(
        updated.is_active
          ? `${updated.name} reactivated`
          : `${updated.name} deactivated`,
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to update user");
    } finally {
      pendingStatus = { ...pendingStatus, [target.id]: false };
    }
  };

  const openDelete = (target: ManagedUser) => {
    deleteTarget = target;
    deleteDialogOpen = true;
  };

  const confirmDelete = async () => {
    if (!deleteTarget || deleting) return;
    if (deleteTarget.id === currentUser?.id) {
      toast.error("You cannot delete your own account");
      return;
    }
    deleting = true;
    try {
      const res = await apiFetch(
        `${import.meta.env.VITE_API_ENDPOINT}/users/${deleteTarget.id}`,
        { method: "DELETE" },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Delete failed: ${res.status}`);
      }
      users = users.filter((u) => u.id !== deleteTarget!.id);
      toast.success(`${deleteTarget.name} deleted`);
      deleteDialogOpen = false;
      deleteTarget = null;
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to delete user");
    } finally {
      deleting = false;
    }
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return iso;
    }
  };
</script>

<svelte:head>
  <title>User Management - 🌊 Wave</title>
</svelte:head>

<Toaster />

<div
  class="flex h-full flex-col overflow-hidden rounded-xl bg-white ring ring-base-300"
>
  <div class="navbar shrink-0 border-b border-base-200 px-4 shadow-sm">
    <div class="flex-1">
      <h1 class="text-lg font-bold">Users</h1>
      <span class="badge badge-ghost ml-2">
        {counts.total} total · {counts.admins} admin · {counts.editors} editor ·
        {counts.viewers} viewer
      </span>
    </div>
    <div class="flex-none">
      <Button.Root
        class="btn btn-ghost btn-sm"
        onclick={() => loadUsers()}
        disabled={loading}
      >
        {#if loading}
          <span class="loading loading-spinner loading-sm"></span>
          Loading...
        {:else}
          Refresh
        {/if}
      </Button.Root>
    </div>
  </div>

  <div class="flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
    <label
      class="input border border-olive-500 rounded-lg flex w-full items-center gap-2 sm:max-w-sm"
    >
      <SearchIcon class="size-4" />
      <input
        type="search"
        class="input grow focus:outline-0 focus:ring-0"
        placeholder="Search by name or email"
        bind:value={search}
      />
    </label>
    <Select.Root type="single" items={userRoles} allowDeselect={true}>
      <Select.Trigger
        class="inline-flex h-10 w-80 touch-none select-none items-center rounded-lg border border-olive-500 bg-white px-3 text-sm text-gray-900 transition-colors data-placeholder:text-olive-500/50 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
        aria-label="Select a theme"
      >
        <UserIcon class="text-muted-foreground mr-2.5 size-6" />
        <Select.Value placeholder="Select a theme" />
        <ChevronDownIcon class="text-muted-foreground ml-auto size-6" />
      </Select.Trigger>
      <Select.Portal>
        <Select.Content
          class="outline-none z-50 max-h-64 w-(--bits-select-anchor-width) min-w-(--bits-select-anchor-width) select-none rounded-xl border border-gray-200 bg-white shadow-lg px-1 py-2 dark:border-gray-700 dark:bg-gray-950 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2"
          sideOffset={10}
        >
          <Select.ScrollUpButton
            class="flex w-full items-center justify-center"
          >
            <ChevronUpIcon class="size-3" />
          </Select.ScrollUpButton>
          <Select.Viewport class="p-1 bg-white">
            {#each userRoles as role, i (i + role.value)}
              <Select.Item
                class="rounded-md data-highlighted:bg-gray-100 dark:data-highlighted:bg-gray-800 outline-none data-disabled:opacity-50 flex h-8 w-full cursor-pointer select-none items-center py-2 pl-3 pr-1.5 text-xs capitalize"
                value={role.value}
                label={role.label}
                disabled={role.disabled}
              >
                {#snippet children({ selected })}
                  {role.label}
                  {#if selected}
                    <div class="ml-auto">
                      <CheckIcon aria-label="check" />
                    </div>
                  {/if}
                {/snippet}
              </Select.Item>
            {/each}
          </Select.Viewport>
          <Select.ScrollDownButton
            class="flex w-full items-center justify-center"
          >
            <ChevronDownIcon class="size-3" />
          </Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  </div>

  <div class="min-h-0 flex-1 overflow-y-auto px-4 pb-6">
    {#if loadError}
      <div role="alert" class="alert alert-error mb-4">
        <span>{loadError}</span>
      </div>
    {/if}

    {#if loading}
      <div class="flex flex-col gap-2">
        {#each Array(5) as _, i (i)}
          <div class="skeleton h-16 w-full"></div>
        {/each}
      </div>
    {:else if filtered.length === 0}
      <div
        class="flex h-48 flex-col items-center justify-center gap-2 text-base-content/60"
      >
        <p class="font-medium">No users found</p>
        <p class="text-sm">
          {#if users.length === 0}
            No users exist yet.
          {:else}
            Try a different search or role filter.
          {/if}
        </p>
      </div>
    {:else}
      <div class="overflow-x-auto rounded-box border border-base-200">
        <table class="table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th class="hidden md:table-cell">Joined</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filtered as u (u.id)}
              {@const isSelf = u.id === currentUser?.id}
              <tr class={!u.is_active ? "opacity-70" : ""}>
                <td>
                  <div class="flex items-center gap-3">
                    <Avatar.Root
                      delayMs={200}
                      class="bg-muted text-muted-foreground h-10 w-10 rounded-full border text-sm font-medium uppercase"
                    >
                      <div
                        class="flex h-full w-full items-center justify-center overflow-hidden rounded-full"
                      >
                        <Avatar.Image src={u.avatar_url} alt={u.name} />
                        <Avatar.Fallback>
                          {u.name ? u.name[0].toUpperCase() : "?"}
                        </Avatar.Fallback>
                      </div>
                    </Avatar.Root>
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="truncate font-bold">{u.name}</span>
                        {#if isSelf}
                          <span class="badge badge-sm badge-neutral">you</span>
                        {/if}
                      </div>
                      <div class="truncate text-sm text-base-content/60">
                        {u.email}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="flex items-center gap-2">
                  {#if isSelf}
                    <span
                      class="badge badge-sm {roleBadgeClass(u.role)} uppercase"
                    >
                      {u.role}
                    </span>
                    {/if}
                    {#if !isSelf}
                      <Select.Root
                        type="single"
                        items={userRoles}
                        value={u.role}
                        disabled={pendingRole[u.id]}
                        onValueChange={(v) => changeRole(u, v as UserRole)}
                      >
                        <Select.Trigger
                          class="inline-flex h-7 w-28 items-center rounded-md border border-olive-500 bg-white px-2 text-xs text-gray-900 data-placeholder:text-olive-500/50 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100 disabled:opacity-50"
                          aria-label="Change role for {u.name}"
                        >
                          <Select.Value placeholder="Select role" />
                          <ChevronDownIcon
                            class="text-muted-foreground ml-auto size-3.5"
                          />
                        </Select.Trigger>
                        <Select.Portal>
                          <Select.Content
                            class="outline-none z-50 max-h-64 w-(--bits-select-anchor-width) min-w-(--bits-select-anchor-width) select-none rounded-xl border border-gray-200 bg-white shadow-lg px-1 py-2 dark:border-gray-700 dark:bg-gray-950 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2"
                            sideOffset={6}
                          >
                            <Select.ScrollUpButton
                              class="flex w-full items-center justify-center"
                            >
                              <ChevronUpIcon class="size-3" />
                            </Select.ScrollUpButton>
                            <Select.Viewport class="p-1 bg-white">
                              {#each userRoles as role, i (i + role.value)}
                                <Select.Item
                                  class="rounded-md data-highlighted:bg-gray-100 dark:data-highlighted:bg-gray-800 outline-none data-disabled:opacity-50 flex h-8 w-full cursor-pointer select-none items-center py-2 pl-3 pr-1.5 text-xs capitalize"
                                  value={role.value}
                                  label={role.label}
                                >
                                  {#snippet children({ selected })}
                                    {role.label}
                                    {#if selected}
                                      <div class="ml-auto">
                                        <CheckIcon
                                          aria-label="check"
                                          class="size-3.5"
                                        />
                                      </div>
                                    {/if}
                                  {/snippet}
                                </Select.Item>
                              {/each}
                            </Select.Viewport>
                            <Select.ScrollDownButton
                              class="flex w-full items-center justify-center"
                            >
                              <ChevronDownIcon class="size-3" />
                            </Select.ScrollDownButton>
                          </Select.Content>
                        </Select.Portal>
                      </Select.Root>
                    {/if}
                  </div>
                </td>
                <td>
                  {#if u.is_active}
                    <span class="badge badge-sm badge-success">active</span>
                  {:else}
                    <span class="badge badge-sm badge-warning">inactive</span>
                  {/if}
                </td>
                <td
                  class="hidden whitespace-nowrap text-sm text-base-content/60 md:table-cell"
                >
                  {formatDate(u.created_at)}
                </td>
                <td>
                  <div class="flex justify-end gap-1">
                    {#if !isSelf}
                      <Button.Root
                        class="btn btn-ghost btn-xs"
                        disabled={pendingStatus[u.id]}
                        onclick={() => toggleActive(u)}
                        title={u.is_active
                          ? "Deactivate user"
                          : "Reactivate user"}
                      >
                        {#if pendingStatus[u.id]}
                          <span class="loading loading-spinner loading-xs"
                          ></span>
                        {:else}
                          {u.is_active ? "Deactivate" : "Activate"}
                        {/if}
                      </Button.Root>
                      <Button.Root
                        class="btn btn-ghost btn-xs text-error"
                        onclick={() => openDelete(u)}
                      >
                        Delete
                      </Button.Root>
                    {:else}
                      <span class="text-xs text-base-content/40">—</span>
                    {/if}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

<Dialog.Root bind:open={deleteDialogOpen}>
  <Dialog.Portal>
    <Dialog.Overlay class="fixed inset-0 z-40 bg-black/40" />
    <Dialog.Content
      class="fixed top-1/2 left-1/2 z-50 w-md max-w-[90vw] -translate-x-1/2 -translate-y-1/2 rounded-box bg-base-100 p-6 shadow-xl"
    >
      <Dialog.Title class="text-lg font-bold">Delete user?</Dialog.Title>
      <Dialog.Description class="mt-2 text-sm text-base-content/70">
        {#if deleteTarget}
          This will permanently delete
          <span class="font-semibold"
            >{deleteTarget.name} ({deleteTarget.email})</span
          >. This action cannot be undone.
        {/if}
      </Dialog.Description>
      <div class="mt-6 flex justify-end gap-2">
        <Dialog.Close class="btn btn-ghost" disabled={deleting}>
          Cancel
        </Dialog.Close>
        <Button.Root
          class="btn btn-error"
          disabled={deleting}
          onclick={confirmDelete}
        >
          {#if deleting}
            <span class="loading loading-spinner loading-sm"></span>
            Deleting...
          {:else}
            Delete user
          {/if}
        </Button.Root>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
