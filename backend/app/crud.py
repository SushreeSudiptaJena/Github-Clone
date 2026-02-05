from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import Session as ChatSession, Message, User
from typing import List, Optional

async def create_user(db: AsyncSession, username: str, hashed_password: str, email: Optional[str] = None) -> User:
    user = User(username=username, hashed_password=hashed_password, email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    q = await db.execute(select(User).where(User.username == username))
    return q.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = await db.execute(select(User).where(User.email == email))
    return q.scalars().first()

async def create_session(db: AsyncSession, name: str, user_id: Optional[int] = None) -> ChatSession:
    session = ChatSession(name=name, user_id=user_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def get_sessions(db: AsyncSession, user_id: Optional[int] = None) -> List[ChatSession]:
    stmt = select(ChatSession).order_by(ChatSession.created_at.desc())
    if user_id:
        stmt = stmt.where(ChatSession.user_id == user_id)
    q = await db.execute(stmt)
    return q.scalars().all()

async def get_session_by_name(db: AsyncSession, name: str, user_id: Optional[int] = None) -> Optional[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.name == name)
    if user_id:
        stmt = stmt.where(ChatSession.user_id == user_id)
    q = await db.execute(stmt)
    return q.scalars().first()

async def get_session(db: AsyncSession, session_id: int) -> Optional[ChatSession]:
    q = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    return q.scalars().first()

async def create_message(db: AsyncSession, session_id: int, role: str, content: str) -> Message:
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def get_messages(db: AsyncSession, session_id: int) -> List[Message]:
    q = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.created_at))
    return q.scalars().all()

async def update_user_password(db: AsyncSession, user_id: int, hashed_password: str) -> User:
    user = await db.get(User, user_id)
    if not user:
        return None
    user.hashed_password = hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
