from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.core.security import get_password_hash

async def create_user(db: AsyncSession, username: str, password: str):
    hashed_password = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).filter(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    query = select(User).filter(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()