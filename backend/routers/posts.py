import re
import uuid
import os
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from mcp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db
from database.post import Post
from database.post import PostStatus
from database.user import User
from schemas import PostCreate, PostResponse, PostUpdate
from openviking_tools import ForgetRequest, WriteMode, WriteRequest, call_tool

DB = Annotated[AsyncSession, Depends(get_db)]

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

router = APIRouter(prefix="/posts", tags=["posts"])


async def get_current_user(request: Request) -> User:
    from database.database import AsyncSessionLocal

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def ov_session(request: Request) -> ClientSession:
    return request.app.state.ov_session


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:270] or "post"


async def unique_slug(db, base: str) -> str:
    slug = base
    while await db.scalar(select(Post).where(Post.slug == slug)):
        slug = f"{base}-{uuid.uuid4().hex[:6]}"
    return slug


# TODO: adapt to the write tool's actual response shape once verified against the live server
async def category_path_slugs(db, category_id: int | None) -> list[str]:
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
    base = "viking://~/resources/" + "".join(f"{s}/" for s in slugs)
    return f"{base}{post_id}-{uuid.uuid4().hex}.md"


async def save_content(
    session: ClientSession, post_id: int, content: str, slugs: list[str]
) -> str:
    uri = content_uri(post_id, slugs)
    params = WriteRequest(uri=uri, content=content, mode=WriteMode.CREATE)
    result = await call_tool(session, "write", params)
    if getattr(result, "isError", False):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store post content in OpenViking",
        )
    return uri


async def delete_content(session: ClientSession, content_ref: str) -> None:
    params = ForgetRequest(uri=content_ref)
    await call_tool(session, "forget", params)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: DB, user: CurrentUser, request: Request):
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
        ov_session(request), post.id, payload.content, await category_path_slugs(db, payload.category_id)
    )

    await db.commit()
    await db.refresh(post)
    return post


@router.get("", response_model=list[PostResponse])
async def list_posts(db: DB):
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    return result.scalars().all()


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: DB):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, payload: PostUpdate, db: DB, user: CurrentUser, request: Request):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if payload.title is not None and payload.title != post.title:
        post.title = payload.title
        post.slug = await unique_slug(db, payload.slug or slugify(payload.title))
    elif payload.slug is not None and payload.slug != post.slug:
        post.slug = await unique_slug(db, payload.slug)

    if payload.category_id is not None:
        post.category_id = payload.category_id

    if payload.content is not None:
        old_ref = post.content_ref
        post.content_ref = await save_content(
            ov_session(request), post.id, payload.content, await category_path_slugs(db, post.category_id)
        )
        if old_ref != "pending":
            await delete_content(ov_session(request), old_ref)

    if payload.status is not None:
        post.status = payload.status
        if payload.status == PostStatus.PUBLISHED and post.published_at is None:
            post.published_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: DB, user: CurrentUser, request: Request):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    await delete_content(ov_session(request), post.content_ref)
    await db.delete(post)
    await db.commit()
