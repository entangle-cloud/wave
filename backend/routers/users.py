import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import unquote, urlparse

from clients.s3_client import s3_client
from database.database import get_db
from database.user import User, UserRole
from routers.auth import get_avatar_svg, get_current_user
from schemas import UserResponse

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

BUCKET_NAME = os.getenv("BUCKET_NAME")

router = APIRouter(prefix="/users", tags=["users"])


def require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


def to_user_response(user_info: User) -> UserResponse:
    avatar_url = user_info.avatar_url
    if avatar_url is not None:
        try:
            parsed = urlparse(avatar_url)
            key = unquote(parsed.path.lstrip("/"))
            avatar_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )
        except Exception:
            avatar_url = get_avatar_svg(user_info.email)
    else:
        avatar_url = get_avatar_svg(user_info.email)

    return UserResponse(
        id=user_info.id,
        email=user_info.email,
        name=user_info.name,
        avatar_url=avatar_url,
        role=user_info.role,
        is_active=user_info.is_active,
        created_at=user_info.created_at,
    )


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


@router.get("", response_model=list[UserResponse])
async def list_users(user: CurrentUser, db: DB):
    require_admin(user)
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [to_user_response(u) for u in users]


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_role(user_id: int, payload: UserAdminUpdate, user: CurrentUser, db: DB):
    require_admin(user)

    target = await db.scalar(select(User).where(User.id == user_id))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.role is None and payload.is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to update"
        )

    # Prevent locking yourself out / removing the last admin.
    if target.id == user.id:
        if payload.role is not None and payload.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own admin role",
            )
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account",
            )

    if payload.role is not None and target.role == UserRole.ADMIN and payload.role != UserRole.ADMIN:
        admin_count = await db.scalar(
            select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
        )
        if (admin_count or 0) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin",
            )
        target.role = payload.role

    elif payload.role is not None:
        target.role = payload.role

    if payload.is_active is not None:
        if target.id == user.id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account",
            )
        target.is_active = payload.is_active

    await db.commit()
    await db.refresh(target)
    return to_user_response(target)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, user: CurrentUser, db: DB):
    require_admin(user)

    if user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    target = await db.scalar(select(User).where(User.id == user_id))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target.role == UserRole.ADMIN:
        admin_count = await db.scalar(
            select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
        )
        if (admin_count or 0) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin",
            )

    await db.delete(target)
    await db.commit()
    return {"detail": "deleted"}
