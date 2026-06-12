from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, exists
from app.models import Note, ShareLink, User, PermissionEnum


async def get_accessible_notes(db: AsyncSession, user_id: int):
    """Get notes owned by user OR accessible via active share link."""
    share_exists = (
        exists()
        .where(
            ShareLink.note_id == Note.id,
            ShareLink.is_active == True,
        )
    )
    result = await db.execute(
        select(Note)
        .where(or_(Note.owner_id == user_id, share_exists))
        .order_by(Note.updated_at.desc())
    )
    return result.scalars().all()


async def check_note_access(db: AsyncSession, note_id: int, user_id: int):
    """Check if user has access. Returns (note, has_write)."""
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return None, False

    # 所有者有完整权限
    if note.owner_id == user_id:
        return note, True

    # 检查是否有活跃的分享链接
    share_result = await db.execute(
        select(ShareLink).where(
            ShareLink.note_id == note_id,
            ShareLink.is_active == True,
        )
    )
    share = share_result.scalar_one_or_none()
    if share:
        return note, share.permission == PermissionEnum.write

    return None, False


async def get_note_with_owner(db: AsyncSession, note_id: int):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if note:
        owner_result = await db.execute(select(User).where(User.id == note.owner_id))
        note.owner = owner_result.scalar_one_or_none()
    return note
