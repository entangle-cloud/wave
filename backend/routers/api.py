from fastapi import APIRouter, Response, Depends, status, Request
import os
import re
from database.user import User
from database.post import Post
from schemas import PostResponse
from typing import Annotated
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from routers.auth import get_current_user
from sqlalchemy import select, desc, or_
from schemas import ActivityResponse
from clients.s3_client import s3_client
from urllib.parse import urlparse, unquote
from schemas import UserResponse

router = APIRouter(prefix="/api", tags=["api"])

DB = Annotated[AsyncSession, Depends(get_db)]
JWT_SECRET = os.getenv("JWT_SECRET")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRECT not set")

if not BUCKET_NAME:
    raise RuntimeError("BUCKET_NAME not set")

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/activity")
async def get_activity(
    user: CurrentUser,
    db: DB,
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
):
    stmt = (
        select(Post, User)
        .join(User, Post.author_id == User.id, isouter=True)
        .order_by(desc(Post.id))
        .limit(10)
    )

    latest_posts = await db.execute(stmt)

    post_respose: list[PostResponse] = []

    for post, user_info in latest_posts:
        if user_info.avatar_url is not None:
            parsed = urlparse(user_info.avatar_url)
            key = unquote(parsed.path.lstrip("/"))
            persistant_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )

        response = PostResponse(
            id=post.id,
            title=post.title,
            slug=post.slug,
            content_ref=post.content_ref,
            author_id=post.author_id,
            author_name=user.name,
            author_avatar=persistant_url,
            author_active=user.is_active,
            category_id=post.category_id,
            status=post.status,
            published_at=post.published_at,
            created_at=post.created_at,
            updated_at=post.updated_at,
            content="",
            description=post.description,
        )
        post_respose.append(response)

    return ActivityResponse(postActivity=post_respose)


@router.get(
    "/search_users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
async def search_user(
    search_query: str,
    db: DB,
    user: CurrentUser,
    limit: int = 10,
):
    user_output: list[UserResponse] = []
    stmt = (
        select(User)
        .where(or_(User.email.contains(search_query), User.name.contains(search_query)))
        .limit(limit=limit)
    )
    result = (await db.execute(stmt)).scalars().all()
    if not result:
        return []
    for user_info in result:
        persistant_url = None
        if user_info.avatar_url is not None:
            parsed = urlparse(user_info.avatar_url)
            key = unquote(parsed.path.lstrip("/"))
            persistant_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )

        user_output.append(
            UserResponse(
                id=user.id,
                email=user_info.email,
                name=user_info.name,
                avatar_url=persistant_url,
                role=user_info.role,
                is_active=user_info.is_active,
                created_at=user_info.created_at,
            )
        )

    return user_output
