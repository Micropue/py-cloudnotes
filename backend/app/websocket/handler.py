"""
WebSocket 协作处理器
作为 Yjs 消息中继 + 光标/在线状态广播
"""
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Note

# 文档 -> 用户连接 映射
# { note_id: { websocket: {"user_id": int, "username": str, "avatar_url": str, "cursor": dict} } }
rooms: dict[int, dict[WebSocket, dict]] = {}


async def persist_document(note_id: int, content: str):
    """将文档内容异步写入 MySQL"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Note).where(Note.id == note_id))
            note = result.scalar_one_or_none()
            if note:
                note.content = content
                await db.commit()
    except Exception as e:
        print(f"持久化文档失败 note_id={note_id}: {e}")


async def broadcast_text_to_room(note_id: int, message: str, exclude: WebSocket = None):
    """广播文本消息给房间内所有用户（可选排除发送者）"""
    if note_id not in rooms:
        return
    dead = []
    for ws in rooms[note_id]:
        if ws == exclude:
            continue
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await disconnect_user(note_id, ws)


async def broadcast_to_room(note_id: int, message: bytes, exclude: WebSocket = None):
    """广播消息给房间内所有用户（可选排除发送者）"""
    if note_id not in rooms:
        return
    dead = []
    for ws in rooms[note_id]:
        if ws == exclude:
            continue
        try:
            await ws.send_bytes(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await disconnect_user(note_id, ws)


async def broadcast_awareness(note_id: int, exclude: WebSocket = None):
    """广播在线状态 + 光标位置"""
    if note_id not in rooms:
        return
    # 收集所有在线用户信息
    users = []
    for ws, info in rooms[note_id].items():
        users.append({
            "user_id": info["user_id"],
            "username": info["username"],
            "avatar_url": info.get("avatar_url", ""),
            "cursor": info.get("cursor"),
        })

    message = json.dumps({"type": "awareness", "users": users})
    dead = []
    for ws in rooms[note_id]:
        if ws == exclude:
            continue
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await disconnect_user(note_id, ws)


async def disconnect_user(note_id: int, ws: WebSocket):
    """断开用户连接"""
    if note_id in rooms and ws in rooms[note_id]:
        user_info = rooms[note_id].pop(ws, None)
        if user_info:
            await broadcast_awareness(note_id)
    if note_id in rooms and not rooms[note_id]:
        del rooms[note_id]


async def handle_websocket(websocket: WebSocket, note_id: int, user_id: int, username: str, avatar_url: str = ""):
    """处理 WebSocket 协作连接"""
    await websocket.accept()

    # 加入房间
    if note_id not in rooms:
        rooms[note_id] = {}
    rooms[note_id][websocket] = {
        "user_id": user_id,
        "username": username,
        "avatar_url": avatar_url,
        "cursor": None,
    }

    # 广播新的在线状态
    await broadcast_awareness(note_id)

    try:
        while True:
            raw = await websocket.receive()

            if "text" in raw:
                text_data = raw["text"]
                try:
                    data = json.loads(text_data)
                    msg_type = data.get("type")

                    if msg_type == "cursor":
                        # 更新光标位置
                        if note_id in rooms and websocket in rooms[note_id]:
                            rooms[note_id][websocket]["cursor"] = data.get("cursor")
                        # 广播光标更新（低频率，每300ms）
                        await broadcast_awareness(note_id, exclude=websocket)

                    elif msg_type == "sync":
                        # 客户端文档内容变更 — 广播给其他客户端
                        content = data.get("content", "")
                        await broadcast_text_to_room(
                            note_id,
                            json.dumps({"type": "sync", "content": content}),
                            exclude=websocket,
                        )

                    elif msg_type == "sync-request":
                        # 客户端请求最新文档内容（从数据库加载）
                        note_content = await load_document(note_id)
                        await websocket.send_text(json.dumps({
                            "type": "sync-response",
                            "content": note_content,
                        }))

                    elif msg_type == "save":
                        # 客户端请求保存
                        await persist_document(note_id, data.get("content", ""))

                except json.JSONDecodeError:
                    pass

            elif "bytes" in raw:
                # Yjs 二进制同步消息 — 广播给其他客户端
                await broadcast_to_room(note_id, raw["bytes"], exclude=websocket)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await disconnect_user(note_id, websocket)


async def load_document(note_id: int) -> str:
    """从数据库加载文档内容"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Note).where(Note.id == note_id))
            note = result.scalar_one_or_none()
            return note.content if note else ""
    except Exception:
        return ""
