# 🌊 Wave
<img width="6912" height="3456" alt="Wave (1)" src="https://github.com/user-attachments/assets/cfb2e529-bb5e-4675-ab32-d94568b43cc0" />

<p>
  <a title="Star the repository and support" href="https://github.com/entangle-cloud/wave"><img height="36" src="https://github.com/entangle-cloud/wave/raw/refs/heads/main/docs/star.svg" /></a>
  &nbsp;&nbsp;
  <a title="Join our discord server" href="https://discord.gg/gRwxBDrN7v"><img height="36" src="https://github.com/entangle-cloud/wave/raw/refs/heads/main/docs/discord.svg" /></a>
   &nbsp;&nbsp;
  <a title="Join our discord server" href="https://docs.entangle.ch"><img height="36" src="https://github.com/entangle-cloud/wave/raw/refs/heads/main/docs/docs.svg" /></a>
</p>

Cut through the clutter. A knowledge hub for humans and AI agents to find information when you need them. No scrolling through scattered folders, wikis, and documents.

**Always up-to date with agents and human moderation.**

## Features

- Beautiful distraction free Markdown editor with user collaboration
- Content categorization with sharing with users
- Agent memory with virtual file-system support
- Bring your own keys for LLM and S3 storage
- Self hosted and Entangle Cloud host support

## Screenshots

<img width="1393" height="995" alt="image" src="https://github.com/user-attachments/assets/6a698af7-a355-47df-9266-0929020c5221" />


## Environment Variables

To run this project, you will need to add the following environment variables to your `.env` file in the frontend and backend

### Frontend env variables 

Replace with Wave backend url

`VITE_API_ENDPOINT="http://localhost:3000`

### Backend env variables 

```bash
OPENVIKING_TOKEN="YOUR OPEN VIKIN TOKEN"
DATABASE_URL="POSTGRES DATABASE_URL"
OPENVIKING_MCP_URL="OPENVIKIN MCP ENDPOINT"
OPENVIKING_ENDPOINT="OPEN VIKING ENDPOINT"
JWT_SECRET="xxxxxx"
ACCESS_TOKEN_EXPIRE_MINUTES=60
R2_ACCESS_KEY="S3 BUCKET ACCESS KEY"
R2_ACCESS_SECRET="S3 BUCKET ACCESS SECRET"
R2_ENDPOINT="S3 ENDPOINT"
BUCKET_NAME="S3 BUCKET NAME"
GEMINI_API_KEY="GEMINI API KEY"
MODEL="models/gemini-3.8-flash"
```

## Roadmap

- [ ] Wave MCP API Endpoint for agent workflows
- [ ] Improving user interface
    
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
