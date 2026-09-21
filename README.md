# 🌊 Wave by Entangle - Knowledge base for agents and humans

<img width="256" height="256" alt="wave" src="https://github.com/user-attachments/assets/330dde7b-12c0-428e-bdb2-772726b3a6d3" />

![GitHub License](https://img.shields.io/github/license/entangle-cloud/wave)
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/entangle-cloud/wave)
![X (formerly Twitter) URL](https://img.shields.io/twitter/url?url=https%3A%2F%2Fx.com%2Fentangle-cloud)

Wave by Entangle is an AI powered knowledge base built for AI agents and humans. 

Replacing traditional company knowledge base with modern agent driven knowledge base with information available to you when you need them.

## Architecture 

```mermaid
flowchart TD
    A[Frontend] --> B(API - Fast API)
    B -->|Metadata| D[Postgres Database]
    B -->|Agent Memory| C[OpenViking]
    B -->|Agent Workflow| E[Your LLM]
    E --> C
    B -->|Media Storage| G[S3 Storage]
    D --> G 
```

### Frontend 

Milkdown based markdown / WSIWYG editor. UI designed with Tailwind CSS.

### Back-end

Fast API based python back-end.
