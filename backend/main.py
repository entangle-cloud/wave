from fastapi import FastAPI, Depends 
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
import httpx
from dotenv import load_dotenv
import os
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from routers.auth import router as auth_router
from routers.posts import router as posts_router
from routers.categories import router as categories_router
from clients import viking_client

load_dotenv()

OPENVIKING_TOKEN=os.getenv("OPENVIKING_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENVIKING_MCP_URL = os.getenv("OPENVIKING_MCP_URL")

HEADERS = {
    "Authorization": f"Bearer {OPENVIKING_TOKEN}"
}




DB = Annotated[AsyncSession, Depends(get_db)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    http_client = httpx.AsyncClient(headers=HEADERS)
    await viking_client.client.initialize()
    async with (
        streamable_http_client(OPENVIKING_MCP_URL, http_client=http_client) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        app.state.ov_session = session
        yield

app = FastAPI(lifespan=lifespan)


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,       # allow cookies/auth headers
    allow_methods=["*"],          # or specify ["GET", "POST", ...]
    allow_headers=["*"],          # or specify specific headers
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
async def health():
    session: ClientSession = app.state.ov_session
    result = await session.call_tool("health")
    if (result.content[0].text == "OpenViking is healthy (service initialized, storage: VikingFS)"):
        return {"result": "all systems go :) W"}
    else:
        return {"result": "server is not healthy :( L"}

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(categories_router)


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

