from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Note
from app.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteListItem, UserInfo
from app.services.auth_service import get_current_user
from app.services.note_service import get_accessible_notes, check_note_access

router = APIRouter(prefix="/api/notes", tags=["notes"])


async def _note_response(note: Note, db: AsyncSession) -> NoteResponse:
    owner_result = await db.execute(select(User).where(User.id == note.owner_id))
    owner = owner_result.scalar_one_or_none()
    return NoteResponse(
        id=note.id, title=note.title, content=note.content or "",
        owner_id=note.owner_id, created_at=note.created_at, updated_at=note.updated_at,
        owner=UserInfo(id=owner.id, username=owner.username, avatar_url=owner.avatar_url) if owner else None,
    )


@router.get("", response_model=list[NoteListItem])
async def list_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notes = await get_accessible_notes(db, current_user.id)
    result = []
    for note in notes:
        owner_result = await db.execute(select(User).where(User.id == note.owner_id))
        owner = owner_result.scalar_one_or_none()
        result.append(NoteListItem(
            id=note.id, title=note.title, owner_id=note.owner_id,
            created_at=note.created_at, updated_at=note.updated_at,
            owner=UserInfo(id=owner.id, username=owner.username, avatar_url=owner.avatar_url) if owner else None,
        ))
    return result


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = Note(title=data.title, content=data.content, owner_id=current_user.id)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return await _note_response(note, db)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note, _ = await check_note_access(db, note_id, current_user.id)
    if not note:
        raise HTTPException(404, "笔记不存在或无权访问")
    return await _note_response(note, db)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int, data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note, has_write = await check_note_access(db, note_id, current_user.id)
    if not note:
        raise HTTPException(404, "笔记不存在或无权访问")
    if not has_write:
        raise HTTPException(403, "无权编辑此笔记")
    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content
    await db.commit()
    await db.refresh(note)
    return await _note_response(note, db)


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note, _ = await check_note_access(db, note_id, current_user.id)
    if not note:
        raise HTTPException(404, "笔记不存在或无权访问")
    if note.owner_id != current_user.id:
        raise HTTPException(403, "只有文档所有者可以删除")
    await db.delete(note)
    await db.commit()
