<script lang="ts">
  import { onMount } from "svelte";
  import { z } from "zod";
  import { Avatar, Button, Label } from "bits-ui";
  import { userStore, updateProfile } from "../store/authStore.svelte";

  let name = $state("");
  let email = $state("");
  let avatar = $state("");
  let avatarFile = $state<File | null>(null);
  let error = $state(false);
  let loading = $state(false);
  let submitting = $state(false);
  let errors = $state<Partial<Record<"name" | "email" | "avatar", string>>>({});
  let errorMessage = $state("");

  const settingsSchema = z.object({
    name: z.string().trim().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Enter a valid email address"),
    avatar: z.custom<File>((val) => val instanceof File, "Invalid file").refine(
      (file) => !file || file.size <= 2 * 1024 * 1024,
      "Avatar must be less than 2MB"
    ).optional()
  });

  type Field = "name" | "email" | "avatar";

  const validateField = (field: Field, value?: unknown) => {
    const val = value ?? (field === "name" ? name : field === "email" ? email : avatarFile);
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

  onMount(() => {
    loading = true;
    const request = fetch(`${import.meta.env.VITE_API_ENDPOINT}/auth/me`, {
      method: "GET",
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        name = data.name;
        email = data.email;
        avatar = data.avatar;
      })
      .catch((e) => {
        error = true;
        errorMessage = "Error loading profile";
      })
      .finally(() => {
        loading = false;
      });
  });

  const handleSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    const result = settingsSchema.safeParse({ name, email, avatar: avatarFile });
    if (!result.success) {
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
      const success = await updateProfile(result.data.name, result.data.email, avatarFile);
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

<div class="mx-auto max-w-5xl">
  <div class="mt-8 space-y-4">
    <div class="card-body">
      <h2 class="font-semibold text-xl">Settings</h2>
      {#if error}
        <div class="alert my-4 alert-error alert-soft">
          {errorMessage}
        </div>
      {/if}
      <form
        onsubmit={handleSubmit}
        novalidate
        class="space-y-4 grid grid-cols-2"
      >
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
              >Your name displyed in the application</span
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
            <span class="fieldset-label">Your email address used to login</span>
            {#if errors.email}
              <span class="mt-1 text-xs text-error">{errors.email}</span>
            {/if}
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
                  class="btn btn-soft btn-sm"
                  onclick={() => document.getElementById("avatar")?.click()}
                  >Change avatar</Button.Root
                >
              </div>
            </div>
          </div>
        </div>
        <div>
          <Button.Root
            type="submit"
            class="btn btn-primary"
            disabled={submitting}
          >
            {#if submitting}
              <span class="loading loading-spinner loading-sm"></span>
              Saving...
            {:else}
              Save Changes
            {/if}
          </Button.Root>
        </div>
      </form>
    </div>
  </div>
</div>
