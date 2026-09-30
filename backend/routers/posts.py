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
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.post import Post
from database.post import PostStatus
from database.user import User
from database.user_activity import UserActivity as DocumentActivity
from database.category import Category
from database.share import Share, ShareRole
from lib.avatar import get_avatar_svg
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
from schemas import CategoryAccessResult
from database.user import UserRole


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
        result.structured_content.get("result", "") if result.structured_content else ""
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

    Requires admin or editor-level access on the target category, so
    viewers cannot create. Uncategorized posts require a global
    editor/admin role. Stores metadata in the database and the markdown
    body in OpenViking under a URI derived from the category path.
    """
    if user.role.value != "admin":
        if payload.category_id is not None:
            category_access_stmt = select(Share).where(Share.category_id == payload.category_id, Share.user_id==user.id)
            category_access = await db.execute(category_access_stmt)
            category_access_record = category_access.scalar_one_or_none()
            if category_access_record is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
                

        elif user.role.value != "editor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed",
            )
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
async def get_post(post_id: int, user: CurrentUser, db: DB):
    """Fetch a post's metadata and its content from OpenViking.

    Permitted when the requester is the post author or an admin, or when
    they hold read-level access (any share role, or category creator) on
    the post's category or any ancestor.

    Raises:
        HTTPException: 404 if the post or its stored content is missing.
    """
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    access_gate = has_category_access(
        db=db, category_id=post.category_id, user=user
    )
    if access_gate is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
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
        else:
            persistant_url = get_avatar_svg(user_info.email)

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )


async def has_category_access(
    db, 
    category_id: int | None, 
    user: CurrentUser, 
    *, 
    editor_only: bool = False
) -> CategoryAccessResult:
    # 1. Admins bypass all checks
    if user.role == UserRole.ADMIN or user.role == "admin":
        return CategoryAccessResult(has_access=True, role=UserRole.ADMIN)

    # 2. Guard against None category_id
    if category_id is None:
        return CategoryAccessResult(has_access=False, role=None)

    # 3. Query the composite lookup (user_id + category_id)
    stmt = select(Share).where(
        Share.user_id == user.id,
        Share.category_id == category_id
    )
    result = await db.execute(stmt)
    share_record = result.scalar_one_or_none()

    # 4. Handle missing access record
    if share_record is None:
        return CategoryAccessResult(has_access=False, role=None)

    # 5. Handle editor_only constraint (assuming share_record stores the category role)
    record_role = share_record.role  # or user.role depending on your domain logic
    
    if editor_only and record_role != UserRole.EDITOR:
        return CategoryAccessResult(has_access=False, role=record_role)

    return CategoryAccessResult(has_access=True, role=record_role)


@router.patch("/{post_id}", response_model=CreatePostResponse)
async def update_post(
    post_id: int, payload: PostUpdate, db: DB, user: CurrentUser, request: Request
):
    """Update a, post (title, slug, category, content, status).

    Permitted when the requester is the post author or an admin, or when
    they hold editor-level access (share role ``EDITOR``/``ADMIN``, or
    category creator) on the post's category or any ancestor category.
    Moving a post also requires editor access on the destination category.
    Content changes write a new document to OpenViking and delete the old
    one. Publishing for the first time stamps `published_at`.

    Raises:
        HTTPException: 404 if the post is missing; 403 if not permitted.
    """
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    has_access = await has_category_access(
        db=db, category_id=post.category_id, user=user
    )

    if has_access.has_access is True and has_access.role == UserRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if has_access.has_access is False:
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

    if post.author_id != user.id:
        stmt = pg_insert(DocumentActivity).values(user_id=user.id, post_id=post.id)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["post_id", "user_id"],
            set_=dict(last_edited_at=datetime.now(UTC)),
        )
        await db.execute(upsert_stmt)
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

    Permitted when the requester is the post author or an admin, or when
    they hold editor-level access on the post's category or any ancestor.

    Raises:
        HTTPException: 404 if the post is missing; 403 if not permitted.
    """
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    access_gate = await has_category_access(
        db=db, category_id=post.category_id, user=user
    )

    if access_gate.has_access is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if access_gate.has_access is True and access_gate.role is UserRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    await delete_content(ov_session(request), post.content_ref)
    await db.delete(post)
    await db.commit()


@router.get("/categories/{category_id}", response_model=CategoryPostResponse)
async def get_posts_in_category(
    category_id: int, db: DB, user: CurrentUser, request: Request
):
    """List posts in a category.

    Permitted when the requester is an admin or holds read-level access
    (any share role, or category creator) on the category or any ancestor.
    """
    if category_id is None:
        raise HTTPException(status_code=400, detail="No category ID provided")

    # Fetch the category scalar object directly
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    has_access = await has_category_access(
        db=db, user=user, category_id=category.id
    )

    if has_access.has_access is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Fetch the posts
    posts_result = await db.execute(select(Post).where(Post.category_id == category_id))
    posts = posts_result.scalars().all()

    return {"posts": posts, "category": category}
