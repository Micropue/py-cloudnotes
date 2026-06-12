"""分享链接路由：创建 / 查询 / 撤销 / 加入"""
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Note, ShareLink, PermissionEnum
from app.schemas import (
    CreateShareLinkRequest, ShareLinkResponse, JoinViaShareResponse,
    UserInfo, CollaboratorInfo,
)
from app.services.auth_service import get_current_user
from app.websocket.handler import rooms  # 在线用户

router = APIRouter(prefix="/api", tags=["share"])


def _share_to_response(sl: ShareLink) -> ShareLinkResponse:
    return ShareLinkResponse(
        token=sl.token,
        permission=sl.permission.value,
        is_active=sl.is_active,
        url=f"/join/{sl.token}",
        created_at=sl.created_at,
    )


@router.post("/notes/{note_id}/share-link", response_model=ShareLinkResponse)
async def create_share_link(
    note_id: int,
    data: CreateShareLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建分享链接（仅文档所有者）"""
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(404, "笔记不存在")
    if note.owner_id != current_user.id:
        raise HTTPException(403, "只有文档所有者可以创建分享链接")

    # 检查是否已有活跃链接
    existing = await db.execute(
        select(ShareLink).where(
            ShareLink.note_id == note_id,
            ShareLink.is_active == True,
        )
    )
    existing_link = existing.scalar_one_or_none()
    if existing_link:
        existing_link.permission = PermissionEnum(data.permission)
        await db.commit()
        await db.refresh(existing_link)
        return _share_to_response(existing_link)

    token = secrets.token_urlsafe(16)
    perm = PermissionEnum(data.permission)
    link = ShareLink(
        note_id=note_id,
        token=token,
        permission=perm,
        created_by=current_user.id,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return _share_to_response(link)


@router.get("/notes/{note_id}/share-link", response_model=Optional[ShareLinkResponse])
async def get_share_link(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取已有的分享链接信息"""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.note_id == note_id,
            ShareLink.is_active == True,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "没有活跃的分享链接")
    if link.created_by != current_user.id and link.note.owner_id != current_user.id:
        raise HTTPException(403, "无权查看")
    return _share_to_response(link)


@router.delete("/notes/{note_id}/share-link")
async def revoke_share_link(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """撤销（停止）分享链接"""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.note_id == note_id,
            ShareLink.is_active == True,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "没有活跃的分享链接")
    if link.created_by != current_user.id:
        result2 = await db.execute(select(Note).where(Note.id == note_id))
        note = result2.scalar_one_or_none()
        if not note or note.owner_id != current_user.id:
            raise HTTPException(403, "无权操作")

    link.is_active = False
    await db.commit()
    return {"message": "分享已停止"}


@router.get("/share/{token}", response_model=JoinViaShareResponse)
async def join_via_share_link(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """通过分享链接加入笔记"""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.token == token,
            ShareLink.is_active == True,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "分享链接无效或已失效")

    # 获取笔记信息
    note_result = await db.execute(select(Note).where(Note.id == link.note_id))
    note = note_result.scalar_one_or_none()
    if not note:
        raise HTTPException(404, "笔记不存在")

    # 获取作者信息
    owner_result = await db.execute(select(User).where(User.id == note.owner_id))
    owner = owner_result.scalar_one_or_none()

    return JoinViaShareResponse(
        note_id=note.id,
        note_title=note.title,
        permission=link.permission.value,
        owner=UserInfo(id=owner.id, username=owner.username, avatar_url=owner.avatar_url) if owner else None,
    )


@router.get("/notes/{note_id}/collaborators", response_model=list[CollaboratorInfo])
async def list_collaborators(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出协作者（所有者 + 通过分享链接加入的在线用户）"""
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(404, "笔记不存在")

    collabs = []

    # 所有者
    owner_result = await db.execute(select(User).where(User.id == note.owner_id))
    owner = owner_result.scalar_one_or_none()
    if owner:
        collabs.append(CollaboratorInfo(
            user_id=owner.id,
            username=owner.username,
            avatar_url=owner.avatar_url,
            permission="owner",
            is_online=_is_online(note_id, owner.id),
        ))

    # 在线用户（从 WebSocket rooms）
    if note_id in rooms:
        for ws, info in rooms[note_id].items():
            uid = info.get("user_id")
            if uid and uid != note.owner_id:
                # 检查是否已有
                if not any(c.user_id == uid for c in collabs):
                    collabs.append(CollaboratorInfo(
                        user_id=uid,
                        username=info.get("username", "未知"),
                        avatar_url=info.get("avatar_url", ""),
                        permission="write",
                        is_online=True,
                    ))

    return collabs


def _is_online(note_id: int, user_id: int) -> bool:
    """检查用户是否在线（通过 WebSocket 连接判断）"""
    if note_id not in rooms:
        return False
    for info in rooms[note_id].values():
        if info.get("user_id") == user_id:
            return True
    return False
