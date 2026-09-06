"""Post management endpoints.

Provides CRUD operations for blog posts. Post bodies are stored in
OpenViking (an external content store accessed via MCP) while metadata
(title, slug, status, author) lives in the local database.
"""

import re
import uuid
import os
from datetime import UTC, datetime
from typing import Annotated

from routers.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Request, status
from mcp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db
from database.post import Post
from database.post import PostStatus
from database.user import User
from database.category import Category
from schemas import (
    PostCreate,
    PostResponse,
    PostUpdate,
    CategoryPostResponse,
    CreatePostResponse,
)
from openviking_tools import ForgetRequest, WriteMode, WriteRequest, call_tool

from clients import viking_client
from openviking_sdk.errors import NotFoundError
from clients.s3_client import s3_client
from urllib.parse import urlparse, unquote


DB = Annotated[AsyncSession, Depends(get_db)]


JWT_SECRET = os.getenv("JWT_SECRET")
BUCKET_NAME = os.getenv("BUCKET_NAME")
_WRITE_URI_RE = re.compile(r"Wrote \d+ bytes to (viking://\S+?) \(mode=")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

router = APIRouter(prefix="/posts", tags=["posts"])


CurrentUser = Annotated[User, Depends(get_current_user)]


def ov_session(request: Request) -> ClientSession:
    """Return the shared OpenViking MCP session attached to the app state."""
    return request.app.state.ov_session


def slugify(title: str) -> str:
    """Convert a title into a URL-safe slug, capped at 270 chars."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:270] or "post"


async def unique_slug(db, base: str) -> str:
    """Return `base`, appending a random suffix if the slug already exists."""
    slug = base
    while await db.scalar(select(Post).where(Post.slug == slug)):
        slug = f"{base}-{uuid.uuid4().hex[:6]}"
    return slug


# TODO: adapt to the write tool's actual response shape once verified against the live server
async def category_path_slugs(db, category_id: int | None) -> list[str]:
    """Walk a category's ancestor chain and return its slugs root-first.

    Used to build the hierarchical storage URI for post content.
    """
    from database.category import Category

    slugs: list[str] = []
    seen: set[int] = set()
    current_id = category_id
    while current_id is not None and current_id not in seen:
        seen.add(current_id)
        category = await db.get(Category, current_id)
        if category is None:
            break
        slugs.append(category.slug)
        current_id = category.parent_id
    slugs.reverse()
    return slugs


def content_uri(post_id: int, slugs: list[str]) -> str:
    """Build a unique `viking://` URI for a post's markdown content."""
    base = "viking://~/resources/" + "".join(f"{s}/" for s in slugs)
    return f"{base}{post_id}-{uuid.uuid4().hex}.md"


def extract_written_uri(result) -> str:
    text = (
        result.structuredContent.get("result", "") if result.structuredContent else ""
    )
    if not text and result.content:
        text = result.content[0].text
    match = _WRITE_URI_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse written URI from write result: {text!r}")
    return match.group(1)


async def save_content(
    session: ClientSession, post_id: int, content: str, slugs: list[str]
) -> str:
    """Write post content to OpenViking and return the stored content URI.

    Raises:
        HTTPException: 502 if the write tool reports an error.
    """
    uri = content_uri(post_id, slugs)
    params = WriteRequest(uri=uri, content=content, mode=WriteMode.CREATE)
    result = await call_tool(session, "write", params)
    if getattr(result, "isError", False):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store post content in OpenViking",
        )
    extract_url = extract_written_uri(result)
    return extract_url


async def delete_content(session: ClientSession, content_ref: str) -> None:
    """Remove a stored document from OpenViking by its URI."""
    params = ForgetRequest(uri=content_ref)
    await call_tool(session, "forget", params)


@router.post("", response_model=CreatePostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: DB, user: CurrentUser, request: Request):
    """Create a new draft post.

    Stores metadata in the database and the markdown body in OpenViking
    under a URI derived from the category path.
    """
    slug = await unique_slug(db, payload.slug or slugify(payload.title))

    post = Post(
        title=payload.title,
        slug=slug,
        content_ref="pending",
        author_id=user.id,
        category_id=payload.category_id,
        status=PostStatus.DRAFT,
    )

    db.add(post)
    await db.flush()

    post.content_ref = await save_content(
        ov_session(request),
        post.id,
        payload.content,
        await category_path_slugs(db, payload.category_id),
    )

    await db.commit()
    await db.refresh(post)
    return CreatePostResponse(
        id=post.id,
        title=post.title,
        slug=post.slug,
        author_id=post.author_id,
        category_id=post.category_id,
        status=post.status,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        description=post.description,
    )


@router.get("", response_model=list[PostResponse])
async def list_posts(db: DB):
    """List all posts, newest first."""
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    return result.scalars().all()


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: DB):
    """Fetch a post's metadata and its content from OpenViking.

    Raises:
        HTTPException: 404 if the post or its stored content is missing.
    """
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    try:
        post_content = await viking_client.client.read(post.content_ref)
        user_info = await db.get(User, post.author_id)

        persistant_url = None
        if user_info.avatar_url is not None:
            parsed = urlparse(user_info.avatar_url)
            key = unquote(parsed.path.lstrip("/"))
            persistant_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,  # 1 hour
            )

        return PostResponse(
            id=post.id,
            title=post.title,
            slug=post.slug,
            content_ref=post.content_ref,
            author_id=post.author_id,
            author_active=user_info.is_active,
            author_name=user_info.name,
            author_avatar=persistant_url,
            category_id=post.category_id,
            status=post.status,
            published_at=post.published_at,
            created_at=post.created_at,
            updated_at=post.updated_at,
            content=post_content,
            description=post.description,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Resource not found")


@router.patch("/{post_id}", response_model=CreatePostResponse)
async def update_post(
    post_id: int, payload: PostUpdate, db: DB, user: CurrentUser, request: Request
):
    """Update a, post (title, slug, category, content, status).

    Only the author or an admin may update. Content changes write a new
    document to OpenViking and delete the old one. Publishing for the
    first time stamps `published_at`.

    Raises:
        HTTPException: 404 if the post is missing; 403 if not permitted.
    """
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    if post.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if payload.title is not None and payload.title != post.title:
        post.title = payload.title
        post.slug = await unique_slug(db, payload.slug or slugify(payload.title))
    elif payload.slug is not None and payload.slug != post.slug:
        post.slug = await unique_slug(db, payload.slug)

    if payload.category_id is not None:
        post.category_id = payload.category_id

    if payload.description is not None:
        post.description = payload.description

    if payload.content is not None:
        old_ref = post.content_ref
        post.content_ref = await save_content(
            ov_session(request),
            post.id,
            payload.content,
            await category_path_slugs(db, post.category_id),
        )
        if old_ref != "pending":
            await delete_content(ov_session(request), old_ref)

    if payload.status is not None:
        post.status = payload.status
        if payload.status == PostStatus.PUBLISHED and post.published_at is None:
            post.published_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(post)
    return CreatePostResponse(
        id=post.id,
        title=post.title,
        slug=post.slug,
        author_id=post.author_id,
        category_id=post.category_id,
        status=post.status,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        description=post.description,
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: DB, user: CurrentUser, request: Request):
    """Delete a post along with its stored OpenViking content.

    Only the author or an admin may delete.

    Raises:
        HTTPException: 404 if the post is missing; 403 if not permitted.
    """
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    if post.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    await delete_content(ov_session(request), post.content_ref)
    await db.delete(post)
    await db.commit()


@router.get("/categories/{category_id}", response_model=CategoryPostResponse)
async def get_posts_in_category(
    category_id: int, db: DB, user: CurrentUser, request: Request
):
    if category_id is None:
        raise HTTPException(status_code=400, detail="No category ID provided")

    # Fetch the category scalar object directly
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Fetch the posts
    posts_result = await db.execute(select(Post).where(Post.category_id == category_id))
    posts = posts_result.scalars().all()

    return {"posts": posts, "category": category}
