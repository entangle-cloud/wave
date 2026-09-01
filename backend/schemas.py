from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from database.post import PostStatus
from fastapi import Form
from database.user import UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    avatar_url: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    name: str 
    role: UserRole |None = None 
    is_active: bool | None = None

def user_update_form(
    email: EmailStr = Form(...),
    name: str = Form(...),
    role: UserRole | None = Form(None),
    is_active: bool | None = Form(None),
) -> UserUpdate:
    return UserUpdate(email=email, name=name, role=role, is_active=is_active)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category_id: int | None = None
    slug: str | None = Field(None, min_length=1, max_length=280)
    description: str | None = Field(None, max_length=500) 


class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    category_id: int | None = None
    slug: str | None = Field(None, min_length=1, max_length=280)
    status: PostStatus | None = None
    description: str | None = Field(None, max_length=500)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    content_ref: str
    author_id: int | None
    category_id: int | None
    status: PostStatus
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    content: str | None
    description: str | None = None

class CategoryPosts(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str 
    colour: str 
    parent_category: int | None = None
    
    
class CategoryPostResponse(BaseModel):
    model_config= ConfigDict(from_attributes = True)
    posts: list[CategoryPosts]
    category: CategoryResponse 

