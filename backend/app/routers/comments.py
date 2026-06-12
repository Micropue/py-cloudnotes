from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Note, Comment
from app.schemas import CommentCreate, CommentResponse, UserInfo
from app.services.auth_service import get_current_user
from app.services.note_service import check_note_access

router = APIRouter(prefix="/api/notes/{note_id}/comments", tags=["comments"])


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note, _ = await check_note_access(db, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权访问")

    result = await db.execute(
        select(Comment)
        .where(Comment.note_id == note_id)
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()

    resp = []
    for c in comments:
        author_result = await db.execute(select(User).where(User.id == c.user_id))
        author = author_result.scalar_one_or_none()
        resp.append(CommentResponse(
            id=c.id,
            note_id=c.note_id,
            user_id=c.user_id,
            content=c.content,
            created_at=c.created_at,
            author=UserInfo(id=author.id, username=author.username, avatar_url=author.avatar_url) if author else None,
        ))
    return resp


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    note_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note, _ = await check_note_access(db, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权访问")

    comment = Comment(note_id=note_id, user_id=current_user.id, content=data.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        note_id=comment.note_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        author=UserInfo(
            id=current_user.id,
            username=current_user.username,
            avatar_url=current_user.avatar_url,
        ),
    )
