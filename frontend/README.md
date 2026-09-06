# AI Docs Frontend

A modern, AI-powered documentation editor built with **Svelte 5**, **TypeScript**, and **Vite**. Features a WYSIWYG Markdown editor (Milkdown/ProseMirror), real-time chat assistance, category management.

## Tech Stack

- **Framework**: Svelte 5, TypeScript, Vite
- **Styling**: Tailwind CSS 4, DaisyUI 5
- **Editor**: Milkdown (Crepe), ProseMirror
- **Routing**: svelte-spa-router
- **State**: Svelte 5 runes
- **Auth**: JWT (access/refresh tokens), HttpOnly cookies
- **Validation**: Zod 4

## Quick Start

```bash
# Install dependencies
bun install

# Development server
bun run dev

# Build for production
bun run build

# Type checking
bun run check
```

Create `.env` with:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## Project Structure

```
src/
├── routes.ts          # Route definitions with auth guards
├── guard.ts           # Route protection utilities
├── lib/
│   ├── api.ts         # Axios client + endpoints
│   ├── Components/    # Reusable UI components
│   ├── layouts/       # AppLayout, AuthLayout
│   └── store/         # Svelte 5 runes-based stores
└── routes/            # Page components
```

## Features

- **Rich Editor**: Milkdown with Nord theme, collaborative editing
- **AI Assistant**: Context-aware chat with streaming responses
- **Categories**: Hierarchical document organization
- **Auth**: Secure JWT flow with auto-refresh
- **Responsive**: Mobile-friendly DaisyUI components

## Scripts

| Command | Description |
|---------|-------------|
| `bun run dev` | Start dev server |
| `bun run build` | Production build |
| `bun run check` | Type check (svelte-check + tsc) |
| `bun run preview` | Preview production build |

## Contributing

1. Run `bun run check` before committing
2. Follow existing code style
3. Components in `lib/Components/` (PascalCase)
4. Stores in `lib/store/` (camelCaseStore.svelte.ts)
5. Pages in `routes/` (PascalCase)