<script lang="ts">
  import { z } from "zod";
  import { Button, Label } from "bits-ui";
  import { signup } from "../store/authStore.svelte";

  let name = $state("");
  let email = $state("");
  let password = $state("");
  let submitting = $state(false);
  let errors = $state<Partial<Record<"name" | "email" | "password", string>>>(
    {},
  );

  const signupSchema = z.object({
    name: z.string().trim().min(2, "Name must be at least 2 characters"),
    email: z.email("Enter a valid email address"),
    password: z
      .string()
      .min(10, "Password must be at least 10 characters")
      .regex(/[A-Z]/, "Must include an uppercase letter")
      .regex(/[0-9]/, "Must include a number"),
  });

  type Field = keyof typeof signupSchema.shape;

  const validateField = (field: Field) => {
    const result = signupSchema.shape[field].safeParse(
      field === "name" ? name : field === "email" ? email : password,
    );
    errors = {
      ...errors,
      [field]: result.success ? undefined : result.error.issues[0].message,
    };
  };

  const handleSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    const result = signupSchema.safeParse({ name, email, password });
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
      const request = await signup(
        result.data.email,
        result.data.name,
        result.data.password,
      );
      if (request) {
        location.hash = "#/";
      } else {
        console.log(request);
      }
    } finally {
      submitting = false;
    }
  };
</script>

<svelte:head>
  <title>Signup - 🌊 Wave</title>
</svelte:head>

<h2 class="card-title mb-4 justify-center">Create account</h2>

<form onsubmit={handleSubmit} novalidate class="flex flex-col gap-3">
  <div class="form-control w-full">
    <Label.Root for="signup-name" class="label-text mb-1">Name</Label.Root>
    <input
      id="signup-name"
      type="text"
      class="input input-bordered w-full {errors.name ? 'input-error' : ''}"
      placeholder="Jane Doe"
      bind:value={name}
      onblur={() => validateField("name")}
      oninput={() => errors.name && validateField("name")}
      aria-invalid={!!errors.name}
    />
    {#if errors.name}
      <span class="mt-1 text-xs text-error">{errors.name}</span>
    {/if}
  </div>

  <div class="form-control w-full">
    <Label.Root for="signup-email" class="label-text mb-1">Email</Label.Root>
    <input
      id="signup-email"
      type="email"
      class="input input-bordered w-full {errors.email ? 'input-error' : ''}"
      placeholder="you@example.com"
      bind:value={email}
      onblur={() => validateField("email")}
      oninput={() => errors.email && validateField("email")}
      aria-invalid={!!errors.email}
    />
    {#if errors.email}
      <span class="mt-1 text-xs text-error">{errors.email}</span>
    {/if}
  </div>

  <div class="form-control w-full">
    <Label.Root for="signup-password" class="label-text mb-1">
      Password
    </Label.Root>
    <input
      id="signup-password"
      type="password"
      class="input input-bordered w-full {errors.password ? 'input-error' : ''}"
      placeholder="••••••••"
      bind:value={password}
      onblur={() => validateField("password")}
      oninput={() => errors.password && validateField("password")}
      aria-invalid={!!errors.password}
      aria-describedby={errors.password ? "signup-password-hint" : undefined}
    />
    {#if errors.password}
      <span id="signup-password-hint" class="mt-1 text-xs text-error">
        {errors.password}
      </span>
    {:else}
      <span id="signup-password-hint" class="mt-1 text-xs text-base-content/50">
        Min. 8 characters, one uppercase letter and one number
      </span>
    {/if}
  </div>

  <Button.Root type="submit" class="btn btn-primary mt-2" disabled={submitting}>
    {#if submitting}
      <span class="loading loading-spinner loading-sm"></span>
      Creating account...
    {:else}
      Sign up
    {/if}
  </Button.Root>
</form>

<p class="mt-4 text-center text-sm text-base-content/60">
  Already have an account?
  <a href="#/login" class="link link-primary">Log in</a>
</p>
