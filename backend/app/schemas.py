from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ---- Auth ----
class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    avatar_url: str

    class Config:
        from_attributes = True


# ---- Notes ----
class NoteCreate(BaseModel):
    title: str = "未命名笔记"
    content: str = ""


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserInfo] = None

    class Config:
        from_attributes = True


class NoteListItem(BaseModel):
    id: int
    title: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserInfo] = None

    class Config:
        from_attributes = True


# ---- Share Link ----
class CreateShareLinkRequest(BaseModel):
    permission: str = "read"


class ShareLinkResponse(BaseModel):
    token: str
    permission: str
    is_active: bool
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class JoinViaShareResponse(BaseModel):
    note_id: int
    note_title: str
    permission: str
    owner: Optional[UserInfo] = None


# ---- Collaborators ----
class CollaboratorInfo(BaseModel):
    user_id: int
    username: str
    avatar_url: str
    permission: str
    is_online: bool = False


# ---- Comments ----
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    note_id: int
    user_id: int
    content: str
    created_at: datetime
    author: Optional[UserInfo] = None

    class Config:
        from_attributes = True
