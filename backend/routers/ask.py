import os
import re
from fastapi import APIRouter, Depends, status, Request, HTTPException
from typing import Annotated
from schemas import Question, SearchResponse, LLMResponseSchema, EditProposal, SectionIn
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from database.user import User
from routers.auth import get_current_user
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pathlib import Path
from functools import lru_cache
from database import Post
from sqlalchemy import select
from schemas import PostResponse
from clients.s3_client import s3_client
from urllib.parse import urlparse, unquote
import httpx2
import yaml

router = APIRouter(prefix="/ask", tags=["ask"])

DB = Annotated[AsyncSession, Depends(get_db)]

JWT_SECRET = os.getenv("JWT_SECRET")
MODEL = os.getenv("MODEL")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

CurrentUser = Annotated[User, Depends(get_current_user)]

DEFAULT_TOOLS = {"google_search"}
READ_ONLY_TOOLS = {"find", "search", "read", "list", "tree", "grep", "glob", "health"}
EDIT_DECL = types.FunctionDeclaration(
    name="edit_section",
    description=(
        "Replace the full markdown of one section of the open document. "
        "Use ONLY when the user asks to change, write or insert content. "
        "For questions, answer in text instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "section_id": {
                "type": "string",
                "description": "ID from the document outline",
            },
            "new_markdown": {
                "type": "string",
                "description": "Full replacement markdown for the section, including its heading",
            },
        },
        "required": ["section_id", "new_markdown"],
    },
)

MAX_TOOL_ROUNDS = 20
SYSTEM_PROMPT_PATH = Path(
    os.environ.get(
        "KB_SYSTEM_PROMPT_PATH",
        Path(__file__).resolve().parents[1] / "prompts" / "kb-agent-prompt.md",
    )
)


def parse_and_validate_yaml(raw_response: str) -> LLMResponseSchema:
    """Extracts YAML from an LLM response, parses it, and validates against Pydantic schema."""
    # Remove markdown code block fences if present
    pattern = r"```(?:yaml)?\n(.*?)```"
    match = re.search(pattern, raw_response, re.DOTALL)
    yaml_text = match.group(1) if match else raw_response.strip()

    # Parse raw YAML to a Python dict
    raw_dict = yaml.safe_load(yaml_text)

    # Handle cases where YAML is empty or returns non-dict
    if not isinstance(raw_dict, dict):
        raise TypeError("YAML content did not parse into a valid dictionary.")

    # Validate dictionary against Pydantic model
    return LLMResponseSchema.model_validate(raw_dict)


def mcp_tools_to_gemini_tool(mcp_tools, allow_edit: bool = False) -> types.Tool:
    """Convert MCP tools to a single Gemini Tool.

    Only the read-only allow-list is taken from MCP, which is what enforces the
    'never call the mutating tools' rule at the API level. `edit_section` is a
    local tool: the agent loop handles it and it is never sent to MCP. It is
    added only when a document is open in the editor.
    """
    declarations = [
        types.FunctionDeclaration(
            name=tool.name,
            description=tool.description or "",
            parameters=sanitize_schema(
                tool.inputSchema or {"type": "object", "properties": {}}
            ),
        )
        for tool in mcp_tools
        if tool.name in READ_ONLY_TOOLS
    ]
    if allow_edit:
        declarations.append(EDIT_DECL)
    return types.Tool(function_declarations=declarations)


def sanitize_schema(schema: dict) -> dict:
    """Strip JSON-Schema keywords that MCP servers include but Gemini's
    FunctionDeclaration schema doesn't accept (e.g. $schema, additionalProperties, title)."""
    if not isinstance(schema, dict):
        return schema
    drop = {"$schema", "additionalProperties", "title"}
    cleaned = {k: v for k, v in schema.items() if k not in drop}
    if "properties" in cleaned and isinstance(cleaned["properties"], dict):
        cleaned["properties"] = {
            name: sanitize_schema(sub) for name, sub in cleaned["properties"].items()
        }
    if "items" in cleaned:
        cleaned["items"] = sanitize_schema(cleaned["items"])
    return cleaned


async def call_mcp_tool(session: ClientSession, name: str, args: dict) -> str:
    if name not in READ_ONLY_TOOLS:
        # Belt-and-braces: refuse even if the model somehow requests a tool
        # that wasn't in its declared tool list.
        return f"Error: '{name}' is not permitted for this read-only agent."
    result = await session.call_tool(name=name, arguments=args)
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(
            text if text is not None else f"[non-text content: {type(block).__name__}]"
        )
    return "\n".join(parts) if parts else "(empty result)"


async def ask(
    question: str,
    db: AsyncSession,
    referenceDocument=None,
    sections: list[SectionIn] | None = None,
    base_version: int | None = None,
) -> SearchResponse:

    # --- Build the prompt -------------------------------------------------
    referenceDocument_ov_link = None
    if referenceDocument is not None:
        referenceDocument_post = await db.get(Post, referenceDocument)
        if referenceDocument_post is not None:
            referenceDocument_ov_link = referenceDocument_post.content_ref

    if referenceDocument_ov_link is not None:
        prompt_text = (
            f"Reference document (use as primary source): {referenceDocument_ov_link}\n\n"
            f"Question: {question}"
        )
    else:
        prompt_text = question

    # Editing is only offered when a document is open in the editor
    allow_edit = bool(sections)
    valid_section_ids = {s.id for s in sections} if sections else set()

    if sections:
        doc = "\n\n".join(
            f'<section id="{s.id}">\n{s.markdown}\n</section>' for s in sections
        )
        prompt_text += (
            "\n\nOpen document (edit it with edit_section, using these section ids):\n"
            f"{doc}"
        )

    gemini = genai.Client()
    system_prompt = get_system_prompt()

    mcp_url = os.environ["OPENVIKING_MCP_URL"]
    mcp_token = os.environ["OPENVIKING_TOKEN"]
    headers = {"Authorization": f"Bearer {mcp_token}"}

    async with (
        httpx2.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=httpx2.Timeout(30.0, read=300.0),
        ) as http_client,
        streamable_http_client(
            mcp_url,
            http_client=http_client,
        ) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        mcp_tools = (await session.list_tools()).tools
        gemini_tool = mcp_tools_to_gemini_tool(mcp_tools, allow_edit=allow_edit)
        print(
            "allow_edit:",
            allow_edit,
            "| tools:",
            [d.name for d in gemini_tool.function_declarations],
            "| prompt has edit section:",
            "edit_section" in system_prompt,
        )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[gemini_tool],
        )

        # Async client so the event loop isn't blocked
        chat = gemini.aio.chats.create(model=MODEL, config=config)
        response = await chat.send_message(prompt_text)

        # --- Agentic loop: resolve tool calls until Gemini returns plain text
        edits: list[EditProposal] = []  # outside the loop so edits accumulate

        for _ in range(MAX_TOOL_ROUNDS):
            if not response.function_calls:
                break

            response_parts = []
            for fc in response.function_calls:
                args = dict(fc.args or {})

                if fc.name == "edit_section":
                    # Local tool: proposed here, applied by the client
                    if args.get("section_id") not in valid_section_ids:
                        result = (
                            "Error: unknown section_id. Use an ID from the outline."
                        )
                    elif not args.get("new_markdown"):
                        result = "Error: new_markdown is required."
                    else:
                        edits.append(
                            EditProposal(
                                section_id=args["section_id"],
                                markdown=args["new_markdown"],
                                base_version=base_version,
                            )
                        )
                        result = (
                            "Edit queued and will be applied to the document. "
                            "Do not repeat it."
                        )
                else:
                    result = await call_mcp_tool(session, fc.name, args)

                response_parts.append(
                    types.Part.from_function_response(
                        name=fc.name, response={"result": result}
                    )
                )

            response = await chat.send_message(response_parts)
        else:
            # range() exhausted without ever breaking: still calling tools
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Assistant did not reach a final answer within the tool-call budget.",
            )

        if response.text is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Model returned no text content.",
            )

        # --- Resolve references -------------------------------------------
        reference_meta: list[PostResponse] = []
        validated_data: LLMResponseSchema = parse_and_validate_yaml(response.text)

        for ref in validated_data.references:
            stmt = select(Post).where(Post.content_ref == ref.url)
            db_result = await db.execute(stmt)
            post = db_result.scalar_one_or_none()
            if post is None:
                continue  # reference doesn't match a known post

            user_info = await db.get(User, post.author_id) if post.author_id else None
            if user_info is None:
                continue

            persistant_url = None
            if user_info.avatar_url:
                parsed = urlparse(user_info.avatar_url)
                key = unquote(parsed.path.lstrip("/"))
                persistant_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": BUCKET_NAME, "Key": key},
                    ExpiresIn=3600,
                )

            reference_meta.append(
                PostResponse(
                    id=post.id,
                    title=post.title,
                    slug=post.slug,
                    content_ref=ref.url,
                    author_id=post.author_id,
                    author_active=user_info.is_active,
                    author_name=user_info.name,
                    author_avatar=persistant_url,
                    category_id=post.category_id,
                    status=post.status,
                    published_at=post.published_at,
                    created_at=post.created_at,
                    updated_at=post.updated_at,
                    content="",
                )
            )

        return SearchResponse(
            response=validated_data.text,
            references=reference_meta,
            edits=edits,
        )


@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    # Cached so a FastAPI route handler doesn't re-read the file on every request.
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def ask_agent(payload: Question, user: CurrentUser, db: DB, request: Request):
    return await ask(
        payload.question,
        db,
        referenceDocument=payload.referenceDocument,
        sections=payload.sections,
        base_version=payload.base_version,
    )