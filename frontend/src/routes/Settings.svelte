<script lang="ts">
  import { onMount } from "svelte";
  import { z } from "zod";
  import { Avatar, Button, Label } from "bits-ui";
  import { updateProfile } from "../store/authStore.svelte";
  import { Toaster, toast } from "svelte-sonner";
  import { apiFetch } from "../lib/api";
  import Setting2Icon from "@iconify-svelte/reicon/setting2";

  let name = $state("");
  let email = $state("");
  let avatar = $state("");
  let avatarFile = $state<File | null>(null);
  let error = $state(false);
  let password = $state("");
  let loading = $state(false);
  let submitting = $state(false);
  let errors = $state<
    Partial<Record<"name" | "email" | "avatar" | "password", string>>
  >({});
  let errorMessage = $state("");

  const settingsSchema = z.object({
    name: z.string().trim().min(2, "Name must be at least 2 characters"),
    email: z.email("Enter a valid email address"),
    password: z
      .string()
      .optional()
      .refine((val) => !val || val.length >= 10, {
        message: "Password must be at least 10 characters",
      })
      .refine((val) => !val || /[A-Z]/.test(val), {
        message: "Must include an uppercase letter",
      })
      .refine((val) => !val || /[0-9]/.test(val), {
        message: "Must include a number",
      }),
    avatar: z
      .custom<File>((val) => val instanceof File, "Invalid file")
      .refine(
        (file) => !file || file.size <= 2 * 1024 * 1024,
        "Avatar must be less than 2MB",
      )
      .nullable()
      .optional(),
  });

  type Field = "name" | "email" | "avatar" | "password";

  const validateField = (field: Field, value?: unknown) => {
    const val =
      value ??
      (field === "password"
        ? password
        : field === "name"
          ? name
          : field === "email"
            ? email
            : avatarFile);
    const result = settingsSchema.shape[field].safeParse(val);
    errors = {
      ...errors,
      [field]: result.success ? undefined : result.error.issues[0].message,
    };
  };

  const updateAvatar = (e: Event) => {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      avatarFile = file;
      validateField("avatar", file);
      const reader = new FileReader();
      reader.onload = () => {
        avatar = reader.result as string;
      };
      reader.readAsDataURL(file);
    }
  };

  const request = apiFetch(`${import.meta.env.VITE_API_ENDPOINT}/auth/me`)
    .then((res) => res.json())
    .then((data) => {
      name = data.name;
      email = data.email;
      avatar = data.avatar_url;
    })
    .catch((e) => {
      error = true;
      errorMessage = "Error loading profile";
    })
    .finally(() => {
      loading = false;
    });

  onMount(() => {
    loading = true;
    toast.promise(request, {
      success: "Settings loaded",
      loading: "Loading settings",
      error: errorMessage,
    });
  });

  const handleSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    const result = settingsSchema.safeParse({
      name,
      email,
      password,
      avatar: avatarFile,
    });
    if (!result.success) {
      console.log(result.error);
      const fieldErrors: typeof errors = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as Field;
        if (!fieldErrors[field]) fieldErrors[field] = issue.message;
      }
      errors = fieldErrors;
      return;
    }

    errors = {};
    submitting = true;
    try {
      const success = await updateProfile(
        result.data.name,
        result.data.email,
        result.data.password,
        avatarFile,
      );
      if (!success) {
        error = true;
      } else {
        avatarFile = null;
      }
    } finally {
      submitting = false;
    }
  };
</script>

<svelte:head>
  <title>Settings - 🌊 Wave</title>
</svelte:head>

<Toaster />

<div class="mx-auto max-w-5xl">
  <div class="mt-8 card card-border border-olive-200">
    <div class="card-body">
      <h2 class="card-title">Account Settings</h2>
      {#if error}
        <div class="alert my-4 alert-error alert-soft">
          {errorMessage}
        </div>
      {/if}
      <form onsubmit={handleSubmit} novalidate class="grid grid-cols-2">
        <div>
          <div class="fieldset grid gap-1">
            <Label.Root for="name" class="fieldset-legend">Name</Label.Root>
            <input
              id="name"
              name="name"
              autocomplete="off"
              bind:value={name}
              placeholder="Your name"
              class="input w-full {errors.name ? 'input-error' : ''}"
              onblur={() => validateField("name")}
              oninput={() => errors.name && validateField("name")}
              aria-invalid={!!errors.name}
            />
            <span class="fieldset-label"
              >The name displayed in the application</span
            >
            {#if errors.name}
              <span class="mt-1 text-xs text-error">{errors.name}</span>
            {/if}
          </div>

          <div class="fieldset grid gap-1">
            <Label.Root for="email" class="fieldset-legend"
              >Email Address</Label.Root
            >
            <input
              id="email"
              autocomplete="off"
              name="email"
              class="input w-full {errors.email ? 'input-error' : ''}"
              placeholder="me@example.com"
              bind:value={email}
              type="email"
              onblur={() => validateField("email")}
              oninput={() => errors.email && validateField("email")}
              aria-invalid={!!errors.email}
            />
            <span class="fieldset-label"
              >The email address you use to sign in</span
            >
            {#if errors.email}
              <span class="mt-1 text-xs text-error">{errors.email}</span>
            {/if}
          </div>
          <div class="fieldset grid gap-1">
            <Label.Root for="password" class="fieldset-legend">
              Change Password
            </Label.Root>
            <input
              id="password"
              autocomplete="off"
              type="password"
              name="password"
              class="input w-full {errors.password ? 'input-error' : ''}"
              placeholder="Your new password"
              bind:value={password}
              onblur={() => validateField("password")}
              oninput={() => errors.password && validateField("password")}
              aria-invalid={!!errors.password}
            />
            {#if errors.password}
              <span class="mt-1 text-xs text-error">{errors.password}</span>
            {/if}
            <span class="fieldset-label">Change your login password</span>
          </div>
        </div>

        <div>
          <div class="form-field flex items-center mx-32">
            <div class="fieldset">
              <Label.Root for="avatar" class="fieldset-legend"
                >Avatar</Label.Root
              >
              <input
                type="file"
                name="avatar"
                class="hidden"
                id="avatar"
                accept="image/*"
                onchange={updateAvatar}
              />
              <div class="flex gap-2 items-center">
                <Avatar.Root
                  delayMs={200}
                  class="data-[status=loaded]:border-foreground bg-olive-200 bg-muted text-muted-foreground h-12 w-12 rounded-full border text-[17px] font-medium uppercase data-[status=loading]:border-transparent"
                >
                  <div
                    class="flex h-full w-full items-center justify-center overflow-hidden rounded-full border-2 border-transparent"
                  >
                    <Avatar.Image src={avatar} alt={name} />
                    <Avatar.Fallback
                      >{name.length > 0
                        ? name[0].toUpperCase()
                        : "A"}</Avatar.Fallback
                    >
                  </div>
                </Avatar.Root>
                <Button.Root
                  class="btn btn-soft btn-sm rounded-md"
                  onclick={() => document.getElementById("avatar")?.click()}
                  >Change avatar</Button.Root
                >
              </div>
            </div>
          </div>
        </div>
        <div class="mt-2 card-actions">
          <Button.Root
            type="submit"
            class="btn rounded-md btn-neutral btn-sm"
            disabled={submitting}
          >
            {#if submitting}
              <span class="loading loading-spinner loading-sm"></span>
              Saving...
            {:else}
              Update Profile
            {/if}
          </Button.Root>
        </div>
      </form>
    </div>
  </div>

  <div class="card card-border border-olive-200 mt-8 bg-white">
    <div class="card-body">
      <h2 class="card-title">Categories</h2>

      <a class="underline flex items-center gap-2" href="/#/categories/">
        <Setting2Icon class="size-4 shrink-0" />
        <span>Manage Categories and Access</span>
      </a>
    </div>
  </div>
</div>
