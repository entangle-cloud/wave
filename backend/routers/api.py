from fastapi import APIRouter, Response, Depends, status, Request
import os
import re
from database.user import User
from database.post import Post
from database.category import Category as CategoryModel
from database.share import Share, ShareRole
from schemas import PostResponse
from typing import Annotated
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from routers.auth import get_current_user
from sqlalchemy import select, desc, or_
from schemas import ActivityResponse, SharePaylod
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


from urllib.parse import urlparse, unquote
from fastapi import APIRouter, status
from sqlalchemy import select, or_, exists, desc, literal, union_all
from sqlalchemy.orm import aliased

@router.get("/activity")
async def get_activity(
    user: CurrentUser,
    db: DB,
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
):
    # 1. Recursive CTE to gather all categories and their parent hierarchy
    cat_alias = aliased(CategoryModel)
    
    # Base case: All categories with their direct parent
    cat_cte = (
        select(
            CategoryModel.id.label("category_id"),
            CategoryModel.parent_id.label("ancestor_id")
        )
        .cte(name="category_hierarchy", recursive=True)
    )

    # Recursive step: Walk up to the top-level parent category
    cat_cte = cat_cte.union_all(
        select(
            cat_cte.c.category_id,
            cat_alias.parent_id.label("ancestor_id")
        )
        .select_from(cat_cte)
        .join(cat_alias, cat_cte.c.ancestor_id == cat_alias.id)
        .where(cat_alias.parent_id.is_not(None))
    )

    # 2. Check if user owns or has access to category OR any ancestor category
    share_exists = exists().where(
        Share.user_id == user.id,
        or_(
            Share.category_id == cat_cte.c.category_id,
            Share.category_id == cat_cte.c.ancestor_id
        )
    )

    anc_category = aliased(CategoryModel)
    
    category_access_exists = exists().where(
        cat_cte.c.category_id == Post.category_id,
        or_(
            # User created the post's category
            exists().where(
                CategoryModel.id == cat_cte.c.category_id,
                CategoryModel.created_by_id == user.id
            ),
            # User created an ancestor of the post's category
            exists().where(
                anc_category.id == cat_cte.c.ancestor_id,
                anc_category.created_by_id == user.id
            ),
            # User has an explicit share for category or ancestor category
            share_exists
        )
    )

    # 3. Fetch Posts filtering by the category access condition
    stmt = (
        select(Post, User)
        .join(User, Post.author_id == User.id, isouter=True)
        .where(category_access_exists)
        .order_by(desc(Post.id))
        .limit(10)
    )

    latest_posts = await db.execute(stmt)

    post_response: list[PostResponse] = []

    for post, user_info in latest_posts:
        persistant_url = None
        if user_info and user_info.avatar_url is not None:
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
            author_name=user_info.name if user_info else user.name,
            author_avatar=persistant_url,
            author_active=user_info.is_active if user_info else user.is_active,
            category_id=post.category_id,
            status=post.status,
            published_at=post.published_at,
            created_at=post.created_at,
            updated_at=post.updated_at,
            content="",
            description=post.description,
        )
        post_response.append(response)

    return ActivityResponse(postActivity=post_response)


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

@router.post("/share", status_code=status.HTTP_200_OK)
async def share_category(payload: SharePaylod, user: CurrentUser, db: DB):
    # Process each user to share with
    for target_user_id in payload.shared_users:
        # Determine the role (defaulting to VIEWER if not provided or invalid)
        try:
            role = ShareRole(payload.access_level) if payload.access_level else ShareRole.VIEWER
        except ValueError:
            role = ShareRole.VIEWER
            
        share_record = Share(
            category_id=payload.collection,
            user_id=target_user_id,
            granted_by_id=user.id,
            role=role,
        )
        db.add(share_record)
        
    await db.commit()
    return {"message": "Shared successfully"}
