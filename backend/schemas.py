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
    role: UserRole | None = None
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


class CreatePostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    author_id: int | None
    category_id: int | None
    status: PostStatus
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    description: str | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    content_ref: str
    author_id: int | None
    author_name: str
    author_avatar: str | None
    author_active: bool
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


class CategoryCreate(BaseModel):
    model_config= ConfigDict(from_attributes=True)
    name: str 
    color: str
    description: str 
    parent_category: int | None = None


class CategoryPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    posts: list[CategoryPosts]
    category: CategoryResponse


class Reference(BaseModel):
    title: str
    url: str  # Use str or custom validation for 'viking://' URIs
    relevance: str

class LLMResponseSchema(BaseModel):
    text: str
    references: list[Reference] = Field(default_factory=list)

class ActivityResponse(BaseModel):
    postActivity: list[PostResponse] | None = None 

class SharePaylod(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    collection: int 
    shared_by: int
    shared_users: list[int]
    access_level: str | None = None
    
class SettingsPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str 
    value: str 
    description: str | None = None 
    is_secret: bool = False

class EmailPayload(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    from_address: str
    to: str 
    subject: str
    content: str
    
class EditProposal(BaseModel):
    section_id: str
    markdown: str
    base_version: int | None = None

class SectionIn(BaseModel):
    id: str
    markdown: str

class Question(BaseModel):
    question: str
    referenceDocument: int | None = None
    sections: list[SectionIn] | None = None     # current editor content, split by section
    base_version: str | int | None = None

class SearchResponse(BaseModel):
    response: str
    references: list[PostResponse]
    edits: list[EditProposal] = []