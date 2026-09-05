from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

import os
import uuid
from datetime import datetime, timedelta, UTC

import bcrypt
import jwt
from typing import Annotated

from database.database import get_db
from database.user import User, UserRole
from schemas import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
    user_update_form,
)


from urllib.parse import urlparse, unquote
from clients.s3_client import s3_client

JWT_SECRET = os.getenv("JWT_SECRET")
BUCKET_NAME = os.getenv("BUCKET_NAME")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")

DB = Annotated[AsyncSession, Depends(get_db)]

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(request: Request) -> User:
    """Resolve the authenticated user from the `access_token` JWT cookie.

    Raises:
        HTTPException: 401 if the cookie is missing, the token is invalid,
            or the user does not exist / is inactive.
    """
    from database.database import AsyncSessionLocal

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user: User) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(payload: SignupRequest, db: DB):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user_count = await db.scalar(select(func.count()).select_from(User))
    role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER

    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DB, response: Response):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )

    persistant_url = None
    if user.avatar_url is not None:
        parsed = urlparse(user.avatar_url)
        key = unquote(parsed.path.lstrip("/"))

        persistant_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600,  # 1 hour
        )

    response_user = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": persistant_url,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }

    access_token = create_access_token(user)
    response.set_cookie(
        key="access_token",
        value=access_token,
        secure=True,
        httponly=True,
        samesite="none",
        max_age=int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60,
        path="/",
    )
    return TokenResponse(access_token=access_token, user=response_user)


@router.get("/me", response_model=UserResponse)
async def get_profile(user: CurrentUser, db: DB):
    findUser = await db.scalar(select(User).where(User.id == user.id))
    if not findUser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    if not findUser.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )

    persistant_url = ""

    if findUser.avatar_url is not None:
        parsed = urlparse(user.avatar_url)
        key = unquote(parsed.path.lstrip("/"))

        persistant_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600,  # 1 hour
        )

    return UserResponse(
        id=findUser.id,
        email=findUser.email,
        name=findUser.name,
        avatar_url=persistant_url,
        role=findUser.role,
        is_active=findUser.is_active,
        created_at=findUser.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    avatar: UploadFile,
    user: CurrentUser,
    db: DB,
    user_payload: UserUpdate = Depends(user_update_form),
):
    findUser = await db.scalar(select(User).where(User.id == user.id))
    if not findUser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if avatar.content_type not in (
        "image/png",
        "image/webp",
        "image/avif",
        "image/jpeg",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Upsupported image type"
        )

    ext = avatar.content_type.split("/")[-1]
    file_key = f"{user.id}/{uuid.uuid4()}.{ext}"
    contents = await avatar.read()

    s3_client.put_object(
        Bucket=BUCKET_NAME, Key=file_key, Body=contents, ContentType=avatar.content_type
    )

    s3_client.delete_object(Bucket=BUCKET_NAME, Key=findUser.avatar_url)
    avatar_url = f"{R2_ENDPOINT}/{file_key}"

    findUser.name = user_payload.name
    findUser.email = user_payload.email
    findUser.avatar_url = avatar_url

    persistant_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": file_key},
        ExpiresIn=3600,  # 1 hour
    )

    await db.commit()
    await db.refresh(findUser)
    return {
        "id": findUser.id,
        "email": findUser.email,
        "name": findUser.name,
        "avatar_url": persistant_url,
        "role": findUser.role,
        "is_active": findUser.is_active,
        "created_at": findUser.created_at,
    }
